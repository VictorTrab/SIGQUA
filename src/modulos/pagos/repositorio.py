"""Contratos de persistencia del módulo de pagos."""

from __future__ import annotations

from typing import Protocol

from modulos.pagos.entidades import Pago


class RepositorioPagos(Protocol):
    """Define el acceso persistente requerido por pagos."""

    def obtener_por_identificador(self, identificador: int) -> Pago | None:
        """Obtiene un pago por su identificador."""
