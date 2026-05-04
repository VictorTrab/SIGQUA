"""Entidades base del módulo de usuarios."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class UsuarioSistema:
    """Representa un usuario del sistema."""

    identificador: int | None = None
    nombre_usuario: str = ""
