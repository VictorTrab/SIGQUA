"""Entidades del modulo de casas."""

from __future__ import annotations

from dataclasses import dataclass, field

from comun.pagos_adelantados import ResumenAdelantoCasa
from math import ceil


FILTRO_CASAS_TODAS = "TODAS"
FILTRO_CASAS_ACTIVAS = "ACTIVAS"
FILTRO_CASAS_SUSPENDIDAS = "SUSPENDIDAS"
FILTRO_CASAS_CON_MORA = "CON_MORA"
FILTRO_CASAS_CORTADAS = "CORTADAS"
FILTRO_CASAS_DEUDA_MAYOR_5 = "DEUDA_MAYOR_5"
FILTRO_CASAS_SIN_PROPIETARIO = "SIN_PROPIETARIO"

ESTADO_SERVICIO_ACTIVO = "ACTIVO"
ESTADO_SERVICIO_CORTADO = "CORTADO"
ESTADO_SERVICIO_INACTIVO = "INACTIVO"
ESTADOS_SERVICIO_VALIDOS = (
    ESTADO_SERVICIO_ACTIVO,
    ESTADO_SERVICIO_CORTADO,
    ESTADO_SERVICIO_INACTIVO,
)

ESTADO_ADMINISTRATIVO_OPERATIVA = "OPERATIVA"
ESTADO_ADMINISTRATIVO_SUSPENDIDA = "SUSPENDIDA"
ESTADOS_ADMINISTRATIVOS_VALIDOS = (
    ESTADO_ADMINISTRATIVO_OPERATIVA,
    ESTADO_ADMINISTRATIVO_SUSPENDIDA,
)

MOTIVO_ESTADO_ADMINISTRATIVO_NINGUNO = "NINGUNO"
MOTIVO_ESTADO_ADMINISTRATIVO_ABONADO_INACTIVO = "ABONADO_INACTIVO"
MOTIVO_ESTADO_ADMINISTRATIVO_REASIGNACION_PENDIENTE = "REASIGNACION_PENDIENTE"
MOTIVO_ESTADO_ADMINISTRATIVO_REVISION_ADMINISTRATIVA = "REVISION_ADMINISTRATIVA"
MOTIVOS_ESTADO_ADMINISTRATIVO_VALIDOS = (
    MOTIVO_ESTADO_ADMINISTRATIVO_NINGUNO,
    MOTIVO_ESTADO_ADMINISTRATIVO_ABONADO_INACTIVO,
    MOTIVO_ESTADO_ADMINISTRATIVO_REASIGNACION_PENDIENTE,
    MOTIVO_ESTADO_ADMINISTRATIVO_REVISION_ADMINISTRATIVA,
)

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

MOTIVO_CAMBIO_RESPONSABLE_FALLECIMIENTO = "FALLECIMIENTO_DEL_ABONADO"


@dataclass(slots=True)
class Casa:
    """Representa una casa con su contexto operativo principal."""

    identificador: int | None
    abonado_id: int | None = None
    abonado_nombre: str = ""
    abonado_dni: str = ""
    abonado_estado: str = "ACTIVO"
    barrio_id: int | None = None
    barrio_nombre: str = ""
    direccion_referencia: str = ""
    observaciones: str = ""
    estado_servicio: str = ESTADO_SERVICIO_ACTIVO
    estado_administrativo: str = ESTADO_ADMINISTRATIVO_OPERATIVA
    motivo_estado_administrativo: str = MOTIVO_ESTADO_ADMINISTRATIVO_NINGUNO
    ha_tenido_servicio_activo: bool = False
    antecedente_servicio_editable: bool = True
    deuda_total_centavos: int = 0
    meses_pendientes: int = 0
    meses_en_mora: int = 0
    tiene_plan_activo: bool = False
    estado_aviso_cobro: str = ESTADO_AVISO_SIN_AVISO
    fecha_ultimo_aviso: str = ""
    usuario_ultimo_aviso_nombre: str = ""
    observacion_ultimo_aviso: str = ""
    creado_en: str = ""
    fecha_alta: str = ""
    actualizado_en: str = ""

    @property
    def codigo(self) -> str:
        if self.identificador is None:
            return "CA-NUEVA"
        return f"CA-{self.identificador:03d}"

    @property
    def propietario_operativo(self) -> bool:
        return self.abonado_id is not None and self.abonado_estado == "ACTIVO"

    @property
    def resumen_propietario(self) -> str:
        if not self.abonado_nombre:
            return "Sin propietario operativo"
        if self.abonado_estado != "ACTIVO":
            return f"{self.abonado_nombre} (inactivo)"
        return self.abonado_nombre

    @property
    def esta_operativa(self) -> bool:
        return self.estado_administrativo == ESTADO_ADMINISTRATIVO_OPERATIVA

    @property
    def resumen_antecedente_servicio(self) -> str:
        if self.ha_tenido_servicio_activo:
            return "Ya tuvo servicio antes"
        return "Nunca ha tenido servicio"

    @property
    def resumen_estado_compuesto(self) -> str:
        return f"{self.estado_servicio} | {self.estado_administrativo}"


@dataclass(slots=True)
class ResumenCasas:
    """Metricas de cabecera del modulo."""

    total_casas: int
    casas_activas: int
    casas_con_deuda: int
    casas_morosas: int


@dataclass(slots=True)
class PaginaCasas:
    """Resultado paginado del listado."""

    items: list[Casa]
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
class OpcionAbonado:
    """Opcion utilizable en formularios y reasignaciones de casas."""

    identificador: int
    nombre_completo: str
    dni: str
    estado: str = "ACTIVO"

    @property
    def etiqueta(self) -> str:
        sufijo = "" if self.estado == "ACTIVO" else " | Inactivo"
        return f"{self.nombre_completo} | {self.dni}{sufijo}"


@dataclass(slots=True)
class OpcionBarrio:
    """Opcion utilizable en formularios de casas."""

    identificador: int
    nombre: str


@dataclass(slots=True)
class FormularioCasa:
    """Datos capturados desde el formulario del modulo."""

    identificador: int | None
    abonado_id: int | None
    barrio_id: int | None
    direccion_referencia: str
    observaciones: str
    estado_servicio: str
    estado_administrativo: str
    motivo_estado_administrativo: str
    ha_tenido_servicio_activo: bool


@dataclass(slots=True)
class FormularioCorteServicioCasa:
    """Datos capturados para confirmar un corte fisico de servicio."""

    casa_id: int
    observaciones: str


@dataclass(slots=True)
class HistorialPropietarioCasa:
    """Registro historico de cambio de propietario de una casa."""

    identificador: int
    fecha_cambio: str
    abonado_anterior_nombre: str
    abonado_nuevo_nombre: str
    motivo: str
    usuario_nombre: str
    observacion: str = ""


@dataclass(slots=True)
class PlanActivoCasa:
    """Resumen del plan de pago activo asociado a la casa."""

    identificador: int
    estado: str
    monto_total_centavos: int
    cuota_regular_centavos: int
    cuotas_pagadas: int
    cuotas_pendientes: int
    saldo_pendiente_centavos: int
    proxima_fecha: str

    @property
    def codigo(self) -> str:
        return f"PP-{self.identificador:03d}"


@dataclass(slots=True)
class DetalleCasa:
    """Detalle operativo ampliado de una casa."""

    casa: Casa
    plan_activo: PlanActivoCasa | None = None
    historial_propietarios: tuple[HistorialPropietarioCasa, ...] = field(default_factory=tuple)
    ultima_fecha_cambio_dueno: str = ""
    resumen_adelanto: ResumenAdelantoCasa = ResumenAdelantoCasa(0)


@dataclass(slots=True)
class ResultadoGestionCasas:
    """Resultado estandar de una operacion del modulo."""

    exito: bool
    mensaje: str
    codigo: str = ""
