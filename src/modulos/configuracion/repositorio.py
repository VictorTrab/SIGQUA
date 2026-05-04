"""Contratos de persistencia del módulo de configuración."""

from __future__ import annotations

from typing import Protocol

from modulos.configuracion.entidades import ParametroConfiguracion


class RepositorioConfiguracion(Protocol):
    """Define el acceso persistente requerido por configuración."""

    def obtener_por_clave(self, clave: str) -> ParametroConfiguracion | None:
        """Obtiene un parámetro de configuración por su clave."""
