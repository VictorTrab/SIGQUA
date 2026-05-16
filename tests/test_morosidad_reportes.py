from __future__ import annotations

import os
import shutil
import sys
import unittest
import uuid
from pathlib import Path


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

RAIZ_PROYECTO = Path(__file__).resolve().parents[1]
RUTA_SRC = RAIZ_PROYECTO / "src"

if str(RUTA_SRC) not in sys.path:
    sys.path.insert(0, str(RUTA_SRC))

from PySide6.QtWidgets import QApplication  # noqa: E402

from comun.base_datos import GestorBaseDatos  # noqa: E402
from comun.configuracion.gestor_rutas import GestorRutas  # noqa: E402
from modulos.morosidad.repositorio import RepositorioMorosidadSQLite  # noqa: E402
from modulos.morosidad.servicio import ServicioMorosidad  # noqa: E402
from modulos.morosidad.vista import VistaMorosidad  # noqa: E402
from modulos.reportes.repositorio import RepositorioReportesSQLite  # noqa: E402
from modulos.reportes.servicio import ServicioReportes  # noqa: E402
from modulos.reportes.vista import VistaReportes  # noqa: E402


class TestMorosidadReportes(unittest.TestCase):
    def setUp(self) -> None:
        self.raiz_temporal = RAIZ_PROYECTO / "tests" / f"_tmp_mr_{uuid.uuid4().hex}"
        (self.raiz_temporal / "database" / "migrations").mkdir(parents=True, exist_ok=True)
        for ruta in (RAIZ_PROYECTO / "database" / "migrations").glob("*.sql"):
            (self.raiz_temporal / "database" / "migrations" / ruta.name).write_text(
                ruta.read_text(encoding="utf-8"),
                encoding="utf-8",
            )
        self.gestor_rutas = GestorRutas(raiz_proyecto=self.raiz_temporal)
        self.gestor_base_datos = GestorBaseDatos(self.gestor_rutas)
        self.gestor_base_datos.inicializar_base_datos()

    def tearDown(self) -> None:
        shutil.rmtree(self.raiz_temporal, ignore_errors=True)

    def test_morosidad_lista_casas_activas_con_deuda_vencida(self) -> None:
        servicio = ServicioMorosidad(RepositorioMorosidadSQLite(self.gestor_base_datos))

        estado = servicio.obtener_estado()

        self.assertGreaterEqual(estado.resumen.total_casas, 1)
        self.assertGreaterEqual(estado.resumen.deuda_total_centavos, estado.resumen.deuda_base_centavos)
        self.assertTrue(all(fila.estado_servicio == "ACTIVO" for fila in estado.filas))
        self.assertTrue(all(fila.deuda_total_centavos > 0 for fila in estado.filas))

    def test_reportes_basicos_exponen_tablas_obligatorias(self) -> None:
        servicio = ServicioReportes(RepositorioReportesSQLite(self.gestor_base_datos))

        estado = servicio.obtener_estado(fecha_desde="2026-01-01", fecha_hasta="2026-12-31")
        codigos = {tabla.codigo for tabla in estado.tablas}

        self.assertEqual(len(estado.indicadores), 5)
        self.assertIn("abonados_estado", codigos)
        self.assertIn("casas_estado", codigos)
        self.assertIn("deuda_activa", codigos)
        self.assertIn("historial_pagos", codigos)
        self.assertIn("ingresos_diarios", codigos)

    def test_vistas_instancian_en_offscreen(self) -> None:
        _app = QApplication.instance() or QApplication([])

        vista_morosidad = VistaMorosidad()
        vista_reportes = VistaReportes()

        self.assertEqual(vista_morosidad.objectName(), "vistaMorosidad")
        self.assertEqual(vista_reportes.objectName(), "vistaReportes")


if __name__ == "__main__":
    unittest.main()
