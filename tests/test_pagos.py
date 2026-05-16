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

from comun.base_datos import GestorBaseDatos  # noqa: E402
from comun.configuracion.gestor_rutas import GestorRutas  # noqa: E402
from modulos.pagos.entidades import FormularioPago, ResumenConfirmacionPago  # noqa: E402
from modulos.pagos.controlador import ControladorPagos  # noqa: E402
from modulos.pagos.repositorio import RepositorioPagosSQLite  # noqa: E402
from modulos.pagos.servicio import ServicioPagos  # noqa: E402
from modulos.pagos.vista import VistaPagos  # noqa: E402


class TestPagos(unittest.TestCase):
    def setUp(self) -> None:
        self.raiz_temporal = RAIZ_PROYECTO / "tests" / f"_tmp_pagos_{uuid.uuid4().hex}"
        (self.raiz_temporal / "database" / "migrations").mkdir(parents=True, exist_ok=True)
        for ruta in (RAIZ_PROYECTO / "database" / "migrations").glob("*.sql"):
            (self.raiz_temporal / "database" / "migrations" / ruta.name).write_text(
                ruta.read_text(encoding="utf-8"),
                encoding="utf-8",
            )
        self.gestor_rutas = GestorRutas(raiz_proyecto=self.raiz_temporal)
        self.gestor_base_datos = GestorBaseDatos(self.gestor_rutas)
        self.ruta_db = self.gestor_base_datos.inicializar_base_datos()
        self.repositorio = RepositorioPagosSQLite(self.gestor_base_datos)
        self.servicio = ServicioPagos(self.repositorio, gestor_rutas=self.gestor_rutas)

    def tearDown(self) -> None:
        shutil.rmtree(self.raiz_temporal, ignore_errors=True)

    def test_migraciones_007_y_008_agregan_campos_y_catalogos_de_pago(self) -> None:
        with closing(sqlite3.connect(self.ruta_db)) as conexion:
            columnas_pagos = {
                fila[1] for fila in conexion.execute("PRAGMA table_info(pagos);").fetchall()
            }
            columnas_comprobantes = {
                fila[1] for fila in conexion.execute("PRAGMA table_info(comprobantes);").fetchall()
            }
            columnas_metodos = {
                fila[1] for fila in conexion.execute("PRAGMA table_info(metodos_pago);").fetchall()
            }
            version = conexion.execute(
                "SELECT 1 FROM esquema_migraciones WHERE version = '007' LIMIT 1;"
            ).fetchone()
            version_008 = conexion.execute(
                "SELECT 1 FROM esquema_migraciones WHERE version = '008' LIMIT 1;"
            ).fetchone()
            deposito = conexion.execute(
                """
                SELECT requiere_referencia
                FROM metodos_pago
                WHERE codigo = 'DEPOSITO'
                LIMIT 1;
                """
            ).fetchone()
            correlativo = conexion.execute(
                """
                SELECT ultimo_numero
                FROM correlativos_comprobantes
                WHERE clave = 'RECIBO_GLOBAL'
                LIMIT 1;
                """
            ).fetchone()

        self.assertIn("tipo_pago", columnas_pagos)
        self.assertIn("plan_pago_id", columnas_pagos)
        self.assertIn("tipo_comprobante", columnas_comprobantes)
        self.assertIn("saldo_posterior_centavos", columnas_comprobantes)
        self.assertIn("requiere_referencia", columnas_metodos)
        self.assertIsNotNone(version)
        self.assertIsNotNone(version_008)
        self.assertIsNotNone(deposito)
        self.assertEqual(deposito[0], 1)
        self.assertIsNotNone(correlativo)

    def test_mensualidad_cubre_primero_el_cargo_mas_antiguo(self) -> None:
        casa_id = self._obtener_casa_por_dni("0801199000022")
        metodo_id = self._obtener_metodo("EFECTIVO")
        formulario = FormularioPago(
            casa_id=casa_id,
            tipo_pago="MENSUALIDAD",
            cantidad_meses=1,
            metodo_pago_id=metodo_id,
        )

        confirmacion = self.servicio.preparar_confirmacion(formulario)
        self.assertIsInstance(confirmacion, ResumenConfirmacionPago)
        assert isinstance(confirmacion, ResumenConfirmacionPago)
        self.assertEqual(confirmacion.total_pago_centavos, 35000)
        self.assertEqual(confirmacion.detalles[0].etiqueta, "Vencido")

        resultado = self.servicio.registrar_pago(formulario, actor_id=1)

        self.assertTrue(resultado.exito, resultado.mensaje)
        self.assertIsNotNone(resultado.comprobante)
        assert resultado.comprobante is not None
        self.assertTrue(resultado.comprobante.numero_comprobante.startswith("REC-"))
        with closing(sqlite3.connect(self.ruta_db)) as conexion:
            pendientes = conexion.execute(
                """
                SELECT estado, saldo_pendiente_centavos
                FROM cargos
                WHERE casa_id = ?
                ORDER BY fecha_vencimiento ASC;
                """,
                (casa_id,),
            ).fetchall()
            detalle = conexion.execute(
                """
                SELECT COUNT(*)
                FROM pagos_detalle pd
                INNER JOIN pagos p ON p.id = pd.pago_id
                WHERE p.casa_id = ?;
                """,
                (casa_id,),
            ).fetchone()

        self.assertEqual(pendientes[0], ("PAGADO", 0))
        self.assertEqual(pendientes[1], ("PENDIENTE", 35000))
        self.assertEqual(detalle[0], 1)

    def test_metodo_con_referencia_obligatoria_rechaza_pago_sin_referencia(self) -> None:
        casa_id = self._obtener_casa_por_dni("0801199000022")
        metodo_id = self._obtener_metodo("TRANSFERENCIA")

        resultado = self.servicio.preparar_confirmacion(
            FormularioPago(
                casa_id=casa_id,
                tipo_pago="MENSUALIDAD",
                cantidad_meses=1,
                metodo_pago_id=metodo_id,
                referencia="",
            )
        )

        self.assertNotIsInstance(resultado, ResumenConfirmacionPago)
        self.assertEqual(resultado.codigo, "VALIDACION")

    def test_abonado_inactivo_no_puede_registrar_pago(self) -> None:
        casa_id = self._obtener_casa_por_dni("0801199000022")
        metodo_id = self._obtener_metodo("EFECTIVO")
        with closing(sqlite3.connect(self.ruta_db)) as conexion:
            conexion.execute(
                """
                UPDATE abonados
                SET estado = 'INACTIVO'
                WHERE id = (SELECT abonado_id FROM casas WHERE id = ?);
                """,
                (casa_id,),
            )
            conexion.commit()

        resultado = self.servicio.preparar_confirmacion(
            FormularioPago(
                casa_id=casa_id,
                tipo_pago="MENSUALIDAD",
                cantidad_meses=1,
                metodo_pago_id=metodo_id,
            )
        )

        self.assertNotIsInstance(resultado, ResumenConfirmacionPago)
        self.assertEqual(resultado.codigo, "VALIDACION")
        self.assertIn("abonado responsable activo", resultado.mensaje)

    def test_adelanto_rechaza_deuda_vencida_no_mensual(self) -> None:
        casa_id = self._crear_casa_activa_sin_cargos()
        metodo_id = self._obtener_metodo("EFECTIVO")
        self._crear_cargo_mora_vencido(casa_id)

        resultado = self.servicio.preparar_confirmacion(
            FormularioPago(
                casa_id=casa_id,
                tipo_pago="MENSUALIDAD",
                cantidad_meses=1,
                metodo_pago_id=metodo_id,
            )
        )

        self.assertNotIsInstance(resultado, ResumenConfirmacionPago)
        self.assertEqual(resultado.codigo, "VALIDACION")
        self.assertIn("deuda vencida no mensual", resultado.mensaje)

    def test_pago_adelantado_no_duplica_periodo_casa(self) -> None:
        casa_id = self._crear_casa_activa_sin_cargos()
        metodo_id = self._obtener_metodo("EFECTIVO")
        formulario = FormularioPago(
            casa_id=casa_id,
            tipo_pago="MENSUALIDAD",
            cantidad_meses=2,
            metodo_pago_id=metodo_id,
        )

        resultado = self.servicio.registrar_pago(formulario, actor_id=1)
        segundo_resultado = self.servicio.registrar_pago(formulario, actor_id=1)

        self.assertTrue(resultado.exito, resultado.mensaje)
        self.assertFalse(segundo_resultado.exito)
        with closing(sqlite3.connect(self.ruta_db)) as conexion:
            adelantos = conexion.execute(
                "SELECT COUNT(*) FROM pagos_adelantados WHERE casa_id = ?;",
                (casa_id,),
            ).fetchone()

        self.assertEqual(adelantos[0], 2)

    def test_vista_pagos_instancia_en_offscreen(self) -> None:
        _app = QApplication.instance() or QApplication([])
        vista = VistaPagos()
        self.assertEqual(vista.objectName(), "vistaPagos")
        self.assertEqual(vista._tabs.count(), 4)
        self.assertEqual(vista._tabs.tabText(0), "Pago mensual")
        self.assertEqual(vista._tabs.currentIndex(), 0)
        self.assertEqual(vista._flujo_mensual._stack.count(), 4)
        self.assertEqual(vista._flujo_mensual._stack.currentIndex(), vista._flujo_mensual.PASO_BUSQUEDA)
        textos = [label.text() for label in vista.findChildren(type(vista.label_mensaje))]
        self.assertNotIn("Historial reciente de comprobantes", textos)

    def test_controlador_avanza_flujo_mensual_con_datos_reales(self) -> None:
        app = QApplication.instance() or QApplication([])
        vista = VistaPagos()
        controlador = ControladorPagos(self.servicio, vista)
        flujo = vista._flujo_mensual

        controlador._refrescar("0801199000022")
        app.processEvents()

        self.assertGreaterEqual(flujo._tabla_casas.rowCount(), 1)
        flujo._seleccionar_casa(0)
        app.processEvents()

        self.assertEqual(flujo._stack.currentIndex(), flujo.PASO_DIAGNOSTICO)
        self.assertIsNotNone(vista.obtener_casa_seleccionada_id())
        self.assertGreaterEqual(flujo._tabla_cargos.rowCount(), 1)

        flujo._ir_a_paso(flujo.PASO_DATOS)

        indice_metodo = flujo._combo_metodo.findData(self._obtener_metodo("EFECTIVO"))
        self.assertGreaterEqual(indice_metodo, 0)
        flujo._combo_metodo.setCurrentIndex(indice_metodo)
        flujo._solicitar_preparacion_resumen()
        app.processEvents()

        self.assertEqual(flujo._stack.currentIndex(), flujo.PASO_RESUMEN)
        self.assertEqual(flujo._metricas_resumen["Método"].text(), "Efectivo")
        self.assertNotEqual(flujo._metricas_resumen["Total"].text(), "-")
        self.assertTrue(flujo._boton_confirmar.isEnabled())

    def test_registro_desde_resumen_persiste_y_abre_comprobante(self) -> None:
        app = QApplication.instance() or QApplication([])
        vista = VistaPagos()
        controlador = ControladorPagos(self.servicio, vista)
        flujo = vista._flujo_mensual
        controlador._actor = type("ActorPrueba", (), {"identificador": 1})()
        comprobante_abierto: dict[str, bool] = {"ok": False}

        def _confirmar(*_args, **_kwargs):
            return True

        def _mostrar_comprobante(**_kwargs):
            comprobante_abierto["ok"] = True

        vista.confirmar_pago = _confirmar  # type: ignore[method-assign]
        vista.mostrar_comprobante = _mostrar_comprobante  # type: ignore[method-assign]

        with closing(sqlite3.connect(self.ruta_db)) as conexion:
            total_antes = conexion.execute("SELECT COUNT(*) FROM pagos;").fetchone()[0]

        controlador._refrescar("0801199000022")
        flujo._seleccionar_casa(0)
        flujo._ir_a_paso(flujo.PASO_DATOS)
        indice_metodo = flujo._combo_metodo.findData(self._obtener_metodo("EFECTIVO"))
        flujo._combo_metodo.setCurrentIndex(indice_metodo)
        flujo._solicitar_preparacion_resumen()
        app.processEvents()

        self.assertEqual(flujo._stack.currentIndex(), flujo.PASO_RESUMEN)
        flujo._emitir_registro()
        app.processEvents()

        with closing(sqlite3.connect(self.ruta_db)) as conexion:
            total_despues = conexion.execute("SELECT COUNT(*) FROM pagos;").fetchone()[0]

        self.assertEqual(total_despues, total_antes + 1)
        self.assertTrue(comprobante_abierto["ok"])
        self.assertEqual(flujo._stack.currentIndex(), flujo.PASO_BUSQUEDA)

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

    def _crear_casa_activa_sin_cargos(self) -> int:
        with closing(sqlite3.connect(self.ruta_db)) as conexion:
            barrio_id = conexion.execute("SELECT id FROM barrios LIMIT 1;").fetchone()[0]
            cursor_abonado = conexion.execute(
                """
                INSERT INTO abonados(dni, nombre_completo, telefono, barrio_id, direccion_referencia)
                VALUES (?, 'Prueba Adelantos', '0000-0000', ?, 'Casa para pruebas');
                """,
                (f"9999{uuid.uuid4().hex[:8]}", barrio_id),
            )
            cursor_casa = conexion.execute(
                """
                INSERT INTO casas(abonado_id, barrio_id, direccion_referencia, estado_servicio)
                VALUES (?, ?, 'Casa sin cargos', 'ACTIVO');
                """,
                (int(cursor_abonado.lastrowid), barrio_id),
            )
            conexion.commit()
        return int(cursor_casa.lastrowid)

    def _crear_cargo_mora_vencido(self, casa_id: int) -> None:
        with closing(sqlite3.connect(self.ruta_db)) as conexion:
            fila = conexion.execute(
                """
                SELECT c.abonado_id, cc.id
                FROM casas c
                CROSS JOIN conceptos_cobro cc
                WHERE c.id = ?
                  AND (cc.codigo = 'MORA' OR cc.tipo = 'MORA')
                LIMIT 1;
                """,
                (casa_id,),
            ).fetchone()
            assert fila is not None
            conexion.execute(
                """
                INSERT INTO cargos(
                    casa_id,
                    abonado_id,
                    periodo_id,
                    concepto_id,
                    descripcion,
                    monto_centavos,
                    saldo_pendiente_centavos,
                    fecha_vencimiento,
                    estado,
                    origen
                )
                VALUES (?, ?, NULL, ?, 'Recargo vencido de prueba', 5000, 5000, date('now', '-15 day'), 'VENCIDO', 'MANUAL');
                """,
                (casa_id, int(fila[0]), int(fila[1])),
            )
            conexion.commit()


if __name__ == "__main__":
    unittest.main()
