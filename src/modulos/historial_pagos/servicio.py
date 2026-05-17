"""Servicios del modulo de historial de pagos."""

from __future__ import annotations

from datetime import datetime

from comun.configuracion.gestor_rutas import GestorRutas
from modulos.documentos.servicios.servicio_comprobante_pago import ServicioComprobantePago
from modulos.historial_pagos.entidades import (
    DetalleHistorialPago,
    FILTRO_HISTORIAL_TODOS,
    FILTRO_METODO_TODOS,
    FiltroHistorialPagos,
    PaginaHistorialPagos,
    ResumenHistorialPagos,
    ResultadoHistorialPagos,
)
from modulos.historial_pagos.repositorio import RepositorioHistorialPagos


class ServicioHistorialPagos:
    """Orquesta filtros, detalle y reimpresion del historial."""

    TAMANO_PAGINA = 10

    def __init__(
        self,
        repositorio_historial: RepositorioHistorialPagos,
        gestor_rutas: GestorRutas | None = None,
        servicio_comprobante_pago: ServicioComprobantePago | None = None,
    ) -> None:
        self._repositorio_historial = repositorio_historial
        self._gestor_rutas = gestor_rutas or GestorRutas()
        self._servicio_comprobante_pago = servicio_comprobante_pago or ServicioComprobantePago(
            gestor_rutas=self._gestor_rutas,
        )

    def obtener_resumen(self, filtros: FiltroHistorialPagos | None = None) -> ResumenHistorialPagos:
        filtros = filtros or FiltroHistorialPagos()
        self._validar_rango(filtros.fecha_desde, filtros.fecha_hasta)
        return self._repositorio_historial.obtener_resumen_historial(filtros)

    def listar(
        self,
        filtros: FiltroHistorialPagos | None = None,
        pagina: int = 1,
    ) -> PaginaHistorialPagos:
        filtros = filtros or FiltroHistorialPagos()
        self._validar_rango(filtros.fecha_desde, filtros.fecha_hasta)
        pagina = max(1, pagina)
        total_registros = self._repositorio_historial.contar_historial(filtros)
        total_paginas = max(1, (total_registros + self.TAMANO_PAGINA - 1) // self.TAMANO_PAGINA)
        pagina = min(pagina, total_paginas)
        desplazamiento = (pagina - 1) * self.TAMANO_PAGINA
        items = self._repositorio_historial.listar_historial(
            filtros=filtros,
            limite=self.TAMANO_PAGINA,
            desplazamiento=desplazamiento,
        )
        return PaginaHistorialPagos(
            items=items,
            pagina_actual=pagina,
            tamano_pagina=self.TAMANO_PAGINA,
            total_registros=total_registros,
        )

    def obtener_detalle(self, pago_id: int) -> DetalleHistorialPago | None:
        return self._repositorio_historial.obtener_detalle_pago(pago_id)

    def reimprimir_copia(self, pago_id: int) -> ResultadoHistorialPagos:
        comprobante = self._repositorio_historial.obtener_comprobante_para_reimpresion(pago_id)
        if comprobante is None:
            return ResultadoHistorialPagos(
                False,
                "No fue posible recuperar el comprobante seleccionado.",
                "NO_ENCONTRADO",
            )
        configuracion = self._repositorio_historial.obtener_configuracion_recibo()
        try:
            ruta = self._servicio_comprobante_pago.generar_pdf(
                comprobante=comprobante,
                configuracion=configuracion,
                formateador_moneda=self.formatear_moneda,
                formateador_fecha=self.formatear_fecha,
                formateador_hora=self.formatear_hora,
                etiqueta_tipo_pago=self.etiqueta_tipo_pago,
            )
        except OSError as error:
            return ResultadoHistorialPagos(
                False,
                f"No fue posible regenerar la copia PDF. {error}",
                "ERROR_PDF",
            )
        return ResultadoHistorialPagos(
            True,
            f"Copia regenerada correctamente: {self._extraer_nombre_archivo(ruta)}",
            "OK",
            ruta_documento=ruta,
        )

    @staticmethod
    def formatear_moneda(valor_centavos: int) -> str:
        return f"L {valor_centavos / 100:,.2f}"

    @staticmethod
    def formatear_fecha_hora(valor: str) -> str:
        if not valor:
            return "Sin registro"
        try:
            fecha = datetime.fromisoformat(valor)
        except ValueError:
            return valor
        return fecha.strftime("%d/%m/%Y %I:%M %p")

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

    @staticmethod
    def etiqueta_tipo_pago(tipo_pago: str) -> str:
        etiquetas = {
            "MENSUALIDAD": "Mensualidad",
            "PLAN_PAGO": "Plan",
            "CONEXION": "Conexion",
            "RECONEXION": "Reconexion",
        }
        return etiquetas.get(tipo_pago, tipo_pago)

    @staticmethod
    def filtro_inicial() -> FiltroHistorialPagos:
        return FiltroHistorialPagos(
            texto="",
            tipo_pago=FILTRO_HISTORIAL_TODOS,
            metodo_pago=FILTRO_METODO_TODOS,
            fecha_desde="",
            fecha_hasta="",
        )

    @staticmethod
    def _validar_rango(fecha_desde: str, fecha_hasta: str) -> None:
        if fecha_desde:
            datetime.strptime(fecha_desde, "%Y-%m-%d")
        if fecha_hasta:
            datetime.strptime(fecha_hasta, "%Y-%m-%d")
        if fecha_desde and fecha_hasta and fecha_desde > fecha_hasta:
            raise ValueError("La fecha inicial no puede ser mayor que la fecha final.")

    @staticmethod
    def _extraer_nombre_archivo(ruta: str) -> str:
        return ruta.replace("\\", "/").split("/")[-1]
