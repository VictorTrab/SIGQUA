"""DTOs limpios para comprobantes PDF."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LineaDetalleComprobantePago:
    """Linea del detalle pagado lista para maquetacion PDF."""

    descripcion: str
    monto: str


@dataclass(frozen=True, slots=True)
class DTOComprobantePago:
    """Representacion limpia de un comprobante para el generador PDF."""

    numero_comprobante: str
    lineas_encabezado: tuple[str, ...]
    titulo_documento: str
    subtitulo_documento: str
    texto_legal_superior: str
    texto_pie: str
    texto_legal_inferior: str
    etiqueta_copia: str
    fecha: str
    hora: str
    tipo_comprobante: str
    casa_codigo: str
    abonado_nombre: str
    abonado_dni: str
    barrio_nombre: str
    direccion_casa: str
    metodo_pago: str
    referencia: str
    usuario_registro: str
    lineas_detalle: tuple[LineaDetalleComprobantePago, ...]
    total_pagado: str
    firma_habilitada: bool
    firma_texto_linea: str
