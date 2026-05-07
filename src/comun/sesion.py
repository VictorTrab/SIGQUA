"""Estado compartido de sesion para la aplicacion."""

from __future__ import annotations

from dataclasses import dataclass

from modulos.autenticacion.entidades import UsuarioAutenticado


@dataclass(slots=True)
class SesionAplicacion:
    """Representa la sesion activa en memoria."""

    usuario: UsuarioAutenticado
    token_sesion: str
