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
from comun.configuracion.gestor_rutas import GestorRutas, RAIZ_INSTALACION  # noqa: E402


class TestGestorBaseDatos(unittest.TestCase):
    def setUp(self) -> None:
        self.directorio_temporal = tempfile.TemporaryDirectory()
        self.raiz_temporal = Path(self.directorio_temporal.name)

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

    def test_rutas_operativas_de_produccion_quedan_fuera_del_proyecto(self) -> None:
        gestor_rutas = GestorRutas()

        self.assertEqual(
            gestor_rutas.obtener_ruta_exportaciones(),
            Path.home() / "Documents" / "SIGQUA_EXPORTACIONES",
        )
        self.assertEqual(
            gestor_rutas.obtener_ruta_exportaciones_reportes(),
            gestor_rutas.obtener_ruta_exportaciones() / "Reportes",
        )
        self.assertEqual(
            gestor_rutas.obtener_ruta_exportaciones_comprobantes(),
            gestor_rutas.obtener_ruta_exportaciones() / "Comprobantes",
        )
        self.assertEqual(
            gestor_rutas.obtener_ruta_reportes_predeterminada(),
            gestor_rutas.obtener_ruta_exportaciones_reportes(),
        )
        self.assertFalse(
            gestor_rutas.obtener_ruta_exportaciones().is_relative_to(RAIZ_INSTALACION)
        )
        self.assertFalse(
            gestor_rutas.obtener_ruta_reportes_predeterminada().is_relative_to(
                RAIZ_INSTALACION
            )
        )
        self.assertFalse(
            gestor_rutas.obtener_ruta_respaldos().is_relative_to(RAIZ_INSTALACION)
        )


if __name__ == "__main__":
    unittest.main()
