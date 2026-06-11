from __future__ import annotations

import shutil
import sqlite3
import sys
import unittest
import uuid
from contextlib import closing
from pathlib import Path


RAIZ_PROYECTO = Path(__file__).resolve().parents[1]
RUTA_SRC = RAIZ_PROYECTO / "src"

if str(RUTA_SRC) not in sys.path:
    sys.path.insert(0, str(RUTA_SRC))

from comun.base_datos import GestorBaseDatos  # noqa: E402
from comun.configuracion.gestor_rutas import GestorRutas  # noqa: E402


class TestMigracionesBaseDatos(unittest.TestCase):
    def setUp(self) -> None:
        self.raiz_temporal = RAIZ_PROYECTO / "tests" / f"_tmp_migraciones_{uuid.uuid4().hex}"
        ruta_migraciones = self.raiz_temporal / "database" / "migrations"
        ruta_migraciones.mkdir(parents=True, exist_ok=True)
        origen = RAIZ_PROYECTO / "database" / "migrations" / "001_esquema_inicial.sql"
        shutil.copy2(origen, ruta_migraciones / origen.name)
        self.gestor = GestorBaseDatos(GestorRutas(raiz_proyecto=self.raiz_temporal))

    def tearDown(self) -> None:
        shutil.rmtree(self.raiz_temporal, ignore_errors=True)

    def test_repositorio_contiene_una_unica_migracion_001(self) -> None:
        migraciones = sorted(
            ruta.name
            for ruta in (RAIZ_PROYECTO / "database" / "migrations").glob("*.sql")
        )

        self.assertEqual(migraciones, ["001_esquema_inicial.sql"])

    def test_001_crea_base_minima_sin_usuario_tecnico_ni_datos_operativos(self) -> None:
        ruta_db = self.gestor.inicializar_base_datos()

        with closing(sqlite3.connect(ruta_db)) as conexion:
            versiones = conexion.execute(
                "SELECT version FROM esquema_migraciones ORDER BY version;"
            ).fetchall()
            roles = {
                fila[0] for fila in conexion.execute("SELECT nombre FROM roles;").fetchall()
            }
            usuarios = conexion.execute(
                "SELECT nombre_usuario, es_tecnico, es_oculto FROM usuarios;"
            ).fetchall()
            conteos = {
                tabla: conexion.execute(f"SELECT COUNT(*) FROM {tabla};").fetchone()[0]
                for tabla in ("barrios", "abonados", "casas", "pagos", "auditoria")
            }

        self.assertEqual(versiones, [("001",)])
        self.assertEqual(roles, {"ADMINISTRADOR", "CAJERO", "CONSULTA"})
        self.assertEqual(usuarios, [("admin", 0, 0)])
        self.assertEqual(conteos, {tabla: 0 for tabla in conteos})

    def test_semilla_de_pruebas_es_separada_e_idempotente(self) -> None:
        ruta_db = self.gestor.inicializar_base_datos(incluir_datos_prueba=True)
        self.gestor.inicializar_base_datos(incluir_datos_prueba=True)

        with closing(sqlite3.connect(ruta_db)) as conexion:
            total_barrios = conexion.execute("SELECT COUNT(*) FROM barrios;").fetchone()[0]
            nombres = {
                fila[0]
                for fila in conexion.execute(
                    "SELECT nombre_usuario FROM usuarios ORDER BY nombre_usuario;"
                ).fetchall()
            }
            versiones = conexion.execute(
                "SELECT version FROM esquema_migraciones ORDER BY version;"
            ).fetchall()
            errores_fk = conexion.execute("PRAGMA foreign_key_check;").fetchall()

        self.assertEqual(total_barrios, 3)
        self.assertEqual(nombres, {"admin", "cajero_demo", "consulta_demo"})
        self.assertEqual(versiones, [("001",)])
        self.assertEqual(errores_fk, [])


if __name__ == "__main__":
    unittest.main()
