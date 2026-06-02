"""Modulo de pagos."""

from __future__ import annotations

from importlib import import_module

__all__ = [
    "CargoPago",
    "CasaPago",
    "ComprobantePago",
    "ConfiguracionReciboPago",
    "ControladorPagos",
    "EstadoModuloPagos",
    "FormularioPago",
    "MetodoPago",
    "RepositorioPagosSQLite",
    "ResumenConfirmacionPago",
    "ResumenDeudaPago",
    "ResultadoPago",
    "ServicioPagos",
    "VistaPagos",
]


def __getattr__(nombre: str):
    if nombre in {
        "CargoPago",
        "CasaPago",
        "ComprobantePago",
        "ConfiguracionReciboPago",
        "EstadoModuloPagos",
        "FormularioPago",
        "MetodoPago",
        "ResumenConfirmacionPago",
        "ResumenDeudaPago",
        "ResultadoPago",
    }:
        return getattr(import_module("modulos.pagos.entidades"), nombre)
    if nombre == "ControladorPagos":
        return import_module("modulos.pagos.controlador").ControladorPagos
    if nombre == "RepositorioPagosSQLite":
        return import_module("modulos.pagos.repositorio").RepositorioPagosSQLite
    if nombre == "ServicioPagos":
        return import_module("modulos.pagos.servicio").ServicioPagos
    if nombre == "VistaPagos":
        return import_module("modulos.pagos.vista").VistaPagos
    raise AttributeError(f"module 'modulos.pagos' has no attribute {nombre!r}")
