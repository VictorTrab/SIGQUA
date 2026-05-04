"""Contratos de persistencia del módulo de abonados."""

from __future__ import annotations

from typing import Protocol

from modulos.abonados.entidades import Abonado


class RepositorioAbonados(Protocol):
    """Define el acceso persistente requerido por abonados."""

    def obtener_por_identificador(self, identificador: int) -> Abonado | None:
        """Obtiene un abonado por su identificador."""
