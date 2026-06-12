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
from tests.utilidades_base_datos import inicializar_base_datos_prueba  # noqa: E402
from comun.ui.temas import obtener_paleta_tema  # noqa: E402
import modulos.pagos.vista as vista_pagos_modulo  # noqa: E402
from modulos.pagos.entidades import (  # noqa: E402
    FormularioPago,
    ResumenConfirmacionPago,
    TIPO_PAGO_CONEXION,
    TIPO_PAGO_RECONEXION,
)
from modulos.pagos.controlador import ControladorPagos  # noqa: E402
from modulos.pagos.repositorio import RepositorioPagosSQLite  # noqa: E402
from modulos.pagos.servicio import ServicioPagos  # noqa: E402
from modulos.pagos.vista import VistaPagos  # noqa: E402


class TestPagos(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.aplicacion = QApplication.instance() or QApplication([])

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
        self.ruta_db = inicializar_base_datos_prueba(self.gestor_base_datos)
        self.repositorio = RepositorioPagosSQLite(self.gestor_base_datos)
        self.servicio = ServicioPagos(self.repositorio, gestor_rutas=self.gestor_rutas)

    def tearDown(self) -> None:
        shutil.rmtree(self.raiz_temporal, ignore_errors=True)

    def test_plantilla_incluye_catalogos_y_separa_comprobantes_termicos(self) -> None:
        with closing(sqlite3.connect(self.ruta_db)) as conexion:
            columnas_pagos = {
                fila[1] for fila in conexion.execute("PRAGMA table_info(pagos);").fetchall()
            }
            columnas_comprobantes = {
                fila[1] for fila in conexion.execute("PRAGMA table_info(comprobantes);").fetchall()
            }
            columnas_impresiones = {
                fila[1] for fila in conexion.execute("PRAGMA table_info(comprobantes_impresiones);").fetchall()
            }
            columnas_metodos = {
                fila[1] for fila in conexion.execute("PRAGMA table_info(metodos_pago);").fetchall()
            }
            tabla_migraciones = conexion.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'esquema_migraciones';"
            ).fetchone()
            columnas_procesos = {
                fila[1] for fila in conexion.execute("PRAGMA table_info(procesos_servicio);").fetchall()
            }
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
            titulo_documento = conexion.execute(
                """
                SELECT valor
                FROM configuracion_sistema
                WHERE clave = 'factura.titulo_documento'
                LIMIT 1;
                """
            ).fetchone()
            impresora_termica = conexion.execute(
                """
                SELECT valor
                FROM configuracion_sistema
                WHERE clave = 'impresion_termica.nombre_impresora'
                LIMIT 1;
                """
            ).fetchone()
            impresora_reportes = conexion.execute(
                """
                SELECT valor
                FROM configuracion_sistema
                WHERE clave = 'impresion_reportes.nombre_impresora'
                LIMIT 1;
                """
            ).fetchone()

        self.assertIn("tipo_pago", columnas_pagos)
        self.assertIn("plan_pago_id", columnas_pagos)
        self.assertIn("tipo_comprobante", columnas_comprobantes)
        self.assertIn("saldo_posterior_centavos", columnas_comprobantes)
        self.assertNotIn("formato_salida", columnas_comprobantes)
        self.assertNotIn("ruta_archivo", columnas_comprobantes)
        self.assertNotIn("hash_documento", columnas_comprobantes)
        self.assertIn("tipo_copia", columnas_impresiones)
        self.assertIn("es_reimpresion", columnas_impresiones)
        self.assertIn("estado", columnas_impresiones)
        self.assertIn("requiere_referencia", columnas_metodos)
        self.assertIsNone(tabla_migraciones)
        self.assertNotIn("multa_corte_centavos", columnas_procesos)
        self.assertIsNotNone(deposito)
        self.assertEqual(deposito[0], 1)
        self.assertIsNotNone(correlativo)
        self.assertEqual(titulo_documento[0], "RECIBO DE PAGO")
        self.assertIsNotNone(impresora_termica)
        self.assertIsNotNone(impresora_reportes)

    def test_configuracion_recibo_expone_firma_compartida(self) -> None:
        with closing(sqlite3.connect(self.ruta_db)) as conexion:
            conexion.execute(
                """
                UPDATE configuracion_sistema
                SET valor = CASE clave
                    WHEN 'documentos.firma_habilitada' THEN '1'
                    WHEN 'documentos.firma_texto_linea' THEN 'Firma autorizada'
                    ELSE valor
                END
                WHERE clave IN (
                    'documentos.firma_habilitada',
                    'documentos.firma_texto_linea'
                );
                """
            )
            conexion.commit()

        configuracion = self.servicio.obtener_configuracion_recibo()

        self.assertTrue(configuracion.firma_habilitada)
        self.assertEqual(configuracion.firma_texto_linea, "Firma autorizada")

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
        self.assertIn("abonado responsable", resultado.mensaje)
        self.assertIn("ACTIVO", resultado.mensaje)

    def test_casa_suspendida_no_puede_registrar_pago_mensual(self) -> None:
        casa_id = self._obtener_casa_por_dni("0801199000022")
        metodo_id = self._obtener_metodo("EFECTIVO")
        with closing(sqlite3.connect(self.ruta_db)) as conexion:
            conexion.execute(
                """
                UPDATE casas
                SET estado_administrativo = 'SUSPENDIDA',
                    motivo_estado_administrativo = 'REVISION_ADMINISTRATIVA'
                WHERE id = ?;
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
        self.assertIn("suspendida", resultado.mensaje.lower())

    def test_pago_crea_comprobante_sqlite_y_deja_impresion_pendiente_sin_pdf(self) -> None:
        casa_id = self._obtener_casa_por_dni("0801199000022")
        metodo_id = self._obtener_metodo("EFECTIVO")
        resultado = self.servicio.registrar_pago(
            FormularioPago(
                casa_id=casa_id,
                tipo_pago="MENSUALIDAD",
                cantidad_meses=1,
                metodo_pago_id=metodo_id,
            ),
            actor_id=1,
        )

        self.assertTrue(resultado.exito, resultado.mensaje)
        assert resultado.comprobante is not None
        self.assertIn("Impresion pendiente", resultado.mensaje)
        with closing(sqlite3.connect(self.ruta_db)) as conexion:
            fila = conexion.execute(
                """
                SELECT numero_comprobante, tipo_comprobante, saldo_posterior_centavos
                FROM comprobantes
                WHERE pago_id = ?;
                """,
                (resultado.comprobante.pago_id,),
            ).fetchone()
            intento = conexion.execute(
                """
                SELECT tipo_copia, es_reimpresion, estado, mensaje_error
                FROM comprobantes_impresiones
                WHERE comprobante_id = (SELECT id FROM comprobantes WHERE pago_id = ?)
                ORDER BY id DESC
                LIMIT 1;
                """,
                (resultado.comprobante.pago_id,),
            ).fetchone()
        self.assertIsNotNone(fila)
        self.assertTrue(fila[0].startswith("REC-"))
        self.assertEqual(fila[1], "MENSUALIDAD")
        self.assertGreaterEqual(fila[2], 0)
        self.assertEqual(intento[0], "AMBAS")
        self.assertEqual(intento[1], 0)
        self.assertEqual(intento[2], "FALLIDO")
        self.assertIn("impresora termica", intento[3])
        ruta_comprobantes = self.raiz_temporal / "exportaciones" / "comprobantes"
        self.assertFalse(any(ruta_comprobantes.glob("*.pdf")) if ruta_comprobantes.exists() else False)

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

    def test_pago_adelantado_continua_sin_duplicar_periodo_casa(self) -> None:
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
        self.assertTrue(segundo_resultado.exito, segundo_resultado.mensaje)
        self.assertIsNotNone(resultado.comprobante)
        assert resultado.comprobante is not None
        self.assertTrue(
            any("adelantada" in detalle.lower() for detalle in resultado.comprobante.detalles)
        )
        with closing(sqlite3.connect(self.ruta_db)) as conexion:
            adelantos = conexion.execute(
                """
                SELECT COUNT(*), COUNT(DISTINCT periodo_id)
                FROM pagos_adelantados
                WHERE casa_id = ?;
                """,
                (casa_id,),
            ).fetchone()

        self.assertEqual(adelantos, (4, 4))

    def test_adelanto_historico_deja_de_consumir_cupo(self) -> None:
        from datetime import date

        casa_id = self._crear_casa_activa_sin_cargos()
        metodo_id = self._obtener_metodo("EFECTIVO")
        resultado = self.servicio.registrar_pago(
            FormularioPago(casa_id, "MENSUALIDAD", 1, metodo_id),
            actor_id=1,
        )
        with closing(sqlite3.connect(self.ruta_db)) as conexion:
            periodo_id = conexion.execute(
                "SELECT periodo_id FROM pagos_adelantados WHERE casa_id = ?;",
                (casa_id,),
            ).fetchone()[0]
            conexion.execute(
                "UPDATE periodos_cobro SET anio = ? WHERE id = ?;",
                (date.today().year - 1, periodo_id),
            )
            conexion.commit()

        resumen = self.repositorio.obtener_resumen_adelanto_casa(casa_id)

        self.assertTrue(resultado.exito, resultado.mensaje)
        self.assertEqual(resumen.meses_activos, 0)
        self.assertEqual(resumen.monto_activo_centavos, 0)
        self.assertEqual(resumen.capacidad_disponible, min(12, 13 - date.today().month))

    def test_configuracion_desactivada_permite_deuda_pero_bloquea_adelanto(self) -> None:
        casa_con_deuda = self._obtener_casa_por_dni("0801199000022")
        casa_sin_cargos = self._crear_casa_activa_sin_cargos()
        metodo_id = self._obtener_metodo("EFECTIVO")
        with closing(sqlite3.connect(self.ruta_db)) as conexion:
            conexion.execute(
                """
                UPDATE configuracion_sistema
                SET valor = '0'
                WHERE clave = 'cobro.permitir_pago_adelantado';
                """
            )
            conexion.commit()

        pago_deuda = self.servicio.preparar_confirmacion(
            FormularioPago(casa_con_deuda, "MENSUALIDAD", 1, metodo_id)
        )
        adelanto = self.servicio.preparar_confirmacion(
            FormularioPago(casa_sin_cargos, "MENSUALIDAD", 1, metodo_id)
        )

        self.assertIsInstance(pago_deuda, ResumenConfirmacionPago)
        self.assertNotIsInstance(adelanto, ResumenConfirmacionPago)
        self.assertIn("desactivados", adelanto.mensaje.lower())

    def test_cupo_de_adelantos_se_calcula_hasta_diciembre(self) -> None:
        casa_id = self._crear_casa_activa_sin_cargos()
        metodo_id = self._obtener_metodo("EFECTIVO")
        from datetime import date

        cupo = 13 - date.today().month
        diagnostico = self.servicio.obtener_diagnostico_pago_mensual(casa_id)
        exceso = self.servicio.preparar_confirmacion(
            FormularioPago(casa_id, "MENSUALIDAD", cupo + 1, metodo_id)
        )

        self.assertIsNotNone(diagnostico)
        assert diagnostico is not None
        self.assertEqual(diagnostico.maximo_meses_seleccionable, cupo)
        self.assertNotIsInstance(exceso, ResumenConfirmacionPago)

    def test_adelanto_no_supera_diciembre_y_mes_actual_consume_cupo(self) -> None:
        from datetime import date

        casa_id = self._crear_casa_activa_sin_cargos()
        metodo_id = self._obtener_metodo("EFECTIVO")
        meses_disponibles = 13 - date.today().month
        confirmacion = self.servicio.preparar_confirmacion(
            FormularioPago(casa_id, "MENSUALIDAD", meses_disponibles, metodo_id)
        )
        exceso = self.servicio.preparar_confirmacion(
            FormularioPago(casa_id, "MENSUALIDAD", meses_disponibles + 1, metodo_id)
        )

        self.assertIsInstance(confirmacion, ResumenConfirmacionPago)
        assert isinstance(confirmacion, ResumenConfirmacionPago)
        self.assertEqual(confirmacion.detalles[0].periodo_mes, date.today().month)
        self.assertEqual(confirmacion.detalles[-1].periodo_mes, 12)
        self.assertNotIsInstance(exceso, ResumenConfirmacionPago)

    def test_plan_reconexion_pendiente_bloquea_solo_el_adelanto(self) -> None:
        casa_id = self._obtener_casa_por_dni("0801199000022")
        metodo_id = self._obtener_metodo("EFECTIVO")

        deuda = self.servicio.preparar_confirmacion(
            FormularioPago(casa_id, "MENSUALIDAD", 2, metodo_id)
        )
        con_adelanto = self.servicio.preparar_confirmacion(
            FormularioPago(casa_id, "MENSUALIDAD", 3, metodo_id)
        )

        self.assertIsInstance(deuda, ResumenConfirmacionPago)
        self.assertNotIsInstance(con_adelanto, ResumenConfirmacionPago)
        self.assertIn("plan de reconexion", con_adelanto.mensaje.lower())

    def test_diagnostico_activacion_clasifica_por_antecedente(self) -> None:
        casa_conexion, _dni_conexion = self._crear_casa_cortada_para_activacion(
            ha_tenido_servicio_activo=False
        )
        casa_reconexion, _dni_reconexion = self._crear_casa_cortada_para_activacion(
            ha_tenido_servicio_activo=True
        )

        diagnostico_conexion = self.servicio.obtener_diagnostico_conexion(casa_conexion)
        diagnostico_reconexion = self.servicio.obtener_diagnostico_reconexion(casa_reconexion)
        resultado_flujo_incorrecto = self.servicio.previsualizar_pago_reconexion(
            FormularioPago(
                casa_id=casa_conexion,
                tipo_pago=TIPO_PAGO_RECONEXION,
                cantidad_meses=1,
                metodo_pago_id=self._obtener_metodo("EFECTIVO"),
                fecha_activacion="2026-05-19",
                monto_reconexion_centavos=50000,
            )
        )

        self.assertIsNotNone(diagnostico_conexion)
        self.assertIsNotNone(diagnostico_reconexion)
        assert diagnostico_conexion is not None
        assert diagnostico_reconexion is not None
        self.assertTrue(diagnostico_conexion.permite_continuar)
        self.assertEqual(diagnostico_conexion.clasificacion, TIPO_PAGO_CONEXION)
        self.assertTrue(diagnostico_reconexion.permite_continuar)
        self.assertEqual(diagnostico_reconexion.clasificacion, TIPO_PAGO_RECONEXION)
        self.assertNotIsInstance(resultado_flujo_incorrecto, ResumenConfirmacionPago)
        self.assertEqual(resultado_flujo_incorrecto.codigo, "VALIDACION")
        self.assertIn("nunca ha tenido servicio", resultado_flujo_incorrecto.mensaje.lower())

    def test_plan_activo_bloquea_activacion_normal(self) -> None:
        casa_id, _dni = self._crear_casa_cortada_para_activacion(ha_tenido_servicio_activo=False)
        self._crear_plan_activo_para_casa(casa_id)

        resultado = self.servicio.previsualizar_pago_conexion(
            FormularioPago(
                casa_id=casa_id,
                tipo_pago=TIPO_PAGO_CONEXION,
                cantidad_meses=1,
                metodo_pago_id=self._obtener_metodo("EFECTIVO"),
                fecha_activacion="2026-05-19",
                monto_conexion_centavos=50000,
            )
        )

        self.assertNotIsInstance(resultado, ResumenConfirmacionPago)
        self.assertEqual(resultado.codigo, "VALIDACION")
        self.assertIn("plan de pago activo", resultado.mensaje.lower())

    def test_previsualizacion_conexion_incluye_prorrateo_si_configurado(self) -> None:
        casa_id, _dni = self._crear_casa_cortada_para_activacion(ha_tenido_servicio_activo=False)
        self._configurar_prorrateo_activacion(True)

        resultado = self.servicio.previsualizar_pago_conexion(
            FormularioPago(
                casa_id=casa_id,
                tipo_pago=TIPO_PAGO_CONEXION,
                cantidad_meses=1,
                metodo_pago_id=self._obtener_metodo("EFECTIVO"),
                fecha_activacion="2026-05-19",
                monto_conexion_centavos=50000,
            )
        )

        self.assertIsInstance(resultado, ResumenConfirmacionPago)
        assert isinstance(resultado, ResumenConfirmacionPago)
        conceptos = [detalle.concepto_codigo for detalle in resultado.detalles]
        self.assertIn("CONEXION", conceptos)
        self.assertIn("MENSUALIDAD_PRORRATEADA", conceptos)

    def test_reconexion_no_acepta_campo_legacy_multa_corte(self) -> None:
        casa_id, _dni = self._crear_casa_cortada_para_activacion(ha_tenido_servicio_activo=True)

        with self.assertRaises(TypeError):
            FormularioPago(  # type: ignore[call-arg]
                casa_id=casa_id,
                tipo_pago=TIPO_PAGO_RECONEXION,
                cantidad_meses=1,
                metodo_pago_id=self._obtener_metodo("EFECTIVO"),
                fecha_activacion="2026-05-19",
                monto_reconexion_centavos=50000,
                multa_corte_centavos=10000,
            )

    def test_previsualizacion_reconexion_sin_prorrateo_cobrado_no_incluye_multa(self) -> None:
        casa_id, _dni = self._crear_casa_cortada_para_activacion(ha_tenido_servicio_activo=True)
        self._configurar_prorrateo_activacion(False)

        resultado = self.servicio.previsualizar_pago_reconexion(
            FormularioPago(
                casa_id=casa_id,
                tipo_pago=TIPO_PAGO_RECONEXION,
                cantidad_meses=1,
                metodo_pago_id=self._obtener_metodo("EFECTIVO"),
                fecha_activacion="2026-05-19",
                monto_reconexion_centavos=50000,
            )
        )

        self.assertIsInstance(resultado, ResumenConfirmacionPago)
        assert isinstance(resultado, ResumenConfirmacionPago)
        conceptos = [detalle.concepto_codigo for detalle in resultado.detalles]
        self.assertEqual(conceptos, ["RECONEXION"])
        self.assertNotIn("MULTA", conceptos)
        self.assertEqual(resultado.total_pago_centavos, 50000)
        self.assertGreater(resultado.prorrateo_pendiente_centavos, 0)

    def test_registro_reconexion_con_prorrateo_inactivo_crea_cargo_pendiente(self) -> None:
        casa_id, _dni = self._crear_casa_cortada_para_activacion(ha_tenido_servicio_activo=True)
        self._configurar_prorrateo_activacion(False)

        resultado = self.servicio.registrar_pago(
            FormularioPago(
                casa_id=casa_id,
                tipo_pago=TIPO_PAGO_RECONEXION,
                cantidad_meses=1,
                metodo_pago_id=self._obtener_metodo("EFECTIVO"),
                fecha_activacion="2026-05-19",
                monto_reconexion_centavos=50000,
            ),
            actor_id=1,
        )

        self.assertTrue(resultado.exito, resultado.mensaje)
        with closing(sqlite3.connect(self.ruta_db)) as conexion:
            detalle_prorrateo = conexion.execute(
                """
                SELECT COUNT(*)
                FROM pagos_detalle pd
                INNER JOIN conceptos_cobro cc ON cc.id = pd.concepto_id
                WHERE pd.pago_id = ?
                  AND cc.codigo = 'MENSUALIDAD_PRORRATEADA';
                """,
                (resultado.comprobante.pago_id,),
            ).fetchone()
            cargo_prorrateo = conexion.execute(
                """
                SELECT ca.estado, ca.saldo_pendiente_centavos
                FROM cargos ca
                INNER JOIN conceptos_cobro cc ON cc.id = ca.concepto_id
                WHERE ca.casa_id = ?
                  AND cc.codigo = 'MENSUALIDAD_PRORRATEADA'
                ORDER BY ca.id DESC
                LIMIT 1;
                """,
                (casa_id,),
            ).fetchone()

        self.assertEqual(detalle_prorrateo[0], 0)
        self.assertIsNotNone(cargo_prorrateo)
        self.assertEqual(cargo_prorrateo[0], "PENDIENTE")
        self.assertGreater(cargo_prorrateo[1], 0)

    def test_reconexion_con_deuda_mensual_regulariza_sin_multa(self) -> None:
        casa_id, _dni = self._crear_casa_cortada_para_activacion(ha_tenido_servicio_activo=True)
        self._crear_cargo_mensual_vencido(casa_id, monto_centavos=35000)
        self._configurar_prorrateo_activacion(False)

        resultado = self.servicio.previsualizar_pago_reconexion(
            FormularioPago(
                casa_id=casa_id,
                tipo_pago=TIPO_PAGO_RECONEXION,
                cantidad_meses=1,
                metodo_pago_id=self._obtener_metodo("EFECTIVO"),
                fecha_activacion="2026-05-19",
                monto_reconexion_centavos=50000,
            )
        )

        self.assertIsInstance(resultado, ResumenConfirmacionPago)
        assert isinstance(resultado, ResumenConfirmacionPago)
        conceptos = [detalle.concepto_codigo for detalle in resultado.detalles]
        self.assertIn("SERVICIO_MENSUAL", conceptos)
        self.assertIn("RECONEXION", conceptos)
        self.assertNotIn("MULTA", conceptos)
        self.assertTrue(resultado.es_operacion_compuesta)

    def test_registro_conexion_actualiza_estado_y_antecedente(self) -> None:
        casa_id, _dni = self._crear_casa_cortada_para_activacion(ha_tenido_servicio_activo=False)
        self._configurar_prorrateo_activacion(False)

        resultado = self.servicio.registrar_pago(
            FormularioPago(
                casa_id=casa_id,
                tipo_pago=TIPO_PAGO_CONEXION,
                cantidad_meses=1,
                metodo_pago_id=self._obtener_metodo("EFECTIVO"),
                fecha_activacion="2026-05-19",
                monto_conexion_centavos=50000,
            ),
            actor_id=1,
        )

        self.assertTrue(resultado.exito, resultado.mensaje)
        with closing(sqlite3.connect(self.ruta_db)) as conexion:
            fila = conexion.execute(
                """
                SELECT estado_servicio, estado_administrativo, ha_tenido_servicio_activo
                FROM casas
                WHERE id = ?;
                """,
                (casa_id,),
            ).fetchone()
        self.assertEqual(fila[0], "ACTIVO")
        self.assertEqual(fila[1], "OPERATIVA")
        self.assertEqual(fila[2], 1)

    def test_vista_pagos_instancia_en_offscreen(self) -> None:
        _app = QApplication.instance() or QApplication([])
        vista = VistaPagos()
        self.assertEqual(vista.objectName(), "vistaPagos")
        self.assertEqual(vista._tabs.count(), 4)
        self.assertEqual(vista._tabs.tabText(0), "Pago mensual")
        self.assertEqual(vista._tabs.tabText(1), "Reconexion")
        self.assertEqual(vista._tabs.tabText(2), "Conexion")
        self.assertEqual(vista._tabs.currentIndex(), 0)
        self.assertEqual(vista._flujo_mensual._stack.count(), 4)
        self.assertEqual(vista._flujo_conexion._stack.count(), 4)
        self.assertEqual(vista._flujo_reconexion._stack.count(), 4)
        self.assertFalse(hasattr(vista._flujo_reconexion, "_input_multa"))
        self.assertEqual(vista._flujo_mensual._stack.currentIndex(), vista._flujo_mensual.PASO_BUSQUEDA)
        textos = [label.text() for label in vista.findChildren(type(vista.label_mensaje))]
        self.assertNotIn("Historial reciente de comprobantes", textos)
        self.assertFalse(hasattr(vista._flujo_mensual, "_barra_progreso"))
        self.assertEqual(vista._flujo_mensual._tabla_casas.rowCount(), 0)
        self.assertEqual(vista._tabs.property("estadoMensual"), None)
        self.assertEqual(vista._label_estado_apertura.text(), "ESC/POS")
        self.assertEqual(vista._label_estado_impresion.text(), "Pendientes")
        self.assertIsInstance(vista._tabs.widget(3), vista_pagos_modulo.FlujoPagoPlan)
        self.assertEqual(vista._flujo_mensual._input_busqueda.objectName(), "campoBusquedaPago")
        self.assertEqual(vista._flujo_conexion._input_busqueda.objectName(), "campoBusquedaPago")
        self.assertEqual(vista._flujo_reconexion._input_busqueda.objectName(), "campoBusquedaPago")
        self.assertIn(
            "QTableWidget#tablaCasasPagoMensual::item:alternate",
            vista._flujo_mensual.styleSheet(),
        )
        self.assertIn(
            obtener_paleta_tema("tema_sigqua")["borde_foco_input"],
            vista._flujo_mensual.styleSheet(),
        )
        vista.aplicar_tema("tema_sigqua")
        self.assertEqual(vista._tema_actual, "tema_sigqua")
        self.assertEqual(vista._flujo_mensual._tema_actual, "tema_sigqua")
        self.assertIn('font-family: "Segoe UI"', vista.styleSheet())

    def test_vista_notifica_resultado_de_impresion_termica(self) -> None:
        _app = QApplication.instance() or QApplication([])
        vista = VistaPagos()
        vista.mostrar_resultado_impresion("Comprobante REC-000001 enviado a impresion termica.")
        self.assertIn("REC-000001", vista.label_mensaje.text())
        self.assertIn("impresion termica", vista.label_mensaje.text().lower())
        vista.close()

    def test_vista_muestra_advertencia_si_falla_impresion_termica(self) -> None:
        _app = QApplication.instance() or QApplication([])
        vista = VistaPagos()
        vista.mostrar_resultado_impresion(
            "Pago registrado; no hay impresora termica configurada para imprimir el comprobante.",
            es_error=True,
        )

        self.assertIn("impresora", vista.label_mensaje.text().lower())
        self.assertIn("termica", vista.label_mensaje.text().lower())
        self.assertIn("configurada", vista.label_mensaje.text().lower())
        vista.close()

    def test_vista_muestra_estado_documental_en_label(self) -> None:
        _app = QApplication.instance() or QApplication([])
        vista = VistaPagos()
        estado = self.servicio.obtener_estado(filtro="0801199000022")

        vista.mostrar_estado(
            estado,
            self.servicio.formatear_moneda,
            self.servicio.formatear_fecha,
            mostrar_casas=True,
        )

        self.assertEqual(vista._label_estado_apertura.text(), "Sin impresora")
        self.assertFalse(vista._label_estado_apertura.property("activo"))
        self.assertIn("Pendientes:", vista._label_estado_impresion.text())
        self.assertFalse(vista._label_estado_impresion.property("activo"))
        vista.close()

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
        self.assertEqual(vista._tabs.property("estadoMensual"), "OK")

        flujo._ir_a_paso(flujo.PASO_DATOS)

        indice_metodo = flujo._combo_metodo.findData(self._obtener_metodo("EFECTIVO"))
        self.assertGreaterEqual(indice_metodo, 0)
        flujo._combo_metodo.setCurrentIndex(indice_metodo)
        flujo._solicitar_preparacion_resumen()
        app.processEvents()

        self.assertEqual(flujo._stack.currentIndex(), flujo.PASO_RESUMEN)
        etiqueta_metodo = next(
            clave for clave in flujo._metricas_resumen.keys() if "todo" in clave.lower()
        )
        self.assertEqual(flujo._metricas_resumen[etiqueta_metodo].text(), "Efectivo")
        self.assertNotEqual(flujo._metricas_resumen["Total"].text(), "-")
        self.assertTrue(flujo._boton_confirmar.isEnabled())

    def test_vista_bloquea_avance_si_casa_no_esta_activa(self) -> None:
        app = QApplication.instance() or QApplication([])
        vista = VistaPagos()
        controlador = ControladorPagos(self.servicio, vista)
        flujo = vista._flujo_mensual
        casa_id = self._crear_casa_activa_sin_cargos()
        dni = self._obtener_dni_por_casa(casa_id)
        with closing(sqlite3.connect(self.ruta_db)) as conexion:
            conexion.execute(
                """
                UPDATE casas
                SET estado_administrativo = 'SUSPENDIDA',
                    motivo_estado_administrativo = 'REVISION_ADMINISTRATIVA'
                WHERE id = ?;
                """,
                (casa_id,),
            )
            conexion.commit()

        controlador._refrescar(dni)
        app.processEvents()

        self.assertGreaterEqual(flujo._tabla_casas.rowCount(), 1)
        fila_casa = self._buscar_fila_tabla_por_casa(flujo._tabla_casas, casa_id)
        self.assertIsNotNone(fila_casa)
        assert fila_casa is not None
        flujo._seleccionar_casa(fila_casa)
        app.processEvents()

        self.assertEqual(flujo._stack.currentIndex(), flujo.PASO_DIAGNOSTICO)
        self.assertFalse(flujo._boton_diagnostico_siguiente.isEnabled())
        self.assertIn("suspendida", flujo._label_alerta_diagnostico.text().lower())
        self.assertEqual(vista._tabs.property("estadoMensual"), "BLOQUEADO")

    def test_controlador_avanza_flujo_conexion_con_datos_reales(self) -> None:
        app = QApplication.instance() or QApplication([])
        vista = VistaPagos()
        controlador = ControladorPagos(self.servicio, vista)
        flujo = vista._flujo_conexion
        _casa_id, dni = self._crear_casa_cortada_para_activacion(ha_tenido_servicio_activo=False)
        self._configurar_prorrateo_activacion(True)

        controlador._refrescar(dni)
        app.processEvents()

        self.assertGreaterEqual(flujo._tabla_casas.rowCount(), 1)
        flujo._seleccionar_casa(0, 0)
        app.processEvents()

        self.assertEqual(flujo._stack.currentIndex(), flujo.PASO_DIAGNOSTICO)
        self.assertTrue(flujo._boton_diagnostico_siguiente.isEnabled())
        self.assertEqual(
            flujo._metricas_diagnostico["Clasificacion calculada"].text().lower(),
            "conexion",
        )

        flujo._stack.setCurrentIndex(flujo.PASO_DATOS)
        flujo._input_fecha_activacion.setText("2026-05-19")
        flujo._input_monto_principal.setText("500.00")
        indice_metodo = flujo._combo_metodo.findData(self._obtener_metodo("EFECTIVO"))
        self.assertGreaterEqual(indice_metodo, 0)
        flujo._combo_metodo.setCurrentIndex(indice_metodo)
        flujo._emitir_previsualizacion()
        app.processEvents()

        self.assertEqual(flujo._stack.currentIndex(), flujo.PASO_RESUMEN)
        self.assertIn("Conexion de servicio", flujo._visor_resumen.toPlainText())
        self.assertIn("Mensualidad prorrateada", flujo._visor_resumen.toPlainText())
        self.assertTrue(flujo._boton_confirmar.isEnabled())

    def test_diagnostico_plan_bloquea_casa_sin_plan_activo(self) -> None:
        casa_id = self._crear_casa_activa_sin_cargos()

        diagnostico = self.servicio.obtener_diagnostico_plan(casa_id)

        self.assertIsNotNone(diagnostico)
        assert diagnostico is not None
        self.assertFalse(diagnostico.permite_continuar)
        self.assertIn("no tiene un plan activo", diagnostico.mensaje_diagnostico.lower())

    def test_pago_plan_multi_cuota_persiste_varias_lineas(self) -> None:
        casa_id = self._crear_casa_activa_sin_cargos()
        self._crear_plan_activo_para_casa(casa_id)
        metodo_id = self._obtener_metodo("EFECTIVO")

        diagnostico = self.servicio.obtener_diagnostico_plan(casa_id)
        self.assertIsNotNone(diagnostico)
        assert diagnostico is not None
        self.assertTrue(diagnostico.permite_continuar)
        self.assertEqual(len(diagnostico.cuotas_cobrables), 2)

        formulario = FormularioPago(
            casa_id=casa_id,
            tipo_pago="PLAN_PAGO",
            cantidad_meses=0,
            metodo_pago_id=metodo_id,
            plan_pago_id=diagnostico.plan_pago_id,
            cuotas_plan_pago_ids=tuple(cuota.cuota_id for cuota in diagnostico.cuotas_cobrables),
        )

        confirmacion = self.servicio.preparar_confirmacion(formulario)
        self.assertIsInstance(confirmacion, ResumenConfirmacionPago)
        assert isinstance(confirmacion, ResumenConfirmacionPago)
        self.assertEqual(confirmacion.total_pago_centavos, 80000)
        self.assertEqual(len(confirmacion.detalles), 2)

        resultado = self.servicio.registrar_pago(formulario, actor_id=1)

        self.assertTrue(resultado.exito, resultado.mensaje)
        with closing(sqlite3.connect(self.ruta_db)) as conexion:
            filas_detalle = conexion.execute(
                """
                SELECT COUNT(*)
                FROM pagos_detalle
                WHERE pago_id = ?;
                """,
                (resultado.comprobante.pago_id,),
            ).fetchone()
            cuotas = conexion.execute(
                """
                SELECT estado, saldo_pendiente_centavos
                FROM cuotas_plan_pago
                WHERE plan_pago_id = ?
                ORDER BY numero_cuota ASC;
                """,
                (diagnostico.plan_pago_id,),
            ).fetchall()
            fila_pago = conexion.execute(
                "SELECT tipo_pago, plan_pago_id FROM pagos WHERE id = ?;",
                (resultado.comprobante.pago_id,),
            ).fetchone()
        self.assertEqual(filas_detalle[0], 2)
        self.assertEqual(fila_pago[0], "PLAN_PAGO")
        self.assertEqual(fila_pago[1], diagnostico.plan_pago_id)
        self.assertEqual(cuotas[0], ("PAGADO", 0))
        self.assertEqual(cuotas[1], ("PAGADO", 0))

    def test_repositorio_rechaza_pago_parcial_de_mensualidad(self) -> None:
        with closing(self.gestor_base_datos.obtener_conexion()) as conexion:
            with self.assertRaisesRegex(ValueError, "saldo completo"):
                self.repositorio._actualizar_saldo_cargo(
                    conexion,
                    cargo_id=2,
                    monto_pagado=10000,
                )
            fila = conexion.execute(
                "SELECT estado, saldo_pendiente_centavos FROM cargos WHERE id = 2;"
            ).fetchone()

        self.assertEqual((fila["estado"], fila["saldo_pendiente_centavos"]), ("VENCIDO", 35000))

    def test_repositorio_rechaza_pago_parcial_de_cuota(self) -> None:
        casa_id = self._crear_casa_activa_sin_cargos()
        self._crear_plan_activo_para_casa(casa_id)
        diagnostico = self.servicio.obtener_diagnostico_plan(casa_id)
        assert diagnostico is not None
        formulario = FormularioPago(
            casa_id=casa_id,
            tipo_pago="PLAN_PAGO",
            cantidad_meses=0,
            metodo_pago_id=self._obtener_metodo("EFECTIVO"),
            plan_pago_id=diagnostico.plan_pago_id,
            cuotas_plan_pago_ids=(diagnostico.cuotas_cobrables[0].cuota_id,),
        )
        confirmacion = self.servicio.preparar_confirmacion(formulario)
        assert isinstance(confirmacion, ResumenConfirmacionPago)
        confirmacion.detalles[0].monto_centavos -= 1

        with closing(self.gestor_base_datos.obtener_conexion()) as conexion:
            with self.assertRaisesRegex(ValueError, "saldo completo"):
                self.repositorio._persistir_detalles_plan_pago(
                    conexion,
                    pago_id=1,
                    resumen=confirmacion,
                )
            fila = conexion.execute(
                """
                SELECT estado, saldo_pendiente_centavos
                FROM cuotas_plan_pago
                WHERE id = ?;
                """,
                (confirmacion.detalles[0].cargo_id,),
            ).fetchone()

        self.assertNotEqual(fila["estado"], "PAGADO")
        self.assertGreater(fila["saldo_pendiente_centavos"], 0)

    def test_controlador_avanza_flujo_plan_con_cuota_preseleccionada(self) -> None:
        app = QApplication.instance() or QApplication([])
        vista = VistaPagos()
        controlador = ControladorPagos(self.servicio, vista)
        flujo = vista._flujo_plan
        casa_id = self._crear_casa_activa_sin_cargos()
        self._crear_plan_activo_para_casa(casa_id)
        dni = self._obtener_dni_por_casa(casa_id)

        controlador._refrescar(dni)
        app.processEvents()

        self.assertGreaterEqual(flujo._tabla_casas.rowCount(), 1)
        flujo._seleccionar_casa(0, 0)
        app.processEvents()

        self.assertEqual(flujo._stack.currentIndex(), flujo.PASO_DIAGNOSTICO)
        self.assertTrue(flujo._boton_diagnostico_siguiente.isEnabled())
        self.assertEqual(flujo._metricas_diagnostico["Codigo plan"].text()[:3], "PP-")

        flujo._ir_a_paso(flujo.PASO_DATOS)
        app.processEvents()

        self.assertEqual(len(flujo._cuotas_seleccionadas), 1)
        indice_metodo = flujo._combo_metodo.findData(self._obtener_metodo("EFECTIVO"))
        self.assertGreaterEqual(indice_metodo, 0)
        flujo._combo_metodo.setCurrentIndex(indice_metodo)
        flujo._emitir_previsualizacion()
        app.processEvents()

        self.assertEqual(flujo._stack.currentIndex(), flujo.PASO_RESUMEN)
        self.assertIn("Cuota 1", flujo._visor_resumen.toPlainText())
        self.assertTrue(flujo._boton_confirmar.isEnabled())

    def test_registro_desde_resumen_persiste_y_notifica_impresion_pendiente(self) -> None:
        app = QApplication.instance() or QApplication([])
        vista = VistaPagos()
        controlador = ControladorPagos(self.servicio, vista)
        flujo = vista._flujo_mensual
        controlador._actor = type("ActorPrueba", (), {"identificador": 1})()
        mensajes: list[str] = []

        def _confirmar(*_args, **_kwargs):
            return True

        vista.confirmar_pago = _confirmar  # type: ignore[method-assign]
        vista.mostrar_mensaje = lambda mensaje, es_error=False: mensajes.append(mensaje)  # type: ignore[method-assign]

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
        self.assertTrue(mensajes)
        self.assertIn("Impresion pendiente", mensajes[-1])
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

    def _crear_casa_cortada_para_activacion(
        self,
        *,
        ha_tenido_servicio_activo: bool,
        estado_administrativo: str = "OPERATIVA",
        abonado_estado: str = "ACTIVO",
    ) -> tuple[int, str]:
        dni = f"8888{uuid.uuid4().hex[:8]}"
        with closing(sqlite3.connect(self.ruta_db)) as conexion:
            barrio_id = conexion.execute("SELECT id FROM barrios LIMIT 1;").fetchone()[0]
            cursor_abonado = conexion.execute(
                """
                INSERT INTO abonados(
                    dni,
                    nombre_completo,
                    telefono,
                    barrio_id,
                    direccion_referencia,
                    estado
                )
                VALUES (?, 'Casa activacion prueba', '0000-0000', ?, 'Casa activacion', ?);
                """,
                (dni, barrio_id, abonado_estado),
            )
            cursor_casa = conexion.execute(
                """
                INSERT INTO casas(
                    abonado_id,
                    barrio_id,
                    direccion_referencia,
                    estado_servicio,
                    estado_administrativo,
                    motivo_estado_administrativo,
                    ha_tenido_servicio_activo
                )
                VALUES (?, ?, 'Casa cortada para activacion', 'CORTADO', ?, ?, ?);
                """,
                (
                    int(cursor_abonado.lastrowid),
                    barrio_id,
                    estado_administrativo,
                    "REVISION_ADMINISTRATIVA" if estado_administrativo == "SUSPENDIDA" else "NINGUNO",
                    1 if ha_tenido_servicio_activo else 0,
                ),
            )
            conexion.commit()
        return int(cursor_casa.lastrowid), dni

    def _crear_plan_activo_para_casa(self, casa_id: int) -> None:
        with closing(sqlite3.connect(self.ruta_db)) as conexion:
            abonado_id = conexion.execute(
                "SELECT abonado_id FROM casas WHERE id = ?;",
                (casa_id,),
            ).fetchone()[0]
            cursor_plan = conexion.execute(
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
                    prima_centavos
                )
                VALUES (?, ?, '2026-05-01', '2026-07-31', 80000, 40000, 2, 0, 'ACTIVO', 'Plan de prueba', 1, 'RECONEXION', 'RECONEXION', 0);
                """,
                (int(abonado_id), casa_id),
            )
            plan_id = int(cursor_plan.lastrowid)
            conexion.executemany(
                """
                INSERT INTO cuotas_plan_pago(
                    plan_pago_id,
                    numero_cuota,
                    fecha_vencimiento,
                    monto_centavos,
                    saldo_pendiente_centavos,
                    estado
                )
                VALUES (?, ?, ?, ?, ?, ?);
                """,
                (
                    (plan_id, 1, "2026-05-15", 40000, 40000, "VENCIDO"),
                    (plan_id, 2, "2026-06-15", 40000, 40000, "PENDIENTE"),
                ),
            )
            conexion.commit()

    def _obtener_dni_por_casa(self, casa_id: int) -> str:
        with closing(sqlite3.connect(self.ruta_db)) as conexion:
            fila = conexion.execute(
                """
                SELECT a.dni
                FROM casas c
                INNER JOIN abonados a ON a.id = c.abonado_id
                WHERE c.id = ?;
                """,
                (casa_id,),
            ).fetchone()
        assert fila is not None
        return str(fila[0])

    @staticmethod
    def _buscar_fila_tabla_por_casa(tabla: object, casa_id: int) -> int | None:
        for fila in range(tabla.rowCount()):
            item = tabla.item(fila, 0)
            if item is not None and int(item.data(vista_pagos_modulo.Qt.ItemDataRole.UserRole)) == casa_id:
                return fila
        return None

    def _configurar_prorrateo_activacion(self, activo: bool) -> None:
        with closing(sqlite3.connect(self.ruta_db)) as conexion:
            conexion.execute(
                """
                UPDATE configuracion_sistema
                SET valor = ?
                WHERE clave = 'cobro.cobrar_mensualidad_prorrateada_activacion';
                """,
                ("1" if activo else "0",),
            )
            conexion.commit()

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
                VALUES (?, ?, NULL, ?, 'Recargo vencido de prueba', 5000, 5000, date('now', 'localtime', '-15 day'), 'VENCIDO', 'MANUAL');
                """,
                (casa_id, int(fila[0]), int(fila[1])),
            )
            conexion.commit()

    def _crear_cargo_mensual_vencido(self, casa_id: int, *, monto_centavos: int) -> None:
        with closing(sqlite3.connect(self.ruta_db)) as conexion:
            fila = conexion.execute(
                """
                SELECT c.abonado_id, cc.id
                FROM casas c
                CROSS JOIN conceptos_cobro cc
                WHERE c.id = ?
                  AND cc.codigo = 'SERVICIO_MENSUAL'
                LIMIT 1;
                """,
                (casa_id,),
            ).fetchone()
            assert fila is not None
            conexion.execute(
                """
                INSERT OR IGNORE INTO periodos_cobro(anio, mes, nombre, fecha_inicio, fecha_fin, fecha_vencimiento)
                VALUES (2026, 4, 'Abril 2026 prueba', '2026-04-01', '2026-04-30', '2026-04-30');
                """
            )
            periodo = conexion.execute(
                "SELECT id FROM periodos_cobro WHERE anio = 2026 AND mes = 4 LIMIT 1;"
            ).fetchone()
            assert periodo is not None
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
                VALUES (?, ?, ?, ?, 'Mensualidad vencida de prueba', ?, ?, '2026-04-30', 'VENCIDO', 'MENSUAL');
                """,
                (casa_id, int(fila[0]), int(periodo[0]), int(fila[1]), monto_centavos, monto_centavos),
            )
            conexion.commit()


if __name__ == "__main__":
    unittest.main()


