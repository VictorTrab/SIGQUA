"""Controladores del módulo de casas."""

from __future__ import annotations

from modulos.casas.servicio import ServicioCasas


class ControladorCasas:
    """Conecta la vista con los servicios del módulo."""

    def __init__(self, servicio_casas: ServicioCasas):
        self.servicio_casas = servicio_casas
