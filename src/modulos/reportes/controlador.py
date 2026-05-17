"""Controlador del modulo de reportes."""

from __future__ import annotations

from comun.actualizaciones import EventoModuloActualizado, bus_actualizaciones_modulos
from modulos.reportes.servicio import ServicioReportes
from modulos.reportes.vista import VistaReportes


class ControladorReportes:
    """Conecta la vista con los servicios del modulo."""

    def __init__(
        self,
        servicio_reportes: ServicioReportes,
        vista_reportes: VistaReportes,
    ) -> None:
        self.servicio_reportes = servicio_reportes
        self.vista_reportes = vista_reportes
        self._fecha_desde = ""
        self._fecha_hasta = ""
        self.vista_reportes.filtros_aplicados.connect(self._aplicar_filtros)
        self.vista_reportes.exportar_solicitado.connect(self._exportar)
        bus_actualizaciones_modulos.actualizacion_emitida.connect(self._manejar_actualizacion_modulo)

    def mostrar(self) -> None:
        try:
            estado = self.servicio_reportes.obtener_estado(
                fecha_desde=self._fecha_desde,
                fecha_hasta=self._fecha_hasta,
            )
        except ValueError as error:
            self.vista_reportes.mostrar_mensaje(str(error), es_error=True)
            return
        self.vista_reportes.mostrar_estado(estado)

    def _aplicar_filtros(self, fecha_desde: str, fecha_hasta: str) -> None:
        self._fecha_desde = fecha_desde
        self._fecha_hasta = fecha_hasta
        self.mostrar()

    def _manejar_actualizacion_modulo(self, evento: object) -> None:
        if not isinstance(evento, EventoModuloActualizado):
            return
        if "reportes" not in evento.modulos_afectados:
            return
        self.mostrar()
        self.vista_reportes.mostrar_mensaje(evento.mensaje, es_error=False)

    def _exportar(self) -> None:
        codigo_reporte = self.vista_reportes.obtener_reporte_actual_codigo()
        if not codigo_reporte:
            self.vista_reportes.mostrar_mensaje(
                "Selecciona un reporte para exportar.",
                es_error=True,
            )
            return
        ruta = self.vista_reportes.solicitar_ruta_exportacion(codigo_reporte)
        if not ruta:
            return
        try:
            self.servicio_reportes.exportar_pdf(
                ruta_destino=ruta,
                codigo_reporte=codigo_reporte,
                fecha_desde=self._fecha_desde,
                fecha_hasta=self._fecha_hasta,
            )
        except (OSError, ValueError) as error:
            self.vista_reportes.mostrar_mensaje(str(error), es_error=True)
            return
        self.vista_reportes.mostrar_mensaje("Reporte exportado correctamente.", es_error=False)
