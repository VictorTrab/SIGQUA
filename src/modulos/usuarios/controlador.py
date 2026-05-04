"""Controladores del módulo de usuarios."""

from __future__ import annotations

from modulos.usuarios.servicio import ServicioUsuarios


class ControladorUsuarios:
    """Conecta la vista con los servicios del módulo."""

    def __init__(self, servicio_usuarios: ServicioUsuarios):
        self.servicio_usuarios = servicio_usuarios
