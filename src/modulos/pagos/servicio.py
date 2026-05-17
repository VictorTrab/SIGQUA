"""Servicios del modulo de pagos."""

from __future__ import annotations

from datetime import date, datetime

from comun.configuracion.gestor_rutas import GestorRutas
from modulos.documentos import ServicioComprobantePago
from modulos.pagos.entidades import (
    CargoPago,
    ComprobantePago,
    ConfiguracionReciboPago,
    DiagnosticoPagoMensual,
    DetalleAplicacionPago,
    ESTADO_VISUAL_PAGO_BLOQUEADO,
    ESTADO_VISUAL_PAGO_OK,
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
        servicio_comprobante_pago: ServicioComprobantePago | None = None,
    ):
        self.repositorio_pagos = repositorio_pagos
        self._gestor_rutas = gestor_rutas or GestorRutas()
        self._servicio_comprobante_pago = servicio_comprobante_pago or ServicioComprobantePago(
            gestor_rutas=self._gestor_rutas,
        )

    def obtener_estado(self, filtro: str = "") -> EstadoModuloPagos:
        return EstadoModuloPagos(
            casas=tuple(self.repositorio_pagos.listar_casas(filtro=filtro)),
            metodos_pago=tuple(self.repositorio_pagos.listar_metodos_pago_activos()),
        )

    def obtener_cargos_mensuales(self, casa_id: int) -> tuple[CargoPago, ...]:
        return tuple(self.repositorio_pagos.listar_cargos_mensuales(casa_id))

    def obtener_casa(self, casa_id: int):
        return self.repositorio_pagos.obtener_casa(casa_id)

    def obtener_diagnostico_pago_mensual(self, casa_id: int) -> DiagnosticoPagoMensual | None:
        casa = self.repositorio_pagos.obtener_casa(casa_id)
        if casa is None:
            return None
        alertas: list[str] = []
        resultado = self._validar_estado_operativo_mensual(casa.abonado_estado, casa.estado_servicio)
        permite_continuar = resultado is None
        if resultado is not None:
            alertas.append(resultado.mensaje)
        if casa.meses_vencidos > 0:
            alertas.append(
                f"La casa tiene {casa.meses_vencidos} mes(es) vencido(s) y se cobrarán primero."
            )
        if casa.deuda_total_centavos <= 0:
            alertas.append(
                "La casa no tiene deuda mensual pendiente; cualquier pago se tratará como adelanto si la regla vigente lo permite."
            )
        if not alertas:
            alertas.append("La casa cumple las reglas vigentes para continuar con el pago mensual.")
        return DiagnosticoPagoMensual(
            casa_id=casa.casa_id,
            permite_continuar=permite_continuar,
            estado_visual=ESTADO_VISUAL_PAGO_OK if permite_continuar else ESTADO_VISUAL_PAGO_BLOQUEADO,
            mensaje_diagnostico=alertas[0],
            alertas=tuple(alertas),
        )

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
        validacion_estado = self._validar_estado_operativo_mensual(casa.abonado_estado, casa.estado_servicio)
        if validacion_estado is not None:
            return validacion_estado

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

    def _validar_estado_operativo_mensual(
        self,
        abonado_estado: str,
        estado_servicio: str,
    ) -> ResultadoPago | None:
        if abonado_estado != "ACTIVO":
            return ResultadoPago(
                False,
                "Solo se puede registrar pago mensual cuando el abonado responsable está ACTIVO.",
                "VALIDACION",
            )
        if estado_servicio == "SUSPENDIDO":
            return ResultadoPago(
                False,
                "No se puede registrar pago mensual para una casa suspendida. Reactiva o reasigna primero un abonado activo responsable.",
                "VALIDACION",
            )
        if estado_servicio == "CORTADO":
            return ResultadoPago(
                False,
                "La casa está cortada. El pago mensual directo no aplica en este flujo; primero debe resolverse mediante reconexión.",
                "VALIDACION",
            )
        if estado_servicio == "INACTIVO":
            return ResultadoPago(
                False,
                "No se puede registrar pago mensual para una casa inactiva.",
                "VALIDACION",
            )
        if estado_servicio != "ACTIVO":
            return ResultadoPago(
                False,
                f"La casa debe estar ACTIVA para registrar pago mensual. Estado actual: {estado_servicio}.",
                "VALIDACION",
            )
        return None

    def obtener_comprobante(self, pago_id: int) -> ComprobantePago | None:
        return self.repositorio_pagos.obtener_comprobante(pago_id)

    def obtener_configuracion_recibo(self) -> ConfiguracionReciboPago:
        return self.repositorio_pagos.obtener_configuracion_recibo()

    def generar_comprobante_pdf(self, pago_id: int, ruta_destino: str | None = None) -> str:
        comprobante = self.obtener_comprobante(pago_id)
        if comprobante is None:
            raise ValueError("No fue posible recuperar el comprobante solicitado.")
        configuracion = self.obtener_configuracion_recibo()
        return self._servicio_comprobante_pago.generar_pdf(
            comprobante=comprobante,
            configuracion=configuracion,
            formateador_moneda=self.formatear_moneda,
            formateador_fecha=self.formatear_fecha,
            formateador_hora=self.formatear_hora,
            etiqueta_tipo_pago=self._etiqueta_tipo_pago,
            ruta_destino=ruta_destino,
        )

    def ruta_sugerida_comprobante(self, comprobante: ComprobantePago, extension: str = ".pdf") -> str:
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
    def formatear_hora(valor: str) -> str:
        if not valor:
            return "Sin registro"
        try:
            fecha = datetime.fromisoformat(valor)
        except ValueError:
            return valor
        return fecha.strftime("%H:%M")

    def _separar_fecha_hora(self, valor: str) -> tuple[str, str]:
        return self.formatear_fecha(valor), self.formatear_hora(valor)

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
