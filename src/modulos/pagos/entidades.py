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

ESTADO_VISUAL_PAGO_OK = "OK"
ESTADO_VISUAL_PAGO_BLOQUEADO = "BLOQUEADO"


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
    estado_administrativo: str
    motivo_estado_administrativo: str
    ha_tenido_servicio_activo: bool
    meses_pendientes: int
    meses_vencidos: int
    deuda_total_centavos: int
    deuda_vencida_centavos: int
    tiene_plan_activo: bool = False


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
    fecha_activacion: str = ""
    monto_conexion_centavos: int = 0
    monto_reconexion_centavos: int = 0
    multa_corte_centavos: int = 0
    plan_pago_id: int | None = None
    cuotas_plan_pago_ids: tuple[int, ...] = ()


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
    fecha_activacion: str = ""
    plan_pago_id: int | None = None


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
    barrio_nombre: str = ""
    direccion_casa: str = ""
    metodo_pago: str = ""
    referencia: str = ""
    usuario_registro: str = ""
    total_pagado_centavos: int = 0
    saldo_posterior_centavos: int = 0
    detalles: tuple[str, ...] = ()
    formato_salida: str = "HTML"
    ruta_archivo: str = ""


@dataclass(slots=True)
class ConfiguracionReciboPago:
    """Configuracion visible del recibo termico tomada desde parametros reales."""

    nombre_junta: str
    telefono_junta: str
    correo_junta: str
    direccion_junta: str
    identificador_fiscal: str
    sitio_web: str
    mensaje_contacto: str
    titulo_documento: str
    subtitulo_documento: str
    texto_legal_superior: str
    texto_pie: str
    texto_legal_inferior: str
    etiqueta_copia: str
    mostrar_correo: bool
    mostrar_telefono: bool
    mostrar_direccion: bool
    mostrar_identificador_fiscal: bool
    firma_habilitada: bool
    firma_nombre: str
    firma_cargo: str
    firma_identificador: str
    firma_texto_apoyo: str
    abrir_pdf_automaticamente: bool = True
    imprimir_pdf_automaticamente: bool = False


@dataclass(slots=True)
class DiagnosticoPagoMensual:
    """Estado visual y operativo de una casa dentro del flujo mensual."""

    casa_id: int
    permite_continuar: bool
    estado_visual: str
    mensaje_diagnostico: str
    alertas: tuple[str, ...] = ()


@dataclass(slots=True)
class DiagnosticoPagoActivacion:
    """Estado visual y operativo de una casa dentro de conexión o reconexión."""

    casa_id: int
    tipo_pago: str
    clasificacion: str
    permite_continuar: bool
    estado_visual: str
    mensaje_diagnostico: str
    alertas: tuple[str, ...] = ()


@dataclass(slots=True)
class CuotaPlanCobrable:
    """Cuota de plan disponible para cobro dentro del flujo de pagos."""

    cuota_id: int
    plan_pago_id: int
    numero_cuota: int
    fecha_vencimiento: str
    estado: str
    saldo_pendiente_centavos: int


@dataclass(slots=True)
class DiagnosticoPagoPlan:
    """Estado visual y operativo del plan activo dentro del flujo de cuotas."""

    casa_id: int
    cantidad_planes_activos: int
    plan_pago_id: int | None
    codigo_plan: str
    tipo_plan: str
    estado_plan: str
    cuotas_pendientes: int
    cuotas_en_mora: int
    saldo_vivo_centavos: int
    cuotas_cobrables: tuple[CuotaPlanCobrable, ...]
    permite_continuar: bool
    estado_visual: str
    mensaje_diagnostico: str
    alertas: tuple[str, ...] = ()


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
    cobrar_mensualidad_prorrateada_activacion: bool = False
    abrir_pdf_automaticamente: bool = True
    imprimir_pdf_automaticamente: bool = False
