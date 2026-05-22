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

    def obtener_resumen_comprobantes(self) -> tuple[int, str, int]:
        """Retorna correlativo global, ultimo comprobante y total emitido."""

    def obtener_resumen_respaldos(self) -> tuple[str, str, int]:
        """Retorna ultima fecha, ultimo estado y total de respaldos."""

    def obtener_detalle_ultimo_respaldo(self) -> dict[str, object]:
        """Retorna metadatos del ultimo respaldo registrado."""

    def registrar_respaldo(
        self,
        nombre_archivo: str,
        ruta_archivo: str,
        tamano_bytes: int,
        hash_archivo: str,
        tipo_respaldo: str,
        estado: str,
        observaciones: str,
        generado_por: int | None = None,
    ) -> None:
        """Registra un respaldo generado desde la capa operativa."""


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
                    int(fila["actualizado_por"]) if fila["actualizado_por"] is not None else None
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
                SELECT ultimo_numero, COALESCE(actualizado_en, '') AS actualizado_en
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

    def obtener_resumen_respaldos(self) -> tuple[str, str, int]:
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            fila_ultimo = conexion.execute(
                """
                SELECT
                    COALESCE(generado_en, '') AS generado_en,
                    COALESCE(estado, '') AS estado
                FROM historial_respaldos
                ORDER BY generado_en DESC, id DESC
                LIMIT 1;
                """
            ).fetchone()
            fila_total = conexion.execute(
                "SELECT COUNT(*) AS total FROM historial_respaldos;"
            ).fetchone()
        return (
            str(fila_ultimo["generado_en"] or "") if fila_ultimo else "",
            str(fila_ultimo["estado"] or "") if fila_ultimo else "",
            int(fila_total["total"] or 0) if fila_total else 0,
        )

    def obtener_detalle_ultimo_respaldo(self) -> dict[str, object]:
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            fila = conexion.execute(
                """
                SELECT
                    COALESCE(hr.nombre_archivo, '') AS nombre_archivo,
                    COALESCE(hr.ruta_archivo, '') AS ruta_archivo,
                    COALESCE(hr.tamano_bytes, 0) AS tamano_bytes,
                    COALESCE(hr.hash_archivo, '') AS hash_archivo,
                    COALESCE(hr.tipo_respaldo, '') AS tipo_respaldo,
                    COALESCE(hr.estado, '') AS estado,
                    COALESCE(hr.observaciones, '') AS observaciones,
                    COALESCE(hr.generado_en, '') AS generado_en,
                    COALESCE(u.nombre_completo, u.nombre_usuario, '') AS generado_por_nombre
                FROM historial_respaldos hr
                LEFT JOIN usuarios u ON u.id = hr.generado_por
                ORDER BY hr.generado_en DESC, hr.id DESC
                LIMIT 1;
                """
            ).fetchone()
        if fila is None:
            return {}
        return {
            "nombre_archivo": str(fila["nombre_archivo"] or ""),
            "ruta_archivo": str(fila["ruta_archivo"] or ""),
            "tamano_bytes": int(fila["tamano_bytes"] or 0),
            "hash_archivo": str(fila["hash_archivo"] or ""),
            "tipo_respaldo": str(fila["tipo_respaldo"] or ""),
            "estado": str(fila["estado"] or ""),
            "observaciones": str(fila["observaciones"] or ""),
            "generado_en": str(fila["generado_en"] or ""),
            "generado_por_nombre": str(fila["generado_por_nombre"] or ""),
        }

    def registrar_respaldo(
        self,
        nombre_archivo: str,
        ruta_archivo: str,
        tamano_bytes: int,
        hash_archivo: str,
        tipo_respaldo: str,
        estado: str,
        observaciones: str,
        generado_por: int | None = None,
    ) -> None:
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            with conexion:
                conexion.execute(
                    """
                    INSERT INTO historial_respaldos(
                        tipo_respaldo,
                        nombre_archivo,
                        ruta_archivo,
                        tamano_bytes,
                        hash_archivo,
                        estado,
                        observaciones,
                        generado_por
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        tipo_respaldo,
                        nombre_archivo,
                        ruta_archivo,
                        tamano_bytes,
                        hash_archivo,
                        estado,
                        observaciones,
                        generado_por,
                    ),
                )

