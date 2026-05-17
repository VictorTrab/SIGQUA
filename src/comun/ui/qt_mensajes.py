"""Filtro centralizado para mensajes ruidosos de Qt en SICAP."""

from __future__ import annotations

import sys
from typing import Any

from PySide6.QtCore import QtMsgType, qInstallMessageHandler


PATRONES_QT_RUIDOSOS = (
    "QPropertyAnimation::updateState (opacity): Changing state of an animation without target",
    "QWindowsWindow::setGeometry: Unable to set geometry",
    "QFont::setPointSize: Point size <= 0",
    "QFontDatabase: Cannot find font directory",
    "This plugin does not support propagateSizeHints()",
    "This plugin does not support setting window masks",
)

_filtro_qt_configurado = False


def _filtrar_mensajes_qt(
    _tipo: QtMsgType,
    _contexto: Any,
    mensaje: str,
) -> None:
    if any(patron in mensaje for patron in PATRONES_QT_RUIDOSOS):
        return
    sys.stderr.write(f"{mensaje}\n")


def configurar_filtro_mensajes_qt() -> None:
    global _filtro_qt_configurado
    if _filtro_qt_configurado:
        return
    qInstallMessageHandler(_filtrar_mensajes_qt)
    _filtro_qt_configurado = True
