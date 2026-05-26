"""Entidades tecnicas para impresion termica ESC/POS."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ConfiguracionImpresoraTermica:
    """Parametros fisicos requeridos para enviar bytes ESC/POS."""

    nombre_impresora: str
    ancho_papel_mm: int = 80
    corte_automatico: bool = True
    codigo_pagina: str = "cp850"


@dataclass(slots=True)
class ResultadoImpresionTicket:
    """Resultado tecnico del envio de un ticket a la impresora."""

    exito: bool
    mensaje: str
    codigo: str = "OK"
