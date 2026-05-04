"""Servicios del módulo de planes de pago."""

from __future__ import annotations

from modulos.planes_pago.repositorio import RepositorioPlanesPago


class ServicioPlanesPago:
    """Orquesta la lógica de negocio del módulo."""

    def __init__(self, repositorio_planes_pago: RepositorioPlanesPago):
        self.repositorio_planes_pago = repositorio_planes_pago
