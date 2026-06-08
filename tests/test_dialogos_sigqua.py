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

from PySide6.QtCore import QPoint, Qt  # noqa: E402
from PySide6.QtWidgets import QApplication, QPushButton, QScrollArea, QToolButton  # noqa: E402

from modulos.abonados.entidades import Abonado, OpcionBarrio  # noqa: E402
from modulos.abonados.vista import (  # noqa: E402
    DialogoConfirmacionEstadoAbonado,
    DialogoDetalleAbonado,
    DialogoFormularioAbonado,
)
from comun.ui.componentes import (  # noqa: E402
    MARGEN_EXTERNO_DIALOGO,
    RADIO_TARJETA_DIALOGO,
    DialogoConfirmacionSigqua,
    DialogoMensajeSigqua,
)
from comun.ui.temas import obtener_paleta_tema_actual  # noqa: E402
from modulos.barrios.entidades import Barrio  # noqa: E402
from modulos.barrios.vista import DialogoDetalleBarrio, DialogoFormularioBarrio  # noqa: E402
from modulos.casas.entidades import Casa, DetalleCasa  # noqa: E402
from modulos.casas.vista import DialogoDetalleCasa  # noqa: E402


class TestDialogosSigqua(unittest.TestCase):
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

    def test_dialogo_mensaje_usa_fondo_opaco_y_tarjeta_alineada(self) -> None:
        dialogo, _ = self._capturar_dialogo(
            DialogoMensajeSigqua(
                "Aviso",
                "Mensaje de prueba para validar transparencias y recorte redondeado.",
            )
        )
        tarjeta = dialogo._tarjeta
        origen_tarjeta = tarjeta.mapTo(dialogo, QPoint(0, 0))

        self.assertEqual(origen_tarjeta.x(), MARGEN_EXTERNO_DIALOGO)
        self.assertEqual(origen_tarjeta.y(), MARGEN_EXTERNO_DIALOGO)
        self.assertFalse(dialogo.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground))
        self.assertTrue(dialogo.mask().isEmpty())
        dialogo.close()

    def test_dialogo_formulario_y_confirmacion_reutilizan_tarjeta_opaca_sin_mascara_top_level(self) -> None:
        dialogo_formulario, _ = self._capturar_dialogo(DialogoFormularioBarrio())
        dialogo_confirmacion, _ = self._capturar_dialogo(
            DialogoConfirmacionSigqua(
                "Confirmar accion",
                "Descripcion de prueba.",
                detalles=(("Campo", "Valor"),),
            )
        )

        for dialogo in (dialogo_formulario, dialogo_confirmacion):
            tarjeta = dialogo._tarjeta
            origen_tarjeta = tarjeta.mapTo(dialogo, QPoint(0, 0))

            self.assertEqual(origen_tarjeta, QPoint(0, 0))
            self.assertTrue(dialogo.mask().isEmpty())
            self.assertFalse(dialogo.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground))
            self._assert_botones_solo_texto(dialogo)
            dialogo.close()

    def test_dialogo_confirmacion_permite_personalizar_texto_cancelar(self) -> None:
        dialogo = DialogoConfirmacionSigqua(
            "Cambios sin guardar",
            "Hay cambios pendientes.",
            texto_confirmar="Descartar cambios",
            texto_cancelar="Seguir editando",
        )
        textos = {boton.text() for boton in dialogo.findChildren(QPushButton)}

        self.assertIn("Descartar cambios", textos)
        self.assertIn("Seguir editando", textos)
        dialogo.close()

    def test_dialogos_compactos_eliminan_iconos_en_botones(self) -> None:
        dialogos = [
            DialogoMensajeSigqua("Aviso", "Mensaje breve para revisar acciones compactas."),
            DialogoFormularioAbonado(barrios=[OpcionBarrio(1, "Centro")]),
        ]

        for dialogo in dialogos:
            self._capturar_dialogo(dialogo)
            self._assert_botones_solo_texto(dialogo)
            self.assertLessEqual(dialogo._layout_tarjeta.contentsMargins().left(), 14)
            self.assertLessEqual(dialogo.layout_cuerpo.spacing(), 10)
            dialogo.close()

    def test_formulario_abonado_usa_buscador_con_id_real_y_scroll_interno(self) -> None:
        dialogo = DialogoFormularioAbonado(
            barrios=[OpcionBarrio(1, "Centro"), OpcionBarrio(2, "San Jorge")]
        )
        self._capturar_dialogo(dialogo)

        dialogo._campo_barrio.seleccionar_por_id(2, "San Jorge")
        formulario = dialogo.obtener_formulario()
        scroll = dialogo.findChild(QScrollArea, "scrollFormularioAbonado")

        self.assertEqual(formulario.barrio_id, 2)
        self.assertIsNotNone(scroll)
        self.assertTrue(dialogo._pie.isVisible())

        dialogo._campo_barrio._al_editar_texto("zzz")
        self.assertEqual(
            dialogo._campo_barrio._modelo_resultados.item(0).text(),
            "No se encontraron barrios",
        )
        dialogo.close()

    def test_confirmacion_diferencia_cancelar_de_accion_peligrosa(self) -> None:
        abonado = Abonado(
            identificador=3,
            dni="0801199000033",
            nombre_completo="Diana Flores",
            estado="ACTIVO",
            total_casas=2,
        )
        dialogo, _ = self._capturar_dialogo(DialogoConfirmacionEstadoAbonado(abonado))
        botones = {boton.text(): boton for boton in dialogo.findChildren(QPushButton)}
        paleta = obtener_paleta_tema_actual()

        self.assertIn("Cancelar", botones)
        self.assertIn("Inactivar", botones)
        self.assertIn(str(paleta["boton_secundario_fondo"]), botones["Cancelar"].styleSheet())
        self.assertIn(str(paleta["boton_peligro_fondo"]), botones["Inactivar"].styleSheet())
        self.assertNotEqual(botones["Cancelar"].styleSheet(), botones["Inactivar"].styleSheet())
        dialogo.close()

    def test_detalles_permiten_copiar_valor_con_un_clic_y_reinician_estado(self) -> None:
        abonado = Abonado(
            identificador=3,
            dni="0801199000033",
            nombre_completo="Diana Flores",
            barrio_nombre="Centro",
            estado="ACTIVO",
        )
        barrio = Barrio(
            identificador=7,
            nombre="Centro",
            estado="ACTIVO",
        )
        casa = Casa(
            identificador=12,
            abonado_id=3,
            abonado_nombre="Diana Flores",
            abonado_dni="0801199000033",
            barrio_nombre="Centro",
            direccion_referencia="Frente al parque",
            estado_servicio="ACTIVO",
        )
        dialogos = [
            (DialogoDetalleAbonado(abonado, "01/06/2026", "02/06/2026", "L 0.00"), "0801199000033"),
            (DialogoDetalleBarrio(barrio, "01/06/2026", "02/06/2026"), "7"),
            (
                DialogoDetalleCasa(
                    DetalleCasa(casa=casa),
                    formateador_fecha=lambda valor: valor or "Sin registro",
                    formateador_moneda=lambda valor: f"L {valor / 100:,.2f}",
                ),
                "12",
            ),
        ]

        for dialogo, esperado in dialogos:
            self._capturar_dialogo(dialogo)
            boton = dialogo.findChild(QToolButton, "botonCopiarIdDetalle")
            self.assertIsNotNone(boton)
            assert boton is not None
            self.assertEqual(boton.text(), "COPIAR")
            self.assertFalse(bool(boton.property("copiado")))
            boton.click()
            self.aplicacion.processEvents()
            self.assertEqual(QApplication.clipboard().text(), esperado)
            self.assertEqual(boton.text(), "OK")
            self.assertTrue(bool(boton.property("copiado")))
            dialogo.close()

        dialogo_reabierto = DialogoDetalleAbonado(abonado, "01/06/2026", "02/06/2026", "L 0.00")
        self._capturar_dialogo(dialogo_reabierto)
        boton_reabierto = dialogo_reabierto.findChild(QToolButton, "botonCopiarIdDetalle")
        self.assertIsNotNone(boton_reabierto)
        assert boton_reabierto is not None
        self.assertEqual(boton_reabierto.text(), "COPIAR")
        self.assertFalse(bool(boton_reabierto.property("copiado")))
        dialogo_reabierto.close()

    def test_dialogo_detalle_barrio_mantiene_panel_y_acciones_operativas(self) -> None:
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
                fecha_creacion="08/05/2026 07:30 AM",
                fecha_actualizada="08/05/2026 08:00 AM",
            )
        )

        panel_contenido = dialogo.findChild(type(dialogo._cuerpo), "panelDetalleSigqua")
        observaciones = dialogo.findChild(type(dialogo._cuerpo), "campoDetalleSigqua")

        self.assertIsNotNone(panel_contenido)
        self.assertIsNotNone(observaciones)
        self.assertTrue(dialogo._pie.isVisible())
        self.assertGreater(dialogo.layout_pie.count(), 0)
        self.assertIn("panelDetalleSigqua", dialogo.styleSheet())
        self.assertIn(f"border-radius: {RADIO_TARJETA_DIALOGO}px;", dialogo.styleSheet())
        dialogo.close()


if __name__ == "__main__":
    unittest.main()
