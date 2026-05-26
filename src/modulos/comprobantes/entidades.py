"""Entidades del modulo interno de comprobantes."""

from __future__ import annotations

from dataclasses import dataclass


COPIA_ORIGINAL = "ORIGINAL"
COPIA_JUNTA = "JUNTA"
COPIA_AMBAS = "AMBAS"

ESTADO_IMPRESO = "IMPRESO"
ESTADO_FALLIDO = "FALLIDO"


@dataclass(slots=True)
class LineaTicketComprobante:
    """Linea economica del detalle impreso."""

    descripcion: str
    monto: str


@dataclass(slots=True)
class TicketComprobantePago:
    """Snapshot imprimible reconstruido desde SQLite."""

    comprobante_id: int
    pago_id: int
    lineas_encabezado: tuple[str, ...]
    numero_comprobante: str
    tipo_comprobante: str
    fecha_hora: str
    usuario_cobrador: str
    abonado_nombre: str
    abonado_dni: str
    casa_codigo: str
    barrio_nombre: str
    direccion_casa: str
    metodo_pago: str
    referencia: str
    lineas_detalle: tuple[LineaTicketComprobante, ...]
    total_pagado: str
    texto_pie: str
    firma_habilitada: bool
    firma_texto_linea: str


@dataclass(slots=True)
class ConfiguracionComprobanteTermico:
    """Configuracion operacional para tickets ESC/POS."""

    nombre_impresora: str
    ancho_papel_mm: int
    corte_automatico: bool
    codigo_pagina: str


@dataclass(slots=True)
class ResultadoComprobante:
    """Resultado operativo del modulo de comprobantes."""

    exito: bool
    mensaje: str
    codigo: str = "OK"
