"""Persistencia SQLite del modulo de configuracion."""

from __future__ import annotations

from contextlib import closing
from typing import Protocol

from comun.base_datos import GestorBaseDatos
from modulos.configuracion.entidades import ParametroConfiguracion


class RepositorioConfiguracion(Protocol):
    """Contrato minimo de persistencia para configuracion."""

    def listar_por_claves(self, claves: tuple[str, ...]) -> dict[str, ParametroConfiguracion]:
        """Obtiene varios parametros indexados por clave."""

    def actualizar_valores(
        self,
        valores: dict[str, str],
        actor_id: int | None = None,
    ) -> None:
        """Actualiza varios parametros editables en una sola transaccion."""


class RepositorioConfiguracionSQLite:
    """Implementacion SQLite del acceso a configuracion_sistema."""

    def __init__(self, gestor_base_datos: GestorBaseDatos) -> None:
        self._gestor_base_datos = gestor_base_datos

    def listar_por_claves(self, claves: tuple[str, ...]) -> dict[str, ParametroConfiguracion]:
        if not claves:
            return {}
        marcadores = ", ".join("?" for _ in claves)
        consulta = f"""
            SELECT
                clave,
                valor,
                tipo_dato,
                categoria,
                COALESCE(descripcion, '') AS descripcion,
                editable,
                COALESCE(actualizado_en, '') AS actualizado_en,
                actualizado_por
            FROM configuracion_sistema
            WHERE clave IN ({marcadores});
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
                    int(fila["actualizado_por"]) if fila["actualizado_por"] is not None else None
                ),
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
                            actualizado_en = datetime('now'),
                            actualizado_por = ?
                        WHERE clave = ?
                          AND editable = 1;
                        """,
                        (valor, actor_id, clave),
                    )
