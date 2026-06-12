from __future__ import annotations

import hashlib
import sqlite3
import sys
import unittest
import uuid
from contextlib import closing
from pathlib import Path
from unittest.mock import patch


RAIZ_PROYECTO = Path(__file__).resolve().parents[1]
RUTA_SRC = RAIZ_PROYECTO / "src"

if str(RUTA_SRC) not in sys.path:
    sys.path.insert(0, str(RUTA_SRC))

from comun.base_datos import GestorBaseDatos  # noqa: E402
from comun.configuracion.gestor_rutas import GestorRutas  # noqa: E402
from tests.utilidades_base_datos import inicializar_base_datos_prueba  # noqa: E402


class TestPlantillaBaseDatos(unittest.TestCase):
    def setUp(self) -> None:
        self.raiz_temporal = RAIZ_PROYECTO / "tests" / f"_tmp_plantilla_{uuid.uuid4().hex}"
        self.gestor = GestorBaseDatos(GestorRutas(raiz_proyecto=self.raiz_temporal))

    def tearDown(self) -> None:
        import shutil

        shutil.rmtree(self.raiz_temporal, ignore_errors=True)

    def test_repositorio_contiene_plantilla_versionada(self) -> None:
        self.assertTrue((RAIZ_PROYECTO / "database" / "sigqua_base.db").is_file())

    def test_plantilla_crea_base_minima_sin_datos_operativos(self) -> None:
        ruta_plantilla = RAIZ_PROYECTO / "database" / "sigqua_base.db"
        hash_antes = hashlib.sha256(ruta_plantilla.read_bytes()).hexdigest()
        ruta_db = self.gestor.inicializar_base_datos()

        with closing(sqlite3.connect(ruta_db)) as conexion:
            roles = {
                fila[0] for fila in conexion.execute("SELECT nombre FROM roles;").fetchall()
            }
            usuarios = conexion.execute(
                "SELECT nombre_usuario, es_tecnico, es_oculto, requiere_cambio_contrasena FROM usuarios;"
            ).fetchall()
            conteos = {
                tabla: conexion.execute(f"SELECT COUNT(*) FROM {tabla};").fetchone()[0]
                for tabla in ("barrios", "abonados", "casas", "pagos", "sesiones")
            }
            tablas_excluidas = {
                fila[0]
                for fila in conexion.execute(
                    """
                    SELECT name FROM sqlite_master
                    WHERE type = 'table'
                      AND name IN (
                          'auditoria', 'historial_respaldos', 'eventos_tecnicos',
                          'esquema_migraciones', 'reportes_generados'
                      );
                    """
                )
            }
            configuracion_adelantos = dict(
                conexion.execute(
                    """
                    SELECT clave, valor
                    FROM configuracion_sistema
                    WHERE clave = 'cobro.permitir_pago_adelantado';
                    """
                ).fetchall()
            )
            indice_adelantos = conexion.execute(
                """
                SELECT 1
                FROM sqlite_master
                WHERE type = 'index'
                  AND name = 'idx_pagos_adelantados_casa_periodo_unico';
                """
            ).fetchone()

        self.assertEqual(roles, {"ADMINISTRADOR", "CAJERO", "CONSULTA"})
        self.assertEqual(usuarios, [("admin", 0, 0, 1)])
        self.assertEqual(conteos, {tabla: 0 for tabla in conteos})
        self.assertEqual(tablas_excluidas, set())
        self.assertEqual(
            configuracion_adelantos,
            {
                "cobro.permitir_pago_adelantado": "0",
            },
        )
        self.assertIsNotNone(indice_adelantos)
        self.assertEqual(
            hashlib.sha256(ruta_plantilla.read_bytes()).hexdigest(),
            hash_antes,
        )

    def test_plantilla_ausente_produce_error_sin_base_parcial(self) -> None:
        gestor_rutas = GestorRutas(raiz_proyecto=self.raiz_temporal)
        gestor = GestorBaseDatos(gestor_rutas)

        with patch(
            "comun.base_datos.gestor_base_datos.RAIZ_RECURSOS",
            self.raiz_temporal / "recursos_ausentes",
        ):
            with self.assertRaises(FileNotFoundError):
                gestor.inicializar_base_datos()

        self.assertFalse(gestor_rutas.obtener_ruta_base_datos().exists())

    def test_plantilla_invalida_produce_error_sin_base_parcial(self) -> None:
        gestor_rutas = GestorRutas(raiz_proyecto=self.raiz_temporal)
        ruta_plantilla = gestor_rutas.obtener_ruta_base_datos_plantilla()
        ruta_plantilla.parent.mkdir(parents=True, exist_ok=True)
        ruta_plantilla.write_bytes(b"base invalida")

        with self.assertRaises(sqlite3.DatabaseError):
            GestorBaseDatos(gestor_rutas).inicializar_base_datos()

        self.assertFalse(gestor_rutas.obtener_ruta_base_datos().exists())

    def test_arranque_posterior_no_sobrescribe_base_operativa(self) -> None:
        ruta_db = self.gestor.inicializar_base_datos()
        with closing(sqlite3.connect(ruta_db)) as conexion:
            conexion.execute("INSERT INTO barrios(nombre, estado) VALUES ('Persistente', 'ACTIVO');")
            conexion.commit()

        self.gestor.inicializar_base_datos()

        with closing(sqlite3.connect(ruta_db)) as conexion:
            total = conexion.execute(
                "SELECT COUNT(*) FROM barrios WHERE nombre = 'Persistente';"
            ).fetchone()[0]
        self.assertEqual(total, 1)

    def test_semilla_de_pruebas_es_separada_e_idempotente(self) -> None:
        ruta_db = inicializar_base_datos_prueba(self.gestor)
        inicializar_base_datos_prueba(self.gestor)

        with closing(sqlite3.connect(ruta_db)) as conexion:
            total_barrios = conexion.execute("SELECT COUNT(*) FROM barrios;").fetchone()[0]
            nombres = {
                fila[0]
                for fila in conexion.execute(
                    "SELECT nombre_usuario FROM usuarios ORDER BY nombre_usuario;"
                ).fetchall()
            }
            errores_fk = conexion.execute("PRAGMA foreign_key_check;").fetchall()
            integridad = conexion.execute("PRAGMA integrity_check;").fetchone()[0]

        self.assertEqual(total_barrios, 3)
        self.assertEqual(nombres, {"admin", "cajero_demo", "consulta_demo"})
        self.assertEqual(errores_fk, [])
        self.assertEqual(integridad, "ok")


if __name__ == "__main__":
    unittest.main()
