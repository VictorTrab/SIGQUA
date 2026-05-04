"""Entidades base del módulo de planes de pago."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class PlanPago:
    """Representa un plan de pago dentro del sistema."""

    identificador: int | None = None
    descripcion: str = ""
