"""Entidades del modulo de morosidad."""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil


FILTRO_MOROSIDAD_TODOS = "TODOS"
FILTRO_MOROSIDAD_LEVE = "LEVE"
FILTRO_MOROSIDAD_MEDIA = "MEDIA"
FILTRO_MOROSIDAD_SEVERA = "SEVERA"
FILTRO_MOROSIDAD_LISTO_CORTE = "LISTO_CORTE"

ESTADO_AVISO_SIN_AVISO = "SIN_AVISO"
ESTADO_AVISO_PRIMER_AVISO = "PRIMER_AVISO"
ESTADO_AVISO_SEGUNDO_AVISO = "SEGUNDO_AVISO"
ESTADO_AVISO_TERCER_AVISO = "TERCER_AVISO"
ESTADO_AVISO_LISTO_PARA_CORTE = "LISTO_PARA_CORTE"
ESTADO_AVISO_CORTADO = "CORTADO"
ESTADOS_AVISO_COBRO_VALIDOS = (
    ESTADO_AVISO_SIN_AVISO,
    ESTADO_AVISO_PRIMER_AVISO,
    ESTADO_AVISO_SEGUNDO_AVISO,
    ESTADO_AVISO_TERCER_AVISO,
    ESTADO_AVISO_LISTO_PARA_CORTE,
    ESTADO_AVISO_CORTADO,
)


@dataclass(slots=True)
class FiltroMorosidad:
    """Filtros activos del modulo."""

    texto: str = ""
    severidad: str = FILTRO_MOROSIDAD_TODOS
    estado_aviso: str = FILTRO_MOROSIDAD_TODOS


@dataclass(slots=True)
class FilaMorosidad:
    """Fila operativa del listado de morosidad."""

    abonado_id: int
    casa_id: int
    casa_codigo: str
    abonado_nombre: str
    abonado_dni: str
    barrio_nombre: str
    direccion_casa: str
    estado_servicio: str
    meses_vencidos: int
    deuda_base_centavos: int
    recargo_mora_centavos: int
    deuda_total_centavos: int
    vencimiento_mas_antiguo: str
    estado_aviso_cobro: str = ESTADO_AVISO_SIN_AVISO
    fecha_ultimo_aviso: str = ""
    usuario_ultimo_aviso: str = ""
    observacion_ultimo_aviso: str = ""
    dias_en_mora: int = 0
    prioridad: str = "Baja"
    severidad: str = FILTRO_MOROSIDAD_LEVE


@dataclass(slots=True)
class ResumenMorosidad:
    """Indicadores principales del modulo."""

    total_casas: int
    total_abonados: int
    deuda_base_centavos: int
    recargo_mora_centavos: int
    deuda_total_centavos: int
    casos_severos: int


@dataclass(slots=True)
class PaginaMorosidad:
    """Resultado paginado del listado."""

    items: list[FilaMorosidad]
    pagina_actual: int
    tamano_pagina: int
    total_registros: int

    @property
    def total_paginas(self) -> int:
        if self.total_registros <= 0:
            return 1
        return ceil(self.total_registros / self.tamano_pagina)

    @property
    def indice_inicio(self) -> int:
        if self.total_registros <= 0:
            return 0
        return ((self.pagina_actual - 1) * self.tamano_pagina) + 1

    @property
    def indice_fin(self) -> int:
        if self.total_registros <= 0:
            return 0
        return min(self.pagina_actual * self.tamano_pagina, self.total_registros)


@dataclass(slots=True)
class LineaDetalleMorosidad:
    """Linea vencida pendiente por casa."""

    cargo_id: int
    descripcion: str
    fecha_vencimiento: str
    saldo_pendiente_centavos: int


@dataclass(slots=True)
class CasaDetalleMorosidad:
    """Detalle de deuda por casa para un abonado."""

    casa_id: int
    casa_codigo: str
    barrio_nombre: str
    direccion_casa: str
    estado_servicio: str
    meses_vencidos: int
    deuda_base_centavos: int
    recargo_mora_centavos: int
    deuda_total_centavos: int
    vencimiento_mas_antiguo: str
    estado_aviso_cobro: str = ESTADO_AVISO_SIN_AVISO
    fecha_ultimo_aviso: str = ""
    usuario_ultimo_aviso: str = ""
    observacion_ultimo_aviso: str = ""
    dias_en_mora: int = 0
    prioridad: str = "Baja"
    lineas_detalle: tuple[LineaDetalleMorosidad, ...] = ()


@dataclass(slots=True)
class DetalleMorosidad:
    """Detalle operativo completo por abonado."""

    abonado_id: int
    abonado_nombre: str
    abonado_dni: str
    casas: tuple[CasaDetalleMorosidad, ...]


@dataclass(slots=True)
class EstadoMorosidad:
    """Estado completo del modulo."""

    resumen: ResumenMorosidad
    pagina: PaginaMorosidad
    filtros: FiltroMorosidad


@dataclass(slots=True)
class ResultadoMorosidad:
    """Resultado de acciones operativas del modulo."""

    exito: bool
    mensaje: str
    codigo: str = ""
    ruta_documento: str = ""
