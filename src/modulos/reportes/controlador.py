"""Controlador del modulo de reportes."""

from __future__ import annotations

from pathlib import Path

from comun.actualizaciones import EventoModuloActualizado, bus_actualizaciones_modulos
from comun.cobros import ErrorCicloCobro
from comun.ui.documentos_pdf import abrir_documento_pdf
from modulos.autenticacion.entidades import UsuarioAutenticado
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
        self._actor: UsuarioAutenticado | None = None
        self.vista_reportes.reporte_seleccionado.connect(self._seleccionar_reporte)
        self.vista_reportes.filtros_aplicados.connect(self._aplicar_filtros)
        self.vista_reportes.exportar_solicitado.connect(self._exportar)
        self.vista_reportes.exportar_en_solicitado.connect(self._exportar_en)
        bus_actualizaciones_modulos.actualizacion_emitida.connect(self._manejar_actualizacion_modulo)

    def mostrar(self) -> None:
        try:
            estado = self.servicio_reportes.obtener_estado(
                codigo_reporte=self._codigo_reporte_actual,
                filtros=self._filtros_actuales,
            )
        except (ErrorCicloCobro, ValueError) as error:
            self.vista_reportes.mostrar_mensaje(str(error), es_error=True)
            return
        if not self._codigo_reporte_actual:
            self._codigo_reporte_actual = estado.reporte_actual
        self.vista_reportes.mostrar_estado(estado)

    def mostrar_para_actor(self, actor: UsuarioAutenticado) -> None:
        self._actor = actor
        self.mostrar()

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
        self._ejecutar_exportacion(codigo_reporte, filtros, directorio_destino=None)

    def _exportar_en(
        self,
        codigo_reporte: str,
        filtros: object,
        directorio_destino: str,
    ) -> None:
        self._ejecutar_exportacion(
            codigo_reporte,
            filtros,
            directorio_destino=directorio_destino,
        )

    def _ejecutar_exportacion(
        self,
        codigo_reporte: str,
        filtros: object,
        directorio_destino: str | None,
    ) -> None:
        codigo = codigo_reporte or self._codigo_reporte_actual
        if not codigo:
            self.vista_reportes.mostrar_mensaje(
                "Selecciona un reporte para exportar.",
                es_error=True,
            )
            return
        self.vista_reportes.establecer_exportacion_en_curso(True)
        try:
            resultado = self.servicio_reportes.exportar_pdf_con_resultado(
                ruta_destino=None,
                codigo_reporte=codigo,
                filtros=dict(filtros or {}),
                generado_por=self._resolver_nombre_actor(),
                directorio_destino=directorio_destino,
            )
        except (ErrorCicloCobro, OSError, ValueError) as error:
            self.vista_reportes.mostrar_mensaje(str(error), es_error=True)
            return
        finally:
            self.vista_reportes.establecer_exportacion_en_curso(False)

        configuracion = self.servicio_reportes.obtener_configuracion_salida_pdf()
        advertencias: list[str] = []
        if resultado.uso_fallback:
            advertencias.append("se uso la carpeta interna de respaldo")
        if configuracion.abrir_automaticamente and not abrir_documento_pdf(
            Path(resultado.ruta).resolve()
        ):
            advertencias.append("no fue posible abrirlo automaticamente")
        mensaje = f"Reporte generado: {Path(resultado.ruta).name}"
        if advertencias:
            mensaje = f"{mensaje}. Advertencia: {'; '.join(advertencias)}."
        self.vista_reportes.mostrar_mensaje(mensaje, es_error=False)

    def _resolver_nombre_actor(self) -> str:
        if self._actor is None:
            return "Sistema"
        return self._actor.nombre_completo.strip() or self._actor.nombre_usuario.strip() or "Sistema"
