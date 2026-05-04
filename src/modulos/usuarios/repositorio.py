"""Contratos de persistencia del módulo de usuarios."""

from __future__ import annotations

from typing import Protocol

from modulos.usuarios.entidades import UsuarioSistema


class RepositorioUsuarios(Protocol):
    """Define el acceso persistente requerido por usuarios."""

    def obtener_por_identificador(self, identificador: int) -> UsuarioSistema | None:
        """Obtiene un usuario por su identificador."""
