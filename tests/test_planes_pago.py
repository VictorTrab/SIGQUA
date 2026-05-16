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
from modulos.planes_pago.entidades import (  # noqa: E402
    FILTRO_PLANES_CON_MORA,
    FILTRO_PLANES_TODOS,
    FormularioPlanPago,
)
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
        self.gestor_base_datos.inicializar_base_datos()
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

    def test_filtro_con_mora_y_creacion_de_plan_operativo(self) -> None:
        pagina_mora = self.servicio.listar(filtro_rapido=FILTRO_PLANES_CON_MORA)
        self.assertEqual(pagina_mora.total_registros, 1)

        resultado = self.servicio.guardar(
            FormularioPlanPago(
                identificador=None,
                casa_id=1,
                tipo_plan="RECONEXION",
                concepto_financiado="RECONEXION",
                prima_centavos=0,
                saldo_financiado_centavos=24000,
                cuota_regular_centavos=12000,
                cantidad_cuotas=2,
                estado="ACTIVO",
                observaciones="Plan operativo de reconexion para prueba.",
            ),
            actor_id=1,
        )

        self.assertTrue(resultado.exito)
        pagina = self.servicio.listar()
        self.assertEqual(pagina.total_registros, 2)
        nuevo_plan = next(plan for plan in pagina.items if plan.tipo_plan == "RECONEXION")
        detalle = self.servicio.obtener_detalle(nuevo_plan.identificador or 0)
        self.assertIsNotNone(detalle)
        assert detalle is not None
        self.assertEqual(detalle.plan.cantidad_cuotas, 2)
        self.assertEqual(len(detalle.cuotas), 2)
        self.assertEqual(sum(cuota.monto_centavos for cuota in detalle.cuotas), 24000)


if __name__ == "__main__":
    unittest.main()
