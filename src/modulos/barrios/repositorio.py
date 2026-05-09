"""Contratos e implementacion SQLite del modulo de barrios."""

from __future__ import annotations

from contextlib import closing
from typing import Protocol

from comun.base_datos import GestorBaseDatos
from modulos.barrios.entidades import (
    Barrio,
    FILTRO_BARRIOS_ACTIVOS,
    FILTRO_BARRIOS_CON_ABONADOS,
    FILTRO_BARRIOS_INACTIVOS,
    FILTRO_BARRIOS_SIN_ABONADOS,
    FILTRO_BARRIOS_TODOS,
    ResumenBarrios,
)


SUBCONSULTA_ABONADOS = """
    SELECT barrio_id, COUNT(*) AS total_abonados
    FROM abonados
    WHERE eliminado_en IS NULL
    GROUP BY barrio_id
"""

SUBCONSULTA_CASAS = """
    SELECT barrio_id, COUNT(*) AS total_casas
    FROM casas
    WHERE eliminado_en IS NULL
    GROUP BY barrio_id
"""


class RepositorioBarrios(Protocol):
    """Define la persistencia requerida por barrios."""

    def listar(
        self,
        filtro: str = "",
        filtro_rapido: str = FILTRO_BARRIOS_TODOS,
        limite: int | None = None,
        desplazamiento: int = 0,
    ) -> list[Barrio]:
        """Lista barrios visibles con sus metricas operativas."""

    def contar(self, filtro: str = "", filtro_rapido: str = FILTRO_BARRIOS_TODOS) -> int:
        """Cuenta barrios visibles segun filtros."""

    def obtener_resumen(self) -> ResumenBarrios:
        """Obtiene metricas de cabecera del modulo."""

    def obtener_por_id(self, barrio_id: int) -> Barrio | None:
        """Obtiene un barrio por ID."""

    def guardar(self, barrio: Barrio) -> None:
        """Crea o actualiza un barrio."""

    def cambiar_estado(self, barrio_id: int, estado: str) -> None:
        """Activa o inactiva un barrio."""


class RepositorioBarriosSQLite:
    """Repositorio SQLite para barrios."""

    def __init__(self, gestor_base_datos: GestorBaseDatos) -> None:
        self._gestor_base_datos = gestor_base_datos

    def listar(
        self,
        filtro: str = "",
        filtro_rapido: str = FILTRO_BARRIOS_TODOS,
        limite: int | None = None,
        desplazamiento: int = 0,
    ) -> list[Barrio]:
        condiciones, parametros = self._construir_filtros(filtro, filtro_rapido)
        clausula_paginacion = ""
        if limite is not None:
            clausula_paginacion = "LIMIT ? OFFSET ?"
            parametros.extend([limite, desplazamiento])

        consulta = f"""
            SELECT
                b.id,
                b.nombre,
                b.estado,
                COALESCE(b.observaciones, '') AS observaciones,
                COALESCE(b.actualizado_en, '') AS actualizado_en,
                COALESCE(ab.total_abonados, 0) AS total_abonados,
                COALESCE(cs.total_casas, 0) AS total_casas
            FROM barrios b
            LEFT JOIN ({SUBCONSULTA_ABONADOS}) ab ON ab.barrio_id = b.id
            LEFT JOIN ({SUBCONSULTA_CASAS}) cs ON cs.barrio_id = b.id
            WHERE {' AND '.join(condiciones)}
            ORDER BY lower(b.nombre)
            {clausula_paginacion};
        """
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            filas = conexion.execute(consulta, tuple(parametros)).fetchall()
        return [self._fila_a_barrio(fila) for fila in filas]

    def contar(self, filtro: str = "", filtro_rapido: str = FILTRO_BARRIOS_TODOS) -> int:
        condiciones, parametros = self._construir_filtros(filtro, filtro_rapido)
        consulta = f"""
            SELECT COUNT(*)
            FROM barrios b
            LEFT JOIN ({SUBCONSULTA_ABONADOS}) ab ON ab.barrio_id = b.id
            WHERE {' AND '.join(condiciones)};
        """
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            return int(conexion.execute(consulta, tuple(parametros)).fetchone()[0] or 0)

    def obtener_resumen(self) -> ResumenBarrios:
        consulta = f"""
            SELECT
                COUNT(*) AS total_barrios,
                SUM(CASE WHEN b.estado = 'ACTIVO' THEN 1 ELSE 0 END) AS barrios_activos,
                SUM(CASE WHEN COALESCE(ab.total_abonados, 0) > 0 THEN 1 ELSE 0 END) AS barrios_con_abonados
            FROM barrios b
            LEFT JOIN ({SUBCONSULTA_ABONADOS}) ab ON ab.barrio_id = b.id
            WHERE b.eliminado_en IS NULL;
        """
        consulta_destacado = f"""
            SELECT
                b.nombre,
                COALESCE(ab.total_abonados, 0) AS total_abonados
            FROM barrios b
            LEFT JOIN ({SUBCONSULTA_ABONADOS}) ab ON ab.barrio_id = b.id
            WHERE b.eliminado_en IS NULL
            ORDER BY total_abonados DESC, lower(b.nombre) ASC
            LIMIT 1;
        """
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            fila_resumen = conexion.execute(consulta).fetchone()
            fila_destacada = conexion.execute(consulta_destacado).fetchone()

        nombre_destacado = "Sin datos"
        total_destacado = 0
        if fila_destacada is not None:
            nombre_destacado = str(fila_destacada["nombre"] or "Sin datos")
            total_destacado = int(fila_destacada["total_abonados"] or 0)

        return ResumenBarrios(
            total_barrios=int(fila_resumen["total_barrios"] or 0),
            barrios_activos=int(fila_resumen["barrios_activos"] or 0),
            barrios_con_abonados=int(fila_resumen["barrios_con_abonados"] or 0),
            barrio_con_mas_abonados=nombre_destacado,
            cantidad_maxima_abonados=total_destacado,
        )

    def obtener_por_id(self, barrio_id: int) -> Barrio | None:
        consulta = f"""
            SELECT
                b.id,
                b.nombre,
                b.estado,
                COALESCE(b.observaciones, '') AS observaciones,
                COALESCE(b.actualizado_en, '') AS actualizado_en,
                COALESCE(ab.total_abonados, 0) AS total_abonados,
                COALESCE(cs.total_casas, 0) AS total_casas
            FROM barrios b
            LEFT JOIN ({SUBCONSULTA_ABONADOS}) ab ON ab.barrio_id = b.id
            LEFT JOIN ({SUBCONSULTA_CASAS}) cs ON cs.barrio_id = b.id
            WHERE b.id = ? AND b.eliminado_en IS NULL
            LIMIT 1;
        """
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            fila = conexion.execute(consulta, (barrio_id,)).fetchone()
        return self._fila_a_barrio(fila) if fila is not None else None

    def guardar(self, barrio: Barrio) -> None:
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            with conexion:
                if barrio.identificador is None:
                    conexion.execute(
                        """
                        INSERT INTO barrios(nombre, estado, observaciones, actualizado_en)
                        VALUES (?, ?, ?, datetime('now'));
                        """,
                        (barrio.nombre, barrio.estado, barrio.observaciones),
                    )
                    return

                conexion.execute(
                    """
                    UPDATE barrios
                    SET nombre = ?,
                        estado = ?,
                        observaciones = ?,
                        actualizado_en = datetime('now')
                    WHERE id = ? AND eliminado_en IS NULL;
                    """,
                    (barrio.nombre, barrio.estado, barrio.observaciones, barrio.identificador),
                )

    def cambiar_estado(self, barrio_id: int, estado: str) -> None:
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            with conexion:
                conexion.execute(
                    """
                    UPDATE barrios
                    SET estado = ?,
                        actualizado_en = datetime('now')
                    WHERE id = ? AND eliminado_en IS NULL;
                    """,
                    (estado, barrio_id),
                )

    def _construir_filtros(
        self,
        filtro: str,
        filtro_rapido: str,
    ) -> tuple[list[str], list[object]]:
        condiciones = ["b.eliminado_en IS NULL"]
        parametros: list[object] = []
        filtro = filtro.strip()
        if filtro:
            condiciones.append("lower(b.nombre) LIKE lower(?)")
            parametros.append(f"%{filtro}%")

        if filtro_rapido == FILTRO_BARRIOS_CON_ABONADOS:
            condiciones.append("COALESCE(ab.total_abonados, 0) > 0")
        elif filtro_rapido == FILTRO_BARRIOS_SIN_ABONADOS:
            condiciones.append("COALESCE(ab.total_abonados, 0) = 0")
        elif filtro_rapido == FILTRO_BARRIOS_ACTIVOS:
            condiciones.append("b.estado = 'ACTIVO'")
        elif filtro_rapido == FILTRO_BARRIOS_INACTIVOS:
            condiciones.append("b.estado = 'INACTIVO'")

        return condiciones, parametros

    @staticmethod
    def _fila_a_barrio(fila: object) -> Barrio:
        return Barrio(
            identificador=int(fila["id"]),
            nombre=str(fila["nombre"]),
            estado=str(fila["estado"]),
            observaciones=str(fila["observaciones"] or ""),
            total_abonados=int(fila["total_abonados"] or 0),
            total_casas=int(fila["total_casas"] or 0),
            actualizado_en=str(fila["actualizado_en"] or ""),
        )
