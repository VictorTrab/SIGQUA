"""Entidades declarativas del modulo de reportes."""

from __future__ import annotations

from dataclasses import dataclass, field


REPORTE_DEUDA_ABONADOS_ESTADO = "deuda_abonados_estado"
REPORTE_SERVICIO_CASAS = "servicio_casas"
REPORTE_INGRESOS_MENSUALES_DIARIOS = "ingresos_mensuales_diarios"
REPORTE_HISTORIAL_ABONADO_CASA = "historial_abonado_casa"
ORIENTACION_VERTICAL = "VERTICAL"
ORIENTACION_HORIZONTAL = "HORIZONTAL"

TIPO_FILTRO_COMBO = "combo"
TIPO_FILTRO_BUSQUEDA = "busqueda"
TIPO_FILTRO_FECHA = "fecha"
TIPO_FILTRO_BOOL = "bool"


@dataclass(slots=True)
class IndicadorReporte:
    """Indicador agregado del tablero administrativo."""

    titulo: str
    valor: str
    detalle: str


@dataclass(slots=True)
class OpcionFiltroReporte:
    """Opcion visible dentro de un filtro de reportes."""

    valor: str
    etiqueta: str


@dataclass(slots=True)
class FiltroReporte:
    """Definicion de un filtro renderizable por la vista."""

    clave: str
    etiqueta: str
    tipo: str
    opciones: tuple[OpcionFiltroReporte, ...] = ()
    valor: str = ""


@dataclass(slots=True)
class TarjetaReporte:
    """Entrada visual del catalogo de reportes."""

    codigo: str
    titulo: str
    descripcion: str
    icono: str
    resumen: str


@dataclass(slots=True)
class TablaReporte:
    """Vista previa tabular del reporte seleccionado."""

    codigo: str
    titulo: str
    descripcion: str
    columnas: tuple[str, ...]
    filas: tuple[tuple[str, ...], ...]
    resumen: tuple[tuple[str, str], ...] = ()
    orientacion: str = ORIENTACION_VERTICAL


@dataclass(frozen=True, slots=True)
class ConfiguracionSalidaReportePdf:
    """Preferencias efectivas para exportar reportes."""

    ruta_salida: str
    abrir_automaticamente: bool
    firma_habilitada: bool
    firma_texto_linea: str


@dataclass(slots=True)
class EstadoReportes:
    """Estado completo del modulo de reportes administrativos."""

    indicadores: tuple[IndicadorReporte, ...]
    catalogo: tuple[TarjetaReporte, ...]
    reporte_actual: str
    filtros_visibles: tuple[FiltroReporte, ...]
    filtros_aplicados: dict[str, str] = field(default_factory=dict)
    tabla_actual: TablaReporte | None = None
