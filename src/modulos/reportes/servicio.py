"""Servicios del módulo de reportes."""

from __future__ import annotations

from modulos.reportes.repositorio import RepositorioReportes


class ServicioReportes:
    """Orquesta la lógica de negocio del módulo."""

    def __init__(self, repositorio_reportes: RepositorioReportes):
        self.repositorio_reportes = repositorio_reportes
