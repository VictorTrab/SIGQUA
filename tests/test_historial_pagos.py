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

from PySide6.QtWidgets import QApplication  # noqa: E402
from PySide6.QtWidgets import QPushButton  # noqa: E402

from comun.base_datos import GestorBaseDatos  # noqa: E402
from comun.configuracion.gestor_rutas import GestorRutas  # noqa: E402
import modulos.historial_pagos.controlador as controlador_historial_modulo  # noqa: E402
from modulos.historial_pagos.controlador import ControladorHistorialPagos  # noqa: E402
from modulos.historial_pagos.repositorio import RepositorioHistorialPagosSQLite  # noqa: E402
from modulos.historial_pagos.servicio import ServicioHistorialPagos  # noqa: E402
from modulos.historial_pagos.vista import VistaHistorialPagos  # noqa: E402
from modulos.pagos.entidades import FormularioPago  # noqa: E402
from modulos.pagos.repositorio import RepositorioPagosSQLite  # noqa: E402
from modulos.pagos.servicio import ServicioPagos  # noqa: E402


class TestHistorialPagos(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.aplicacion = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.raiz_temporal = RAIZ_PROYECTO / "tests" / f"_tmp_historial_{uuid.uuid4().hex}"
        (self.raiz_temporal / "database" / "migrations").mkdir(parents=True, exist_ok=True)
        for ruta in (RAIZ_PROYECTO / "database" / "migrations").glob("*.sql"):
            (self.raiz_temporal / "database" / "migrations" / ruta.name).write_text(
                ruta.read_text(encoding="utf-8"),
                encoding="utf-8",
            )
        self.gestor_rutas = GestorRutas(raiz_proyecto=self.raiz_temporal)
        self.gestor_base_datos = GestorBaseDatos(self.gestor_rutas)
        self.ruta_db = self.gestor_base_datos.inicializar_base_datos(incluir_datos_prueba=True)
        self.repositorio_pagos = RepositorioPagosSQLite(self.gestor_base_datos)
        self.servicio_pagos = ServicioPagos(self.repositorio_pagos, gestor_rutas=self.gestor_rutas)
        self.repositorio_historial = RepositorioHistorialPagosSQLite(self.gestor_base_datos)
        self.servicio_historial = ServicioHistorialPagos(
            self.repositorio_historial,
            gestor_rutas=self.gestor_rutas,
        )
        self._crear_pago_historial("0801199000022", "EFECTIVO")
        self._crear_pago_historial("0801199000022", "TRANSFERENCIA", referencia="TRX-9001")

    def tearDown(self) -> None:
        shutil.rmtree(self.raiz_temporal, ignore_errors=True)

    def test_listado_y_resumen_cargan_pagos_confirmados_reales(self) -> None:
        resumen = self.servicio_historial.obtener_resumen()
        pagina = self.servicio_historial.listar()

        self.assertGreaterEqual(resumen.total_pagos, 2)
        self.assertGreaterEqual(len(pagina.items), 2)
        self.assertTrue(all(item.numero_comprobante.startswith("REC-") for item in pagina.items))
        self.assertGreaterEqual(pagina.total_paginas, 1)

    def test_busqueda_libre_filtra_por_comprobante_y_abonado(self) -> None:
        pagina_base = self.servicio_historial.listar()
        self.assertGreaterEqual(len(pagina_base.items), 1)
        primer_item = pagina_base.items[0]

        filtros_comprobante = self.servicio_historial.filtro_inicial()
        filtros_comprobante.texto = primer_item.numero_comprobante
        pagina_comprobante = self.servicio_historial.listar(filtros_comprobante)

        filtros_abonado = self.servicio_historial.filtro_inicial()
        filtros_abonado.texto = primer_item.abonado_nombre.split()[0]
        pagina_abonado = self.servicio_historial.listar(filtros_abonado)

        self.assertGreaterEqual(len(pagina_comprobante.items), 1)
        self.assertTrue(
            all(item.numero_comprobante == primer_item.numero_comprobante for item in pagina_comprobante.items)
        )
        self.assertGreaterEqual(len(pagina_abonado.items), 1)
        self.assertTrue(any(item.pago_id == primer_item.pago_id for item in pagina_abonado.items))

    def test_filtros_por_tipo_y_metodo_no_mezclan_resultados(self) -> None:
        filtros = self.servicio_historial.filtro_inicial()
        filtros.tipo_pago = "MENSUALIDAD"
        filtros.metodo_pago = "TRANSFERENCIA"

        pagina = self.servicio_historial.listar(filtros)

        self.assertGreaterEqual(len(pagina.items), 1)
        self.assertTrue(all(item.tipo_pago == "MENSUALIDAD" for item in pagina.items))
        self.assertTrue(all(item.metodo_pago_codigo == "TRANSFERENCIA" for item in pagina.items))

    def test_rango_de_fechas_invalido_se_rechaza(self) -> None:
        filtros = self.servicio_historial.filtro_inicial()
        filtros.fecha_desde = "2026-12-31"
        filtros.fecha_hasta = "2026-01-01"

        with self.assertRaises(ValueError):
            self.servicio_historial.listar(filtros)

    def test_detalle_expone_lineas_reales_de_pagos_detalle(self) -> None:
        pagina = self.servicio_historial.listar()
        detalle = self.servicio_historial.obtener_detalle(pagina.items[0].pago_id)

        self.assertIsNotNone(detalle)
        assert detalle is not None
        self.assertGreaterEqual(len(detalle.lineas_detalle), 1)
        self.assertTrue(all(linea.descripcion for linea in detalle.lineas_detalle))

    def test_reimpresion_regenera_pdf_sin_actualizar_metadata(self) -> None:
        pagina = self.servicio_historial.listar()
        pago_id = pagina.items[0].pago_id

        with closing(sqlite3.connect(self.ruta_db)) as conexion:
            fila_antes = conexion.execute(
                """
                SELECT COALESCE(ruta_archivo, ''), COALESCE(formato_salida, '')
                FROM comprobantes
                WHERE pago_id = ?;
                """,
                (pago_id,),
            ).fetchone()

        resultado = self.servicio_historial.reimprimir_copia(pago_id)

        self.assertTrue(resultado.exito, resultado.mensaje)
        self.assertTrue(Path(resultado.ruta_documento).exists())
        self.assertTrue(Path(resultado.ruta_documento).read_bytes().startswith(b"%PDF"))

        with closing(sqlite3.connect(self.ruta_db)) as conexion:
            fila_despues = conexion.execute(
                """
                SELECT COALESCE(ruta_archivo, ''), COALESCE(formato_salida, '')
                FROM comprobantes
                WHERE pago_id = ?;
                """,
                (pago_id,),
            ).fetchone()

        self.assertEqual(fila_antes, fila_despues)

    def test_vista_historial_instancia_en_offscreen(self) -> None:
        vista = VistaHistorialPagos()

        self.assertEqual(vista.objectName(), "vistaHistorialPagos")
        self.assertEqual(vista._tabla.viewport().objectName(), "viewportTablaHistorialPagos")
        self.assertEqual(vista._combo_metodo.count(), 5)
        self.assertEqual(
            vista._tabla.selectionBehavior(),
            vista._tabla.SelectionBehavior.SelectRows,
        )
        self.assertNotIn(
            "Actualizar",
            [boton.text() for boton in vista.findChildren(QPushButton)],
        )
        vista.aplicar_tema("claro")
        self.assertEqual(vista._tema_actual, "claro")
        self.assertIn('font-family: "Segoe UI"', vista.styleSheet())
        vista.close()

    def test_controlador_reimprime_y_aplica_politica_documental(self) -> None:
        vista = VistaHistorialPagos()
        controlador = ControladorHistorialPagos(self.servicio_historial, vista)
        pagina = self.servicio_historial.listar()
        pago_id = pagina.items[0].pago_id
        mensajes: list[str] = []
        vista.mostrar_mensaje = lambda mensaje, es_error=False: mensajes.append(mensaje)  # type: ignore[method-assign]
        helper_original = controlador_historial_modulo.ejecutar_acciones_documento_pdf
        controlador_historial_modulo.ejecutar_acciones_documento_pdf = (  # type: ignore[assignment]
            lambda ruta, **_kwargs: f"Documento abierto automaticamente desde {ruta}"
        )

        try:
            controlador._reimprimir_copia(pago_id)
        finally:
            controlador_historial_modulo.ejecutar_acciones_documento_pdf = helper_original  # type: ignore[assignment]

        self.assertTrue(mensajes)
        self.assertIn("abierto automaticamente", mensajes[-1].lower())
        vista.close()

    def _crear_pago_historial(self, dni: str, metodo_codigo: str, referencia: str = "") -> None:
        casa_id = self._obtener_casa_por_dni(dni)
        metodo_id = self._obtener_metodo(metodo_codigo)
        formulario = FormularioPago(
            casa_id=casa_id,
            tipo_pago="MENSUALIDAD",
            cantidad_meses=1,
            metodo_pago_id=metodo_id,
            referencia=referencia,
        )
        resultado = self.servicio_pagos.registrar_pago(formulario, actor_id=1)
        self.assertTrue(resultado.exito, resultado.mensaje)

    def _obtener_casa_por_dni(self, dni: str) -> int:
        with closing(sqlite3.connect(self.ruta_db)) as conexion:
            fila = conexion.execute(
                """
                SELECT c.id
                FROM casas c
                INNER JOIN abonados a ON a.id = c.abonado_id
                WHERE a.dni = ?
                LIMIT 1;
                """,
                (dni,),
            ).fetchone()
        assert fila is not None
        return int(fila[0])

    def _obtener_metodo(self, codigo: str) -> int:
        with closing(sqlite3.connect(self.ruta_db)) as conexion:
            fila = conexion.execute(
                "SELECT id FROM metodos_pago WHERE codigo = ? LIMIT 1;",
                (codigo,),
            ).fetchone()
        assert fila is not None
        return int(fila[0])


if __name__ == "__main__":
    unittest.main()

