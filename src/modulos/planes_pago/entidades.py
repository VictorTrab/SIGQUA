"""Entidades del modulo de planes de pago."""

from __future__ import annotations

from dataclasses import dataclass, field
from math import ceil


FILTRO_PLANES_TODOS = "TODOS"
FILTRO_PLANES_ACTIVOS = "ACTIVOS"
FILTRO_PLANES_CON_MORA = "CON_MORA"
FILTRO_PLANES_SERVICIO = "SERVICIO"

TIPOS_PLAN_VALIDOS = (
    "CONEXION",
    "RECONEXION",
)
ESTADOS_PLAN_VALIDOS = ("ACTIVO", "FINALIZADO", "ANULADO", "CANCELADO")


@dataclass(slots=True)
class PlanPago:
    """Representa un plan de pago con su contexto operativo principal."""

    identificador: int | None
    casa_id: int
    casa_codigo: str
    abonado_id: int
    abonado_nombre: str
    abonado_dni: str
    barrio_nombre: str = ""
    tipo_plan: str = "RECONEXION"
    concepto_financiado: str = "RECONEXION"
    prima_centavos: int = 0
    saldo_financiado_centavos: int = 0
    monto_total_centavos: int = 0
    cuota_regular_centavos: int = 0
    cantidad_cuotas: int = 0
    cuotas_pagadas: int = 0
    cuotas_pendientes: int = 0
    saldo_pendiente_centavos: int = 0
    cuotas_en_mora: int = 0
    proxima_fecha: str = ""
    estado: str = "ACTIVO"
    observaciones: str = ""
    creado_en: str = ""
    actualizado_en: str = ""
    creado_por_nombre: str = ""

    @property
    def codigo(self) -> str:
        if self.identificador is None:
            return "PP-NUEVO"
        return f"PP-{self.identificador:03d}"

    @property
    def resumen_concepto(self) -> str:
        return self.concepto_financiado.replace("_", " ").title()


@dataclass(slots=True)
class ResumenPlanesPago:
    """Metricas de cabecera del modulo."""

    total_planes: int
    planes_activos: int
    planes_con_mora: int
    saldo_pendiente_centavos: int


@dataclass(slots=True)
class PaginaPlanesPago:
    """Resultado paginado del listado."""

    items: list[PlanPago]
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
class OpcionCasaPlanPago:
    """Opcion utilizable al crear o editar planes."""

    casa_id: int
    casa_codigo: str
    abonado_id: int
    abonado_nombre: str
    abonado_dni: str
    barrio_nombre: str
    estado_servicio: str
    meses_pendientes: int = 0
    meses_en_mora: int = 0
    deuda_total_centavos: int = 0

    @property
    def etiqueta(self) -> str:
        return (
            f"{self.casa_codigo} | {self.abonado_nombre} | {self.barrio_nombre} | "
            f"Servicio {self.estado_servicio} | Deuda {self.deuda_total_centavos / 100:,.2f}"
        )


@dataclass(slots=True)
class FormularioPlanPago:
    """Datos capturados en el formulario de planes."""

    identificador: int | None
    casa_id: int | None
    tipo_plan: str
    concepto_financiado: str
    prima_centavos: int
    saldo_financiado_centavos: int
    cuota_regular_centavos: int
    cantidad_cuotas: int
    estado: str
    observaciones: str


@dataclass(slots=True)
class CuotaPlanPago:
    """Cuota individual de un plan."""

    identificador: int
    numero_cuota: int
    fecha_vencimiento: str
    monto_centavos: int
    saldo_pendiente_centavos: int
    estado: str


@dataclass(slots=True)
class DetallePlanPago:
    """Detalle ampliado del plan con cuotas y cargos vinculados."""

    plan: PlanPago
    cuotas: tuple[CuotaPlanPago, ...] = field(default_factory=tuple)
    cargos_vinculados: tuple[str, ...] = field(default_factory=tuple)


@dataclass(slots=True)
class ResultadoGestionPlanesPago:
    """Resultado estandar de operaciones del modulo."""

    exito: bool
    mensaje: str
    codigo: str = ""
