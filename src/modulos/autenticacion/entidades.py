"""Entidades del modulo de autenticacion."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class CredencialesUsuario:
    """Representa credenciales minimas de autenticacion."""

    nombre_usuario: str = ""
    contrasena_plana: str = ""


@dataclass(slots=True)
class UsuarioRegistroAutenticacion:
    """Representa un usuario persistido con sus datos de autenticacion."""

    identificador: int
    nombre_usuario: str
    nombre_completo: str
    correo: str
    estado: str
    contrasena_hash: str
    es_tecnico: bool = False
    es_oculto: bool = False
    requiere_cambio_contrasena: bool = False
    contrasena_temporal_expira_en: str | None = None
    intentos_fallidos: int = 0
    bloqueado_hasta: str | None = None
    roles: tuple[str, ...] = ()
    permisos: frozenset[str] = frozenset()


@dataclass(slots=True)
class UsuarioAutenticado:
    """Representa un usuario autenticado listo para la capa de UI."""

    identificador: int
    nombre_usuario: str
    nombre_completo: str
    correo: str
    estado: str
    es_tecnico: bool = False
    es_oculto: bool = False
    requiere_cambio_contrasena: bool = False
    contrasena_temporal_expira_en: str | None = None
    roles: tuple[str, ...] = ()
    permisos: frozenset[str] = frozenset()

    @classmethod
    def desde_registro(
        cls,
        usuario_registro: UsuarioRegistroAutenticacion,
    ) -> "UsuarioAutenticado":
        return cls(
            identificador=usuario_registro.identificador,
            nombre_usuario=usuario_registro.nombre_usuario,
            nombre_completo=usuario_registro.nombre_completo,
            correo=usuario_registro.correo,
            estado=usuario_registro.estado,
            es_tecnico=usuario_registro.es_tecnico,
            es_oculto=usuario_registro.es_oculto,
            requiere_cambio_contrasena=usuario_registro.requiere_cambio_contrasena,
            contrasena_temporal_expira_en=usuario_registro.contrasena_temporal_expira_en,
            roles=usuario_registro.roles,
            permisos=usuario_registro.permisos,
        )

    def tiene_permiso(self, codigo_permiso: str) -> bool:
        return codigo_permiso in self.permisos

    def es_superadministrador(self) -> bool:
        return "SUPERADMINISTRADOR" in self.roles


@dataclass(slots=True)
class ResultadoOperacion:
    """Resultado generico para operaciones del modulo."""

    exito: bool
    mensaje: str
    codigo: str = ""


@dataclass(slots=True)
class ResultadoLogin(ResultadoOperacion):
    """Resultado especifico del inicio de sesion."""

    usuario: UsuarioAutenticado | None = None
    token_sesion: str | None = None
    requiere_cambio_contrasena: bool = False


@dataclass(slots=True)
class SesionIniciada:
    """Representa una sesion autenticada lista para la app."""

    usuario: UsuarioAutenticado
    token_sesion: str
