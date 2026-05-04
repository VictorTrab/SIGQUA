"""Contratos de persistencia del módulo de casas."""

from __future__ import annotations

from typing import Protocol

from modulos.casas.entidades import Casa


class RepositorioCasas(Protocol):
    """Define el acceso persistente requerido por casas."""

    def obtener_por_identificador(self, identificador: int) -> Casa | None:
        """Obtiene una casa por su identificador."""
