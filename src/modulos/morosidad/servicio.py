"""Servicio del modulo de morosidad."""

from __future__ import annotations

from datetime import date, datetime

from comun.configuracion.identidad_empresa import (
    CLAVES_IDENTIDAD_EMPRESA,
    CLAVES_IDENTIDAD_LEGADAS_JUNTA,
    construir_identidad_empresa,
)
from comun.configuracion.gestor_rutas import GestorRutas
from modulos.documentos import ServicioEstadoCuenta
from modulos.documentos.servicios.servicio_comprobante_pago import ServicioComprobantePago
from modulos.morosidad.entidades import (
    DetalleMorosidad,
    EstadoMorosidad,
    FILTRO_MOROSIDAD_LEVE,
    FILTRO_MOROSIDAD_MEDIA,
    FILTRO_MOROSIDAD_SEVERA,
    FILTRO_MOROSIDAD_TODOS,
    FilaMorosidad,
    FiltroMorosidad,
    PaginaMorosidad,
    ResumenMorosidad,
    ResultadoMorosidad,
)
from modulos.morosidad.repositorio import RepositorioMorosidad


class ServicioMorosidad:
    """Orquesta consultas, detalle y emision de documentos de deuda."""

    CLAVES_IDENTIDAD_DOCUMENTAL = (
        *CLAVES_IDENTIDAD_EMPRESA,
        *CLAVES_IDENTIDAD_LEGADAS_JUNTA,
        "factura.mostrar_correo",
        "factura.mostrar_telefono",
        "factura.mostrar_direccion",
        "factura.mostrar_identificador_fiscal",
        "documentos.firma_habilitada",
        "documentos.firma_nombre",
        "documentos.firma_cargo",
        "documentos.firma_identificador",
        "documentos.firma_texto_apoyo",
    )
    CLAVES_MORA_VISUAL = (
        "cobro.mora_leve_hasta_meses",
        "cobro.mora_media_hasta_meses",
    )
    TAMANO_PAGINA = 10

    def __init__(
        self,
        repositorio_morosidad: RepositorioMorosidad,
        gestor_rutas: GestorRutas | None = None,
        servicio_estado_cuenta: ServicioEstadoCuenta | None = None,
    ) -> None:
        self._repositorio_morosidad = repositorio_morosidad
        self._gestor_rutas = gestor_rutas or GestorRutas()
        self._servicio_estado_cuenta = servicio_estado_cuenta or ServicioEstadoCuenta(
            gestor_rutas=self._gestor_rutas
        )

    def obtener_estado(self, filtros: FiltroMorosidad | None = None, pagina: int = 1) -> EstadoMorosidad:
        filtros = filtros or FiltroMorosidad()
        pagina = max(1, pagina)
        rangos = self.obtener_parametros_mora_visual()
        filas = [
            self._aplicar_severidad(item, rangos)
            for item in self._repositorio_morosidad.listar_morosidad(filtros)
        ]
        if filtros.severidad != FILTRO_MOROSIDAD_TODOS:
            filas = [item for item in filas if item.severidad == filtros.severidad]
        resumen = ResumenMorosidad(
            total_casas=len(filas),
            total_abonados=len({fila.abonado_id for fila in filas}),
            deuda_base_centavos=sum(fila.deuda_base_centavos for fila in filas),
            recargo_mora_centavos=sum(fila.recargo_mora_centavos for fila in filas),
            deuda_total_centavos=sum(fila.deuda_total_centavos for fila in filas),
            casos_severos=sum(1 for fila in filas if fila.severidad == FILTRO_MOROSIDAD_SEVERA),
        )
        total_registros = len(filas)
        total_paginas = max(1, (total_registros + self.TAMANO_PAGINA - 1) // self.TAMANO_PAGINA)
        pagina = min(pagina, total_paginas)
        inicio = (pagina - 1) * self.TAMANO_PAGINA
        fin = inicio + self.TAMANO_PAGINA
        pagina_resultado = PaginaMorosidad(
            items=filas[inicio:fin],
            pagina_actual=pagina,
            tamano_pagina=self.TAMANO_PAGINA,
            total_registros=total_registros,
        )
        return EstadoMorosidad(resumen=resumen, pagina=pagina_resultado, filtros=filtros)

    def obtener_detalle(self, abonado_id: int) -> DetalleMorosidad | None:
        detalle = self._repositorio_morosidad.obtener_detalle_abonado(abonado_id)
        if detalle is None:
            return None
        rangos = self.obtener_parametros_mora_visual()
        casas = []
        for casa in detalle.casas:
            severidad = self._resolver_severidad(casa.meses_vencidos, rangos)
            casa.prioridad = self.etiqueta_severidad(severidad)
            casa.dias_en_mora = self._calcular_dias_en_mora(casa.vencimiento_mas_antiguo)
            casas.append(casa)
        detalle.casas = tuple(casas)
        return detalle

    def emitir_documento_deuda(
        self,
        abonado_id: int,
        casas_seleccionadas: tuple[int, ...],
    ) -> ResultadoMorosidad:
        detalle = self.obtener_detalle(abonado_id)
        if detalle is None:
            return ResultadoMorosidad(
                exito=False,
                mensaje="No fue posible reconstruir la deuda del abonado seleccionado.",
                codigo="NO_ENCONTRADO",
            )
        if not detalle.casas:
            return ResultadoMorosidad(
                exito=False,
                mensaje="El abonado ya no tiene casas con deuda vencida.",
                codigo="SIN_DEUDA",
            )
        try:
            ruta = self._servicio_estado_cuenta.generar_pdf(
                detalle=detalle,
                casas_seleccionadas=casas_seleccionadas,
                lineas_encabezado=self._obtener_lineas_encabezado_documental(),
                formateador_moneda=self.formatear_moneda,
                formateador_fecha=self.formatear_fecha,
                firma=self._obtener_configuracion_documental(),
            )
        except OSError as error:
            return ResultadoMorosidad(
                exito=False,
                mensaje=f"No fue posible generar el documento PDF de deuda. {error}",
                codigo="ERROR_PDF",
            )
        return ResultadoMorosidad(
            exito=True,
            mensaje=f"Documento de deuda generado correctamente: {self._extraer_nombre_archivo(ruta)}",
            codigo="OK",
            ruta_documento=ruta,
        )

    def obtener_parametros_mora_visual(self) -> tuple[int, int]:
        parametros = self._repositorio_morosidad.listar_parametros_configuracion(self.CLAVES_MORA_VISUAL)
        leve = self._leer_entero(parametros.get("cobro.mora_leve_hasta_meses"), 2)
        media = self._leer_entero(parametros.get("cobro.mora_media_hasta_meses"), 5)
        if leve < 1:
            leve = 1
        if media <= leve:
            media = leve + 1
        return leve, media

    @staticmethod
    def filtro_inicial() -> FiltroMorosidad:
        return FiltroMorosidad()

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
    def etiqueta_severidad(severidad: str) -> str:
        etiquetas = {
            FILTRO_MOROSIDAD_LEVE: "Baja",
            FILTRO_MOROSIDAD_MEDIA: "Media",
            FILTRO_MOROSIDAD_SEVERA: "Critica",
        }
        return etiquetas.get(severidad, "Mora")

    def _aplicar_severidad(self, fila: FilaMorosidad, rangos: tuple[int, int]) -> FilaMorosidad:
        severidad = self._resolver_severidad(fila.meses_vencidos, rangos)
        fila.severidad = severidad
        fila.prioridad = self.etiqueta_severidad(severidad)
        fila.dias_en_mora = self._calcular_dias_en_mora(fila.vencimiento_mas_antiguo)
        return fila

    def _obtener_lineas_encabezado_documental(self) -> tuple[str, ...]:
        return tuple(
            ServicioComprobantePago.lineas_encabezado_desde_configuracion(
                self._obtener_configuracion_documental()
            )
        )

    def _obtener_configuracion_documental(self) -> object:
        valores = self._repositorio_morosidad.listar_parametros_configuracion(
            self.CLAVES_IDENTIDAD_DOCUMENTAL
        )
        parametros = {
            clave: getattr(parametro, "valor", "")
            for clave, parametro in valores.items()
        }
        identidad = construir_identidad_empresa(parametros, nombre_predeterminado="SICAP")

        class _ConfiguracionTemporal:
            nombre_junta = identidad.nombre
            telefono_junta = identidad.telefono
            correo_junta = identidad.correo
            direccion_junta = identidad.direccion
            identificador_fiscal = identidad.identificador_fiscal
            sitio_web = identidad.sitio_web
            mensaje_contacto = identidad.mensaje_contacto
            mostrar_correo = ServicioMorosidad._a_booleano(
                valores.get("factura.mostrar_correo").valor
                if valores.get("factura.mostrar_correo")
                else "1"
            )
            mostrar_telefono = ServicioMorosidad._a_booleano(
                valores.get("factura.mostrar_telefono").valor
                if valores.get("factura.mostrar_telefono")
                else "1"
            )
            mostrar_direccion = ServicioMorosidad._a_booleano(
                valores.get("factura.mostrar_direccion").valor
                if valores.get("factura.mostrar_direccion")
                else "1"
            )
            mostrar_identificador_fiscal = ServicioMorosidad._a_booleano(
                valores.get("factura.mostrar_identificador_fiscal").valor
                if valores.get("factura.mostrar_identificador_fiscal")
                else "0"
            )
            firma_habilitada = ServicioMorosidad._a_booleano(
                valores.get("documentos.firma_habilitada").valor
                if valores.get("documentos.firma_habilitada")
                else "0"
            )
            firma_nombre = (
                valores.get("documentos.firma_nombre").valor
                if valores.get("documentos.firma_nombre")
                else ""
            )
            firma_cargo = (
                valores.get("documentos.firma_cargo").valor
                if valores.get("documentos.firma_cargo")
                else ""
            )
            firma_identificador = (
                valores.get("documentos.firma_identificador").valor
                if valores.get("documentos.firma_identificador")
                else ""
            )
            firma_texto_apoyo = (
                valores.get("documentos.firma_texto_apoyo").valor
                if valores.get("documentos.firma_texto_apoyo")
                else ""
            )

        return _ConfiguracionTemporal()

    @staticmethod
    def _a_booleano(valor: str) -> bool:
        return str(valor).strip().upper() in {"1", "TRUE", "SI", "S", "YES", "ON"}

    @staticmethod
    def _leer_entero(parametro: object, predeterminado: int) -> int:
        if parametro is None:
            return predeterminado
        try:
            return int(getattr(parametro, "valor", predeterminado))
        except (TypeError, ValueError):
            return predeterminado

    @staticmethod
    def _extraer_nombre_archivo(ruta: str) -> str:
        return ruta.replace("\\", "/").split("/")[-1]

    @staticmethod
    def _calcular_dias_en_mora(vencimiento_mas_antiguo: str) -> int:
        if not vencimiento_mas_antiguo:
            return 0
        try:
            fecha_vencimiento = datetime.fromisoformat(vencimiento_mas_antiguo).date()
        except ValueError:
            return 0
        return max(0, (date.today() - fecha_vencimiento).days)

    @staticmethod
    def _resolver_severidad(meses_vencidos: int, rangos: tuple[int, int]) -> str:
        leve, media = rangos
        if meses_vencidos <= leve:
            return FILTRO_MOROSIDAD_LEVE
        if meses_vencidos <= media:
            return FILTRO_MOROSIDAD_MEDIA
        return FILTRO_MOROSIDAD_SEVERA
