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
    modulos: tuple[ModuloNavegacion, ...]
    puede_abrir_mantenimiento: bool = False

