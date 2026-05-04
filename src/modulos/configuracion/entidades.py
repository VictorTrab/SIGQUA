"""Entidades base del módulo de configuración."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ParametroConfiguracion:
    """Representa un parámetro configurable del sistema."""

    clave: str = ""
    valor: str = ""
