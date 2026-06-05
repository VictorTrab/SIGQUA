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
        (self.raiz_temporal / "database" / "migrations").mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        if self.raiz_temporal.exists():
            shutil.rmtree(self.raiz_temporal, ignore_errors=True)

    def test_migracion_005_repara_triggers_legacy_de_auditoria(self) -> None:
        ruta_migraciones_origen = RAIZ_PROYECTO / "database" / "migrations"
        for nombre in (
            "002_esquema_inicial.sql",
            "003_seguridad_superadmin_mantenimiento.sql",
            "004_datos_prueba_desarrollo.sql",
        ):
            origen = ruta_migraciones_origen / nombre
            destino = self.raiz_temporal / "database" / "migrations" / nombre
            destino.write_text(origen.read_text(encoding="utf-8"), encoding="utf-8")

        gestor_rutas = GestorRutas(raiz_proyecto=self.raiz_temporal)
        gestor = GestorBaseDatos(gestor_rutas)
        ruta_db = gestor.inicializar_base_datos(incluir_datos_prueba=True)

        with closing(sqlite3.connect(ruta_db)) as conexion:
            conexion.executescript(
                """
                DROP TRIGGER IF EXISTS trg_auditoria_pago_anulado;
                CREATE TRIGGER trg_auditoria_pago_anulado
                AFTER UPDATE OF estado ON pagos
                FOR EACH ROW
                WHEN OLD.estado <> NEW.estado AND NEW.estado = 'ANULADO'
                BEGIN
                    INSERT INTO "auditoria_legacy_003"(
                        usuario_id,
                        accion,
                        entidad,
                        entidad_id,
                        resumen,
                        datos_antes_json,
                        datos_despues_json
                    )
                    VALUES (
                        NEW.anulado_por,
                        'ANULAR_PAGO',
                        'pagos',
                        NEW.id,
                        'Pago anulado',
                        '{}',
                        '{}'
                    );
                END;

                DROP TRIGGER IF EXISTS trg_auditoria_cambio_estado_casa;
                CREATE TRIGGER trg_auditoria_cambio_estado_casa
                AFTER UPDATE OF estado_servicio ON casas
                FOR EACH ROW
                WHEN OLD.estado_servicio <> NEW.estado_servicio
                BEGIN
                    INSERT INTO "auditoria_legacy_003"(
                        usuario_id,
                        accion,
                        entidad,
                        entidad_id,
                        resumen,
                        datos_antes_json,
                        datos_despues_json
                    )
                    VALUES (
                        NULL,
                        'CAMBIAR_ESTADO_SERVICIO',
                        'casas',
                        NEW.id,
                        'Cambio de estado',
                        '{}',
                        '{}'
                    );
                END;
                """
            )

        migracion_005 = ruta_migraciones_origen / "005_reparar_triggers_auditoria_post_legacy.sql"
        (self.raiz_temporal / "database" / "migrations" / migracion_005.name).write_text(
            migracion_005.read_text(encoding="utf-8"),
            encoding="utf-8",
        )

        gestor.inicializar_base_datos(incluir_datos_prueba=True)

        with closing(sqlite3.connect(ruta_db)) as conexion:
            triggers_rotos = conexion.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'trigger'
                  AND sql LIKE '%auditoria_legacy_003%';
                """
            ).fetchall()
            version_005 = conexion.execute(
                "SELECT 1 FROM esquema_migraciones WHERE version = '005' LIMIT 1;"
            ).fetchone()

            self.assertEqual(triggers_rotos, [])
            self.assertIsNotNone(version_005)

            conexion.execute(
                """
                UPDATE casas
                SET estado_servicio = 'SUSPENDIDO',
                    actualizado_en = datetime('now', 'localtime')
                WHERE id = 1;
                """
            )
            auditoria = conexion.execute(
                """
                SELECT accion, entidad, entidad_id
                FROM auditoria
                WHERE accion = 'CAMBIAR_ESTADO_SERVICIO'
                  AND entidad = 'casas'
                  AND entidad_id = 1
                ORDER BY id DESC
                LIMIT 1;
                """
            ).fetchone()
            self.assertIsNotNone(auditoria)

    def test_migracion_014_separa_estado_fisico_administrativo_y_activacion(self) -> None:
        ruta_migraciones_origen = RAIZ_PROYECTO / "database" / "migrations"
        for ruta in ruta_migraciones_origen.glob("*.sql"):
            destino = self.raiz_temporal / "database" / "migrations" / ruta.name
            destino.write_text(ruta.read_text(encoding="utf-8"), encoding="utf-8")

        gestor_rutas = GestorRutas(raiz_proyecto=self.raiz_temporal)
        gestor = GestorBaseDatos(gestor_rutas)
        ruta_db = gestor.inicializar_base_datos(incluir_datos_prueba=True)

        with closing(sqlite3.connect(ruta_db)) as conexion:
            columnas_casas = {
                fila[1] for fila in conexion.execute("PRAGMA table_info(casas);").fetchall()
            }
            columnas_procesos = {
                fila[1] for fila in conexion.execute("PRAGMA table_info(procesos_servicio);").fetchall()
            }
            columnas_cargos = {
                fila[1] for fila in conexion.execute("PRAGMA table_info(cargos);").fetchall()
            }
            casa_suspendida = conexion.execute(
                """
                SELECT estado_servicio, estado_administrativo, motivo_estado_administrativo
                FROM casas
                WHERE direccion_referencia = 'Casa 03, pasaje las flores'
                LIMIT 1;
                """
            ).fetchone()
            configuracion = conexion.execute(
                """
                SELECT valor
                FROM configuracion_sistema
                WHERE clave = 'cobro.cobrar_mensualidad_prorrateada_activacion'
                LIMIT 1;
                """
            ).fetchone()
            conceptos = {
                fila[0]
                for fila in conexion.execute(
                    """
                    SELECT codigo
                    FROM conceptos_cobro
                    WHERE codigo IN ('CONEXION', 'MENSUALIDAD_PRORRATEADA');
                    """
                ).fetchall()
            }

        self.assertIn("estado_administrativo", columnas_casas)
        self.assertIn("motivo_estado_administrativo", columnas_casas)
        self.assertIn("ha_tenido_servicio_activo", columnas_casas)
        self.assertIn("fecha_activacion", columnas_procesos)
        self.assertIn("pago_id", columnas_procesos)
        self.assertIn("proceso_servicio_id", columnas_cargos)
        self.assertIsNotNone(casa_suspendida)
        self.assertEqual(casa_suspendida[0], "ACTIVO")
        self.assertEqual(casa_suspendida[1], "SUSPENDIDA")
        self.assertEqual(casa_suspendida[2], "REVISION_ADMINISTRATIVA")
        self.assertIsNotNone(configuracion)
        self.assertEqual(configuracion[0], "0")
        self.assertEqual(conceptos, {"CONEXION", "MENSUALIDAD_PRORRATEADA"})

    def test_migracion_016_se_recupera_si_la_columna_ya_existe_pero_falta_la_version(self) -> None:
        ruta_migraciones_origen = RAIZ_PROYECTO / "database" / "migrations"
        for ruta in ruta_migraciones_origen.glob("*.sql"):
            destino = self.raiz_temporal / "database" / "migrations" / ruta.name
            destino.write_text(ruta.read_text(encoding="utf-8"), encoding="utf-8")

        gestor_rutas = GestorRutas(raiz_proyecto=self.raiz_temporal)
        gestor = GestorBaseDatos(gestor_rutas)
        ruta_db = gestor.inicializar_base_datos(incluir_datos_prueba=True)

        with closing(sqlite3.connect(ruta_db)) as conexion:
            columnas_usuarios = {
                fila[1] for fila in conexion.execute("PRAGMA table_info(usuarios);").fetchall()
            }
            version_016 = conexion.execute(
                "SELECT 1 FROM esquema_migraciones WHERE version = '016' LIMIT 1;"
            ).fetchone()
            self.assertIn("contrasena_temporal_expira_en", columnas_usuarios)
            self.assertIsNotNone(version_016)

            conexion.execute("DELETE FROM esquema_migraciones WHERE version = '016';")
            conexion.commit()

        gestor.inicializar_base_datos(incluir_datos_prueba=True)

        with closing(sqlite3.connect(ruta_db)) as conexion:
            version_016_recuperada = conexion.execute(
                "SELECT 1 FROM esquema_migraciones WHERE version = '016' LIMIT 1;"
            ).fetchone()
            columnas_usuarios = {
                fila[1] for fila in conexion.execute("PRAGMA table_info(usuarios);").fetchall()
            }

        self.assertIn("contrasena_temporal_expira_en", columnas_usuarios)
        self.assertIsNotNone(version_016_recuperada)

    def test_migracion_027_elimina_parametros_de_laboratorio_visual(self) -> None:
        ruta_migraciones_origen = RAIZ_PROYECTO / "database" / "migrations"
        for ruta in ruta_migraciones_origen.glob("*.sql"):
            destino = self.raiz_temporal / "database" / "migrations" / ruta.name
            destino.write_text(ruta.read_text(encoding="utf-8"), encoding="utf-8")

        gestor_rutas = GestorRutas(raiz_proyecto=self.raiz_temporal)
        gestor = GestorBaseDatos(gestor_rutas)
        ruta_db = gestor.inicializar_base_datos(incluir_datos_prueba=True)

        with closing(sqlite3.connect(ruta_db)) as conexion:
            parametros = conexion.execute(
                "SELECT COUNT(*) FROM configuracion_sistema WHERE clave LIKE 'ui.laboratorio.%';"
            ).fetchone()[0]
            version = conexion.execute(
                "SELECT 1 FROM esquema_migraciones WHERE version = '027' LIMIT 1;"
            ).fetchone()

        self.assertEqual(parametros, 0)
        self.assertIsNotNone(version)


if __name__ == "__main__":
    unittest.main()


