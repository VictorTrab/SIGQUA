"""Controladores del modulo principal."""

from __future__ import annotations

from typing import Callable

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
        self.vista_modulo_principal.abrir_mantenimiento_solicitado.connect(
            self._manejar_apertura_mantenimiento
        )
        self._callback_cierre_sesion: Callable[[], None] | None = None
        self._callback_apertura_mantenimiento: Callable[[], None] | None = None

    def mostrar_inicio(self, usuario: UsuarioAutenticado) -> None:
        estado = self.servicio_modulo_principal.obtener_estado_para_usuario(usuario)
        self.vista_modulo_principal.mostrar_estado(estado)

    def configurar_callback_cierre_sesion(
        self,
        callback_cierre_sesion: Callable[[], None],
    ) -> None:
        self._callback_cierre_sesion = callback_cierre_sesion

    def configurar_callback_apertura_mantenimiento(
        self,
        callback_apertura_mantenimiento: Callable[[], None],
    ) -> None:
        self._callback_apertura_mantenimiento = callback_apertura_mantenimiento

    def _manejar_cierre_sesion(self) -> None:
        if self._callback_cierre_sesion is not None:
            self._callback_cierre_sesion()

    def _manejar_apertura_mantenimiento(self) -> None:
        if self._callback_apertura_mantenimiento is not None:
            self._callback_apertura_mantenimiento()
