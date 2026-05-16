"""Servicios del modulo de pagos."""

from __future__ import annotations

import hashlib
from datetime import date, datetime
from pathlib import Path

from comun.configuracion.gestor_rutas import GestorRutas
from modulos.pagos.entidades import (
    CargoPago,
    ComprobantePago,
    DetalleAplicacionPago,
    EstadoModuloPagos,
    FormularioPago,
    ResumenConfirmacionPago,
    ResultadoPago,
    TIPO_PAGO_MENSUALIDAD,
    TIPOS_PAGO_VALIDOS,
)
from modulos.pagos.repositorio import RepositorioPagos


class ServicioPagos:
    """Orquesta las reglas de negocio del modulo de pagos."""

    def __init__(
        self,
        repositorio_pagos: RepositorioPagos,
        gestor_rutas: GestorRutas | None = None,
    ):
        self.repositorio_pagos = repositorio_pagos
        self._gestor_rutas = gestor_rutas or GestorRutas()

    def obtener_estado(self, filtro: str = "") -> EstadoModuloPagos:
        return EstadoModuloPagos(
            casas=tuple(self.repositorio_pagos.listar_casas(filtro=filtro)),
            metodos_pago=tuple(self.repositorio_pagos.listar_metodos_pago_activos()),
        )

    def obtener_cargos_mensuales(self, casa_id: int) -> tuple[CargoPago, ...]:
        return tuple(self.repositorio_pagos.listar_cargos_mensuales(casa_id))

    def obtener_casa(self, casa_id: int):
        return self.repositorio_pagos.obtener_casa(casa_id)

    def previsualizar_pago_mensual(
        self,
        formulario: FormularioPago,
    ) -> ResumenConfirmacionPago | ResultadoPago:
        return self.preparar_confirmacion(formulario)

    def preparar_confirmacion(self, formulario: FormularioPago) -> ResumenConfirmacionPago | ResultadoPago:
        if formulario.tipo_pago not in TIPOS_PAGO_VALIDOS:
            return ResultadoPago(False, "El tipo de pago no es valido.", "VALIDACION")
        if formulario.tipo_pago != TIPO_PAGO_MENSUALIDAD:
            return ResultadoPago(
                False,
                "Esta version cierra primero mensualidades y pagos adelantados. Usa planes, conexion o reconexion en una fase separada.",
                "FLUJO_PENDIENTE",
            )
        if formulario.casa_id is None or formulario.casa_id <= 0:
            return ResultadoPago(False, "Selecciona una casa para registrar el pago.", "VALIDACION")
        if formulario.metodo_pago_id is None or formulario.metodo_pago_id <= 0:
            return ResultadoPago(False, "Selecciona un metodo de pago.", "VALIDACION")
        if formulario.cantidad_meses <= 0:
            return ResultadoPago(False, "Indica al menos un mes a pagar.", "VALIDACION")

        casa = self.repositorio_pagos.obtener_casa(formulario.casa_id)
        if casa is None:
            return ResultadoPago(False, "La casa seleccionada ya no existe.", "NO_ENCONTRADO")
        if casa.abonado_estado != "ACTIVO":
            return ResultadoPago(
                False,
                "La casa no tiene un abonado responsable activo para registrar pagos.",
                "VALIDACION",
            )
        if casa.estado_servicio in {"SUSPENDIDO", "INACTIVO"}:
            return ResultadoPago(
                False,
                "La casa debe tener un abonado responsable activo antes de registrar pagos.",
                "VALIDACION",
            )

        metodo = self.repositorio_pagos.obtener_metodo_pago(formulario.metodo_pago_id)
        if metodo is None:
            return ResultadoPago(False, "El metodo de pago seleccionado no esta activo.", "VALIDACION")
        referencia = formulario.referencia.strip()
        if metodo.requiere_referencia and not referencia:
            return ResultadoPago(
                False,
                "Este metodo de pago requiere una referencia.",
                "VALIDACION",
            )

        resumen_deuda = self.repositorio_pagos.obtener_resumen_deuda_pago(casa.casa_id)
        cargos = self.repositorio_pagos.listar_cargos_mensuales(casa.casa_id)
        precio_mensual = self.repositorio_pagos.obtener_precio_mensual_centavos()
        if precio_mensual <= 0:
            return ResultadoPago(
                False,
                "Configura primero el precio mensual del servicio.",
                "VALIDACION",
            )

        detalles: list[DetalleAplicacionPago] = []
        meses_solicitados = formulario.cantidad_meses
        for cargo in cargos[:meses_solicitados]:
            etiqueta = "Vencido" if cargo.estado == "VENCIDO" else "Pendiente"
            detalles.append(
                DetalleAplicacionPago(
                    cargo_id=cargo.identificador,
                    periodo_id=cargo.periodo_id,
                    periodo_anio=cargo.periodo_anio,
                    periodo_mes=cargo.periodo_mes,
                    periodo_nombre=cargo.periodo_nombre,
                    concepto_codigo=cargo.concepto_codigo,
                    descripcion=cargo.descripcion,
                    monto_centavos=cargo.saldo_pendiente_centavos,
                    etiqueta=etiqueta,
                    es_adelantado=False,
                )
            )

        meses_adelantados = meses_solicitados - len(detalles)
        if meses_adelantados > 0:
            if resumen_deuda.deuda_vencida_no_mensual_centavos > 0:
                return ResultadoPago(
                    False,
                    "No se pueden registrar pagos adelantados mientras exista deuda vencida no mensual.",
                    "VALIDACION",
                )
            ultimo_anio, ultimo_mes = self._resolver_ultimo_periodo(cargos)
            for desplazamiento in range(1, meses_adelantados + 1):
                anio, mes = self._sumar_meses(ultimo_anio, ultimo_mes, desplazamiento)
                detalles.append(
                    DetalleAplicacionPago(
                        cargo_id=None,
                        periodo_id=None,
                        periodo_anio=anio,
                        periodo_mes=mes,
                        periodo_nombre=f"Periodo {mes:02d}/{anio:04d}",
                        concepto_codigo="SERVICIO_MENSUAL",
                        descripcion=f"Mensualidad adelantada {mes:02d}/{anio:04d}",
                        monto_centavos=precio_mensual,
                        etiqueta="Adelantado",
                        es_adelantado=True,
                    )
                )

        total_pago = sum(detalle.monto_centavos for detalle in detalles)
        monto_aplicado_deuda = sum(
            detalle.monto_centavos for detalle in detalles if not detalle.es_adelantado
        )
        saldo_posterior = max(0, casa.deuda_total_centavos - monto_aplicado_deuda)
        return ResumenConfirmacionPago(
            casa=casa,
            tipo_pago=formulario.tipo_pago,
            metodo_pago=metodo,
            detalles=tuple(detalles),
            saldo_anterior_centavos=casa.deuda_total_centavos,
            total_pago_centavos=total_pago,
            saldo_posterior_centavos=saldo_posterior,
            referencia=referencia,
            observaciones=formulario.observaciones.strip(),
        )

    def registrar_pago(
        self,
        formulario: FormularioPago,
        actor_id: int | None,
    ) -> ResultadoPago:
        if actor_id is None or actor_id <= 0:
            return ResultadoPago(False, "No hay un usuario valido registrando el pago.", "VALIDACION")
        confirmacion = self.preparar_confirmacion(formulario)
        if isinstance(confirmacion, ResultadoPago):
            return confirmacion
        try:
            comprobante = self.repositorio_pagos.guardar_pago_confirmado(
                resumen=confirmacion,
                actor_id=actor_id,
            )
        except Exception as error:
            return ResultadoPago(
                False,
                f"No fue posible registrar el pago. {error}",
                "ERROR_SQLITE",
            )
        return ResultadoPago(
            True,
            f"Pago registrado correctamente. Comprobante {comprobante.numero_comprobante}.",
            "OK",
            comprobante,
        )

    def obtener_comprobante(self, pago_id: int) -> ComprobantePago | None:
        return self.repositorio_pagos.obtener_comprobante(pago_id)

    def generar_html_comprobante(self, comprobante: ComprobantePago) -> str:
        detalles = "".join(
            f"<li>{self._escapar_html(detalle)}</li>"
            for detalle in comprobante.detalles
        ) or "<li>Sin detalle registrado.</li>"
        referencia = comprobante.referencia or "No aplica"
        return f"""
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <title>{self._escapar_html(comprobante.numero_comprobante)}</title>
  <style>
    body {{
      background: #2c2966;
      color: #f7fbff;
      font-family: Segoe UI, Arial, sans-serif;
      margin: 0;
      padding: 24px;
    }}
    .tarjeta {{
      max-width: 720px;
      margin: 0 auto;
      background: rgba(65, 62, 130, 0.95);
      border: 1px solid rgba(148, 161, 194, 0.28);
      border-radius: 18px;
      padding: 28px;
    }}
    .encabezado {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 18px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.12);
      padding-bottom: 16px;
      margin-bottom: 18px;
    }}
    .marca {{ font-size: 28px; font-weight: 800; }}
    .subtitulo {{ color: #c7d4e5; margin-top: 6px; }}
    .numero {{ color: #73f2db; font-size: 22px; font-weight: 800; }}
    .fila {{
      display: grid;
      grid-template-columns: 180px 1fr;
      gap: 12px;
      padding: 8px 0;
    }}
    .etiqueta {{ color: #c7d4e5; }}
    .valor {{ color: #ffffff; font-weight: 700; }}
    .totales {{ margin-top: 14px; }}
    ul {{ margin: 10px 0 0 18px; padding: 0; }}
    li {{ margin: 6px 0; }}
  </style>
</head>
<body>
  <div class="tarjeta">
    <div class="encabezado">
      <div>
        <div class="marca">SICAP</div>
        <div class="subtitulo">Comprobante de pago</div>
      </div>
      <div class="numero">{self._escapar_html(comprobante.numero_comprobante)}</div>
    </div>
    <div class="fila"><div class="etiqueta">Tipo</div><div class="valor">{self._escapar_html(self._etiqueta_tipo_pago(comprobante.tipo_comprobante))}</div></div>
    <div class="fila"><div class="etiqueta">Casa</div><div class="valor">{self._escapar_html(comprobante.casa_codigo)}</div></div>
    <div class="fila"><div class="etiqueta">Abonado</div><div class="valor">{self._escapar_html(comprobante.abonado_nombre)}</div></div>
    <div class="fila"><div class="etiqueta">DNI</div><div class="valor">{self._escapar_html(comprobante.abonado_dni)}</div></div>
    <div class="fila"><div class="etiqueta">Metodo</div><div class="valor">{self._escapar_html(comprobante.metodo_pago)}</div></div>
    <div class="fila"><div class="etiqueta">Referencia</div><div class="valor">{self._escapar_html(referencia)}</div></div>
    <div class="fila"><div class="etiqueta">Detalle</div><div class="valor"><ul>{detalles}</ul></div></div>
    <div class="fila totales"><div class="etiqueta">Total pagado</div><div class="valor">{self.formatear_moneda(comprobante.total_pagado_centavos)}</div></div>
    <div class="fila"><div class="etiqueta">Saldo posterior</div><div class="valor">{self.formatear_moneda(comprobante.saldo_posterior_centavos)}</div></div>
    <div class="fila"><div class="etiqueta">Generado</div><div class="valor">{self.formatear_fecha(comprobante.generado_en)}</div></div>
  </div>
</body>
</html>
""".strip()

    def generar_texto_comprobante(self, comprobante: ComprobantePago) -> str:
        detalle = "\n".join(f"- {item}" for item in comprobante.detalles) or "- Sin detalle registrado."
        referencia = comprobante.referencia or "No aplica"
        return (
            f"SICAP\n"
            f"Comprobante de pago {comprobante.numero_comprobante}\n\n"
            f"Tipo: {self._etiqueta_tipo_pago(comprobante.tipo_comprobante)}\n"
            f"Casa: {comprobante.casa_codigo}\n"
            f"Abonado: {comprobante.abonado_nombre}\n"
            f"DNI: {comprobante.abonado_dni}\n"
            f"Metodo: {comprobante.metodo_pago}\n"
            f"Referencia: {referencia}\n"
            f"Detalle:\n{detalle}\n\n"
            f"Total pagado: {self.formatear_moneda(comprobante.total_pagado_centavos)}\n"
            f"Saldo posterior: {self.formatear_moneda(comprobante.saldo_posterior_centavos)}\n"
            f"Fecha: {self.formatear_fecha(comprobante.generado_en)}\n"
        )

    def exportar_comprobante(
        self,
        comprobante: ComprobantePago,
        ruta_destino: str,
    ) -> str:
        ruta = Path(ruta_destino).expanduser()
        ruta.parent.mkdir(parents=True, exist_ok=True)
        sufijo = ruta.suffix.lower()
        if sufijo == ".txt":
            contenido = self.generar_texto_comprobante(comprobante)
            formato = "TEXTO"
        else:
            contenido = self.generar_html_comprobante(comprobante)
            formato = "HTML"
        ruta.write_text(contenido, encoding="utf-8")
        hash_documento = hashlib.sha256(contenido.encode("utf-8")).hexdigest()
        self.repositorio_pagos.actualizar_documento_comprobante(
            pago_id=comprobante.pago_id,
            ruta_archivo=str(ruta),
            formato_salida=formato,
            hash_documento=hash_documento,
        )
        return str(ruta)

    def ruta_sugerida_comprobante(self, comprobante: ComprobantePago, extension: str = ".html") -> str:
        base = self._gestor_rutas.obtener_ruta_exportaciones_comprobantes()
        return str(base / f"{comprobante.numero_comprobante}{extension}")

    @staticmethod
    def formatear_moneda(valor_centavos: int) -> str:
        return f"L {valor_centavos / 100:,.2f}"

    @staticmethod
    def formatear_fecha(valor: str) -> str:
        if not valor:
            return "Sin registro"
        try:
            fecha = datetime.fromisoformat(valor)
        except ValueError:
            return valor
        return fecha.strftime("%d/%m/%Y")

    @staticmethod
    def _resolver_ultimo_periodo(cargos: list[object]) -> tuple[int, int]:
        periodos = [
            (cargo.periodo_anio, cargo.periodo_mes)
            for cargo in cargos
            if cargo.periodo_anio is not None and cargo.periodo_mes is not None
        ]
        if periodos:
            return max(periodos)
        hoy = date.today()
        if hoy.month == 1:
            return hoy.year - 1, 12
        return hoy.year, hoy.month - 1

    @staticmethod
    def _sumar_meses(anio: int, mes: int, desplazamiento: int) -> tuple[int, int]:
        indice = (anio * 12) + (mes - 1) + desplazamiento
        return indice // 12, (indice % 12) + 1

    @staticmethod
    def _etiqueta_tipo_pago(tipo_pago: str) -> str:
        etiquetas = {
            "MENSUALIDAD": "Mensualidad",
            "PLAN_PAGO": "Plan de pago",
            "CONEXION": "Conexion",
            "RECONEXION": "Reconexion",
        }
        return etiquetas.get(tipo_pago, tipo_pago)

    @staticmethod
    def _escapar_html(valor: str) -> str:
        return (
            valor.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )
