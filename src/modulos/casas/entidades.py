"""Entidades base del módulo de casas."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Casa:
    """Representa una casa administrada por el sistema."""

    identificador: int | None = None
    direccion_referencial: str = ""
