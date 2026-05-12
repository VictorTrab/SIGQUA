from __future__ import annotations

import shutil
import sqlite3
import sys
import unittest
import uuid
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
        ruta_db = gestor.inicializar_base_datos()

        with sqlite3.connect(ruta_db) as conexion:
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

        gestor.inicializar_base_datos()

        with sqlite3.connect(ruta_db) as conexion:
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
                    actualizado_en = datetime('now')
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


if __name__ == "__main__":
    unittest.main()
