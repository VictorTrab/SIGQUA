"""Servicio del modulo de morosidad."""

from __future__ import annotations

from datetime import datetime

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
        "junta.nombre",
        "junta.telefono",
        "junta.correo",
        "junta.direccion",
        "junta.identificador_fiscal",
        "junta.sitio_web",
        "junta.mensaje_contacto",
        "factura.mostrar_correo",
        "factura.mostrar_telefono",
        "factura.mostrar_direccion",
        "factura.mostrar_identificador_fiscal",
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
        return self._repositorio_morosidad.obtener_detalle_abonado(abonado_id)

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
            FILTRO_MOROSIDAD_LEVE: "Mora leve",
            FILTRO_MOROSIDAD_MEDIA: "Mora media",
            FILTRO_MOROSIDAD_SEVERA: "Mora severa",
        }
        return etiquetas.get(severidad, "Mora")

    def _aplicar_severidad(self, fila: FilaMorosidad, rangos: tuple[int, int]) -> FilaMorosidad:
        leve, media = rangos
        severidad = FILTRO_MOROSIDAD_SEVERA
        if fila.meses_vencidos <= leve:
            severidad = FILTRO_MOROSIDAD_LEVE
        elif fila.meses_vencidos <= media:
            severidad = FILTRO_MOROSIDAD_MEDIA
        fila.severidad = severidad
        return fila

    def _obtener_lineas_encabezado_documental(self) -> tuple[str, ...]:
        valores = self._repositorio_morosidad.listar_parametros_configuracion(
            self.CLAVES_IDENTIDAD_DOCUMENTAL
        )

        class _ConfiguracionTemporal:
            nombre_junta = valores.get("junta.nombre").valor if valores.get("junta.nombre") else "Junta de Agua"
            telefono_junta = valores.get("junta.telefono").valor if valores.get("junta.telefono") else ""
            correo_junta = valores.get("junta.correo").valor if valores.get("junta.correo") else ""
            direccion_junta = valores.get("junta.direccion").valor if valores.get("junta.direccion") else ""
            identificador_fiscal = (
                valores.get("junta.identificador_fiscal").valor
                if valores.get("junta.identificador_fiscal")
                else ""
            )
            sitio_web = valores.get("junta.sitio_web").valor if valores.get("junta.sitio_web") else ""
            mensaje_contacto = (
                valores.get("junta.mensaje_contacto").valor
                if valores.get("junta.mensaje_contacto")
                else ""
            )
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

        return tuple(ServicioComprobantePago.lineas_encabezado_desde_configuracion(_ConfiguracionTemporal()))

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
