"""Widgets compartidos para navegacion persistente."""

from __future__ import annotations

from PySide6.QtCore import QSize
from PySide6.QtWidgets import QStackedWidget


class ContenedorApiladoAjustable(QStackedWidget):
    """QStackedWidget que reporta tamano segun la pagina actual.

    QStackedWidget usa por defecto el maximo de todas sus paginas para
    `sizeHint` y `minimumSizeHint`, lo que puede deformar la ventana al
    alternar entre pantallas muy distintas. Este contenedor mantiene la
    navegacion persistente, pero ajusta la geometria segun la vista activa.
    """

    def __init__(self) -> None:
        super().__init__()
        self.currentChanged.connect(self._refrescar_geometria)

    def sizeHint(self) -> QSize:
        widget_actual = self.currentWidget()
        if widget_actual is None:
            return super().sizeHint()
        return widget_actual.sizeHint()

    def minimumSizeHint(self) -> QSize:
        widget_actual = self.currentWidget()
        if widget_actual is None:
            return super().minimumSizeHint()

        tamano_actual = widget_actual.minimumSizeHint()
        if not tamano_actual.isValid():
            return QSize(0, 0)
        return tamano_actual

    def _refrescar_geometria(self, _: int) -> None:
        self.updateGeometry()
        widget_actual = self.currentWidget()
        if widget_actual is not None:
            widget_actual.updateGeometry()
