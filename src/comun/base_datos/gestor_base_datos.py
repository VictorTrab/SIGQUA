"""Utilidades compartidas para inicializar y abrir SQLite en SICAP."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from comun.configuracion.gestor_rutas import GestorRutas


class GestorBaseDatos:
    """Centraliza la inicializacion y apertura segura de la base de datos."""

    VERSION_MIGRACION_DATOS_PRUEBA = "004"

    def __init__(self, gestor_rutas: GestorRutas | None = None) -> None:
        self._gestor_rutas = gestor_rutas or GestorRutas()

    def obtener_conexion(self) -> sqlite3.Connection:
        """Abre una conexion SQLite con la configuracion minima requerida."""
        self._gestor_rutas.asegurar_directorios_base()

        conexion = sqlite3.connect(self._gestor_rutas.obtener_ruta_base_datos())
        conexion.row_factory = sqlite3.Row
        conexion.execute("PRAGMA foreign_keys = ON;")
        conexion.execute("PRAGMA busy_timeout = 5000;")
        return conexion

    def inicializar_base_datos(
        self,
        forzar_recreacion: bool = False,
        incluir_datos_prueba: bool = False,
    ) -> Path:
        """Crea la base y aplica migraciones versionadas pendientes."""
        self._gestor_rutas.asegurar_directorios_base()

        ruta_base_datos = self._gestor_rutas.obtener_ruta_base_datos()
        ruta_esquema = self._gestor_rutas.obtener_ruta_esquema_inicial_base_datos()
        ruta_migraciones = self._gestor_rutas.obtener_ruta_migraciones_base_datos()

        if not ruta_esquema.exists():
            raise FileNotFoundError(
                f"No se encontro el esquema inicial de la base de datos: {ruta_esquema}"
            )

        if forzar_recreacion and ruta_base_datos.exists():
            ruta_base_datos.unlink()

        if not ruta_base_datos.exists():
            self._crear_base_desde_esquema_inicial(ruta_base_datos, ruta_esquema)

        self._aplicar_migraciones_pendientes(
            ruta_base_datos,
            ruta_migraciones,
            incluir_datos_prueba=incluir_datos_prueba,
        )
        return ruta_base_datos

    def _crear_base_desde_esquema_inicial(
        self,
        ruta_base_datos: Path,
        ruta_esquema: Path,
    ) -> None:
        script_sql = ruta_esquema.read_text(encoding="utf-8")
        conexion: sqlite3.Connection | None = None
        try:
            conexion = sqlite3.connect(ruta_base_datos)
            with conexion:
                conexion.execute("PRAGMA foreign_keys = ON;")
                conexion.executescript(script_sql)

                resultado_integridad = conexion.execute("PRAGMA integrity_check;").fetchone()
                if not resultado_integridad or resultado_integridad[0] != "ok":
                    raise RuntimeError(
                        "La validacion de integridad SQLite fallo despues de crear la base de datos."
                    )

                errores_claves_foraneas = conexion.execute(
                    "PRAGMA foreign_key_check;"
                ).fetchall()
                if errores_claves_foraneas:
                    raise RuntimeError(
                        "Se detectaron errores de claves foraneas despues de crear la base de datos."
                    )
        except Exception:
            if ruta_base_datos.exists():
                ruta_base_datos.unlink()
            raise
        finally:
            if conexion is not None:
                conexion.close()

    def _aplicar_migraciones_pendientes(
        self,
        ruta_base_datos: Path,
        ruta_migraciones: Path,
        *,
        incluir_datos_prueba: bool,
    ) -> None:
        rutas_migracion = sorted(ruta_migraciones.glob("[0-9][0-9][0-9]_*.sql"))
        if not rutas_migracion:
            return

        conexion = sqlite3.connect(ruta_base_datos)
        try:
            conexion.row_factory = sqlite3.Row
            conexion.execute("PRAGMA foreign_keys = ON;")
            versiones_aplicadas = {
                str(fila["version"])
                for fila in conexion.execute(
                    "SELECT version FROM esquema_migraciones;"
                ).fetchall()
            }
            for ruta_migracion in rutas_migracion:
                version = ruta_migracion.stem.split("_", maxsplit=1)[0]
                if version in versiones_aplicadas:
                    continue
                if (
                    version == self.VERSION_MIGRACION_DATOS_PRUEBA
                    and not incluir_datos_prueba
                ):
                    continue

                script_sql = ruta_migracion.read_text(encoding="utf-8")
                with conexion:
                    conexion.executescript(script_sql)

                resultado_integridad = conexion.execute("PRAGMA integrity_check;").fetchone()
                if not resultado_integridad or resultado_integridad[0] != "ok":
                    raise RuntimeError(
                        f"La validacion de integridad SQLite fallo tras aplicar {ruta_migracion.name}."
                    )

                errores_claves_foraneas = conexion.execute(
                    "PRAGMA foreign_key_check;"
                ).fetchall()
                if errores_claves_foraneas:
                    raise RuntimeError(
                        f"Se detectaron errores de claves foraneas tras aplicar {ruta_migracion.name}."
                    )
        finally:
            conexion.close()
