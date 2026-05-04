"""Servicios del módulo de configuración."""

from __future__ import annotations

from modulos.configuracion.repositorio import RepositorioConfiguracion


class ServicioConfiguracion:
    """Orquesta la lógica de negocio del módulo."""

    def __init__(self, repositorio_configuracion: RepositorioConfiguracion):
        self.repositorio_configuracion = repositorio_configuracion
