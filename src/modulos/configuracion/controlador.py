"""Controladores del módulo de configuración."""

from __future__ import annotations

from modulos.configuracion.servicio import ServicioConfiguracion


class ControladorConfiguracion:
    """Conecta la vista con los servicios del módulo."""

    def __init__(self, servicio_configuracion: ServicioConfiguracion):
        self.servicio_configuracion = servicio_configuracion
