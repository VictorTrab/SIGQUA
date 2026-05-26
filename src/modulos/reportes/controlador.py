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
        self._codigo_reporte_actual = ""
        self._filtros_actuales: dict[str, str] = {}
        self.vista_reportes.reporte_seleccionado.connect(self._seleccionar_reporte)
        self.vista_reportes.filtros_aplicados.connect(self._aplicar_filtros)
        self.vista_reportes.exportar_solicitado.connect(self._exportar)
        bus_actualizaciones_modulos.actualizacion_emitida.connect(self._manejar_actualizacion_modulo)

    def mostrar(self) -> None:
        try:
            estado = self.servicio_reportes.obtener_estado(
                codigo_reporte=self._codigo_reporte_actual,
                filtros=self._filtros_actuales,
            )
        except ValueError as error:
            self.vista_reportes.mostrar_mensaje(str(error), es_error=True)
            return
        if not self._codigo_reporte_actual:
            self._codigo_reporte_actual = estado.reporte_actual
        self.vista_reportes.mostrar_estado(estado)

    def _seleccionar_reporte(self, codigo_reporte: str) -> None:
        self._codigo_reporte_actual = codigo_reporte
        self.mostrar()

    def _aplicar_filtros(self, codigo_reporte: str, filtros: object) -> None:
        self._codigo_reporte_actual = codigo_reporte or self._codigo_reporte_actual
        self._filtros_actuales = dict(filtros or {})
        self.mostrar()

    def _manejar_actualizacion_modulo(self, evento: object) -> None:
        if not isinstance(evento, EventoModuloActualizado):
            return
        if "reportes" not in evento.modulos_afectados:
            return
        self.mostrar()
        self.vista_reportes.mostrar_mensaje(evento.mensaje, es_error=False)

    def _exportar(self, codigo_reporte: str, filtros: object) -> None:
        codigo = codigo_reporte or self._codigo_reporte_actual
        if not codigo:
            self.vista_reportes.mostrar_mensaje(
                "Selecciona un reporte para exportar.",
                es_error=True,
            )
            return
        ruta = self.vista_reportes.solicitar_ruta_exportacion(codigo)
        if not ruta:
            return
        try:
            ruta_pdf = self.servicio_reportes.exportar_pdf(
                ruta_destino=ruta,
                codigo_reporte=codigo,
                filtros=dict(filtros or {}),
            )
        except (OSError, ValueError) as error:
            self.vista_reportes.mostrar_mensaje(str(error), es_error=True)
            return
        self.vista_reportes.mostrar_mensaje(
            f"Reporte PDF generado correctamente: {ruta_pdf}",
            es_error=False,
        )
