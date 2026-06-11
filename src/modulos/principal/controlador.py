"""Controladores del modulo principal."""

from __future__ import annotations

from typing import Callable

from comun.actualizaciones import EventoModuloActualizado, bus_actualizaciones_modulos
from modulos.autenticacion.entidades import UsuarioAutenticado
from modulos.principal.servicio import ServicioModuloPrincipal
from modulos.principal.vista import VistaModuloPrincipal


class ControladorModuloPrincipal:
    """Conecta la vista con los servicios del modulo principal."""

    def __init__(
        self,
        servicio_modulo_principal: ServicioModuloPrincipal,
        vista_modulo_principal: VistaModuloPrincipal,
    ) -> None:
        self.servicio_modulo_principal = servicio_modulo_principal
        self.vista_modulo_principal = vista_modulo_principal
        self.vista_modulo_principal.cerrar_sesion_solicitada.connect(
            self._manejar_cierre_sesion
        )
        self.vista_modulo_principal.modulo_solicitado.connect(self._manejar_modulo_solicitado)
        bus_actualizaciones_modulos.actualizacion_emitida.connect(
            self._manejar_actualizacion_modulo
        )
        self._callback_cierre_sesion: Callable[[], None] | None = None
        self._usuario_actual: UsuarioAutenticado | None = None
        self._dashboard_pendiente_actualizacion = False

    def mostrar_inicio(self, usuario: UsuarioAutenticado) -> None:
        self._usuario_actual = usuario
        self.vista_modulo_principal.preparar_perfil_usuario(usuario.correo)
        estado = self.servicio_modulo_principal.obtener_estado_para_usuario(usuario)
        self.vista_modulo_principal.mostrar_estado(estado)
        self._dashboard_pendiente_actualizacion = False

    def registrar_modulo(self, codigo: str, vista: object) -> None:
        self.vista_modulo_principal.registrar_modulo(codigo, vista)

    def configurar_callback_cierre_sesion(
        self,
        callback_cierre_sesion: Callable[[], None],
    ) -> None:
        self._callback_cierre_sesion = callback_cierre_sesion

    def _manejar_cierre_sesion(self) -> None:
        if self._callback_cierre_sesion is not None:
            self._callback_cierre_sesion()

    def _manejar_modulo_solicitado(self, codigo: str) -> None:
        if codigo == "dashboard" and self._dashboard_pendiente_actualizacion:
            self._recargar_dashboard_pendiente()
        self.vista_modulo_principal.mostrar_modulo(codigo)

    def _recargar_dashboard_pendiente(self) -> None:
        if self._usuario_actual is None:
            return
        try:
            estado = self.servicio_modulo_principal.obtener_estado_para_usuario(self._usuario_actual)
            self.vista_modulo_principal.actualizar_dashboard(estado)
            self._dashboard_pendiente_actualizacion = False
            self.vista_modulo_principal.mostrar_resultado_actualizacion_dashboard("Dashboard actualizado")
        except Exception:
            self.vista_modulo_principal.mostrar_resultado_actualizacion_dashboard(
                "No se pudo actualizar", error=True
            )

    def _manejar_actualizacion_modulo(self, evento: EventoModuloActualizado) -> None:
        if not isinstance(evento, EventoModuloActualizado):
            return
        modulos_dashboard = {
            "barrios",
            "abonados",
            "casas",
            "pagos",
            "historial_pagos",
            "morosidad",
            "planes_pago",
            "reportes",
            "configuracion",
        }
        modulos_afectados = {evento.modulo_origen, *evento.modulos_afectados}
        if self._usuario_actual is None or not modulos_dashboard.intersection(modulos_afectados):
            return
        self._dashboard_pendiente_actualizacion = True
        self.vista_modulo_principal.establecer_dashboard_pendiente_actualizacion(True)
