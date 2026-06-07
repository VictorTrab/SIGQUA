"""Barra de titulo integrada para la ventana principal de SIGQUA."""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QIcon, QMouseEvent
from PySide6.QtWidgets import QHBoxLayout, QLabel, QToolButton, QWidget

from comun.ui.iconos import obtener_icono_tabler_coloreado


class BarraTituloVentana(QWidget):
    """Reemplaza los controles nativos de la ventana principal."""

    minimizar_solicitado = Signal()
    cerrar_solicitado = Signal()
    mover_solicitado = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("barraTituloVentana")
        self.setFixedHeight(34)
        self._movimiento_habilitado = False

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 0, 0)
        layout.setSpacing(8)

        self._icono = QLabel()
        self._icono.setObjectName("iconoBarraTitulo")
        self._icono.setFixedSize(18, 18)
        self._icono.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icono.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        self._titulo = QLabel("SIGQUA")
        self._titulo.setObjectName("textoBarraTitulo")
        self._titulo.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        self._boton_minimizar = self._crear_boton_control(
            "botonMinimizarVentana",
            "Minimizar",
            "minus.svg",
        )
        self._boton_cerrar = self._crear_boton_control(
            "botonCerrarVentana",
            "Cerrar",
            "x.svg",
        )
        self._boton_minimizar.clicked.connect(self.minimizar_solicitado.emit)
        self._boton_cerrar.clicked.connect(self.cerrar_solicitado.emit)

        layout.addWidget(self._icono)
        layout.addWidget(self._titulo, 1)
        layout.addWidget(self._boton_minimizar)
        layout.addWidget(self._boton_cerrar)
        self._aplicar_estilos()

    def actualizar_titulo(self, titulo: str) -> None:
        self._titulo.setText(titulo.strip() or "SIGQUA")

    def actualizar_icono(self, icono: QIcon) -> None:
        self._icono.setVisible(not icono.isNull())
        self._icono.setPixmap(icono.pixmap(QSize(16, 16)))

    def establecer_movimiento_habilitado(self, habilitado: bool) -> None:
        self._movimiento_habilitado = habilitado
        self.setCursor(
            Qt.CursorShape.SizeAllCursor
            if habilitado
            else Qt.CursorShape.ArrowCursor
        )

    def movimiento_habilitado(self) -> bool:
        return self._movimiento_habilitado

    def mousePressEvent(self, evento: QMouseEvent) -> None:  # noqa: N802
        if (
            self._movimiento_habilitado
            and evento.button() == Qt.MouseButton.LeftButton
        ):
            self.mover_solicitado.emit()
            evento.accept()
            return
        super().mousePressEvent(evento)

    @staticmethod
    def _crear_boton_control(
        object_name: str,
        tooltip: str,
        icono: str,
    ) -> QToolButton:
        boton = QToolButton()
        boton.setObjectName(object_name)
        boton.setFixedSize(38, 34)
        boton.setToolTip(tooltip)
        boton.setCursor(Qt.CursorShape.PointingHandCursor)
        boton.setIcon(
            obtener_icono_tabler_coloreado(
                icono,
                "#D9E7F2",
                tamano=15,
            )
        )
        boton.setIconSize(QSize(15, 15))
        return boton

    def _aplicar_estilos(self) -> None:
        self.setStyleSheet(
            """
            QWidget#barraTituloVentana {
                background: #0B0D0F;
                border: none;
                border-bottom: 1px solid rgba(117, 199, 240, 0.14);
            }
            QLabel#iconoBarraTitulo {
                background: transparent;
                border: none;
            }
            QLabel#textoBarraTitulo {
                background: transparent;
                border: none;
                color: #C5DDEE;
                font-size: 11px;
                font-weight: 700;
            }
            QToolButton#botonMinimizarVentana,
            QToolButton#botonCerrarVentana {
                background: transparent;
                border: none;
                border-radius: 0;
                padding: 0;
            }
            QToolButton#botonMinimizarVentana:hover {
                background: rgba(47, 155, 255, 0.18);
            }
            QToolButton#botonMinimizarVentana:pressed {
                background: rgba(47, 155, 255, 0.28);
            }
            QToolButton#botonCerrarVentana:hover {
                background: #C42B1C;
            }
            QToolButton#botonCerrarVentana:pressed {
                background: #9F1F15;
            }
            """
        )
