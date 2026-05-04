"""Contratos de persistencia del módulo de autenticación."""

from __future__ import annotations

from typing import Protocol

from modulos.autenticacion.entidades import CredencialesUsuario


class RepositorioAutenticacion(Protocol):
    """Define el acceso persistente requerido por autenticación."""

    def obtener_credenciales(self, nombre_usuario: str) -> CredencialesUsuario | None:
        """Obtiene credenciales por nombre de usuario."""
