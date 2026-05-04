"""Entidades base del módulo de pagos."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Pago:
    """Representa un pago registrado en el sistema."""

    identificador: int | None = None
    monto: float = 0.0
