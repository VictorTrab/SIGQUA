"""Entidades del modulo de barrios."""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil


FILTRO_BARRIOS_TODOS = "TODOS"
FILTRO_BARRIOS_ACTIVOS = "ACTIVOS"
FILTRO_BARRIOS_INACTIVOS = "INACTIVOS"
FILTRO_BARRIOS_CON_ABONADOS = "CON_ABONADOS"
FILTRO_BARRIOS_SIN_ABONADOS = "SIN_ABONADOS"


@dataclass(slots=True)
class Barrio:
    """Representa un barrio del sistema con sus datos operativos."""

    identificador: int | None
    nombre: str
    estado: str = "ACTIVO"
    observaciones: str = ""
    total_abonados: int = 0
    total_casas: int = 0
    creado_en: str = ""
    actualizado_en: str = ""

    @property
    def codigo(self) -> str:
        if self.identificador is None:
            return "BR-NUEVO"
        return f"BR-{self.identificador:03d}"


@dataclass(slots=True)
class ResumenBarrios:
    """Metricas de cabecera para el modulo."""

    total_barrios: int
    barrios_activos: int
    barrios_con_abonados: int
    barrio_con_mas_abonados: str
    cantidad_maxima_abonados: int


@dataclass(slots=True)
class PaginaBarrios:
    """Resultado paginado del listado de barrios."""

    items: list[Barrio]
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
class FormularioBarrio:
    """Datos capturados desde el modal de creacion o edicion."""

    identificador: int | None
    nombre: str
    estado: str
    observaciones: str


@dataclass(slots=True)
class ResultadoGestionBarrios:
    """Resultado de una operacion sobre barrios."""

    exito: bool
    mensaje: str
    codigo: str = ""
