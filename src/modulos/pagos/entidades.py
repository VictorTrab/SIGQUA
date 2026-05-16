"""Entidades del modulo de pagos."""

from __future__ import annotations

from dataclasses import dataclass


TIPO_PAGO_MENSUALIDAD = "MENSUALIDAD"
TIPO_PAGO_PLAN = "PLAN_PAGO"
TIPO_PAGO_CONEXION = "CONEXION"
TIPO_PAGO_RECONEXION = "RECONEXION"

TIPOS_PAGO_VALIDOS = (
    TIPO_PAGO_MENSUALIDAD,
    TIPO_PAGO_PLAN,
    TIPO_PAGO_CONEXION,
    TIPO_PAGO_RECONEXION,
)


@dataclass(slots=True)
class MetodoPago:
    """Metodo de pago disponible desde el catalogo oficial."""

    identificador: int
    codigo: str
    nombre: str
    requiere_referencia: bool = False


@dataclass(slots=True)
class CasaPago:
    """Casa cobrable con su abonado responsable y deuda actual."""

    casa_id: int
    casa_codigo: str
    abonado_id: int
    abonado_nombre: str
    abonado_dni: str
    abonado_estado: str
    barrio_nombre: str
    estado_servicio: str
    meses_pendientes: int
    meses_vencidos: int
    deuda_total_centavos: int
    deuda_vencida_centavos: int


@dataclass(slots=True)
class ResumenDeudaPago:
    """Totales de deuda usados para validar reglas antes de cobrar."""

    deuda_total_centavos: int
    deuda_mensual_centavos: int
    deuda_vencida_centavos: int
    deuda_vencida_no_mensual_centavos: int


@dataclass(slots=True)
class CargoPago:
    """Cargo pendiente que puede cubrirse con un pago."""

    identificador: int
    casa_id: int
    abonado_id: int
    periodo_id: int | None
    periodo_anio: int | None
    periodo_mes: int | None
    periodo_nombre: str
    concepto_codigo: str
    descripcion: str
    saldo_pendiente_centavos: int
    fecha_vencimiento: str
    estado: str


@dataclass(slots=True)
class DetalleAplicacionPago:
    """Linea calculada para aplicar un pago antes de persistirlo."""

    cargo_id: int | None
    periodo_id: int | None
    periodo_anio: int | None
    periodo_mes: int | None
    periodo_nombre: str
    concepto_codigo: str
    descripcion: str
    monto_centavos: int
    etiqueta: str
    es_adelantado: bool = False


@dataclass(slots=True)
class FormularioPago:
    """Datos capturados desde la UI para confirmar un pago."""

    casa_id: int | None
    tipo_pago: str
    cantidad_meses: int
    metodo_pago_id: int | None
    referencia: str = ""
    observaciones: str = ""


@dataclass(slots=True)
class ResumenConfirmacionPago:
    """Resumen calculado antes de registrar un pago definitivo."""

    casa: CasaPago
    tipo_pago: str
    metodo_pago: MetodoPago
    detalles: tuple[DetalleAplicacionPago, ...]
    saldo_anterior_centavos: int
    total_pago_centavos: int
    saldo_posterior_centavos: int
    referencia: str
    observaciones: str


@dataclass(slots=True)
class ComprobantePago:
    """Comprobante generado para un pago confirmado."""

    pago_id: int
    numero_comprobante: str
    tipo_comprobante: str
    generado_en: str
    casa_codigo: str = ""
    abonado_nombre: str = ""
    abonado_dni: str = ""
    metodo_pago: str = ""
    referencia: str = ""
    total_pagado_centavos: int = 0
    saldo_posterior_centavos: int = 0
    detalles: tuple[str, ...] = ()
    formato_salida: str = "PDF"
    ruta_archivo: str = ""


@dataclass(slots=True)
class ResultadoPago:
    """Resultado de una operacion del modulo de pagos."""

    exito: bool
    mensaje: str
    codigo: str = "OK"
    comprobante: ComprobantePago | None = None


@dataclass(slots=True)
class HistorialPago:
    """Fila del historial reciente de pagos."""

    pago_id: int
    numero_comprobante: str
    tipo_pago: str
    abonado_nombre: str
    casa_codigo: str
    metodo_pago: str
    total_pagado_centavos: int
    fecha_pago: str


@dataclass(slots=True)
class EstadoModuloPagos:
    """Estado completo para renderizar la pantalla de pagos."""

    casas: tuple[CasaPago, ...]
    metodos_pago: tuple[MetodoPago, ...]
