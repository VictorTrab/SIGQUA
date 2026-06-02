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
import modulos.reportes.entidades as entidades_reportes  # noqa: E402
from modulos.reportes.entidades import (  # noqa: E402
    REPORTE_DEUDA_ABONADOS_ESTADO,
    REPORTE_HISTORIAL_ABONADO_CASA,
    REPORTE_INGRESOS_MENSUALES_DIARIOS,
    REPORTE_SERVICIO_CASAS,
)
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

    def test_catalogo_final_expone_solo_cuatro_reportes(self) -> None:
        estado = self.servicio.obtener_estado()

        codigos = tuple(tarjeta.codigo for tarjeta in estado.catalogo)

        self.assertEqual(
            codigos,
            (
                REPORTE_DEUDA_ABONADOS_ESTADO,
                REPORTE_SERVICIO_CASAS,
                REPORTE_INGRESOS_MENSUALES_DIARIOS,
                REPORTE_HISTORIAL_ABONADO_CASA,
            ),
        )
        self.assertEqual(len(estado.indicadores), 5)
        self.assertIsNotNone(estado.tabla_actual)
        assert estado.tabla_actual is not None
        self.assertEqual(estado.reporte_actual, REPORTE_DEUDA_ABONADOS_ESTADO)

    def test_constantes_obsoletas_no_existen_en_contrato_activo(self) -> None:
        constantes_retiradas = (
            "REPORTE_DEUDA_POR_CASA",
            "REPORTE_FORMATO_FISICO_ABONADOS",
            "REPORTE_ABONADOS_SIN_DEUDA",
            "REPORTE_INGRESOS_MENSUALES",
            "REPORTE_INGRESOS_DIARIOS",
            "REPORTE_HISTORIAL_ABONADO",
            "REPORTE_HISTORIAL_CASA",
            "REPORTE_PLANES_ACTIVOS",
            "REPORTE_DEUDA_MENSUAL",
            "REPORTE_CASAS_CORTADAS",
            "REPORTE_CASAS_SUSPENDIDAS_INACTIVAS",
            "REPORTE_NUEVOS_ABONADOS",
            "REPORTE_PAGOS_POR_USUARIO",
        )

        for nombre in constantes_retiradas:
            self.assertFalse(hasattr(entidades_reportes, nombre), nombre)

    def test_cada_reporte_activo_genera_preview(self) -> None:
        filtros_fecha = {"fecha_desde": "2026-01-01", "fecha_hasta": "2026-12-31"}
        escenarios = (
            (REPORTE_DEUDA_ABONADOS_ESTADO, {"estado_abonado": "TODOS", "incluir_mora": "1"}),
            (REPORTE_SERVICIO_CASAS, {"estado_servicio": "TODOS"}),
            (REPORTE_INGRESOS_MENSUALES_DIARIOS, filtros_fecha),
            (REPORTE_HISTORIAL_ABONADO_CASA, filtros_fecha),
        )

        for codigo, filtros in escenarios:
            with self.subTest(codigo=codigo):
                estado = self.servicio.obtener_estado(codigo_reporte=codigo, filtros=filtros)

                self.assertIsNotNone(estado.tabla_actual)
                assert estado.tabla_actual is not None
                self.assertEqual(estado.tabla_actual.codigo, codigo)
                self.assertGreater(len(estado.tabla_actual.columnas), 0)

    def test_reportes_fusionados_tienen_columnas_esperadas(self) -> None:
        ingresos = self.servicio.obtener_estado(
            codigo_reporte=REPORTE_INGRESOS_MENSUALES_DIARIOS,
            filtros={"fecha_desde": "2026-01-01", "fecha_hasta": "2026-12-31"},
        )
        historial = self.servicio.obtener_estado(
            codigo_reporte=REPORTE_HISTORIAL_ABONADO_CASA,
            filtros={"fecha_desde": "2026-01-01", "fecha_hasta": "2026-12-31"},
        )

        assert ingresos.tabla_actual is not None
        assert historial.tabla_actual is not None
        self.assertEqual(ingresos.tabla_actual.columnas, ("Mes", "Dia/Fecha", "Pagos", "Ingresos"))
        self.assertEqual(
            historial.tabla_actual.columnas,
            ("Recibo", "Abonado", "Casa", "Metodo", "Usuario", "Total", "Fecha"),
        )

    def test_filtros_visibles_son_minimos_por_reporte(self) -> None:
        casos = {
            REPORTE_DEUDA_ABONADOS_ESTADO: ("estado_abonado", "barrio", "estado_servicio", "incluir_mora"),
            REPORTE_SERVICIO_CASAS: ("estado_abonado", "barrio", "estado_servicio"),
            REPORTE_INGRESOS_MENSUALES_DIARIOS: ("fecha_desde", "fecha_hasta"),
            REPORTE_HISTORIAL_ABONADO_CASA: ("fecha_desde", "fecha_hasta", "abonado_id", "casa_id"),
        }

        for codigo, claves_esperadas in casos.items():
            with self.subTest(codigo=codigo):
                estado = self.servicio.obtener_estado(codigo_reporte=codigo)
                claves = tuple(filtro.clave for filtro in estado.filtros_visibles)

                self.assertEqual(claves, claves_esperadas)


if __name__ == "__main__":
    unittest.main()
