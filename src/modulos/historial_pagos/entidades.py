"""Entidades del modulo de historial de pagos."""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil


FILTRO_HISTORIAL_TODOS = "TODOS"
FILTRO_HISTORIAL_MENSUALIDAD = "MENSUALIDAD"
FILTRO_HISTORIAL_PLAN = "PLAN_PAGO"
FILTRO_HISTORIAL_CONEXION = "CONEXION"
FILTRO_HISTORIAL_RECONEXION = "RECONEXION"

FILTRO_METODO_TODOS = "TODOS"
FILTRO_METODO_EFECTIVO = "EFECTIVO"
FILTRO_METODO_TRANSFERENCIA = "TRANSFERENCIA"
FILTRO_METODO_DEPOSITO = "DEPOSITO"
FILTRO_METODO_OTRO = "OTRO"


@dataclass(slots=True)
class FiltroHistorialPagos:
    """Filtros activos del modulo."""

    texto: str = ""
    tipo_pago: str = FILTRO_HISTORIAL_TODOS
    metodo_pago: str = FILTRO_METODO_TODOS
    fecha_desde: str = ""
    fecha_hasta: str = ""


@dataclass(slots=True)
class FilaHistorialPago:
    """Fila operativa del listado historico."""

    pago_id: int
    numero_comprobante: str
    fecha_pago: str
    tipo_pago: str
    abonado_nombre: str
    abonado_dni: str
    casa_codigo: str
    metodo_pago_codigo: str
    metodo_pago: str
    referencia: str
    total_pagado_centavos: int
    usuario_registro: str


@dataclass(slots=True)
class ResumenHistorialPagos:
    """Metricas de cabecera del historial."""

    total_pagos: int
    pagos_hoy: int
    total_cobrado_hoy_centavos: int
    ultimo_comprobante: str


@dataclass(slots=True)
class PaginaHistorialPagos:
    """Resultado paginado del listado historico."""

    items: list[FilaHistorialPago]
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
class LineaDetalleHistorialPago:
    """Linea detallada de una aplicacion de pago."""

    descripcion: str
    monto_pagado_centavos: int


@dataclass(slots=True)
class DetalleHistorialPago:
    """Detalle completo del pago para consulta y reimpresion."""

    pago_id: int
    numero_comprobante: str
    fecha_pago: str
    tipo_pago: str
    casa_codigo: str
    abonado_nombre: str
    abonado_dni: str
    barrio_nombre: str
    direccion_casa: str
    metodo_pago: str
    referencia: str
    usuario_registro: str
    total_pagado_centavos: int
    saldo_posterior_centavos: int
    lineas_detalle: tuple[LineaDetalleHistorialPago, ...]


@dataclass(slots=True)
class ResultadoHistorialPagos:
    """Resultado de acciones operativas del modulo."""

    exito: bool
    mensaje: str
    codigo: str = ""
