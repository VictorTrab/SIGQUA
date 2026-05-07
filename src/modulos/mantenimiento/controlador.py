"""Controlador del modulo de mantenimiento."""

from __future__ import annotations

from typing import Callable

from modulos.mantenimiento.servicio import ServicioMantenimiento
from modulos.mantenimiento.vista import VistaMantenimiento


class ControladorMantenimiento:
    """Conecta la vista tecnica con el servicio."""

    def __init__(
        self,
        servicio_mantenimiento: ServicioMantenimiento,
        vista_mantenimiento: VistaMantenimiento,
    ) -> None:
        self.servicio_mantenimiento = servicio_mantenimiento
        self.vista_mantenimiento = vista_mantenimiento
        self._callback_volver: Callable[[], None] | None = None
        self.vista_mantenimiento.volver_solicitado.connect(self._manejar_volver)

    def mostrar_panel(self) -> None:
        self.vista_mantenimiento.mostrar_estado(
            self.servicio_mantenimiento.obtener_estado()
        )

    def configurar_callback_volver(self, callback_volver: Callable[[], None]) -> None:
        self._callback_volver = callback_volver

    def _manejar_volver(self) -> None:
        if self._callback_volver is not None:
            self._callback_volver()

