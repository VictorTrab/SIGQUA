"""Contratos e implementaciones de persistencia del modulo principal."""

from __future__ import annotations

from contextlib import closing
from datetime import datetime
from typing import Protocol

from comun.base_datos import GestorBaseDatos
from modulos.principal.entidades import (
    AnaliticaDashboard,
    CategoriaDashboard,
    InsightDashboard,
    MetricaDashboard,
    PuntoSerieDashboard,
)


class RepositorioModuloPrincipal(Protocol):
    """Define las consultas necesarias para el dashboard inicial."""

    def obtener_metricas_dashboard(self) -> tuple[MetricaDashboard, ...]:
        """Obtiene las metricas operativas del dashboard."""

    def obtener_analitica_dashboard(self) -> AnaliticaDashboard:
        """Obtiene series y paneles analiticos para la pantalla de inicio."""


class RepositorioModuloPrincipalSQLite:
    """Repositorio SQLite para metricas generales del sistema."""

    def __init__(self, gestor_base_datos: GestorBaseDatos) -> None:
        self._gestor_base_datos = gestor_base_datos

    def obtener_metricas_dashboard(self) -> tuple[MetricaDashboard, ...]:
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            fila = conexion.execute(
                """
                SELECT
                    (SELECT COUNT(*)
                     FROM abonados
                     WHERE eliminado_en IS NULL
                       AND estado = 'ACTIVO') AS abonados_activos,
                    (SELECT COUNT(*)
                     FROM casas
                     WHERE eliminado_en IS NULL
                       AND estado_servicio = 'ACTIVO'
                       AND COALESCE(estado_administrativo, 'OPERATIVA') = 'OPERATIVA') AS casas_activas,
                    (SELECT COUNT(DISTINCT c.casa_id)
                     FROM cargos c
                     INNER JOIN casas ca ON ca.id = c.casa_id
                     WHERE ca.estado_servicio IN ('ACTIVO', 'CORTADO')
                       AND c.estado = 'VENCIDO'
                       AND c.saldo_pendiente_centavos > 0
                       AND c.anulado_en IS NULL) AS casas_con_deuda_vencida,
                    (SELECT COALESCE(SUM(total_ingresos_centavos), 0)
                     FROM vw_ingresos_por_fecha
                     WHERE fecha = date('now', 'localtime')) AS ingresos_hoy_centavos,
                    (SELECT COALESCE(SUM(total_pagado_centavos), 0)
                     FROM pagos
                     WHERE strftime('%Y-%m', fecha_pago) = strftime('%Y-%m', 'now', 'localtime')
                       AND estado = 'CONFIRMADO') AS ingresos_mes_centavos,
                    (SELECT COALESCE(deuda_total_centavos, 0)
                     FROM vw_deuda_total_servicios_activos) AS deuda_total_centavos,
                    (SELECT COALESCE(total_pagos, 0)
                     FROM vw_ingresos_por_fecha
                     WHERE fecha = date('now', 'localtime')) AS pagos_hoy
                """
            ).fetchone()

        return (
            MetricaDashboard(
                "ingresos_hoy",
                "Ingresos de hoy",
                self._formatear_lps(int(fila["ingresos_hoy_centavos"] or 0)),
                f"{int(fila['pagos_hoy'] or 0)} pago(s) confirmados hoy.",
            ),
            MetricaDashboard(
                "ingresos_mes",
                "Ingresos del mes",
                self._formatear_lps(int(fila["ingresos_mes_centavos"] or 0)),
                "Recaudacion confirmada del mes en curso.",
            ),
            MetricaDashboard(
                "deuda",
                "Deuda pendiente",
                self._formatear_lps(int(fila["deuda_total_centavos"] or 0)),
                "Saldo vigente en servicios activos y cortados.",
            ),
            MetricaDashboard(
                "casas_mora",
                "Casas con deuda vencida",
                str(int(fila["casas_con_deuda_vencida"] or 0)),
                "Servicios con cargos vencidos pendientes.",
            ),
            MetricaDashboard(
                "abonados_activos",
                "Abonados activos",
                str(int(fila["abonados_activos"] or 0)),
                "Usuarios operativos con servicio vigente.",
            ),
            MetricaDashboard(
                "casas_activas",
                "Casas activas",
                str(int(fila["casas_activas"] or 0)),
                "Servicios operativos habilitados actualmente.",
            ),
        )

    def obtener_analitica_dashboard(self) -> AnaliticaDashboard:
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            recaudacion = tuple(
                PuntoSerieDashboard(str(fila["etiqueta"]), float(fila["valor"] or 0) / 100.0)
                for fila in conexion.execute(
                    """
                    WITH RECURSIVE meses(offseto, fecha_base) AS (
                        SELECT 5, date('now', 'localtime', 'start of month', '-5 month')
                        UNION ALL
                        SELECT offseto - 1, date(fecha_base, '+1 month')
                        FROM meses
                        WHERE offseto > 0
                    )
                    SELECT
                        strftime('%m/%Y', m.fecha_base) AS etiqueta,
                        COALESCE(SUM(p.total_pagado_centavos), 0) AS valor
                    FROM meses m
                    LEFT JOIN pagos p
                        ON strftime('%Y-%m', p.fecha_pago) = strftime('%Y-%m', m.fecha_base)
                       AND p.estado = 'CONFIRMADO'
                    GROUP BY m.fecha_base
                    ORDER BY m.fecha_base;
                    """
                ).fetchall()
            )
            deuda_por_barrio = tuple(
                CategoriaDashboard(str(fila["etiqueta"]), float(fila["valor"] or 0) / 100.0)
                for fila in conexion.execute(
                    """
                    SELECT
                        barrio_nombre AS etiqueta,
                        deuda_total_centavos AS valor
                    FROM vw_deuda_por_barrio
                    WHERE deuda_total_centavos > 0
                    ORDER BY deuda_total_centavos DESC, barrio_nombre ASC
                    LIMIT 6;
                    """
                ).fetchall()
            )
            estados_servicio = tuple(
                CategoriaDashboard(str(fila["etiqueta"]), float(fila["valor"] or 0))
                for fila in conexion.execute(
                    """
                    SELECT
                        CASE
                            WHEN COALESCE(estado_administrativo, 'OPERATIVA') = 'SUSPENDIDA' THEN 'Suspendidas'
                            WHEN estado_servicio = 'CORTADO' THEN 'Cortadas'
                            WHEN estado_servicio = 'INACTIVO' THEN 'Inactivas'
                            ELSE 'Activas'
                        END AS etiqueta,
                        COUNT(*) AS valor
                    FROM casas
                    WHERE eliminado_en IS NULL
                    GROUP BY
                        CASE
                            WHEN COALESCE(estado_administrativo, 'OPERATIVA') = 'SUSPENDIDA' THEN 'Suspendidas'
                            WHEN estado_servicio = 'CORTADO' THEN 'Cortadas'
                            WHEN estado_servicio = 'INACTIVO' THEN 'Inactivas'
                            ELSE 'Activas'
                        END
                    ORDER BY CASE etiqueta
                        WHEN 'Activas' THEN 1
                        WHEN 'Cortadas' THEN 2
                        WHEN 'Suspendidas' THEN 3
                        WHEN 'Inactivas' THEN 4
                        ELSE 5
                    END;
                    """
                ).fetchall()
            )
            antiguedad_deuda = tuple(
                CategoriaDashboard(str(fila["etiqueta"]), float(fila["valor"] or 0) / 100.0)
                for fila in conexion.execute(
                    """
                    SELECT
                        CASE
                            WHEN dias_vencidos BETWEEN 0 AND 30 THEN '0-30 dias'
                            WHEN dias_vencidos BETWEEN 31 AND 60 THEN '31-60 dias'
                            WHEN dias_vencidos BETWEEN 61 AND 90 THEN '61-90 dias'
                            ELSE '+90 dias'
                        END AS etiqueta,
                        SUM(saldo_pendiente_centavos) AS valor
                    FROM (
                        SELECT
                            c.saldo_pendiente_centavos,
                            CAST(
                                julianday(date('now', 'localtime')) - julianday(date(c.fecha_vencimiento))
                                AS INTEGER
                            ) AS dias_vencidos
                        FROM cargos c
                        INNER JOIN casas ca ON ca.id = c.casa_id
                        WHERE ca.estado_servicio IN ('ACTIVO', 'CORTADO')
                          AND c.estado IN ('PENDIENTE', 'PARCIAL', 'VENCIDO')
                          AND c.saldo_pendiente_centavos > 0
                          AND date(c.fecha_vencimiento) <= date('now', 'localtime')
                          AND c.anulado_en IS NULL
                    )
                    GROUP BY
                        CASE
                            WHEN dias_vencidos BETWEEN 0 AND 30 THEN '0-30 dias'
                            WHEN dias_vencidos BETWEEN 31 AND 60 THEN '31-60 dias'
                            WHEN dias_vencidos BETWEEN 61 AND 90 THEN '61-90 dias'
                            ELSE '+90 dias'
                        END
                    ORDER BY CASE etiqueta
                        WHEN '0-30 dias' THEN 1
                        WHEN '31-60 dias' THEN 2
                        WHEN '61-90 dias' THEN 3
                        ELSE 4
                    END;
                    """
                ).fetchall()
            )
            fila_resumen = conexion.execute(
                """
                SELECT
                    (SELECT COUNT(*)
                     FROM casas
                     WHERE eliminado_en IS NULL
                       AND estado_servicio = 'CORTADO') AS casas_cortadas,
                    (SELECT COUNT(*)
                     FROM casas
                     WHERE eliminado_en IS NULL
                       AND COALESCE(estado_administrativo, 'OPERATIVA') = 'SUSPENDIDA') AS casas_suspendidas,
                    (SELECT COUNT(*)
                     FROM vw_cargos_pendientes_ordenados) AS cargos_pendientes,
                    (SELECT COUNT(DISTINCT casa_id)
                     FROM cargos
                     WHERE estado = 'VENCIDO'
                       AND saldo_pendiente_centavos > 0
                       AND anulado_en IS NULL) AS casas_vencidas,
                    (SELECT COUNT(*)
                     FROM pagos
                     WHERE estado = 'CONFIRMADO'
                       AND date(fecha_pago) = date('now', 'localtime')) AS pagos_hoy,
                    (SELECT COALESCE(SUM(total_ingresos_centavos), 0)
                     FROM vw_ingresos_por_fecha
                     WHERE fecha = date('now', 'localtime')) AS ingresos_hoy_centavos,
                    (SELECT COUNT(*)
                     FROM vw_planes_pago_activos) AS planes_activos
                """
            ).fetchone()
            ultimo_pago = conexion.execute(
                """
                SELECT
                    p.fecha_pago,
                    p.total_pagado_centavos,
                    a.nombre_completo AS abonado_nombre,
                    COALESCE(u.nombre_usuario, u.nombre_completo, 'Sistema') AS cobrador
                FROM pagos p
                LEFT JOIN abonados a ON a.id = p.abonado_id
                LEFT JOIN usuarios u ON u.id = p.usuario_cobrador_id
                WHERE p.estado = 'CONFIRMADO'
                ORDER BY datetime(p.fecha_pago) DESC, p.id DESC
                LIMIT 1;
                """
            ).fetchone()

        insights = self._construir_insights_reales(fila_resumen, ultimo_pago)
        return AnaliticaDashboard(
            recaudacion_mensual=recaudacion,
            deuda_por_barrio=deuda_por_barrio,
            estados_servicio=estados_servicio,
            antiguedad_deuda=antiguedad_deuda,
            insights=insights,
        )

    @staticmethod
    def _contar(conexion: object, consulta: str, parametros: tuple[object, ...] = ()) -> int:
        return int(conexion.execute(consulta, parametros).fetchone()[0] or 0)

    @staticmethod
    def _sumar(conexion: object, consulta: str) -> int:
        return int(conexion.execute(consulta).fetchone()[0] or 0)

    @staticmethod
    def _formatear_lps(valor_centavos: int) -> str:
        return f"L {valor_centavos / 100:,.2f}"

    def _construir_insights_reales(
        self,
        fila_resumen: object,
        ultimo_pago: object,
    ) -> tuple[InsightDashboard, ...]:
        fecha_ultimo_pago = "Sin pagos confirmados"
        detalle_ultimo_pago = "No hay actividad de cobro registrada todavia."
        valor_ultimo_pago = "Sin registro"
        if ultimo_pago is not None:
            fecha_ultimo_pago = self._formatear_fecha_hora(str(ultimo_pago["fecha_pago"] or ""))
            valor_ultimo_pago = self._formatear_lps(int(ultimo_pago["total_pagado_centavos"] or 0))
            detalle_ultimo_pago = (
                f"{ultimo_pago['abonado_nombre'] or 'Abonado sin nombre'} · "
                f"{fecha_ultimo_pago} por {ultimo_pago['cobrador'] or 'Sistema'}."
            )

        casas_cortadas = int(fila_resumen["casas_cortadas"] or 0)
        casas_suspendidas = int(fila_resumen["casas_suspendidas"] or 0)
        cargos_pendientes = int(fila_resumen["cargos_pendientes"] or 0)
        casas_vencidas = int(fila_resumen["casas_vencidas"] or 0)
        pagos_hoy = int(fila_resumen["pagos_hoy"] or 0)
        ingresos_hoy = int(fila_resumen["ingresos_hoy_centavos"] or 0)
        planes_activos = int(fila_resumen["planes_activos"] or 0)

        return (
            InsightDashboard(
                "Servicios comprometidos",
                str(casas_cortadas + casas_suspendidas),
                f"{casas_cortadas} cortadas y {casas_suspendidas} suspendidas requieren seguimiento.",
            ),
            InsightDashboard(
                "Pagos registrados hoy",
                str(pagos_hoy),
                f"{self._formatear_lps(ingresos_hoy)} confirmados durante la jornada actual.",
            ),
            InsightDashboard(
                "Cargos pendientes",
                str(cargos_pendientes),
                f"{casas_vencidas} casa(s) ya presentan deuda vencida.",
            ),
            InsightDashboard(
                "Planes de pago activos",
                str(planes_activos),
                "Acuerdos vigentes que deben mantenerse bajo seguimiento operativo.",
            ),
            InsightDashboard(
                "Ultimo pago registrado",
                valor_ultimo_pago,
                detalle_ultimo_pago,
            ),
        )

    @staticmethod
    def _formatear_fecha_hora(valor: str) -> str:
        if not valor:
            return "Sin fecha"
        try:
            fecha = datetime.fromisoformat(valor)
        except ValueError:
            return valor
        return fecha.strftime("%d/%m/%Y %I:%M %p")


class RepositorioModuloPrincipalMemoria:
    """Repositorio de respaldo para pruebas o ejecuciones sin SQLite."""

    def obtener_metricas_dashboard(self) -> tuple[MetricaDashboard, ...]:
        return (
            MetricaDashboard("ingresos_hoy", "Ingresos de hoy", "L 0.00", "Sin pagos confirmados hoy."),
            MetricaDashboard("ingresos_mes", "Ingresos del mes", "L 0.00", "Sin pagos registrados."),
            MetricaDashboard("deuda", "Deuda pendiente", "L 0.00", "Sin cargos pendientes."),
            MetricaDashboard("casas_mora", "Casas con deuda vencida", "0", "Sin mora registrada."),
            MetricaDashboard("abonados_activos", "Abonados activos", "0", "Sin datos cargados."),
            MetricaDashboard("casas_activas", "Casas activas", "0", "Sin datos cargados."),
        )

    def obtener_analitica_dashboard(self) -> AnaliticaDashboard:
        return AnaliticaDashboard(
            recaudacion_mensual=(),
            deuda_por_barrio=(),
            estados_servicio=(),
            antiguedad_deuda=(),
            insights=(
                InsightDashboard("Servicios comprometidos", "0", "Sin incidencias activas."),
                InsightDashboard("Pagos registrados hoy", "0", "No hay pagos confirmados en esta jornada."),
                InsightDashboard("Cargos pendientes", "0", "No existen cargos pendientes cargados."),
                InsightDashboard("Planes de pago activos", "0", "Sin acuerdos activos en este entorno."),
                InsightDashboard("Ultimo pago registrado", "Sin registro", "No hay pagos confirmados."),
            ),
        )
