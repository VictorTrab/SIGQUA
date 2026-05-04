"""Controladores del módulo de abonados."""

from __future__ import annotations

from modulos.abonados.servicio import ServicioAbonados


class ControladorAbonados:
    """Conecta la vista con los servicios del módulo."""

    def __init__(self, servicio_abonados: ServicioAbonados):
        self.servicio_abonados = servicio_abonados
