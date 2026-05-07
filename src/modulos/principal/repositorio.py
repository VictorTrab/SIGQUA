"""Contratos e implementaciones de persistencia del modulo principal."""

from __future__ import annotations

from contextlib import closing
from typing import Protocol

from comun.base_datos import GestorBaseDatos
from modulos.principal.entidades import MetricaDashboard


class RepositorioModuloPrincipal(Protocol):
    """Define las consultas necesarias para el dashboard inicial."""

    def obtener_metricas_dashboard(self) -> tuple[MetricaDashboard, ...]:
        """Obtiene las metricas operativas del dashboard."""


class RepositorioModuloPrincipalSQLite:
    """Repositorio SQLite para metricas generales del sistema."""

    def __init__(self, gestor_base_datos: GestorBaseDatos) -> None:
        self._gestor_base_datos = gestor_base_datos

    def obtener_metricas_dashboard(self) -> tuple[MetricaDashboard, ...]:
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            abonados_activos = self._contar(
                conexion,
                "SELECT COUNT(*) FROM abonados WHERE eliminado_en IS NULL AND estado = 'ACTIVO';",
            )
            casas_activas = self._contar(
                conexion,
                "SELECT COUNT(*) FROM casas WHERE eliminado_en IS NULL AND estado_servicio = 'ACTIVO';",
            )
            deuda_centavos = self._sumar(
                conexion,
                """
                SELECT COALESCE(SUM(saldo_pendiente_centavos), 0)
                FROM cargos
                WHERE estado IN ('PENDIENTE', 'PARCIAL', 'VENCIDO');
                """,
            )
            pagos_mes_centavos = self._sumar(
                conexion,
                """
                SELECT COALESCE(SUM(monto_total_centavos), 0)
                FROM pagos
                WHERE strftime('%Y-%m', fecha_pago) = strftime('%Y-%m', 'now')
                  AND estado = 'REGISTRADO';
                """,
            )
            casas_en_mora = self._contar(
                conexion,
                """
                SELECT COUNT(DISTINCT casa_id)
                FROM cargos
                WHERE estado = 'VENCIDO' AND saldo_pendiente_centavos > 0;
                """,
            )

        return (
            MetricaDashboard("abonados", "Abonados activos", str(abonados_activos), "Registros operativos"),
            MetricaDashboard("casas", "Casas activas", str(casas_activas), "Servicios habilitados"),
            MetricaDashboard("deuda", "Deuda pendiente", self._formatear_lps(deuda_centavos), "Cargos pendientes"),
            MetricaDashboard("pagos_mes", "Pagos del mes", self._formatear_lps(pagos_mes_centavos), "Ingresos registrados"),
            MetricaDashboard("mora", "Casas en mora", str(casas_en_mora), "Con cargos vencidos"),
        )

    @staticmethod
    def _contar(conexion: object, consulta: str) -> int:
        return int(conexion.execute(consulta).fetchone()[0] or 0)

    @staticmethod
    def _sumar(conexion: object, consulta: str) -> int:
        return int(conexion.execute(consulta).fetchone()[0] or 0)

    @staticmethod
    def _formatear_lps(valor_centavos: int) -> str:
        return f"L {valor_centavos / 100:,.2f}"


class RepositorioModuloPrincipalMemoria:
    """Repositorio de respaldo para pruebas o ejecuciones sin SQLite."""

    def obtener_metricas_dashboard(self) -> tuple[MetricaDashboard, ...]:
        return (
            MetricaDashboard("abonados", "Abonados activos", "0", "Sin datos cargados"),
            MetricaDashboard("casas", "Casas activas", "0", "Sin datos cargados"),
            MetricaDashboard("deuda", "Deuda pendiente", "L 0.00", "Sin cargos pendientes"),
            MetricaDashboard("pagos_mes", "Pagos del mes", "L 0.00", "Sin pagos registrados"),
            MetricaDashboard("mora", "Casas en mora", "0", "Sin mora registrada"),
        )

