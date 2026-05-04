"""Contratos de persistencia del módulo de planes de pago."""

from __future__ import annotations

from typing import Protocol

from modulos.planes_pago.entidades import PlanPago


class RepositorioPlanesPago(Protocol):
    """Define el acceso persistente requerido por planes de pago."""

    def obtener_por_identificador(self, identificador: int) -> PlanPago | None:
        """Obtiene un plan de pago por su identificador."""
