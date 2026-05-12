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
        self.assertEqual(estado.informacion.version_sistema, "2.2.0")
        self.assertEqual(estado.seguridad.maximo_intentos_fallidos, 5)

    def test_guardado_datos_junta_y_cobro_actualiza_base(self) -> None:
        resultado_junta = self.servicio.guardar_datos_junta(
            nombre="Junta Nueva",
            telefono="9999-0000",
            correo="junta@local.test",
            direccion="Centro de Yarumela",
            actor_id=1,
        )
        resultado_cobro = self.servicio.guardar_parametros_cobro(
            precio_mensual_centavos=3200,
            multa_mora_automatica_activa=True,
            multa_mora_automatica_centavos=450,
            corte_automatico_activo=True,
            actor_id=1,
        )

        self.assertTrue(resultado_junta.exito)
        self.assertTrue(resultado_cobro.exito)

        estado = self.servicio.obtener_estado()
        self.assertEqual(estado.datos_junta.nombre, "Junta Nueva")
        self.assertEqual(estado.parametros_cobro.precio_mensual_centavos, 3200)
        self.assertTrue(estado.parametros_cobro.multa_mora_automatica_activa)
        self.assertEqual(estado.parametros_cobro.multa_mora_automatica_centavos, 450)
        self.assertTrue(estado.parametros_cobro.corte_automatico_activo)


if __name__ == "__main__":
    unittest.main()
