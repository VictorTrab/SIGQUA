"""Persistencia SQLite del modulo de reportes administrativos."""

from __future__ import annotations

from contextlib import closing
from typing import Protocol

from comun.base_datos import GestorBaseDatos
from modulos.reportes.entidades import (
    EstadoReportes,
    FiltroReporte,
    IndicadorReporte,
    ORIENTACION_HORIZONTAL,
    ORIENTACION_VERTICAL,
    OpcionFiltroReporte,
    REPORTE_DEUDA_ABONADOS_ESTADO,
    REPORTE_INGRESOS_MENSUALES_DIARIOS,
    REPORTE_SERVICIO_CASAS,
    TablaReporte,
    TarjetaReporte,
    TIPO_FILTRO_BUSQUEDA,
)


class RepositorioReportes(Protocol):
    """Contrato de consultas administrativas para reportes."""

    def obtener_estado(
        self,
        catalogo: tuple[TarjetaReporte, ...],
        codigo_reporte: str,
        filtros: dict[str, str],
    ) -> EstadoReportes:
        """Obtiene el estado completo del modulo."""


class RepositorioReportesSQLite:
    """Consultas SQLite del modulo de reportes administrativos."""

    def __init__(self, gestor_base_datos: GestorBaseDatos) -> None:
        self._gestor_base_datos = gestor_base_datos

    def obtener_estado(
        self,
        catalogo: tuple[TarjetaReporte, ...],
        codigo_reporte: str,
        filtros: dict[str, str],
    ) -> EstadoReportes:
        codigo = self._resolver_codigo_reporte(catalogo, codigo_reporte)
        filtros_normalizados = self._normalizar_filtros(filtros)
        indicadores = self._obtener_indicadores()
        filtros_visibles = self._construir_filtros_visibles(codigo, filtros_normalizados)
        tabla_actual = self._obtener_tabla(codigo, filtros_normalizados)
        return EstadoReportes(
            indicadores=indicadores,
            catalogo=catalogo,
            reporte_actual=codigo,
            filtros_visibles=filtros_visibles,
            filtros_aplicados=filtros_normalizados,
            tabla_actual=tabla_actual,
        )

    def _resolver_codigo_reporte(
        self,
        catalogo: tuple[TarjetaReporte, ...],
        codigo_reporte: str,
    ) -> str:
        codigos_validos = {tarjeta.codigo for tarjeta in catalogo}
        if codigo_reporte in codigos_validos:
            return codigo_reporte
        return catalogo[0].codigo if catalogo else REPORTE_DEUDA_ABONADOS_ESTADO

    def _obtener_indicadores(self) -> tuple[IndicadorReporte, ...]:
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            ingresos_mes = self._escalar(
                conexion,
                """
                SELECT COALESCE(SUM(total_pagado_centavos), 0)
                FROM pagos
                WHERE estado = 'CONFIRMADO'
                  AND strftime('%Y-%m', fecha_pago) = strftime('%Y-%m', 'now', 'localtime');
                """,
            )
            total_pagos_mes = self._escalar(
                conexion,
                """
                SELECT COUNT(*)
                FROM pagos
                WHERE estado = 'CONFIRMADO'
                  AND strftime('%Y-%m', fecha_pago) = strftime('%Y-%m', 'now', 'localtime');
                """,
            )
            deuda_admin = self._escalar(
                conexion,
                """
                SELECT COALESCE(SUM(deuda_base_centavos + mora_centavos + saldo_plan_centavos), 0)
                FROM vw_reportes_deuda_abonado_estado;
                """,
            )
            casas_con_servicio = self._escalar(
                conexion,
                """
                SELECT COUNT(*)
                FROM vw_reportes_servicio_casas
                WHERE tiene_servicio = 1;
                """,
            )
            casas_sin_servicio = self._escalar(
                conexion,
                """
                SELECT COUNT(*)
                FROM vw_reportes_servicio_casas
                WHERE tiene_servicio = 0;
                """,
            )
        return (
            IndicadorReporte("Ingresos del mes", self._moneda(ingresos_mes), "Pagos confirmados del mes actual"),
            IndicadorReporte("Pagos confirmados", str(total_pagos_mes), "Registros confirmados del mes actual"),
            IndicadorReporte("Deuda administrativa", self._moneda(deuda_admin), "Deuda base, mora y saldo vivo de plan"),
            IndicadorReporte("Casas con servicio", str(casas_con_servicio), "Viviendas con servicio activo"),
            IndicadorReporte("Casas sin servicio", str(casas_sin_servicio), "Viviendas cortadas o inactivas"),
        )

    def _construir_filtros_visibles(
        self,
        codigo_reporte: str,
        filtros: dict[str, str],
    ) -> tuple[FiltroReporte, ...]:
        visibles: list[FiltroReporte] = []
        if codigo_reporte in {REPORTE_DEUDA_ABONADOS_ESTADO, REPORTE_SERVICIO_CASAS}:
            visibles.extend(
                (
                    FiltroReporte(
                        clave="estado_abonado",
                        etiqueta="Estado del abonado",
                        tipo="combo",
                        opciones=self._opciones_estado_abonado(),
                        valor=filtros.get("estado_abonado", "TODOS"),
                    ),
                    FiltroReporte(
                        clave="barrio",
                        etiqueta="Barrio",
                        tipo=TIPO_FILTRO_BUSQUEDA,
                        opciones=self._opciones_barrios(),
                        valor=filtros.get("barrio", "TODOS"),
                    ),
                )
            )
        if codigo_reporte == REPORTE_DEUDA_ABONADOS_ESTADO:
            visibles.append(
                FiltroReporte(
                    clave="incluir_mora",
                    etiqueta="Incluir mora",
                    tipo="bool",
                    opciones=(
                        OpcionFiltroReporte("1", "Si"),
                        OpcionFiltroReporte("0", "No"),
                    ),
                    valor=filtros.get("incluir_mora", "1"),
                )
            )
        if codigo_reporte == REPORTE_SERVICIO_CASAS:
            visibles.extend(
                (
                    FiltroReporte(
                        clave="disponibilidad",
                        etiqueta="Disponibilidad",
                        tipo="combo",
                        opciones=self._opciones_disponibilidad(),
                        valor=filtros.get("disponibilidad", "TODOS"),
                    ),
                    FiltroReporte(
                        clave="estado_servicio",
                        etiqueta="Estado fisico",
                        tipo="combo",
                        opciones=self._opciones_estado_servicio(),
                        valor=filtros.get("estado_servicio", "TODOS"),
                    ),
                    FiltroReporte(
                        clave="estado_administrativo",
                        etiqueta="Estado administrativo",
                        tipo="combo",
                        opciones=self._opciones_estado_administrativo(),
                        valor=filtros.get("estado_administrativo", "TODOS"),
                    ),
                )
            )
        if codigo_reporte == REPORTE_INGRESOS_MENSUALES_DIARIOS:
            visibles.extend(
                (
                    FiltroReporte(
                        clave="fecha_desde",
                        etiqueta="Desde",
                        tipo="fecha",
                        valor=filtros.get("fecha_desde", ""),
                    ),
                    FiltroReporte(
                        clave="fecha_hasta",
                        etiqueta="Hasta",
                        tipo="fecha",
                        valor=filtros.get("fecha_hasta", ""),
                    ),
                )
            )
        return tuple(visibles)

    def _obtener_tabla(self, codigo_reporte: str, filtros: dict[str, str]) -> TablaReporte:
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            if codigo_reporte == REPORTE_SERVICIO_CASAS:
                return self._tabla_servicio_casas(conexion, filtros)
            if codigo_reporte == REPORTE_INGRESOS_MENSUALES_DIARIOS:
                return self._tabla_ingresos_mensuales_diarios(conexion, filtros)
            return self._tabla_deuda_abonados_estado(conexion, filtros)

    def _tabla_deuda_abonados_estado(self, conexion: object, filtros: dict[str, str]) -> TablaReporte:
        condiciones = ["a.eliminado_en IS NULL"]
        parametros: list[object] = []
        if filtros.get("estado_abonado", "TODOS") != "TODOS":
            condiciones.append("a.estado = ?")
            parametros.append(filtros["estado_abonado"])
        if filtros.get("barrio", "TODOS") != "TODOS":
            condiciones.append(
                "deuda.barrio_nombre = "
                "(SELECT nombre FROM barrios WHERE id = ? LIMIT 1)"
            )
            parametros.append(filtros["barrio"])
        consulta = f"""
            WITH meses_por_casa AS (
                SELECT
                    cg.casa_id,
                    COUNT(
                        DISTINCT CASE
                            WHEN cc.codigo = 'SERVICIO_MENSUAL'
                             AND cg.estado IN ('PENDIENTE', 'PARCIAL', 'VENCIDO')
                             AND cg.saldo_pendiente_centavos > 0
                             AND cg.anulado_en IS NULL
                             AND NOT EXISTS (
                                SELECT 1
                                FROM planes_pago_cargos ppc
                                INNER JOIN planes_pago pp ON pp.id = ppc.plan_pago_id
                                WHERE ppc.cargo_id = cg.id
                                  AND pp.estado = 'ACTIVO'
                             )
                            THEN COALESCE(cg.periodo_id, cg.id)
                        END
                    ) AS meses_vencidos
                FROM cargos cg
                INNER JOIN conceptos_cobro cc ON cc.id = cg.concepto_id
                GROUP BY cg.casa_id
            )
            SELECT
                a.id AS abonado_id,
                a.dni AS abonado_dni,
                a.nombre_completo AS abonado_nombre,
                a.estado AS estado_abonado,
                GROUP_CONCAT(DISTINCT deuda.barrio_nombre) AS barrios,
                COUNT(DISTINCT deuda.casa_id) AS total_casas,
                COALESCE(SUM(meses_por_casa.meses_vencidos), 0) AS meses_vencidos,
                COALESCE(SUM(deuda.deuda_base_centavos), 0) AS deuda_base_centavos,
                COALESCE(SUM(deuda.mora_centavos), 0) AS mora_centavos,
                COALESCE(SUM(deuda.saldo_plan_centavos), 0) AS saldo_plan_centavos
            FROM abonados a
            LEFT JOIN vw_reportes_deuda_abonado_estado deuda ON deuda.abonado_id = a.id
            LEFT JOIN meses_por_casa ON meses_por_casa.casa_id = deuda.casa_id
            WHERE {' AND '.join(condiciones)}
            GROUP BY a.id, a.dni, a.nombre_completo, a.estado
            ORDER BY (deuda_base_centavos + mora_centavos + saldo_plan_centavos) DESC, abonado_nombre ASC;
        """
        filas = conexion.execute(consulta, tuple(parametros)).fetchall()
        incluir_mora = filtros.get("incluir_mora", "1") != "0"
        deuda_total_centavos = sum(
            int(fila["deuda_base_centavos"] or 0)
            + (int(fila["mora_centavos"] or 0) if incluir_mora else 0)
            + int(fila["saldo_plan_centavos"] or 0)
            for fila in filas
        )
        return TablaReporte(
            codigo=REPORTE_DEUDA_ABONADOS_ESTADO,
            titulo="Deuda global por abonado",
            descripcion="Consolidado administrativo global; no sustituye el documento individual de cobro.",
            columnas=("DNI", "Abonado", "Barrio", "Casas", "Meses vencidos", "Deuda total", "Estado"),
            filas=tuple(
                (
                    str(fila["abonado_dni"] or ""),
                    str(fila["abonado_nombre"]),
                    str(fila["barrios"] or ""),
                    str(fila["total_casas"] or 0),
                    str(fila["meses_vencidos"] or 0),
                    self._moneda(
                        int(fila["deuda_base_centavos"] or 0)
                        + (int(fila["mora_centavos"] or 0) if incluir_mora else 0)
                        + int(fila["saldo_plan_centavos"] or 0)
                    ),
                    str(fila["estado_abonado"]),
                )
                for fila in filas
            ),
            resumen=(
                ("Abonados listados", str(len(filas))),
                ("Deuda consolidada", self._moneda(deuda_total_centavos)),
            ),
            orientacion=ORIENTACION_HORIZONTAL,
        )

    def _tabla_servicio_casas(self, conexion: object, filtros: dict[str, str]) -> TablaReporte:
        condiciones = ["c.eliminado_en IS NULL"]
        parametros: list[object] = []
        if filtros.get("estado_abonado", "TODOS") != "TODOS":
            condiciones.append("a.estado = ?")
            parametros.append(filtros["estado_abonado"])
        if filtros.get("estado_servicio", "TODOS") != "TODOS":
            condiciones.append("c.estado_servicio = ?")
            parametros.append(filtros["estado_servicio"])
        if filtros.get("estado_administrativo", "TODOS") != "TODOS":
            condiciones.append("c.estado_administrativo = ?")
            parametros.append(filtros["estado_administrativo"])
        if filtros.get("disponibilidad", "TODOS") == "CON_SERVICIO":
            condiciones.append("c.estado_servicio = 'ACTIVO'")
        elif filtros.get("disponibilidad", "TODOS") == "SIN_SERVICIO":
            condiciones.append("c.estado_servicio IN ('CORTADO', 'INACTIVO')")
        if filtros.get("barrio", "TODOS") != "TODOS":
            condiciones.append("b.id = ?")
            parametros.append(filtros["barrio"])
        consulta = f"""
            SELECT
                printf('CA-%03d', c.id) AS casa_codigo,
                a.nombre_completo AS abonado_nombre,
                a.dni AS abonado_dni,
                COALESCE(b.nombre, '') AS barrio_nombre,
                c.estado_servicio,
                c.estado_administrativo,
                a.estado AS estado_abonado,
                COALESCE(c.actualizado_en, '') AS ultima_actualizacion
            FROM casas c
            INNER JOIN abonados a ON a.id = c.abonado_id
            LEFT JOIN barrios b ON b.id = c.barrio_id
            WHERE {' AND '.join(condiciones)}
            ORDER BY c.estado_servicio ASC, c.id ASC;
        """
        filas = conexion.execute(consulta, tuple(parametros)).fetchall()
        conteos_fisicos = {"ACTIVO": 0, "CORTADO": 0, "INACTIVO": 0}
        conteos_administrativos = {"OPERATIVA": 0, "SUSPENDIDA": 0}
        conteos_abonados = {"ACTIVO": 0, "INACTIVO": 0}
        for fila in filas:
            estado_fisico = str(fila["estado_servicio"] or "")
            estado_administrativo = str(fila["estado_administrativo"] or "")
            estado_abonado = str(fila["estado_abonado"] or "")
            if estado_fisico in conteos_fisicos:
                conteos_fisicos[estado_fisico] += 1
            if estado_administrativo in conteos_administrativos:
                conteos_administrativos[estado_administrativo] += 1
            if estado_abonado in conteos_abonados:
                conteos_abonados[estado_abonado] += 1
        con_servicio = conteos_fisicos["ACTIVO"]
        sin_servicio = conteos_fisicos["CORTADO"] + conteos_fisicos["INACTIVO"]
        return TablaReporte(
            codigo=REPORTE_SERVICIO_CASAS,
            titulo="Estado del servicio por casa",
            descripcion="Disponibilidad y estados de las viviendas, sin informacion financiera.",
            columnas=(
                "Casa",
                "Abonado",
                "DNI",
                "Barrio",
                "Disponibilidad",
                "Estado fisico",
                "Estado administrativo",
                "Estado abonado",
                "Ultima actualizacion",
            ),
            filas=tuple(
                (
                    str(fila["casa_codigo"]),
                    str(fila["abonado_nombre"]),
                    str(fila["abonado_dni"] or ""),
                    str(fila["barrio_nombre"] or ""),
                    self._disponibilidad_servicio(str(fila["estado_servicio"])),
                    str(fila["estado_servicio"]),
                    str(fila["estado_administrativo"]),
                    str(fila["estado_abonado"]),
                    str(fila["ultima_actualizacion"] or ""),
                )
                for fila in filas
            ),
            resumen=(
                ("Casas listadas", str(len(filas))),
                ("Con servicio", str(con_servicio)),
                ("Sin servicio", str(sin_servicio)),
                ("Activas", str(conteos_fisicos["ACTIVO"])),
                ("Cortadas", str(conteos_fisicos["CORTADO"])),
                ("Inactivas", str(conteos_fisicos["INACTIVO"])),
                ("Operativas", str(conteos_administrativos["OPERATIVA"])),
                ("Suspendidas", str(conteos_administrativos["SUSPENDIDA"])),
                ("Abonados activos", str(conteos_abonados["ACTIVO"])),
                ("Abonados inactivos", str(conteos_abonados["INACTIVO"])),
            ),
            orientacion=ORIENTACION_HORIZONTAL,
        )

    def _tabla_ingresos_mensuales_diarios(self, conexion: object, filtros: dict[str, str]) -> TablaReporte:
        fragmento, parametros = self._fragmento_rango("fecha_pago", filtros)
        consulta = f"""
            SELECT
                strftime('%Y-%m', fecha_pago) AS mes,
                date(fecha_pago) AS fecha,
                COUNT(*) AS total_pagos,
                COALESCE(SUM(total_pagado_centavos), 0) AS total_centavos
            FROM pagos
            WHERE estado = 'CONFIRMADO'
              {fragmento}
            GROUP BY strftime('%Y-%m', fecha_pago), date(fecha_pago)
            ORDER BY mes DESC, fecha DESC;
        """
        filas = conexion.execute(consulta, tuple(parametros)).fetchall()
        return TablaReporte(
            codigo=REPORTE_INGRESOS_MENSUALES_DIARIOS,
            titulo="Ingresos mensuales con detalle diario",
            descripcion="Ingresos confirmados por mes con desglose diario.",
            columnas=("Mes", "Dia/Fecha", "Pagos", "Ingresos"),
            filas=tuple(
                (
                    str(fila["mes"] or ""),
                    str(fila["fecha"] or ""),
                    str(fila["total_pagos"] or 0),
                    self._moneda(int(fila["total_centavos"] or 0)),
                )
                for fila in filas
            ),
            resumen=(
                ("Pagos confirmados", str(sum(int(fila["total_pagos"] or 0) for fila in filas))),
                ("Ingresos del periodo", self._moneda(sum(int(fila["total_centavos"] or 0) for fila in filas))),
            ),
            orientacion=ORIENTACION_VERTICAL,
        )

    def _opciones_barrios(self) -> tuple[OpcionFiltroReporte, ...]:
        consulta = """
            SELECT DISTINCT b.id AS barrio_id, b.nombre AS barrio_nombre
            FROM barrios b
            INNER JOIN casas c ON c.barrio_id = b.id
            WHERE c.eliminado_en IS NULL
              AND trim(COALESCE(b.nombre, '')) <> ''
            ORDER BY b.nombre ASC;
        """
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            filas = conexion.execute(consulta).fetchall()
        return (OpcionFiltroReporte("TODOS", "Todos"),) + tuple(
            OpcionFiltroReporte(str(fila["barrio_id"]), str(fila["barrio_nombre"]))
            for fila in filas
        )

    @staticmethod
    def _opciones_estado_abonado() -> tuple[OpcionFiltroReporte, ...]:
        return (
            OpcionFiltroReporte("TODOS", "Todos"),
            OpcionFiltroReporte("ACTIVO", "Activos"),
            OpcionFiltroReporte("INACTIVO", "Inactivos"),
        )

    @staticmethod
    def _opciones_estado_servicio() -> tuple[OpcionFiltroReporte, ...]:
        return (
            OpcionFiltroReporte("TODOS", "Todos"),
            OpcionFiltroReporte("ACTIVO", "Activos"),
            OpcionFiltroReporte("CORTADO", "Cortados"),
            OpcionFiltroReporte("INACTIVO", "Inactivos"),
        )

    @staticmethod
    def _opciones_estado_administrativo() -> tuple[OpcionFiltroReporte, ...]:
        return (
            OpcionFiltroReporte("TODOS", "Todos"),
            OpcionFiltroReporte("OPERATIVA", "Operativas"),
            OpcionFiltroReporte("SUSPENDIDA", "Suspendidas"),
        )

    @staticmethod
    def _opciones_disponibilidad() -> tuple[OpcionFiltroReporte, ...]:
        return (
            OpcionFiltroReporte("TODOS", "Todas"),
            OpcionFiltroReporte("CON_SERVICIO", "Con servicio"),
            OpcionFiltroReporte("SIN_SERVICIO", "Sin servicio"),
        )

    @staticmethod
    def _disponibilidad_servicio(estado_servicio: str) -> str:
        return "CON SERVICIO" if estado_servicio == "ACTIVO" else "SIN SERVICIO"

    @staticmethod
    def _fragmento_rango(campo_fecha: str, filtros: dict[str, str]) -> tuple[str, list[object]]:
        condiciones: list[str] = []
        parametros: list[object] = []
        if filtros.get("fecha_desde", "").strip():
            condiciones.append(f"date({campo_fecha}) >= date(?)")
            parametros.append(filtros["fecha_desde"].strip())
        if filtros.get("fecha_hasta", "").strip():
            condiciones.append(f"date({campo_fecha}) <= date(?)")
            parametros.append(filtros["fecha_hasta"].strip())
        if not condiciones:
            return "", []
        return "AND " + " AND ".join(condiciones), parametros

    @staticmethod
    def _normalizar_filtros(filtros: dict[str, str] | None) -> dict[str, str]:
        base = {
            "estado_abonado": "TODOS",
            "estado_servicio": "TODOS",
            "estado_administrativo": "TODOS",
            "disponibilidad": "TODOS",
            "barrio": "TODOS",
            "fecha_desde": "",
            "fecha_hasta": "",
            "incluir_mora": "1",
        }
        if filtros:
            base.update({clave: str(valor) for clave, valor in filtros.items() if valor is not None})
        return base

    @staticmethod
    def _escalar(conexion: object, consulta: str) -> int:
        fila = conexion.execute(consulta).fetchone()
        return int(fila[0] or 0) if fila else 0

    @staticmethod
    def _moneda(valor_centavos: int) -> str:
        return f"L {valor_centavos / 100:,.2f}"
