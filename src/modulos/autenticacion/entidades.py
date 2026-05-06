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


@dataclass(slots=True)
class UsuarioAutenticado:
    """Representa un usuario autenticado listo para la capa de UI."""

    identificador: int
    nombre_usuario: str
    nombre_completo: str
    correo: str
    estado: str

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
        )


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


@dataclass(slots=True)
class TokenRecuperacion:
    """Representa un token persistido de recuperacion de contrasena."""

    identificador: int
    usuario_id: int
    token: str
    expira_en: str
    usado_en: str | None = None


@dataclass(slots=True)
class ResultadoValidacionToken(ResultadoOperacion):
    """Resultado de validar un token de recuperacion."""

    token_recuperacion: TokenRecuperacion | None = None


@dataclass(slots=True)
class ResultadoRecuperacion(ResultadoOperacion):
    """Resultado de solicitar recuperacion de contrasena."""

    token_prueba: str | None = None
