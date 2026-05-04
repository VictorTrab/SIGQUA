"""Entidades base del módulo de abonados."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Abonado:
    """Representa un abonado del sistema."""

    identificador: int | None = None
    nombre_completo: str = ""
