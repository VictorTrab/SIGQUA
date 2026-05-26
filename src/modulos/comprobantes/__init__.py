"""Modulo interno de comprobantes termicos."""

from modulos.comprobantes.entidades import (
    COPIA_AMBAS,
    COPIA_JUNTA,
    COPIA_ORIGINAL,
    ConfiguracionComprobanteTermico,
    ResultadoComprobante,
)
from modulos.comprobantes.repositorio import RepositorioComprobantesSQLite
from modulos.comprobantes.servicio import ServicioComprobantes

__all__ = [
    "COPIA_AMBAS",
    "COPIA_JUNTA",
    "COPIA_ORIGINAL",
    "ConfiguracionComprobanteTermico",
    "RepositorioComprobantesSQLite",
    "ResultadoComprobante",
    "ServicioComprobantes",
]
