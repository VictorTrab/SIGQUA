"""Controladores del módulo de reportes."""

from __future__ import annotations

from modulos.reportes.servicio import ServicioReportes


class ControladorReportes:
    """Conecta la vista con los servicios del módulo."""

    def __init__(self, servicio_reportes: ServicioReportes):
        self.servicio_reportes = servicio_reportes
