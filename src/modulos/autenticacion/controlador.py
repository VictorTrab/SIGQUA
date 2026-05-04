"""Controladores del módulo de autenticación."""

from __future__ import annotations

from modulos.autenticacion.servicio import ServicioAutenticacion


class ControladorAutenticacion:
    """Conecta la vista con los servicios del módulo."""

    def __init__(self, servicio_autenticacion: ServicioAutenticacion):
        self.servicio_autenticacion = servicio_autenticacion
