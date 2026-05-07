"""Componentes reutilizables para pantallas operativas de SICAP."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


COLOR_TEXTO_PRIMARIO = "#10233d"
COLOR_TEXTO_SECUNDARIO = "rgba(226, 235, 247, 0.82)"
COLOR_BORDE = "rgba(255, 255, 255, 0.18)"
COLOR_FONDO_PANEL = "rgba(255, 255, 255, 0.12)"


class TarjetaKPI(QFrame):
    """Tarjeta compacta para metricas del dashboard."""

    def __init__(self, titulo: str, valor: str, detalle: str = "") -> None:
        super().__init__()
        self.setObjectName("tarjetaKPI")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(104)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 15, 18, 15)
        layout.setSpacing(5)

        self._titulo = QLabel(titulo)
        self._titulo.setObjectName("kpiTitulo")
        self._valor = QLabel(valor)
        self._valor.setObjectName("kpiValor")
        self._detalle = QLabel(detalle)
        self._detalle.setObjectName("kpiDetalle")
        self._detalle.setWordWrap(True)

        layout.addWidget(self._titulo)
        layout.addWidget(self._valor)
        layout.addWidget(self._detalle)
        self._aplicar_estilos()

    def actualizar(self, valor: str, detalle: str = "") -> None:
        self._valor.setText(valor)
        self._detalle.setText(detalle)

    def _aplicar_estilos(self) -> None:
        self.setStyleSheet(
            f"""
            QFrame#tarjetaKPI {{
                background-color: {COLOR_FONDO_PANEL};
                border: 1px solid {COLOR_BORDE};
                border-radius: 20px;
            }}
            QLabel#kpiTitulo {{
                color: {COLOR_TEXTO_SECUNDARIO};
                font-size: 12px;
                font-weight: 700;
                letter-spacing: 0.04em;
            }}
            QLabel#kpiValor {{
                color: #ffffff;
                font-size: 30px;
                font-weight: 800;
            }}
            QLabel#kpiDetalle {{
                color: {COLOR_TEXTO_SECUNDARIO};
                font-size: 12px;
            }}
            """
        )


class VistaPlaceholderModulo(QWidget):
    """Pantalla profesional para modulos todavia no implementados."""

    def __init__(self, titulo: str, descripcion: str) -> None:
        super().__init__()
        self.setObjectName("vistaPlaceholderModulo")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addStretch(1)

        tarjeta = QFrame()
        tarjeta.setObjectName("tarjetaPlaceholder")
        tarjeta.setMaximumWidth(680)
        tarjeta.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        tarjeta_layout = QVBoxLayout(tarjeta)
        tarjeta_layout.setContentsMargins(30, 28, 30, 28)
        tarjeta_layout.setSpacing(12)

        label_titulo = QLabel(titulo)
        label_titulo.setObjectName("placeholderTitulo")
        label_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        label_descripcion = QLabel(descripcion)
        label_descripcion.setObjectName("placeholderDescripcion")
        label_descripcion.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label_descripcion.setWordWrap(True)

        aviso = QLabel("Modulo en desarrollo.")
        aviso.setObjectName("placeholderAviso")
        aviso.setAlignment(Qt.AlignmentFlag.AlignCenter)

        tarjeta_layout.addWidget(label_titulo)
        tarjeta_layout.addWidget(label_descripcion)
        tarjeta_layout.addWidget(aviso)
        layout.addWidget(tarjeta, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch(1)
        self._aplicar_estilos()

    def _aplicar_estilos(self) -> None:
        self.setStyleSheet(
            f"""
            QWidget#vistaPlaceholderModulo {{
                background-color: transparent;
            }}
            QFrame#tarjetaPlaceholder {{
                background-color: {COLOR_FONDO_PANEL};
                border: 1px solid {COLOR_BORDE};
                border-radius: 22px;
            }}
            QLabel#placeholderTitulo {{
                color: #ffffff;
                font-size: 22px;
                font-weight: 800;
            }}
            QLabel#placeholderDescripcion {{
                color: {COLOR_TEXTO_SECUNDARIO};
                font-size: 14px;
            }}
            QLabel#placeholderAviso {{
                color: #fce6a8;
                background-color: rgba(255, 246, 223, 0.10);
                border: 1px solid rgba(242, 209, 139, 0.45);
                border-radius: 14px;
                padding: 10px 12px;
                font-size: 13px;
                font-weight: 700;
            }}
            """
        )


def configurar_tabla_operativa(tabla: QTableWidget, encabezados: list[str]) -> None:
    """Aplica estilo y encabezados base a una tabla operativa."""
    tabla.setColumnCount(len(encabezados))
    tabla.setHorizontalHeaderLabels(encabezados)
    tabla.verticalHeader().setVisible(False)
    tabla.setAlternatingRowColors(True)
    tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    tabla.horizontalHeader().setStretchLastSection(True)
    tabla.horizontalHeader().setMinimumSectionSize(96)
    tabla.verticalHeader().setDefaultSectionSize(44)
    tabla.setShowGrid(False)
    tabla.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    tabla.setStyleSheet(
        """
        QTableWidget {
            background-color: rgba(255, 255, 255, 0.11);
            alternate-background-color: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.16);
            border-radius: 16px;
            gridline-color: transparent;
            color: #f7fbff;
            padding: 4px;
            selection-background-color: rgba(140, 220, 226, 0.18);
        }
        QHeaderView::section {
            background-color: rgba(255, 255, 255, 0.12);
            color: #f7fbff;
            border: none;
            border-right: 1px solid rgba(255, 255, 255, 0.08);
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
            padding: 11px 10px;
            font-weight: 700;
        }
        QTableWidget::item {
            padding: 10px 12px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }
        QTableWidget::item:selected {
            background-color: rgba(109, 241, 220, 0.22);
            color: #ffffff;
        }
        """
    )


def crear_item_tabla(texto: object) -> QTableWidgetItem:
    """Crea un item de tabla centrado verticalmente."""
    item = QTableWidgetItem("" if texto is None else str(texto))
    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
    return item


def crear_boton_operativo(texto: str, principal: bool = False) -> QPushButton:
    """Crea un boton consistente para acciones de modulos."""
    boton = QPushButton(texto)
    boton.setCursor(Qt.CursorShape.PointingHandCursor)
    boton.setObjectName("botonOperativoPrimario" if principal else "botonOperativo")
    boton.setMinimumHeight(40)
    boton.setStyleSheet(
        """
        QPushButton#botonOperativo,
        QPushButton#botonOperativoPrimario {
            border-radius: 14px;
            font-size: 13px;
            font-weight: 700;
            padding: 0 16px;
            min-height: 40px;
        }
        QPushButton#botonOperativo {
            background-color: rgba(255, 255, 255, 0.11);
            border: 1px solid rgba(255, 255, 255, 0.18);
            color: #f7fbff;
        }
        QPushButton#botonOperativo:hover {
            background-color: rgba(255, 255, 255, 0.18);
            border-color: rgba(255, 255, 255, 0.24);
        }
        QPushButton#botonOperativo:pressed {
            background-color: rgba(255, 255, 255, 0.24);
        }
        QPushButton#botonOperativoPrimario {
            background-color: rgba(23, 39, 75, 0.92);
            border: 1px solid rgba(255, 255, 255, 0.10);
            color: #ffffff;
        }
        QPushButton#botonOperativoPrimario:hover {
            background-color: rgba(31, 52, 99, 0.96);
        }
        QPushButton#botonOperativoPrimario:pressed {
            background-color: rgba(18, 32, 64, 0.98);
        }
        """
    )
    return boton
