"""Controladores del módulo de planes de pago."""

from __future__ import annotations

from modulos.planes_pago.servicio import ServicioPlanesPago


class ControladorPlanesPago:
    """Conecta la vista con los servicios del módulo."""

    def __init__(self, servicio_planes_pago: ServicioPlanesPago):
        self.servicio_planes_pago = servicio_planes_pago
