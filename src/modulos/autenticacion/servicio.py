"""Servicios del módulo de autenticación."""

from __future__ import annotations

from modulos.autenticacion.repositorio import RepositorioAutenticacion


class ServicioAutenticacion:
    """Orquesta la lógica de negocio del módulo."""

    def __init__(self, repositorio_autenticacion: RepositorioAutenticacion):
        self.repositorio_autenticacion = repositorio_autenticacion
