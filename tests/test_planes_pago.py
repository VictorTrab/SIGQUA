from __future__ import annotations

import shutil
import sqlite3
import sys
import unittest
import uuid
from contextlib import closing
from pathlib import Path


RAIZ_PROYECTO = Path(__file__).resolve().parents[1]
RUTA_SRC = RAIZ_PROYECTO / "src"

if str(RUTA_SRC) not in sys.path:
    sys.path.insert(0, str(RUTA_SRC))

from comun.base_datos import GestorBaseDatos  # noqa: E402
from comun.configuracion.gestor_rutas import GestorRutas  # noqa: E402
from modulos.planes_pago.entidades import FILTRO_PLANES_CON_MORA, FILTRO_PLANES_TODOS, FormularioPlanPago  # noqa: E402
from modulos.planes_pago.repositorio import RepositorioPlanesPagoSQLite  # noqa: E402
from modulos.planes_pago.servicio import ServicioPlanesPago  # noqa: E402


class TestPlanesPago(unittest.TestCase):
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
        self.ruta_db = self.gestor_base_datos.inicializar_base_datos(incluir_datos_prueba=True)
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

    def test_crear_plan_financia_deuda_y_activa_servicio_con_prima(self) -> None:
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
                multa_corte_centavos=0,
                prima_centavos=20000,
                cantidad_cuotas=4,
                estado="ACTIVO",
                observaciones="Plan de activacion con deuda financiada.",
            ),
            actor_id=1,
        )

        self.assertTrue(resultado.exito, resultado.mensaje)
        pagina = self.servicio.listar()
        self.assertEqual(pagina.total_registros, 2)
        nuevo_plan = max(pagina.items, key=lambda item: item.identificador or 0)
        self.assertEqual(nuevo_plan.deuda_financiada_centavos, 35000)
        self.assertEqual(nuevo_plan.monto_activacion_centavos, 60000)
        self.assertEqual(nuevo_plan.prima_centavos, 20000)
        self.assertEqual(nuevo_plan.saldo_financiado_centavos, 75000)
        with closing(sqlite3.connect(self.ruta_db)) as conexion:
            fila_casa = conexion.execute(
                "SELECT estado_servicio, ha_tenido_servicio_activo FROM casas WHERE id = ?;",
                (casa_id,),
            ).fetchone()
            fila_pago = conexion.execute(
                """
                SELECT tipo_pago, total_pagado_centavos
                FROM pagos
                WHERE casa_id = ?
                ORDER BY id DESC
                LIMIT 1;
                """,
                (casa_id,),
            ).fetchone()
            deuda = conexion.execute(
                """
                SELECT COALESCE(SUM(saldo_pendiente_centavos), 0)
                FROM cargos
                WHERE casa_id = ?
                  AND estado IN ('PENDIENTE', 'PARCIAL', 'VENCIDO');
                """,
                (casa_id,),
            ).fetchone()

        self.assertEqual(tuple(fila_casa), ("ACTIVO", 1))
        self.assertEqual(tuple(fila_pago), ("PLAN_PAGO", 20000))
        self.assertEqual(deuda[0], 0)

    def test_filtro_con_mora_mantiene_plan_semilla(self) -> None:
        pagina_mora = self.servicio.listar(filtro_rapido=FILTRO_PLANES_CON_MORA)
        self.assertEqual(pagina_mora.total_registros, 1)

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


if __name__ == "__main__":
    unittest.main()
