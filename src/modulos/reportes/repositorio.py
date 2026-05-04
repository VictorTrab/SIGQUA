"""Contratos de persistencia del módulo de reportes."""

from __future__ import annotations

from typing import Protocol

from modulos.reportes.entidades import Reporte


class RepositorioReportes(Protocol):
    """Define el acceso persistente requerido por reportes."""

    def obtener_por_identificador(self, identificador: int) -> Reporte | None:
        """Obtiene un reporte por su identificador."""
