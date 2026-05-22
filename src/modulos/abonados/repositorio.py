"""Contratos e implementacion SQLite del modulo de abonados."""

from __future__ import annotations

from contextlib import closing
from typing import Protocol

from comun.base_datos import GestorBaseDatos
from modulos.abonados.entidades import (
    Abonado,
    FILTRO_ABONADOS_CON_MORA,
    FILTRO_ABONADOS_CON_PLAN,
    FILTRO_ABONADOS_SIN_MORA,
    FILTRO_ABONADOS_TODOS,
    OpcionBarrio,
    ResumenAbonados,
)


SUBCONSULTA_CASAS = """
    SELECT abonado_id, COUNT(*) AS total_casas
    FROM casas
    WHERE eliminado_en IS NULL
    GROUP BY abonado_id
"""

SUBCONSULTA_DEUDA = """
    SELECT
        abonado_id,
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
                WHEN estado = 'VENCIDO' AND saldo_pendiente_centavos > 0
                THEN COALESCE(periodo_id, id)
                ELSE NULL
            END
        ) AS meses_en_mora
    FROM cargos
    WHERE anulado_en IS NULL
    GROUP BY abonado_id
"""

SUBCONSULTA_PLANES = """
    SELECT abonado_id, COUNT(*) AS total_planes_activos
    FROM planes_pago
    WHERE estado = 'ACTIVO'
    GROUP BY abonado_id
"""


class RepositorioAbonados(Protocol):
    """Define la persistencia requerida por abonados."""

    def listar(
        self,
        filtro: str = "",
        filtro_rapido: str = FILTRO_ABONADOS_TODOS,
        limite: int | None = None,
        desplazamiento: int = 0,
    ) -> list[Abonado]:
        """Lista abonados visibles con su contexto operativo."""

    def contar(self, filtro: str = "", filtro_rapido: str = FILTRO_ABONADOS_TODOS) -> int:
        """Cuenta abonados visibles segun filtros."""

    def obtener_resumen(self) -> ResumenAbonados:
        """Obtiene metricas de cabecera del modulo."""

    def obtener_por_id(self, abonado_id: int) -> Abonado | None:
        """Obtiene un abonado por ID."""

    def guardar(self, abonado: Abonado) -> None:
        """Crea o actualiza un abonado."""

    def cambiar_estado(self, abonado_id: int, estado: str) -> None:
        """Activa o inactiva un abonado."""

    def listar_barrios_disponibles(self) -> list[OpcionBarrio]:
        """Obtiene barrios utilizables en formularios."""


class RepositorioAbonadosSQLite:
    """Repositorio SQLite para abonados."""

    def __init__(self, gestor_base_datos: GestorBaseDatos) -> None:
        self._gestor_base_datos = gestor_base_datos

    def listar(
        self,
        filtro: str = "",
        filtro_rapido: str = FILTRO_ABONADOS_TODOS,
        limite: int | None = None,
        desplazamiento: int = 0,
    ) -> list[Abonado]:
        condiciones, parametros = self._construir_filtros(filtro, filtro_rapido)
        clausula_paginacion = ""
        if limite is not None:
            clausula_paginacion = "LIMIT ? OFFSET ?"
            parametros.extend([limite, desplazamiento])

        consulta = f"""
            SELECT
                a.id,
                a.dni,
                a.nombre_completo,
                COALESCE(a.telefono, '') AS telefono,
                a.barrio_id,
                b.nombre AS barrio_nombre,
                COALESCE(a.direccion_referencia, '') AS direccion_referencia,
                COALESCE(a.observaciones, '') AS observaciones,
                a.estado,
                COALESCE(a.creado_en, '') AS creado_en,
                COALESCE(a.actualizado_en, '') AS actualizado_en,
                COALESCE(cs.total_casas, 0) AS total_casas,
                COALESCE(dd.meses_en_mora, 0) AS meses_en_mora,
                COALESCE(dd.deuda_total_centavos, 0) AS deuda_total_centavos,
                COALESCE(pp.total_planes_activos, 0) AS total_planes_activos
            FROM abonados a
            INNER JOIN barrios b ON b.id = a.barrio_id
            LEFT JOIN ({SUBCONSULTA_CASAS}) cs ON cs.abonado_id = a.id
            LEFT JOIN ({SUBCONSULTA_DEUDA}) dd ON dd.abonado_id = a.id
            LEFT JOIN ({SUBCONSULTA_PLANES}) pp ON pp.abonado_id = a.id
            WHERE {' AND '.join(condiciones)}
            ORDER BY lower(a.nombre_completo), a.dni
            {clausula_paginacion};
        """
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            filas = conexion.execute(consulta, tuple(parametros)).fetchall()
        return [self._fila_a_abonado(fila) for fila in filas]

    def contar(self, filtro: str = "", filtro_rapido: str = FILTRO_ABONADOS_TODOS) -> int:
        condiciones, parametros = self._construir_filtros(filtro, filtro_rapido)
        consulta = f"""
            SELECT COUNT(*)
            FROM abonados a
            INNER JOIN barrios b ON b.id = a.barrio_id
            LEFT JOIN ({SUBCONSULTA_DEUDA}) dd ON dd.abonado_id = a.id
            LEFT JOIN ({SUBCONSULTA_PLANES}) pp ON pp.abonado_id = a.id
            WHERE {' AND '.join(condiciones)};
        """
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            return int(conexion.execute(consulta, tuple(parametros)).fetchone()[0] or 0)

    def obtener_resumen(self) -> ResumenAbonados:
        consulta = f"""
            SELECT
                COUNT(*) AS total_abonados,
                SUM(CASE WHEN a.estado = 'ACTIVO' THEN 1 ELSE 0 END) AS abonados_activos,
                SUM(
                    CASE WHEN COALESCE(dd.deuda_total_centavos, 0) > 0 THEN 1 ELSE 0 END
                ) AS abonados_con_deuda,
                SUM(CASE WHEN COALESCE(dd.meses_en_mora, 0) > 0 THEN 1 ELSE 0 END) AS abonados_morosos
            FROM abonados a
            LEFT JOIN ({SUBCONSULTA_DEUDA}) dd ON dd.abonado_id = a.id
            WHERE a.eliminado_en IS NULL;
        """
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            fila = conexion.execute(consulta).fetchone()
        return ResumenAbonados(
            total_abonados=int(fila["total_abonados"] or 0),
            abonados_activos=int(fila["abonados_activos"] or 0),
            abonados_con_deuda=int(fila["abonados_con_deuda"] or 0),
            abonados_morosos=int(fila["abonados_morosos"] or 0),
        )

    def obtener_por_id(self, abonado_id: int) -> Abonado | None:
        consulta = f"""
            SELECT
                a.id,
                a.dni,
                a.nombre_completo,
                COALESCE(a.telefono, '') AS telefono,
                a.barrio_id,
                b.nombre AS barrio_nombre,
                COALESCE(a.direccion_referencia, '') AS direccion_referencia,
                COALESCE(a.observaciones, '') AS observaciones,
                a.estado,
                COALESCE(a.creado_en, '') AS creado_en,
                COALESCE(a.actualizado_en, '') AS actualizado_en,
                COALESCE(cs.total_casas, 0) AS total_casas,
                COALESCE(dd.meses_en_mora, 0) AS meses_en_mora,
                COALESCE(dd.deuda_total_centavos, 0) AS deuda_total_centavos,
                COALESCE(pp.total_planes_activos, 0) AS total_planes_activos
            FROM abonados a
            INNER JOIN barrios b ON b.id = a.barrio_id
            LEFT JOIN ({SUBCONSULTA_CASAS}) cs ON cs.abonado_id = a.id
            LEFT JOIN ({SUBCONSULTA_DEUDA}) dd ON dd.abonado_id = a.id
            LEFT JOIN ({SUBCONSULTA_PLANES}) pp ON pp.abonado_id = a.id
            WHERE a.id = ? AND a.eliminado_en IS NULL
            LIMIT 1;
        """
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            fila = conexion.execute(consulta, (abonado_id,)).fetchone()
        return self._fila_a_abonado(fila) if fila is not None else None

    def guardar(self, abonado: Abonado) -> None:
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            with conexion:
                if abonado.identificador is None:
                    conexion.execute(
                        """
                        INSERT INTO abonados(
                            dni,
                            nombre_completo,
                            telefono,
                            barrio_id,
                            direccion_referencia,
                            observaciones,
                            estado,
                            actualizado_en
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now', 'localtime'));
                        """,
                        (
                            abonado.dni,
                            abonado.nombre_completo,
                            abonado.telefono,
                            abonado.barrio_id,
                            abonado.direccion_referencia,
                            abonado.observaciones,
                            abonado.estado,
                        ),
                    )
                    return

                conexion.execute(
                    """
                    UPDATE abonados
                    SET dni = ?,
                        nombre_completo = ?,
                        telefono = ?,
                        barrio_id = ?,
                        direccion_referencia = ?,
                        observaciones = ?,
                        estado = ?,
                        actualizado_en = datetime('now', 'localtime')
                    WHERE id = ? AND eliminado_en IS NULL;
                    """,
                    (
                        abonado.dni,
                        abonado.nombre_completo,
                        abonado.telefono,
                        abonado.barrio_id,
                        abonado.direccion_referencia,
                        abonado.observaciones,
                        abonado.estado,
                        abonado.identificador,
                    ),
                )

    def cambiar_estado(self, abonado_id: int, estado: str) -> None:
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            with conexion:
                conexion.execute(
                    """
                    UPDATE abonados
                    SET estado = ?,
                        actualizado_en = datetime('now', 'localtime')
                    WHERE id = ? AND eliminado_en IS NULL;
                    """,
                    (estado, abonado_id),
                )

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

    def _construir_filtros(
        self,
        filtro: str,
        filtro_rapido: str,
    ) -> tuple[list[str], list[object]]:
        condiciones = ["a.eliminado_en IS NULL"]
        parametros: list[object] = []
        filtro = filtro.strip()
        if filtro:
            patron = f"%{filtro}%"
            condiciones.append(
                """
                (
                    a.dni LIKE ?
                    OR lower(a.nombre_completo) LIKE lower(?)
                    OR lower(COALESCE(b.nombre, '')) LIKE lower(?)
                    OR lower(printf('BR-%03d', a.barrio_id)) LIKE lower(?)
                )
                """
            )
            parametros.extend([patron, patron, patron, patron])

        if filtro_rapido == FILTRO_ABONADOS_CON_MORA:
            condiciones.append("COALESCE(dd.meses_en_mora, 0) > 0")
        elif filtro_rapido == FILTRO_ABONADOS_SIN_MORA:
            condiciones.append("COALESCE(dd.meses_en_mora, 0) = 0")
        elif filtro_rapido == FILTRO_ABONADOS_CON_PLAN:
            condiciones.append("COALESCE(pp.total_planes_activos, 0) > 0")

        return condiciones, parametros

    @staticmethod
    def _fila_a_abonado(fila: object) -> Abonado:
        return Abonado(
            identificador=int(fila["id"]),
            dni=str(fila["dni"]),
            nombre_completo=str(fila["nombre_completo"]),
            telefono=str(fila["telefono"] or ""),
            barrio_id=int(fila["barrio_id"]) if fila["barrio_id"] is not None else None,
            barrio_nombre=str(fila["barrio_nombre"] or ""),
            direccion_referencia=str(fila["direccion_referencia"] or ""),
            observaciones=str(fila["observaciones"] or ""),
            estado=str(fila["estado"]),
            total_casas=int(fila["total_casas"] or 0),
            meses_en_mora=int(fila["meses_en_mora"] or 0),
            deuda_total_centavos=int(fila["deuda_total_centavos"] or 0),
            tiene_plan_activo=int(fila["total_planes_activos"] or 0) > 0,
            creado_en=str(fila["creado_en"] or ""),
            actualizado_en=str(fila["actualizado_en"] or ""),
        )

