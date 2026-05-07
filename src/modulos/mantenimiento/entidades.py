"""Entidades del modulo de mantenimiento."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class EstadoMantenimiento:
    """Resumen visible del estado tecnico del sistema."""

    total_respaldos: int
    total_eventos_tecnicos: int
    ultimo_evento: str

