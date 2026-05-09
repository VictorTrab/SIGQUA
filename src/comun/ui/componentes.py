"""Componentes reutilizables para pantallas operativas de SICAP."""

from __future__ import annotations

from PySide6.QtCore import QRectF, QSize, Qt
from PySide6.QtGui import QPaintEvent, QPainter, QPainterPath, QRegion, QResizeEvent
from PySide6.QtWidgets import (
    QDialog,
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

from comun.ui.iconos import obtener_icono_tabler_coloreado


COLOR_TEXTO_PRIMARIO = "#10233d"
COLOR_TEXTO_SECUNDARIO = "rgba(226, 235, 247, 0.82)"
COLOR_BORDE = "rgba(255, 255, 255, 0.18)"
COLOR_FONDO_PANEL = "rgba(255, 255, 255, 0.12)"
COLOR_FONDO_DIALOGO = "#565384"
RADIO_TARJETA_DIALOGO = 4
MARGEN_EXTERNO_DIALOGO = 0


def _crear_estilo_dialogo_sicap(color_fondo: str) -> str:
    return f"""
    QDialog#dialogoBaseSicap,
    QWidget#tarjetaDialogoSicap,
    QFrame#cabeceraDialogoSicap,
    QFrame#cuerpoDialogoSicap,
    QFrame#pieDialogoSicap {{
        background: transparent;
        border: none;
    }}
    QFrame#bloqueDialogoSicap {{
        background: {color_fondo};
        border: 1px solid rgba(255, 255, 255, 0.10);
        border-radius: 4px;
    }}
    QLabel#tituloDialogoSicap {{
        color: #ffffff;
        font-size: 20px;
        font-weight: 900;
    }}
    QLabel#descripcionDialogoSicap {{
        color: rgba(232, 239, 249, 0.80);
        font-size: 13px;
    }}
    QLabel#mensajeErrorDialogoSicap {{
        color: #ffd7d2;
        background: rgba(191, 60, 44, 0.18);
        border: 1px solid rgba(255, 205, 199, 0.20);
        border-radius: 4px;
        padding: 10px 12px;
        font-size: 13px;
        font-weight: 700;
    }}
    QLabel#etiquetaDatoDialogoSicap {{
        color: rgba(232, 239, 249, 0.72);
        font-size: 12px;
        font-weight: 700;
    }}
    QLabel#valorDatoDialogoSicap {{
        color: #f5fbff;
        font-size: 13px;
        font-weight: 800;
    }}
    QLineEdit, QComboBox, QPlainTextEdit {{
        border: 1px solid rgba(255, 255, 255, 0.18);
        border-radius: 4px;
        background: rgba(255, 255, 255, 0.11);
        color: #f5fbff;
        padding: 10px 12px;
        font-size: 13px;
    }}
    QLineEdit:focus, QComboBox:focus, QPlainTextEdit:focus {{
        border-color: rgba(109, 241, 220, 0.40);
        background: rgba(255, 255, 255, 0.16);
    }}
    QComboBox::drop-down {{
        border: none;
        width: 24px;
    }}
    QComboBox QAbstractItemView {{
        background: #24304d;
        color: #f5fbff;
        selection-background-color: rgba(109, 241, 220, 0.22);
    }}
    QLabel {{
        color: #f5fbff;
        font-size: 13px;
        font-weight: 700;
    }}
    """


ESTILO_DIALOGO_SICAP = _crear_estilo_dialogo_sicap(COLOR_FONDO_DIALOGO)

MAPA_VARIANTES_ACCION: dict[str, dict[str, str]] = {
    "neutro": {
        "fondo": "rgba(255, 255, 255, 0.04)",
        "fondo_hover": "rgba(255, 255, 255, 0.10)",
        "fondo_pressed": "rgba(255, 255, 255, 0.16)",
        "borde": "rgba(255, 255, 255, 0.10)",
        "borde_hover": "rgba(255, 255, 255, 0.14)",
        "texto": "#f5fbff",
        "icono": "#f5fbff",
        "icono_hover": "#ffffff",
    },
    "informacion": {
        "fondo": "rgba(79, 163, 255, 0.08)",
        "fondo_hover": "rgba(79, 163, 255, 0.18)",
        "fondo_pressed": "rgba(79, 163, 255, 0.24)",
        "borde": "rgba(131, 195, 255, 0.16)",
        "borde_hover": "rgba(131, 195, 255, 0.28)",
        "texto": "#dff1ff",
        "icono": "#8ec9ff",
        "icono_hover": "#dff1ff",
    },
    "ayuda": {
        "fondo": "rgba(146, 128, 255, 0.08)",
        "fondo_hover": "rgba(146, 128, 255, 0.18)",
        "fondo_pressed": "rgba(146, 128, 255, 0.24)",
        "borde": "rgba(198, 182, 255, 0.16)",
        "borde_hover": "rgba(198, 182, 255, 0.28)",
        "texto": "#f0ebff",
        "icono": "#c6b6ff",
        "icono_hover": "#f5f1ff",
    },
    "edicion": {
        "fondo": "rgba(247, 204, 122, 0.08)",
        "fondo_hover": "rgba(247, 204, 122, 0.18)",
        "fondo_pressed": "rgba(247, 204, 122, 0.24)",
        "borde": "rgba(247, 204, 122, 0.16)",
        "borde_hover": "rgba(247, 204, 122, 0.28)",
        "texto": "#fff4da",
        "icono": "#f7cc7a",
        "icono_hover": "#fff0c7",
    },
    "primario": {
        "fondo": "rgba(109, 241, 220, 0.10)",
        "fondo_hover": "rgba(109, 241, 220, 0.20)",
        "fondo_pressed": "rgba(109, 241, 220, 0.28)",
        "borde": "rgba(109, 241, 220, 0.18)",
        "borde_hover": "rgba(109, 241, 220, 0.30)",
        "texto": "#ebfffb",
        "icono": "#9ef3e4",
        "icono_hover": "#ffffff",
    },
    "salida": {
        "fondo": "rgba(255, 255, 255, 0.04)",
        "fondo_hover": "rgba(187, 48, 39, 0.18)",
        "fondo_pressed": "rgba(187, 48, 39, 0.28)",
        "borde": "rgba(255, 255, 255, 0.10)",
        "borde_hover": "rgba(255, 137, 126, 0.28)",
        "texto": "#f5fbff",
        "icono": "#f5fbff",
        "icono_hover": "#ff7c72",
    },
    "advertencia": {
        "fondo": "rgba(255, 206, 120, 0.08)",
        "fondo_hover": "rgba(255, 206, 120, 0.18)",
        "fondo_pressed": "rgba(255, 206, 120, 0.24)",
        "borde": "rgba(255, 206, 120, 0.16)",
        "borde_hover": "rgba(255, 206, 120, 0.28)",
        "texto": "#fff5db",
        "icono": "#ffcf75",
        "icono_hover": "#fff5db",
    },
}


class DialogoBaseSicap(QDialog):
    """Dialogo base para modales coherentes del sistema."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("dialogoBaseSicap")
        self.setModal(True)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setMinimumWidth(420)
        self._color_fondo_dialogo = COLOR_FONDO_DIALOGO

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._tarjeta = QWidget()
        self._tarjeta.setObjectName("tarjetaDialogoSicap")
        self._tarjeta.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._layout_tarjeta = QVBoxLayout(self._tarjeta)
        self._layout_tarjeta.setContentsMargins(18, 18, 18, 18)
        self._layout_tarjeta.setSpacing(14)

        self._cabecera = QFrame()
        self._cabecera.setObjectName("cabeceraDialogoSicap")
        self._layout_cabecera = QVBoxLayout(self._cabecera)
        self._layout_cabecera.setContentsMargins(18, 18, 18, 18)
        self._layout_cabecera.setSpacing(8)

        self._cuerpo = QFrame()
        self._cuerpo.setObjectName("cuerpoDialogoSicap")
        self._layout_cuerpo = QVBoxLayout(self._cuerpo)
        self._layout_cuerpo.setContentsMargins(18, 18, 18, 18)
        self._layout_cuerpo.setSpacing(14)

        self._pie = QFrame()
        self._pie.setObjectName("pieDialogoSicap")
        self._pie.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._layout_pie = QVBoxLayout(self._pie)
        self._layout_pie.setContentsMargins(16, 14, 16, 14)
        self._layout_pie.setSpacing(0)

        self._layout_tarjeta.addWidget(self._cabecera)
        self._layout_tarjeta.addWidget(self._cuerpo)
        self._layout_tarjeta.addWidget(self._pie)
        layout.addWidget(self._tarjeta)
        self.setStyleSheet(_crear_estilo_dialogo_sicap(self._color_fondo_dialogo))

    def resizeEvent(self, evento: QResizeEvent) -> None:
        self._actualizar_mascara_dialogo()
        super().resizeEvent(evento)

    def paintEvent(self, evento: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self._color_fondo_dialogo)
        painter.drawRect(self.rect())
        painter.end()
        super().paintEvent(evento)

    @property
    def layout_cabecera(self) -> QVBoxLayout:
        return self._layout_cabecera

    @property
    def layout_tarjeta(self) -> QVBoxLayout:
        return self._layout_cuerpo

    @property
    def layout_cuerpo(self) -> QVBoxLayout:
        return self._layout_cuerpo

    @property
    def layout_pie(self) -> QVBoxLayout:
        return self._layout_pie

    def aplicar_color_fondo_personalizado(self, color_fondo: str) -> None:
        self._color_fondo_dialogo = color_fondo
        self.update()
        self.setStyleSheet(_crear_estilo_dialogo_sicap(color_fondo))

    def _actualizar_mascara_dialogo(self) -> None:
        if self.width() <= 0 or self.height() <= 0:
            self.clearMask()
            return
        ruta = QPainterPath()
        ruta.addRoundedRect(QRectF(self.rect()), RADIO_TARJETA_DIALOGO, RADIO_TARJETA_DIALOGO)
        self.setMask(QRegion(ruta.toFillPolygon().toPolygon()))


class BotonAccionContextual(QPushButton):
    """Boton con iconografia y color funcional consistente."""

    def __init__(
        self,
        texto: str,
        icono: str,
        variante: str = "neutro",
        centrado: bool = False,
    ) -> None:
        super().__init__(texto)
        self._icono = icono
        self._variante = variante if variante in MAPA_VARIANTES_ACCION else "neutro"
        self._centrado = centrado
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setObjectName("botonAccionContextual")
        self.setMinimumHeight(36)
        self.setIconSize(QSize(16, 16))
        self._aplicar_estilos()
        self._actualizar_icono(False)

    def enterEvent(self, evento: object) -> None:
        self._actualizar_icono(True)
        super().enterEvent(evento)

    def leaveEvent(self, evento: object) -> None:
        self._actualizar_icono(False)
        super().leaveEvent(evento)

    def _actualizar_icono(self, hover: bool) -> None:
        colores = MAPA_VARIANTES_ACCION[self._variante]
        color_icono = colores["icono_hover"] if hover else colores["icono"]
        self.setIcon(obtener_icono_tabler_coloreado(self._icono, color_icono, tamano=18))

    def _aplicar_estilos(self) -> None:
        colores = MAPA_VARIANTES_ACCION[self._variante]
        alineacion = "center" if self._centrado else "left"
        self.setStyleSheet(
            f"""
            QPushButton#botonAccionContextual {{
                min-height: 36px;
                border-radius: 4px;
                border: 1px solid {colores["borde"]};
                background: {colores["fondo"]};
                color: {colores["texto"]};
                text-align: {alineacion};
                padding: 0 13px;
                font-size: 12px;
                font-weight: 800;
            }}
            QPushButton#botonAccionContextual:hover {{
                border-color: {colores["borde_hover"]};
                background: {colores["fondo_hover"]};
            }}
            QPushButton#botonAccionContextual:pressed {{
                background: {colores["fondo_pressed"]};
            }}
            """
        )


class DialogoMensajeSicap(DialogoBaseSicap):
    """Dialogo informativo estandar del sistema."""

    def __init__(
        self,
        titulo: str,
        mensaje: str,
        icono: str = "info-circle.svg",
        variante: str = "informacion",
        texto_boton: str = "Cerrar",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setMinimumWidth(440)
        self._cuerpo.setVisible(False)

        encabezado = QHBoxLayout()
        encabezado.setSpacing(14)

        icono_label = QLabel("")
        icono_label.setObjectName("iconoDialogoSicap")
        icono_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icono_label.setFixedSize(46, 46)
        icono_label.setPixmap(
            obtener_icono_tabler_coloreado(
                icono,
                MAPA_VARIANTES_ACCION.get(variante, MAPA_VARIANTES_ACCION["informacion"])[
                    "icono_hover"
                ],
                tamano=22,
            ).pixmap(22, 22)
        )

        bloque_titulo = QVBoxLayout()
        bloque_titulo.setContentsMargins(0, 0, 0, 0)
        bloque_titulo.setSpacing(4)

        label_titulo = QLabel(titulo)
        label_titulo.setObjectName("tituloDialogoSicap")
        label_mensaje = QLabel(mensaje)
        label_mensaje.setObjectName("descripcionDialogoSicap")
        label_mensaje.setWordWrap(True)
        bloque_titulo.addWidget(label_titulo)
        bloque_titulo.addWidget(label_mensaje)

        encabezado.addWidget(icono_label, alignment=Qt.AlignmentFlag.AlignTop)
        encabezado.addLayout(bloque_titulo, 1)

        fila_acciones = QHBoxLayout()
        fila_acciones.setContentsMargins(0, 0, 0, 0)
        fila_acciones.setSpacing(12)
        fila_acciones.addStretch(1)
        boton_cerrar = BotonAccionContextual(
            texto_boton,
            "circle-check.svg",
            variante,
            centrado=True,
        )
        boton_cerrar.setMinimumWidth(152)
        boton_cerrar.clicked.connect(self.accept)
        fila_acciones.addWidget(boton_cerrar)

        self.layout_cabecera.addLayout(encabezado)
        self.layout_pie.addLayout(fila_acciones)
        self.setStyleSheet(
            self.styleSheet()
            + """
            QLabel#iconoDialogoSicap {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.10);
                border-radius: 4px;
            }
            """
        )


class DialogoConfirmacionSicap(DialogoBaseSicap):
    """Dialogo de confirmacion coherente para acciones sensibles."""

    def __init__(
        self,
        titulo: str,
        descripcion: str,
        detalles: tuple[tuple[str, str], ...] = (),
        texto_confirmar: str = "Confirmar",
        icono: str = "alert-triangle.svg",
        variante_confirmar: str = "primario",
        color_fondo: str | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setMinimumWidth(460)

        encabezado = QHBoxLayout()
        encabezado.setSpacing(14)

        icono_label = QLabel("")
        icono_label.setObjectName("iconoDialogoSicap")
        icono_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icono_label.setFixedSize(48, 48)
        icono_label.setPixmap(
            obtener_icono_tabler_coloreado(
                icono,
                MAPA_VARIANTES_ACCION.get(variante_confirmar, MAPA_VARIANTES_ACCION["primario"])[
                    "icono_hover"
                ],
                tamano=22,
            ).pixmap(22, 22)
        )

        bloque_titulo = QVBoxLayout()
        bloque_titulo.setContentsMargins(0, 0, 0, 0)
        bloque_titulo.setSpacing(4)

        label_titulo = QLabel(titulo)
        label_titulo.setObjectName("tituloDialogoSicap")
        label_descripcion = QLabel(descripcion)
        label_descripcion.setObjectName("descripcionDialogoSicap")
        label_descripcion.setWordWrap(True)
        bloque_titulo.addWidget(label_titulo)
        bloque_titulo.addWidget(label_descripcion)

        encabezado.addWidget(icono_label, alignment=Qt.AlignmentFlag.AlignTop)
        encabezado.addLayout(bloque_titulo, 1)
        self.layout_cabecera.addLayout(encabezado)

        if detalles:
            panel_detalles = QFrame()
            panel_detalles.setObjectName("bloqueDialogoSicap")
            layout_detalles = QVBoxLayout(panel_detalles)
            layout_detalles.setContentsMargins(16, 16, 16, 16)
            layout_detalles.setSpacing(10)
            for etiqueta, valor in detalles:
                fila = QHBoxLayout()
                fila.setSpacing(12)
                label_etiqueta = QLabel(etiqueta)
                label_etiqueta.setObjectName("etiquetaDatoDialogoSicap")
                label_valor = QLabel(valor)
                label_valor.setObjectName("valorDatoDialogoSicap")
                label_valor.setWordWrap(True)
                fila.addWidget(label_etiqueta, 1)
                fila.addWidget(label_valor, 2)
                layout_detalles.addLayout(fila)
            self.layout_cuerpo.addWidget(panel_detalles)
        else:
            self._cuerpo.setVisible(False)

        fila_acciones = QHBoxLayout()
        fila_acciones.setContentsMargins(0, 0, 0, 0)
        fila_acciones.setSpacing(12)
        boton_cancelar = BotonAccionContextual(
            "Cancelar",
            "arrow-left.svg",
            "neutro",
            centrado=True,
        )
        boton_confirmar = BotonAccionContextual(
            texto_confirmar,
            "circle-check.svg",
            variante_confirmar,
            centrado=True,
        )
        boton_cancelar.setMinimumWidth(148)
        boton_confirmar.setMinimumWidth(176)
        boton_cancelar.clicked.connect(self.reject)
        boton_confirmar.clicked.connect(self.accept)
        fila_acciones.addWidget(boton_cancelar)
        fila_acciones.addStretch(1)
        fila_acciones.addWidget(boton_confirmar)
        self.layout_pie.addLayout(fila_acciones)

        self.setStyleSheet(
            self.styleSheet()
            + """
            QLabel#iconoDialogoSicap {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.10);
                border-radius: 4px;
            }
            """
        )
        if color_fondo:
            self.aplicar_color_fondo_personalizado(color_fondo)


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
    tabla.verticalHeader().setDefaultSectionSize(38)
    tabla.setShowGrid(False)
    tabla.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    tabla.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)


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
    boton.setMinimumHeight(36)
    boton.setStyleSheet(
        """
        QPushButton#botonOperativo,
        QPushButton#botonOperativoPrimario {
            border-radius: 12px;
            font-size: 12px;
            font-weight: 700;
            padding: 0 14px;
            min-height: 36px;
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
