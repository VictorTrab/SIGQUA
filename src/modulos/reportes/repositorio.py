"""Persistencia SQLite del modulo de reportes."""

from __future__ import annotations

from contextlib import closing
from typing import Protocol

from comun.base_datos import GestorBaseDatos
from modulos.reportes.entidades import (
    FiltrosReportes,
    REPORTE_ABONADOS_ESTADO,
    REPORTE_CASAS_ESTADO,
    REPORTE_DEUDA_ACTIVA,
    REPORTE_HISTORIAL_PAGOS,
    REPORTE_INGRESOS_DIARIOS,
    EstadoReportes,
    IndicadorReporte,
    TablaReporte,
)


class RepositorioReportes(Protocol):
    """Contrato de consultas para reportes basicos."""

    def obtener_estado(self, fecha_desde: str = "", fecha_hasta: str = "") -> EstadoReportes:
        """Obtiene indicadores y tablas del tablero."""


class RepositorioReportesSQLite:
    """Consultas SQLite de reportes operativos del prototipo."""

    def __init__(self, gestor_base_datos: GestorBaseDatos) -> None:
        self._gestor_base_datos = gestor_base_datos

    def obtener_estado(self, fecha_desde: str = "", fecha_hasta: str = "") -> EstadoReportes:
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            indicadores = self._obtener_indicadores(
                conexion,
                fecha_desde=fecha_desde,
                fecha_hasta=fecha_hasta,
            )
            tablas = (
                self._reporte_abonados_por_estado(conexion),
                self._reporte_casas_por_estado(conexion),
                self._reporte_deuda_activa(conexion),
                self._reporte_historial_pagos(
                    conexion,
                    fecha_desde=fecha_desde,
                    fecha_hasta=fecha_hasta,
                ),
                self._reporte_ingresos_diarios(
                    conexion,
                    fecha_desde=fecha_desde,
                    fecha_hasta=fecha_hasta,
                ),
            )
        return EstadoReportes(
            indicadores=indicadores,
            tablas=tablas,
            filtros=FiltrosReportes(
                fecha_desde=fecha_desde,
                fecha_hasta=fecha_hasta,
            ),
        )

    def _obtener_indicadores(
        self,
        conexion: object,
        fecha_desde: str = "",
        fecha_hasta: str = "",
    ) -> tuple[IndicadorReporte, ...]:
        total_abonados = self._escalar(conexion, "SELECT COUNT(*) FROM abonados WHERE eliminado_en IS NULL;")
        total_casas = self._escalar(conexion, "SELECT COUNT(*) FROM casas WHERE eliminado_en IS NULL;")
        deuda_activa = self._escalar(
            conexion,
            """
            SELECT COALESCE(SUM(c.saldo_pendiente_centavos), 0)
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
        mora = self._escalar(
            conexion,
            """
            SELECT COALESCE(SUM(c.saldo_pendiente_centavos), 0)
            FROM cargos c
            INNER JOIN casas ca ON ca.id = c.casa_id
            INNER JOIN conceptos_cobro cc ON cc.id = c.concepto_id
            WHERE ca.estado_servicio = 'ACTIVO'
              AND c.estado IN ('PENDIENTE', 'PARCIAL', 'VENCIDO')
              AND c.saldo_pendiente_centavos > 0
              AND c.anulado_en IS NULL
              AND (cc.tipo = 'MORA' OR cc.codigo = 'MORA');
            """,
        )
        ingresos = self._escalar(
            conexion,
            f"""
            SELECT COALESCE(SUM(total_pagado_centavos), 0)
            FROM pagos
            WHERE estado = 'CONFIRMADO'
              {self._fragmento_rango_pagos(fecha_desde, fecha_hasta, incluir_and=True)};
            """,
        )
        detalle_ingresos = "Pagos confirmados"
        if fecha_desde or fecha_hasta:
            detalle_ingresos = self._descripcion_rango(fecha_desde, fecha_hasta)
        return (
            IndicadorReporte("Abonados", str(total_abonados), "Registros no eliminados"),
            IndicadorReporte("Casas", str(total_casas), "Casas operativas registradas"),
            IndicadorReporte("Deuda activa", self._moneda(deuda_activa), "Sin recargo por mora"),
            IndicadorReporte("Recargo mora", self._moneda(mora), "Separado de deuda base"),
            IndicadorReporte("Ingresos", self._moneda(ingresos), detalle_ingresos),
        )

    def _reporte_abonados_por_estado(self, conexion: object) -> TablaReporte:
        filas = conexion.execute(
            """
            SELECT estado, COUNT(*) AS total
            FROM abonados
            WHERE eliminado_en IS NULL
            GROUP BY estado
            ORDER BY estado;
            """
        ).fetchall()
        return TablaReporte(
            codigo=REPORTE_ABONADOS_ESTADO,
            titulo="Abonados por estado",
            descripcion="Conteo de abonados activos e inactivos.",
            columnas=("Estado", "Total"),
            filas=tuple((str(fila["estado"]), str(fila["total"])) for fila in filas),
        )

    def _reporte_casas_por_estado(self, conexion: object) -> TablaReporte:
        filas = conexion.execute(
            """
            SELECT estado_servicio, COUNT(*) AS total
            FROM casas
            WHERE eliminado_en IS NULL
            GROUP BY estado_servicio
            ORDER BY estado_servicio;
            """
        ).fetchall()
        return TablaReporte(
            codigo=REPORTE_CASAS_ESTADO,
            titulo="Casas por estado",
            descripcion="Distribucion de casas por estado del servicio.",
            columnas=("Estado", "Total"),
            filas=tuple((str(fila["estado_servicio"]), str(fila["total"])) for fila in filas),
        )

    def _reporte_deuda_activa(self, conexion: object) -> TablaReporte:
        filas = conexion.execute(
            """
            SELECT
                printf('CA-%03d', ca.id) AS casa_codigo,
                a.nombre_completo AS abonado_nombre,
                ca.estado_servicio,
                COALESCE(
                    SUM(CASE WHEN cc.tipo <> 'MORA' THEN c.saldo_pendiente_centavos ELSE 0 END),
                    0
                ) AS deuda_base_centavos,
                COALESCE(
                    SUM(CASE WHEN cc.tipo = 'MORA' OR cc.codigo = 'MORA' THEN c.saldo_pendiente_centavos ELSE 0 END),
                    0
                ) AS mora_centavos,
                COALESCE(SUM(c.saldo_pendiente_centavos), 0) AS total_centavos
            FROM cargos c
            INNER JOIN casas ca ON ca.id = c.casa_id
            INNER JOIN abonados a ON a.id = ca.abonado_id
            INNER JOIN conceptos_cobro cc ON cc.id = c.concepto_id
            WHERE ca.estado_servicio = 'ACTIVO'
              AND c.estado IN ('PENDIENTE', 'PARCIAL', 'VENCIDO')
              AND c.saldo_pendiente_centavos > 0
              AND c.anulado_en IS NULL
            GROUP BY ca.id, a.id
            ORDER BY total_centavos DESC, ca.id ASC
            LIMIT 50;
            """
        ).fetchall()
        return TablaReporte(
            codigo=REPORTE_DEUDA_ACTIVA,
            titulo="Deuda vencida/pendiente de casas activas",
            descripcion="Deuda base y recargo por mora separados para casas activas.",
            columnas=("Casa", "Abonado", "Estado", "Deuda base", "Mora", "Total"),
            filas=tuple(
                (
                    str(fila["casa_codigo"]),
                    str(fila["abonado_nombre"]),
                    str(fila["estado_servicio"]),
                    self._moneda(int(fila["deuda_base_centavos"] or 0)),
                    self._moneda(int(fila["mora_centavos"] or 0)),
                    self._moneda(int(fila["total_centavos"] or 0)),
                )
                for fila in filas
            ),
        )

    def _reporte_historial_pagos(
        self,
        conexion: object,
        fecha_desde: str = "",
        fecha_hasta: str = "",
    ) -> TablaReporte:
        filas = conexion.execute(
            f"""
            SELECT
                COALESCE(co.numero_comprobante, 'Sin comprobante') AS comprobante,
                COALESCE(p.tipo_pago, 'MENSUALIDAD') AS tipo_pago,
                printf('CA-%03d', p.casa_id) AS casa_codigo,
                a.nombre_completo AS abonado_nombre,
                mp.nombre AS metodo_pago,
                u.nombre_usuario AS usuario,
                p.total_pagado_centavos,
                p.fecha_pago
            FROM pagos p
            INNER JOIN abonados a ON a.id = p.abonado_id
            INNER JOIN metodos_pago mp ON mp.id = p.metodo_pago_id
            INNER JOIN usuarios u ON u.id = p.usuario_cobrador_id
            LEFT JOIN comprobantes co ON co.pago_id = p.id
            WHERE p.estado = 'CONFIRMADO'
              {self._fragmento_rango_pagos(fecha_desde, fecha_hasta, incluir_and=True)}
            ORDER BY p.fecha_pago DESC, p.id DESC
            LIMIT 50;
            """
        ).fetchall()
        return TablaReporte(
            codigo=REPORTE_HISTORIAL_PAGOS,
            titulo="Historial de pagos",
            descripcion=(
                "Pagos confirmados con metodo y usuario cobrador. "
                + self._descripcion_rango(fecha_desde, fecha_hasta)
            ),
            columnas=("Recibo", "Tipo", "Casa", "Abonado", "Metodo", "Usuario", "Total", "Fecha"),
            filas=tuple(
                (
                    str(fila["comprobante"]),
                    str(fila["tipo_pago"]),
                    str(fila["casa_codigo"]),
                    str(fila["abonado_nombre"]),
                    str(fila["metodo_pago"]),
                    str(fila["usuario"]),
                    self._moneda(int(fila["total_pagado_centavos"] or 0)),
                    str(fila["fecha_pago"] or ""),
                )
                for fila in filas
            ),
        )

    def _reporte_ingresos_diarios(
        self,
        conexion: object,
        fecha_desde: str = "",
        fecha_hasta: str = "",
    ) -> TablaReporte:
        filas = conexion.execute(
            f"""
            SELECT
                date(fecha_pago) AS fecha,
                COUNT(*) AS total_pagos,
                COALESCE(SUM(total_pagado_centavos), 0) AS total_centavos
            FROM pagos
            WHERE estado = 'CONFIRMADO'
              {self._fragmento_rango_pagos(fecha_desde, fecha_hasta, incluir_and=True)}
            GROUP BY date(fecha_pago)
            ORDER BY date(fecha_pago) DESC
            LIMIT 60;
            """
        ).fetchall()
        return TablaReporte(
            codigo=REPORTE_INGRESOS_DIARIOS,
            titulo="Ingresos diarios",
            descripcion="Consolidado diario de pagos confirmados dentro del rango aplicado.",
            columnas=("Fecha", "Pagos", "Ingresos"),
            filas=tuple(
                (
                    str(fila["fecha"] or ""),
                    str(fila["total_pagos"] or 0),
                    self._moneda(int(fila["total_centavos"] or 0)),
                )
                for fila in filas
            ),
        )

    @staticmethod
    def _fragmento_rango_pagos(
        fecha_desde: str,
        fecha_hasta: str,
        *,
        incluir_and: bool = False,
    ) -> str:
        condiciones: list[str] = []
        if fecha_desde:
            condiciones.append(f"date(fecha_pago) >= date('{fecha_desde}')")
        if fecha_hasta:
            condiciones.append(f"date(fecha_pago) <= date('{fecha_hasta}')")
        if not condiciones:
            return ""
        prefijo = "AND " if incluir_and else "WHERE "
        return prefijo + " AND ".join(condiciones)

    @staticmethod
    def _descripcion_rango(fecha_desde: str, fecha_hasta: str) -> str:
        if fecha_desde and fecha_hasta:
            return f"Rango {fecha_desde} a {fecha_hasta}."
        if fecha_desde:
            return f"Desde {fecha_desde}."
        if fecha_hasta:
            return f"Hasta {fecha_hasta}."
        return "Sin filtro de fechas."

    @staticmethod
    def _escalar(conexion: object, consulta: str) -> int:
        fila = conexion.execute(consulta).fetchone()
        return int(fila[0] or 0) if fila is not None else 0

    @staticmethod
    def _moneda(valor_centavos: int) -> str:
        return f"L {valor_centavos / 100:,.2f}"
