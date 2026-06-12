from __future__ import annotations

import json
import os
import shutil
import sqlite3
import sys
import unittest
import uuid
from pathlib import Path
import zipfile


RAIZ_PROYECTO = Path(__file__).resolve().parents[1]
RUTA_SRC = RAIZ_PROYECTO / "src"

if str(RUTA_SRC) not in sys.path:
    sys.path.insert(0, str(RUTA_SRC))

from comun.base_datos import GestorBaseDatos  # noqa: E402
from comun.configuracion.gestor_rutas import GestorRutas  # noqa: E402
from comun.respaldo import ConfiguracionRespaldoLocal, ServicioRespaldoLocal  # noqa: E402
from modulos.configuracion.repositorio import RepositorioConfiguracionSQLite  # noqa: E402
from modulos.configuracion.servicio import ServicioConfiguracion  # noqa: E402
from tests.utilidades_base_datos import inicializar_base_datos_prueba  # noqa: E402


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
        inicializar_base_datos_prueba(self.gestor_base_datos)
        self.repositorio = RepositorioConfiguracionSQLite(self.gestor_base_datos)
        self.servicio_respaldo = ServicioRespaldoLocal(
            gestor_base_datos=self.gestor_base_datos,
            gestor_rutas=self.gestor_rutas,
        )
        self.servicio = ServicioConfiguracion(
            self.repositorio,
            self.gestor_rutas,
            servicio_respaldo=self.servicio_respaldo,
        )

    def tearDown(self) -> None:
        shutil.rmtree(self.raiz_temporal, ignore_errors=True)

    def test_estado_inicial_refleja_parametros_reales(self) -> None:
        estado = self.servicio.obtener_estado()

        self.assertTrue(estado.parametros_cobro.mora_visible)
        self.assertFalse(estado.parametros_cobro.multa_mora_automatica_activa)
        self.assertFalse(estado.parametros_cobro.corte_automatico_activo)
        self.assertEqual(estado.parametros_cobro.meses_para_corte, 5)
        self.assertFalse(estado.parametros_cobro.cobrar_mensualidad_prorrateada_activacion)
        self.assertTrue(estado.parametros_cobro.permitir_pago_adelantado)
        self.assertEqual(estado.parametros_cobro.mora_leve_hasta_meses, 2)
        self.assertEqual(estado.parametros_cobro.mora_media_hasta_meses, 5)
        self.assertEqual(estado.factura.titulo_documento, "RECIBO DE PAGO")
        self.assertEqual(estado.factura.etiqueta_copia, "ORIGINAL")
        self.assertFalse(estado.factura.firma_habilitada)
        self.assertEqual(estado.factura.firma_texto_linea, "Firma autorizada")
        self.assertEqual(estado.factura.impresora_termica_nombre, "")
        self.assertEqual(estado.factura.impresora_termica_ancho_mm, 80)
        self.assertTrue(estado.factura.impresora_termica_corte_automatico)
        self.assertEqual(estado.factura.impresora_termica_codigo_pagina, "cp850")
        self.assertEqual(estado.factura.impresora_reportes_nombre, "")
        self.assertEqual(
            estado.reportes_pdf.ruta_salida,
            str(self.gestor_rutas.obtener_ruta_reportes_predeterminada()),
        )
        self.assertTrue(estado.reportes_pdf.abrir_automaticamente)
        self.assertFalse(estado.reportes_pdf.firma_habilitada)
        self.assertEqual(estado.reportes_pdf.firma_texto_linea, "Firma autorizada")
        self.assertEqual(estado.factura.comprobantes_pendientes_impresion, 0)
        self.assertTrue(estado.factura.correlativo_actual.startswith("REC-"))
        self.assertEqual(estado.operacion.total_respaldos, 0)
        self.assertEqual(estado.operacion.ruta_respaldos_principal, str(self.gestor_rutas.obtener_ruta_respaldos()))
        self.assertEqual(estado.operacion.retencion_maxima, 5)
        self.assertEqual(estado.seguridad.duracion_sesion_horas, 8.0)
        self.assertEqual(estado.informacion.version_sistema, "2.3.0")
        self.assertEqual(estado.seguridad.maximo_intentos_fallidos, 5)
        self.assertEqual(estado.informacion.actualizado_por, "Sistema")
        self.assertFalse(hasattr(estado, "laboratorio_visual"))
        with sqlite3.connect(self.gestor_rutas.obtener_ruta_base_datos()) as conexion:
            parametros_laboratorio = conexion.execute(
                "SELECT COUNT(*) FROM configuracion_sistema WHERE clave LIKE 'ui.laboratorio.%';"
            ).fetchone()[0]
        self.assertEqual(parametros_laboratorio, 0)

    def test_guardado_datos_junta_y_cobro_actualiza_base(self) -> None:
        resultado_junta = self.servicio.guardar_datos_junta(
            nombre="Empresa Nueva",
            telefono="9999-0000",
            correo="empresa@local.test",
            direccion="Centro de Yarumela",
            identificador_fiscal="08011900123456",
            sitio_web="www.empresa.test",
            mensaje_contacto="Atencion administrativa de lunes a viernes.",
            actor_id=1,
        )
        resultado_cobro = self.servicio.guardar_parametros_cobro(
            precio_mensual_centavos=3200,
            multa_mora_automatica_activa=True,
            multa_mora_automatica_centavos=450,
            corte_automatico_activo=True,
            meses_para_corte=3,
            cobrar_mensualidad_prorrateada_activacion=True,
            permitir_pago_adelantado=True,
            mora_leve_hasta_meses=2,
            mora_media_hasta_meses=4,
            actor_id=1,
        )

        self.assertTrue(resultado_junta.exito)
        self.assertTrue(resultado_cobro.exito)

        estado = self.servicio.obtener_estado()
        self.assertEqual(estado.identidad_empresa.nombre, "Empresa Nueva")
        self.assertEqual(estado.identidad_empresa.identificador_fiscal, "08011900123456")
        self.assertEqual(estado.identidad_empresa.sitio_web, "www.empresa.test")
        self.assertEqual(estado.parametros_cobro.precio_mensual_centavos, 3200)
        self.assertTrue(estado.parametros_cobro.multa_mora_automatica_activa)
        self.assertEqual(estado.parametros_cobro.multa_mora_automatica_centavos, 450)
        self.assertTrue(estado.parametros_cobro.corte_automatico_activo)
        self.assertEqual(estado.parametros_cobro.meses_para_corte, 3)
        self.assertTrue(estado.parametros_cobro.cobrar_mensualidad_prorrateada_activacion)
        self.assertTrue(estado.parametros_cobro.permitir_pago_adelantado)
        self.assertEqual(estado.parametros_cobro.mora_leve_hasta_meses, 2)
        self.assertEqual(estado.parametros_cobro.mora_media_hasta_meses, 4)
        self.assertEqual(estado.informacion.actualizado_por, "Administrador del Sistema")

    def test_guardado_factura_y_sesion_conserva_respaldo_fijo(self) -> None:
        self.repositorio.actualizar_valores(
            {
                "impresion_termica.codigo_pagina": "utf-8",
                "respaldo.comprimir_zip": "0",
                "respaldo.organizar_por_periodo": "1",
            },
            actor_id=1,
        )
        resultado_factura = self.servicio.guardar_parametros_factura(
            titulo_documento="RECIBO OFICIAL DE PAGO",
            texto_pie="Conserve este comprobante.",
            etiqueta_copia="ORIGINAL",
            mostrar_correo=True,
            mostrar_telefono=True,
            mostrar_direccion=True,
            mostrar_identificador_fiscal=True,
            firma_habilitada=True,
            firma_texto_linea="Firma autorizada",
            impresora_termica_nombre="Ticketera Caja",
            impresora_termica_ancho_mm=58,
            impresora_termica_corte_automatico=False,
            impresora_reportes_nombre="Impresora Administrativa",
            actor_id=1,
        )
        resultado_sesion = self.servicio.guardar_duracion_sesion(4.0, actor_id=1)

        self.assertTrue(resultado_factura.exito)
        self.assertTrue(resultado_sesion.exito)

        estado = self.servicio.obtener_estado()
        self.assertEqual(estado.factura.titulo_documento, "RECIBO OFICIAL DE PAGO")
        self.assertEqual(estado.factura.texto_pie, "Conserve este comprobante.")
        self.assertTrue(estado.factura.mostrar_identificador_fiscal)
        self.assertTrue(estado.factura.firma_habilitada)
        self.assertEqual(estado.factura.firma_texto_linea, "Firma autorizada")
        self.assertEqual(estado.factura.impresora_termica_nombre, "Ticketera Caja")
        self.assertEqual(estado.factura.impresora_termica_ancho_mm, 58)
        self.assertFalse(estado.factura.impresora_termica_corte_automatico)
        self.assertEqual(estado.factura.impresora_termica_codigo_pagina, "cp850")
        self.assertEqual(estado.factura.impresora_reportes_nombre, "Impresora Administrativa")
        self.assertTrue(estado.operacion.respaldo_automatico)
        self.assertEqual(estado.operacion.retencion_maxima, 5)
        self.assertEqual(estado.seguridad.duracion_sesion_horas, 4.0)
        parametros_fijos = self.repositorio.listar_por_claves(("impresion_termica.codigo_pagina",))
        self.assertEqual(parametros_fijos["impresion_termica.codigo_pagina"].valor, "cp850")

    def test_guardado_reportes_pdf_actualiza_claves_independientes(self) -> None:
        ruta = self.raiz_temporal / "reportes_personalizados"

        resultado = self.servicio.guardar_reportes_pdf(
            ruta_salida=str(ruta),
            abrir_automaticamente=False,
            firma_habilitada=True,
            firma_texto_linea="Responsable administrativo",
            actor_id=1,
        )

        self.assertTrue(resultado.exito)
        estado = self.servicio.obtener_estado()
        self.assertEqual(estado.reportes_pdf.ruta_salida, str(ruta))
        self.assertFalse(estado.reportes_pdf.abrir_automaticamente)
        self.assertTrue(estado.reportes_pdf.firma_habilitada)
        self.assertEqual(
            estado.reportes_pdf.firma_texto_linea,
            "Responsable administrativo",
        )
        parametros = self.repositorio.listar_por_claves(
            (
                "reportes.ruta_salida",
                "reportes.abrir_automaticamente",
                "reportes.firma_habilitada",
                "reportes.firma_texto_linea",
            )
        )
        self.assertEqual(len(parametros), 4)

    def test_crear_respaldo_automatico_genera_zip_con_hash(self) -> None:
        resultado = self.servicio.crear_respaldo_automatico(actor_id=1)

        self.assertTrue(resultado.exito)
        estado = self.servicio.obtener_estado()
        ruta_respaldo = Path(estado.operacion.ruta_respaldos_principal)
        archivos = list(ruta_respaldo.rglob("SIGQUA_RESPALDO_*.zip"))
        self.assertTrue(archivos)
        with zipfile.ZipFile(archivos[0], "r") as archivo_zip:
            nombres = archivo_zip.namelist()
            self.assertIn("sigqua.db", nombres)
            self.assertIn("manifiesto.json", nombres)
            manifiesto = json.loads(archivo_zip.read("manifiesto.json").decode("utf-8"))
        self.assertEqual(manifiesto["tipo_respaldo"], "AUTOMATICO")
        self.assertTrue(manifiesto["sha256_base_datos"])
        self.assertTrue(estado.operacion.total_respaldos >= 1)
        self.assertEqual(estado.operacion.ultimo_respaldo_generado_por, "Sistema local")
        self.assertEqual(estado.operacion.retencion_maxima, 5)

    def test_retencion_conserva_solo_cinco_respaldos_recientes(self) -> None:
        ruta_respaldos = self.gestor_rutas.obtener_ruta_respaldos()
        ruta_respaldos.mkdir(parents=True, exist_ok=True)
        for indice in range(7):
            archivo = ruta_respaldos / f"SIGQUA_RESPALDO_PRUEBA_{indice}.zip"
            archivo.write_bytes(b"contenido")
            marca_tiempo = 1_700_000_000 + indice

            os.utime(archivo, (marca_tiempo, marca_tiempo))

        self.servicio_respaldo.aplicar_retencion(
            ConfiguracionRespaldoLocal(
                ruta_principal=str(ruta_respaldos),
                retencion_maxima=5,
                version_sistema="test",
            )
        )

        archivos = sorted(archivo.name for archivo in ruta_respaldos.glob("SIGQUA_RESPALDO_PRUEBA_*.zip"))
        self.assertEqual(
            archivos,
            [f"SIGQUA_RESPALDO_PRUEBA_{indice}.zip" for indice in range(2, 7)],
        )

    def test_restaurar_respaldo_externo_reemplaza_base_sin_eventos_sqlite(self) -> None:
        resultado_respaldo = self.servicio.crear_respaldo_automatico(actor_id=1)
        self.assertTrue(resultado_respaldo.exito)
        ruta_generada = next(
            self.gestor_rutas.obtener_ruta_respaldos().glob("SIGQUA_RESPALDO_*.zip")
        )
        ruta_externa = self.raiz_temporal / "respaldo_externo.zip"
        shutil.copy2(ruta_generada, ruta_externa)

        with sqlite3.connect(self.gestor_rutas.obtener_ruta_base_datos()) as conexion:
            conexion.execute("CREATE TABLE marcador_post_respaldo(id INTEGER PRIMARY KEY);")
            conexion.commit()

        resultado = self.servicio.restaurar_respaldo_externo(str(ruta_externa), actor_id=1)

        self.assertTrue(resultado.exito)
        with sqlite3.connect(self.gestor_rutas.obtener_ruta_base_datos()) as conexion:
            marcador = conexion.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'marcador_post_respaldo';"
            ).fetchone()
            tabla_eventos = conexion.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'eventos_tecnicos';"
            ).fetchone()
        self.assertIsNone(marcador)
        archivos_seguridad = list(
            self.gestor_rutas.obtener_ruta_respaldos().glob("SIGQUA_RESPALDO_*.zip")
        )
        self.assertGreaterEqual(len(archivos_seguridad), 2)
        self.assertIsNone(tabla_eventos)

    def test_restaurar_respaldo_externo_rechaza_ruta_extension_y_zip_invalidos(self) -> None:
        ruta_respaldos = self.gestor_rutas.obtener_ruta_respaldos()
        ruta_respaldos.mkdir(parents=True, exist_ok=True)

        ruta_zip_invalido = ruta_respaldos / "SIGQUA_RESPALDO_ZIP_INVALIDO.zip"
        ruta_zip_invalido.write_bytes(b"no es zip")
        ruta_db = ruta_respaldos / "SIGQUA_RESPALDO_INVALIDO.db"
        ruta_db.write_bytes(b"contenido")

        faltante = self.servicio.restaurar_respaldo_externo(
            str(ruta_respaldos / "SIGQUA_RESPALDO_FALTANTE.zip"),
            actor_id=1,
        )
        extension = self.servicio.restaurar_respaldo_externo(str(ruta_db), actor_id=1)
        zip_invalido = self.servicio.restaurar_respaldo_externo(
            str(ruta_zip_invalido),
            actor_id=1,
        )

        self.assertFalse(faltante.exito)
        self.assertEqual(faltante.codigo, "VALIDACION")
        self.assertFalse(extension.exito)
        self.assertEqual(extension.codigo, "VALIDACION")
        self.assertFalse(zip_invalido.exito)
        self.assertEqual(zip_invalido.codigo, "ERROR_RESTAURACION")

        with sqlite3.connect(self.gestor_rutas.obtener_ruta_base_datos()) as conexion:
            tabla_eventos = conexion.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'eventos_tecnicos';"
            ).fetchone()
        self.assertIsNone(tabla_eventos)

    def test_firma_visual_vacia_usa_texto_predeterminado(self) -> None:
        self.repositorio.actualizar_valores(
            {
                "factura.subtitulo_documento": "Texto conservado",
                "factura.texto_legal_superior": "Legal superior conservado",
                "factura.texto_legal_inferior": "Legal inferior conservado",
            },
            actor_id=1,
        )
        resultado = self.servicio.guardar_parametros_factura(
            titulo_documento="RECIBO",
            texto_pie="Pie",
            etiqueta_copia="ORIGINAL",
            mostrar_correo=True,
            mostrar_telefono=True,
            mostrar_direccion=True,
            mostrar_identificador_fiscal=False,
            firma_habilitada=True,
            firma_texto_linea="",
            actor_id=1,
        )

        self.assertTrue(resultado.exito)
        factura = self.servicio.obtener_estado().factura
        self.assertEqual(factura.firma_texto_linea, "Firma autorizada")
        self.assertEqual(factura.subtitulo_documento, "Texto conservado")
        self.assertEqual(factura.texto_legal_superior, "Legal superior conservado")
        self.assertEqual(factura.texto_legal_inferior, "Legal inferior conservado")

    def test_no_permite_meses_corte_invalido(self) -> None:
        resultado = self.servicio.guardar_parametros_cobro(
            precio_mensual_centavos=2500,
            multa_mora_automatica_activa=False,
            multa_mora_automatica_centavos=0,
            corte_automatico_activo=False,
            meses_para_corte=0,
            cobrar_mensualidad_prorrateada_activacion=False,
            permitir_pago_adelantado=False,
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
            cobrar_mensualidad_prorrateada_activacion=False,
            permitir_pago_adelantado=False,
            mora_leve_hasta_meses=3,
            mora_media_hasta_meses=3,
            actor_id=1,
        )

        self.assertFalse(resultado.exito)
        self.assertEqual(resultado.codigo, "VALIDACION")

if __name__ == "__main__":
    unittest.main()

