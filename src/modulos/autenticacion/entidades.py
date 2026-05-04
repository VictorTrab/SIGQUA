"""Entidades base del módulo de autenticación."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class CredencialesUsuario:
    """Representa credenciales mínimas de autenticación."""

    nombre_usuario: str = ""
    contrasena_plana: str = ""
