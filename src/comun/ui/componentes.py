"""Componentes reutilizables para pantallas operativas de SICAP."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


COLOR_TEXTO_PRIMARIO = "#10233d"
COLOR_TEXTO_SECUNDARIO = "#5d7187"
COLOR_BORDE = "#d8e2ec"
COLOR_FONDO_PANEL = "#ffffff"


class TarjetaKPI(QFrame):
    """Tarjeta compacta para metricas del dashboard."""

    def __init__(self, titulo: str, valor: str, detalle: str = "") -> None:
        super().__init__()
        self.setObjectName("tarjetaKPI")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(112)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(6)

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
                border-radius: 8px;
            }}
            QLabel#kpiTitulo {{
                color: {COLOR_TEXTO_SECUNDARIO};
                font-size: 12px;
                font-weight: 700;
            }}
            QLabel#kpiValor {{
                color: {COLOR_TEXTO_PRIMARIO};
                font-size: 28px;
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
                border-radius: 8px;
            }}
            QLabel#placeholderTitulo {{
                color: {COLOR_TEXTO_PRIMARIO};
                font-size: 22px;
                font-weight: 800;
            }}
            QLabel#placeholderDescripcion {{
                color: {COLOR_TEXTO_SECUNDARIO};
                font-size: 14px;
            }}
            QLabel#placeholderAviso {{
                color: #8a5d00;
                background-color: #fff6df;
                border: 1px solid #f2d18b;
                border-radius: 8px;
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
    tabla.setStyleSheet(
        """
        QTableWidget {
            background-color: #ffffff;
            alternate-background-color: #f7fafc;
            border: 1px solid #d8e2ec;
            border-radius: 8px;
            gridline-color: #e6edf4;
            color: #10233d;
        }
        QHeaderView::section {
            background-color: #eef4f8;
            color: #17324d;
            border: none;
            border-right: 1px solid #d8e2ec;
            padding: 8px;
            font-weight: 700;
        }
        QTableWidget::item {
            padding: 8px;
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
    boton.setMinimumHeight(38)
    boton.setStyleSheet(
        """
        QPushButton#botonOperativo,
        QPushButton#botonOperativoPrimario {
            border-radius: 8px;
            font-size: 13px;
            font-weight: 700;
            padding: 0 14px;
        }
        QPushButton#botonOperativo {
            background-color: #ffffff;
            border: 1px solid #c9d7e5;
            color: #17324d;
        }
        QPushButton#botonOperativo:hover {
            background-color: #edf5fb;
        }
        QPushButton#botonOperativoPrimario {
            background-color: #1f2c51;
            border: 1px solid #1f2c51;
            color: #ffffff;
        }
        QPushButton#botonOperativoPrimario:hover {
            background-color: #263866;
        }
        """
    )
    return boton

