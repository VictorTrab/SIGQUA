"""Persistencia SQLite del modulo de reportes administrativos."""

from __future__ import annotations

from contextlib import closing
from typing import Protocol

from comun.base_datos import GestorBaseDatos
from modulos.reportes.entidades import (
    EstadoReportes,
    FiltroReporte,
    IndicadorReporte,
    OpcionFiltroReporte,
    REPORTE_ABONADOS_SIN_DEUDA,
    REPORTE_DEUDA_ABONADOS_ESTADO,
    REPORTE_HISTORIAL_ABONADO,
    REPORTE_HISTORIAL_CASA,
    REPORTE_INGRESOS_DIARIOS,
    REPORTE_INGRESOS_MENSUALES,
    REPORTE_PLANES_ACTIVOS,
    REPORTE_SERVICIO_CASAS,
    TablaReporte,
    TarjetaReporte,
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
        codigo = codigo_reporte or (catalogo[0].codigo if catalogo else REPORTE_DEUDA_ABONADOS_ESTADO)
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
            sin_deuda = self._escalar(
                conexion,
                """
                SELECT COUNT(*)
                FROM (
                    SELECT abonado_id
                    FROM vw_reportes_deuda_abonado_estado
                    GROUP BY abonado_id
                    HAVING SUM(deuda_base_centavos + mora_centavos + saldo_plan_centavos) = 0
                );
                """,
            )
            planes_activos = self._escalar(
                conexion,
                """
                SELECT COUNT(*)
                FROM vw_reportes_planes_pago_activos_admin
                WHERE estado = 'ACTIVO';
                """,
            )
        return (
            IndicadorReporte("Ingresos del mes", self._moneda(ingresos_mes), "Pagos confirmados del mes actual"),
            IndicadorReporte("Total de pagos", str(total_pagos_mes), "Registros confirmados del mes actual"),
            IndicadorReporte("Deuda administrativa", self._moneda(deuda_admin), "Deuda base, mora y saldo vivo de plan"),
            IndicadorReporte("Abonados sin deuda", str(sin_deuda), "Sin deuda base, mora ni saldo vivo"),
            IndicadorReporte("Planes activos", str(planes_activos), "Planes vigentes con saldo pendiente"),
        )

    def _construir_filtros_visibles(
        self,
        codigo_reporte: str,
        filtros: dict[str, str],
    ) -> tuple[FiltroReporte, ...]:
        visibles: list[FiltroReporte] = []
        if codigo_reporte in {REPORTE_DEUDA_ABONADOS_ESTADO, REPORTE_ABONADOS_SIN_DEUDA, REPORTE_SERVICIO_CASAS, REPORTE_PLANES_ACTIVOS}:
            visibles.append(
                FiltroReporte(
                    clave="estado_abonado",
                    etiqueta="Estado del abonado",
                    tipo="combo",
                    opciones=self._opciones_estado_abonado(),
                    valor=filtros.get("estado_abonado", "TODOS"),
                )
            )
            visibles.append(
                FiltroReporte(
                    clave="barrio",
                    etiqueta="Barrio",
                    tipo="combo",
                    opciones=self._opciones_barrios(),
                    valor=filtros.get("barrio", "TODOS"),
                )
            )
        if codigo_reporte in {REPORTE_DEUDA_ABONADOS_ESTADO, REPORTE_SERVICIO_CASAS}:
            visibles.append(
                FiltroReporte(
                    clave="estado_servicio",
                    etiqueta="Estado del servicio",
                    tipo="combo",
                    opciones=self._opciones_estado_servicio(),
                    valor=filtros.get("estado_servicio", "TODOS"),
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
        if codigo_reporte in {REPORTE_INGRESOS_MENSUALES, REPORTE_INGRESOS_DIARIOS, REPORTE_HISTORIAL_ABONADO, REPORTE_HISTORIAL_CASA}:
            visibles.append(
                FiltroReporte(
                    clave="fecha_desde",
                    etiqueta="Desde",
                    tipo="fecha",
                    valor=filtros.get("fecha_desde", ""),
                )
            )
            visibles.append(
                FiltroReporte(
                    clave="fecha_hasta",
                    etiqueta="Hasta",
                    tipo="fecha",
                    valor=filtros.get("fecha_hasta", ""),
                )
            )
        if codigo_reporte == REPORTE_HISTORIAL_ABONADO:
            visibles.append(
                FiltroReporte(
                    clave="abonado_id",
                    etiqueta="Abonado",
                    tipo="combo",
                    opciones=self._opciones_abonados(),
                    valor=filtros.get("abonado_id", "TODOS"),
                )
            )
        if codigo_reporte == REPORTE_HISTORIAL_CASA:
            visibles.append(
                FiltroReporte(
                    clave="casa_id",
                    etiqueta="Casa",
                    tipo="combo",
                    opciones=self._opciones_casas(),
                    valor=filtros.get("casa_id", "TODOS"),
                )
            )
        return tuple(visibles)

    def _obtener_tabla(self, codigo_reporte: str, filtros: dict[str, str]) -> TablaReporte:
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            if codigo_reporte == REPORTE_DEUDA_ABONADOS_ESTADO:
                return self._tabla_deuda_abonados_estado(conexion, filtros)
            if codigo_reporte == REPORTE_ABONADOS_SIN_DEUDA:
                return self._tabla_abonados_sin_deuda(conexion, filtros)
            if codigo_reporte == REPORTE_SERVICIO_CASAS:
                return self._tabla_servicio_casas(conexion, filtros)
            if codigo_reporte == REPORTE_INGRESOS_MENSUALES:
                return self._tabla_ingresos_mensuales(conexion, filtros)
            if codigo_reporte == REPORTE_INGRESOS_DIARIOS:
                return self._tabla_ingresos_diarios(conexion, filtros)
            if codigo_reporte == REPORTE_HISTORIAL_ABONADO:
                return self._tabla_historial_abonado(conexion, filtros)
            if codigo_reporte == REPORTE_HISTORIAL_CASA:
                return self._tabla_historial_casa(conexion, filtros)
            return self._tabla_planes_activos(conexion, filtros)

    def _tabla_deuda_abonados_estado(self, conexion: object, filtros: dict[str, str]) -> TablaReporte:
        condiciones = ["1 = 1"]
        parametros: list[object] = []
        self._aplicar_filtros_estado(condiciones, parametros, filtros)
        consulta = f"""
            SELECT
                casa_codigo,
                abonado_nombre,
                estado_abonado,
                estado_servicio,
                barrio_nombre,
                deuda_base_centavos,
                mora_centavos,
                saldo_plan_centavos
            FROM vw_reportes_deuda_abonado_estado
            WHERE {' AND '.join(condiciones)}
            ORDER BY (deuda_base_centavos + mora_centavos + saldo_plan_centavos) DESC, casa_id ASC;
        """
        filas = conexion.execute(consulta, tuple(parametros)).fetchall()
        incluir_mora = filtros.get("incluir_mora", "1") != "0"
        return TablaReporte(
            codigo=REPORTE_DEUDA_ABONADOS_ESTADO,
            titulo="Deuda total por abonados activos e inactivos",
            descripcion="La deuda se agrupa por el estado del abonado responsable actual.",
            columnas=("Casa", "Abonado", "Estado abonado", "Servicio", "Barrio", "Deuda base", "Mora", "Saldo plan", "Total"),
            filas=tuple(
                (
                    str(fila["casa_codigo"]),
                    str(fila["abonado_nombre"]),
                    str(fila["estado_abonado"]),
                    str(fila["estado_servicio"]),
                    str(fila["barrio_nombre"] or ""),
                    self._moneda(int(fila["deuda_base_centavos"] or 0)),
                    self._moneda(int(fila["mora_centavos"] or 0)),
                    self._moneda(int(fila["saldo_plan_centavos"] or 0)),
                    self._moneda(
                        int(fila["deuda_base_centavos"] or 0)
                        + (int(fila["mora_centavos"] or 0) if incluir_mora else 0)
                        + int(fila["saldo_plan_centavos"] or 0)
                    ),
                )
                for fila in filas
            ),
        )

    def _tabla_abonados_sin_deuda(self, conexion: object, filtros: dict[str, str]) -> TablaReporte:
        condiciones = ["1 = 1"]
        parametros: list[object] = []
        if filtros.get("estado_abonado", "TODOS") != "TODOS":
            condiciones.append("estado_abonado = ?")
            parametros.append(filtros["estado_abonado"])
        if filtros.get("barrio", "TODOS") != "TODOS":
            condiciones.append("barrio_nombre = ?")
            parametros.append(filtros["barrio"])
        consulta = f"""
            SELECT
                abonado_id,
                abonado_nombre,
                estado_abonado,
                COUNT(*) AS total_casas,
                GROUP_CONCAT(casa_codigo, ', ') AS casas
            FROM vw_reportes_deuda_abonado_estado
            WHERE {' AND '.join(condiciones)}
            GROUP BY abonado_id, abonado_nombre, estado_abonado
            HAVING SUM(deuda_base_centavos + mora_centavos + saldo_plan_centavos) = 0
            ORDER BY abonado_nombre ASC;
        """
        filas = conexion.execute(consulta, tuple(parametros)).fetchall()
        return TablaReporte(
            codigo=REPORTE_ABONADOS_SIN_DEUDA,
            titulo="Abonados sin deuda",
            descripcion="No presentan deuda base, mora ni saldo vivo de plan.",
            columnas=("Abonado", "Estado", "Casas", "Detalle de casas"),
            filas=tuple(
                (
                    str(fila["abonado_nombre"]),
                    str(fila["estado_abonado"]),
                    str(fila["total_casas"] or 0),
                    str(fila["casas"] or ""),
                )
                for fila in filas
            ),
        )

    def _tabla_servicio_casas(self, conexion: object, filtros: dict[str, str]) -> TablaReporte:
        condiciones = ["1 = 1"]
        parametros: list[object] = []
        self._aplicar_filtros_estado(condiciones, parametros, filtros)
        consulta = f"""
            SELECT casa_codigo, abonado_nombre, estado_abonado, barrio_nombre, estado_servicio, estado_administrativo,
                   CASE WHEN tiene_servicio = 1 THEN 'Con servicio' ELSE 'Sin servicio' END AS resumen_servicio
            FROM vw_reportes_servicio_casas
            WHERE {' AND '.join(condiciones)}
            ORDER BY tiene_servicio DESC, casa_id ASC;
        """
        filas = conexion.execute(consulta, tuple(parametros)).fetchall()
        return TablaReporte(
            codigo=REPORTE_SERVICIO_CASAS,
            titulo="Casas con servicio y sin servicio",
            descripcion="Resume el estado fisico del servicio por casa.",
            columnas=("Casa", "Abonado", "Estado abonado", "Barrio", "Estado fisico", "Estado administrativo", "Resumen"),
            filas=tuple(
                (
                    str(fila["casa_codigo"]),
                    str(fila["abonado_nombre"]),
                    str(fila["estado_abonado"]),
                    str(fila["barrio_nombre"] or ""),
                    str(fila["estado_servicio"]),
                    str(fila["estado_administrativo"]),
                    str(fila["resumen_servicio"]),
                )
                for fila in filas
            ),
        )

    def _tabla_ingresos_mensuales(self, conexion: object, filtros: dict[str, str]) -> TablaReporte:
        fragmento, parametros = self._fragmento_rango("fecha_pago", filtros)
        consulta = f"""
            SELECT
                strftime('%Y-%m', fecha_pago) AS periodo,
                COUNT(*) AS total_pagos,
                COALESCE(SUM(total_pagado_centavos), 0) AS total_centavos
            FROM pagos
            WHERE estado = 'CONFIRMADO'
              {fragmento}
            GROUP BY strftime('%Y-%m', fecha_pago)
            ORDER BY periodo DESC;
        """
        filas = conexion.execute(consulta, tuple(parametros)).fetchall()
        return TablaReporte(
            codigo=REPORTE_INGRESOS_MENSUALES,
            titulo="Resumen mensual de ingresos",
            descripcion="Consolidado mensual de pagos confirmados en el rango aplicado.",
            columnas=("Periodo", "Pagos", "Ingresos"),
            filas=tuple(
                (
                    str(fila["periodo"] or ""),
                    str(fila["total_pagos"] or 0),
                    self._moneda(int(fila["total_centavos"] or 0)),
                )
                for fila in filas
            ),
        )

    def _tabla_ingresos_diarios(self, conexion: object, filtros: dict[str, str]) -> TablaReporte:
        fragmento, parametros = self._fragmento_rango("fecha_pago", filtros)
        consulta = f"""
            SELECT
                date(fecha_pago) AS fecha,
                COUNT(*) AS total_pagos,
                COALESCE(SUM(total_pagado_centavos), 0) AS total_centavos
            FROM pagos
            WHERE estado = 'CONFIRMADO'
              {fragmento}
            GROUP BY date(fecha_pago)
            ORDER BY fecha DESC;
        """
        filas = conexion.execute(consulta, tuple(parametros)).fetchall()
        return TablaReporte(
            codigo=REPORTE_INGRESOS_DIARIOS,
            titulo="Detalle diario de ingresos",
            descripcion="Detalle por dia dentro del rango aplicado.",
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

    def _tabla_historial_abonado(self, conexion: object, filtros: dict[str, str]) -> TablaReporte:
        condiciones = ["1 = 1"]
        parametros: list[object] = []
        fragmento, parametros_fechas = self._fragmento_rango("fecha_pago", filtros)
        if fragmento:
            condiciones.append(fragmento.replace("AND ", "", 1))
            parametros.extend(parametros_fechas)
        if filtros.get("abonado_id", "TODOS") != "TODOS":
            condiciones.append("CAST(abonado_id AS TEXT) = ?")
            parametros.append(filtros["abonado_id"])
        consulta = f"""
            SELECT numero_comprobante, abonado_nombre, casa_codigo, metodo_pago, usuario_registro, total_pagado_centavos, fecha_pago
            FROM vw_reportes_historial_pagos_admin
            WHERE {' AND '.join(condiciones)}
            ORDER BY fecha_pago DESC, pago_id DESC;
        """
        filas = conexion.execute(consulta, tuple(parametros)).fetchall()
        return TablaReporte(
            codigo=REPORTE_HISTORIAL_ABONADO,
            titulo="Historial por abonado",
            descripcion="Pagos confirmados filtrados por abonado responsable.",
            columnas=("Recibo", "Abonado", "Casa", "Metodo", "Usuario", "Total", "Fecha"),
            filas=tuple(
                (
                    str(fila["numero_comprobante"]),
                    str(fila["abonado_nombre"]),
                    str(fila["casa_codigo"]),
                    str(fila["metodo_pago"]),
                    str(fila["usuario_registro"]),
                    self._moneda(int(fila["total_pagado_centavos"] or 0)),
                    str(fila["fecha_pago"] or ""),
                )
                for fila in filas
            ),
        )

    def _tabla_historial_casa(self, conexion: object, filtros: dict[str, str]) -> TablaReporte:
        condiciones = ["1 = 1"]
        parametros: list[object] = []
        fragmento, parametros_fechas = self._fragmento_rango("fecha_pago", filtros)
        if fragmento:
            condiciones.append(fragmento.replace("AND ", "", 1))
            parametros.extend(parametros_fechas)
        if filtros.get("casa_id", "TODOS") != "TODOS":
            condiciones.append("CAST(casa_id AS TEXT) = ?")
            parametros.append(filtros["casa_id"])
        consulta = f"""
            SELECT numero_comprobante, casa_codigo, abonado_nombre, metodo_pago, usuario_registro, total_pagado_centavos, fecha_pago
            FROM vw_reportes_historial_pagos_admin
            WHERE {' AND '.join(condiciones)}
            ORDER BY fecha_pago DESC, pago_id DESC;
        """
        filas = conexion.execute(consulta, tuple(parametros)).fetchall()
        return TablaReporte(
            codigo=REPORTE_HISTORIAL_CASA,
            titulo="Historial por casa",
            descripcion="Pagos confirmados filtrados por casa.",
            columnas=("Recibo", "Casa", "Abonado", "Metodo", "Usuario", "Total", "Fecha"),
            filas=tuple(
                (
                    str(fila["numero_comprobante"]),
                    str(fila["casa_codigo"]),
                    str(fila["abonado_nombre"]),
                    str(fila["metodo_pago"]),
                    str(fila["usuario_registro"]),
                    self._moneda(int(fila["total_pagado_centavos"] or 0)),
                    str(fila["fecha_pago"] or ""),
                )
                for fila in filas
            ),
        )

    def _tabla_planes_activos(self, conexion: object, filtros: dict[str, str]) -> TablaReporte:
        condiciones = ["estado = 'ACTIVO'"]
        parametros: list[object] = []
        if filtros.get("estado_abonado", "TODOS") != "TODOS":
            condiciones.append("estado_abonado = ?")
            parametros.append(filtros["estado_abonado"])
        if filtros.get("barrio", "TODOS") != "TODOS":
            condiciones.append("barrio_nombre = ?")
            parametros.append(filtros["barrio"])
        consulta = f"""
            SELECT plan_codigo, casa_codigo, abonado_nombre, barrio_nombre, tipo_plan, deuda_financiada_centavos,
                   monto_activacion_centavos, prima_centavos, cuota_regular_centavos, cuotas_pendientes, saldo_vivo_centavos
            FROM vw_reportes_planes_pago_activos_admin
            WHERE {' AND '.join(condiciones)}
            ORDER BY plan_pago_id DESC;
        """
        filas = conexion.execute(consulta, tuple(parametros)).fetchall()
        return TablaReporte(
            codigo=REPORTE_PLANES_ACTIVOS,
            titulo="Planes de pago activos",
            descripcion="Estado administrativo de planes vigentes y su saldo pendiente.",
            columnas=("Plan", "Casa", "Abonado", "Barrio", "Tipo", "Deuda financiada", "Activacion", "Prima", "Cuota", "Cuotas pendientes", "Saldo vivo"),
            filas=tuple(
                (
                    str(fila["plan_codigo"]),
                    str(fila["casa_codigo"]),
                    str(fila["abonado_nombre"]),
                    str(fila["barrio_nombre"] or ""),
                    str(fila["tipo_plan"]),
                    self._moneda(int(fila["deuda_financiada_centavos"] or 0)),
                    self._moneda(int(fila["monto_activacion_centavos"] or 0)),
                    self._moneda(int(fila["prima_centavos"] or 0)),
                    self._moneda(int(fila["cuota_regular_centavos"] or 0)),
                    str(fila["cuotas_pendientes"] or 0),
                    self._moneda(int(fila["saldo_vivo_centavos"] or 0)),
                )
                for fila in filas
            ),
        )

    def _opciones_abonados(self) -> tuple[OpcionFiltroReporte, ...]:
        consulta = """
            SELECT DISTINCT abonado_id, abonado_nombre
            FROM vw_reportes_deuda_abonado_estado
            ORDER BY abonado_nombre ASC;
        """
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            filas = conexion.execute(consulta).fetchall()
        return (OpcionFiltroReporte("TODOS", "Todos"),) + tuple(
            OpcionFiltroReporte(str(fila["abonado_id"]), str(fila["abonado_nombre"]))
            for fila in filas
        )

    def _opciones_casas(self) -> tuple[OpcionFiltroReporte, ...]:
        consulta = """
            SELECT DISTINCT casa_id, casa_codigo
            FROM vw_reportes_servicio_casas
            ORDER BY casa_id ASC;
        """
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            filas = conexion.execute(consulta).fetchall()
        return (OpcionFiltroReporte("TODOS", "Todas"),) + tuple(
            OpcionFiltroReporte(str(fila["casa_id"]), str(fila["casa_codigo"]))
            for fila in filas
        )

    def _opciones_barrios(self) -> tuple[OpcionFiltroReporte, ...]:
        consulta = """
            SELECT DISTINCT barrio_nombre
            FROM vw_reportes_deuda_abonado_estado
            WHERE trim(COALESCE(barrio_nombre, '')) <> ''
            ORDER BY barrio_nombre ASC;
        """
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            filas = conexion.execute(consulta).fetchall()
        return (OpcionFiltroReporte("TODOS", "Todos"),) + tuple(
            OpcionFiltroReporte(str(fila["barrio_nombre"]), str(fila["barrio_nombre"]))
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
            OpcionFiltroReporte("SUSPENDIDA", "Suspendidos"),
            OpcionFiltroReporte("INACTIVO", "Inactivos"),
        )

    @staticmethod
    def _aplicar_filtros_estado(
        condiciones: list[str],
        parametros: list[object],
        filtros: dict[str, str],
    ) -> None:
        if filtros.get("estado_abonado", "TODOS") != "TODOS":
            condiciones.append("estado_abonado = ?")
            parametros.append(filtros["estado_abonado"])
        if filtros.get("estado_servicio", "TODOS") != "TODOS":
            condiciones.append("estado_servicio = ?")
            parametros.append(filtros["estado_servicio"])
        if filtros.get("barrio", "TODOS") != "TODOS":
            condiciones.append("barrio_nombre = ?")
            parametros.append(filtros["barrio"])

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
            "barrio": "TODOS",
            "abonado_id": "TODOS",
            "casa_id": "TODOS",
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
