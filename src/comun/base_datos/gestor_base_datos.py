"""Utilidades compartidas para inicializar y abrir SQLite en SIGQUA."""

from __future__ import annotations

import sqlite3
from pathlib import Path
import shutil
import tempfile

from comun.configuracion.gestor_rutas import GestorRutas, RAIZ_RECURSOS


class GestorBaseDatos:
    """Centraliza la inicializacion y apertura segura de la base de datos."""

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
    ) -> Path:
        """Copia la plantilla limpia cuando no existe una base operativa."""
        self._gestor_rutas.asegurar_directorios_base()

        ruta_base_datos = self._gestor_rutas.obtener_ruta_base_datos()
        ruta_plantilla = self._gestor_rutas.obtener_ruta_base_datos_plantilla()
        if not ruta_plantilla.exists():
            ruta_plantilla_empaquetada = RAIZ_RECURSOS / "database" / "sigqua_base.db"
            if ruta_plantilla_empaquetada.exists():
                ruta_plantilla = ruta_plantilla_empaquetada

        if not ruta_plantilla.exists():
            raise FileNotFoundError(
                f"No se encontro la base plantilla de SIGQUA: {ruta_plantilla}"
            )

        if forzar_recreacion and ruta_base_datos.exists():
            ruta_base_datos.unlink()

        if not ruta_base_datos.exists():
            self._copiar_plantilla_atomicamente(ruta_plantilla, ruta_base_datos)

        self._validar_base_datos(ruta_base_datos)
        return ruta_base_datos

    def _copiar_plantilla_atomicamente(
        self,
        ruta_plantilla: Path,
        ruta_base_datos: Path,
    ) -> None:
        """Copia la plantilla sin exponer una base operativa parcial."""
        ruta_temporal: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                prefix="sigqua_",
                suffix=".db.tmp",
                dir=ruta_base_datos.parent,
                delete=False,
            ) as archivo_temporal:
                ruta_temporal = Path(archivo_temporal.name)
            shutil.copy2(ruta_plantilla, ruta_temporal)
            self._validar_base_datos(ruta_temporal)
            ruta_temporal.replace(ruta_base_datos)
        except Exception:
            if ruta_temporal is not None:
                ruta_temporal.unlink(missing_ok=True)
            if ruta_base_datos.exists():
                ruta_base_datos.unlink()
            raise

    @staticmethod
    def _validar_base_datos(ruta_base_datos: Path) -> None:
        conexion = sqlite3.connect(ruta_base_datos)
        try:
            conexion.execute("PRAGMA foreign_keys = ON;")
            resultado = conexion.execute("PRAGMA integrity_check;").fetchone()
            if not resultado or str(resultado[0]).lower() != "ok":
                raise RuntimeError("La base de datos no supero la validacion de integridad.")
            errores = conexion.execute("PRAGMA foreign_key_check;").fetchall()
            if errores:
                raise RuntimeError("La base de datos contiene claves foraneas invalidas.")
        finally:
            conexion.close()
