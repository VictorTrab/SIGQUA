"""Componentes reutilizables para pantallas operativas de SICAP."""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from comun.ui.iconos import obtener_icono_tabler_coloreado
from comun.ui.qt_mensajes import configurar_filtro_mensajes_qt
from comun.ui.temas import (
    TEMA_SICAP_PREDETERMINADO,
    obtener_paleta_tema,
    obtener_paleta_tema_actual,
    obtener_tema_actual,
)
from comun.utilidades.moneda import formatear_monto_desde_centavos, parsear_monto_a_centavos


COLOR_TEXTO_PRIMARIO = "#10233d"
COLOR_TEXTO_SECUNDARIO = "rgba(226, 235, 247, 0.82)"
COLOR_BORDE = "rgba(255, 255, 255, 0.18)"
COLOR_FONDO_PANEL = "rgba(255, 255, 255, 0.12)"
COLOR_FONDO_DIALOGO = "#565384"
RADIO_TARJETA_DIALOGO = 4
MARGEN_EXTERNO_DIALOGO = 0
PADDING_TARJETA_DIALOGO = 14
ESPACIADO_TARJETA_DIALOGO = 10
PADDING_BLOQUE_DIALOGO = 12
ALTURA_BOTON_DIALOGO = 34


configurar_filtro_mensajes_qt()


class CampoMontoMonetario(QLineEdit):
    """Campo comun para capturar montos visibles y convertirlos a centavos."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setPlaceholderText("0.00")
        self.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.editingFinished.connect(self._normalizar_texto)

    def obtener_centavos(self) -> int:
        valor = parsear_monto_a_centavos(self.text())
        return -1 if valor is None else valor

    def establecer_desde_centavos(self, valor: int | None) -> None:
        if valor is None:
            self.clear()
            return
        self.setText(formatear_monto_desde_centavos(valor))

    def _normalizar_texto(self) -> None:
        valor = parsear_monto_a_centavos(self.text())
        if valor is None:
            if self.text().strip():
                self.setText(self.text().strip())
            else:
                self.clear()
            return
        self.setText(formatear_monto_desde_centavos(valor))


def _crear_estilo_dialogo_sicap(color_fondo: str, paleta: dict[str, object]) -> str:
    return f"""
    QDialog#dialogoBaseSicap {{
        background: {color_fondo};
        border: 1px solid {paleta["borde_suave"]};
        border-radius: 4px;
        font-family: "{paleta["familia_tipografica"]}";
    }}
    QWidget#tarjetaDialogoSicap,
    QFrame#cabeceraDialogoSicap,
    QFrame#cuerpoDialogoSicap,
    QFrame#pieDialogoSicap {{
        background: transparent;
        border: none;
    }}
    QScrollArea,
    QScrollArea > QWidget > QWidget,
    QAbstractScrollArea,
    QAbstractScrollArea > QWidget > QWidget {{
        background: transparent;
        border: none;
    }}
    QFrame#bloqueDialogoSicap {{
        background: {color_fondo};
        border: 1px solid {paleta["borde_suave"]};
        border-radius: 4px;
    }}
    QLabel#tituloDialogoSicap {{
        color: {paleta["texto_principal"]};
        font-size: {paleta["tamano_titulo_panel"] + 4}px;
        font-weight: {paleta["peso_titulo"]};
    }}
    QLabel#descripcionDialogoSicap {{
        color: {paleta["texto_suave"]};
        font-size: {paleta["tamano_fuente_base"] + 2}px;
    }}
    QLabel#ayudaCampoDialogoSicap {{
        color: {paleta["texto_suave"]};
        font-size: {paleta["tamano_fuente_base"] + 1}px;
        font-weight: {paleta["peso_subtitulo"]};
    }}
    QLabel#mensajeErrorDialogoSicap {{
        color: {paleta["texto_error"]};
        background: {paleta["fondo_error"]};
        border: 1px solid {paleta["borde_error"]};
        border-radius: 4px;
        padding: 8px 10px;
        font-size: {paleta["tamano_fuente_base"] + 2}px;
        font-weight: {paleta["peso_subtitulo"]};
    }}
    QLabel#etiquetaDatoDialogoSicap {{
        color: {paleta["texto_muted"]};
        font-size: {paleta["tamano_fuente_base"] + 1}px;
        font-weight: {paleta["peso_subtitulo"]};
    }}
    QLabel#valorDatoDialogoSicap {{
        color: {paleta["texto_input"]};
        font-size: {paleta["tamano_fuente_base"] + 2}px;
        font-weight: {paleta["peso_titulo"]};
    }}
    QLineEdit, QComboBox, QPlainTextEdit, QTextEdit, QSpinBox {{
        border: 1px solid {paleta["borde_medio"]};
        border-radius: 4px;
        background: {paleta["fondo_input"]};
        color: {paleta["texto_input"]};
        padding: 8px 10px;
        font-size: {paleta["tamano_fuente_base"] + 2}px;
    }}
    QTableWidget {{
        border: 1px solid {paleta["borde_tabla"]};
        border-radius: 8px;
        background: {paleta["fondo_tabla_cuerpo"]};
        alternate-background-color: {paleta["fondo_tabla_fila_alterna"]};
        color: {paleta["texto_input"]};
        padding: 0px;
        gridline-color: {paleta["borde_tabla"]};
    }}
    QLineEdit:focus, QComboBox:focus, QPlainTextEdit:focus, QTextEdit:focus, QSpinBox:focus {{
        border-color: {paleta["borde_foco_input"]};
        background: {paleta["fondo_input_focus"]};
    }}
    QTableWidget::item {{
        padding: 6px 8px;
        border-bottom: 1px solid {paleta["borde_tabla"]};
        background: {paleta["fondo_tabla_fila"]};
    }}
    QTableWidget::item:alternate {{
        background: {paleta["fondo_tabla_fila_alterna"]};
    }}
    QTableWidget::item:selected {{
        background: {paleta["fondo_tabla_seleccion"]};
        color: {paleta["texto_input"]};
    }}
    QHeaderView::section {{
        background: {paleta["fondo_tabla_header_destacado"]};
        color: {paleta["texto_input"]};
        border: none;
        border-right: 1px solid {paleta["borde_tabla"]};
        border-bottom: 1px solid {paleta["borde_tabla"]};
        padding: 8px;
        font-size: {paleta["tamano_fuente_base"] + 1}px;
        font-weight: {paleta["peso_titulo"]};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 24px;
    }}
    QComboBox QAbstractItemView {{
        background: {paleta["fondo_dialogo"]};
        color: {paleta["texto_input"]};
        selection-background-color: {paleta["fondo_badge_activo"]};
    }}
    QLabel {{
        color: {paleta["texto_input"]};
        font-size: {paleta["tamano_fuente_base"] + 2}px;
        font-weight: {paleta["peso_subtitulo"]};
    }}
    """

ESTILO_DIALOGO_SICAP = _crear_estilo_dialogo_sicap(
    COLOR_FONDO_DIALOGO,
    obtener_paleta_tema_actual(),
)

MAPA_VARIANTES_ACCION: dict[str, dict[str, str]] = {
    "neutro": {
        "fondo": "rgba(255, 255, 255, 0.04)",
        "fondo_hover": "rgba(255, 255, 255, 0.12)",
        "fondo_pressed": "rgba(255, 255, 255, 0.19)",
        "fondo_focus": "rgba(255, 255, 255, 0.10)",
        "borde": "rgba(255, 255, 255, 0.10)",
        "borde_hover": "rgba(255, 255, 255, 0.20)",
        "borde_pressed": "rgba(255, 255, 255, 0.24)",
        "borde_focus": "rgba(255, 255, 255, 0.28)",
        "texto": "#f5fbff",
        "texto_hover": "#ffffff",
        "icono": "#f5fbff",
        "icono_hover": "#ffffff",
    },
    "informacion": {
        "fondo": "rgba(79, 163, 255, 0.10)",
        "fondo_hover": "rgba(46, 127, 255, 0.30)",
        "fondo_pressed": "rgba(32, 110, 226, 0.38)",
        "fondo_focus": "rgba(46, 127, 255, 0.22)",
        "borde": "rgba(131, 195, 255, 0.16)",
        "borde_hover": "rgba(139, 199, 255, 0.42)",
        "borde_pressed": "rgba(164, 214, 255, 0.48)",
        "borde_focus": "rgba(164, 214, 255, 0.56)",
        "texto": "#dff1ff",
        "texto_hover": "#ffffff",
        "icono": "#8ec9ff",
        "icono_hover": "#dff1ff",
    },
    "ayuda": {
        "fondo": "rgba(146, 128, 255, 0.08)",
        "fondo_hover": "rgba(146, 128, 255, 0.18)",
        "fondo_pressed": "rgba(146, 128, 255, 0.24)",
        "fondo_focus": "rgba(146, 128, 255, 0.16)",
        "borde": "rgba(198, 182, 255, 0.16)",
        "borde_hover": "rgba(198, 182, 255, 0.28)",
        "borde_pressed": "rgba(214, 202, 255, 0.34)",
        "borde_focus": "rgba(214, 202, 255, 0.42)",
        "texto": "#f0ebff",
        "texto_hover": "#ffffff",
        "icono": "#c6b6ff",
        "icono_hover": "#f5f1ff",
    },
    "edicion": {
        "fondo": "rgba(247, 204, 122, 0.10)",
        "fondo_hover": "rgba(234, 182, 63, 0.28)",
        "fondo_pressed": "rgba(214, 162, 44, 0.36)",
        "fondo_focus": "rgba(234, 182, 63, 0.20)",
        "borde": "rgba(247, 204, 122, 0.16)",
        "borde_hover": "rgba(247, 204, 122, 0.36)",
        "borde_pressed": "rgba(255, 219, 145, 0.44)",
        "borde_focus": "rgba(255, 219, 145, 0.52)",
        "texto": "#fff4da",
        "texto_hover": "#fffaf0",
        "icono": "#f7cc7a",
        "icono_hover": "#fff0c7",
    },
    "primario": {
        "fondo": "rgba(73, 201, 154, 0.16)",
        "fondo_hover": "rgba(33, 170, 114, 0.34)",
        "fondo_pressed": "rgba(20, 139, 90, 0.44)",
        "fondo_focus": "rgba(33, 170, 114, 0.24)",
        "borde": "rgba(109, 241, 220, 0.18)",
        "borde_hover": "rgba(129, 245, 210, 0.40)",
        "borde_pressed": "rgba(167, 255, 229, 0.48)",
        "borde_focus": "rgba(167, 255, 229, 0.56)",
        "texto": "#ebfffb",
        "texto_hover": "#ffffff",
        "icono": "#9ef3e4",
        "icono_hover": "#ffffff",
    },
    "salida": {
        "fondo": "rgba(182, 62, 52, 0.12)",
        "fondo_hover": "rgba(187, 48, 39, 0.34)",
        "fondo_pressed": "rgba(157, 32, 24, 0.44)",
        "fondo_focus": "rgba(187, 48, 39, 0.22)",
        "borde": "rgba(255, 153, 143, 0.18)",
        "borde_hover": "rgba(255, 137, 126, 0.40)",
        "borde_pressed": "rgba(255, 168, 160, 0.48)",
        "borde_focus": "rgba(255, 168, 160, 0.54)",
        "texto": "#f5fbff",
        "texto_hover": "#ffffff",
        "icono": "#f5fbff",
        "icono_hover": "#ff7c72",
    },
    "advertencia": {
        "fondo": "rgba(255, 206, 120, 0.10)",
        "fondo_hover": "rgba(255, 206, 120, 0.20)",
        "fondo_pressed": "rgba(255, 206, 120, 0.28)",
        "fondo_focus": "rgba(255, 206, 120, 0.16)",
        "borde": "rgba(255, 206, 120, 0.16)",
        "borde_hover": "rgba(255, 206, 120, 0.32)",
        "borde_pressed": "rgba(255, 218, 154, 0.38)",
        "borde_focus": "rgba(255, 218, 154, 0.46)",
        "texto": "#fff5db",
        "texto_hover": "#fffaf0",
        "icono": "#ffcf75",
        "icono_hover": "#fff5db",
    },
}


def _obtener_mapa_variantes_accion(nombre_tema: str) -> dict[str, dict[str, str]]:
    if nombre_tema == "claro":
        return {
            "neutro": {
                "fondo": "rgba(111, 129, 149, 0.08)",
                "fondo_hover": "rgba(111, 129, 149, 0.14)",
                "fondo_pressed": "rgba(111, 129, 149, 0.20)",
                "fondo_focus": "rgba(111, 129, 149, 0.12)",
                "borde": "rgba(131, 145, 164, 0.24)",
                "borde_hover": "rgba(131, 145, 164, 0.34)",
                "borde_pressed": "rgba(131, 145, 164, 0.40)",
                "borde_focus": "rgba(131, 145, 164, 0.48)",
                "texto": "#31465c",
                "texto_hover": "#223548",
                "icono": "#4b6075",
                "icono_hover": "#223548",
            },
            "informacion": {
                "fondo": "rgba(79, 163, 255, 0.12)",
                "fondo_hover": "rgba(46, 127, 255, 0.20)",
                "fondo_pressed": "rgba(46, 127, 255, 0.28)",
                "fondo_focus": "rgba(46, 127, 255, 0.16)",
                "borde": "rgba(79, 163, 255, 0.24)",
                "borde_hover": "rgba(46, 127, 255, 0.34)",
                "borde_pressed": "rgba(46, 127, 255, 0.42)",
                "borde_focus": "rgba(46, 127, 255, 0.48)",
                "texto": "#2e597f",
                "texto_hover": "#1f476d",
                "icono": "#3d84c8",
                "icono_hover": "#1f476d",
            },
            "ayuda": {
                "fondo": "rgba(146, 128, 255, 0.10)",
                "fondo_hover": "rgba(146, 128, 255, 0.18)",
                "fondo_pressed": "rgba(146, 128, 255, 0.24)",
                "fondo_focus": "rgba(146, 128, 255, 0.14)",
                "borde": "rgba(146, 128, 255, 0.22)",
                "borde_hover": "rgba(146, 128, 255, 0.30)",
                "borde_pressed": "rgba(146, 128, 255, 0.38)",
                "borde_focus": "rgba(146, 128, 255, 0.44)",
                "texto": "#5d4ea0",
                "texto_hover": "#4b3f88",
                "icono": "#7262b0",
                "icono_hover": "#4b3f88",
            },
            "edicion": {
                "fondo": "rgba(247, 204, 122, 0.14)",
                "fondo_hover": "rgba(234, 182, 63, 0.24)",
                "fondo_pressed": "rgba(214, 162, 44, 0.30)",
                "fondo_focus": "rgba(234, 182, 63, 0.18)",
                "borde": "rgba(214, 162, 44, 0.22)",
                "borde_hover": "rgba(214, 162, 44, 0.30)",
                "borde_pressed": "rgba(214, 162, 44, 0.38)",
                "borde_focus": "rgba(214, 162, 44, 0.44)",
                "texto": "#8a6521",
                "texto_hover": "#725118",
                "icono": "#b07f2f",
                "icono_hover": "#725118",
            },
            "primario": {
                "fondo": "rgba(73, 201, 154, 0.14)",
                "fondo_hover": "rgba(33, 170, 114, 0.24)",
                "fondo_pressed": "rgba(20, 139, 90, 0.30)",
                "fondo_focus": "rgba(33, 170, 114, 0.18)",
                "borde": "rgba(33, 170, 114, 0.22)",
                "borde_hover": "rgba(33, 170, 114, 0.30)",
                "borde_pressed": "rgba(20, 139, 90, 0.38)",
                "borde_focus": "rgba(20, 139, 90, 0.44)",
                "texto": "#26694b",
                "texto_hover": "#1d563d",
                "icono": "#2f8e66",
                "icono_hover": "#1d563d",
            },
            "salida": {
                "fondo": "rgba(182, 62, 52, 0.12)",
                "fondo_hover": "rgba(187, 48, 39, 0.22)",
                "fondo_pressed": "rgba(157, 32, 24, 0.28)",
                "fondo_focus": "rgba(187, 48, 39, 0.16)",
                "borde": "rgba(182, 62, 52, 0.22)",
                "borde_hover": "rgba(182, 62, 52, 0.32)",
                "borde_pressed": "rgba(157, 32, 24, 0.40)",
                "borde_focus": "rgba(157, 32, 24, 0.46)",
                "texto": "#a84336",
                "texto_hover": "#8f2d21",
                "icono": "#bf5d52",
                "icono_hover": "#8f2d21",
            },
            "advertencia": {
                "fondo": "rgba(255, 206, 120, 0.14)",
                "fondo_hover": "rgba(255, 206, 120, 0.22)",
                "fondo_pressed": "rgba(255, 206, 120, 0.28)",
                "fondo_focus": "rgba(255, 206, 120, 0.18)",
                "borde": "rgba(237, 185, 96, 0.24)",
                "borde_hover": "rgba(237, 185, 96, 0.34)",
                "borde_pressed": "rgba(237, 185, 96, 0.40)",
                "borde_focus": "rgba(237, 185, 96, 0.48)",
                "texto": "#8d6b28",
                "texto_hover": "#73541b",
                "icono": "#b98a3a",
                "icono_hover": "#73541b",
            },
        }
    return MAPA_VARIANTES_ACCION


def resolver_variante_boton_modal(texto: str, variante_sugerida: str = "neutro") -> str:
    """Ajusta la variante visual segun la accion escrita en el boton."""

    texto_normalizado = texto.casefold()
    acciones_destructivas = ("salir", "cerrar", "cancelar", "suspender", "inactivar", "desactivar")
    acciones_informativas = ("detalle", "ver ")
    acciones_positivas = ("guardar", "confirmar", "activar")

    if any(palabra in texto_normalizado for palabra in acciones_destructivas):
        return "salida"
    if any(palabra in texto_normalizado for palabra in acciones_informativas):
        return "informacion"
    if any(palabra in texto_normalizado for palabra in acciones_positivas):
        return "primario"
    return variante_sugerida if variante_sugerida in MAPA_VARIANTES_ACCION else "neutro"


class DialogoBaseSicap(QDialog):
    """Dialogo base para modales coherentes del sistema."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("dialogoBaseSicap")
        self.setModal(True)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setMinimumWidth(420)
        self._nombre_tema = obtener_tema_actual()
        self._paleta_tema = obtener_paleta_tema_actual()
        self._color_fondo_dialogo = str(self._paleta_tema["fondo_dialogo"])
        self._presentacion_preparada = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._tarjeta = QWidget()
        self._tarjeta.setObjectName("tarjetaDialogoSicap")
        self._tarjeta.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._layout_tarjeta = QVBoxLayout(self._tarjeta)
        self._layout_tarjeta.setContentsMargins(
            PADDING_TARJETA_DIALOGO,
            PADDING_TARJETA_DIALOGO,
            PADDING_TARJETA_DIALOGO,
            PADDING_TARJETA_DIALOGO,
        )
        self._layout_tarjeta.setSpacing(ESPACIADO_TARJETA_DIALOGO)

        self._cabecera = QFrame()
        self._cabecera.setObjectName("cabeceraDialogoSicap")
        self._layout_cabecera = QVBoxLayout(self._cabecera)
        self._layout_cabecera.setContentsMargins(0, 0, 0, 0)
        self._layout_cabecera.setSpacing(6)

        self._cuerpo = QFrame()
        self._cuerpo.setObjectName("cuerpoDialogoSicap")
        self._layout_cuerpo = QVBoxLayout(self._cuerpo)
        self._layout_cuerpo.setContentsMargins(0, 0, 0, 0)
        self._layout_cuerpo.setSpacing(10)

        self._pie = QFrame()
        self._pie.setObjectName("pieDialogoSicap")
        self._pie.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._layout_pie = QVBoxLayout(self._pie)
        self._layout_pie.setContentsMargins(0, 0, 0, 0)
        self._layout_pie.setSpacing(0)

        self._layout_tarjeta.addWidget(self._cabecera)
        self._layout_tarjeta.addWidget(self._cuerpo)
        self._layout_tarjeta.addWidget(self._pie)
        layout.addWidget(self._tarjeta)
        self.setStyleSheet(_crear_estilo_dialogo_sicap(self._color_fondo_dialogo, self._paleta_tema))

    def exec(self) -> int:
        self._preparar_presentacion_inicial()
        return super().exec()

    def showEvent(self, evento) -> None:
        super().showEvent(evento)
        if self._presentacion_preparada:
            if self.layout() is not None:
                self.layout().activate()
            self.adjustSize()
            self.resize(self.sizeHint().expandedTo(self.minimumSizeHint()))
            self._centrar_en_pantalla_activa()

    @property
    def layout_cabecera(self) -> QVBoxLayout:
        return self._layout_cabecera

    @property
    def layout_tarjeta(self) -> QVBoxLayout:
        return self._layout_tarjeta

    @property
    def layout_cuerpo(self) -> QVBoxLayout:
        return self._layout_cuerpo

    @property
    def layout_pie(self) -> QVBoxLayout:
        return self._layout_pie

    def aplicar_color_fondo_personalizado(self, color_fondo: str) -> None:
        self._color_fondo_dialogo = color_fondo
        self.setStyleSheet(_crear_estilo_dialogo_sicap(color_fondo, self._paleta_tema))

    def aplicar_tema(self, nombre_tema: str) -> None:
        self._nombre_tema = nombre_tema if nombre_tema in ("oscuro", "claro") else TEMA_SICAP_PREDETERMINADO
        self._paleta_tema = obtener_paleta_tema(self._nombre_tema)
        self._color_fondo_dialogo = str(self._paleta_tema["fondo_dialogo"])
        self.setStyleSheet(_crear_estilo_dialogo_sicap(self._color_fondo_dialogo, self._paleta_tema))
        self._presentacion_preparada = False

    def _preparar_presentacion_inicial(self) -> None:
        if self._presentacion_preparada:
            return
        self.ensurePolished()
        if self.layout() is not None:
            self.layout().activate()
        self.adjustSize()
        tamano_objetivo = self.sizeHint().expandedTo(self.minimumSizeHint())
        self.resize(tamano_objetivo)
        self._centrar_en_pantalla_activa()
        self._presentacion_preparada = True

    def _centrar_en_pantalla_activa(self) -> None:
        pantalla = self.screen()
        if pantalla is None:
            ventana_padre = self.parentWidget().window() if self.parentWidget() is not None else None
            pantalla = (
                None if ventana_padre is None else ventana_padre.screen()
            ) or QApplication.primaryScreen()
        if pantalla is None:
            return

        geometria_disponible = pantalla.availableGeometry()
        geometria_dialogo = self.frameGeometry()
        geometria_dialogo.moveCenter(geometria_disponible.center())

        posicion_x = max(geometria_disponible.left(), geometria_dialogo.left())
        posicion_y = max(geometria_disponible.top(), geometria_dialogo.top())
        posicion_x = min(
            posicion_x,
            geometria_disponible.right() - geometria_dialogo.width() + 1,
        )
        posicion_y = min(
            posicion_y,
            geometria_disponible.bottom() - geometria_dialogo.height() + 1,
        )
        self.move(posicion_x, posicion_y)


class BotonAccionContextual(QPushButton):
    """Boton con iconografia y color funcional consistente."""

    def __init__(
        self,
        texto: str,
        icono: str | None = None,
        variante: str = "neutro",
        centrado: bool = False,
        mostrar_icono: bool = True,
    ) -> None:
        super().__init__(texto)
        self._icono = icono
        self._variante = variante if variante in MAPA_VARIANTES_ACCION else "neutro"
        self._centrado = centrado
        self._mostrar_icono = mostrar_icono and bool(icono)
        self._nombre_tema = obtener_tema_actual()
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setObjectName("botonAccionContextual")
        self.setMinimumHeight(ALTURA_BOTON_DIALOGO)
        self.setIconSize(QSize(16, 16))
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._aplicar_estilos()
        self._actualizar_icono(False)

    def enterEvent(self, evento: object) -> None:
        self._actualizar_icono(True)
        super().enterEvent(evento)

    def leaveEvent(self, evento: object) -> None:
        self._actualizar_icono(False)
        super().leaveEvent(evento)

    def _actualizar_icono(self, hover: bool) -> None:
        if not self._mostrar_icono or not self._icono:
            self.setIcon(QIcon())
            return
        colores = _obtener_mapa_variantes_accion(self._nombre_tema)[self._variante]
        color_icono = colores["icono_hover"] if hover else colores["icono"]
        self.setIcon(obtener_icono_tabler_coloreado(self._icono, color_icono, tamano=18))

    def _aplicar_estilos(self) -> None:
        colores = _obtener_mapa_variantes_accion(self._nombre_tema)[self._variante]
        alineacion = "center" if self._centrado else "left"
        self.setStyleSheet(
            f"""
            QPushButton#botonAccionContextual {{
                min-height: {ALTURA_BOTON_DIALOGO}px;
                border-radius: 4px;
                border: 1px solid {colores["borde"]};
                background: {colores["fondo"]};
                color: {colores["texto"]};
                text-align: {alineacion};
                padding: 0 12px;
                font-size: 12px;
                font-weight: 800;
            }}
            QPushButton#botonAccionContextual:hover {{
                border-color: {colores["borde_hover"]};
                background: {colores["fondo_hover"]};
                color: {colores["texto_hover"]};
            }}
            QPushButton#botonAccionContextual:pressed {{
                background: {colores["fondo_pressed"]};
                border-color: {colores["borde_pressed"]};
                color: {colores["texto_hover"]};
            }}
            QPushButton#botonAccionContextual:focus {{
                background: {colores["fondo_focus"]};
                border-color: {colores["borde_focus"]};
                color: {colores["texto_hover"]};
            }}
            """
        )

    def aplicar_tema(self, nombre_tema: str) -> None:
        self._nombre_tema = nombre_tema if nombre_tema in ("oscuro", "claro") else TEMA_SICAP_PREDETERMINADO
        self._aplicar_estilos()
        self._actualizar_icono(False)


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
        self.setMinimumWidth(420)
        self._cuerpo.setVisible(False)

        label_titulo = QLabel(titulo)
        label_titulo.setObjectName("tituloDialogoSicap")
        label_mensaje = QLabel(mensaje)
        label_mensaje.setObjectName("descripcionDialogoSicap")
        label_mensaje.setWordWrap(True)

        fila_acciones = QHBoxLayout()
        fila_acciones.setContentsMargins(0, 0, 0, 0)
        fila_acciones.setSpacing(10)
        fila_acciones.addStretch(1)
        variante_boton = resolver_variante_boton_modal(texto_boton, variante)
        boton_cerrar = BotonAccionContextual(
            texto_boton,
            variante=variante_boton,
            centrado=True,
            mostrar_icono=False,
        )
        boton_cerrar.setMinimumWidth(136)
        boton_cerrar.clicked.connect(self.accept)
        fila_acciones.addWidget(boton_cerrar)

        self.layout_cabecera.addWidget(label_titulo)
        self.layout_cabecera.addWidget(label_mensaje)
        self.layout_pie.addLayout(fila_acciones)


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
        self.setMinimumWidth(520)

        label_titulo = QLabel(titulo)
        label_titulo.setObjectName("tituloDialogoSicap")
        label_descripcion = QLabel(descripcion)
        label_descripcion.setObjectName("descripcionDialogoSicap")
        label_descripcion.setWordWrap(True)
        self.layout_cabecera.addWidget(label_titulo)
        self.layout_cabecera.addWidget(label_descripcion)

        if detalles:
            titulo_resumen = QLabel("Resumen de la accion")
            titulo_resumen.setObjectName("etiquetaDatoDialogoSicap")
            panel_detalles = QFrame()
            panel_detalles.setObjectName("bloqueDialogoSicap")
            layout_detalles = QVBoxLayout(panel_detalles)
            layout_detalles.setContentsMargins(
                PADDING_BLOQUE_DIALOGO,
                PADDING_BLOQUE_DIALOGO,
                PADDING_BLOQUE_DIALOGO,
                PADDING_BLOQUE_DIALOGO,
            )
            layout_detalles.setSpacing(10)
            for etiqueta, valor in detalles:
                fila = QHBoxLayout()
                fila.setSpacing(10)
                label_etiqueta = QLabel(etiqueta)
                label_etiqueta.setObjectName("etiquetaDatoDialogoSicap")
                label_valor = QLabel(valor)
                label_valor.setObjectName("valorDatoDialogoSicap")
                label_valor.setWordWrap(True)
                fila.addWidget(label_etiqueta, 1)
                fila.addWidget(label_valor, 2)
                layout_detalles.addLayout(fila)
            self.layout_cuerpo.addWidget(titulo_resumen)
            self.layout_cuerpo.addWidget(panel_detalles)
        else:
            self._cuerpo.setVisible(False)

        fila_acciones = QHBoxLayout()
        fila_acciones.setContentsMargins(0, 0, 0, 0)
        fila_acciones.setSpacing(10)
        variante_cancelar = resolver_variante_boton_modal("Cancelar", "neutro")
        variante_confirmacion = resolver_variante_boton_modal(texto_confirmar, variante_confirmar)
        boton_cancelar = BotonAccionContextual(
            "Cancelar",
            variante=variante_cancelar,
            centrado=True,
            mostrar_icono=False,
        )
        boton_confirmar = BotonAccionContextual(
            texto_confirmar,
            variante=variante_confirmacion,
            centrado=True,
            mostrar_icono=False,
        )
        boton_cancelar.setMinimumWidth(132)
        boton_confirmar.setMinimumWidth(160)
        boton_cancelar.clicked.connect(self.reject)
        boton_confirmar.clicked.connect(self.accept)
        fila_acciones.addWidget(boton_cancelar)
        fila_acciones.addStretch(1)
        fila_acciones.addWidget(boton_confirmar)
        self.layout_pie.addLayout(fila_acciones)
        if color_fondo:
            self.aplicar_color_fondo_personalizado(color_fondo)


class TarjetaKPI(QFrame):
    """Tarjeta compacta para metricas del dashboard."""

    def __init__(self, titulo: str, valor: str, detalle: str = "") -> None:
        super().__init__()
        self.setObjectName("tarjetaKPI")
        self._tema_actual = obtener_tema_actual()
        self._paleta_tema = obtener_paleta_tema_actual()
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
        paleta = self._paleta_tema
        self.setStyleSheet(
            f"""
            QFrame#tarjetaKPI {{
                background-color: {paleta["fondo_superficie_suave"]};
                border: 1px solid {paleta["borde_suave"]};
                border-radius: 20px;
                font-family: "{paleta["familia_tipografica"]}";
            }}
            QLabel#kpiTitulo {{
                color: {paleta["texto_secundario"]};
                font-size: {paleta["tamano_fuente_base"] + 2}px;
                font-weight: {paleta["peso_subtitulo"]};
                letter-spacing: 0.04em;
            }}
            QLabel#kpiValor {{
                color: {paleta["texto_principal"]};
                font-size: {paleta["tamano_titulo_tarjeta"] + 10}px;
                font-weight: {paleta["peso_titulo"]};
            }}
            QLabel#kpiDetalle {{
                color: {paleta["texto_secundario"]};
                font-size: {paleta["tamano_fuente_base"] + 2}px;
            }}
            """
        )

    def aplicar_tema(self, nombre_tema: str) -> None:
        self._tema_actual = (
            nombre_tema if nombre_tema in ("oscuro", "claro") else TEMA_SICAP_PREDETERMINADO
        )
        self._paleta_tema = obtener_paleta_tema(self._tema_actual)
        self._aplicar_estilos()


class VistaPlaceholderModulo(QWidget):
    """Pantalla profesional para modulos todavia no implementados."""

    def __init__(self, titulo: str, descripcion: str) -> None:
        super().__init__()
        self.setObjectName("vistaPlaceholderModulo")
        self._tema_actual = obtener_tema_actual()
        self._paleta_tema = obtener_paleta_tema_actual()
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
        paleta = self._paleta_tema
        self.setStyleSheet(
            f"""
            QWidget#vistaPlaceholderModulo {{
                background-color: transparent;
            }}
            QFrame#tarjetaPlaceholder {{
                background-color: {paleta["fondo_superficie"]};
                border: 1px solid {paleta["borde_principal"]};
                border-radius: 22px;
            }}
            QLabel#placeholderTitulo {{
                color: {paleta["texto_principal"]};
                font-size: {paleta["tamano_titulo_modulo"]}px;
                font-weight: {paleta["peso_titulo"]};
                font-family: "{paleta["familia_tipografica"]}";
            }}
            QLabel#placeholderDescripcion {{
                color: {paleta["texto_secundario"]};
                font-size: {paleta["tamano_fuente_base"] + 4}px;
            }}
            QLabel#placeholderAviso {{
                color: {paleta["texto_advertencia"]};
                background-color: {paleta["fondo_advertencia"]};
                border: 1px solid {paleta["borde_advertencia"]};
                border-radius: 14px;
                padding: 10px 12px;
                font-size: {paleta["tamano_fuente_base"] + 3}px;
                font-weight: {paleta["peso_subtitulo"]};
            }}
            """
        )

    def aplicar_tema(self, nombre_tema: str) -> None:
        self._tema_actual = nombre_tema if nombre_tema in ("oscuro", "claro") else TEMA_SICAP_PREDETERMINADO
        self._paleta_tema = obtener_paleta_tema(self._tema_actual)
        self._aplicar_estilos()


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


def aplicar_estilo_boton_operativo(boton: QPushButton, principal: bool = False) -> None:
    """Aplica el estilo visual del boton operativo segun el tema activo."""
    paleta = obtener_paleta_tema_actual()
    hover_primario = (
        paleta["fondo_superficie_suave"]
        if paleta["nombre"] == "claro"
        else "rgba(31, 52, 99, 0.96)"
    )
    pressed_primario = (
        paleta["fondo_superficie"]
        if paleta["nombre"] == "claro"
        else "rgba(18, 32, 64, 0.98)"
    )
    boton.setStyleSheet(
        f"""
        QPushButton#botonOperativo,
        QPushButton#botonOperativoPrimario {{
            border-radius: 12px;
            font-size: 12px;
            font-weight: 700;
            padding: 0 14px;
            min-height: 36px;
        }}
        QPushButton#botonOperativo {{
            background-color: {paleta["fondo_input"]};
            border: 1px solid {paleta["borde_medio"]};
            color: {paleta["texto_input"]};
        }}
        QPushButton#botonOperativo:hover {{
            background-color: {paleta["fondo_superficie"]};
            border-color: {paleta["borde_principal"]};
        }}
        QPushButton#botonOperativo:pressed {{
            background-color: {paleta["fondo_superficie_suave"]};
        }}
        QPushButton#botonOperativoPrimario {{
            background-color: {paleta["fondo_dialogo"]};
            border: 1px solid {paleta["borde_suave"]};
            color: {paleta["texto_principal"]};
        }}
        QPushButton#botonOperativoPrimario:hover {{
            background-color: {hover_primario};
        }}
        QPushButton#botonOperativoPrimario:pressed {{
            background-color: {pressed_primario};
        }}
        """
    )


def crear_boton_operativo(texto: str, principal: bool = False) -> QPushButton:
    """Crea un boton consistente para acciones de modulos."""
    boton = QPushButton(texto)
    boton.setCursor(Qt.CursorShape.PointingHandCursor)
    boton.setObjectName("botonOperativoPrimario" if principal else "botonOperativo")
    boton.setMinimumHeight(36)
    aplicar_estilo_boton_operativo(boton, principal=principal)
    return boton
