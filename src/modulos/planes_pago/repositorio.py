"""Persistencia SQLite del modulo de planes de pago."""

from __future__ import annotations

from contextlib import closing
from dataclasses import dataclass
from typing import Protocol

from comun.base_datos import GestorBaseDatos
from modulos.planes_pago.entidades import (
    CuotaPlanPago,
    DetallePlanPago,
    FILTRO_PLANES_ACTIVOS,
    FILTRO_PLANES_CON_MORA,
    FILTRO_PLANES_SERVICIO,
    FILTRO_PLANES_TODOS,
    OpcionCasaPlanPago,
    PlanPago,
    ResumenPlanesPago,
)


SUBCONSULTA_CUOTAS = """
    SELECT
        plan_pago_id,
        COUNT(CASE WHEN estado = 'PAGADO' THEN 1 END) AS cuotas_pagadas_reales,
        COUNT(
            CASE
                WHEN estado IN ('PENDIENTE', 'PARCIAL', 'VENCIDO')
                 AND saldo_pendiente_centavos > 0
                THEN 1
            END
        ) AS cuotas_pendientes,
        COUNT(
            CASE
                WHEN estado = 'VENCIDO' AND saldo_pendiente_centavos > 0
                THEN 1
            END
        ) AS cuotas_en_mora,
        COALESCE(
            SUM(
                CASE
                    WHEN estado IN ('PENDIENTE', 'PARCIAL', 'VENCIDO')
                     AND saldo_pendiente_centavos > 0
                    THEN saldo_pendiente_centavos
                    ELSE 0
                END
            ),
            0
        ) AS saldo_pendiente_centavos,
        MIN(
            CASE
                WHEN estado IN ('PENDIENTE', 'PARCIAL', 'VENCIDO')
                 AND saldo_pendiente_centavos > 0
                THEN fecha_vencimiento
            END
        ) AS proxima_fecha
    FROM cuotas_plan_pago
    GROUP BY plan_pago_id
"""

SUBCONSULTA_DEUDA_CASA = """
    SELECT
        casa_id,
        COUNT(
            DISTINCT CASE
                WHEN estado IN ('PENDIENTE', 'PARCIAL', 'VENCIDO')
                 AND saldo_pendiente_centavos > 0
                THEN COALESCE(periodo_id, id)
            END
        ) AS meses_pendientes,
        COUNT(
            DISTINCT CASE
                WHEN estado = 'VENCIDO' AND saldo_pendiente_centavos > 0
                THEN COALESCE(periodo_id, id)
            END
        ) AS meses_en_mora,
        COALESCE(
            SUM(
                CASE
                    WHEN estado IN ('PENDIENTE', 'PARCIAL', 'VENCIDO')
                     AND saldo_pendiente_centavos > 0
                    THEN saldo_pendiente_centavos
                    ELSE 0
                END
            ),
            0
        ) AS deuda_total_centavos
    FROM cargos
    WHERE anulado_en IS NULL
    GROUP BY casa_id
"""


@dataclass(slots=True)
class RegistroGuardadoPlanPago:
    """Datos base persistidos de un plan antes de crear cuotas."""

    identificador: int
    casa_id: int
    abonado_id: int
    cantidad_cuotas: int


class RepositorioPlanesPago(Protocol):
    """Contrato minimo de persistencia para planes."""

    def listar(
        self,
        filtro: str = "",
        filtro_rapido: str = FILTRO_PLANES_TODOS,
        limite: int | None = None,
        desplazamiento: int = 0,
    ) -> list[PlanPago]:
        """Lista planes visibles."""

    def contar(self, filtro: str = "", filtro_rapido: str = FILTRO_PLANES_TODOS) -> int:
        """Cuenta planes visibles."""

    def obtener_resumen(self) -> ResumenPlanesPago:
        """Obtiene metricas de cabecera."""

    def obtener_por_id(self, plan_id: int) -> PlanPago | None:
        """Obtiene un plan puntual."""

    def obtener_detalle(self, plan_id: int) -> DetallePlanPago | None:
        """Obtiene detalle completo del plan."""

    def listar_casas_disponibles(self) -> list[OpcionCasaPlanPago]:
        """Lista casas con contexto suficiente para crear planes."""

    def guardar_plan(
        self,
        plan: PlanPago,
        cuotas: list[tuple[str, int]],
        cargos_vinculados: tuple[int, ...],
        actor_id: int | None = None,
    ) -> int:
        """Crea o actualiza un plan y sus cuotas."""

    def contar_cuotas_pagadas(self, plan_id: int) -> int:
        """Cuenta cuotas ya pagadas para validar edicion estructural."""

    def obtener_cargos_vinculables(
        self,
        casa_id: int,
        concepto_financiado: str,
    ) -> tuple[int, ...]:
        """Obtiene cargos pendientes compatibles con el concepto del plan."""


class RepositorioPlanesPagoSQLite:
    """Implementacion SQLite para planes de pago."""

    def __init__(self, gestor_base_datos: GestorBaseDatos) -> None:
        self._gestor_base_datos = gestor_base_datos

    def listar(
        self,
        filtro: str = "",
        filtro_rapido: str = FILTRO_PLANES_TODOS,
        limite: int | None = None,
        desplazamiento: int = 0,
    ) -> list[PlanPago]:
        condiciones, parametros = self._construir_filtros(filtro, filtro_rapido)
        paginacion = ""
        if limite is not None:
            paginacion = "LIMIT ? OFFSET ?"
            parametros.extend([limite, desplazamiento])
        consulta = f"""
            SELECT
                pp.id,
                pp.casa_id,
                printf('CA-%03d', pp.casa_id) AS casa_codigo,
                pp.abonado_id,
                a.nombre_completo AS abonado_nombre,
                a.dni AS abonado_dni,
                COALESCE(b.nombre, '') AS barrio_nombre,
                COALESCE(pp.tipo_plan, 'RECONEXION') AS tipo_plan,
                COALESCE(pp.concepto_financiado, 'RECONEXION') AS concepto_financiado,
                COALESCE(pp.prima_centavos, 0) AS prima_centavos,
                MAX(pp.monto_total_centavos - COALESCE(pp.prima_centavos, 0), 0) AS saldo_financiado_centavos,
                pp.monto_total_centavos,
                pp.cuota_regular_centavos,
                pp.cantidad_cuotas,
                COALESCE(qc.cuotas_pagadas_reales, pp.cuotas_pagadas, 0) AS cuotas_pagadas,
                COALESCE(qc.cuotas_pendientes, 0) AS cuotas_pendientes,
                COALESCE(qc.saldo_pendiente_centavos, 0) AS saldo_pendiente_centavos,
                COALESCE(qc.cuotas_en_mora, 0) AS cuotas_en_mora,
                COALESCE(qc.proxima_fecha, '') AS proxima_fecha,
                pp.estado,
                COALESCE(pp.observaciones, '') AS observaciones,
                COALESCE(pp.creado_en, '') AS creado_en,
                COALESCE(pp.actualizado_en, '') AS actualizado_en,
                COALESCE(uc.nombre_completo, uc.nombre_usuario, '') AS creado_por_nombre
            FROM planes_pago pp
            INNER JOIN abonados a ON a.id = pp.abonado_id
            INNER JOIN casas c ON c.id = pp.casa_id
            LEFT JOIN barrios b ON b.id = c.barrio_id
            LEFT JOIN usuarios uc ON uc.id = pp.creado_por
            LEFT JOIN ({SUBCONSULTA_CUOTAS}) qc ON qc.plan_pago_id = pp.id
            WHERE {' AND '.join(condiciones)}
            ORDER BY pp.id DESC
            {paginacion};
        """
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            filas = conexion.execute(consulta, tuple(parametros)).fetchall()
        return [self._fila_a_plan(fila) for fila in filas]

    def contar(self, filtro: str = "", filtro_rapido: str = FILTRO_PLANES_TODOS) -> int:
        condiciones, parametros = self._construir_filtros(filtro, filtro_rapido)
        consulta = f"""
            SELECT COUNT(*)
            FROM planes_pago pp
            INNER JOIN abonados a ON a.id = pp.abonado_id
            LEFT JOIN ({SUBCONSULTA_CUOTAS}) qc ON qc.plan_pago_id = pp.id
            WHERE {' AND '.join(condiciones)};
        """
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            return int(conexion.execute(consulta, tuple(parametros)).fetchone()[0] or 0)

    def obtener_resumen(self) -> ResumenPlanesPago:
        consulta = f"""
            SELECT
                COUNT(*) AS total_planes,
                SUM(CASE WHEN pp.estado = 'ACTIVO' THEN 1 ELSE 0 END) AS planes_activos,
                SUM(CASE WHEN COALESCE(qc.cuotas_en_mora, 0) > 0 THEN 1 ELSE 0 END) AS planes_con_mora,
                COALESCE(SUM(COALESCE(qc.saldo_pendiente_centavos, 0)), 0) AS saldo_pendiente_centavos
            FROM planes_pago pp
            LEFT JOIN ({SUBCONSULTA_CUOTAS}) qc ON qc.plan_pago_id = pp.id;
        """
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            fila = conexion.execute(consulta).fetchone()
        return ResumenPlanesPago(
            total_planes=int(fila["total_planes"] or 0),
            planes_activos=int(fila["planes_activos"] or 0),
            planes_con_mora=int(fila["planes_con_mora"] or 0),
            saldo_pendiente_centavos=int(fila["saldo_pendiente_centavos"] or 0),
        )

    def obtener_por_id(self, plan_id: int) -> PlanPago | None:
        consulta = f"""
            SELECT
                pp.id,
                pp.casa_id,
                printf('CA-%03d', pp.casa_id) AS casa_codigo,
                pp.abonado_id,
                a.nombre_completo AS abonado_nombre,
                a.dni AS abonado_dni,
                COALESCE(b.nombre, '') AS barrio_nombre,
                COALESCE(pp.tipo_plan, 'RECONEXION') AS tipo_plan,
                COALESCE(pp.concepto_financiado, 'RECONEXION') AS concepto_financiado,
                COALESCE(pp.prima_centavos, 0) AS prima_centavos,
                MAX(pp.monto_total_centavos - COALESCE(pp.prima_centavos, 0), 0) AS saldo_financiado_centavos,
                pp.monto_total_centavos,
                pp.cuota_regular_centavos,
                pp.cantidad_cuotas,
                COALESCE(qc.cuotas_pagadas_reales, pp.cuotas_pagadas, 0) AS cuotas_pagadas,
                COALESCE(qc.cuotas_pendientes, 0) AS cuotas_pendientes,
                COALESCE(qc.saldo_pendiente_centavos, 0) AS saldo_pendiente_centavos,
                COALESCE(qc.cuotas_en_mora, 0) AS cuotas_en_mora,
                COALESCE(qc.proxima_fecha, '') AS proxima_fecha,
                pp.estado,
                COALESCE(pp.observaciones, '') AS observaciones,
                COALESCE(pp.creado_en, '') AS creado_en,
                COALESCE(pp.actualizado_en, '') AS actualizado_en,
                COALESCE(uc.nombre_completo, uc.nombre_usuario, '') AS creado_por_nombre
            FROM planes_pago pp
            INNER JOIN abonados a ON a.id = pp.abonado_id
            INNER JOIN casas c ON c.id = pp.casa_id
            LEFT JOIN barrios b ON b.id = c.barrio_id
            LEFT JOIN usuarios uc ON uc.id = pp.creado_por
            LEFT JOIN ({SUBCONSULTA_CUOTAS}) qc ON qc.plan_pago_id = pp.id
            WHERE pp.id = ?
            LIMIT 1;
        """
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            fila = conexion.execute(consulta, (plan_id,)).fetchone()
        return self._fila_a_plan(fila) if fila is not None else None

    def obtener_detalle(self, plan_id: int) -> DetallePlanPago | None:
        plan = self.obtener_por_id(plan_id)
        if plan is None:
            return None
        consulta_cuotas = """
            SELECT id, numero_cuota, fecha_vencimiento, monto_centavos, saldo_pendiente_centavos, estado
            FROM cuotas_plan_pago
            WHERE plan_pago_id = ?
            ORDER BY numero_cuota ASC;
        """
        consulta_cargos = """
            SELECT
                COALESCE(cg.descripcion, cc.nombre, 'Cargo vinculado') AS descripcion
            FROM planes_pago_cargos ppc
            INNER JOIN cargos cg ON cg.id = ppc.cargo_id
            LEFT JOIN conceptos_cobro cc ON cc.id = cg.concepto_id
            WHERE ppc.plan_pago_id = ?
            ORDER BY cg.fecha_vencimiento, cg.id;
        """
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            filas_cuotas = conexion.execute(consulta_cuotas, (plan_id,)).fetchall()
            filas_cargos = conexion.execute(consulta_cargos, (plan_id,)).fetchall()
        cuotas = tuple(
            CuotaPlanPago(
                identificador=int(fila["id"]),
                numero_cuota=int(fila["numero_cuota"]),
                fecha_vencimiento=str(fila["fecha_vencimiento"] or ""),
                monto_centavos=int(fila["monto_centavos"] or 0),
                saldo_pendiente_centavos=int(fila["saldo_pendiente_centavos"] or 0),
                estado=str(fila["estado"] or "PENDIENTE"),
            )
            for fila in filas_cuotas
        )
        return DetallePlanPago(
            plan=plan,
            cuotas=cuotas,
            cargos_vinculados=tuple(str(fila["descripcion"] or "") for fila in filas_cargos),
        )

    def listar_casas_disponibles(self) -> list[OpcionCasaPlanPago]:
        consulta = f"""
            SELECT
                c.id AS casa_id,
                printf('CA-%03d', c.id) AS casa_codigo,
                a.id AS abonado_id,
                a.nombre_completo AS abonado_nombre,
                a.dni AS abonado_dni,
                COALESCE(b.nombre, '') AS barrio_nombre,
                c.estado_servicio,
                COALESCE(dd.meses_pendientes, 0) AS meses_pendientes,
                COALESCE(dd.meses_en_mora, 0) AS meses_en_mora,
                COALESCE(dd.deuda_total_centavos, 0) AS deuda_total_centavos
            FROM casas c
            INNER JOIN abonados a ON a.id = c.abonado_id
            LEFT JOIN barrios b ON b.id = c.barrio_id
            LEFT JOIN ({SUBCONSULTA_DEUDA_CASA}) dd ON dd.casa_id = c.id
            WHERE c.eliminado_en IS NULL
            ORDER BY c.id ASC;
        """
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            filas = conexion.execute(consulta).fetchall()
        return [
            OpcionCasaPlanPago(
                casa_id=int(fila["casa_id"]),
                casa_codigo=str(fila["casa_codigo"]),
                abonado_id=int(fila["abonado_id"]),
                abonado_nombre=str(fila["abonado_nombre"] or ""),
                abonado_dni=str(fila["abonado_dni"] or ""),
                barrio_nombre=str(fila["barrio_nombre"] or ""),
                estado_servicio=str(fila["estado_servicio"] or "ACTIVO"),
                meses_pendientes=int(fila["meses_pendientes"] or 0),
                meses_en_mora=int(fila["meses_en_mora"] or 0),
                deuda_total_centavos=int(fila["deuda_total_centavos"] or 0),
            )
            for fila in filas
        ]

    def guardar_plan(
        self,
        plan: PlanPago,
        cuotas: list[tuple[str, int]],
        cargos_vinculados: tuple[int, ...],
        actor_id: int | None = None,
    ) -> int:
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            with conexion:
                if plan.identificador is None:
                    cursor = conexion.execute(
                        """
                        INSERT INTO planes_pago(
                            abonado_id,
                            casa_id,
                            fecha_inicio,
                            fecha_fin,
                            monto_total_centavos,
                            cuota_regular_centavos,
                            cantidad_cuotas,
                            cuotas_pagadas,
                            estado,
                            observaciones,
                            creado_por,
                            tipo_plan,
                            concepto_financiado,
                            prima_centavos
                        )
                        VALUES (?, ?, date('now', 'localtime'), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                        """,
                        (
                            plan.abonado_id,
                            plan.casa_id,
                            cuotas[-1][0] if cuotas else None,
                            plan.monto_total_centavos,
                            plan.cuota_regular_centavos,
                            plan.cantidad_cuotas,
                            plan.cuotas_pagadas,
                            plan.estado,
                            plan.observaciones,
                            actor_id,
                            plan.tipo_plan,
                            plan.concepto_financiado,
                            plan.prima_centavos,
                        ),
                    )
                    plan_id = int(cursor.lastrowid)
                else:
                    conexion.execute(
                        """
                        UPDATE planes_pago
                        SET abonado_id = ?,
                            casa_id = ?,
                            fecha_fin = ?,
                            monto_total_centavos = ?,
                            cuota_regular_centavos = ?,
                            cantidad_cuotas = ?,
                            estado = ?,
                            observaciones = ?,
                            tipo_plan = ?,
                            concepto_financiado = ?,
                            prima_centavos = ?,
                            actualizado_en = datetime('now', 'localtime')
                        WHERE id = ?;
                        """,
                        (
                            plan.abonado_id,
                            plan.casa_id,
                            cuotas[-1][0] if cuotas else None,
                            plan.monto_total_centavos,
                            plan.cuota_regular_centavos,
                            plan.cantidad_cuotas,
                            plan.estado,
                            plan.observaciones,
                            plan.tipo_plan,
                            plan.concepto_financiado,
                            plan.prima_centavos,
                            plan.identificador,
                        ),
                    )
                    plan_id = int(plan.identificador)
                    conexion.execute("DELETE FROM cuotas_plan_pago WHERE plan_pago_id = ?;", (plan_id,))
                    conexion.execute("DELETE FROM planes_pago_cargos WHERE plan_pago_id = ?;", (plan_id,))

                for indice, (fecha_vencimiento, monto) in enumerate(cuotas, start=1):
                    conexion.execute(
                        """
                        INSERT INTO cuotas_plan_pago(
                            plan_pago_id,
                            numero_cuota,
                            fecha_vencimiento,
                            monto_centavos,
                            saldo_pendiente_centavos,
                            estado
                        )
                        VALUES (?, ?, ?, ?, ?, 'PENDIENTE');
                        """,
                        (plan_id, indice, fecha_vencimiento, monto, monto),
                    )
                for cargo_id in cargos_vinculados:
                    conexion.execute(
                        """
                        INSERT INTO planes_pago_cargos(plan_pago_id, cargo_id)
                        VALUES (?, ?);
                        """,
                        (plan_id, cargo_id),
                    )
                return plan_id

    def contar_cuotas_pagadas(self, plan_id: int) -> int:
        consulta = """
            SELECT COUNT(*)
            FROM cuotas_plan_pago
            WHERE plan_pago_id = ?
              AND estado = 'PAGADO';
        """
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            return int(conexion.execute(consulta, (plan_id,)).fetchone()[0] or 0)

    def obtener_cargos_vinculables(
        self,
        casa_id: int,
        concepto_financiado: str,
    ) -> tuple[int, ...]:
        condiciones = [
            "casa_id = ?",
            "anulado_en IS NULL",
            "saldo_pendiente_centavos > 0",
        ]
        parametros: list[object] = [casa_id]
        if concepto_financiado == "RECONEXION":
            condiciones.append(
                "concepto_id IN (SELECT id FROM conceptos_cobro WHERE codigo = 'RECONEXION')"
            )
        elif concepto_financiado == "CONEXION":
            condiciones.append(
                "concepto_id IN (SELECT id FROM conceptos_cobro WHERE codigo IN ('CONEXION', 'PRIMA'))"
            )
        else:
            return ()
        consulta = f"""
            SELECT id
            FROM cargos
            WHERE {' AND '.join(condiciones)}
            ORDER BY fecha_vencimiento, id;
        """
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            filas = conexion.execute(consulta, tuple(parametros)).fetchall()
        return tuple(int(fila["id"]) for fila in filas)

    def _construir_filtros(
        self,
        filtro: str,
        filtro_rapido: str,
    ) -> tuple[list[str], list[object]]:
        condiciones = ["1 = 1"]
        parametros: list[object] = []
        filtro = filtro.strip()
        if filtro:
            patron = f"%{filtro}%"
            condiciones.append(
                """
                (
                    CAST(pp.id AS TEXT) LIKE ?
                    OR lower(printf('PP-%03d', pp.id)) LIKE lower(?)
                    OR lower(printf('CA-%03d', pp.casa_id)) LIKE lower(?)
                    OR a.dni LIKE ?
                    OR lower(a.nombre_completo) LIKE lower(?)
                )
                """
            )
            parametros.extend([patron, patron, patron, patron, patron])

        if filtro_rapido == FILTRO_PLANES_ACTIVOS:
            condiciones.append("pp.estado = 'ACTIVO'")
        elif filtro_rapido == FILTRO_PLANES_CON_MORA:
            condiciones.append("COALESCE(qc.cuotas_en_mora, 0) > 0")
        elif filtro_rapido == FILTRO_PLANES_SERVICIO:
            condiciones.append("COALESCE(pp.tipo_plan, '') IN ('CONEXION', 'RECONEXION')")
        return condiciones, parametros

    @staticmethod
    def _fila_a_plan(fila: object) -> PlanPago:
        return PlanPago(
            identificador=int(fila["id"]),
            casa_id=int(fila["casa_id"]),
            casa_codigo=str(fila["casa_codigo"]),
            abonado_id=int(fila["abonado_id"]),
            abonado_nombre=str(fila["abonado_nombre"] or ""),
            abonado_dni=str(fila["abonado_dni"] or ""),
            barrio_nombre=str(fila["barrio_nombre"] or ""),
            tipo_plan=str(fila["tipo_plan"] or "MESES_PENDIENTES"),
            concepto_financiado=str(fila["concepto_financiado"] or "MESES_PENDIENTES"),
            prima_centavos=int(fila["prima_centavos"] or 0),
            saldo_financiado_centavos=int(fila["saldo_financiado_centavos"] or 0),
            monto_total_centavos=int(fila["monto_total_centavos"] or 0),
            cuota_regular_centavos=int(fila["cuota_regular_centavos"] or 0),
            cantidad_cuotas=int(fila["cantidad_cuotas"] or 0),
            cuotas_pagadas=int(fila["cuotas_pagadas"] or 0),
            cuotas_pendientes=int(fila["cuotas_pendientes"] or 0),
            saldo_pendiente_centavos=int(fila["saldo_pendiente_centavos"] or 0),
            cuotas_en_mora=int(fila["cuotas_en_mora"] or 0),
            proxima_fecha=str(fila["proxima_fecha"] or ""),
            estado=str(fila["estado"] or "ACTIVO"),
            observaciones=str(fila["observaciones"] or ""),
            creado_en=str(fila["creado_en"] or ""),
            actualizado_en=str(fila["actualizado_en"] or ""),
            creado_por_nombre=str(fila["creado_por_nombre"] or ""),
        )

