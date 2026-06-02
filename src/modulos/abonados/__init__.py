"""Modulo de abonados."""

from __future__ import annotations

from importlib import import_module

__all__ = [
    "Abonado",
    "ControladorAbonados",
    "FILTRO_ABONADOS_CON_MORA",
    "FILTRO_ABONADOS_CON_PLAN",
    "FILTRO_ABONADOS_SIN_MORA",
    "FILTRO_ABONADOS_TODOS",
    "FormularioAbonado",
    "OpcionBarrio",
    "PaginaAbonados",
    "RepositorioAbonados",
    "RepositorioAbonadosSQLite",
    "ResumenAbonados",
    "ResultadoGestionAbonados",
    "ServicioAbonados",
    "VistaAbonados",
]


def __getattr__(nombre: str):
    if nombre in {
        "Abonado",
        "FILTRO_ABONADOS_CON_MORA",
        "FILTRO_ABONADOS_CON_PLAN",
        "FILTRO_ABONADOS_SIN_MORA",
        "FILTRO_ABONADOS_TODOS",
        "FormularioAbonado",
        "OpcionBarrio",
        "PaginaAbonados",
        "ResumenAbonados",
        "ResultadoGestionAbonados",
    }:
        return getattr(import_module("modulos.abonados.entidades"), nombre)
    if nombre == "ControladorAbonados":
        return import_module("modulos.abonados.controlador").ControladorAbonados
    if nombre in {"RepositorioAbonados", "RepositorioAbonadosSQLite"}:
        return getattr(import_module("modulos.abonados.repositorio"), nombre)
    if nombre == "ServicioAbonados":
        return import_module("modulos.abonados.servicio").ServicioAbonados
    if nombre == "VistaAbonados":
        return import_module("modulos.abonados.vista").VistaAbonados
    raise AttributeError(f"module 'modulos.abonados' has no attribute {nombre!r}")
