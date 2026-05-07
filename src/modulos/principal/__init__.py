"""Modulo principal."""

from modulos.principal.controlador import ControladorModuloPrincipal
from modulos.principal.repositorio import (
    RepositorioModuloPrincipal,
    RepositorioModuloPrincipalMemoria,
)
from modulos.principal.servicio import ServicioModuloPrincipal
from modulos.principal.vista import VistaModuloPrincipal

__all__ = [
    "ControladorModuloPrincipal",
    "RepositorioModuloPrincipal",
    "RepositorioModuloPrincipalMemoria",
    "ServicioModuloPrincipal",
    "VistaModuloPrincipal",
]
