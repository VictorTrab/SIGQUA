"""Entidades del modulo de abonados."""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil


FILTRO_ABONADOS_TODOS = "TODOS"
FILTRO_ABONADOS_CON_MORA = "CON_MORA"
FILTRO_ABONADOS_SIN_MORA = "SIN_MORA"
FILTRO_ABONADOS_CON_PLAN = "CON_PLAN"


@dataclass(slots=True)
class Abonado:
    """Representa un abonado con su contexto operativo principal."""

    identificador: int | None
    dni: str
    nombre_completo: str
    telefono: str = ""
    barrio_id: int | None = None
    barrio_nombre: str = ""
    direccion_referencia: str = ""
    observaciones: str = ""
    estado: str = "ACTIVO"
    total_casas: int = 0
    meses_en_mora: int = 0
    deuda_total_centavos: int = 0
    tiene_plan_activo: bool = False
    actualizado_en: str = ""


@dataclass(slots=True)
class ResumenAbonados:
    """Metricas de cabecera del modulo."""

    total_abonados: int
    abonados_activos: int
    abonados_con_deuda: int
    abonados_morosos: int


@dataclass(slots=True)
class PaginaAbonados:
    """Resultado paginado del listado."""

    items: list[Abonado]
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
class OpcionBarrio:
    """Opcion utilizable en formularios de abonados."""

    identificador: int
    nombre: str


@dataclass(slots=True)
class FormularioAbonado:
    """Datos capturados desde el formulario de abonados."""

    identificador: int | None
    dni: str
    nombre_completo: str
    telefono: str
    barrio_id: int | None
    direccion_referencia: str
    observaciones: str
    estado: str


@dataclass(slots=True)
class ResultadoGestionAbonados:
    """Resultado estandar de una operacion del modulo."""

    exito: bool
    mensaje: str
    codigo: str = ""
