"""Persistencia SQLite de la configuracion operativa."""

from __future__ import annotations

from contextlib import closing
from typing import Protocol

from comun.base_datos import GestorBaseDatos
from modulos.configuracion.entidades import ParametroConfiguracion


class RepositorioConfiguracion(Protocol):
    """Contrato minimo de configuracion persistida."""

    def listar_por_claves(
        self,
        claves: tuple[str, ...],
    ) -> dict[str, ParametroConfiguracion]:
        """Obtiene parametros indexados por clave."""

    def actualizar_valores(
        self,
        valores: dict[str, str],
        actor_id: int | None = None,
    ) -> None:
        """Actualiza parametros editables."""

    def obtener_resumen_comprobantes(self) -> tuple[int, str, int]:
        """Retorna correlativo global, ultimo comprobante y total emitido."""


class RepositorioConfiguracionSQLite:
    """Implementacion SQLite para configuracion_sistema."""

    def __init__(self, gestor_base_datos: GestorBaseDatos) -> None:
        self._gestor_base_datos = gestor_base_datos

    def listar_por_claves(
        self,
        claves: tuple[str, ...],
    ) -> dict[str, ParametroConfiguracion]:
        if not claves:
            return {}
        marcadores = ", ".join("?" for _ in claves)
        consulta = f"""
            SELECT
                cs.clave,
                cs.valor,
                cs.tipo_dato,
                cs.categoria,
                COALESCE(cs.descripcion, '') AS descripcion,
                cs.editable,
                COALESCE(cs.actualizado_en, '') AS actualizado_en,
                cs.actualizado_por,
                COALESCE(u.nombre_completo, u.nombre_usuario, '') AS actualizado_por_nombre
            FROM configuracion_sistema cs
            LEFT JOIN usuarios u ON u.id = cs.actualizado_por
            WHERE cs.clave IN ({marcadores});
        """
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            filas = conexion.execute(consulta, claves).fetchall()
        return {
            str(fila["clave"]): ParametroConfiguracion(
                clave=str(fila["clave"]),
                valor=str(fila["valor"] or ""),
                tipo_dato=str(fila["tipo_dato"] or "TEXTO"),
                categoria=str(fila["categoria"] or ""),
                descripcion=str(fila["descripcion"] or ""),
                editable=bool(fila["editable"]),
                actualizado_en=str(fila["actualizado_en"] or ""),
                actualizado_por=(
                    int(fila["actualizado_por"])
                    if fila["actualizado_por"] is not None
                    else None
                ),
                actualizado_por_nombre=str(fila["actualizado_por_nombre"] or ""),
            )
            for fila in filas
        }

    def actualizar_valores(
        self,
        valores: dict[str, str],
        actor_id: int | None = None,
    ) -> None:
        if not valores:
            return
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            with conexion:
                for clave, valor in valores.items():
                    conexion.execute(
                        """
                        UPDATE configuracion_sistema
                        SET valor = ?,
                            actualizado_en = datetime('now', 'localtime'),
                            actualizado_por = ?
                        WHERE clave = ?
                          AND editable = 1;
                        """,
                        (valor, actor_id, clave),
                    )

    def obtener_resumen_comprobantes(self) -> tuple[int, str, int]:
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            fila_correlativo = conexion.execute(
                """
                SELECT ultimo_numero
                FROM correlativos_comprobantes
                WHERE clave = 'RECIBO_GLOBAL';
                """
            ).fetchone()
            fila_total = conexion.execute(
                "SELECT COUNT(*) AS total FROM comprobantes;"
            ).fetchone()
            fila_ultimo = conexion.execute(
                """
                SELECT COALESCE(numero_comprobante, '') AS numero_comprobante
                FROM comprobantes
                ORDER BY id DESC
                LIMIT 1;
                """
            ).fetchone()
        return (
            int(fila_correlativo["ultimo_numero"] or 0) if fila_correlativo else 0,
            str(fila_ultimo["numero_comprobante"] or "") if fila_ultimo else "",
            int(fila_total["total"] or 0) if fila_total else 0,
        )
