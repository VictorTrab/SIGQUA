"""Entidades base del módulo de reportes."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Reporte:
    """Representa un reporte configurable del sistema."""

    identificador: int | None = None
    nombre: str = ""
