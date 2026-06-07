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
from modulos.documentos.generadores.generador_pdf_reportlab import GeneradorPdfReportLab  # noqa: E402
from modulos.documentos.modelos.dto_estado_cuenta import (  # noqa: E402
    CasaEstadoCuenta,
    DTOEstadoCuenta,
    LineaDetalleEstadoCuenta,
)
from modulos.documentos import ServicioReportePdf  # noqa: E402
from modulos.documentos.modelos.dto_reporte_tabular import DTOReporteTabular  # noqa: E402
from modulos.pagos.repositorio import RepositorioPagosSQLite  # noqa: E402
from modulos.pagos.servicio import ServicioPagos  # noqa: E402
from modulos.reportes.repositorio import RepositorioReportesSQLite  # noqa: E402
from modulos.reportes.servicio import ServicioReportes  # noqa: E402
from reportlab.lib import colors  # noqa: E402
from reportlab.lib.units import mm  # noqa: E402
from reportlab.platypus import Paragraph, Spacer, Table  # noqa: E402


class TestDocumentosPdf(unittest.TestCase):
    def setUp(self) -> None:
        self.raiz_temporal = RAIZ_PROYECTO / "tests" / f"_tmp_docs_{uuid.uuid4().hex}"
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
        self.servicio_reporte_pdf = ServicioReportePdf(gestor_rutas=self.gestor_rutas)

    def tearDown(self) -> None:
        shutil.rmtree(self.raiz_temporal, ignore_errors=True)

    def test_generador_pdf_ya_no_expone_comprobantes_de_pago(self) -> None:
        generador = GeneradorPdfReportLab()

        self.assertFalse(hasattr(generador, "generar_comprobante_pago"))

    def test_servicio_reporte_pdf_genera_pdf_tabular(self) -> None:
        servicio_reportes = ServicioReportes(RepositorioReportesSQLite(self.gestor_base_datos))
        estado = servicio_reportes.obtener_estado(
            codigo_reporte="servicio_casas",
            filtros={"fecha_desde": "2026-01-01", "fecha_hasta": "2026-12-31"},
        )
        assert estado.tabla_actual is not None
        tabla = estado.tabla_actual
        ruta_pdf = self.servicio_reporte_pdf.generar_pdf(
            tabla=tabla,
            fecha_desde="2026-01-01",
            fecha_hasta="2026-12-31",
            lineas_encabezado=("SIGQUA", "Junta de Agua de Yarumela"),
            directorio_destino=str(self.raiz_temporal / "salida_reportes"),
            generado_por="Administrador",
            firma_habilitada=True,
        )

        self.assertTrue(Path(ruta_pdf).exists())
        self.assertTrue(Path(ruta_pdf).read_bytes().startswith(b"%PDF"))
        self.assertIn("SIGQUA_SERVICIO_CASAS_", Path(ruta_pdf).name)

    def test_dto_reporte_incluye_usuario_resumen_y_firma(self) -> None:
        servicio_reportes = ServicioReportes(RepositorioReportesSQLite(self.gestor_base_datos))
        tabla = servicio_reportes.obtener_estado(codigo_reporte="servicio_casas").tabla_actual
        assert tabla is not None

        dto = self.servicio_reporte_pdf.construir_dto(
            tabla=tabla,
            fecha_desde="",
            fecha_hasta="",
            lineas_encabezado=("Junta de Agua",),
            generado_por="Maria Operadora",
            firma_habilitada=True,
            firma_texto_linea="Responsable administrativo",
        )

        self.assertEqual(dto.generado_por, "Maria Operadora")
        self.assertTrue(dto.resumen)
        self.assertTrue(dto.firma_habilitada)
        self.assertEqual(dto.firma_texto_linea, "Responsable administrativo")

    def test_generador_usa_anchos_especificos_y_soporta_reporte_vacio(self) -> None:
        generador = GeneradorPdfReportLab()
        dto = DTOReporteTabular(
            codigo_reporte="deuda_abonados_estado",
            titulo="Deuda",
            descripcion="",
            columnas=("DNI", "Abonado", "Barrio", "Casas", "Meses", "Deuda", "Estado"),
            filas=(),
            fecha_desde="",
            fecha_hasta="",
            generado_en="2026-06-06 10:00:00",
            generado_por="Sistema",
            lineas_encabezado=("SIGQUA",),
            resumen=(("Abonados listados", "0"), ("Deuda consolidada", "L 0.00")),
            orientacion="HORIZONTAL",
        )

        tabla = generador._crear_tabla_reporte(dto)

        self.assertGreater(len(set(round(ancho, 2) for ancho in tabla._colWidths)), 1)
        self.assertEqual(len(tabla._cellvalues), 2)

    def test_reporte_aplica_jerarquia_institucional_totales_y_firma(self) -> None:
        generador = GeneradorPdfReportLab()
        dto = DTOReporteTabular(
            codigo_reporte="deuda_abonados_estado",
            titulo="Deuda total por abonados",
            descripcion="Deuda administrativa consolidada.",
            columnas=("DNI", "Abonado", "Barrio", "Casas", "Meses", "Deuda", "Estado"),
            filas=(
                (
                    "0801199012345",
                    "Victor Hugo Lopez Hernandez",
                    "Barrio El Centro",
                    "2",
                    "3",
                    "L 450.00",
                    "ACTIVO",
                ),
            ),
            fecha_desde="",
            fecha_hasta="",
            generado_en="2026-06-06 10:00:00",
            generado_por="Administrador",
            lineas_encabezado=(
                "Junta de Agua de Yarumela",
                "Telefono 2774-0000",
                "yarumela@example.com",
            ),
            resumen=(
                ("Abonados listados", "1"),
                ("Deuda consolidada", "L 450.00"),
            ),
            orientacion="HORIZONTAL",
            firma_habilitada=True,
            firma_texto_linea="Firma autorizada",
        )

        encabezado = generador._crear_encabezado_reporte(dto)
        nombre_junta = encabezado._cellvalues[0][0][0]
        tabla = generador._crear_tabla_reporte(dto)
        resumen = generador._crear_resumen_reporte(dto.resumen)
        firma = generador._construir_bloque_firma(True, dto.firma_texto_linea)

        self.assertEqual(nombre_junta.text, "JUNTA DE AGUA DE YARUMELA")
        self.assertEqual(nombre_junta.style.fontName, "Helvetica-Bold")
        self.assertGreaterEqual(nombre_junta.style.fontSize, 15)
        self.assertTrue(
            any(comando[0] == "LINEBELOW" and comando[3] >= 1.5 for comando in encabezado._linecmds)
        )
        self.assertIsInstance(tabla._cellvalues[1][1], Paragraph)
        self.assertEqual(tabla._cellvalues[1][1].text, "Victor Hugo Lopez Hernandez")
        self.assertEqual(resumen._cellvalues[1][0].text, "DEUDA CONSOLIDADA")
        self.assertEqual(resumen._cellvalues[1][0].style.textColor, colors.white)
        self.assertGreater(resumen._cellvalues[1][0].style.fontSize, 8)
        self.assertTrue(
            any(
                comando[0] == "BACKGROUND" and comando[3] == colors.HexColor("#202020")
                for comando in resumen._bkgrndcmds
            )
        )
        self.assertIsInstance(firma[0], Spacer)
        self.assertGreaterEqual(firma[0].height, 10 * mm)
        self.assertEqual(firma[-1].style.alignment, 1)

    def test_los_tres_reportes_generan_pdf_con_nuevo_diseno(self) -> None:
        servicio_reportes = ServicioReportes(RepositorioReportesSQLite(self.gestor_base_datos))
        codigos = (
            "deuda_abonados_estado",
            "servicio_casas",
            "ingresos_mensuales_diarios",
        )
        rutas: list[Path] = []

        for codigo in codigos:
            with self.subTest(codigo=codigo):
                tabla = servicio_reportes.obtener_estado(
                    codigo_reporte=codigo,
                    filtros={"fecha_desde": "2026-01-01", "fecha_hasta": "2026-12-31"},
                ).tabla_actual
                assert tabla is not None
                ruta = Path(
                    self.servicio_reporte_pdf.generar_pdf(
                        tabla=tabla,
                        fecha_desde="2026-01-01",
                        fecha_hasta="2026-12-31",
                        lineas_encabezado=(
                            "Junta de Agua de Yarumela",
                            "Telefono 2774-0000",
                            "yarumela@example.com",
                            "Yarumela, La Paz",
                        ),
                        directorio_destino=str(self.raiz_temporal / "tres_reportes"),
                        generado_por="Administrador",
                        firma_habilitada=True,
                    )
                )
                rutas.append(ruta)
                self.assertTrue(ruta.exists())
                self.assertTrue(ruta.read_bytes().startswith(b"%PDF"))

        self.assertEqual(len(rutas), 3)

    def test_nombre_fechado_no_sobrescribe_colision(self) -> None:
        servicio_reportes = ServicioReportes(RepositorioReportesSQLite(self.gestor_base_datos))
        tabla = servicio_reportes.obtener_estado(codigo_reporte="servicio_casas").tabla_actual
        assert tabla is not None
        directorio = self.raiz_temporal / "colisiones"

        primera = self.servicio_reporte_pdf.generar_pdf(
            tabla=tabla,
            fecha_desde="",
            fecha_hasta="",
            lineas_encabezado=("SIGQUA",),
            directorio_destino=str(directorio),
        )
        segunda = self.servicio_reporte_pdf.generar_pdf(
            tabla=tabla,
            fecha_desde="",
            fecha_hasta="",
            lineas_encabezado=("SIGQUA",),
            directorio_destino=str(directorio),
        )

        self.assertNotEqual(primera, segunda)
        self.assertTrue(Path(segunda).stem.endswith("_2"))

    def test_ruta_no_escribible_usa_fallback_interno(self) -> None:
        servicio_reportes = ServicioReportes(RepositorioReportesSQLite(self.gestor_base_datos))
        tabla = servicio_reportes.obtener_estado(codigo_reporte="servicio_casas").tabla_actual
        assert tabla is not None
        ruta_invalida = self.raiz_temporal / "no_es_directorio"
        ruta_invalida.write_text("archivo", encoding="utf-8")

        resultado = self.servicio_reporte_pdf.generar_pdf_con_resultado(
            tabla=tabla,
            fecha_desde="",
            fecha_hasta="",
            lineas_encabezado=("SIGQUA",),
            directorio_destino=str(ruta_invalida),
        )

        self.assertTrue(resultado.uso_fallback)
        self.assertEqual(
            Path(resultado.ruta).parent,
            self.gestor_rutas.obtener_ruta_exportaciones_reportes(),
        )
        self.assertTrue(Path(resultado.ruta).exists())

    def test_servicio_reporte_pdf_rechaza_fecha_emision_fuera_del_dia_actual(self) -> None:
        servicio_reportes = ServicioReportes(RepositorioReportesSQLite(self.gestor_base_datos))
        estado = servicio_reportes.obtener_estado(
            codigo_reporte="servicio_casas",
            filtros={"fecha_desde": "2026-01-01", "fecha_hasta": "2026-12-31"},
        )
        assert estado.tabla_actual is not None
        tabla = estado.tabla_actual

        with self.assertRaises(ValueError):
            self.servicio_reporte_pdf.construir_dto(
                tabla=tabla,
                fecha_desde="2026-01-01",
                fecha_hasta="2026-12-31",
                lineas_encabezado=("SIGQUA",),
                generado_en="2020-01-01 08:00:00",
            )

    def test_estado_cuenta_no_duplica_totales_generales_con_una_sola_casa(self) -> None:
        generador = GeneradorPdfReportLab()
        dto = DTOEstadoCuenta(
            titulo="DOCUMENTO DE DEUDA",
            subtitulo="Detalle operativo generado desde morosidad",
            lineas_encabezado=("SIGQUA",),
            abonado_nombre="Julio Perdomo",
            abonado_dni="0801199402022",
            generado_en="20/05/2026 08:00",
            observacion="Documento de consulta operativa.",
            casas=(
                CasaEstadoCuenta(
                    casa_codigo="CA-007",
                    barrio_nombre="La Laguna",
                    direccion_casa="Casa blanca",
                    estado_servicio="ACTIVO",
                    meses_vencidos=1,
                    dias_en_mora=38,
                    prioridad="Baja",
                    vencimiento_mas_antiguo="10/04/2026",
                    deuda_base="L 150.00",
                    recargo_mora="L 30.00",
                    deuda_total="L 180.00",
                    lineas_detalle=(
                        LineaDetalleEstadoCuenta(
                            descripcion="Mensualidad en mora 04/2026",
                            fecha_vencimiento="10/04/2026",
                            monto="L 150.00",
                        ),
                    ),
                ),
            ),
            total_deuda_base="L 150.00",
            total_recargo_mora="L 30.00",
            total_general="L 180.00",
            firma_habilitada=False,
            firma_texto_linea="Firma autorizada",
        )

        elementos = generador._construir_elementos_estado_cuenta(dto)
        tablas = [elemento for elemento in elementos if isinstance(elemento, Table)]

        self.assertEqual(len(tablas), 3)

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

