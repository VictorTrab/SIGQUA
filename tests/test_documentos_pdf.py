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
from modulos.documentos import ServicioComprobantePago, ServicioReportePdf  # noqa: E402
from modulos.pagos.entidades import FormularioPago  # noqa: E402
from modulos.pagos.repositorio import RepositorioPagosSQLite  # noqa: E402
from modulos.pagos.servicio import ServicioPagos  # noqa: E402
from modulos.reportes.repositorio import RepositorioReportesSQLite  # noqa: E402


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
        self.ruta_db = self.gestor_base_datos.inicializar_base_datos()
        self.repositorio_pagos = RepositorioPagosSQLite(self.gestor_base_datos)
        self.servicio_pagos = ServicioPagos(self.repositorio_pagos, gestor_rutas=self.gestor_rutas)
        self.servicio_comprobantes = ServicioComprobantePago(gestor_rutas=self.gestor_rutas)
        self.servicio_reporte_pdf = ServicioReportePdf(gestor_rutas=self.gestor_rutas)

    def tearDown(self) -> None:
        shutil.rmtree(self.raiz_temporal, ignore_errors=True)

    def test_servicio_comprobante_pago_construye_pdf_desde_datos_reales(self) -> None:
        casa_id = self._obtener_casa_por_dni("0801199000022")
        metodo_id = self._obtener_metodo("EFECTIVO")
        resultado = self.servicio_pagos.registrar_pago(
            FormularioPago(
                casa_id=casa_id,
                tipo_pago="MENSUALIDAD",
                cantidad_meses=1,
                metodo_pago_id=metodo_id,
            ),
            actor_id=1,
        )
        assert resultado.comprobante is not None
        comprobante = self.servicio_pagos.obtener_comprobante(resultado.comprobante.pago_id)
        assert comprobante is not None
        configuracion = self.servicio_pagos.obtener_configuracion_recibo()

        ruta_pdf = self.servicio_comprobantes.generar_pdf(
            comprobante=comprobante,
            configuracion=configuracion,
            formateador_moneda=self.servicio_pagos.formatear_moneda,
            formateador_fecha=self.servicio_pagos.formatear_fecha,
            formateador_hora=self.servicio_pagos.formatear_hora,
            etiqueta_tipo_pago=self.servicio_pagos._etiqueta_tipo_pago,
        )

        self.assertTrue(Path(ruta_pdf).exists())
        self.assertTrue(Path(ruta_pdf).read_bytes().startswith(b"%PDF"))

    def test_servicio_reporte_pdf_genera_pdf_tabular(self) -> None:
        servicio_reportes = RepositorioReportesSQLite(self.gestor_base_datos)
        estado = servicio_reportes.obtener_estado(fecha_desde="2026-01-01", fecha_hasta="2026-12-31")
        tabla = next(tabla for tabla in estado.tablas if tabla.codigo == "casas_estado")
        ruta_pdf = self.servicio_reporte_pdf.generar_pdf(
            tabla=tabla,
            fecha_desde="2026-01-01",
            fecha_hasta="2026-12-31",
            lineas_encabezado=("SICAP", "Junta de Agua de Yarumela"),
        )

        self.assertTrue(Path(ruta_pdf).exists())
        self.assertTrue(Path(ruta_pdf).read_bytes().startswith(b"%PDF"))

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
