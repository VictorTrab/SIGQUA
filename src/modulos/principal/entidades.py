"""Entidades del modulo principal."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class MetricaDashboard:
    """Representa una metrica visible en el dashboard."""

    codigo: str
    titulo: str
    valor: str
    detalle: str = ""


@dataclass(slots=True)
class PuntoSerieDashboard:
    """Punto simple para series temporales del dashboard."""

    etiqueta: str
    valor: float


@dataclass(slots=True)
class CategoriaDashboard:
    """Valor agrupado por categoria para analitica del dashboard."""

    etiqueta: str
    valor: float


@dataclass(slots=True)
class InsightDashboard:
    """Resumen ejecutivo compacto para la pantalla de inicio."""

    titulo: str
    valor: str
    detalle: str


@dataclass(slots=True)
class AnaliticaDashboard:
    """Agrupa las series y distribuciones del dashboard."""

    recaudacion_mensual: tuple[PuntoSerieDashboard, ...]
    deuda_por_barrio: tuple[CategoriaDashboard, ...]
    estados_servicio: tuple[CategoriaDashboard, ...]
    antiguedad_deuda: tuple[CategoriaDashboard, ...]
    insights: tuple[InsightDashboard, ...]


@dataclass(slots=True)
class ModuloNavegacion:
    """Describe un modulo navegable del shell principal."""

    codigo: str
    titulo: str
    descripcion: str
    icono: str
    permiso_requerido: str | None = None
    es_tecnico: bool = False


@dataclass(slots=True)
class EstadoModuloPrincipal:
    """Estado inicial del shell principal para el usuario activo."""

    nombre_usuario: str
    nombre_completo: str
    perfil: str
    metricas: tuple[MetricaDashboard, ...]
    analitica: AnaliticaDashboard
    modulos: tuple[ModuloNavegacion, ...]
