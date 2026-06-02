"""Modulo de planes de pago."""

from __future__ import annotations

from importlib import import_module

__all__ = [
    "ControladorPlanesPago",
    "RepositorioPlanesPagoSQLite",
    "ServicioPlanesPago",
    "VistaPlanesPago",
]


def __getattr__(nombre: str):
    if nombre == "ControladorPlanesPago":
        return import_module("modulos.planes_pago.controlador").ControladorPlanesPago
    if nombre == "RepositorioPlanesPagoSQLite":
        return import_module("modulos.planes_pago.repositorio").RepositorioPlanesPagoSQLite
    if nombre == "ServicioPlanesPago":
        return import_module("modulos.planes_pago.servicio").ServicioPlanesPago
    if nombre == "VistaPlanesPago":
        return import_module("modulos.planes_pago.vista").VistaPlanesPago
    raise AttributeError(f"module 'modulos.planes_pago' has no attribute {nombre!r}")
