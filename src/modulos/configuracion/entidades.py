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


@dataclass(slots=True)
class DatosJunta:
    """Datos operativos basicos de la junta."""

    nombre: str
    telefono: str
    correo: str
    direccion: str


@dataclass(slots=True)
class ParametrosCobro:
    """Configuracion vigente para el cobro operativo."""

    precio_mensual_centavos: int
    mora_visible: bool
    multa_mora_automatica_activa: bool
    multa_mora_automatica_centavos: int
    corte_automatico_activo: bool


@dataclass(slots=True)
class SeguridadConfiguracion:
    """Resumen de reglas de seguridad vigentes."""

    autenticacion_local: bool
    maximo_intentos_fallidos: int
    duracion_sesion_horas: int
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


@dataclass(slots=True)
class EstadoConfiguracion:
    """Estado agregado mostrado en la UI de configuracion."""

    datos_junta: DatosJunta
    parametros_cobro: ParametrosCobro
    seguridad: SeguridadConfiguracion
    informacion: InformacionConfiguracion


@dataclass(slots=True)
class ResultadoGestionConfiguracion:
    """Resultado estandar de guardado en configuracion."""

    exito: bool
    mensaje: str
    codigo: str = ""
