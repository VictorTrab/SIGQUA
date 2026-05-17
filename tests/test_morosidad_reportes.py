from __future__ import annotations

import os
import shutil
import sqlite3
import sys
import unittest
import uuid
from pathlib import Path


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

RAIZ_PROYECTO = Path(__file__).resolve().parents[1]
RUTA_SRC = RAIZ_PROYECTO / "src"

if str(RUTA_SRC) not in sys.path:
    sys.path.insert(0, str(RUTA_SRC))

from PySide6.QtWidgets import QApplication  # noqa: E402

from comun.base_datos import GestorBaseDatos  # noqa: E402
from comun.configuracion.gestor_rutas import GestorRutas  # noqa: E402
from modulos.morosidad.entidades import FILTRO_MOROSIDAD_SEVERA  # noqa: E402
from modulos.morosidad.repositorio import RepositorioMorosidadSQLite  # noqa: E402
from modulos.morosidad.servicio import ServicioMorosidad  # noqa: E402
from modulos.morosidad.vista import VistaMorosidad  # noqa: E402
from modulos.reportes.repositorio import RepositorioReportesSQLite  # noqa: E402
from modulos.reportes.servicio import ServicioReportes  # noqa: E402
from modulos.reportes.vista import VistaReportes  # noqa: E402


class TestMorosidadReportes(unittest.TestCase):
    def setUp(self) -> None:
        self.raiz_temporal = RAIZ_PROYECTO / "tests" / f"_tmp_mr_{uuid.uuid4().hex}"
        (self.raiz_temporal / "database" / "migrations").mkdir(parents=True, exist_ok=True)
        for ruta in (RAIZ_PROYECTO / "database" / "migrations").glob("*.sql"):
            (self.raiz_temporal / "database" / "migrations" / ruta.name).write_text(
                ruta.read_text(encoding="utf-8"),
                encoding="utf-8",
            )
        self.gestor_rutas = GestorRutas(raiz_proyecto=self.raiz_temporal)
        self.gestor_base_datos = GestorBaseDatos(self.gestor_rutas)
        self.gestor_base_datos.inicializar_base_datos()

    def tearDown(self) -> None:
        shutil.rmtree(self.raiz_temporal, ignore_errors=True)

    def test_morosidad_lista_casas_con_severidad_y_totales(self) -> None:
        servicio = ServicioMorosidad(
            RepositorioMorosidadSQLite(self.gestor_base_datos),
            gestor_rutas=self.gestor_rutas,
        )

        estado = servicio.obtener_estado()

        self.assertGreaterEqual(estado.resumen.total_casas, 1)
        self.assertGreaterEqual(estado.resumen.deuda_total_centavos, estado.resumen.deuda_base_centavos)
        self.assertTrue(all(fila.deuda_total_centavos > 0 for fila in estado.pagina.items))
        self.assertTrue(all(fila.severidad in {"LEVE", "MEDIA", "SEVERA"} for fila in estado.pagina.items))

    def test_morosidad_respeta_umbral_visual_configurable(self) -> None:
        with sqlite3.connect(self.gestor_rutas.obtener_ruta_base_datos()) as conexion:
            conexion.row_factory = sqlite3.Row
            fila_base = conexion.execute(
                """
                SELECT b.id AS barrio_id, cc.id AS concepto_id
                FROM barrios b
                CROSS JOIN conceptos_cobro cc
                WHERE cc.codigo = 'SERVICIO_MENSUAL'
                ORDER BY b.id ASC
                LIMIT 1;
                """
            ).fetchone()
            self.assertIsNotNone(fila_base)
            assert fila_base is not None
            conexion.execute(
                """
                INSERT INTO abonados(nombre_completo, dni, telefono, barrio_id, direccion_referencia, estado)
                VALUES ('Abonado Morosidad Prueba', '0801190012345', '0000-0000', ?, 'Casa de prueba para severidad', 'ACTIVO');
                """
                ,
                (fila_base["barrio_id"],),
            )
            abonado_id = int(conexion.execute("SELECT last_insert_rowid();").fetchone()[0])
            conexion.execute(
                """
                INSERT INTO casas(abonado_id, barrio_id, direccion_referencia, estado_servicio)
                VALUES (?, ?, 'Casa de prueba para severidad', 'ACTIVO');
                """,
                (abonado_id, fila_base["barrio_id"]),
            )
            casa_id = int(conexion.execute("SELECT last_insert_rowid();").fetchone()[0])
            for indice, vencimiento in enumerate(("2026-01-05", "2026-02-05", "2026-03-05"), start=1):
                conexion.execute(
                    """
                    INSERT INTO cargos(
                        casa_id, abonado_id, periodo_id, concepto_id, descripcion,
                        monto_centavos, saldo_pendiente_centavos, fecha_vencimiento, estado, origen
                    ) VALUES (?, ?, NULL, ?, ?, ?, ?, ?, 'VENCIDO', 'MENSUAL');
                    """,
                    (
                        casa_id,
                        abonado_id,
                        fila_base["concepto_id"],
                        f"Mensualidad de prueba {indice}",
                        15000,
                        15000,
                        vencimiento,
                    ),
                )
            conexion.execute(
                "UPDATE configuracion_sistema SET valor = '1' WHERE clave = 'cobro.mora_leve_hasta_meses';"
            )
            conexion.execute(
                "UPDATE configuracion_sistema SET valor = '2' WHERE clave = 'cobro.mora_media_hasta_meses';"
            )
            conexion.commit()

        servicio = ServicioMorosidad(
            RepositorioMorosidadSQLite(self.gestor_base_datos),
            gestor_rutas=self.gestor_rutas,
        )
        estado = servicio.obtener_estado()

        self.assertTrue(any(fila.meses_vencidos >= 3 and fila.severidad == FILTRO_MOROSIDAD_SEVERA for fila in estado.pagina.items))
        self.assertFalse(any(fila.meses_vencidos <= 1 and fila.severidad == FILTRO_MOROSIDAD_SEVERA for fila in estado.pagina.items))

    def test_morosidad_emite_pdf_deuda_desde_datos_reales(self) -> None:
        servicio = ServicioMorosidad(
            RepositorioMorosidadSQLite(self.gestor_base_datos),
            gestor_rutas=self.gestor_rutas,
        )
        estado = servicio.obtener_estado()
        self.assertTrue(estado.pagina.items)
        abonado_id = estado.pagina.items[0].abonado_id
        detalle = servicio.obtener_detalle(abonado_id)
        assert detalle is not None

        resultado = servicio.emitir_documento_deuda(
            abonado_id=abonado_id,
            casas_seleccionadas=(detalle.casas[0].casa_id,),
        )

        self.assertTrue(resultado.exito, resultado.mensaje)
        self.assertTrue(Path(resultado.ruta_documento).exists())
        self.assertTrue(Path(resultado.ruta_documento).read_bytes().startswith(b"%PDF"))

    def test_reportes_basicos_exponen_tablas_obligatorias(self) -> None:
        servicio = ServicioReportes(RepositorioReportesSQLite(self.gestor_base_datos))

        estado = servicio.obtener_estado(fecha_desde="2026-01-01", fecha_hasta="2026-12-31")
        codigos = {tabla.codigo for tabla in estado.tablas}

        self.assertEqual(len(estado.indicadores), 5)
        self.assertIn("abonados_estado", codigos)
        self.assertIn("casas_estado", codigos)
        self.assertIn("deuda_activa", codigos)
        self.assertIn("historial_pagos", codigos)
        self.assertIn("ingresos_diarios", codigos)

    def test_reportes_exportan_pdf_tabular_real(self) -> None:
        servicio = ServicioReportes(RepositorioReportesSQLite(self.gestor_base_datos))
        ruta_pdf = self.raiz_temporal / "exportaciones" / "reportes" / "historial_pagos.pdf"

        resultado = servicio.exportar_pdf(
            ruta_destino=str(ruta_pdf),
            codigo_reporte="historial_pagos",
            fecha_desde="2026-01-01",
            fecha_hasta="2026-12-31",
        )

        self.assertEqual(resultado, str(ruta_pdf))
        self.assertTrue(ruta_pdf.exists())
        self.assertTrue(ruta_pdf.read_bytes().startswith(b"%PDF"))

    def test_vistas_instancian_en_offscreen(self) -> None:
        _app = QApplication.instance() or QApplication([])

        vista_morosidad = VistaMorosidad()
        vista_reportes = VistaReportes()

        self.assertEqual(vista_morosidad.objectName(), "vistaMorosidad")
        self.assertEqual(vista_reportes.objectName(), "vistaReportes")


if __name__ == "__main__":
    unittest.main()
