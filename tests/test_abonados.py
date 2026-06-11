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
from tests.utilidades_base_datos import inicializar_base_datos_prueba  # noqa: E402
from modulos.abonados.entidades import (  # noqa: E402
    FILTRO_ABONADOS_CON_MORA,
    FILTRO_ABONADOS_CON_PLAN,
    FILTRO_ABONADOS_SIN_MORA,
)
from modulos.abonados.repositorio import RepositorioAbonadosSQLite  # noqa: E402
from modulos.abonados.servicio import ServicioAbonados  # noqa: E402
from modulos.casas.repositorio import RepositorioCasasSQLite  # noqa: E402


class TestAbonados(unittest.TestCase):
    def setUp(self) -> None:
        self.raiz_temporal = RAIZ_PROYECTO / "tests" / f"_tmp_abonados_{uuid.uuid4().hex}"
        (self.raiz_temporal / "database" / "migrations").mkdir(parents=True, exist_ok=True)

        for ruta_migracion in (RAIZ_PROYECTO / "database" / "migrations").glob("*.sql"):
            (self.raiz_temporal / "database" / "migrations" / ruta_migracion.name).write_text(
                ruta_migracion.read_text(encoding="utf-8"),
                encoding="utf-8",
            )

        self.gestor_rutas = GestorRutas(raiz_proyecto=self.raiz_temporal)
        self.gestor_base_datos = GestorBaseDatos(self.gestor_rutas)
        inicializar_base_datos_prueba(self.gestor_base_datos)
        self.repositorio_casas = RepositorioCasasSQLite(self.gestor_base_datos)
        self.repositorio = RepositorioAbonadosSQLite(self.gestor_base_datos)
        self.servicio = ServicioAbonados(self.repositorio, self.repositorio_casas)

    def tearDown(self) -> None:
        if self.raiz_temporal.exists():
            shutil.rmtree(self.raiz_temporal, ignore_errors=True)

    def test_resumen_y_listado_inicial_reflejan_semilla(self) -> None:
        resumen = self.servicio.obtener_resumen()
        pagina = self.servicio.listar()

        self.assertEqual(resumen.total_abonados, 4)
        self.assertEqual(resumen.abonados_activos, 4)
        self.assertEqual(resumen.abonados_con_deuda, 2)
        self.assertEqual(resumen.abonados_morosos, 1)
        self.assertEqual(pagina.total_registros, 4)
        self.assertEqual(len(pagina.items), 4)
        self.assertEqual(pagina.items[0].dni, "0801199000011")
        self.assertEqual(pagina.items[1].meses_en_mora, 1)

    def test_filtros_rapidos_distinguen_mora_y_plan(self) -> None:
        pagina_con_mora = self.servicio.listar(filtro_rapido=FILTRO_ABONADOS_CON_MORA)
        pagina_sin_mora = self.servicio.listar(filtro_rapido=FILTRO_ABONADOS_SIN_MORA)
        pagina_con_plan = self.servicio.listar(filtro_rapido=FILTRO_ABONADOS_CON_PLAN)

        self.assertEqual(pagina_con_mora.total_registros, 1)
        self.assertEqual(pagina_con_mora.items[0].nombre_completo, "Carlos Ramirez")
        self.assertEqual(pagina_sin_mora.total_registros, 3)
        self.assertEqual(pagina_con_plan.total_registros, 1)
        self.assertEqual(pagina_con_plan.items[0].nombre_completo, "Carlos Ramirez")

    def test_inactivar_abonado_suspenda_casas_asociadas(self) -> None:
        carlos = next(item for item in self.servicio.listar().items if item.nombre_completo == "Carlos Ramirez")

        resultado = self.servicio.cambiar_estado(carlos.identificador or 0, carlos.estado, actor_id=1)

        self.assertTrue(resultado.exito)
        casa_carlos = next(
            item for item in self.repositorio_casas.listar() if item.abonado_dni == "0801199000022"
        )
        self.assertEqual(casa_carlos.estado_servicio, "ACTIVO")
        self.assertEqual(casa_carlos.estado_administrativo, "SUSPENDIDA")
        self.assertEqual(casa_carlos.motivo_estado_administrativo, "ABONADO_INACTIVO")
        self.assertIn("pasaron a estado suspendido", resultado.mensaje.lower())

    def test_reactivar_abonado_restaura_casas_suspendidas_por_esa_causa(self) -> None:
        carlos = next(item for item in self.servicio.listar().items if item.nombre_completo == "Carlos Ramirez")

        self.servicio.cambiar_estado(carlos.identificador or 0, carlos.estado, actor_id=1)
        resultado = self.servicio.cambiar_estado(carlos.identificador or 0, "INACTIVO", actor_id=1)

        self.assertTrue(resultado.exito)
        casa_carlos = next(
            item for item in self.repositorio_casas.listar() if item.abonado_dni == "0801199000022"
        )
        self.assertEqual(casa_carlos.estado_servicio, "ACTIVO")
        self.assertEqual(casa_carlos.estado_administrativo, "OPERATIVA")
        self.assertEqual(casa_carlos.motivo_estado_administrativo, "NINGUNO")
        self.assertIn("volvieron a operativa", resultado.mensaje.lower())

    def test_guardar_nuevo_abonado_y_exportar_csv(self) -> None:
        barrios = self.servicio.listar_barrios_disponibles()
        self.assertTrue(barrios)

        resultado_guardado = self.servicio.guardar(
            identificador=None,
            dni="0801199000099",
            nombre_completo="Fabian Aguilar",
            telefono="9999-1099",
            barrio_id=barrios[0].identificador,
            direccion_referencia="Casa nueva frente a la pulperia",
            observaciones="Registro de prueba para modulo abonados.",
            estado="ACTIVO",
        )
        self.assertTrue(resultado_guardado.exito)

        pagina = self.servicio.listar(filtro="Fabian")
        self.assertEqual(pagina.total_registros, 1)
        self.assertEqual(pagina.items[0].barrio_nombre, barrios[0].nombre)

        ruta_exportacion = self.raiz_temporal / "abonados.csv"
        resultado_exportacion = self.servicio.exportar_csv(str(ruta_exportacion))

        self.assertTrue(resultado_exportacion.exito)
        self.assertTrue(ruta_exportacion.exists())

        with ruta_exportacion.open("r", encoding="utf-8", newline="") as archivo_csv:
            filas = list(csv.reader(archivo_csv))

        self.assertEqual(
            filas[0],
            [
                "DNI",
                "Abonado",
                "Telefono",
                "Barrio",
                "Casas",
                "Meses en mora",
                "Estado",
                "Creado",
                "Ultima actualizacion",
                "Tiene plan activo",
                "Deuda pendiente",
            ],
        )
        self.assertEqual(filas[-1][0], "0801199000099")
        self.assertEqual(filas[-1][1], "Fabian Aguilar")
        self.assertTrue(filas[-1][7])


if __name__ == "__main__":
    unittest.main()

