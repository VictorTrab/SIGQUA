"""Contratos e implementacion SQLite del modulo de casas."""

from __future__ import annotations

import json
from contextlib import closing
from typing import Protocol

from comun.base_datos import GestorBaseDatos
from modulos.casas.entidades import (
    Casa,
    DetalleCasa,
    FILTRO_CASAS_ACTIVAS,
    FILTRO_CASAS_CON_MORA,
    FILTRO_CASAS_SIN_PROPIETARIO,
    FILTRO_CASAS_SUSPENDIDAS,
    FILTRO_CASAS_TODAS,
    HistorialPropietarioCasa,
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

    def cambiar_estado(self, casa_id: int, estado: str) -> None:
        """Cambia el estado de servicio de una casa."""

    def cambiar_dueno(
        self,
        casa_id: int,
        nuevo_abonado_id: int,
        motivo: str,
        actor_id: int | None,
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


class RepositorioCasasSQLite:
    """Repositorio SQLite para casas."""

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
                COALESCE(dd.deuda_total_centavos, 0) AS deuda_total_centavos,
                COALESCE(dd.meses_pendientes, 0) AS meses_pendientes,
                COALESCE(dd.meses_en_mora, 0) AS meses_en_mora,
                COALESCE(pp.total_planes_activos, 0) AS total_planes_activos,
                COALESCE(c.fecha_alta, '') AS fecha_alta,
                COALESCE(c.actualizado_en, '') AS actualizado_en
            FROM casas c
            INNER JOIN barrios b ON b.id = c.barrio_id
            LEFT JOIN abonados a ON a.id = c.abonado_id
            LEFT JOIN ({SUBCONSULTA_DEUDA}) dd ON dd.casa_id = c.id
            LEFT JOIN ({SUBCONSULTA_PLANES}) pp ON pp.casa_id = c.id
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
                SUM(CASE WHEN c.estado_servicio = 'ACTIVO' THEN 1 ELSE 0 END) AS casas_activas,
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
                COALESCE(dd.deuda_total_centavos, 0) AS deuda_total_centavos,
                COALESCE(dd.meses_pendientes, 0) AS meses_pendientes,
                COALESCE(dd.meses_en_mora, 0) AS meses_en_mora,
                COALESCE(pp.total_planes_activos, 0) AS total_planes_activos,
                COALESCE(c.fecha_alta, '') AS fecha_alta,
                COALESCE(c.actualizado_en, '') AS actualizado_en
            FROM casas c
            INNER JOIN barrios b ON b.id = c.barrio_id
            LEFT JOIN abonados a ON a.id = c.abonado_id
            LEFT JOIN ({SUBCONSULTA_DEUDA}) dd ON dd.casa_id = c.id
            LEFT JOIN ({SUBCONSULTA_PLANES}) pp ON pp.casa_id = c.id
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
                            observaciones,
                            actualizado_en
                        )
                        VALUES (?, ?, ?, ?, ?, datetime('now'));
                        """,
                        (
                            casa.abonado_id,
                            casa.barrio_id,
                            casa.direccion_referencia,
                            casa.estado_servicio,
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
                        observaciones = ?,
                        actualizado_en = datetime('now')
                    WHERE id = ? AND eliminado_en IS NULL;
                    """,
                    (
                        casa.abonado_id,
                        casa.barrio_id,
                        casa.direccion_referencia,
                        casa.estado_servicio,
                        casa.observaciones,
                        casa.identificador,
                    ),
                )

    def cambiar_estado(self, casa_id: int, estado: str) -> None:
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            with conexion:
                conexion.execute(
                    """
                    UPDATE casas
                    SET estado_servicio = ?,
                        actualizado_en = datetime('now')
                    WHERE id = ? AND eliminado_en IS NULL;
                    """,
                    (estado, casa_id),
                )

    def cambiar_dueno(
        self,
        casa_id: int,
        nuevo_abonado_id: int,
        motivo: str,
        actor_id: int | None,
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
                        COALESCE(c.estado_servicio, '') AS estado_servicio
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
                        actualizado_en = datetime('now')
                    WHERE id = ? AND eliminado_en IS NULL;
                    """,
                    (nuevo_abonado_id, casa_id),
                )
                conexion.execute(
                    """
                    UPDATE cargos
                    SET abonado_id = ?,
                        actualizado_en = datetime('now')
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
                        actualizado_en = datetime('now')
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
                        usuario_id
                    )
                    VALUES (?, ?, ?, datetime('now'), ?, ?);
                    """,
                    (casa_id, abonado_anterior_id, nuevo_abonado_id, motivo, actor_id),
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
                            },
                            ensure_ascii=True,
                        ),
                        json.dumps(
                            {
                                "abonado_id": int(fila_nuevo_abonado["id"]),
                                "abonado_nombre": str(fila_nuevo_abonado["nombre_completo"] or ""),
                                "abonado_dni": str(fila_nuevo_abonado["dni"] or ""),
                                "motivo": motivo,
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
                    SELECT id, estado_servicio
                    FROM casas
                    WHERE abonado_id = ?
                      AND eliminado_en IS NULL
                      AND estado_servicio != 'INACTIVO'
                      AND estado_servicio != 'SUSPENDIDO';
                    """,
                    (abonado_id,),
                ).fetchall()
                if not filas_afectadas:
                    return 0

                conexion.execute(
                    """
                    UPDATE casas
                    SET estado_servicio = 'SUSPENDIDO',
                        actualizado_en = datetime('now')
                    WHERE abonado_id = ?
                      AND eliminado_en IS NULL
                      AND estado_servicio != 'INACTIVO'
                      AND estado_servicio != 'SUSPENDIDO';
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
                                {"estado_servicio": str(fila["estado_servicio"] or "")},
                                ensure_ascii=True,
                            ),
                            json.dumps({"estado_servicio": "SUSPENDIDO"}, ensure_ascii=True),
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
                    OR a.dni LIKE ?
                    OR lower(COALESCE(a.nombre_completo, '')) LIKE lower(?)
                    OR lower(COALESCE(c.direccion_referencia, '')) LIKE lower(?)
                )
                """
            )
            parametros.extend([patron, patron, patron, patron, patron])

        if filtro_rapido == FILTRO_CASAS_ACTIVAS:
            condiciones.append("c.estado_servicio = 'ACTIVO'")
        elif filtro_rapido == FILTRO_CASAS_SUSPENDIDAS:
            condiciones.append("c.estado_servicio = 'SUSPENDIDO'")
        elif filtro_rapido == FILTRO_CASAS_CON_MORA:
            condiciones.append("COALESCE(dd.meses_en_mora, 0) > 0")
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
            deuda_total_centavos=int(fila["deuda_total_centavos"] or 0),
            meses_pendientes=int(fila["meses_pendientes"] or 0),
            meses_en_mora=int(fila["meses_en_mora"] or 0),
            tiene_plan_activo=int(fila["total_planes_activos"] or 0) > 0,
            fecha_alta=str(fila["fecha_alta"] or ""),
            actualizado_en=str(fila["actualizado_en"] or ""),
        )
