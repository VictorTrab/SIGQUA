"""DTOs limpios para documentos operativos de deuda."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LineaDetalleEstadoCuenta:
    """Linea vencida incluida en el documento de deuda."""

    descripcion: str
    fecha_vencimiento: str
    monto: str


@dataclass(frozen=True, slots=True)
class CasaEstadoCuenta:
    """Bloque de deuda por casa dentro del estado de cuenta."""

    casa_codigo: str
    barrio_nombre: str
    direccion_casa: str
    estado_servicio: str
    meses_vencidos: int
    dias_en_mora: int
    prioridad: str
    vencimiento_mas_antiguo: str
    deuda_base: str
    recargo_mora: str
    deuda_total: str
    lineas_detalle: tuple[LineaDetalleEstadoCuenta, ...]
    estado_aviso_cobro: str = "SIN_AVISO"
    fecha_ultimo_aviso: str = ""


@dataclass(frozen=True, slots=True)
class DTOEstadoCuenta:
    """Documento operativo de deuda listo para generar en PDF."""

    titulo: str
    subtitulo: str
    lineas_encabezado: tuple[str, ...]
    abonado_nombre: str
    abonado_dni: str
    generado_en: str
    observacion: str
    casas: tuple[CasaEstadoCuenta, ...]
    total_deuda_base: str
    total_recargo_mora: str
    total_general: str
    firma_habilitada: bool
    firma_texto_linea: str
