"""Impresion termica ESC/POS compartida por SIGQUA."""

from comun.impresion_termica.entidades import (
    ConfiguracionImpresoraTermica,
    ResultadoImpresionTicket,
)
from comun.impresion_termica.renderizador import RenderizadorTicketEscpos
from comun.impresion_termica.transporte_windows import TransporteWindowsRawEscpos

__all__ = [
    "ConfiguracionImpresoraTermica",
    "RenderizadorTicketEscpos",
    "ResultadoImpresionTicket",
    "TransporteWindowsRawEscpos",
]
