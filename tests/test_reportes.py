from __future__ import annotations

import os
import shutil
import sqlite3
import sys
import unittest
import uuid
from contextlib import closing
from pathlib import Path


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

RAIZ_PROYECTO = Path(__file__).resolve().parents[1]
RUTA_SRC = RAIZ_PROYECTO / "src"

if str(RUTA_SRC) not in sys.path:
    sys.path.insert(0, str(RUTA_SRC))

from comun.base_datos import GestorBaseDatos  # noqa: E402
from comun.configuracion.gestor_rutas import GestorRutas  # noqa: E402
from comun.ui import CampoBusquedaSeleccionSigqua  # noqa: E402
import modulos.reportes.entidades as entidades_reportes  # noqa: E402
from modulos.reportes.entidades import (  # noqa: E402
    ORIENTACION_HORIZONTAL,
    ORIENTACION_VERTICAL,
    REPORTE_DEUDA_ABONADOS_ESTADO,
    REPORTE_INGRESOS_MENSUALES_DIARIOS,
    REPORTE_SERVICIO_CASAS,
    TIPO_FILTRO_BUSQUEDA,
)
from modulos.reportes.repositorio import RepositorioReportesSQLite  # noqa: E402
from modulos.reportes.servicio import ServicioReportes  # noqa: E402
from modulos.reportes.vista import TarjetaSeleccionReporte, VistaReportes  # noqa: E402
from PySide6.QtWidgets import QApplication, QComboBox  # noqa: E402


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

    def test_catalogo_final_expone_solo_tres_reportes(self) -> None:
        estado = self.servicio.obtener_estado()

        codigos = tuple(tarjeta.codigo for tarjeta in estado.catalogo)

        self.assertEqual(
            codigos,
            (
                REPORTE_DEUDA_ABONADOS_ESTADO,
                REPORTE_SERVICIO_CASAS,
                REPORTE_INGRESOS_MENSUALES_DIARIOS,
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
            "REPORTE_HISTORIAL_ABONADO_CASA",
        )

        for nombre in constantes_retiradas:
            self.assertFalse(hasattr(entidades_reportes, nombre), nombre)

    def test_cada_reporte_activo_genera_preview(self) -> None:
        filtros_fecha = {"fecha_desde": "2026-01-01", "fecha_hasta": "2026-12-31"}
        escenarios = (
            (REPORTE_DEUDA_ABONADOS_ESTADO, {"estado_abonado": "TODOS", "incluir_mora": "1"}),
            (REPORTE_SERVICIO_CASAS, {"estado_servicio": "TODOS"}),
            (REPORTE_INGRESOS_MENSUALES_DIARIOS, filtros_fecha),
        )

        for codigo, filtros in escenarios:
            with self.subTest(codigo=codigo):
                estado = self.servicio.obtener_estado(codigo_reporte=codigo, filtros=filtros)

                self.assertIsNotNone(estado.tabla_actual)
                assert estado.tabla_actual is not None
                self.assertEqual(estado.tabla_actual.codigo, codigo)
                self.assertGreater(len(estado.tabla_actual.columnas), 0)
                self.assertTrue(estado.tabla_actual.resumen)

    def test_orientacion_es_adaptativa_por_reporte(self) -> None:
        for codigo in (
            REPORTE_DEUDA_ABONADOS_ESTADO,
            REPORTE_SERVICIO_CASAS,
        ):
            tabla = self.servicio.obtener_estado(codigo_reporte=codigo).tabla_actual
            assert tabla is not None
            self.assertEqual(tabla.orientacion, ORIENTACION_HORIZONTAL)

        ingresos = self.servicio.obtener_estado(
            codigo_reporte=REPORTE_INGRESOS_MENSUALES_DIARIOS
        ).tabla_actual
        assert ingresos is not None
        self.assertEqual(ingresos.orientacion, ORIENTACION_VERTICAL)

    def test_ingresos_y_servicio_tienen_columnas_esperadas(self) -> None:
        ingresos = self.servicio.obtener_estado(
            codigo_reporte=REPORTE_INGRESOS_MENSUALES_DIARIOS,
            filtros={"fecha_desde": "2026-01-01", "fecha_hasta": "2026-12-31"},
        )
        servicio = self.servicio.obtener_estado(codigo_reporte=REPORTE_SERVICIO_CASAS)

        assert ingresos.tabla_actual is not None
        assert servicio.tabla_actual is not None
        self.assertEqual(ingresos.tabla_actual.columnas, ("Mes", "Dia/Fecha", "Pagos", "Ingresos"))
        self.assertEqual(
            servicio.tabla_actual.columnas,
            (
                "Casa",
                "Abonado",
                "DNI",
                "Barrio",
                "Disponibilidad",
                "Estado fisico",
                "Estado administrativo",
                "Estado abonado",
                "Ultima actualizacion",
            ),
        )

    def test_filtros_visibles_son_minimos_por_reporte(self) -> None:
        casos = {
            REPORTE_DEUDA_ABONADOS_ESTADO: ("estado_abonado", "barrio", "incluir_mora"),
            REPORTE_SERVICIO_CASAS: (
                "estado_abonado",
                "barrio",
                "disponibilidad",
                "estado_servicio",
                "estado_administrativo",
            ),
            REPORTE_INGRESOS_MENSUALES_DIARIOS: ("fecha_desde", "fecha_hasta"),
        }

        for codigo, claves_esperadas in casos.items():
            with self.subTest(codigo=codigo):
                estado = self.servicio.obtener_estado(codigo_reporte=codigo)
                claves = tuple(filtro.clave for filtro in estado.filtros_visibles)

                self.assertEqual(claves, claves_esperadas)

    def test_filtros_grandes_exponen_ids_reales_para_busqueda(self) -> None:
        deuda = self.servicio.obtener_estado(
            codigo_reporte=REPORTE_DEUDA_ABONADOS_ESTADO
        )
        filtros = {
            filtro.clave: filtro
            for filtro in deuda.filtros_visibles
        }

        for clave in ("barrio",):
            with self.subTest(clave=clave):
                filtro = filtros[clave]
                self.assertEqual(filtro.tipo, TIPO_FILTRO_BUSQUEDA)
                self.assertEqual(filtro.opciones[0].valor, "TODOS")
                self.assertTrue(all(opcion.valor.isdigit() for opcion in filtro.opciones[1:]))

    def test_filtro_barrio_aplica_id_real_en_el_servicio(self) -> None:
        estado_inicial = self.servicio.obtener_estado(
            codigo_reporte=REPORTE_SERVICIO_CASAS
        )
        filtro_barrio = next(
            filtro for filtro in estado_inicial.filtros_visibles if filtro.clave == "barrio"
        )
        opcion = filtro_barrio.opciones[1]

        estado_filtrado = self.servicio.obtener_estado(
            codigo_reporte=REPORTE_SERVICIO_CASAS,
            filtros={"barrio": opcion.valor},
        )

        self.assertEqual(estado_filtrado.filtros_aplicados["barrio"], opcion.valor)
        assert estado_filtrado.tabla_actual is not None
        self.assertTrue(estado_filtrado.tabla_actual.filas)
        self.assertTrue(
            all(fila[3] == opcion.etiqueta for fila in estado_filtrado.tabla_actual.filas)
        )

    def test_deuda_filtra_estado_e_incluye_abonado_sin_casa(self) -> None:
        with closing(sqlite3.connect(self.gestor_rutas.obtener_ruta_base_datos())) as conexion:
            barrio_id = conexion.execute(
                "SELECT id FROM barrios ORDER BY id LIMIT 1;"
            ).fetchone()[0]
            conexion.execute(
                """
                INSERT INTO abonados(
                    nombre_completo, dni, telefono, barrio_id, direccion_referencia, estado
                )
                VALUES ('Abonado Sin Casa', '0801199911111', '', ?, '', 'INACTIVO');
                """,
                (barrio_id,),
            )
            conexion.commit()

        estado = self.servicio.obtener_estado(
            codigo_reporte=REPORTE_DEUDA_ABONADOS_ESTADO,
            filtros={"estado_abonado": "INACTIVO"},
        )

        assert estado.tabla_actual is not None
        self.assertTrue(estado.tabla_actual.filas)
        self.assertTrue(all(fila[6] == "INACTIVO" for fila in estado.tabla_actual.filas))
        fila_sin_casa = next(
            fila for fila in estado.tabla_actual.filas if fila[1] == "Abonado Sin Casa"
        )
        self.assertEqual(fila_sin_casa[3], "0")
        self.assertEqual(fila_sin_casa[5], "L 0.00")

    def test_servicio_resume_dimensiones_y_filtra_disponibilidad(self) -> None:
        estado = self.servicio.obtener_estado(codigo_reporte=REPORTE_SERVICIO_CASAS)
        assert estado.tabla_actual is not None
        resumen = dict(estado.tabla_actual.resumen)

        self.assertEqual(
            tuple(resumen),
            (
                "Casas listadas",
                "Con servicio",
                "Sin servicio",
                "Activas",
                "Cortadas",
                "Inactivas",
                "Operativas",
                "Suspendidas",
                "Abonados activos",
                "Abonados inactivos",
            ),
        )
        self.assertEqual(
            int(resumen["Con servicio"]) + int(resumen["Sin servicio"]),
            int(resumen["Casas listadas"]),
        )

        sin_servicio = self.servicio.obtener_estado(
            codigo_reporte=REPORTE_SERVICIO_CASAS,
            filtros={"disponibilidad": "SIN_SERVICIO"},
        )
        assert sin_servicio.tabla_actual is not None
        self.assertTrue(
            all(fila[4] == "SIN SERVICIO" for fila in sin_servicio.tabla_actual.filas)
        )

    def test_vista_captura_ids_de_busqueda_y_vacio_como_todos(self) -> None:
        _app = QApplication.instance() or QApplication([])
        estado = self.servicio.obtener_estado(
            codigo_reporte=REPORTE_SERVICIO_CASAS
        )
        vista = VistaReportes()
        vista.mostrar_estado(estado)

        campo_barrio = vista._filtros_widgets["barrio"]
        self.assertIsInstance(campo_barrio, CampoBusquedaSeleccionSigqua)
        self.assertNotIsInstance(campo_barrio, QComboBox)

        filtro_barrio = next(
            filtro for filtro in estado.filtros_visibles if filtro.clave == "barrio"
        )
        opcion = filtro_barrio.opciones[1]
        campo_barrio.seleccionar_por_id(int(opcion.valor), opcion.etiqueta)

        capturados = vista._capturar_filtros()

        self.assertEqual(capturados["barrio"], opcion.valor)
        vista.close()

        vista_barrio = VistaReportes()
        vista_barrio.mostrar_estado(
            self.servicio.obtener_estado(codigo_reporte=REPORTE_SERVICIO_CASAS)
        )
        self.assertIsInstance(
            vista_barrio._filtros_widgets["barrio"],
            CampoBusquedaSeleccionSigqua,
        )
        vista_barrio.close()

    def test_tarjetas_reportes_tienen_altura_y_estados_visuales_diferenciados(self) -> None:
        _app = QApplication.instance() or QApplication([])
        vista = VistaReportes()
        vista.mostrar_estado(self.servicio.obtener_estado())
        tarjeta = next(iter(vista._tarjetas.values()))

        self.assertEqual(tarjeta.minimumHeight(), TarjetaSeleccionReporte.ALTURA)
        self.assertGreaterEqual(TarjetaSeleccionReporte.ALTURA, 160)
        self.assertIn("QPushButton#tarjetaReporteAdmin:hover", vista.styleSheet())
        self.assertIn("QPushButton#tarjetaReporteAdmin:checked", vista.styleSheet())
        self.assertIn('border: 2px solid', vista.styleSheet())
        vista.close()


if __name__ == "__main__":
    unittest.main()
