"""Componentes reutilizables para pantallas operativas de SIGQUA."""

from __future__ import annotations

import shiboken6

from PySide6.QtCore import QEvent, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QIcon, QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCompleter,
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLayout,
    QLabel,
    QLineEdit,
    QListView,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from comun.ui.iconos import obtener_icono_tabler_coloreado
from comun.ui.qt_mensajes import configurar_filtro_mensajes_qt
from comun.ui.temas import (
    TEMA_SIGQUA_PREDETERMINADO,
    obtener_paleta_tema,
    obtener_paleta_tema_actual,
    obtener_tema_actual,
    resolver_nombre_tema,
)
from comun.utilidades.moneda import formatear_monto_desde_centavos, parsear_monto_a_centavos


_PALETA_BASE = obtener_paleta_tema_actual()
COLOR_TEXTO_PRIMARIO = str(_PALETA_BASE["texto_principal"])
COLOR_TEXTO_SECUNDARIO = str(_PALETA_BASE["texto_secundario"])
COLOR_BORDE = str(_PALETA_BASE["borde_principal"])
COLOR_FONDO_PANEL = str(_PALETA_BASE["fondo_superficie_suave"])
COLOR_FONDO_DIALOGO = str(_PALETA_BASE["modal_fondo"])
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


class CampoBusquedaSeleccionSigqua(QWidget):
    """Campo reutilizable para buscar y seleccionar registros grandes por ID real."""

    RESULTADOS_VISIBLES_MAX = 7
    seleccion_cambiada = Signal(object, str)

    def __init__(
        self,
        texto_sin_resultados: str,
        placeholder: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("campoBusquedaSeleccionSigqua")
        self._texto_sin_resultados = texto_sin_resultados
        self._opciones: list[tuple[int, str]] = []
        self._opciones_por_id: dict[int, str] = {}
        self._identificador_seleccionado: int | None = None
        self._texto_seleccionado = ""
        self._actualizando_texto = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._campo = QLineEdit()
        self._campo.setObjectName("campoBusquedaSeleccionSigqua")
        self._campo.setPlaceholderText(placeholder)
        self._campo.installEventFilter(self)
        layout.addWidget(self._campo)

        self._modelo_resultados = QStandardItemModel(self)
        self._popup = QListView()
        self._popup.setObjectName("popupBusquedaSeleccionSigqua")
        self._popup.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._popup.setUniformItemSizes(True)

        self._completer = QCompleter(self._modelo_resultados, self)
        self._completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._completer.setCompletionMode(QCompleter.CompletionMode.UnfilteredPopupCompletion)
        self._completer.setMaxVisibleItems(self.RESULTADOS_VISIBLES_MAX)
        self._completer.setPopup(self._popup)
        self._campo.setCompleter(self._completer)

        self._campo.textEdited.connect(self._al_editar_texto)
        self._campo.editingFinished.connect(self._normalizar_seleccion_manual)
        self._popup.clicked.connect(self._seleccionar_desde_indice)
        self._popup.activated.connect(self._seleccionar_desde_indice)

    def eventFilter(self, origen: object, evento: QEvent) -> bool:
        if origen is self._campo and evento.type() == QEvent.Type.FocusIn:
            self._mostrar_resultados(self._campo.text().strip())
        return super().eventFilter(origen, evento)

    def establecer_opciones(self, opciones: list[tuple[int, str]]) -> None:
        self._opciones = list(opciones)
        self._opciones_por_id = {identificador: etiqueta for identificador, etiqueta in self._opciones}
        self._mostrar_resultados(self._campo.text().strip())

    def seleccionar_por_id(self, identificador: int | None, etiqueta_fallback: str = "") -> None:
        if identificador is None:
            self._establecer_seleccion(None, "")
            return
        etiqueta = self._opciones_por_id.get(int(identificador), etiqueta_fallback)
        self._establecer_seleccion(int(identificador), etiqueta)

    def identificador_seleccionado(self) -> int | None:
        return self._identificador_seleccionado

    def texto_seleccionado(self) -> str:
        return self._campo.text().strip()

    def setPlaceholderText(self, texto: str) -> None:
        self._campo.setPlaceholderText(texto)

    def setEnabled(self, habilitado: bool) -> None:
        super().setEnabled(habilitado)
        self._campo.setEnabled(habilitado)

    def setFocus(self, reason: Qt.FocusReason = Qt.FocusReason.OtherFocusReason) -> None:
        self._campo.setFocus(reason)

    def _al_editar_texto(self, texto: str) -> None:
        texto = texto.strip()
        if texto != self._texto_seleccionado:
            if self._identificador_seleccionado is not None or self._texto_seleccionado:
                self._identificador_seleccionado = None
                self._texto_seleccionado = ""
                self.seleccion_cambiada.emit(None, "")
        self._mostrar_resultados(texto)

    def _normalizar_seleccion_manual(self) -> None:
        if self._actualizando_texto:
            return
        texto = self._campo.text().strip()
        if not texto:
            self._establecer_seleccion(None, "")
            return
        coincidencias_exactas = [
            (identificador, etiqueta)
            for identificador, etiqueta in self._opciones
            if etiqueta.casefold() == texto.casefold()
        ]
        if len(coincidencias_exactas) == 1:
            identificador, etiqueta = coincidencias_exactas[0]
            self._establecer_seleccion(identificador, etiqueta)

    def _mostrar_resultados(self, texto: str) -> None:
        self._modelo_resultados.clear()
        coincidencias = [
            (identificador, etiqueta)
            for identificador, etiqueta in self._opciones
            if not texto or texto.casefold() in etiqueta.casefold()
        ]
        if not coincidencias:
            item_vacio = QStandardItem(self._texto_sin_resultados)
            item_vacio.setEditable(False)
            item_vacio.setSelectable(False)
            item_vacio.setEnabled(False)
            self._modelo_resultados.appendRow(item_vacio)
        else:
            for identificador, etiqueta in coincidencias:
                item = QStandardItem(etiqueta)
                item.setData(int(identificador), Qt.ItemDataRole.UserRole)
                item.setEditable(False)
                self._modelo_resultados.appendRow(item)
        if self.isEnabled() and self._campo.hasFocus():
            self._completer.complete()

    def _seleccionar_desde_indice(self, indice) -> None:
        identificador = indice.data(Qt.ItemDataRole.UserRole)
        etiqueta = str(indice.data(Qt.ItemDataRole.DisplayRole) or "").strip()
        if identificador is None or not etiqueta:
            return
        self._establecer_seleccion(int(identificador), etiqueta)
        self._popup.hide()

    def _establecer_seleccion(self, identificador: int | None, etiqueta: str) -> None:
        self._identificador_seleccionado = identificador
        self._texto_seleccionado = etiqueta
        self._actualizando_texto = True
        self._campo.setText(etiqueta)
        self._actualizando_texto = False
        self.seleccion_cambiada.emit(identificador, etiqueta)


def _crear_estilo_dialogo_sigqua(color_fondo: str, paleta: dict[str, object]) -> str:
    return f"""
    QDialog#dialogoBaseSigqua {{
        background: {paleta["modal_fondo"]};
        border: 1px solid {paleta["modal_borde"]};
        border-radius: 4px;
        font-family: "{paleta["familia_tipografica"]}";
    }}
    QWidget#tarjetaDialogoSigqua {{
        background: {paleta["modal_fondo"]};
        border: none;
    }}
    QFrame#cabeceraDialogoSigqua,
    QFrame#cuerpoDialogoSigqua {{
        background: transparent;
        border: none;
    }}
    QFrame#pieDialogoSigqua {{
        background: {paleta["modal_footer_fondo"]};
        border: none;
        border-top: 1px solid {paleta["modal_footer_separador"]};
        margin-top: 2px;
        padding-top: 8px;
    }}
    QScrollArea,
    QScrollArea > QWidget > QWidget,
    QAbstractScrollArea,
    QAbstractScrollArea > QWidget > QWidget {{
        background: transparent;
        border: none;
    }}
    QFrame#bloqueDialogoSigqua {{
        background: {paleta["modal_fondo_seccion"]};
        border: 1px solid {paleta["modal_borde"]};
        border-radius: 4px;
    }}
    QLabel#tituloDialogoSigqua {{
        color: {paleta["modal_titulo"]};
        font-size: {paleta["tamano_titulo_panel"] + 4}px;
        font-weight: {paleta["peso_titulo"]};
    }}
    QLabel#descripcionDialogoSigqua {{
        color: {paleta["modal_texto"]};
        font-size: {paleta["tamano_fuente_base"] + 2}px;
    }}
    QLabel#ayudaCampoDialogoSigqua {{
        color: {paleta["modal_texto_secundario"]};
        font-size: {paleta["tamano_fuente_base"] + 1}px;
        font-weight: {paleta["peso_subtitulo"]};
    }}
    QLabel#mensajeErrorDialogoSigqua {{
        color: {paleta["texto_error"]};
        background: {paleta["fondo_error"]};
        border: 1px solid {paleta["borde_error"]};
        border-radius: 4px;
        padding: 8px 10px;
        font-size: {paleta["tamano_fuente_base"] + 2}px;
        font-weight: {paleta["peso_subtitulo"]};
    }}
    QLabel#etiquetaDatoDialogoSigqua {{
        color: {paleta["modal_texto_secundario"]};
        font-size: {paleta["tamano_fuente_base"] + 1}px;
        font-weight: {paleta["peso_subtitulo"]};
    }}
    QLabel#valorDatoDialogoSigqua {{
        color: {paleta["modal_titulo"]};
        font-size: {paleta["tamano_fuente_base"] + 2}px;
        font-weight: {paleta["peso_titulo"]};
    }}
    QLineEdit, QComboBox, QPlainTextEdit, QTextEdit, QSpinBox {{
        border: 1px solid {paleta["borde_medio"]};
        border-radius: 4px;
        background: {paleta["modal_fondo_campo"]};
        color: {paleta["modal_titulo"]};
        padding: 6px 8px;
        font-size: {paleta["tamano_fuente_base"] + 2}px;
    }}
    QLineEdit, QComboBox, QSpinBox, QWidget#campoBusquedaSeleccionSigqua QLineEdit {{
        min-height: 18px;
    }}
    QPlainTextEdit, QTextEdit {{
        padding-top: 6px;
        padding-bottom: 6px;
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
        background: {paleta["modal_fondo"]};
        color: {paleta["modal_titulo"]};
        selection-background-color: {paleta["fondo_badge_activo"]};
    }}
    QListView#popupBusquedaSeleccionSigqua {{
        background: {paleta["modal_fondo"]};
        color: {paleta["modal_titulo"]};
        border: 1px solid {paleta["modal_borde"]};
        border-radius: 4px;
        outline: none;
        padding: 2px;
    }}
    QListView#popupBusquedaSeleccionSigqua::item {{
        padding: 6px 8px;
        min-height: 18px;
    }}
    QListView#popupBusquedaSeleccionSigqua::item:selected {{
        background: {paleta["fondo_badge_activo"]};
        color: {paleta["texto_principal"]};
    }}
    QLabel {{
        color: {paleta["modal_texto"]};
        font-size: {paleta["tamano_fuente_base"] + 2}px;
        font-weight: {paleta["peso_subtitulo"]};
    }}
    """

ESTILO_DIALOGO_SIGQUA = _crear_estilo_dialogo_sigqua(
    COLOR_FONDO_DIALOGO,
    obtener_paleta_tema_actual(),
)

def _crear_mapa_variantes_accion(paleta: dict[str, object]) -> dict[str, dict[str, str]]:
    return {
        "neutro": {
            "fondo": str(paleta["boton_secundario_fondo"]),
            "fondo_hover": str(paleta["boton_secundario_hover"]),
            "fondo_pressed": str(paleta["fondo_menu_activo"]),
            "fondo_focus": str(paleta["boton_secundario_hover"]),
            "borde": str(paleta["borde_suave"]),
            "borde_hover": str(paleta["borde_principal"]),
            "borde_pressed": str(paleta["borde_foco_input"]),
            "borde_focus": str(paleta["borde_foco_input"]),
            "texto": str(paleta["boton_secundario_texto"]),
            "texto_hover": str(paleta["texto_destacado"]),
            "icono": str(paleta["modal_icono_accion"]),
            "icono_hover": str(paleta["texto_destacado"]),
        },
        "informacion": {
            "fondo": str(paleta["fondo_info"]),
            "fondo_hover": str(paleta["boton_secundario_hover"]),
            "fondo_pressed": str(paleta["acento_seleccion"]),
            "fondo_focus": str(paleta["boton_secundario_hover"]),
            "borde": str(paleta["borde_info"]),
            "borde_hover": str(paleta["borde_principal"]),
            "borde_pressed": str(paleta["borde_foco_input"]),
            "borde_focus": str(paleta["borde_foco_input"]),
            "texto": str(paleta["texto_secundario"]),
            "texto_hover": str(paleta["texto_principal"]),
            "icono": str(paleta["icono_tema_inactivo"]),
            "icono_hover": str(paleta["icono_tema_activo"]),
        },
        "ayuda": {
            "fondo": str(paleta["fondo_panel_accion"]),
            "fondo_hover": str(paleta["boton_secundario_hover"]),
            "fondo_pressed": str(paleta["fondo_menu_activo"]),
            "fondo_focus": str(paleta["boton_secundario_hover"]),
            "borde": str(paleta["borde_suave"]),
            "borde_hover": str(paleta["borde_principal"]),
            "borde_pressed": str(paleta["borde_foco_input"]),
            "borde_focus": str(paleta["borde_foco_input"]),
            "texto": str(paleta["texto_secundario"]),
            "texto_hover": str(paleta["texto_destacado"]),
            "icono": str(paleta["icono_tarjeta_help"]),
            "icono_hover": str(paleta["texto_destacado"]),
        },
        "edicion": {
            "fondo": str(paleta["fondo_advertencia"]),
            "fondo_hover": "rgba(245, 184, 75, 0.26)",
            "fondo_pressed": "rgba(245, 184, 75, 0.34)",
            "fondo_focus": "rgba(245, 184, 75, 0.26)",
            "borde": str(paleta["borde_advertencia"]),
            "borde_hover": "rgba(245, 184, 75, 0.46)",
            "borde_pressed": "rgba(245, 184, 75, 0.54)",
            "borde_focus": "rgba(245, 184, 75, 0.54)",
            "texto": str(paleta["texto_advertencia"]),
            "texto_hover": str(paleta["texto_advertencia"]),
            "icono": str(paleta["icono_editar"]),
            "icono_hover": str(paleta["icono_editar"]),
        },
        "primario": {
            "fondo": str(paleta["boton_primario_fondo"]),
            "fondo_hover": str(paleta["boton_primario_hover"]),
            "fondo_pressed": str(paleta["acento_hover"]),
            "fondo_focus": str(paleta["boton_primario_hover"]),
            "borde": str(paleta["borde_info"]),
            "borde_hover": str(paleta["borde_foco_input"]),
            "borde_pressed": str(paleta["borde_foco_input"]),
            "borde_focus": str(paleta["borde_foco_input"]),
            "texto": str(paleta["boton_primario_texto"]),
            "texto_hover": str(paleta["boton_primario_texto"]),
            "icono": str(paleta["modal_icono_accion_principal"]),
            "icono_hover": str(paleta["modal_icono_accion_principal"]),
        },
        "salida": {
            "fondo": str(paleta["boton_peligro_fondo"]),
            "fondo_hover": str(paleta["boton_peligro_hover"]),
            "fondo_pressed": "#B95562",
            "fondo_focus": str(paleta["boton_peligro_hover"]),
            "borde": str(paleta["borde_error"]),
            "borde_hover": "rgba(242, 116, 116, 0.46)",
            "borde_pressed": "rgba(242, 116, 116, 0.54)",
            "borde_focus": "rgba(242, 116, 116, 0.54)",
            "texto": str(paleta["boton_peligro_texto"]),
            "texto_hover": str(paleta["boton_peligro_texto"]),
            "icono": str(paleta["boton_peligro_texto"]),
            "icono_hover": str(paleta["boton_peligro_texto"]),
        },
        "advertencia": {
            "fondo": str(paleta["fondo_advertencia"]),
            "fondo_hover": "rgba(245, 184, 75, 0.26)",
            "fondo_pressed": "rgba(245, 184, 75, 0.34)",
            "fondo_focus": "rgba(245, 184, 75, 0.26)",
            "borde": str(paleta["borde_advertencia"]),
            "borde_hover": "rgba(245, 184, 75, 0.46)",
            "borde_pressed": "rgba(245, 184, 75, 0.54)",
            "borde_focus": "rgba(245, 184, 75, 0.54)",
            "texto": str(paleta["texto_advertencia"]),
            "texto_hover": str(paleta["texto_advertencia"]),
            "icono": str(paleta["icono_aviso"]),
            "icono_hover": str(paleta["icono_aviso"]),
        },
    }


MAPA_VARIANTES_ACCION: dict[str, dict[str, str]] = _crear_mapa_variantes_accion(
    obtener_paleta_tema_actual()
)


def _obtener_mapa_variantes_accion(nombre_tema: str) -> dict[str, dict[str, str]]:
    return _crear_mapa_variantes_accion(obtener_paleta_tema(nombre_tema))


def resolver_variante_boton_modal(texto: str, variante_sugerida: str = "neutro") -> str:
    """Ajusta la variante visual segun la accion escrita en el boton."""

    texto_normalizado = texto.casefold()
    alias_variantes = {
        "peligro": "salida",
        "destructivo": "salida",
    }
    variante_resuelta = alias_variantes.get(variante_sugerida, variante_sugerida)
    if texto_normalizado == "cancelar":
        return "neutro"
    acciones_destructivas = ("salir", "cerrar sistema", "suspender", "inactivar", "desactivar")
    acciones_informativas = ("detalle", "ver ")
    acciones_positivas = ("guardar", "confirmar", "activar")

    if any(palabra in texto_normalizado for palabra in acciones_destructivas):
        return "salida"
    if any(palabra in texto_normalizado for palabra in acciones_informativas):
        return "informacion"
    if any(palabra in texto_normalizado for palabra in acciones_positivas):
        return "primario"
    return variante_resuelta if variante_resuelta in MAPA_VARIANTES_ACCION else "neutro"


class DialogoBaseSigqua(QDialog):
    """Dialogo base para modales coherentes del sistema."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("dialogoBaseSigqua")
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
        self._tarjeta.setObjectName("tarjetaDialogoSigqua")
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
        self._cabecera.setObjectName("cabeceraDialogoSigqua")
        self._layout_cabecera = QVBoxLayout(self._cabecera)
        self._layout_cabecera.setContentsMargins(0, 0, 0, 0)
        self._layout_cabecera.setSpacing(6)

        self._cuerpo = QFrame()
        self._cuerpo.setObjectName("cuerpoDialogoSigqua")
        self._layout_cuerpo = QVBoxLayout(self._cuerpo)
        self._layout_cuerpo.setContentsMargins(0, 0, 0, 0)
        self._layout_cuerpo.setSpacing(10)

        self._pie = QFrame()
        self._pie.setObjectName("pieDialogoSigqua")
        self._pie.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._layout_pie = QVBoxLayout(self._pie)
        self._layout_pie.setContentsMargins(0, 0, 0, 0)
        self._layout_pie.setSpacing(0)

        self._layout_tarjeta.addWidget(self._cabecera)
        self._layout_tarjeta.addWidget(self._cuerpo)
        self._layout_tarjeta.addWidget(self._pie)
        layout.addWidget(self._tarjeta)
        self.setStyleSheet(_crear_estilo_dialogo_sigqua(self._color_fondo_dialogo, self._paleta_tema))

    def exec(self) -> int:
        self._preparar_presentacion_inicial()
        return super().exec()

    def showEvent(self, evento) -> None:
        super().showEvent(evento)
        if self._presentacion_preparada:
            if self.layout() is not None:
                self.layout().activate()
            self.adjustSize()
            self.resize(self._obtener_tamano_presentacion())
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

    def crear_area_scroll_cuerpo(
        self,
        contenido: QWidget,
        object_name: str = "scrollCuerpoDialogoSigqua",
    ) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setObjectName(object_name)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setWidget(contenido)
        return scroll

    def aplicar_color_fondo_personalizado(self, color_fondo: str) -> None:
        self._color_fondo_dialogo = color_fondo
        self.setStyleSheet(_crear_estilo_dialogo_sigqua(color_fondo, self._paleta_tema))

    def aplicar_tema(self, nombre_tema: str) -> None:
        self._nombre_tema = resolver_nombre_tema(nombre_tema)
        self._paleta_tema = obtener_paleta_tema(self._nombre_tema)
        self._color_fondo_dialogo = str(self._paleta_tema["fondo_dialogo"])
        self.setStyleSheet(_crear_estilo_dialogo_sigqua(self._color_fondo_dialogo, self._paleta_tema))
        self._presentacion_preparada = False

    def _preparar_presentacion_inicial(self) -> None:
        if self._presentacion_preparada:
            return
        self.ensurePolished()
        if self.layout() is not None:
            self.layout().activate()
        self.adjustSize()
        self.resize(self._obtener_tamano_presentacion())
        self._centrar_en_pantalla_activa()
        self._presentacion_preparada = True

    def _obtener_tamano_presentacion(self) -> QSize:
        tamano = self.sizeHint().expandedTo(self.minimumSizeHint())
        geometria_disponible = self._obtener_geometria_disponible()
        if geometria_disponible is None:
            return tamano
        ancho_maximo = max(360, geometria_disponible.width() - 72)
        alto_maximo = max(280, geometria_disponible.height() - 88)
        tamano.setWidth(min(tamano.width(), ancho_maximo))
        tamano.setHeight(min(tamano.height(), alto_maximo))
        return tamano

    def _centrar_en_pantalla_activa(self) -> None:
        geometria_disponible = self._obtener_geometria_disponible()
        if geometria_disponible is None:
            return
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

    def _obtener_geometria_disponible(self):
        pantalla = self.screen()
        if pantalla is None:
            ventana_padre = self.parentWidget().window() if self.parentWidget() is not None else None
            pantalla = (
                None if ventana_padre is None else ventana_padre.screen()
            ) or QApplication.primaryScreen()
        if pantalla is None:
            return None
        return pantalla.availableGeometry()


def obtener_estilo_detalle_sigqua(nombre_tema: str | None = None) -> str:
    """Devuelve el stylesheet comun para modales de detalle administrativos."""
    paleta = obtener_paleta_tema(
        resolver_nombre_tema(nombre_tema or obtener_tema_actual())
    )
    radio = RADIO_TARJETA_DIALOGO
    return f"""
    QFrame#panelDetalleSigqua {{
        background: {paleta["fondo_dialogo"]};
        border: 1px solid {paleta["borde_principal"]};
        border-radius: {radio}px;
    }}
    QFrame#seccionDetalleSigqua {{
        background: {paleta["fondo_superficie"]};
        border: 1px solid {paleta["borde_principal"]};
        border-radius: {radio}px;
    }}
    QFrame#campoDetalleSigqua,
    QFrame#tarjetaResumenDetalleSigqua {{
        background: {paleta["fondo_superficie_suave"]};
        border: 1px solid {paleta["borde_suave"]};
        border-radius: {radio}px;
    }}
    QLabel#codigoIdentificacionDetalleSigqua {{
        color: {paleta["icono_tarjeta_info"]};
        font-size: 12px;
        font-weight: 800;
        letter-spacing: 0.08em;
    }}
    QLabel#nombreIdentificacionDetalleSigqua {{
        color: {paleta["texto_principal"]};
        font-size: 19px;
        font-weight: 900;
    }}
    QLabel#tituloSeccionDetalleSigqua {{
        color: {paleta["texto_principal"]};
        font-size: 14px;
        font-weight: 800;
    }}
    QLabel#descripcionSeccionDetalleSigqua,
    QLabel#etiquetaCampoDetalleSigqua {{
        color: {paleta["texto_suave"]};
        font-size: 11px;
        font-weight: 600;
    }}
    QLabel#valorCampoDetalleSigqua {{
        color: {paleta["texto_principal"]};
        font-size: 13px;
        font-weight: 700;
    }}
    QLabel#valorResumenDetalleSigqua {{
        color: {paleta["texto_principal"]};
        font-size: 15px;
        font-weight: 800;
    }}
    QLabel#badgeEstadoDetalleSigqua {{
        border-radius: 11px;
        padding: 6px 10px;
        font-size: 11px;
        font-weight: 800;
        color: {paleta["texto_badge"]};
        background: {paleta["fondo_badge"]};
        border: 1px solid {paleta["borde_suave"]};
    }}
    QLabel#badgeEstadoDetalleSigqua[tono="activo"] {{
        color: {paleta["texto_badge_activo"]};
        background: {paleta["fondo_badge_activo"]};
        border-color: {paleta["borde_badge_activo"]};
    }}
    QLabel#badgeEstadoDetalleSigqua[tono="info"] {{
        color: {paleta["texto_info"]};
        background: {paleta["fondo_info"]};
        border-color: {paleta["borde_info"]};
    }}
    QLabel#badgeEstadoDetalleSigqua[tono="advertencia"] {{
        color: {paleta["texto_advertencia"]};
        background: {paleta["fondo_advertencia"]};
        border-color: {paleta["borde_advertencia"]};
    }}
    QLabel#badgeEstadoDetalleSigqua[tono="error"] {{
        color: {paleta["texto_error"]};
        background: {paleta["fondo_error"]};
        border-color: {paleta["borde_error"]};
    }}
    QToolButton#botonCopiarIdDetalle {{
        min-height: 22px;
        min-width: 62px;
        padding: 0 10px;
        border-radius: {radio}px;
        border: 1px solid {paleta["borde_suave"]};
        background: {paleta["fondo_superficie_suave"]};
        color: {paleta["texto_secundario"]};
        font-size: 10px;
        font-weight: 800;
    }}
    QToolButton#botonCopiarIdDetalle:hover {{
        border-color: {paleta["borde_principal"]};
        background: {paleta["fondo_superficie_muy_suave"]};
        color: {paleta["texto_principal"]};
    }}
    QToolButton#botonCopiarIdDetalle[copiado="true"] {{
        border-color: {paleta["borde_badge_activo"]};
        background: {paleta["fondo_badge_activo"]};
        color: {paleta["texto_badge_activo"]};
    }}
    """


def crear_badge_estado_detalle_sigqua(
    texto: str,
    tono: str = "neutro",
) -> QLabel:
    """Crea un badge semantico comun para encabezados de detalle."""
    badge = QLabel(texto)
    badge.setObjectName("badgeEstadoDetalleSigqua")
    badge.setProperty("tono", tono if tono in {"activo", "info", "advertencia", "error"} else "neutro")
    badge.style().unpolish(badge)
    badge.style().polish(badge)
    return badge


def crear_boton_copiar_detalle_sigqua(
    valor_copiable: str,
    *,
    etiqueta: str,
) -> QToolButton:
    """Crea la microaccion comun de copia rapida para encabezados de detalle."""
    boton = QToolButton()
    valor_copiable = valor_copiable.strip()
    boton.setObjectName("botonCopiarIdDetalle")
    boton.setText("COPIAR")
    boton.setProperty("copiado", False)
    boton.setCursor(Qt.CursorShape.PointingHandCursor)
    boton.setToolTip(f"Copiar {etiqueta}: {valor_copiable or 'Sin registro'}")
    boton.setAutoRaise(False)
    boton.setEnabled(bool(valor_copiable))

    def _restaurar() -> None:
        if not shiboken6.isValid(boton):
            return
        boton.setText("COPIAR")
        boton.setProperty("copiado", False)
        boton.style().unpolish(boton)
        boton.style().polish(boton)
        boton.setToolTip(f"Copiar {etiqueta}: {valor_copiable or 'Sin registro'}")

    def _copiar() -> None:
        QApplication.clipboard().setText(valor_copiable)
        boton.setText("OK")
        boton.setProperty("copiado", True)
        boton.style().unpolish(boton)
        boton.style().polish(boton)
        boton.setToolTip(f"{etiqueta} copiado: {valor_copiable}")
        QTimer.singleShot(900, _restaurar)

    boton.clicked.connect(_copiar)
    return boton


class EncabezadoDetalleSigqua(QWidget):
    """Bloque comun de identificacion principal para modales de detalle."""

    def __init__(
        self,
        codigo: str,
        nombre: str,
        *,
        boton_copiar: QToolButton | None = None,
        badges: tuple[QWidget, ...] = (),
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        bloque_principal = QVBoxLayout()
        bloque_principal.setContentsMargins(0, 0, 0, 0)
        bloque_principal.setSpacing(4)

        fila_codigo = QHBoxLayout()
        fila_codigo.setContentsMargins(0, 0, 0, 0)
        fila_codigo.setSpacing(6)
        label_codigo = QLabel(codigo)
        label_codigo.setObjectName("codigoIdentificacionDetalleSigqua")
        fila_codigo.addWidget(label_codigo)
        if boton_copiar is not None:
            fila_codigo.addWidget(boton_copiar, alignment=Qt.AlignmentFlag.AlignVCenter)
        fila_codigo.addStretch(1)

        label_nombre = QLabel(nombre)
        label_nombre.setObjectName("nombreIdentificacionDetalleSigqua")
        label_nombre.setWordWrap(True)

        bloque_principal.addLayout(fila_codigo)
        bloque_principal.addWidget(label_nombre)

        layout.addLayout(bloque_principal, 1)
        if badges:
            columna_badges = QVBoxLayout()
            columna_badges.setContentsMargins(0, 0, 0, 0)
            columna_badges.setSpacing(6)
            for badge in badges:
                columna_badges.addWidget(badge, alignment=Qt.AlignmentFlag.AlignRight)
            layout.addLayout(columna_badges)


class CampoDetalleSigqua(QFrame):
    """Campo informativo simple sin iconos internos."""

    def __init__(self, etiqueta: str, valor: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("campoDetalleSigqua")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(5)
        label_etiqueta = QLabel(etiqueta)
        label_etiqueta.setObjectName("etiquetaCampoDetalleSigqua")
        label_valor = QLabel(valor)
        label_valor.setObjectName("valorCampoDetalleSigqua")
        label_valor.setWordWrap(True)
        layout.addWidget(label_etiqueta)
        layout.addWidget(label_valor)


class TarjetaResumenDetalleSigqua(QFrame):
    """Tarjeta compacta de metrica o resumen sin icono interno."""

    def __init__(self, etiqueta: str, valor: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("tarjetaResumenDetalleSigqua")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(4)
        label_etiqueta = QLabel(etiqueta)
        label_etiqueta.setObjectName("etiquetaCampoDetalleSigqua")
        label_valor = QLabel(valor)
        label_valor.setObjectName("valorResumenDetalleSigqua")
        label_valor.setWordWrap(True)
        layout.addWidget(label_etiqueta)
        layout.addWidget(label_valor)


class SeccionDetalleSigqua(QFrame):
    """Bloque comun con titulo, descripcion y contenido variable."""

    def __init__(
        self,
        titulo: str,
        descripcion: str,
        contenido: QLayout | QWidget | list[QWidget | QLayout],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("seccionDetalleSigqua")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        label_titulo = QLabel(titulo)
        label_titulo.setObjectName("tituloSeccionDetalleSigqua")
        label_descripcion = QLabel(descripcion)
        label_descripcion.setObjectName("descripcionSeccionDetalleSigqua")
        label_descripcion.setWordWrap(True)
        layout.addWidget(label_titulo)
        layout.addWidget(label_descripcion)

        elementos = contenido if isinstance(contenido, list) else [contenido]
        for elemento in elementos:
            if isinstance(elemento, QWidget):
                layout.addWidget(elemento)
            else:
                layout.addLayout(elemento)


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
        self._variante = resolver_variante_boton_modal(texto, self._variante)
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
        self._nombre_tema = resolver_nombre_tema(nombre_tema)
        self._aplicar_estilos()
        self._actualizar_icono(False)


class DialogoMensajeSigqua(DialogoBaseSigqua):
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
        label_titulo.setObjectName("tituloDialogoSigqua")
        label_mensaje = QLabel(mensaje)
        label_mensaje.setObjectName("descripcionDialogoSigqua")
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


class DialogoConfirmacionSigqua(DialogoBaseSigqua):
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
        label_titulo.setObjectName("tituloDialogoSigqua")
        label_descripcion = QLabel(descripcion)
        label_descripcion.setObjectName("descripcionDialogoSigqua")
        label_descripcion.setWordWrap(True)
        self.layout_cabecera.addWidget(label_titulo)
        self.layout_cabecera.addWidget(label_descripcion)

        if detalles:
            titulo_resumen = QLabel("Resumen de la accion")
            titulo_resumen.setObjectName("etiquetaDatoDialogoSigqua")
            panel_detalles = QFrame()
            panel_detalles.setObjectName("bloqueDialogoSigqua")
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
                label_etiqueta.setObjectName("etiquetaDatoDialogoSigqua")
                label_valor = QLabel(valor)
                label_valor.setObjectName("valorDatoDialogoSigqua")
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
        self._tema_actual = resolver_nombre_tema(nombre_tema)
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
        self._tema_actual = resolver_nombre_tema(nombre_tema)
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
    boton.setStyleSheet(
        f"""
        QPushButton#botonOperativo,
        QPushButton#botonOperativoPrimario {{
            border-radius: 12px;
            font-size: 12px;
            font-weight: 800;
            padding: 0 16px;
            min-height: 36px;
        }}
        QPushButton#botonOperativo {{
            background-color: {paleta["boton_secundario_fondo"]};
            border: 1px solid {paleta["borde_suave"]};
            color: {paleta["boton_secundario_texto"]};
        }}
        QPushButton#botonOperativo:hover {{
            background-color: {paleta["boton_secundario_hover"]};
            border-color: {paleta["borde_principal"]};
            color: {paleta["texto_destacado"]};
        }}
        QPushButton#botonOperativo:pressed {{
            background-color: {paleta["fondo_menu_activo"]};
        }}
        QPushButton#botonOperativoPrimario {{
            background-color: {paleta["boton_primario_fondo"]};
            border: 1px solid {paleta["borde_info"]};
            color: {paleta["boton_primario_texto"]};
        }}
        QPushButton#botonOperativoPrimario:hover {{
            background-color: {paleta["boton_primario_hover"]};
        }}
        QPushButton#botonOperativoPrimario:pressed {{
            background-color: {paleta["acento_hover"]};
        }}
        QPushButton#botonOperativo:disabled,
        QPushButton#botonOperativoPrimario:disabled {{
            background-color: {paleta["boton_deshabilitado_fondo"]};
            border-color: {paleta["borde_suave"]};
            color: {paleta["boton_deshabilitado_texto"]};
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
