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
from modulos.configuracion.repositorio import RepositorioConfiguracionSQLite  # noqa: E402
from modulos.configuracion.servicio import ServicioConfiguracion  # noqa: E402


class TestConfiguracion(unittest.TestCase):
    def setUp(self) -> None:
        self.raiz_temporal = RAIZ_PROYECTO / "tests" / f"_tmp_configuracion_{uuid.uuid4().hex}"
        (self.raiz_temporal / "database" / "migrations").mkdir(parents=True, exist_ok=True)
        for ruta in (RAIZ_PROYECTO / "database" / "migrations").glob("*.sql"):
            (self.raiz_temporal / "database" / "migrations" / ruta.name).write_text(
                ruta.read_text(encoding="utf-8"),
                encoding="utf-8",
            )
        self.gestor_rutas = GestorRutas(raiz_proyecto=self.raiz_temporal)
        self.gestor_base_datos = GestorBaseDatos(self.gestor_rutas)
        self.gestor_base_datos.inicializar_base_datos()
        self.repositorio = RepositorioConfiguracionSQLite(self.gestor_base_datos)
        self.servicio = ServicioConfiguracion(self.repositorio, self.gestor_rutas)

    def tearDown(self) -> None:
        shutil.rmtree(self.raiz_temporal, ignore_errors=True)

    def test_estado_inicial_refleja_parametros_reales(self) -> None:
        estado = self.servicio.obtener_estado()

        self.assertTrue(estado.parametros_cobro.mora_visible)
        self.assertFalse(estado.parametros_cobro.multa_mora_automatica_activa)
        self.assertFalse(estado.parametros_cobro.corte_automatico_activo)
        self.assertEqual(estado.parametros_cobro.meses_para_corte, 5)
        self.assertTrue(estado.parametros_cobro.permitir_pago_adelantado)
        self.assertEqual(estado.parametros_cobro.meses_adelanto_maximo, 12)
        self.assertEqual(estado.parametros_cobro.mora_leve_hasta_meses, 2)
        self.assertEqual(estado.parametros_cobro.mora_media_hasta_meses, 5)
        self.assertEqual(estado.factura.formato_salida, "HTML")
        self.assertEqual(estado.factura.titulo_documento, "RECIBO DE PAGO")
        self.assertEqual(estado.factura.etiqueta_copia, "ORIGINAL")
        self.assertTrue(estado.factura.correlativo_actual.startswith("REC-"))
        self.assertEqual(estado.operacion.total_respaldos, 0)
        self.assertEqual(estado.informacion.version_sistema, "2.2.0")
        self.assertEqual(estado.seguridad.maximo_intentos_fallidos, 5)

    def test_guardado_datos_junta_y_cobro_actualiza_base(self) -> None:
        resultado_junta = self.servicio.guardar_datos_junta(
            nombre="Junta Nueva",
            telefono="9999-0000",
            correo="junta@local.test",
            direccion="Centro de Yarumela",
            identificador_fiscal="08011900123456",
            sitio_web="www.junta.test",
            mensaje_contacto="Atencion administrativa de lunes a viernes.",
            actor_id=1,
        )
        resultado_cobro = self.servicio.guardar_parametros_cobro(
            precio_mensual_centavos=3200,
            multa_mora_automatica_activa=True,
            multa_mora_automatica_centavos=450,
            corte_automatico_activo=True,
            meses_para_corte=3,
            permitir_pago_adelantado=True,
            meses_adelanto_maximo=6,
            mora_leve_hasta_meses=2,
            mora_media_hasta_meses=4,
            actor_id=1,
        )

        self.assertTrue(resultado_junta.exito)
        self.assertTrue(resultado_cobro.exito)

        estado = self.servicio.obtener_estado()
        self.assertEqual(estado.datos_junta.nombre, "Junta Nueva")
        self.assertEqual(estado.datos_junta.identificador_fiscal, "08011900123456")
        self.assertEqual(estado.datos_junta.sitio_web, "www.junta.test")
        self.assertEqual(estado.parametros_cobro.precio_mensual_centavos, 3200)
        self.assertTrue(estado.parametros_cobro.multa_mora_automatica_activa)
        self.assertEqual(estado.parametros_cobro.multa_mora_automatica_centavos, 450)
        self.assertTrue(estado.parametros_cobro.corte_automatico_activo)
        self.assertEqual(estado.parametros_cobro.meses_para_corte, 3)
        self.assertTrue(estado.parametros_cobro.permitir_pago_adelantado)
        self.assertEqual(estado.parametros_cobro.meses_adelanto_maximo, 6)
        self.assertEqual(estado.parametros_cobro.mora_leve_hasta_meses, 2)
        self.assertEqual(estado.parametros_cobro.mora_media_hasta_meses, 4)

    def test_guardado_factura_y_respaldo_actualiza_base(self) -> None:
        resultado_factura = self.servicio.guardar_parametros_factura(
            titulo_documento="RECIBO OFICIAL DE PAGO",
            subtitulo_documento="Junta de Agua",
            texto_legal_superior="No es factura de deuda.",
            texto_pie="Conserve este comprobante.",
            texto_legal_inferior="No se aceptan anulaciones desde caja.",
            etiqueta_copia="ORIGINAL",
            formato_salida="html",
            mostrar_correo=True,
            mostrar_telefono=True,
            mostrar_direccion=True,
            mostrar_identificador_fiscal=True,
            actor_id=1,
        )
        resultado_respaldo = self.servicio.guardar_operacion_respaldo(
            respaldo_automatico=True,
            actor_id=1,
        )

        self.assertTrue(resultado_factura.exito)
        self.assertTrue(resultado_respaldo.exito)

        estado = self.servicio.obtener_estado()
        self.assertEqual(estado.factura.titulo_documento, "RECIBO OFICIAL DE PAGO")
        self.assertEqual(estado.factura.texto_pie, "Conserve este comprobante.")
        self.assertEqual(estado.factura.formato_salida, "HTML")
        self.assertTrue(estado.factura.mostrar_identificador_fiscal)
        self.assertTrue(estado.operacion.respaldo_automatico)

    def test_no_permite_meses_corte_invalido(self) -> None:
        resultado = self.servicio.guardar_parametros_cobro(
            precio_mensual_centavos=2500,
            multa_mora_automatica_activa=False,
            multa_mora_automatica_centavos=0,
            corte_automatico_activo=False,
            meses_para_corte=0,
            permitir_pago_adelantado=False,
            meses_adelanto_maximo=0,
            mora_leve_hasta_meses=2,
            mora_media_hasta_meses=5,
            actor_id=1,
        )

        self.assertFalse(resultado.exito)
        self.assertEqual(resultado.codigo, "VALIDACION")

    def test_no_permite_adelantos_sin_limite_valido(self) -> None:
        resultado = self.servicio.guardar_parametros_cobro(
            precio_mensual_centavos=2500,
            multa_mora_automatica_activa=False,
            multa_mora_automatica_centavos=0,
            corte_automatico_activo=False,
            meses_para_corte=5,
            permitir_pago_adelantado=True,
            meses_adelanto_maximo=0,
            mora_leve_hasta_meses=2,
            mora_media_hasta_meses=5,
            actor_id=1,
        )

        self.assertFalse(resultado.exito)
        self.assertEqual(resultado.codigo, "VALIDACION")

    def test_no_permite_rangos_de_mora_invalidos(self) -> None:
        resultado = self.servicio.guardar_parametros_cobro(
            precio_mensual_centavos=2500,
            multa_mora_automatica_activa=False,
            multa_mora_automatica_centavos=0,
            corte_automatico_activo=False,
            meses_para_corte=5,
            permitir_pago_adelantado=False,
            meses_adelanto_maximo=0,
            mora_leve_hasta_meses=3,
            mora_media_hasta_meses=3,
            actor_id=1,
        )

        self.assertFalse(resultado.exito)
        self.assertEqual(resultado.codigo, "VALIDACION")


if __name__ == "__main__":
    unittest.main()
