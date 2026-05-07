"""Entidades del modulo de usuarios."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class UsuarioSistema:
    """Representa un usuario recuperado desde la persistencia."""

    identificador: int
    nombre_usuario: str
    nombre_completo: str
    correo: str
    estado: str
    es_tecnico: bool = False
    es_oculto: bool = False
    requiere_cambio_contrasena: bool = False
    intentos_fallidos: int = 0
    bloqueado_hasta: str | None = None
    roles: tuple[str, ...] = ()
    permisos: frozenset[str] = frozenset()

    def tiene_permiso(self, codigo_permiso: str) -> bool:
        return codigo_permiso in self.permisos

    def es_superadministrador(self) -> bool:
        return "SUPERADMINISTRADOR" in self.roles


@dataclass(slots=True)
class ResultadoGestionUsuarios:
    """Resultado generico de operaciones del modulo."""

    exito: bool
    mensaje: str
    codigo: str = ""

