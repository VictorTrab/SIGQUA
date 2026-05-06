from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

RAIZ_PROYECTO = Path(__file__).resolve().parents[1]
RUTA_SRC = RAIZ_PROYECTO / "src"

if str(RUTA_SRC) not in sys.path:
    sys.path.insert(0, str(RUTA_SRC))

from PySide6.QtWidgets import QApplication  # noqa: E402

from app import crear_ventana_principal  # noqa: E402
from comun.configuracion.gestor_rutas import GestorRutas  # noqa: E402
from modulos.autenticacion.vista import (  # noqa: E402
    ANCHO_MAXIMO_TARJETA,
    COLOR_GRADIENTE_FINAL,
    COLOR_GRADIENTE_INICIAL,
    VistaAutenticacion,
)


class TestVistaYAppAutenticacion(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.aplicacion = QApplication.instance() or QApplication([])

    def test_vista_usa_contenedor_con_ancho_maximo_y_navegacion_adaptable(self) -> None:
        vista = VistaAutenticacion()

        self.assertEqual(vista._stack.count(), 6)
        self.assertEqual(vista._boton_login.parentWidget().maximumWidth(), ANCHO_MAXIMO_TARJETA)
        self.assertGreater(vista.maximumWidth(), ANCHO_MAXIMO_TARJETA)
        self.assertEqual(COLOR_GRADIENTE_INICIAL, "#1abc9c")
        self.assertEqual(COLOR_GRADIENTE_FINAL, "#1f2c51")
        self.assertEqual(len(vista._campo_contrasena.actions()), 2)
        self.assertEqual(vista._campo_contrasena.echoMode(), vista._campo_contrasena.EchoMode.Password)

        vista._campo_contrasena.actions()[-1].trigger()
        self.assertEqual(vista._campo_contrasena.echoMode(), vista._campo_contrasena.EchoMode.Normal)

        vista._campo_contrasena.actions()[-1].trigger()
        self.assertEqual(vista._campo_contrasena.echoMode(), vista._campo_contrasena.EchoMode.Password)
        self.assertFalse(vista._boton_login.icon().isNull())

        vista.mostrar_olvido_contrasena()
        self.assertIs(vista._stack.currentWidget(), vista._pagina_olvido)

        vista.mostrar_enlace_invalido("Token invalido")
        self.assertIs(vista._stack.currentWidget(), vista._pagina_enlace_invalido)

    def test_app_compone_ventana_y_abre_maximizada(self) -> None:
        with tempfile.TemporaryDirectory() as directorio_temporal:
            raiz_temporal = Path(directorio_temporal)
            (raiz_temporal / "database" / "migrations").mkdir(parents=True, exist_ok=True)

            ruta_esquema_real = (
                RAIZ_PROYECTO / "database" / "migrations" / "002_esquema_inicial.sql"
            )
            contenido_sql = ruta_esquema_real.read_text(encoding="utf-8")
            (raiz_temporal / "database" / "migrations" / "002_esquema_inicial.sql").write_text(
                contenido_sql,
                encoding="utf-8",
            )

            gestor_rutas = GestorRutas(raiz_proyecto=raiz_temporal)
            _, ventana_principal, vista_autenticacion = crear_ventana_principal(gestor_rutas)

            self.assertIs(ventana_principal.centralWidget(), vista_autenticacion)

            ventana_principal.showMaximized()
            self.assertTrue(ventana_principal.isMaximized())
            self.assertFalse(ventana_principal.isFullScreen())
            ventana_principal.close()


if __name__ == "__main__":
    unittest.main()
