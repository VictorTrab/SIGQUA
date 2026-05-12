from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

RAIZ_PROYECTO = Path(__file__).resolve().parents[1]
RUTA_SRC = RAIZ_PROYECTO / "src"

if str(RUTA_SRC) not in sys.path:
    sys.path.insert(0, str(RUTA_SRC))

from PySide6.QtCore import QPoint  # noqa: E402
from PySide6.QtWidgets import QApplication, QPushButton  # noqa: E402

from modulos.abonados.entidades import OpcionBarrio  # noqa: E402
from modulos.abonados.vista import DialogoFormularioAbonado  # noqa: E402
from comun.ui.componentes import (  # noqa: E402
    MARGEN_EXTERNO_DIALOGO,
    RADIO_TARJETA_DIALOGO,
    DialogoConfirmacionSicap,
    DialogoMensajeSicap,
)
from modulos.barrios.entidades import Barrio  # noqa: E402
from modulos.barrios.vista import DialogoDetalleBarrio, DialogoFormularioBarrio  # noqa: E402


class TestDialogosSicap(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.aplicacion = QApplication.instance() or QApplication([])

    def _capturar_dialogo(self, dialogo) -> tuple[object, object]:
        dialogo.adjustSize()
        dialogo.show()
        self.aplicacion.processEvents()
        return dialogo, dialogo.grab().toImage()

    def _assert_botones_solo_texto(self, dialogo) -> None:
        botones = dialogo.findChildren(QPushButton)
        self.assertTrue(botones)
        for boton in botones:
            self.assertTrue(boton.icon().isNull(), boton.text())

    def test_dialogo_mensaje_recorta_esquinas_y_conserva_transparencia(self) -> None:
        dialogo, _ = self._capturar_dialogo(
            DialogoMensajeSicap(
                "Aviso",
                "Mensaje de prueba para validar transparencias y recorte redondeado.",
            )
        )
        tarjeta = dialogo._tarjeta
        origen_tarjeta = tarjeta.mapTo(dialogo, QPoint(0, 0))
        mascara = dialogo.mask()

        self.assertFalse(mascara.isEmpty())
        self.assertEqual(origen_tarjeta.x(), MARGEN_EXTERNO_DIALOGO)
        self.assertEqual(origen_tarjeta.y(), MARGEN_EXTERNO_DIALOGO)
        self.assertFalse(mascara.contains(QPoint(0, 0)))
        if RADIO_TARJETA_DIALOGO > 4:
            self.assertFalse(mascara.contains(QPoint(1, 1)))
            self.assertFalse(mascara.contains(QPoint(3, 3)))
        self.assertTrue(mascara.contains(QPoint(RADIO_TARJETA_DIALOGO, 1)))
        self.assertTrue(mascara.contains(QPoint(1, RADIO_TARJETA_DIALOGO)))
        dialogo.close()

    def test_dialogo_formulario_y_confirmacion_reutilizan_tarjeta_recortada(self) -> None:
        dialogo_formulario, _ = self._capturar_dialogo(DialogoFormularioBarrio())
        dialogo_confirmacion, _ = self._capturar_dialogo(
            DialogoConfirmacionSicap(
                "Confirmar accion",
                "Descripcion de prueba.",
                detalles=(("Campo", "Valor"),),
            )
        )

        for dialogo in (dialogo_formulario, dialogo_confirmacion):
            tarjeta = dialogo._tarjeta
            origen_tarjeta = tarjeta.mapTo(dialogo, QPoint(0, 0))
            mascara = dialogo.mask()

            self.assertFalse(mascara.isEmpty())
            self.assertEqual(origen_tarjeta, QPoint(0, 0))
            self.assertFalse(mascara.contains(QPoint(0, 0)))
            self.assertTrue(mascara.contains(QPoint(RADIO_TARJETA_DIALOGO, 1)))
            self._assert_botones_solo_texto(dialogo)
            dialogo.close()

    def test_dialogos_compactos_eliminan_iconos_en_botones(self) -> None:
        dialogos = [
            DialogoMensajeSicap("Aviso", "Mensaje breve para revisar acciones compactas."),
            DialogoFormularioAbonado(barrios=[OpcionBarrio(1, "Centro")]),
        ]

        for dialogo in dialogos:
            self._capturar_dialogo(dialogo)
            self._assert_botones_solo_texto(dialogo)
            self.assertLessEqual(dialogo._layout_tarjeta.contentsMargins().left(), 14)
            self.assertLessEqual(dialogo.layout_cuerpo.spacing(), 10)
            dialogo.close()

    def test_dialogo_detalle_barrio_unifica_panel_y_acciones_en_un_mismo_bloque(self) -> None:
        barrio = Barrio(
            identificador=1,
            nombre="Centro",
            estado="ACTIVO",
            observaciones="Observacion de prueba.",
            total_abonados=12,
            total_casas=9,
            actualizado_en="2026-05-08 08:00:00",
        )
        dialogo, _ = self._capturar_dialogo(
            DialogoDetalleBarrio(
                barrio=barrio,
                fecha_actualizada="08/05/2026 08:00 AM",
            )
        )

        panel_contenido = dialogo.findChild(type(dialogo._cuerpo), "panelContenidoDetalleBarrio")
        separador = dialogo.findChild(type(dialogo._cuerpo), "separadorDetalleBarrio")
        observaciones = dialogo.findChild(type(dialogo._cuerpo), "campoDetalleBarrioAmplio")

        self.assertIsNotNone(panel_contenido)
        self.assertIsNotNone(separador)
        self.assertIsNotNone(observaciones)
        self.assertFalse(dialogo._pie.isVisible())
        self.assertEqual(dialogo.layout_pie.count(), 0)
        self.assertIn("panelContenidoDetalleBarrio", dialogo.styleSheet())
        self.assertIn(f"border-radius: {RADIO_TARJETA_DIALOGO}px;", dialogo.styleSheet())
        dialogo.close()


if __name__ == "__main__":
    unittest.main()
