"""Entidades del modulo de reportes."""

from __future__ import annotations

from dataclasses import dataclass


REPORTE_ABONADOS_ESTADO = "abonados_estado"
REPORTE_CASAS_ESTADO = "casas_estado"
REPORTE_DEUDA_ACTIVA = "deuda_activa"
REPORTE_HISTORIAL_PAGOS = "historial_pagos"
REPORTE_INGRESOS_DIARIOS = "ingresos_diarios"


@dataclass(slots=True)
class IndicadorReporte:
    """Indicador agregado para el tablero de reportes."""

    titulo: str
    valor: str
    detalle: str


@dataclass(slots=True)
class TablaReporte:
    """Tabla de reporte renderizable por la vista."""

    codigo: str
    titulo: str
    descripcion: str
    columnas: tuple[str, ...]
    filas: tuple[tuple[str, ...], ...]


@dataclass(slots=True)
class FiltrosReportes:
    """Rango simple aplicado a reportes con componente temporal."""

    fecha_desde: str = ""
    fecha_hasta: str = ""


@dataclass(slots=True)
class EstadoReportes:
    """Estado completo de reportes basicos."""

    indicadores: tuple[IndicadorReporte, ...]
    tablas: tuple[TablaReporte, ...]
    filtros: FiltrosReportes
