"""Controlador del modulo de morosidad."""

from __future__ import annotations

from modulos.morosidad.servicio import ServicioMorosidad
from modulos.morosidad.vista import VistaMorosidad


class ControladorMorosidad:
    """Conecta la vista de morosidad con sus consultas."""

    def __init__(
        self,
        servicio_morosidad: ServicioMorosidad,
        vista_morosidad: VistaMorosidad,
    ) -> None:
        self.servicio_morosidad = servicio_morosidad
        self.vista_morosidad = vista_morosidad
        self.vista_morosidad.buscar_solicitado.connect(self.mostrar)

    def mostrar(self, filtro: str = "") -> None:
        estado = self.servicio_morosidad.obtener_estado(filtro=filtro)
        self.vista_morosidad.mostrar_estado(
            estado,
            self.servicio_morosidad.formatear_moneda,
            self.servicio_morosidad.formatear_fecha,
        )
