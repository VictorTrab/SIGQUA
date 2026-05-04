"""Servicios del módulo de usuarios."""

from __future__ import annotations

from modulos.usuarios.repositorio import RepositorioUsuarios


class ServicioUsuarios:
    """Orquesta la lógica de negocio del módulo."""

    def __init__(self, repositorio_usuarios: RepositorioUsuarios):
        self.repositorio_usuarios = repositorio_usuarios
