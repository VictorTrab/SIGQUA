"""Entidades del modulo de morosidad."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class FilaMorosidad:
    """Resumen de deuda vencida por casa."""

    casa_id: int
    casa_codigo: str
    abonado_nombre: str
    abonado_dni: str
    barrio_nombre: str
    estado_servicio: str
    meses_vencidos: int
    deuda_base_centavos: int
    recargo_mora_centavos: int
    deuda_total_centavos: int
    vencimiento_mas_antiguo: str


@dataclass(slots=True)
class ResumenMorosidad:
    """Indicadores principales de morosidad."""

    total_casas: int
    total_meses_vencidos: int
    deuda_base_centavos: int
    recargo_mora_centavos: int
    deuda_total_centavos: int


@dataclass(slots=True)
class EstadoMorosidad:
    """Estado completo para renderizar morosidad."""

    resumen: ResumenMorosidad
    filas: tuple[FilaMorosidad, ...]
