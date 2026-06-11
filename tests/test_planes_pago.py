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
from tests.utilidades_base_datos import inicializar_base_datos_prueba  # noqa: E402
from PySide6.QtWidgets import QApplication, QLabel, QScrollArea  # noqa: E402
from modulos.planes_pago.entidades import FILTRO_PLANES_CON_MORA, FILTRO_PLANES_TODOS, FormularioPlanPago  # noqa: E402
from modulos.planes_pago.repositorio import RepositorioPlanesPagoSQLite  # noqa: E402
from modulos.planes_pago.servicio import ServicioPlanesPago  # noqa: E402
from modulos.planes_pago.vista import (  # noqa: E402
    DialogoDetallePlanPago,
    DialogoFormularioPlanPago,
    VistaPlanesPago,
)


class TestPlanesPago(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.aplicacion = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.raiz_temporal = RAIZ_PROYECTO / "tests" / f"_tmp_planes_{uuid.uuid4().hex}"
        (self.raiz_temporal / "database" / "migrations").mkdir(parents=True, exist_ok=True)
        for ruta in (RAIZ_PROYECTO / "database" / "migrations").glob("*.sql"):
            (self.raiz_temporal / "database" / "migrations" / ruta.name).write_text(
                ruta.read_text(encoding="utf-8"),
                encoding="utf-8",
            )
        self.gestor_rutas = GestorRutas(raiz_proyecto=self.raiz_temporal)
        self.gestor_base_datos = GestorBaseDatos(self.gestor_rutas)
        self.ruta_db = inicializar_base_datos_prueba(self.gestor_base_datos)
        self.repositorio = RepositorioPlanesPagoSQLite(self.gestor_base_datos)
        self.servicio = ServicioPlanesPago(self.repositorio)

    def tearDown(self) -> None:
        shutil.rmtree(self.raiz_temporal, ignore_errors=True)

    def test_resumen_y_detalle_reflejan_plan_semilla(self) -> None:
        resumen = self.servicio.obtener_resumen()
        pagina = self.servicio.listar(filtro_rapido=FILTRO_PLANES_TODOS)

        self.assertEqual(resumen.total_planes, 1)
        self.assertEqual(resumen.planes_activos, 1)
        self.assertEqual(resumen.planes_con_mora, 1)
        self.assertEqual(pagina.total_registros, 1)

        detalle = self.servicio.obtener_detalle(pagina.items[0].identificador or 0)
        self.assertIsNotNone(detalle)
        assert detalle is not None
        self.assertEqual(detalle.plan.tipo_plan, "RECONEXION")
        self.assertEqual(detalle.plan.cuotas_pendientes, 2)
        self.assertEqual(len(detalle.cuotas), 2)
        self.assertGreaterEqual(len(detalle.cargos_vinculados), 1)

    def test_dialogo_detalle_plan_aplica_estilos_a_sus_componentes(self) -> None:
        pagina = self.servicio.listar(filtro_rapido=FILTRO_PLANES_TODOS)
        detalle = self.servicio.obtener_detalle(pagina.items[0].identificador or 0)
        self.assertIsNotNone(detalle)
        assert detalle is not None

        dialogo = DialogoDetallePlanPago(
            detalle,
            lambda centavos: f"L {centavos / 100:,.2f}",
            lambda fecha: fecha,
        )

        self.assertIn("QFrame#panelContenidoDetallePlan", dialogo.styleSheet())
        self.assertIn("QFrame#seccionDetallePlan", dialogo.styleSheet())
        self.assertIn("QFrame#campoDetallePlan", dialogo.styleSheet())
        self.assertIn("QFrame#tarjetaMiniDetallePlan", dialogo.styleSheet())
        badge = dialogo.findChild(QLabel, "badgeEstadoDetalleSigqua")
        self.assertIsNotNone(badge)
        assert badge is not None
        self.assertEqual(badge.minimumHeight(), badge.maximumHeight())
        self.assertGreaterEqual(badge.minimumHeight(), 28)
        dialogo.close()

    def test_rechaza_plan_de_conexion(self) -> None:
        casa_id = self._crear_casa_cortada(ha_tenido_servicio_activo=False)
        metodo_id = self._obtener_metodo_pago("EFECTIVO")

        resultado = self.servicio.guardar(
            FormularioPlanPago(
                identificador=None,
                casa_id=casa_id,
                tipo_plan="CONEXION",
                concepto_financiado="CONEXION",
                fecha_activacion="2026-05-24",
                metodo_pago_id=metodo_id,
                referencia_pago="",
                monto_activacion_centavos=60000,
                prima_centavos=20000,
                cantidad_cuotas=4,
                estado="ACTIVO",
                observaciones="Plan de activacion con deuda financiada.",
            ),
            actor_id=1,
        )

        self.assertFalse(resultado.exito)
        self.assertEqual(resultado.codigo, "VALIDACION")
        self.assertIn("reconexion", resultado.mensaje.lower())

    def test_previsualizacion_plan_genera_vencimientos_desde_fecha_activacion(self) -> None:
        casa_id = self._crear_casa_cortada(ha_tenido_servicio_activo=True)
        metodo_id = self._obtener_metodo_pago("EFECTIVO")

        confirmacion = self.servicio.previsualizar_confirmacion(
            FormularioPlanPago(
                identificador=None,
                casa_id=casa_id,
                tipo_plan="RECONEXION",
                concepto_financiado="RECONEXION",
                fecha_activacion="2026-06-15",
                metodo_pago_id=metodo_id,
                referencia_pago="",
                monto_activacion_centavos=45000,
                prima_centavos=15000,
                cantidad_cuotas=3,
                estado="ACTIVO",
                observaciones="Plan guiado de reconexion.",
            )
        )

        self.assertTrue(hasattr(confirmacion, "primer_vencimiento"))
        self.assertEqual(confirmacion.primer_vencimiento, "2026-07-15")
        self.assertEqual(confirmacion.ultimo_vencimiento, "2026-09-15")
        self.assertEqual(confirmacion.deuda_financiada_centavos, 35000)
        self.assertEqual(confirmacion.monto_total_centavos, 80000)

    def test_crear_plan_usa_fecha_activacion_como_inicio_para_evitar_check_fecha_fin(self) -> None:
        casa_id = self._crear_casa_cortada(ha_tenido_servicio_activo=True)
        metodo_id = self._obtener_metodo_pago("EFECTIVO")

        resultado = self.servicio.guardar(
            FormularioPlanPago(
                identificador=None,
                casa_id=casa_id,
                tipo_plan="RECONEXION",
                concepto_financiado="RECONEXION",
                fecha_activacion="2026-05-01",
                metodo_pago_id=metodo_id,
                referencia_pago="",
                monto_activacion_centavos=45000,
                prima_centavos=10000,
                cantidad_cuotas=1,
                estado="ACTIVO",
                observaciones="Plan con activacion anterior a la fecha local.",
            ),
            actor_id=1,
        )

        self.assertTrue(resultado.exito, resultado.mensaje)
        with closing(sqlite3.connect(self.ruta_db)) as conexion:
            fila = conexion.execute(
                """
                SELECT fecha_inicio, fecha_fin
                FROM planes_pago
                WHERE casa_id = ?
                ORDER BY id DESC
                LIMIT 1;
                """,
                (casa_id,),
            ).fetchone()
        self.assertEqual(tuple(fila), ("2026-05-01", "2026-06-01"))

    def test_casa_con_plan_finalizado_cuenta_como_reconexion_aunque_flag_este_en_cero(self) -> None:
        casa_id = self._crear_casa_cortada(ha_tenido_servicio_activo=True)
        self._crear_plan_finalizado_reconexion(casa_id)
        metodo_id = self._obtener_metodo_pago("EFECTIVO")

        casa = next(casa for casa in self.servicio.listar_casas_disponibles() if casa.casa_id == casa_id)
        self.assertTrue(casa.ha_tenido_servicio_activo)

        confirmacion = self.servicio.previsualizar_confirmacion(
            FormularioPlanPago(
                identificador=None,
                casa_id=casa_id,
                tipo_plan="RECONEXION",
                concepto_financiado="RECONEXION",
                fecha_activacion="2026-06-02",
                metodo_pago_id=metodo_id,
                referencia_pago="",
                monto_activacion_centavos=45000,
                prima_centavos=15000,
                cantidad_cuotas=3,
                estado="ACTIVO",
                observaciones="Nueva reconexion por corte posterior.",
            )
        )

        self.assertFalse(hasattr(confirmacion, "exito"))
        self.assertEqual(confirmacion.tipo_plan, "RECONEXION")

    def test_filtro_con_mora_mantiene_plan_semilla(self) -> None:
        pagina_mora = self.servicio.listar(filtro_rapido=FILTRO_PLANES_CON_MORA)
        self.assertEqual(pagina_mora.total_registros, 1)

    def test_error_de_guardado_resalta_fecha_cuando_la_excepcion_la_menciona(self) -> None:
        casa_id = self._crear_casa_cortada(ha_tenido_servicio_activo=True)
        metodo_id = self._obtener_metodo_pago("EFECTIVO")
        original = self.repositorio.guardar_plan

        def guardar_plan_fallido(*args, **kwargs):
            raise ValueError("fecha_activacion invalida en procesos_servicio")

        self.repositorio.guardar_plan = guardar_plan_fallido  # type: ignore[method-assign]
        try:
            resultado = self.servicio.guardar(
                FormularioPlanPago(
                    identificador=None,
                    casa_id=casa_id,
                    tipo_plan="RECONEXION",
                    concepto_financiado="RECONEXION",
                    fecha_activacion="2026-06-01",
                    metodo_pago_id=metodo_id,
                    referencia_pago="",
                    monto_activacion_centavos=60000,
                    prima_centavos=20000,
                    cantidad_cuotas=4,
                    estado="ACTIVO",
                    observaciones="Plan con error de fecha.",
                ),
                actor_id=1,
            )
        finally:
            self.repositorio.guardar_plan = original  # type: ignore[method-assign]

        self.assertFalse(resultado.exito)
        self.assertIn("Revisa la fecha de activacion o los vencimientos generados.", resultado.mensaje)

    def test_vista_mantiene_visible_el_error_hasta_reemplazarlo(self) -> None:
        vista = VistaPlanesPago()
        vista.show()
        self.aplicacion.processEvents()
        vista.mostrar_mensaje("Error de fecha en plan.", es_error=True)
        self.aplicacion.processEvents()

        self.assertTrue(vista._mensaje.isVisible())
        self.assertTrue(bool(vista._mensaje.property("error")))
        self.assertFalse(vista._temporizador_mensaje.isActive())

        vista.mostrar_mensaje("Plan guardado correctamente.", es_error=False)
        self.assertTrue(vista._temporizador_mensaje.isActive())
        vista.close()

    def test_listar_abonados_nuevo_plan_agrupa_e_informa_motivo_no_apto(self) -> None:
        casa_apta_id = self._crear_casa_cortada(ha_tenido_servicio_activo=True)
        abonado_no_apto = self._crear_casa_no_apta(estado_servicio="ACTIVO")

        abonados = self.servicio.listar_abonados_nuevo_plan()
        apto = next(abonado for abonado in abonados if any(casa.casa_id == casa_apta_id for casa in abonado.casas_elegibles))
        no_apto = next(abonado for abonado in abonados if abonado.abonado_id == abonado_no_apto)

        self.assertTrue(apto.apto_para_plan)
        self.assertGreaterEqual(len(apto.casas_elegibles), 1)
        self.assertFalse(no_apto.apto_para_plan)
        self.assertEqual(no_apto.motivo_no_apto, "No tiene casas cortadas aptas para plan")

    def test_dialogo_nuevo_plan_usa_buscador_de_abonado_y_chips_de_casa(self) -> None:
        casa_apta_id = self._crear_casa_cortada(ha_tenido_servicio_activo=True)
        abonado_no_apto_id = self._crear_casa_no_apta(estado_servicio="ACTIVO")
        abonados = self.servicio.listar_abonados_nuevo_plan()
        abonado_apto = next(
            abonado for abonado in abonados if any(casa.casa_id == casa_apta_id for casa in abonado.casas_elegibles)
        )
        abonado_no_apto = next(abonado for abonado in abonados if abonado.abonado_id == abonado_no_apto_id)
        casa = next(casa for casa in abonado_apto.casas_elegibles if casa.casa_id == casa_apta_id)
        dialogo = DialogoFormularioPlanPago(
            metodos_pago=self.servicio.listar_metodos_pago_activos(),
            abonados=abonados,
        )
        dialogo.show()
        self.aplicacion.processEvents()
        scroll = dialogo.findChild(QScrollArea, "scrollFormularioPlanPago")

        self.assertEqual(dialogo.minimumHeight(), 440)
        self.assertIsNotNone(scroll)
        self.assertIsNotNone(dialogo._campo_abonado)
        self.assertIsNone(dialogo.obtener_formulario().casa_id)
        self.assertTrue(dialogo._pie.isVisible())
        self.assertFalse(hasattr(dialogo, "_combo_tipo_plan"))
        self.assertFalse(hasattr(dialogo, "_combo_estado"))
        self.assertFalse(dialogo._contenedor_casas.isVisible())

        dialogo._campo_abonado.seleccionar_por_id(abonado_no_apto.abonado_id, abonado_no_apto.etiqueta_busqueda)
        dialogo._manejar_cambio_abonado(abonado_no_apto.abonado_id, abonado_no_apto.etiqueta_busqueda)
        self.assertIn("No tiene casas cortadas aptas para plan", dialogo._aviso_aptitud.text())
        self.assertFalse(dialogo._contenedor_casas.isVisible())

        dialogo._campo_abonado.seleccionar_por_id(abonado_apto.abonado_id, abonado_apto.etiqueta_busqueda)
        dialogo._manejar_cambio_abonado(abonado_apto.abonado_id, abonado_apto.etiqueta_busqueda)
        self.assertTrue(dialogo._contenedor_casas.isVisible())
        self.assertEqual(dialogo._layout_casas.count(), len(abonado_apto.casas_elegibles))
        self.assertIsNone(dialogo.obtener_formulario().casa_id)

        dialogo._seleccionar_casa_desde_chip(casa.casa_id)
        dialogo._campo_activacion.establecer_desde_centavos(60000)
        dialogo._campo_prima.establecer_desde_centavos(20000)
        dialogo._campo_cantidad.setValue(4)
        dialogo._actualizar_resumen_financiado()

        self.assertIsNotNone(dialogo.obtener_formulario().casa_id)
        self.assertIn(abonado_apto.abonado_nombre, dialogo._valor_resumen_abonado.text())
        self.assertEqual(dialogo._campo_cuota.obtener_centavos(), 18750)
        dialogo.close()

    def _crear_casa_cortada(self, *, ha_tenido_servicio_activo: bool) -> int:
        with closing(sqlite3.connect(self.ruta_db)) as conexion:
            conexion.row_factory = sqlite3.Row
            nuevo_abonado = conexion.execute(
                """
                INSERT INTO abonados(nombre_completo, dni, telefono, barrio_id, direccion_referencia, estado)
                VALUES ('Plan Test', ?, '0000-0000', 1, 'Direccion test', 'ACTIVO');
                """,
                (f"08011999{uuid.uuid4().hex[:6]}",),
            )
            abonado_id = int(nuevo_abonado.lastrowid)
            barrio_id = int(
                conexion.execute("SELECT id FROM barrios ORDER BY id ASC LIMIT 1;").fetchone()[0]
            )
            cursor_casa = conexion.execute(
                """
                INSERT INTO casas(
                    abonado_id,
                    barrio_id,
                    direccion_referencia,
                    estado_servicio,
                    estado_administrativo,
                    ha_tenido_servicio_activo
                )
                VALUES (?, ?, 'Casa plan test', 'CORTADO', 'OPERATIVA', ?);
                """,
                (abonado_id, barrio_id, 1 if ha_tenido_servicio_activo else 0),
            )
            casa_id = int(cursor_casa.lastrowid)
            periodo_id = int(
                conexion.execute("SELECT id FROM periodos_cobro ORDER BY id ASC LIMIT 1;").fetchone()[0]
            )
            concepto_id = int(
                conexion.execute(
                    "SELECT id FROM conceptos_cobro WHERE codigo = 'SERVICIO_MENSUAL' LIMIT 1;"
                ).fetchone()[0]
            )
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
                VALUES (?, ?, ?, ?, 'Mensualidad vencida plan test', 35000, 35000, '2026-01-10', 'VENCIDO', 'MANUAL');
                """,
                (casa_id, abonado_id, periodo_id, concepto_id),
            )
            conexion.commit()
        return casa_id

    def _obtener_metodo_pago(self, codigo: str) -> int:
        with closing(sqlite3.connect(self.ruta_db)) as conexion:
            fila = conexion.execute(
                "SELECT id FROM metodos_pago WHERE codigo = ? LIMIT 1;",
                (codigo,),
            ).fetchone()
        assert fila is not None
        return int(fila[0])

    def _crear_casa_no_apta(self, *, estado_servicio: str) -> int:
        with closing(sqlite3.connect(self.ruta_db)) as conexion:
            conexion.row_factory = sqlite3.Row
            nuevo_abonado = conexion.execute(
                """
                INSERT INTO abonados(nombre_completo, dni, telefono, barrio_id, direccion_referencia, estado)
                VALUES ('Plan No Apto', ?, '0000-0000', 1, 'Direccion no apta', 'ACTIVO');
                """,
                (f"08022999{uuid.uuid4().hex[:6]}",),
            )
            abonado_id = int(nuevo_abonado.lastrowid)
            barrio_id = int(
                conexion.execute("SELECT id FROM barrios ORDER BY id ASC LIMIT 1;").fetchone()[0]
            )
            conexion.execute(
                """
                INSERT INTO casas(
                    abonado_id,
                    barrio_id,
                    direccion_referencia,
                    estado_servicio,
                    estado_administrativo,
                    ha_tenido_servicio_activo
                )
                VALUES (?, ?, 'Casa no apta', ?, 'OPERATIVA', 1);
                """,
                (abonado_id, barrio_id, estado_servicio),
            )
            conexion.commit()
        return abonado_id

    def _crear_plan_finalizado_reconexion(self, casa_id: int) -> int:
        with closing(sqlite3.connect(self.ruta_db)) as conexion:
            conexion.row_factory = sqlite3.Row
            fila_casa = conexion.execute(
                "SELECT abonado_id FROM casas WHERE id = ?;",
                (casa_id,),
            ).fetchone()
            cursor = conexion.execute(
                """
                INSERT INTO planes_pago(
                    abonado_id,
                    casa_id,
                    fecha_inicio,
                    fecha_fin,
                    monto_total_centavos,
                    cuota_regular_centavos,
                    cantidad_cuotas,
                    cuotas_pagadas,
                    estado,
                    observaciones,
                    creado_por,
                    tipo_plan,
                    concepto_financiado,
                    prima_centavos,
                    tipo_activacion_origen,
                    fecha_corte_deuda,
                    deuda_financiada_centavos,
                    monto_activacion_centavos
                )
                VALUES (?, ?, '2026-03-01', '2026-05-01', 60000, 30000, 2, 2, 'FINALIZADO',
                        'Plan historico finalizado.', 1, 'RECONEXION', 'RECONEXION', 0,
                        'RECONEXION', '2026-03-01', 0, 60000);
                """,
                (int(fila_casa["abonado_id"]), casa_id),
            )
            conexion.commit()
        return int(cursor.lastrowid)


if __name__ == "__main__":
    unittest.main()
