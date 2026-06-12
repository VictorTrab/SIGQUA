"""Contratos compartidos para consultar cobertura de pagos adelantados."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class ConfiguracionPagoAdelantado:
    """Politica administrativa vigente para mensualidades adelantadas."""

    permitir_pago_adelantado: bool


@dataclass(frozen=True, slots=True)
class ResumenAdelantoCasa:
    """Cobertura adelantada vigente de una casa."""

    casa_id: int
    meses_activos: int = 0
    monto_activo_centavos: int = 0
    ultimo_periodo_cubierto: str = ""
    periodos_activos: tuple[tuple[int, int], ...] = ()
    capacidad_disponible: int = 0


@dataclass(frozen=True, slots=True)
class EstadoFinancieroCasaAbonado:
    """Estado resumido de una casa dentro del detalle de su abonado."""

    casa_id: int
    casa_codigo: str
    meses_pendientes: int
    resumen_adelanto: ResumenAdelantoCasa


class LectorPagosAdelantados(Protocol):
    """Lecturas de adelantos reutilizables por modulos operativos."""

    def obtener_configuracion_pago_adelantado(self) -> ConfiguracionPagoAdelantado:
        """Obtiene la politica vigente."""

    def obtener_resumen_adelanto_casa(self, casa_id: int) -> ResumenAdelantoCasa:
        """Obtiene la cobertura activa de una casa."""

    def listar_estados_casas_abonado(
        self,
        abonado_id: int,
    ) -> tuple[EstadoFinancieroCasaAbonado, ...]:
        """Lista estados financieros resumidos de las casas de un abonado."""

    def tiene_plan_reconexion_pendiente(self, casa_id: int) -> bool:
        """Indica si existe un plan de reconexion con cuotas pendientes."""
