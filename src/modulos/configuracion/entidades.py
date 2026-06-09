"""Entidades del modulo de configuracion."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ParametroConfiguracion:
    """Representa un parametro persistido en configuracion_sistema."""

    clave: str
    valor: str
    tipo_dato: str
    categoria: str
    descripcion: str = ""
    editable: bool = True
    actualizado_en: str = ""
    actualizado_por: int | None = None
    actualizado_por_nombre: str = ""


@dataclass(slots=True)
class IdentidadEmpresa:
    """Datos operativos visibles de la empresa o institucion."""

    nombre: str
    telefono: str
    correo: str
    direccion: str
    identificador_fiscal: str = ""
    sitio_web: str = ""
    mensaje_contacto: str = ""


@dataclass(slots=True)
class ParametrosCobro:
    """Configuracion vigente para cobro, mora visual y adelantos."""

    precio_mensual_centavos: int
    mora_visible: bool
    multa_mora_automatica_activa: bool
    multa_mora_automatica_centavos: int
    corte_automatico_activo: bool
    meses_para_corte: int
    cobrar_mensualidad_prorrateada_activacion: bool
    permitir_pago_adelantado: bool
    meses_adelanto_maximo: int
    mora_leve_hasta_meses: int
    mora_media_hasta_meses: int


@dataclass(slots=True)
class FacturaConfiguracion:
    """Configuracion operativa de comprobantes termicos."""

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
    firma_texto_linea: str
    impresora_termica_nombre: str
    impresora_termica_ancho_mm: int
    impresora_termica_corte_automatico: bool
    # Compatibilidad interna: en esta version siempre se resuelve como cp850.
    impresora_termica_codigo_pagina: str
    impresora_reportes_nombre: str
    comprobantes_pendientes_impresion: int
    correlativo_actual: str
    proximo_correlativo: str
    ultimo_comprobante_emitido: str
    total_comprobantes_emitidos: int


@dataclass(slots=True)
class ReportesPdfConfiguracion:
    """Preferencias independientes para reportes administrativos PDF."""

    ruta_salida: str
    ruta_predeterminada: str
    abrir_automaticamente: bool
    firma_habilitada: bool
    firma_texto_linea: str


@dataclass(slots=True)
class OperacionConfiguracion:
    """Resumen operativo conectado a respaldo y soporte."""

    respaldo_automatico: bool
    ultimo_respaldo_en: str
    ultimo_respaldo_estado: str
    total_respaldos: int
    ultimo_respaldo_archivo: str
    ultimo_respaldo_tamano_bytes: int
    ultimo_respaldo_generado_por: str
    ruta_respaldos_principal: str
    retencion_maxima: int


@dataclass(slots=True)
class RespaldoAutomaticoDisponible:
    """Respaldo automatico registrado y candidato a restauracion."""

    identificador: int
    nombre_archivo: str
    ruta_archivo: str
    generado_en: str
    tamano_bytes: int
    hash_archivo: str


@dataclass(slots=True)
class ResultadoBusquedaRespaldoAutomatico:
    """Resultado de localizar el respaldo automatico util mas reciente."""

    exito: bool
    mensaje: str
    respaldo: RespaldoAutomaticoDisponible | None = None


@dataclass(slots=True)
class SeguridadConfiguracion:
    """Resumen de reglas de seguridad vigentes."""

    autenticacion_local: bool
    maximo_intentos_fallidos: int
    duracion_sesion_horas: float
    restablecimiento_administrativo: bool
    cambio_contrasena_obligatorio: bool


@dataclass(slots=True)
class InformacionConfiguracion:
    """Resumen informativo del sistema."""

    nombre_sistema: str
    version_sistema: str
    ruta_base_datos: str
    modo_operacion: str
    ultima_actualizacion: str
    actualizado_por: str


@dataclass(slots=True)
class EstadoConfiguracion:
    """Estado agregado mostrado en la UI de configuracion."""

    identidad_empresa: IdentidadEmpresa
    parametros_cobro: ParametrosCobro
    factura: FacturaConfiguracion
    reportes_pdf: ReportesPdfConfiguracion
    operacion: OperacionConfiguracion
    seguridad: SeguridadConfiguracion
    informacion: InformacionConfiguracion

    @property
    def datos_junta(self) -> IdentidadEmpresa:
        """Compatibilidad temporal con implementaciones antiguas."""

        return self.identidad_empresa


@dataclass(slots=True)
class ResultadoGestionConfiguracion:
    """Resultado estandar de guardado en configuracion."""

    exito: bool
    mensaje: str
    codigo: str = ""


DatosJunta = IdentidadEmpresa
