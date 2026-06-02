"""Modulo de barrios."""

from __future__ import annotations

from importlib import import_module

__all__ = [
    "Barrio",
    "ControladorBarrios",
    "FILTRO_BARRIOS_CON_ABONADOS",
    "FILTRO_BARRIOS_SIN_ABONADOS",
    "FILTRO_BARRIOS_TODOS",
    "FormularioBarrio",
    "PaginaBarrios",
    "RepositorioBarrios",
    "RepositorioBarriosSQLite",
    "ResumenBarrios",
    "ResultadoGestionBarrios",
    "ServicioBarrios",
    "VistaBarrios",
]


def __getattr__(nombre: str):
    if nombre in {
        "Barrio",
        "FILTRO_BARRIOS_CON_ABONADOS",
        "FILTRO_BARRIOS_SIN_ABONADOS",
        "FILTRO_BARRIOS_TODOS",
        "FormularioBarrio",
        "PaginaBarrios",
        "ResumenBarrios",
        "ResultadoGestionBarrios",
    }:
        return getattr(import_module("modulos.barrios.entidades"), nombre)
    if nombre == "ControladorBarrios":
        return import_module("modulos.barrios.controlador").ControladorBarrios
    if nombre in {"RepositorioBarrios", "RepositorioBarriosSQLite"}:
        return getattr(import_module("modulos.barrios.repositorio"), nombre)
    if nombre == "ServicioBarrios":
        return import_module("modulos.barrios.servicio").ServicioBarrios
    if nombre == "VistaBarrios":
        return import_module("modulos.barrios.vista").VistaBarrios
    raise AttributeError(f"module 'modulos.barrios' has no attribute {nombre!r}")
