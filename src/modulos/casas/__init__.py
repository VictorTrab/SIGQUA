"""Modulo de casas."""

from __future__ import annotations

from importlib import import_module

__all__ = [
    "Casa",
    "ControladorCasas",
    "DetalleCasa",
    "FILTRO_CASAS_ACTIVAS",
    "FILTRO_CASAS_CON_MORA",
    "FILTRO_CASAS_SIN_PROPIETARIO",
    "FILTRO_CASAS_SUSPENDIDAS",
    "FILTRO_CASAS_TODAS",
    "FormularioCasa",
    "HistorialPropietarioCasa",
    "OpcionAbonado",
    "OpcionBarrio",
    "PaginaCasas",
    "PlanActivoCasa",
    "RepositorioCasas",
    "RepositorioCasasSQLite",
    "ResumenCasas",
    "ResultadoGestionCasas",
    "ServicioCasas",
    "VistaCasas",
]


def __getattr__(nombre: str):
    if nombre in {
        "Casa",
        "DetalleCasa",
        "FILTRO_CASAS_ACTIVAS",
        "FILTRO_CASAS_CON_MORA",
        "FILTRO_CASAS_SIN_PROPIETARIO",
        "FILTRO_CASAS_SUSPENDIDAS",
        "FILTRO_CASAS_TODAS",
        "FormularioCasa",
        "HistorialPropietarioCasa",
        "OpcionAbonado",
        "OpcionBarrio",
        "PaginaCasas",
        "PlanActivoCasa",
        "ResumenCasas",
        "ResultadoGestionCasas",
    }:
        return getattr(import_module("modulos.casas.entidades"), nombre)
    if nombre == "ControladorCasas":
        return import_module("modulos.casas.controlador").ControladorCasas
    if nombre in {"RepositorioCasas", "RepositorioCasasSQLite"}:
        return getattr(import_module("modulos.casas.repositorio"), nombre)
    if nombre == "ServicioCasas":
        return import_module("modulos.casas.servicio").ServicioCasas
    if nombre == "VistaCasas":
        return import_module("modulos.casas.vista").VistaCasas
    raise AttributeError(f"module 'modulos.casas' has no attribute {nombre!r}")
