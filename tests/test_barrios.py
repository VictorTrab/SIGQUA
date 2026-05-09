from __future__ import annotations

import csv
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
from modulos.barrios.entidades import (  # noqa: E402
    FILTRO_BARRIOS_ACTIVOS,
    FILTRO_BARRIOS_CON_ABONADOS,
    FILTRO_BARRIOS_INACTIVOS,
    FILTRO_BARRIOS_SIN_ABONADOS,
)
from modulos.barrios.repositorio import RepositorioBarriosSQLite  # noqa: E402
from modulos.barrios.servicio import ServicioBarrios  # noqa: E402


class TestBarrios(unittest.TestCase):
    def setUp(self) -> None:
        self.raiz_temporal = RAIZ_PROYECTO / "tests" / f"_tmp_barrios_{uuid.uuid4().hex}"
        (self.raiz_temporal / "database" / "migrations").mkdir(parents=True, exist_ok=True)

        for ruta_migracion in (RAIZ_PROYECTO / "database" / "migrations").glob("*.sql"):
            (self.raiz_temporal / "database" / "migrations" / ruta_migracion.name).write_text(
                ruta_migracion.read_text(encoding="utf-8"),
                encoding="utf-8",
            )

        self.gestor_rutas = GestorRutas(raiz_proyecto=self.raiz_temporal)
        self.gestor_base_datos = GestorBaseDatos(self.gestor_rutas)
        self.gestor_base_datos.inicializar_base_datos()
        self.repositorio = RepositorioBarriosSQLite(self.gestor_base_datos)
        self.servicio = ServicioBarrios(self.repositorio)

    def tearDown(self) -> None:
        if self.raiz_temporal.exists():
            shutil.rmtree(self.raiz_temporal, ignore_errors=True)

    def test_resumen_y_listado_inicial_reflejan_semilla(self) -> None:
        resumen = self.servicio.obtener_resumen()
        pagina = self.servicio.listar()

        self.assertEqual(resumen.total_barrios, 3)
        self.assertEqual(resumen.barrios_activos, 3)
        self.assertEqual(resumen.barrios_con_abonados, 3)
        self.assertEqual(resumen.barrio_con_mas_abonados, "Centro")
        self.assertEqual(resumen.cantidad_maxima_abonados, 2)
        self.assertEqual(pagina.total_registros, 3)
        self.assertEqual(len(pagina.items), 3)
        self.assertEqual(pagina.items[0].codigo, "BR-001")
        self.assertEqual(pagina.items[0].total_abonados, 2)

    def test_filtros_rapidos_distinguen_barrios_con_y_sin_abonados(self) -> None:
        creacion = self.servicio.guardar(
            identificador=None,
            nombre="Nuevo Sector",
            estado="ACTIVO",
            observaciones="Sin abonados aun.",
        )
        self.assertTrue(creacion.exito)

        pagina_con_abonados = self.servicio.listar(filtro_rapido=FILTRO_BARRIOS_CON_ABONADOS)
        pagina_sin_abonados = self.servicio.listar(filtro_rapido=FILTRO_BARRIOS_SIN_ABONADOS)

        self.assertEqual(pagina_con_abonados.total_registros, 3)
        self.assertEqual(pagina_sin_abonados.total_registros, 1)
        self.assertEqual(pagina_sin_abonados.items[0].nombre, "Nuevo Sector")

    def test_filtros_rapidos_distinguen_barrios_activos_e_inactivos(self) -> None:
        creacion = self.servicio.guardar(
            identificador=None,
            nombre="Sector Suspendido",
            estado="INACTIVO",
            observaciones="Barrio para validar filtro de estado.",
        )
        self.assertTrue(creacion.exito)

        pagina_activos = self.servicio.listar(filtro_rapido=FILTRO_BARRIOS_ACTIVOS)
        pagina_inactivos = self.servicio.listar(filtro_rapido=FILTRO_BARRIOS_INACTIVOS)

        self.assertEqual(pagina_activos.total_registros, 3)
        self.assertTrue(all(barrio.estado == "ACTIVO" for barrio in pagina_activos.items))
        self.assertEqual(pagina_inactivos.total_registros, 1)
        self.assertEqual(pagina_inactivos.items[0].nombre, "Sector Suspendido")
        self.assertEqual(pagina_inactivos.items[0].estado, "INACTIVO")

    def test_exportacion_csv_genera_columnas_operativas(self) -> None:
        ruta_exportacion = self.raiz_temporal / "barrios.csv"

        resultado = self.servicio.exportar_csv(str(ruta_exportacion))

        self.assertTrue(resultado.exito)
        self.assertTrue(ruta_exportacion.exists())

        with ruta_exportacion.open("r", encoding="utf-8", newline="") as archivo_csv:
            filas = list(csv.reader(archivo_csv))

        self.assertEqual(
            filas[0],
            [
                "Codigo",
                "Barrio",
                "Abonados",
                "Casas",
                "Estado",
                "Ultima actualizacion",
                "Observaciones",
            ],
        )
        self.assertEqual(filas[1][0], "BR-001")
        self.assertEqual(filas[1][1], "Centro")


if __name__ == "__main__":
    unittest.main()
