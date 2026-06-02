"""Contratos e implementacion SQLite del modulo de casas."""

from __future__ import annotations

import json
from contextlib import closing
from typing import Protocol

from comun.base_datos import GestorBaseDatos
from modulos.casas.entidades import (
    Casa,
    DetalleCasa,
    ESTADO_ADMINISTRATIVO_OPERATIVA,
    ESTADO_ADMINISTRATIVO_SUSPENDIDA,
    ESTADO_AVISO_CORTADO,
    ESTADO_SERVICIO_ACTIVO,
    ESTADO_SERVICIO_CORTADO,
    FILTRO_CASAS_ACTIVAS,
    FILTRO_CASAS_CORTADAS,
    FILTRO_CASAS_CON_MORA,
    FILTRO_CASAS_DEUDA_MAYOR_5,
    FILTRO_CASAS_SIN_PROPIETARIO,
    FILTRO_CASAS_SUSPENDIDAS,
    FILTRO_CASAS_TODAS,
    HistorialPropietarioCasa,
    MOTIVO_ESTADO_ADMINISTRATIVO_ABONADO_INACTIVO,
    MOTIVO_ESTADO_ADMINISTRATIVO_NINGUNO,
    MOTIVO_ESTADO_ADMINISTRATIVO_REASIGNACION_PENDIENTE,
    MOTIVO_ESTADO_ADMINISTRATIVO_REVISION_ADMINISTRATIVA,
    OpcionAbonado,
    OpcionBarrio,
    PlanActivoCasa,
    ResumenCasas,
)


SUBCONSULTA_DEUDA = """
    SELECT
        casa_id,
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
        ) AS deuda_total_centavos,
        COUNT(
            DISTINCT CASE
                WHEN estado IN ('PENDIENTE', 'PARCIAL', 'VENCIDO')
                 AND saldo_pendiente_centavos > 0
                THEN COALESCE(periodo_id, id)
                ELSE NULL
            END
        ) AS meses_pendientes,
        COUNT(
            DISTINCT CASE
                WHEN estado = 'VENCIDO' AND saldo_pendiente_centavos > 0
                THEN COALESCE(periodo_id, id)
                ELSE NULL
            END
        ) AS meses_en_mora
    FROM cargos
    WHERE anulado_en IS NULL
    GROUP BY casa_id
"""

SUBCONSULTA_PLANES = """
    SELECT casa_id, COUNT(*) AS total_planes_activos
    FROM planes_pago
    WHERE estado = 'ACTIVO'
    GROUP BY casa_id
"""

SUBCONSULTA_TRAZABILIDAD_ACTIVACION = """
    SELECT
        c.id AS casa_id,
        CASE
            WHEN EXISTS (
                SELECT 1
                FROM procesos_servicio ps
                WHERE ps.casa_id = c.id
                  AND ps.tipo IN ('CONEXION', 'RECONEXION')
            ) THEN 0
            WHEN EXISTS (
                SELECT 1
                FROM pagos p
                WHERE p.casa_id = c.id
                  AND COALESCE(p.tipo_pago, 'MENSUALIDAD') IN ('CONEXION', 'RECONEXION')
            ) THEN 0
            ELSE 1
        END AS antecedente_servicio_editable
    FROM casas c
"""


class RepositorioCasas(Protocol):
    """Define la persistencia requerida por casas."""

    def listar(
        self,
        filtro: str = "",
        filtro_rapido: str = FILTRO_CASAS_TODAS,
        limite: int | None = None,
        desplazamiento: int = 0,
    ) -> list[Casa]:
        """Lista casas visibles con su contexto operativo."""

    def contar(self, filtro: str = "", filtro_rapido: str = FILTRO_CASAS_TODAS) -> int:
        """Cuenta casas visibles segun filtros."""

    def obtener_resumen(self) -> ResumenCasas:
        """Obtiene metricas de cabecera del modulo."""

    def obtener_por_id(self, casa_id: int) -> Casa | None:
        """Obtiene una casa por ID."""

    def obtener_detalle(self, casa_id: int) -> DetalleCasa | None:
        """Obtiene el detalle operativo ampliado de una casa."""

    def guardar(self, casa: Casa) -> None:
        """Crea o actualiza una casa."""

    def cambiar_estado(
        self,
        casa_id: int,
        estado_administrativo: str,
        motivo_estado_administrativo: str,
    ) -> None:
        """Cambia el estado administrativo de una casa."""

    def cortar_servicio(
        self,
        casa_id: int,
        observaciones: str,
        actor_id: int | None,
    ) -> None:
        """Registra un corte fisico de servicio y actualiza la casa."""

    def cambiar_dueno(
        self,
        casa_id: int,
        nuevo_abonado_id: int,
        motivo: str,
        actor_id: int | None = None,
        observacion: str = "",
    ) -> None:
        """Cambia el propietario actual de la casa y migra contexto pendiente."""

    def listar_historial_propietarios(self, casa_id: int) -> list[HistorialPropietarioCasa]:
        """Lista el historial de propietarios asociado a una casa."""

    def listar_abonados_disponibles(self) -> list[OpcionAbonado]:
        """Obtiene abonados disponibles para asignacion."""

    def listar_barrios_disponibles(self) -> list[OpcionBarrio]:
        """Obtiene barrios utilizables en formularios."""

    def suspender_casas_por_abonado_inactivo(
        self,
        abonado_id: int,
        actor_id: int | None = None,
    ) -> int:
        """Suspende casas operativas de un abonado inactivado."""

    def reactivar_casas_por_abonado_activado(
        self,
        abonado_id: int,
        actor_id: int | None = None,
    ) -> int:
        """Reactiva administrativamente casas suspendidas por abonado inactivo."""


class RepositorioCasasSQLite:
    """Repositorio SQLite para casas."""

    MOTIVO_CORTE_MANUAL = "CORTE_MANUAL"

    def __init__(self, gestor_base_datos: GestorBaseDatos) -> None:
        self._gestor_base_datos = gestor_base_datos

    def listar(
        self,
        filtro: str = "",
        filtro_rapido: str = FILTRO_CASAS_TODAS,
        limite: int | None = None,
        desplazamiento: int = 0,
    ) -> list[Casa]:
        condiciones, parametros = self._construir_filtros(filtro, filtro_rapido)
        clausula_paginacion = ""
        if limite is not None:
            clausula_paginacion = "LIMIT ? OFFSET ?"
            parametros.extend([limite, desplazamiento])

        consulta = f"""
            SELECT
                c.id,
                c.abonado_id,
                COALESCE(a.nombre_completo, '') AS abonado_nombre,
                COALESCE(a.dni, '') AS abonado_dni,
                COALESCE(a.estado, 'INACTIVO') AS abonado_estado,
                c.barrio_id,
                b.nombre AS barrio_nombre,
                COALESCE(c.direccion_referencia, '') AS direccion_referencia,
                COALESCE(c.observaciones, '') AS observaciones,
                c.estado_servicio,
                c.estado_administrativo,
                c.motivo_estado_administrativo,
                COALESCE(c.ha_tenido_servicio_activo, 0) AS ha_tenido_servicio_activo,
                COALESCE(ta.antecedente_servicio_editable, 1) AS antecedente_servicio_editable,
                COALESCE(dd.deuda_total_centavos, 0) AS deuda_total_centavos,
                COALESCE(dd.meses_pendientes, 0) AS meses_pendientes,
                COALESCE(dd.meses_en_mora, 0) AS meses_en_mora,
                COALESCE(pp.total_planes_activos, 0) AS total_planes_activos,
                COALESCE(c.estado_aviso_cobro, 'SIN_AVISO') AS estado_aviso_cobro,
                COALESCE(c.fecha_ultimo_aviso, '') AS fecha_ultimo_aviso,
                COALESCE(u_aviso.nombre_completo, COALESCE(u_aviso.nombre_usuario, '')) AS usuario_ultimo_aviso_nombre,
                COALESCE(c.observacion_ultimo_aviso, '') AS observacion_ultimo_aviso,
                COALESCE(c.creado_en, '') AS creado_en,
                COALESCE(c.fecha_alta, '') AS fecha_alta,
                COALESCE(c.actualizado_en, '') AS actualizado_en
            FROM casas c
            INNER JOIN barrios b ON b.id = c.barrio_id
            LEFT JOIN abonados a ON a.id = c.abonado_id
            LEFT JOIN ({SUBCONSULTA_DEUDA}) dd ON dd.casa_id = c.id
            LEFT JOIN ({SUBCONSULTA_PLANES}) pp ON pp.casa_id = c.id
            LEFT JOIN ({SUBCONSULTA_TRAZABILIDAD_ACTIVACION}) ta ON ta.casa_id = c.id
            LEFT JOIN usuarios u_aviso ON u_aviso.id = c.usuario_ultimo_aviso_id
            WHERE {' AND '.join(condiciones)}
            ORDER BY c.id ASC
            {clausula_paginacion};
        """
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            filas = conexion.execute(consulta, tuple(parametros)).fetchall()
        return [self._fila_a_casa(fila) for fila in filas]

    def contar(self, filtro: str = "", filtro_rapido: str = FILTRO_CASAS_TODAS) -> int:
        condiciones, parametros = self._construir_filtros(filtro, filtro_rapido)
        consulta = f"""
            SELECT COUNT(*)
            FROM casas c
            INNER JOIN barrios b ON b.id = c.barrio_id
            LEFT JOIN abonados a ON a.id = c.abonado_id
            LEFT JOIN ({SUBCONSULTA_DEUDA}) dd ON dd.casa_id = c.id
            WHERE {' AND '.join(condiciones)};
        """
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            return int(conexion.execute(consulta, tuple(parametros)).fetchone()[0] or 0)

    def obtener_resumen(self) -> ResumenCasas:
        consulta = f"""
            SELECT
                COUNT(*) AS total_casas,
                SUM(
                    CASE
                        WHEN c.estado_servicio = 'ACTIVO'
                         AND c.estado_administrativo = 'OPERATIVA'
                        THEN 1
                        ELSE 0
                    END
                ) AS casas_activas,
                SUM(CASE WHEN COALESCE(dd.deuda_total_centavos, 0) > 0 THEN 1 ELSE 0 END) AS casas_con_deuda,
                SUM(CASE WHEN COALESCE(dd.meses_en_mora, 0) > 0 THEN 1 ELSE 0 END) AS casas_morosas
            FROM casas c
            LEFT JOIN ({SUBCONSULTA_DEUDA}) dd ON dd.casa_id = c.id
            WHERE c.eliminado_en IS NULL;
        """
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            fila = conexion.execute(consulta).fetchone()
        return ResumenCasas(
            total_casas=int(fila["total_casas"] or 0),
            casas_activas=int(fila["casas_activas"] or 0),
            casas_con_deuda=int(fila["casas_con_deuda"] or 0),
            casas_morosas=int(fila["casas_morosas"] or 0),
        )

    def obtener_por_id(self, casa_id: int) -> Casa | None:
        consulta = f"""
            SELECT
                c.id,
                c.abonado_id,
                COALESCE(a.nombre_completo, '') AS abonado_nombre,
                COALESCE(a.dni, '') AS abonado_dni,
                COALESCE(a.estado, 'INACTIVO') AS abonado_estado,
                c.barrio_id,
                b.nombre AS barrio_nombre,
                COALESCE(c.direccion_referencia, '') AS direccion_referencia,
                COALESCE(c.observaciones, '') AS observaciones,
                c.estado_servicio,
                c.estado_administrativo,
                c.motivo_estado_administrativo,
                COALESCE(c.ha_tenido_servicio_activo, 0) AS ha_tenido_servicio_activo,
                COALESCE(ta.antecedente_servicio_editable, 1) AS antecedente_servicio_editable,
                COALESCE(dd.deuda_total_centavos, 0) AS deuda_total_centavos,
                COALESCE(dd.meses_pendientes, 0) AS meses_pendientes,
                COALESCE(dd.meses_en_mora, 0) AS meses_en_mora,
                COALESCE(pp.total_planes_activos, 0) AS total_planes_activos,
                COALESCE(c.estado_aviso_cobro, 'SIN_AVISO') AS estado_aviso_cobro,
                COALESCE(c.fecha_ultimo_aviso, '') AS fecha_ultimo_aviso,
                COALESCE(u_aviso.nombre_completo, COALESCE(u_aviso.nombre_usuario, '')) AS usuario_ultimo_aviso_nombre,
                COALESCE(c.observacion_ultimo_aviso, '') AS observacion_ultimo_aviso,
                COALESCE(c.creado_en, '') AS creado_en,
                COALESCE(c.fecha_alta, '') AS fecha_alta,
                COALESCE(c.actualizado_en, '') AS actualizado_en
            FROM casas c
            INNER JOIN barrios b ON b.id = c.barrio_id
            LEFT JOIN abonados a ON a.id = c.abonado_id
            LEFT JOIN ({SUBCONSULTA_DEUDA}) dd ON dd.casa_id = c.id
            LEFT JOIN ({SUBCONSULTA_PLANES}) pp ON pp.casa_id = c.id
            LEFT JOIN ({SUBCONSULTA_TRAZABILIDAD_ACTIVACION}) ta ON ta.casa_id = c.id
            LEFT JOIN usuarios u_aviso ON u_aviso.id = c.usuario_ultimo_aviso_id
            WHERE c.id = ? AND c.eliminado_en IS NULL
            LIMIT 1;
        """
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            fila = conexion.execute(consulta, (casa_id,)).fetchone()
        return self._fila_a_casa(fila) if fila is not None else None

    def obtener_detalle(self, casa_id: int) -> DetalleCasa | None:
        casa = self.obtener_por_id(casa_id)
        if casa is None:
            return None

        consulta_plan = """
            SELECT
                pp.id,
                pp.estado,
                pp.monto_total_centavos,
                pp.cuota_regular_centavos,
                pp.cuotas_pagadas,
                COALESCE(pendientes.cuotas_pendientes, 0) AS cuotas_pendientes,
                COALESCE(pendientes.saldo_pendiente_centavos, 0) AS saldo_pendiente_centavos,
                COALESCE(pendientes.proxima_fecha, '') AS proxima_fecha
            FROM planes_pago pp
            LEFT JOIN (
                SELECT
                    plan_pago_id,
                    COUNT(*) AS cuotas_pendientes,
                    COALESCE(SUM(saldo_pendiente_centavos), 0) AS saldo_pendiente_centavos,
                    MIN(fecha_vencimiento) AS proxima_fecha
                FROM cuotas_plan_pago
                WHERE estado IN ('PENDIENTE', 'PARCIAL', 'VENCIDO')
                  AND saldo_pendiente_centavos > 0
                GROUP BY plan_pago_id
            ) pendientes ON pendientes.plan_pago_id = pp.id
            WHERE pp.casa_id = ? AND pp.estado = 'ACTIVO'
            ORDER BY pp.id DESC
            LIMIT 1;
        """
        consulta_ultima_fecha = """
            SELECT COALESCE(MAX(fecha_cambio), '') AS ultima_fecha_cambio
            FROM historial_propietarios_casa
            WHERE casa_id = ?;
        """
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            fila_plan = conexion.execute(consulta_plan, (casa_id,)).fetchone()
            fila_ultima_fecha = conexion.execute(consulta_ultima_fecha, (casa_id,)).fetchone()

        plan_activo = None
        if fila_plan is not None:
            plan_activo = PlanActivoCasa(
                identificador=int(fila_plan["id"]),
                estado=str(fila_plan["estado"]),
                monto_total_centavos=int(fila_plan["monto_total_centavos"] or 0),
                cuota_regular_centavos=int(fila_plan["cuota_regular_centavos"] or 0),
                cuotas_pagadas=int(fila_plan["cuotas_pagadas"] or 0),
                cuotas_pendientes=int(fila_plan["cuotas_pendientes"] or 0),
                saldo_pendiente_centavos=int(fila_plan["saldo_pendiente_centavos"] or 0),
                proxima_fecha=str(fila_plan["proxima_fecha"] or ""),
            )

        historial = tuple(self.listar_historial_propietarios(casa_id))
        return DetalleCasa(
            casa=casa,
            plan_activo=plan_activo,
            historial_propietarios=historial,
            ultima_fecha_cambio_dueno=str(fila_ultima_fecha["ultima_fecha_cambio"] or ""),
        )

    def guardar(self, casa: Casa) -> None:
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            with conexion:
                if casa.identificador is None:
                    conexion.execute(
                        """
                        INSERT INTO casas(
                            abonado_id,
                            barrio_id,
                            direccion_referencia,
                            estado_servicio,
                            estado_administrativo,
                            motivo_estado_administrativo,
                            ha_tenido_servicio_activo,
                            observaciones,
                            actualizado_en
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now', 'localtime'));
                        """,
                        (
                            casa.abonado_id,
                            casa.barrio_id,
                            casa.direccion_referencia,
                            casa.estado_servicio,
                            casa.estado_administrativo,
                            casa.motivo_estado_administrativo,
                            1 if casa.ha_tenido_servicio_activo else 0,
                            casa.observaciones,
                        ),
                    )
                    return

                conexion.execute(
                    """
                    UPDATE casas
                    SET abonado_id = ?,
                        barrio_id = ?,
                        direccion_referencia = ?,
                        estado_servicio = ?,
                        estado_administrativo = ?,
                        motivo_estado_administrativo = ?,
                        ha_tenido_servicio_activo = ?,
                        observaciones = ?,
                        actualizado_en = datetime('now', 'localtime')
                    WHERE id = ? AND eliminado_en IS NULL;
                    """,
                    (
                        casa.abonado_id,
                        casa.barrio_id,
                        casa.direccion_referencia,
                        casa.estado_servicio,
                        casa.estado_administrativo,
                        casa.motivo_estado_administrativo,
                        1 if casa.ha_tenido_servicio_activo else 0,
                        casa.observaciones,
                        casa.identificador,
                    ),
                )

    def cambiar_estado(
        self,
        casa_id: int,
        estado_administrativo: str,
        motivo_estado_administrativo: str,
    ) -> None:
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            with conexion:
                conexion.execute(
                    """
                    UPDATE casas
                    SET estado_administrativo = ?,
                        motivo_estado_administrativo = ?,
                        actualizado_en = datetime('now', 'localtime')
                    WHERE id = ? AND eliminado_en IS NULL;
                    """,
                    (estado_administrativo, motivo_estado_administrativo, casa_id),
                )

    def cortar_servicio(
        self,
        casa_id: int,
        observaciones: str,
        actor_id: int | None,
    ) -> None:
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            with conexion:
                fila_actual = conexion.execute(
                    """
                    SELECT
                        c.id,
                        c.abonado_id,
                        COALESCE(c.estado_servicio, 'ACTIVO') AS estado_servicio,
                        COALESCE(c.estado_administrativo, 'OPERATIVA') AS estado_administrativo,
                        COALESCE(c.motivo_estado_administrativo, 'NINGUNO') AS motivo_estado_administrativo
                    FROM casas c
                    WHERE c.id = ? AND c.eliminado_en IS NULL
                    LIMIT 1;
                    """,
                    (casa_id,),
                ).fetchone()
                if fila_actual is None:
                    raise ValueError("La casa indicada no existe.")
                if str(fila_actual["estado_servicio"] or ESTADO_SERVICIO_ACTIVO) != ESTADO_SERVICIO_ACTIVO:
                    raise ValueError("Solo puedes cortar servicio a casas activas.")

                conexion.execute(
                    """
                    INSERT INTO procesos_servicio(
                        abonado_id,
                        casa_id,
                        tipo,
                        fecha_ejecucion,
                        estado,
                        motivo,
                        observaciones,
                        usuario_id
                    )
                    VALUES (?, ?, 'CORTE', datetime('now', 'localtime'), 'EJECUTADO', ?, ?, ?);
                    """,
                    (
                        int(fila_actual["abonado_id"]) if fila_actual["abonado_id"] is not None else None,
                        casa_id,
                        self.MOTIVO_CORTE_MANUAL,
                        observaciones,
                        actor_id,
                    ),
                )
                conexion.execute(
                    """
                    UPDATE casas
                    SET estado_servicio = ?,
                        estado_aviso_cobro = ?,
                        fecha_ultimo_aviso = datetime('now', 'localtime'),
                        usuario_ultimo_aviso_id = ?,
                        observacion_ultimo_aviso = ?,
                        actualizado_en = datetime('now', 'localtime')
                    WHERE id = ? AND eliminado_en IS NULL;
                    """,
                    (ESTADO_SERVICIO_CORTADO, ESTADO_AVISO_CORTADO, actor_id, observaciones, casa_id),
                )
                conexion.execute(
                    """
                    INSERT INTO auditoria(
                        usuario_id,
                        accion,
                        entidad,
                        entidad_id,
                        resumen,
                        datos_antes_json,
                        datos_despues_json
                    )
                    VALUES (?, 'CORTE_SERVICIO_CASA', 'casas', ?, ?, ?, ?);
                    """,
                    (
                        actor_id,
                        casa_id,
                        f"Corte fisico manual de servicio para casa {casa_id}",
                        json.dumps(
                            {
                                "estado_servicio": str(
                                    fila_actual["estado_servicio"] or ESTADO_SERVICIO_ACTIVO
                                ),
                                "estado_administrativo": str(
                                    fila_actual["estado_administrativo"]
                                    or ESTADO_ADMINISTRATIVO_OPERATIVA
                                ),
                                "motivo_estado_administrativo": str(
                                    fila_actual["motivo_estado_administrativo"]
                                    or MOTIVO_ESTADO_ADMINISTRATIVO_NINGUNO
                                ),
                            },
                            ensure_ascii=True,
                        ),
                        json.dumps(
                            {
                                "estado_servicio": ESTADO_SERVICIO_CORTADO,
                                "estado_administrativo": str(
                                    fila_actual["estado_administrativo"]
                                    or ESTADO_ADMINISTRATIVO_OPERATIVA
                                ),
                                "motivo_estado_administrativo": str(
                                    fila_actual["motivo_estado_administrativo"]
                                    or MOTIVO_ESTADO_ADMINISTRATIVO_NINGUNO
                                ),
                                "motivo": self.MOTIVO_CORTE_MANUAL,
                                "observaciones": observaciones,
                            },
                            ensure_ascii=True,
                        ),
                    ),
                )

    def cambiar_dueno(
        self,
        casa_id: int,
        nuevo_abonado_id: int,
        motivo: str,
        actor_id: int | None = None,
        observacion: str = "",
    ) -> None:
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            with conexion:
                fila_actual = conexion.execute(
                    """
                    SELECT
                        c.id,
                        c.abonado_id,
                        COALESCE(a.nombre_completo, '') AS abonado_actual,
                        COALESCE(a.dni, '') AS dni_actual,
                        COALESCE(c.estado_servicio, '') AS estado_servicio,
                        COALESCE(c.estado_administrativo, 'OPERATIVA') AS estado_administrativo,
                        COALESCE(c.motivo_estado_administrativo, 'NINGUNO') AS motivo_estado_administrativo
                    FROM casas c
                    LEFT JOIN abonados a ON a.id = c.abonado_id
                    WHERE c.id = ? AND c.eliminado_en IS NULL
                    LIMIT 1;
                    """,
                    (casa_id,),
                ).fetchone()
                if fila_actual is None:
                    raise ValueError("La casa indicada no existe.")

                fila_nuevo_abonado = conexion.execute(
                    """
                    SELECT id, nombre_completo, dni, estado
                    FROM abonados
                    WHERE id = ? AND eliminado_en IS NULL
                    LIMIT 1;
                    """,
                    (nuevo_abonado_id,),
                ).fetchone()
                if fila_nuevo_abonado is None:
                    raise ValueError("El abonado seleccionado no existe.")

                abonado_anterior_id = (
                    int(fila_actual["abonado_id"]) if fila_actual["abonado_id"] is not None else None
                )
                if abonado_anterior_id == nuevo_abonado_id:
                    raise ValueError("La casa ya esta asociada al abonado seleccionado.")

                conexion.execute(
                    """
                    UPDATE casas
                    SET abonado_id = ?,
                        estado_administrativo = CASE
                            WHEN ? = 'ACTIVO'
                             AND motivo_estado_administrativo IN ('ABONADO_INACTIVO', 'REASIGNACION_PENDIENTE')
                            THEN 'OPERATIVA'
                            ELSE estado_administrativo
                        END,
                        motivo_estado_administrativo = CASE
                            WHEN ? = 'ACTIVO'
                             AND motivo_estado_administrativo IN ('ABONADO_INACTIVO', 'REASIGNACION_PENDIENTE')
                            THEN 'NINGUNO'
                            ELSE motivo_estado_administrativo
                        END,
                        actualizado_en = datetime('now', 'localtime')
                    WHERE id = ? AND eliminado_en IS NULL;
                    """,
                    (nuevo_abonado_id, str(fila_nuevo_abonado["estado"] or ""), str(fila_nuevo_abonado["estado"] or ""), casa_id),
                )
                conexion.execute(
                    """
                    UPDATE cargos
                    SET abonado_id = ?,
                        actualizado_en = datetime('now', 'localtime')
                    WHERE casa_id = ?
                      AND anulado_en IS NULL
                      AND estado IN ('PENDIENTE', 'PARCIAL', 'VENCIDO')
                      AND saldo_pendiente_centavos > 0;
                    """,
                    (nuevo_abonado_id, casa_id),
                )
                conexion.execute(
                    """
                    UPDATE planes_pago
                    SET abonado_id = ?,
                        actualizado_en = datetime('now', 'localtime')
                    WHERE casa_id = ?
                      AND estado = 'ACTIVO';
                    """,
                    (nuevo_abonado_id, casa_id),
                )
                conexion.execute(
                    """
                    INSERT INTO historial_propietarios_casa(
                        casa_id,
                        abonado_anterior_id,
                        abonado_nuevo_id,
                        fecha_cambio,
                        motivo,
                        observacion,
                        usuario_id
                    )
                    VALUES (?, ?, ?, datetime('now', 'localtime'), ?, ?, ?);
                    """,
                    (casa_id, abonado_anterior_id, nuevo_abonado_id, motivo, observacion, actor_id),
                )
                conexion.execute(
                    """
                    INSERT INTO auditoria(
                        usuario_id,
                        accion,
                        entidad,
                        entidad_id,
                        resumen,
                        datos_antes_json,
                        datos_despues_json
                    )
                    VALUES (?, ?, 'casas', ?, ?, ?, ?);
                    """,
                    (
                        actor_id,
                        "CAMBIO_DUENO_CASA",
                        casa_id,
                        f"Cambio de propietario para casa {casa_id}",
                        json.dumps(
                            {
                                "abonado_id": abonado_anterior_id,
                                "abonado_nombre": str(fila_actual["abonado_actual"] or ""),
                                "abonado_dni": str(fila_actual["dni_actual"] or ""),
                                "estado_servicio": str(fila_actual["estado_servicio"] or ""),
                                "estado_administrativo": str(fila_actual["estado_administrativo"] or ""),
                                "motivo_estado_administrativo": str(fila_actual["motivo_estado_administrativo"] or ""),
                            },
                            ensure_ascii=True,
                        ),
                        json.dumps(
                            {
                                "abonado_id": int(fila_nuevo_abonado["id"]),
                                "abonado_nombre": str(fila_nuevo_abonado["nombre_completo"] or ""),
                                "abonado_dni": str(fila_nuevo_abonado["dni"] or ""),
                                "estado_abonado": str(fila_nuevo_abonado["estado"] or ""),
                                "motivo": motivo,
                                "observacion": observacion,
                            },
                            ensure_ascii=True,
                        ),
                    ),
                )

    def listar_historial_propietarios(self, casa_id: int) -> list[HistorialPropietarioCasa]:
        consulta = """
            SELECT
                h.id,
                COALESCE(h.fecha_cambio, '') AS fecha_cambio,
                COALESCE(anterior.nombre_completo, 'Sin registro previo') AS abonado_anterior_nombre,
                COALESCE(nuevo.nombre_completo, 'Sin asignacion') AS abonado_nuevo_nombre,
                COALESCE(h.motivo, '') AS motivo,
                COALESCE(h.observacion, '') AS observacion,
                COALESCE(u.nombre_completo, COALESCE(u.nombre_usuario, 'Sistema')) AS usuario_nombre
            FROM historial_propietarios_casa h
            LEFT JOIN abonados anterior ON anterior.id = h.abonado_anterior_id
            LEFT JOIN abonados nuevo ON nuevo.id = h.abonado_nuevo_id
            LEFT JOIN usuarios u ON u.id = h.usuario_id
            WHERE h.casa_id = ?
            ORDER BY h.fecha_cambio DESC, h.id DESC;
        """
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            filas = conexion.execute(consulta, (casa_id,)).fetchall()
        return [
            HistorialPropietarioCasa(
                identificador=int(fila["id"]),
                fecha_cambio=str(fila["fecha_cambio"] or ""),
                abonado_anterior_nombre=str(fila["abonado_anterior_nombre"] or ""),
                abonado_nuevo_nombre=str(fila["abonado_nuevo_nombre"] or ""),
                motivo=str(fila["motivo"] or ""),
                usuario_nombre=str(fila["usuario_nombre"] or "Sistema"),
                observacion=str(fila["observacion"] or ""),
            )
            for fila in filas
        ]

    def listar_abonados_disponibles(self) -> list[OpcionAbonado]:
        consulta = """
            SELECT id, nombre_completo, dni, estado
            FROM abonados
            WHERE eliminado_en IS NULL
            ORDER BY
                CASE WHEN estado = 'ACTIVO' THEN 0 ELSE 1 END,
                lower(nombre_completo),
                dni;
        """
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            filas = conexion.execute(consulta).fetchall()
        return [
            OpcionAbonado(
                identificador=int(fila["id"]),
                nombre_completo=str(fila["nombre_completo"] or ""),
                dni=str(fila["dni"] or ""),
                estado=str(fila["estado"] or "ACTIVO"),
            )
            for fila in filas
        ]

    def listar_barrios_disponibles(self) -> list[OpcionBarrio]:
        consulta = """
            SELECT id, nombre
            FROM barrios
            WHERE eliminado_en IS NULL
            ORDER BY lower(nombre);
        """
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            filas = conexion.execute(consulta).fetchall()
        return [OpcionBarrio(int(fila["id"]), str(fila["nombre"])) for fila in filas]

    def suspender_casas_por_abonado_inactivo(
        self,
        abonado_id: int,
        actor_id: int | None = None,
    ) -> int:
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            with conexion:
                filas_afectadas = conexion.execute(
                    """
                    SELECT id, estado_servicio, estado_administrativo, motivo_estado_administrativo
                    FROM casas
                    WHERE abonado_id = ?
                      AND eliminado_en IS NULL
                      AND estado_servicio != 'INACTIVO'
                      AND estado_administrativo != 'SUSPENDIDA';
                    """,
                    (abonado_id,),
                ).fetchall()
                if not filas_afectadas:
                    return 0

                conexion.execute(
                    """
                    UPDATE casas
                    SET estado_administrativo = 'SUSPENDIDA',
                        motivo_estado_administrativo = 'ABONADO_INACTIVO',
                        actualizado_en = datetime('now', 'localtime')
                    WHERE abonado_id = ?
                      AND eliminado_en IS NULL
                      AND estado_servicio != 'INACTIVO'
                      AND estado_administrativo != 'SUSPENDIDA';
                    """,
                    (abonado_id,),
                )
                for fila in filas_afectadas:
                    conexion.execute(
                        """
                        INSERT INTO auditoria(
                            usuario_id,
                            accion,
                            entidad,
                            entidad_id,
                            resumen,
                            datos_antes_json,
                            datos_despues_json
                        )
                        VALUES (?, 'SUSPENDER_CASA_POR_ABONADO_INACTIVO', 'casas', ?, ?, ?, ?);
                        """,
                        (
                            actor_id,
                            int(fila["id"]),
                            f"Suspension automatica de casa {int(fila['id'])} por inactivacion del abonado",
                            json.dumps(
                                {
                                    "estado_servicio": str(fila["estado_servicio"] or ""),
                                    "estado_administrativo": str(fila["estado_administrativo"] or ""),
                                    "motivo_estado_administrativo": str(
                                        fila["motivo_estado_administrativo"] or ""
                                    ),
                                },
                                ensure_ascii=True,
                            ),
                            json.dumps(
                                {
                                    "estado_administrativo": "SUSPENDIDA",
                                    "motivo_estado_administrativo": "ABONADO_INACTIVO",
                                },
                                ensure_ascii=True,
                            ),
                        ),
                    )
                return len(filas_afectadas)

    def reactivar_casas_por_abonado_activado(
        self,
        abonado_id: int,
        actor_id: int | None = None,
    ) -> int:
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            with conexion:
                filas_afectadas = conexion.execute(
                    """
                    SELECT id, estado_servicio, estado_administrativo, motivo_estado_administrativo
                    FROM casas
                    WHERE abonado_id = ?
                      AND eliminado_en IS NULL
                      AND estado_administrativo = 'SUSPENDIDA'
                      AND motivo_estado_administrativo = 'ABONADO_INACTIVO';
                    """,
                    (abonado_id,),
                ).fetchall()
                if not filas_afectadas:
                    return 0

                conexion.execute(
                    """
                    UPDATE casas
                    SET estado_administrativo = 'OPERATIVA',
                        motivo_estado_administrativo = 'NINGUNO',
                        actualizado_en = datetime('now', 'localtime')
                    WHERE abonado_id = ?
                      AND eliminado_en IS NULL
                      AND estado_administrativo = 'SUSPENDIDA'
                      AND motivo_estado_administrativo = 'ABONADO_INACTIVO';
                    """,
                    (abonado_id,),
                )
                for fila in filas_afectadas:
                    conexion.execute(
                        """
                        INSERT INTO auditoria(
                            usuario_id,
                            accion,
                            entidad,
                            entidad_id,
                            resumen,
                            datos_antes_json,
                            datos_despues_json
                        )
                        VALUES (?, 'REACTIVAR_CASA_POR_ABONADO_ACTIVO', 'casas', ?, ?, ?, ?);
                        """,
                        (
                            actor_id,
                            int(fila["id"]),
                            f"Reactivacion administrativa de casa {int(fila['id'])} por restauracion del abonado",
                            json.dumps(
                                {
                                    "estado_servicio": str(fila["estado_servicio"] or ""),
                                    "estado_administrativo": str(fila["estado_administrativo"] or ""),
                                    "motivo_estado_administrativo": str(
                                        fila["motivo_estado_administrativo"] or ""
                                    ),
                                },
                                ensure_ascii=True,
                            ),
                            json.dumps(
                                {
                                    "estado_administrativo": "OPERATIVA",
                                    "motivo_estado_administrativo": "NINGUNO",
                                },
                                ensure_ascii=True,
                            ),
                        ),
                    )
                return len(filas_afectadas)

    def _construir_filtros(
        self,
        filtro: str,
        filtro_rapido: str,
    ) -> tuple[list[str], list[object]]:
        condiciones = ["c.eliminado_en IS NULL"]
        parametros: list[object] = []
        filtro = filtro.strip()
        if filtro:
            patron = f"%{filtro}%"
            condiciones.append(
                """
                (
                    CAST(c.id AS TEXT) LIKE ?
                    OR lower(printf('CA-%03d', c.id)) LIKE lower(?)
                    OR lower(printf('BR-%03d', c.barrio_id)) LIKE lower(?)
                    OR a.dni LIKE ?
                    OR lower(COALESCE(a.nombre_completo, '')) LIKE lower(?)
                    OR lower(COALESCE(b.nombre, '')) LIKE lower(?)
                    OR lower(COALESCE(c.direccion_referencia, '')) LIKE lower(?)
                )
                """
            )
            parametros.extend([patron, patron, patron, patron, patron, patron, patron])

        if filtro_rapido == FILTRO_CASAS_ACTIVAS:
            condiciones.append(
                "c.estado_servicio = 'ACTIVO' AND c.estado_administrativo = 'OPERATIVA'"
            )
        elif filtro_rapido == FILTRO_CASAS_SUSPENDIDAS:
            condiciones.append("c.estado_administrativo = 'SUSPENDIDA'")
        elif filtro_rapido == FILTRO_CASAS_CON_MORA:
            condiciones.append("COALESCE(dd.meses_en_mora, 0) > 0")
        elif filtro_rapido == FILTRO_CASAS_CORTADAS:
            condiciones.append("c.estado_servicio = 'CORTADO'")
        elif filtro_rapido == FILTRO_CASAS_DEUDA_MAYOR_5:
            condiciones.append("COALESCE(dd.meses_en_mora, 0) > 5")
        elif filtro_rapido == FILTRO_CASAS_SIN_PROPIETARIO:
            condiciones.append("COALESCE(a.estado, 'INACTIVO') != 'ACTIVO'")

        return condiciones, parametros

    @staticmethod
    def _fila_a_casa(fila: object) -> Casa:
        return Casa(
            identificador=int(fila["id"]),
            abonado_id=int(fila["abonado_id"]) if fila["abonado_id"] is not None else None,
            abonado_nombre=str(fila["abonado_nombre"] or ""),
            abonado_dni=str(fila["abonado_dni"] or ""),
            abonado_estado=str(fila["abonado_estado"] or "INACTIVO"),
            barrio_id=int(fila["barrio_id"]) if fila["barrio_id"] is not None else None,
            barrio_nombre=str(fila["barrio_nombre"] or ""),
            direccion_referencia=str(fila["direccion_referencia"] or ""),
            observaciones=str(fila["observaciones"] or ""),
            estado_servicio=str(fila["estado_servicio"] or "ACTIVO"),
            estado_administrativo=str(fila["estado_administrativo"] or "OPERATIVA"),
            motivo_estado_administrativo=str(
                fila["motivo_estado_administrativo"] or "NINGUNO"
            ),
            ha_tenido_servicio_activo=bool(int(fila["ha_tenido_servicio_activo"] or 0)),
            antecedente_servicio_editable=bool(int(fila["antecedente_servicio_editable"] or 0)),
            deuda_total_centavos=int(fila["deuda_total_centavos"] or 0),
            meses_pendientes=int(fila["meses_pendientes"] or 0),
            meses_en_mora=int(fila["meses_en_mora"] or 0),
            tiene_plan_activo=int(fila["total_planes_activos"] or 0) > 0,
            estado_aviso_cobro=str(fila["estado_aviso_cobro"] or "SIN_AVISO"),
            fecha_ultimo_aviso=str(fila["fecha_ultimo_aviso"] or ""),
            usuario_ultimo_aviso_nombre=str(fila["usuario_ultimo_aviso_nombre"] or ""),
            observacion_ultimo_aviso=str(fila["observacion_ultimo_aviso"] or ""),
            creado_en=str(fila["creado_en"] or ""),
            fecha_alta=str(fila["fecha_alta"] or ""),
            actualizado_en=str(fila["actualizado_en"] or ""),
        )

