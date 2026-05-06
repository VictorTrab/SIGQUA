from __future__ import annotations

import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path


RAIZ_PROYECTO = Path(__file__).resolve().parents[1]
RUTA_SRC = RAIZ_PROYECTO / "src"

if str(RUTA_SRC) not in sys.path:
    sys.path.insert(0, str(RUTA_SRC))

from comun.base_datos import GestorBaseDatos  # noqa: E402
from comun.configuracion.gestor_rutas import GestorRutas  # noqa: E402


class TestGestorBaseDatos(unittest.TestCase):
    def setUp(self) -> None:
        self.directorio_temporal = tempfile.TemporaryDirectory()
        self.raiz_temporal = Path(self.directorio_temporal.name)
        (self.raiz_temporal / "database" / "migrations").mkdir(parents=True, exist_ok=True)

        ruta_esquema_real = (
            RAIZ_PROYECTO / "database" / "migrations" / "002_esquema_inicial.sql"
        )
        contenido_sql = ruta_esquema_real.read_text(encoding="utf-8")
        (self.raiz_temporal / "database" / "migrations" / "002_esquema_inicial.sql").write_text(
            contenido_sql,
            encoding="utf-8",
        )

        self.gestor = GestorBaseDatos(GestorRutas(raiz_proyecto=self.raiz_temporal))

    def tearDown(self) -> None:
        self.directorio_temporal.cleanup()

    def test_inicializar_base_datos_crea_tablas_y_datos_semilla(self) -> None:
        ruta_base_datos = self.gestor.inicializar_base_datos()

        self.assertTrue(ruta_base_datos.exists())

        conexion = sqlite3.connect(ruta_base_datos)
        try:
            tablas = {
                fila[0]
                for fila in conexion.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table';"
                ).fetchall()
            }
            self.assertIn("usuarios", tablas)
            self.assertIn("abonados", tablas)

            usuario_admin = conexion.execute(
                "SELECT nombre_usuario, contrasena_hash FROM usuarios WHERE id = 1;"
            ).fetchone()
            self.assertEqual(usuario_admin[0], "admin")
            self.assertTrue(usuario_admin[1].startswith("scrypt$"))
        finally:
            conexion.close()

    def test_obtener_conexion_activa_claves_foraneas(self) -> None:
        self.gestor.inicializar_base_datos()

        conexion = self.gestor.obtener_conexion()
        try:
            estado_claves_foraneas = conexion.execute("PRAGMA foreign_keys;").fetchone()
        finally:
            conexion.close()

        self.assertEqual(estado_claves_foraneas[0], 1)


if __name__ == "__main__":
    unittest.main()
