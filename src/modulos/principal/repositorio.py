"""Contratos e implementaciones de persistencia del modulo principal."""

from __future__ import annotations

from contextlib import closing
from typing import Protocol

from comun.base_datos import GestorBaseDatos
from modulos.principal.entidades import (
    AnaliticaDashboard,
    CategoriaDashboard,
    InsightDashboard,
    MetricaDashboard,
    PuntoSerieDashboard,
    ResumenOperativoCabecera,
)


class RepositorioModuloPrincipal(Protocol):
    """Define las consultas necesarias para el dashboard inicial."""

    def obtener_metricas_dashboard(self) -> tuple[MetricaDashboard, ...]:
        """Obtiene las metricas operativas del dashboard."""

    def obtener_analitica_dashboard(self) -> AnaliticaDashboard:
        """Obtiene series y paneles analiticos para la pantalla de inicio."""

    def obtener_resumen_operativo_cabecera(self) -> ResumenOperativoCabecera:
        """Obtiene datos compactos para el encabezado operativo del shell."""

    def listar_eventos_criticos_sistema(self, limite: int = 10) -> tuple[tuple[str, str], ...]:
        """Lista advertencias y errores tecnicos pendientes para notificaciones."""


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
                FROM cargos c
                INNER JOIN casas ca ON ca.id = c.casa_id
                INNER JOIN conceptos_cobro cc ON cc.id = c.concepto_id
                WHERE ca.estado_servicio = 'ACTIVO'
                  AND c.estado IN ('PENDIENTE', 'PARCIAL', 'VENCIDO')
                  AND c.saldo_pendiente_centavos > 0
                  AND c.anulado_en IS NULL
                  AND cc.tipo <> 'MORA';
                """,
            )
            pagos_mes_centavos = self._sumar(
                conexion,
                """
                SELECT COALESCE(SUM(total_pagado_centavos), 0)
                FROM pagos
                WHERE strftime('%Y-%m', fecha_pago) = strftime('%Y-%m', 'now')
                  AND estado = 'CONFIRMADO';
                """,
            )
            casas_en_mora = self._contar(
                conexion,
                """
                SELECT COUNT(DISTINCT casa_id)
                FROM cargos c
                INNER JOIN casas ca ON ca.id = c.casa_id
                WHERE ca.estado_servicio = 'ACTIVO'
                  AND c.estado = 'VENCIDO'
                  AND c.saldo_pendiente_centavos > 0
                  AND c.anulado_en IS NULL;
                """,
            )

        return (
            MetricaDashboard("abonados", "Abonados activos", str(abonados_activos), "Registros operativos"),
            MetricaDashboard("casas", "Casas activas", str(casas_activas), "Servicios habilitados"),
            MetricaDashboard("deuda", "Deuda pendiente", self._formatear_lps(deuda_centavos), "Cargos pendientes"),
            MetricaDashboard("pagos_mes", "Pagos del mes", self._formatear_lps(pagos_mes_centavos), "Ingresos registrados"),
            MetricaDashboard("mora", "Casas en mora", str(casas_en_mora), "Con cargos vencidos"),
        )

    def obtener_analitica_dashboard(self) -> AnaliticaDashboard:
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            recaudacion = tuple(
                PuntoSerieDashboard(str(fila["etiqueta"]), float(fila["valor"] or 0) / 100.0)
                for fila in conexion.execute(
                    """
                    WITH RECURSIVE meses(offseto, fecha_base) AS (
                        SELECT 5, date('now', 'start of month', '-5 month')
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
                        b.nombre AS etiqueta,
                        COALESCE(SUM(cg.saldo_pendiente_centavos), 0) AS valor
                    FROM cargos cg
                    JOIN casas c ON c.id = cg.casa_id
                    JOIN barrios b ON b.id = c.barrio_id
                    INNER JOIN conceptos_cobro cc ON cc.id = cg.concepto_id
                    WHERE c.estado_servicio = 'ACTIVO'
                      AND cg.estado IN ('PENDIENTE', 'PARCIAL', 'VENCIDO')
                      AND cg.saldo_pendiente_centavos > 0
                      AND cg.anulado_en IS NULL
                      AND cc.tipo <> 'MORA'
                    GROUP BY b.id, b.nombre
                    HAVING valor > 0
                    ORDER BY valor DESC, b.nombre ASC
                    LIMIT 5;
                    """
                ).fetchall()
            )
            estados_servicio = tuple(
                CategoriaDashboard(str(fila["etiqueta"]), float(fila["valor"] or 0))
                for fila in conexion.execute(
                    """
                    SELECT estado_servicio AS etiqueta, COUNT(*) AS valor
                    FROM casas
                    WHERE eliminado_en IS NULL
                    GROUP BY estado_servicio
                    ORDER BY COUNT(*) DESC, estado_servicio ASC;
                    """
                ).fetchall()
            )

            ticket_promedio = self._sumar(
                conexion,
                """
                SELECT COALESCE(AVG(total_pagado_centavos), 0)
                FROM pagos
                WHERE estado = 'CONFIRMADO';
                """,
            )
            hogares_suspendidos = self._contar(
                conexion,
                """
                SELECT COUNT(*)
                FROM casas
                WHERE eliminado_en IS NULL
                  AND estado_servicio IN ('SUSPENDIDO', 'CORTADO');
                """,
            )
            abonados_con_deuda = self._contar(
                conexion,
                """
                SELECT COUNT(DISTINCT c.abonado_id)
                FROM cargos c
                INNER JOIN casas ca ON ca.id = c.casa_id
                WHERE ca.estado_servicio = 'ACTIVO'
                  AND c.estado IN ('PENDIENTE', 'PARCIAL', 'VENCIDO')
                  AND c.saldo_pendiente_centavos > 0
                  AND c.anulado_en IS NULL;
                """,
            )
            total_ingresos = self._sumar(
                conexion,
                """
                SELECT COALESCE(SUM(total_pagado_centavos), 0)
                FROM pagos
                WHERE estado = 'CONFIRMADO';
                """,
            )

        insights = (
            InsightDashboard(
                "Ticket promedio",
                self._formatear_lps(ticket_promedio),
                "Valor medio por pago confirmado en el sistema.",
            ),
            InsightDashboard(
                "Abonados con deuda",
                str(abonados_con_deuda),
                "Usuarios con al menos un cargo pendiente o vencido.",
            ),
            InsightDashboard(
                "Servicios comprometidos",
                str(hogares_suspendidos),
                "Casas en estado suspendido o cortado que requieren seguimiento.",
            ),
            InsightDashboard(
                "Ingresos acumulados",
                self._formatear_lps(total_ingresos),
                "Total historico confirmado en recaudacion.",
            ),
        )
        return AnaliticaDashboard(
            recaudacion_mensual=recaudacion,
            deuda_por_barrio=deuda_por_barrio,
            estados_servicio=estados_servicio,
            insights=insights,
        )

    def obtener_resumen_operativo_cabecera(self) -> ResumenOperativoCabecera:
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            pagos_registrados_hoy = self._contar(
                conexion,
                """
                SELECT COUNT(*)
                FROM pagos
                WHERE date(fecha_pago, 'localtime') = date('now', 'localtime')
                  AND estado = 'CONFIRMADO';
                """,
            )
            meses_alerta_corte = self._obtener_entero_configuracion(
                conexion,
                "cobro.meses_para_corte",
                predeterminado=5,
            )
            casas_con_deuda_critica = self._contar(
                conexion,
                """
                SELECT COUNT(*)
                FROM (
                    SELECT c.casa_id
                    FROM cargos c
                    INNER JOIN casas ca ON ca.id = c.casa_id
                    INNER JOIN conceptos_cobro cc ON cc.id = c.concepto_id
                    WHERE ca.estado_servicio = 'ACTIVO'
                      AND c.estado = 'VENCIDO'
                      AND c.saldo_pendiente_centavos > 0
                      AND c.anulado_en IS NULL
                      AND c.periodo_id IS NOT NULL
                      AND cc.tipo <> 'MORA'
                    GROUP BY c.casa_id
                    HAVING COUNT(DISTINCT c.periodo_id) >= ?
                ) resumen;
                """,
                (meses_alerta_corte,),
            )
            respaldo_automatico = bool(
                self._obtener_entero_configuracion(
                    conexion,
                    "sistema.respaldo_automatico",
                    predeterminado=0,
                )
            )
            fila_respaldo = conexion.execute(
                """
                SELECT
                    COALESCE(generado_en, '') AS generado_en,
                    COALESCE(estado, '') AS estado
                FROM historial_respaldos
                ORDER BY generado_en DESC, id DESC
                LIMIT 1;
                """
            ).fetchone()
            fila_eventos = conexion.execute(
                """
                SELECT
                    COALESCE(SUM(CASE WHEN severidad = 'ADVERTENCIA' AND resuelto_en IS NULL THEN 1 ELSE 0 END), 0) AS advertencias,
                    COALESCE(SUM(CASE WHEN severidad IN ('ERROR', 'CRITICO') AND resuelto_en IS NULL THEN 1 ELSE 0 END), 0) AS errores
                FROM eventos_tecnicos;
                """
            ).fetchone()
            fila_ultimo_evento = conexion.execute(
                """
                SELECT
                    COALESCE(severidad, 'INFO') AS severidad,
                    COALESCE(mensaje, '') AS mensaje
                FROM eventos_tecnicos
                ORDER BY registrado_en DESC, id DESC
                LIMIT 1;
                """
            ).fetchone()

        return ResumenOperativoCabecera(
            pagos_registrados_hoy=pagos_registrados_hoy,
            casas_con_deuda_critica=casas_con_deuda_critica,
            meses_alerta_corte=meses_alerta_corte,
            respaldo_automatico=respaldo_automatico,
            ultimo_respaldo_en=str(fila_respaldo["generado_en"] or "") if fila_respaldo else "",
            ultimo_respaldo_estado=str(fila_respaldo["estado"] or "") if fila_respaldo else "",
            eventos_advertencia=int(fila_eventos["advertencias"] or 0) if fila_eventos else 0,
            eventos_error=int(fila_eventos["errores"] or 0) if fila_eventos else 0,
            ultimo_evento_mensaje=str(fila_ultimo_evento["mensaje"] or "") if fila_ultimo_evento else "",
            ultimo_evento_severidad=str(fila_ultimo_evento["severidad"] or "INFO")
            if fila_ultimo_evento
            else "INFO",
        )

    def listar_eventos_criticos_sistema(self, limite: int = 10) -> tuple[tuple[str, str], ...]:
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            filas = conexion.execute(
                """
                SELECT
                    COALESCE(severidad, 'INFO') AS severidad,
                    COALESCE(mensaje, '') AS mensaje
                FROM eventos_tecnicos
                WHERE severidad IN ('ADVERTENCIA', 'ERROR', 'CRITICO')
                  AND resuelto_en IS NULL
                ORDER BY registrado_en DESC, id DESC
                LIMIT ?;
                """,
                (limite,),
            ).fetchall()
        return tuple(
            (str(fila["severidad"] or "INFO"), str(fila["mensaje"] or ""))
            for fila in filas
            if str(fila["mensaje"] or "").strip()
        )

    @staticmethod
    def _contar(conexion: object, consulta: str, parametros: tuple[object, ...] = ()) -> int:
        return int(conexion.execute(consulta, parametros).fetchone()[0] or 0)

    @staticmethod
    def _sumar(conexion: object, consulta: str) -> int:
        return int(conexion.execute(consulta).fetchone()[0] or 0)

    @staticmethod
    def _obtener_entero_configuracion(
        conexion: object,
        clave: str,
        *,
        predeterminado: int,
    ) -> int:
        fila = conexion.execute(
            """
            SELECT COALESCE(valor, ?) AS valor
            FROM configuracion_sistema
            WHERE clave = ?
            LIMIT 1;
            """,
            (str(predeterminado), clave),
        ).fetchone()
        try:
            return int((fila["valor"] if fila else predeterminado) or predeterminado)
        except (TypeError, ValueError):
            return predeterminado

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

    def obtener_analitica_dashboard(self) -> AnaliticaDashboard:
        return AnaliticaDashboard(
            recaudacion_mensual=(),
            deuda_por_barrio=(),
            estados_servicio=(),
            insights=(
                InsightDashboard("Ticket promedio", "L 0.00", "Sin pagos registrados."),
                InsightDashboard("Abonados con deuda", "0", "Sin mora registrada."),
                InsightDashboard("Servicios comprometidos", "0", "Sin incidencias activas."),
                InsightDashboard("Ingresos acumulados", "L 0.00", "Sin historial financiero."),
            ),
        )

    def obtener_resumen_operativo_cabecera(self) -> ResumenOperativoCabecera:
        return ResumenOperativoCabecera(
            pagos_registrados_hoy=0,
            casas_con_deuda_critica=0,
            meses_alerta_corte=5,
            respaldo_automatico=False,
            ultimo_respaldo_en="",
            ultimo_respaldo_estado="",
            eventos_advertencia=0,
            eventos_error=0,
            ultimo_evento_mensaje="",
            ultimo_evento_severidad="INFO",
        )

    def listar_eventos_criticos_sistema(self, limite: int = 10) -> tuple[tuple[str, str], ...]:
        return ()
