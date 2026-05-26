from __future__ import annotations

import shutil
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
from modulos.reportes.entidades import REPORTE_INGRESOS_DIARIOS, REPORTE_PLANES_ACTIVOS  # noqa: E402
from modulos.reportes.repositorio import RepositorioReportesSQLite  # noqa: E402
from modulos.reportes.servicio import ServicioReportes  # noqa: E402


class TestReportes(unittest.TestCase):
    def setUp(self) -> None:
        self.raiz_temporal = RAIZ_PROYECTO / "tests" / f"_tmp_reportes_{uuid.uuid4().hex}"
        (self.raiz_temporal / "database" / "migrations").mkdir(parents=True, exist_ok=True)
        for ruta in (RAIZ_PROYECTO / "database" / "migrations").glob("*.sql"):
            (self.raiz_temporal / "database" / "migrations" / ruta.name).write_text(
                ruta.read_text(encoding="utf-8"),
                encoding="utf-8",
            )
        self.gestor_rutas = GestorRutas(raiz_proyecto=self.raiz_temporal)
        self.gestor_base_datos = GestorBaseDatos(self.gestor_rutas)
        self.gestor_base_datos.inicializar_base_datos(incluir_datos_prueba=True)
        self.servicio = ServicioReportes(RepositorioReportesSQLite(self.gestor_base_datos))

    def tearDown(self) -> None:
        shutil.rmtree(self.raiz_temporal, ignore_errors=True)

    def test_estado_admin_devuelve_catalogo_filtros_y_preview(self) -> None:
        estado = self.servicio.obtener_estado()

        self.assertEqual(len(estado.catalogo), 8)
        self.assertEqual(len(estado.indicadores), 5)
        self.assertIsNotNone(estado.tabla_actual)
        assert estado.tabla_actual is not None
        self.assertEqual(estado.reporte_actual, estado.catalogo[0].codigo)
        self.assertGreater(len(estado.filtros_visibles), 0)

    def test_ingresos_diarios_y_planes_activos_generan_preview(self) -> None:
        ingresos = self.servicio.obtener_estado(
            codigo_reporte=REPORTE_INGRESOS_DIARIOS,
            filtros={"fecha_desde": "2026-01-01", "fecha_hasta": "2026-12-31"},
        )
        planes = self.servicio.obtener_estado(codigo_reporte=REPORTE_PLANES_ACTIVOS)

        self.assertIsNotNone(ingresos.tabla_actual)
        self.assertIsNotNone(planes.tabla_actual)
        assert ingresos.tabla_actual is not None
        assert planes.tabla_actual is not None
        self.assertEqual(ingresos.tabla_actual.codigo, REPORTE_INGRESOS_DIARIOS)
        self.assertEqual(planes.tabla_actual.codigo, REPORTE_PLANES_ACTIVOS)
        self.assertGreaterEqual(len(planes.tabla_actual.filas), 1)


if __name__ == "__main__":
    unittest.main()
