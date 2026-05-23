"""Vista del shell principal de SICAP."""

from __future__ import annotations

from datetime import datetime
from statistics import fmean

from PySide6.QtCharts import (
    QBarCategoryAxis,
    QBarSeries,
    QBarSet,
    QChart,
    QChartView,
    QHorizontalBarSeries,
    QLineSeries,
    QPieSeries,
    QValueAxis,
)
from PySide6.QtCore import (
    QEvent,
    QEasingCurve,
    QMargins,
    QPauseAnimation,
    QPoint,
    QPropertyAnimation,
    QSequentialAnimationGroup,
    QSize,
    Qt,
    Signal,
)
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QLinearGradient,
    QPainterPath,
    QPaintEvent,
    QPainter,
    QPen,
    QPixmap,
    QResizeEvent,
)
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QGraphicsOpacityEffect,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from comun.configuracion.gestor_rutas import GestorRutas
from comun.ui import (
    BotonAccionContextual,
    DialogoConfirmacionSicap,
    DialogoMensajeSicap,
    VistaPlaceholderModulo,
    aplicar_estilo_boton_operativo,
    crear_boton_operativo,
    obtener_icono_tabler_coloreado,
    resolver_variante_boton_modal,
)
from comun.ui.componentes import COLOR_FONDO_DIALOGO
from comun.ui.temas import (
    TEMA_SICAP_PREDETERMINADO,
    establecer_tema_actual,
    obtener_fondo_header_destacado,
    obtener_paleta_tema,
    resolver_nombre_tema,
)
from modulos.principal.entidades import (
    AnaliticaDashboard,
    CategoriaDashboard,
    EstadoModuloPrincipal,
    InsightDashboard,
    ModuloNavegacion,
    PuntoSerieDashboard,
)


COLOR_FONDO_PRINCIPAL = "#2c2966"
ANCHO_MINIMO_SHELL_PRINCIPAL = 960
ALTO_MINIMO_SHELL_PRINCIPAL = 640
ANCHO_RUPTURA_DASHBOARD_AMPLIO = 1320
ANCHO_RUPTURA_DASHBOARD_MEDIO = 980
ANCHO_RUPTURA_METRICAS_4_COLUMNAS = 1660
ANCHO_RUPTURA_METRICAS_3_COLUMNAS = 1080
ANCHO_RUPTURA_METRICAS_2_COLUMNAS = 760
COLOR_GRADIENTE_MARCA_INICIAL = "#22d3a6"
COLOR_GRADIENTE_MARCA_FINAL = "#E4EACC"


class TarjetaMetricaEjecutiva(QFrame):
    """Tarjeta KPI con acento e iconografia para el dashboard ejecutivo."""

    def __init__(
        self,
        icono: str,
        color_acento: str,
        color_fondo: str,
        etiqueta_contexto: str,
        nombre_tema: str = TEMA_SICAP_PREDETERMINADO,
    ) -> None:
        super().__init__()
        self._icono = icono
        self._color_acento = color_acento
        self._color_fondo = color_fondo
        self._etiqueta_contexto = etiqueta_contexto
        self._tema_actual = nombre_tema
        self.setObjectName("tarjetaMetricaEjecutiva")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(130)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)

        fila_superior = QHBoxLayout()
        fila_superior.setContentsMargins(0, 0, 0, 0)
        fila_superior.setSpacing(10)

        self._insignia = QLabel("")
        self._insignia.setObjectName("insigniaMetricaEjecutiva")
        self._insignia.setFixedSize(42, 42)
        self._insignia.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._chip = QLabel(etiqueta_contexto.upper())
        self._chip.setObjectName("chipMetricaEjecutiva")
        self._chip.setAlignment(Qt.AlignmentFlag.AlignCenter)

        fila_superior.addWidget(self._insignia)
        fila_superior.addStretch(1)
        fila_superior.addWidget(self._chip)

        self._titulo = QLabel("")
        self._titulo.setObjectName("tituloMetricaEjecutiva")
        self._titulo.setWordWrap(True)
        self._valor = QLabel("")
        self._valor.setObjectName("valorMetricaEjecutiva")
        self._detalle = QLabel("")
        self._detalle.setObjectName("detalleMetricaEjecutiva")
        self._detalle.setWordWrap(True)

        layout.addLayout(fila_superior)
        layout.addWidget(self._titulo)
        layout.addWidget(self._valor)
        layout.addStretch(1)
        layout.addWidget(self._detalle)
        self._aplicar_estilo()

    def actualizar(self, titulo: str, valor: str, detalle: str) -> None:
        self._titulo.setText(titulo)
        self._valor.setText(valor)
        self._detalle.setText(detalle)

    def _aplicar_estilo(self) -> None:
        paleta = obtener_paleta_tema(self._tema_actual)
        color_base = QColor(self._color_fondo)
        color_acento = QColor(self._color_acento)
        tono_superior = QColor(color_base)
        tono_superior.setAlpha(184)
        tono_inferior = QColor(228, 234, 204, 126)
        borde = QColor(color_acento)
        borde.setAlpha(130)
        fondo_insignia = QColor(color_acento)
        fondo_insignia.setAlpha(66)
        chip_fondo = QColor(color_base)
        chip_fondo.setAlpha(116)

        self._insignia.setPixmap(
            obtener_icono_tabler_coloreado(self._icono, self._color_acento, tamano=20).pixmap(20, 20)
        )
        self.setStyleSheet(
            f"""
            QFrame#tarjetaMetricaEjecutiva {{
                background: qlineargradient(
                    x1: 0, y1: 0,
                    x2: 1, y2: 1,
                    stop: 0 rgba({tono_superior.red()}, {tono_superior.green()}, {tono_superior.blue()}, {tono_superior.alpha()}),
                    stop: 1 rgba({tono_inferior.red()}, {tono_inferior.green()}, {tono_inferior.blue()}, {tono_inferior.alpha()})
                );
                border: 1px solid rgba({borde.red()}, {borde.green()}, {borde.blue()}, {borde.alpha()});
                border-radius: 20px;
            }}
            QLabel#insigniaMetricaEjecutiva {{
                background: rgba({fondo_insignia.red()}, {fondo_insignia.green()}, {fondo_insignia.blue()}, {fondo_insignia.alpha()});
                border: 1px solid rgba({borde.red()}, {borde.green()}, {borde.blue()}, {min(255, borde.alpha() + 24)});
                border-radius: 14px;
            }}
            QLabel#chipMetricaEjecutiva {{
                background: rgba({chip_fondo.red()}, {chip_fondo.green()}, {chip_fondo.blue()}, {chip_fondo.alpha()});
                color: {paleta["texto_panel_principal"]};
                border: 1px solid rgba({borde.red()}, {borde.green()}, {borde.blue()}, {max(70, borde.alpha() - 10)});
                border-radius: 11px;
                padding: 4px 9px;
                font-size: 10px;
                font-weight: 800;
                letter-spacing: 0.08em;
            }}
            QLabel#tituloMetricaEjecutiva {{
                color: {paleta["texto_panel_principal"]};
                font-size: 12px;
                font-weight: 800;
            }}
            QLabel#valorMetricaEjecutiva {{
                color: {paleta["texto_panel_fuerte"]};
                font-size: 31px;
                font-weight: 900;
            }}
            QLabel#detalleMetricaEjecutiva {{
                color: {paleta["texto_panel_detalle"]};
                font-size: 11px;
                font-weight: 700;
            }}
            """
        )

    def aplicar_tema(self, nombre_tema: str) -> None:
        self._tema_actual = nombre_tema
        self._aplicar_estilo()


class FilaRanking(QFrame):
    """Fila compacta con barra de progreso para ranking lateral."""

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("filaRanking")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self._etiqueta = QLabel("")
        self._etiqueta.setObjectName("rankingEtiqueta")
        self._barra = QProgressBar()
        self._barra.setTextVisible(False)
        self._barra.setMaximumHeight(8)
        self._barra.setObjectName("rankingBarra")
        self._valor = QLabel("")
        self._valor.setObjectName("rankingValor")

        layout.addWidget(self._etiqueta, 2)
        layout.addWidget(self._barra, 3)
        layout.addWidget(self._valor, 1, alignment=Qt.AlignmentFlag.AlignRight)

    def actualizar(self, etiqueta: str, porcentaje: float, valor_formateado: str) -> None:
        self._etiqueta.setText(etiqueta)
        self._barra.setValue(int(max(0.0, min(100.0, porcentaje))))
        self._valor.setText(valor_formateado)


class TarjetaInsight(QWidget):
    """Tarjeta compacta para lecturas rapidas del panel."""

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("tarjetaInsight")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(3)

        self._titulo = QLabel("")
        self._titulo.setObjectName("insightTitulo")
        self._valor = QLabel("")
        self._valor.setObjectName("insightValor")
        self._detalle = QLabel("")
        self._detalle.setObjectName("insightDetalle")
        self._detalle.setWordWrap(True)

        layout.addWidget(self._titulo)
        layout.addWidget(self._valor)
        layout.addWidget(self._detalle)

    def actualizar(self, insight: InsightDashboard) -> None:
        self._titulo.setText(insight.titulo)
        self._valor.setText(insight.valor)
        self._detalle.setText(insight.detalle)


class EtiquetaMarcaGradiente(QLabel):
    """Renderiza el nombre SICAP con degradado similar al login."""

    def __init__(self, texto: str) -> None:
        super().__init__(texto)
        self.setObjectName("marcaPrincipal")
        self.setMinimumHeight(72)

    def paintEvent(self, evento: QPaintEvent) -> None:
        texto = self.text().strip()
        if not texto:
            super().paintEvent(evento)
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)

        fuente = self.font()
        metricas = self.fontMetrics()
        recta = self.contentsRect()
        ancho_texto = metricas.horizontalAdvance(texto)
        alto_texto = metricas.height()
        alineacion = self.alignment() or Qt.AlignmentFlag.AlignLeft
        if alineacion & Qt.AlignmentFlag.AlignHCenter:
            origen_x = recta.x() + max(0, (recta.width() - ancho_texto) / 2)
        elif alineacion & Qt.AlignmentFlag.AlignRight:
            origen_x = recta.right() - ancho_texto - 6
        else:
            origen_x = recta.x() + 4
        origen_y = recta.y() + max(0, (recta.height() - alto_texto) / 2) + metricas.ascent()

        trazo = QPainterPath()
        trazo.addText(origen_x, origen_y, fuente, texto)

        degradado = QLinearGradient(recta.left(), recta.top(), recta.right(), recta.top())
        degradado.setColorAt(0.0, QColor(COLOR_GRADIENTE_MARCA_INICIAL))
        degradado.setColorAt(1.0, QColor(COLOR_GRADIENTE_MARCA_FINAL))

        painter.fillPath(trazo, degradado)
        painter.setPen(QPen(QColor(255, 255, 255, 42), 1.0))
        painter.drawPath(trazo)
        painter.end()


class SeccionSidebarDesplegable(QFrame):
    """Agrupa modulos del sidebar en bloques compactos."""

    def __init__(self, titulo: str) -> None:
        super().__init__()
        self._titulo = titulo
        self._expandida = True
        self._modulos: set[str] = set()
        self._modulo_activo: str | None = None
        self.setObjectName("seccionSidebarCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self._etiqueta_titulo = QLabel(titulo.upper())
        self._etiqueta_titulo.setObjectName("tituloSeccionSidebar")

        self._contenedor_items = QWidget()
        self._contenedor_items.setObjectName("contenedorItemsSidebar")
        self._layout_items = QVBoxLayout(self._contenedor_items)
        self._layout_items.setContentsMargins(0, 0, 0, 0)
        self._layout_items.setSpacing(6)

        layout.addWidget(self._etiqueta_titulo)
        layout.addWidget(self._contenedor_items)

    def agregar_boton(self, codigo_modulo: str, boton: QPushButton) -> None:
        self._modulos.add(codigo_modulo)
        self._layout_items.addWidget(boton)

    def marcar_modulo_activo(self, codigo_modulo: str) -> None:
        self._modulo_activo = codigo_modulo if codigo_modulo in self._modulos else None
        tiene_activo = self._modulo_activo is not None
        self._etiqueta_titulo.setProperty("activa", tiene_activo)
        self._etiqueta_titulo.style().unpolish(self._etiqueta_titulo)
        self._etiqueta_titulo.style().polish(self._etiqueta_titulo)
        if tiene_activo:
            self.establecer_expandida(True, forzar=True)

    def establecer_expandida(self, expandida: bool, forzar: bool = False) -> None:
        if not expandida and self._modulo_activo is not None and not forzar:
            return
        self._expandida = expandida
        self._contenedor_items.setVisible(expandida)
        self._etiqueta_titulo.setProperty("expandida", expandida)
        self._etiqueta_titulo.style().unpolish(self._etiqueta_titulo)
        self._etiqueta_titulo.style().polish(self._etiqueta_titulo)

    def esta_expandida(self) -> bool:
        return self._expandida


class BotonPerfilUsuario(QPushButton):
    """Disparador del perfil en el encabezado superior."""

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("botonPerfilHeader")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setCheckable(False)
        self.setMinimumSize(48, 48)
        self.setMaximumSize(48, 48)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setToolTip("Perfil de usuario")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(0)

        self._avatar = QLabel("A")
        self._avatar.setObjectName("avatarPerfilHeader")
        self._avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._avatar.setFixedSize(40, 40)

        layout.addWidget(self._avatar, alignment=Qt.AlignmentFlag.AlignCenter)

    def actualizar(self, nombre_completo: str, perfil: str) -> None:
        self._avatar.setText(self._resolver_iniciales(nombre_completo))
        self.setToolTip(f"{nombre_completo} · {perfil}")
        self.updateGeometry()
        self.adjustSize()

    def sizeHint(self) -> QSize:
        return QSize(48, 48)

    def minimumSizeHint(self) -> QSize:
        return QSize(48, 48)

    @staticmethod
    def _resolver_iniciales(nombre_completo: str) -> str:
        partes = [parte for parte in nombre_completo.strip().split() if parte]
        if not partes:
            return "US"
        if len(partes) == 1:
            return partes[0][:2].upper()
        return f"{partes[0][0]}{partes[1][0]}".upper()


class PanelPerfilUsuario(QFrame):
    """Ventana flotante de perfil inspirada en el componente de Figma."""

    cerrar_sesion_solicitada = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._tema_actual = TEMA_SICAP_PREDETERMINADO
        self._paleta_tema = obtener_paleta_tema(self._tema_actual)
        self.setObjectName("panelPerfilUsuario")
        self.setWindowFlags(
            Qt.WindowType.Popup
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.NoDropShadowWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setMinimumWidth(360)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        encabezado = QFrame()
        encabezado.setObjectName("encabezadoPanelPerfil")
        layout_encabezado = QHBoxLayout(encabezado)
        layout_encabezado.setContentsMargins(14, 14, 14, 14)
        layout_encabezado.setSpacing(12)

        self._avatar = QLabel("US")
        self._avatar.setObjectName("avatarPanelPerfil")
        self._avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._avatar.setFixedSize(54, 54)

        bloque_identidad = QVBoxLayout()
        bloque_identidad.setContentsMargins(0, 0, 0, 0)
        bloque_identidad.setSpacing(2)
        self._nombre = QLabel("")
        self._nombre.setObjectName("nombrePanelPerfil")
        self._rol = QLabel("")
        self._rol.setObjectName("rolPanelPerfil")
        bloque_identidad.addWidget(self._nombre)
        bloque_identidad.addWidget(self._rol)

        layout_encabezado.addWidget(self._avatar)
        layout_encabezado.addLayout(bloque_identidad, 1)

        panel_datos = QFrame()
        panel_datos.setObjectName("bloquePanelPerfil")
        layout_datos = QVBoxLayout(panel_datos)
        layout_datos.setContentsMargins(14, 14, 14, 14)
        layout_datos.setSpacing(10)

        self._correo = self._crear_fila_dato("Correo electr\u00f3nico", "mail.svg")
        self._ultimo_acceso = self._crear_fila_dato("\u00daltimo acceso", "clock.svg")
        self._estado_sesion = self._crear_fila_dato("Estado de sesi\u00f3n", "circle-check.svg")
        layout_datos.addWidget(self._correo["contenedor"])
        layout_datos.addWidget(self._ultimo_acceso["contenedor"])
        layout_datos.addWidget(self._estado_sesion["contenedor"])

        panel_acciones = QFrame()
        panel_acciones.setObjectName("bloquePanelPerfil")
        layout_acciones = QVBoxLayout(panel_acciones)
        layout_acciones.setContentsMargins(10, 10, 10, 10)
        layout_acciones.setSpacing(6)

        self._boton_mi_perfil = self._crear_boton_accion(
            "Mi perfil",
            "user.svg",
            "edicion",
        )
        self._boton_ayuda = self._crear_boton_accion(
            "Ayuda y soporte",
            "help.svg",
            "ayuda",
        )
        self._boton_acerca = self._crear_boton_accion(
            "Acerca del sistema",
            "info-circle.svg",
            "informacion",
        )
        self._boton_cerrar_sesion = self._crear_boton_accion(
            "Cerrar sesi\u00f3n",
            "arrow-left.svg",
            "salida",
        )
        self._boton_mi_perfil.clicked.connect(
            lambda: self._mostrar_informacion(
                "Mi perfil",
                "La edici\u00f3n detallada del perfil se integrar\u00e1 en el siguiente hito.",
                "user.svg",
                "edicion",
            )
        )
        self._boton_ayuda.clicked.connect(
            lambda: self._mostrar_informacion(
                "Ayuda y soporte",
                "El acceso directo a ayuda y soporte se integrar\u00e1 en el siguiente hito.",
                "help.svg",
                "ayuda",
            )
        )
        self._boton_acerca.clicked.connect(
            lambda: self._mostrar_informacion(
                "Acerca del sistema",
                "SICAP\nVersi\u00f3n 2.0.0\nSistema de control administrativo",
                "info-circle.svg",
                "informacion",
            )
        )
        self._boton_cerrar_sesion.clicked.connect(self._emitir_cierre_sesion)
        layout_acciones.addWidget(self._boton_mi_perfil)
        layout_acciones.addWidget(self._boton_ayuda)
        layout_acciones.addWidget(self._boton_acerca)
        layout_acciones.addWidget(self._boton_cerrar_sesion)

        pie = QFrame()
        pie.setObjectName("piePanelPerfil")
        layout_pie = QVBoxLayout(pie)
        layout_pie.setContentsMargins(12, 12, 12, 12)
        layout_pie.setSpacing(2)

        etiqueta_sistema = QLabel("SICAP")
        etiqueta_sistema.setObjectName("sistemaPanelPerfil")
        etiqueta_version = QLabel("Versi\u00f3n 2.0.0")
        etiqueta_version.setObjectName("detallePanelPerfil")
        etiqueta_institucion = QLabel("Sistema de control administrativo")
        etiqueta_institucion.setObjectName("detallePanelPerfil")
        etiqueta_desarrollado = QLabel("Desarrollado por Proyecto SICAP")
        etiqueta_desarrollado.setObjectName("detallePanelPerfil")
        layout_pie.addWidget(etiqueta_sistema)
        layout_pie.addWidget(etiqueta_version)
        layout_pie.addWidget(etiqueta_institucion)
        layout_pie.addWidget(etiqueta_desarrollado)

        layout.addWidget(encabezado)
        layout.addWidget(panel_datos)
        layout.addWidget(panel_acciones)
        layout.addWidget(pie)
        self._aplicar_estilos()

    def actualizar(
        self,
        nombre_completo: str,
        rol: str,
        correo: str,
        ultimo_acceso: str,
        estado_sesion: str,
    ) -> None:
        self._avatar.setText(BotonPerfilUsuario._resolver_iniciales(nombre_completo))
        self._nombre.setText(nombre_completo)
        self._rol.setText(rol)
        self._correo["valor"].setText(correo)
        self._ultimo_acceso["valor"].setText(ultimo_acceso)
        self._estado_sesion["valor"].setText(estado_sesion)

    def mostrar_desde(self, disparador: QWidget) -> None:
        self.adjustSize()
        posicion = disparador.mapToGlobal(disparador.rect().bottomRight())
        destino_x = posicion.x() - self.width()
        destino_y = posicion.y() + 10
        self.move(QPoint(destino_x, destino_y))
        self.show()
        self.raise_()

    def _crear_fila_dato(self, titulo: str, icono: str) -> dict[str, QWidget | QLabel]:
        contenedor = QFrame()
        contenedor.setObjectName("filaDatoPerfil")
        layout = QHBoxLayout(contenedor)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        icono_label = QLabel("")
        icono_label.setObjectName("iconoDatoPerfil")
        icono_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icono_label.setFixedSize(32, 32)
        icono_label.setPixmap(
            obtener_icono_tabler_coloreado(icono, "#d7e9ff", tamano=16).pixmap(16, 16)
        )

        bloque = QVBoxLayout()
        bloque.setContentsMargins(0, 0, 0, 0)
        bloque.setSpacing(1)
        etiqueta = QLabel(titulo)
        etiqueta.setObjectName("tituloDatoPerfil")
        valor = QLabel("")
        valor.setObjectName("valorDatoPerfil")
        valor.setWordWrap(True)
        bloque.addWidget(etiqueta)
        bloque.addWidget(valor)

        layout.addWidget(icono_label, alignment=Qt.AlignmentFlag.AlignTop)
        layout.addLayout(bloque, 1)
        return {"contenedor": contenedor, "valor": valor}

    def _crear_boton_accion(self, texto: str, icono: str, variante: str) -> QPushButton:
        boton = BotonAccionContextual(texto, icono, variante)
        boton.setMinimumHeight(46)
        return boton

    def aplicar_tema(self, nombre_tema: str) -> None:
        self._tema_actual = (
            resolver_nombre_tema(nombre_tema)
        )
        self._paleta_tema = obtener_paleta_tema(self._tema_actual)
        self._aplicar_estilos()

    def _aplicar_estilos(self) -> None:
        paleta = self._paleta_tema
        fondo_header_destacado = obtener_fondo_header_destacado(self._tema_actual)
        self.setStyleSheet(
            f"""
            QFrame#panelPerfilUsuario {{
                background: {paleta["fondo_dialogo"]};
                border: 1px solid {paleta["borde_principal"]};
                border-radius: 22px;
            }}
            QFrame#encabezadoPanelPerfil,
            QFrame#bloquePanelPerfil,
            QFrame#piePanelPerfil {{
                background: {paleta["fondo_superficie_suave"]};
                border: 1px solid {paleta["borde_suave"]};
                border-radius: 18px;
            }}
            QFrame#filaDatoPerfil {{
                background: transparent;
                border: none;
            }}
            QLabel#avatarPanelPerfil {{
                background: {paleta["fondo_avatar"]};
                border: 1px solid {paleta["borde_avatar"]};
                border-radius: 27px;
                color: {paleta["texto_principal"]};
                font-size: 18px;
                font-weight: 900;
            }}
            QLabel#nombrePanelPerfil {{
                color: {paleta["texto_principal"]};
                font-size: 16px;
                font-weight: 900;
            }}
            QLabel#rolPanelPerfil,
            QLabel#tituloDatoPerfil,
            QLabel#detallePanelPerfil {{
                color: {paleta["texto_secundario"]};
                font-size: 12px;
                font-weight: {paleta["peso_cuerpo"]};
            }}
            QLabel#valorDatoPerfil,
            QLabel#sistemaPanelPerfil {{
                color: {paleta["texto_panel_principal"]};
                font-size: 13px;
                font-weight: {paleta["peso_titulo"]};
            }}
            QLabel#sistemaPanelPerfil {{
                font-size: 14px;
            }}
            QLabel#iconoDatoPerfil {{
                background: {paleta["fondo_superficie_suave"]};
                border: 1px solid {paleta["borde_suave"]};
                border-radius: 12px;
            }}
            """
        )

    def _mostrar_informacion(
        self,
        titulo: str,
        mensaje: str,
        icono: str,
        variante: str,
    ) -> None:
        self.hide()
        DialogoMensajeSicap(
            titulo,
            mensaje,
            icono=icono,
            variante=variante,
            parent=self.parentWidget() or self,
        ).exec()

    def _emitir_cierre_sesion(self) -> None:
        self.hide()
        dialogo = DialogoConfirmacionSicap(
            titulo="Confirmar cierre de sesi\u00f3n",
            descripcion=(
                "Vas a cerrar la sesi\u00f3n actual en este equipo. "
                "Confirma solo si deseas salir ahora."
            ),
            texto_confirmar="Confirmar salida",
            icono="alert-triangle.svg",
            variante_confirmar="salida",
            color_fondo=COLOR_FONDO_DIALOGO,
            parent=self.parentWidget() or self,
        )
        if dialogo.exec() == QDialog.DialogCode.Accepted:
            self.cerrar_sesion_solicitada.emit()


class DialogoPruebaModalBase(QDialog):
    """Base de laboratorio para comparar estrategias de modal."""

    def __init__(
        self,
        titulo: str,
        descripcion: str,
        etiqueta_tecnica: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._titulo_modal = titulo
        self._descripcion_modal = descripcion
        self._etiqueta_tecnica = etiqueta_tecnica
        self.setModal(True)
        self.setMinimumWidth(480)
        self._layout_raiz = QVBoxLayout(self)
        self._layout_raiz.setContentsMargins(0, 0, 0, 0)
        self._layout_raiz.setSpacing(0)

    def _construir_panel_contenido(
        self,
        contenedor: QWidget,
        color_fondo: str,
        radio: int,
        borde: str,
    ) -> None:
        layout = QVBoxLayout(contenedor)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        titulo = QLabel(self._titulo_modal)
        titulo.setStyleSheet("color: #E4EACC; font-size: 22px; font-weight: 900;")
        descripcion = QLabel(self._descripcion_modal)
        descripcion.setWordWrap(True)
        descripcion.setStyleSheet("color: #C9DBE9; font-size: 13px; font-weight: 700;")

        etiqueta = QLabel(self._etiqueta_tecnica)
        etiqueta.setWordWrap(True)
        etiqueta.setStyleSheet(
            "color: rgba(247, 249, 255, 0.82);"
            "background: rgba(29, 54, 78, 0.78);"
            f"border: 1px solid {borde};"
            "padding: 8px 10px;"
            "font-size: 12px;"
            "font-weight: 700;"
            "border-radius: 4px;"
        )

        bloque = QFrame()
        bloque.setStyleSheet(
            "QFrame {"
            f"background: {color_fondo};"
            f"border: 1px solid {borde};"
            f"border-radius: {0 if radio <= 0 else 4}px;"
            "}"
        )
        layout_bloque = QVBoxLayout(bloque)
        layout_bloque.setContentsMargins(0, 0, 0, 0)
        layout_bloque.setSpacing(8)
        layout_bloque.addWidget(QLabel("Vista previa del cuerpo del modal"))
        layout_bloque.addWidget(
            QLabel("Color sólido base #1D364E, misma familia visual que el flujo actual.")
        )

        fila_acciones = QHBoxLayout()
        fila_acciones.setContentsMargins(0, 0, 0, 0)
        fila_acciones.setSpacing(10)

        boton_cancelar = BotonAccionContextual(
            "Cancelar",
            variante=resolver_variante_boton_modal("Cancelar", "neutro"),
            centrado=True,
            mostrar_icono=False,
        )
        boton_cancelar.setMinimumWidth(132)
        boton_cancelar.clicked.connect(self.reject)

        boton_confirmar = BotonAccionContextual(
            "Confirmar prueba",
            variante=resolver_variante_boton_modal("Confirmar prueba", "primario"),
            centrado=True,
            mostrar_icono=False,
        )
        boton_confirmar.setMinimumWidth(160)
        boton_confirmar.clicked.connect(self.accept)

        fila_acciones.addWidget(boton_cancelar)
        fila_acciones.addStretch(1)
        fila_acciones.addWidget(boton_confirmar)

        layout.addWidget(titulo)
        layout.addWidget(descripcion)
        layout.addWidget(etiqueta)
        layout.addWidget(bloque)
        layout.addLayout(fila_acciones)


class DialogoPruebaModalSistema(DialogoPruebaModalBase):
    """Alternativa con marco nativo del sistema."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(
            titulo="Prueba modal con marco del sistema",
            descripcion="Usa QDialog estándar con borde nativo de Windows y panel interno redondeado.",
            etiqueta_tecnica="Alternativa robusta: evita forma personalizada de la ventana.",
            parent=parent,
        )
        self.setWindowTitle("Prueba modal del sistema")

        panel = QFrame()
        panel.setStyleSheet(
            "QFrame {"
            f"background: {COLOR_FONDO_DIALOGO};"
            "border: 1px solid rgba(83, 112, 139, 0.30);"
            "border-radius: 4px;"
            "}"
        )
        self._construir_panel_contenido(
            panel,
            COLOR_FONDO_DIALOGO,
            4,
            "rgba(83, 112, 139, 0.30)",
        )
        self._layout_raiz.addWidget(panel)


class DialogoPruebaModalRecto(DialogoPruebaModalBase):
    """Alternativa opaca rectangular sin esquinas redondeadas."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(
            titulo="Prueba modal rectangular",
            descripcion="Ventana opaca sin recorte ni translucencia, pensada para descartar artefactos.",
            etiqueta_tecnica="Alternativa de control: no usa máscara ni transparencia.",
            parent=parent,
        )
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        self.setStyleSheet(f"QDialog {{ background: {COLOR_FONDO_DIALOGO}; }}")
        self._layout_raiz.setContentsMargins(0, 0, 0, 0)

        panel = QWidget()
        panel.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._construir_panel_contenido(
            panel,
            COLOR_FONDO_DIALOGO,
            0,
            "rgba(83, 112, 139, 0.30)",
        )
        self._layout_raiz.addWidget(panel)


class DialogoPruebaModalMascara(DialogoPruebaModalBase):
    """Alternativa opaca con máscara redondeada."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(
            titulo="Prueba modal con máscara",
            descripcion="Ventana sólida redondeada por máscara, sin translucencia ni blur.",
            etiqueta_tecnica="Alternativa actual: top-level opaco + setMask() + radio moderado.",
            parent=parent,
        )
        self._radio = 4
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._layout_raiz.setContentsMargins(0, 0, 0, 0)

        panel = QWidget()
        panel.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._construir_panel_contenido(
            panel,
            COLOR_FONDO_DIALOGO,
            self._radio,
            "rgba(83, 112, 139, 0.30)",
        )
        self._layout_raiz.addWidget(panel)

    def paintEvent(self, evento: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(COLOR_FONDO_DIALOGO))
        painter.drawRect(self.rect())
        painter.end()
        super().paintEvent(evento)


class DialogoPruebaModalTranslucido(DialogoPruebaModalBase):
    """Alternativa con translucidez y sombra suave."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(
            titulo="Prueba modal translúcido",
            descripcion="Ventana sin marco con fondo translúcido y panel interno redondeado con sombra.",
            etiqueta_tecnica="Alternativa de bordes suaves: depende del compositor de Windows.",
            parent=parent,
        )
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        panel = QFrame()
        panel.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        panel.setStyleSheet(
            "QFrame {"
            f"background: {COLOR_FONDO_DIALOGO};"
            "border: 1px solid rgba(83, 112, 139, 0.55);"
            "border-radius: 4px;"
            "}"
        )
        sombra = QGraphicsDropShadowEffect(panel)
        sombra.setBlurRadius(24)
        sombra.setOffset(0, 8)
        sombra.setColor(QColor(18, 18, 42, 110))
        panel.setGraphicsEffect(sombra)
        self._construir_panel_contenido(
            panel,
            COLOR_FONDO_DIALOGO,
            4,
            "rgba(83, 112, 139, 0.55)",
        )
        self._layout_raiz.addWidget(panel)


class VistaModuloPrincipal(QWidget):
    """Shell operativo con sidebar, header y area central navegable."""

    cerrar_sesion_solicitada = Signal()
    abrir_mantenimiento_solicitado = Signal()
    modulo_solicitado = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._gestor_rutas = GestorRutas()
        self.setObjectName("vistaModuloPrincipal")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._tema_actual = TEMA_SICAP_PREDETERMINADO
        self._paleta_tema = obtener_paleta_tema(self._tema_actual)
        self._correo_usuario_actual = "soporte@sicap.local"
        self._modulo_activo = "dashboard"
        self._modulos_sidebar: dict[str, ModuloNavegacion] = {}
        self._botones_modulos: dict[str, QPushButton] = {}
        self._secciones_sidebar: dict[str, SeccionSidebarDesplegable] = {}
        self._estado_secciones_sidebar: dict[str, bool] = {
            "Vista general": True,
            "Registro y control": True,
            "Cobranza": True,
            "Administración": True,
            "Soporte": True,
            "Otros": True,
        }
        self._paginas_modulos: dict[str, QWidget] = {}
        self._tarjetas_metricas: dict[str, TarjetaMetricaEjecutiva] = {}
        self._orden_metricas: list[str] = []
        self._filas_ranking: list[FilaRanking] = []
        self._tarjetas_insight: list[TarjetaInsight] = []
        self._animaciones_activas: list[object] = []
        self._modo_dashboard_actual = "amplio"
        self._ultimo_ancho_dashboard = -1
        self._ultimo_estado_mostrado: EstadoModuloPrincipal | None = None
        self._fondo_personalizado_activo = False
        self._fondo_personalizado_modo = "SOLIDO"
        self._fondo_personalizado_color_primario = ""
        self._fondo_personalizado_color_secundario = ""
        self._panel_perfil_usuario = PanelPerfilUsuario(self)
        self._panel_perfil_usuario.cerrar_sesion_solicitada.connect(
            self.cerrar_sesion_solicitada.emit
        )
        establecer_tema_actual(self._tema_actual)
        self._aplicar_estilos()
        self._construir_ui()

    def sizeHint(self) -> QSize:
        return QSize(1500, 900)

    def minimumSizeHint(self) -> QSize:
        return QSize(ANCHO_MINIMO_SHELL_PRINCIPAL, ALTO_MINIMO_SHELL_PRINCIPAL)

    def resizeEvent(self, evento: QResizeEvent) -> None:
        super().resizeEvent(evento)
        self._actualizar_disposicion_dashboard()

    def eventFilter(self, objeto: object, evento: QEvent) -> bool:
        if (
            hasattr(self, "_scroll_dashboard")
            and objeto is self._scroll_dashboard.viewport()
            and evento.type() == QEvent.Type.Resize
        ):
            self._actualizar_disposicion_dashboard()
        return super().eventFilter(objeto, evento)

    def paintEvent(self, evento: QPaintEvent) -> None:
        """Pinta el fondo principal del shell."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        painter.setPen(Qt.PenStyle.NoPen)
        if self._fondo_personalizado_activo:
            color_primario = self._resolver_color_fondo_personalizado(
                self._fondo_personalizado_color_primario,
                str(self._paleta_tema["fondo_principal"]),
            )
            color_secundario = self._resolver_color_fondo_personalizado(
                self._fondo_personalizado_color_secundario,
                color_primario.name(),
            )
            if self._fondo_personalizado_modo == "DEGRADADO":
                degradado = QLinearGradient(self.rect().topLeft(), self.rect().bottomRight())
                degradado.setColorAt(0.0, color_primario)
                degradado.setColorAt(1.0, color_secundario)
                painter.setBrush(QBrush(degradado))
            else:
                painter.setBrush(color_primario)
        else:
            painter.setBrush(QColor(str(self._paleta_tema["fondo_principal"])))
        painter.drawRect(self.rect())
        painter.end()

        super().paintEvent(evento)

    def aplicar_fondo_personalizado(
        self,
        activo: bool,
        modo: str,
        color_primario: str,
        color_secundario: str,
    ) -> None:
        self._fondo_personalizado_activo = bool(activo)
        self._fondo_personalizado_modo = (
            modo.strip().upper() if modo.strip().upper() in {"SOLIDO", "DEGRADADO"} else "SOLIDO"
        )
        self._fondo_personalizado_color_primario = color_primario.strip().upper()
        self._fondo_personalizado_color_secundario = color_secundario.strip().upper()
        if self._fondo_personalizado_modo == "SOLIDO":
            self._fondo_personalizado_color_secundario = self._fondo_personalizado_color_primario
        self.update()

    def registrar_modulo(self, codigo: str, widget: QWidget) -> None:
        if codigo in self._paginas_modulos:
            return
        self._paginas_modulos[codigo] = widget
        if hasattr(widget, "aplicar_tema"):
            widget.aplicar_tema(self._tema_actual)
        self._stack_contenido.addWidget(widget)

    def preparar_perfil_usuario(self, correo: str) -> None:
        self._correo_usuario_actual = correo.strip() or "soporte@sicap.local"

    def mostrar_estado(self, estado: EstadoModuloPrincipal) -> None:
        self._ultimo_estado_mostrado = estado
        self._modulos_sidebar = {modulo.codigo: modulo for modulo in estado.modulos}
        self._boton_perfil_header.actualizar(estado.nombre_completo, estado.perfil)
        self._panel_perfil_usuario.actualizar(
            nombre_completo=estado.nombre_completo,
            rol=estado.perfil,
            correo=self._correo_usuario_actual,
            ultimo_acceso=datetime.now().strftime("%d/%m/%Y %I:%M %p"),
            estado_sesion="Activa en este equipo",
        )
        self._reconstruir_sidebar(estado.modulos)
        self._mostrar_metricas(estado)
        self._mostrar_analitica(estado.analitica)
        self._boton_mantenimiento.setVisible(estado.puede_abrir_mantenimiento)
        self._panel_acciones_sidebar.setVisible(estado.puede_abrir_mantenimiento)
        self.mostrar_modulo("dashboard")
        self._actualizar_disposicion_dashboard()
        self._animar_aparicion_dashboard()

    @staticmethod
    def _resolver_saludo(momento: datetime | None = None) -> str:
        referencia = momento or datetime.now()
        hora = referencia.hour
        if 5 <= hora <= 11:
            return "Buenos dias"
        if 12 <= hora <= 17:
            return "Buenas tardes"
        return "Buenas noches"

    def aplicar_tema(self, nombre_tema: str) -> None:
        self._tema_actual = (
            resolver_nombre_tema(nombre_tema)
        )
        self._paleta_tema = obtener_paleta_tema(self._tema_actual)
        establecer_tema_actual(self._tema_actual)
        self._aplicar_estilos()
        self._aplicar_tema_a_descendientes()
        if self._ultimo_estado_mostrado is not None:
            self._mostrar_metricas(self._ultimo_estado_mostrado)
            self._mostrar_analitica(self._ultimo_estado_mostrado.analitica)
        self.update()

    @staticmethod
    def _resolver_color_fondo_personalizado(color: str, predeterminado: str) -> QColor:
        color_resuelto = QColor((color or "").strip())
        if color_resuelto.isValid():
            return color_resuelto
        return QColor(predeterminado)

    def _aplicar_tema_a_descendientes(self) -> None:
        for tarjeta in self._tarjetas_metricas.values():
            tarjeta.aplicar_tema(self._tema_actual)
        self._panel_perfil_usuario.aplicar_tema(self._tema_actual)
        for boton in self.findChildren(BotonAccionContextual):
            boton.aplicar_tema(self._tema_actual)
        for boton in self.findChildren(QPushButton):
            if boton.objectName() == "botonOperativo":
                aplicar_estilo_boton_operativo(boton, principal=False)
            elif boton.objectName() == "botonOperativoPrimario":
                aplicar_estilo_boton_operativo(boton, principal=True)
            elif boton.objectName() == "botonSidebar":
                nombre_icono = boton.property("iconoSidebar")
                if isinstance(nombre_icono, str):
                    color_icono = (
                        str(self._paleta_tema["texto_principal"])
                        if boton.property("activo") is True
                        else str(self._paleta_tema["icono_tema_inactivo"])
                    )
                    boton.setIcon(obtener_icono_tabler_coloreado(nombre_icono, color_icono, tamano=18))
        for pagina in self._paginas_modulos.values():
            if hasattr(pagina, "aplicar_tema"):
                pagina.aplicar_tema(self._tema_actual)

    def mostrar_modulo(self, codigo: str) -> None:
        pagina = self._paginas_modulos.get(codigo)
        if pagina is None:
            return
        self._modulo_activo = codigo
        self._actualizar_encabezado_modulo(codigo)
        self._stack_contenido.setCurrentWidget(pagina)
        for codigo_boton, boton in self._botones_modulos.items():
            boton.setProperty("activo", codigo_boton == codigo)
            boton.style().unpolish(boton)
            boton.style().polish(boton)
            nombre_icono = boton.property("iconoSidebar")
            if isinstance(nombre_icono, str):
                color_icono = (
                    str(self._paleta_tema["texto_principal"])
                    if codigo_boton == codigo
                    else str(self._paleta_tema["icono_tema_inactivo"])
                )
                boton.setIcon(obtener_icono_tabler_coloreado(nombre_icono, color_icono, tamano=18))
        for titulo, seccion in self._secciones_sidebar.items():
            seccion.marcar_modulo_activo(codigo)
            self._estado_secciones_sidebar[titulo] = seccion.esta_expandida()

    def _construir_ui(self) -> None:
        layout_raiz = QHBoxLayout(self)
        layout_raiz.setContentsMargins(14, 14, 14, 14)
        layout_raiz.setSpacing(12)

        self._sidebar = QFrame()
        self._sidebar.setObjectName("sidebarPrincipal")
        self._sidebar.setMinimumWidth(192)
        self._sidebar.setMaximumWidth(198)
        self._sidebar.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        layout_sidebar = QVBoxLayout(self._sidebar)
        layout_sidebar.setContentsMargins(12, 12, 12, 12)
        layout_sidebar.setSpacing(10)

        layout_sidebar.addWidget(self._crear_encabezado_sidebar())

        self._scroll_navegacion = QScrollArea()
        self._scroll_navegacion.setObjectName("scrollNavegacionSidebar")
        self._scroll_navegacion.setWidgetResizable(True)
        self._scroll_navegacion.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll_navegacion.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._scroll_navegacion.setFrameShape(QFrame.Shape.NoFrame)

        contenedor_navegacion = QWidget()
        contenedor_navegacion.setObjectName("contenedorNavegacionSidebar")
        self._contenedor_botones = QVBoxLayout(contenedor_navegacion)
        self._contenedor_botones.setContentsMargins(0, 0, 0, 0)
        self._contenedor_botones.setSpacing(12)
        self._scroll_navegacion.setWidget(contenedor_navegacion)
        layout_sidebar.addWidget(self._scroll_navegacion, 1)

        self._panel_acciones_sidebar = QFrame()
        self._panel_acciones_sidebar.setObjectName("panelAccionesSidebar")
        layout_acciones_sidebar = QVBoxLayout(self._panel_acciones_sidebar)
        layout_acciones_sidebar.setContentsMargins(0, 0, 0, 0)
        layout_acciones_sidebar.setSpacing(6)

        self._boton_mantenimiento = self._crear_boton_sidebar(
            ModuloNavegacion("mantenimiento", "Mantenimiento", "", "tool.svg"),
            tipo="accion",
        )
        self._boton_mantenimiento.clicked.connect(self.abrir_mantenimiento_solicitado.emit)
        self._boton_mantenimiento.setVisible(False)
        layout_acciones_sidebar.addWidget(self._boton_mantenimiento)
        self._panel_acciones_sidebar.setVisible(False)
        layout_sidebar.addWidget(self._panel_acciones_sidebar)

        panel = QWidget()
        panel.setObjectName("panelPrincipal")
        layout_panel = QVBoxLayout(panel)
        layout_panel.setContentsMargins(0, 0, 0, 0)
        layout_panel.setSpacing(12)

        header = QFrame()
        header.setObjectName("headerPrincipal")
        layout_header = QHBoxLayout(header)
        layout_header.setContentsMargins(16, 14, 16, 14)
        layout_header.setSpacing(14)

        bloque_titulo = QVBoxLayout()
        bloque_titulo.setSpacing(4)
        self._label_bienvenida = QLabel("Buenas noches")
        self._label_bienvenida.setObjectName("tituloPrincipal")
        self._label_subresumen = QLabel("")
        self._label_subresumen.setObjectName("descripcionPrincipal")
        self._label_subresumen.setWordWrap(True)
        bloque_titulo.addWidget(self._label_bienvenida)
        bloque_titulo.addWidget(self._label_subresumen)

        self._boton_perfil_header = BotonPerfilUsuario()
        self._boton_perfil_header.clicked.connect(self._alternar_panel_perfil_usuario)

        layout_header.addLayout(bloque_titulo, 1)
        layout_header.addStretch(1)
        layout_header.addWidget(
            self._boton_perfil_header,
            alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight,
        )

        self._stack_contenido = QStackedWidget()
        self._stack_contenido.setObjectName("stackPrincipal")

        self._pagina_dashboard = self._crear_dashboard()
        self.registrar_modulo("dashboard", self._pagina_dashboard)

        layout_panel.addWidget(header)
        layout_panel.addWidget(self._stack_contenido, 1)

        layout_raiz.addWidget(self._sidebar)
        layout_raiz.addWidget(panel, 1)

    def _actualizar_encabezado_modulo(self, codigo: str) -> None:
        if self._ultimo_estado_mostrado is None:
            return
        if codigo == "dashboard":
            primer_nombre = (
                self._ultimo_estado_mostrado.nombre_completo.split()[0]
                if self._ultimo_estado_mostrado.nombre_completo
                else self._ultimo_estado_mostrado.nombre_usuario
            )
            perfil_legible = self._ultimo_estado_mostrado.perfil.replace("_", " ").title()
            self._label_bienvenida.setText(f"{self._resolver_saludo()}, {primer_nombre}")
            self._label_subresumen.setText(
                (
                    f"{perfil_legible} en sesion. Monitorea ingresos, pagos pendientes "
                    "y estabilidad operativa desde un solo tablero."
                )
            )
            return

        modulo = self._modulos_sidebar.get(codigo)
        if modulo is None:
            self._label_bienvenida.setText("Modulo")
            self._label_subresumen.setText("Vista operativa del sistema.")
            return

        self._label_bienvenida.setText(modulo.titulo)
        self._label_subresumen.setText(modulo.descripcion or "Vista operativa del sistema.")

    def _crear_dashboard(self) -> QWidget:
        pagina = QWidget()
        pagina.setObjectName("paginaDashboard")
        layout_pagina = QVBoxLayout(pagina)
        layout_pagina.setContentsMargins(0, 0, 0, 0)
        layout_pagina.setSpacing(0)

        self._scroll_dashboard = QScrollArea()
        self._scroll_dashboard.setObjectName("scrollDashboard")
        self._scroll_dashboard.setWidgetResizable(True)
        self._scroll_dashboard.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll_dashboard.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll_dashboard.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._scroll_dashboard.viewport().setAutoFillBackground(False)
        self._scroll_dashboard.viewport().installEventFilter(self)

        self._contenido_dashboard = QWidget()
        self._contenido_dashboard.setObjectName("contenidoDashboard")
        self._contenido_dashboard.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        self._contenido_dashboard.setAutoFillBackground(False)
        layout = QVBoxLayout(self._contenido_dashboard)
        layout.setContentsMargins(0, 4, 0, 6)
        layout.setSpacing(18)

        self._grid_metricas = QGridLayout()
        self._grid_metricas.setHorizontalSpacing(12)
        self._grid_metricas.setVerticalSpacing(12)
        layout.addLayout(self._grid_metricas)

        self._layout_paneles_dashboard = QGridLayout()
        self._layout_paneles_dashboard.setHorizontalSpacing(14)
        self._layout_paneles_dashboard.setVerticalSpacing(14)
        layout.addLayout(self._layout_paneles_dashboard)

        self._panel_tendencia = QFrame()
        self._panel_tendencia.setObjectName("tarjetaPanel")
        self._panel_tendencia.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout_tendencia = QVBoxLayout(self._panel_tendencia)
        layout_tendencia.setContentsMargins(18, 16, 18, 16)
        layout_tendencia.setSpacing(10)

        self._titulo_tendencia = QLabel("Rendimiento de recaudacion")
        self._titulo_tendencia.setObjectName("tituloPanel")
        self._agregar_cabecera_panel_dashboard(
            layout_tendencia,
            self._titulo_tendencia,
            "Comparativo mensual de ingresos reales frente al ritmo promedio.",
            "Mensual",
        )

        self._grafica_tendencia = self._crear_chart_view()
        self._grafica_tendencia.setMinimumHeight(228)
        layout_tendencia.addWidget(self._grafica_tendencia, 1)

        self._panel_ranking = QFrame()
        self._panel_ranking.setObjectName("tarjetaPanel")
        self._panel_ranking.setMinimumWidth(224)
        self._panel_ranking.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        layout_ranking = QVBoxLayout(self._panel_ranking)
        layout_ranking.setContentsMargins(18, 16, 18, 16)
        layout_ranking.setSpacing(10)
        titulo_ranking = QLabel("Deuda por barrio")
        titulo_ranking.setObjectName("tituloPanel")
        self._agregar_cabecera_panel_dashboard(
            layout_ranking,
            titulo_ranking,
            "Zonas con mayor concentracion de saldo pendiente.",
            "Top zonas",
        )
        self._grafica_barrios = self._crear_chart_view()
        self._grafica_barrios.setMinimumHeight(220)
        layout_ranking.addWidget(self._grafica_barrios, 1)

        self._panel_estados = QFrame()
        self._panel_estados.setObjectName("tarjetaPanel")
        self._panel_estados.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout_estados = QVBoxLayout(self._panel_estados)
        layout_estados.setContentsMargins(18, 16, 18, 16)
        layout_estados.setSpacing(10)
        titulo_estados = QLabel("Estado del servicio")
        titulo_estados.setObjectName("tituloPanel")
        self._agregar_cabecera_panel_dashboard(
            layout_estados,
            titulo_estados,
            "Distribucion de casas segun su condicion operativa actual.",
            "Servicios",
        )
        self._grafica_estados = self._crear_chart_view()
        self._grafica_estados.setMinimumHeight(206)
        layout_estados.addWidget(self._grafica_estados, 1)

        self._panel_insights = QFrame()
        self._panel_insights.setObjectName("tarjetaPanel")
        self._panel_insights.setMinimumWidth(248)
        self._panel_insights.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        layout_insights = QVBoxLayout(self._panel_insights)
        layout_insights.setContentsMargins(18, 16, 18, 16)
        layout_insights.setSpacing(10)
        titulo_insights = QLabel("Lecturas clave")
        titulo_insights.setObjectName("tituloPanel")
        self._agregar_cabecera_panel_dashboard(
            layout_insights,
            titulo_insights,
            "Señales ejecutivas para decidir rapido y con contexto.",
            "Ejecutivo",
        )
        self._layout_insights = QVBoxLayout()
        self._layout_insights.setSpacing(10)
        layout_insights.addLayout(self._layout_insights)
        layout_insights.addStretch(1)

        self._panel_distribucion = QFrame()
        self._panel_distribucion.setObjectName("tarjetaPanel")
        self._panel_distribucion.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout_distribucion = QVBoxLayout(self._panel_distribucion)
        layout_distribucion.setContentsMargins(18, 16, 18, 16)
        layout_distribucion.setSpacing(10)
        titulo_distribucion = QLabel("Antiguedad de deuda")
        titulo_distribucion.setObjectName("tituloPanel")
        self._agregar_cabecera_panel_dashboard(
            layout_distribucion,
            titulo_distribucion,
            "Saldo vencido agrupado por rango de atraso para priorizar cobro.",
            "Mora",
        )
        self._grafica_distribucion = self._crear_chart_view()
        self._grafica_distribucion.setMinimumHeight(206)
        layout_distribucion.addWidget(self._grafica_distribucion, 1)

        self._scroll_dashboard.setWidget(self._contenido_dashboard)
        layout_pagina.addWidget(self._scroll_dashboard)
        self._actualizar_disposicion_dashboard()
        return pagina

    def _agregar_cabecera_panel_dashboard(
        self,
        layout_destino: QVBoxLayout,
        titulo: QLabel,
        descripcion: str,
        etiqueta: str,
    ) -> None:
        fila = QHBoxLayout()
        fila.setContentsMargins(0, 0, 0, 0)
        fila.setSpacing(10)
        badge = QLabel(etiqueta)
        badge.setObjectName("badgePanelDashboard")
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        descripcion_label = QLabel(descripcion)
        descripcion_label.setObjectName("descripcionPanel")
        descripcion_label.setWordWrap(True)
        fila.addWidget(titulo)
        fila.addStretch(1)
        fila.addWidget(badge)
        layout_destino.addLayout(fila)
        layout_destino.addWidget(descripcion_label)

    @staticmethod
    def _resolver_visual_metrica(codigo: str) -> tuple[str, str, str, str]:
        mapa = {
            "ingresos_hoy": ("receipt-2.svg", "#66d7ff", "#d8edff", "Hoy"),
            "ingresos_mes": ("chart-bar.svg", "#9db6ff", "#e5e9ff", "Mensual"),
            "deuda": ("urgent.svg", "#ffb86c", "#ffe7cf", "Cobranza"),
            "casas_mora": ("alert-triangle.svg", "#ff8f8f", "#ffe0e6", "Alerta"),
            "abonados_activos": ("users.svg", "#66d7ff", "#d8edff", "Registro"),
            "casas_activas": ("home-2.svg", "#72e3c0", "#daf8ec", "Servicio"),
        }
        return mapa.get(codigo, ("chart-bar.svg", "#C9DBE9", "#e4efff", "Resumen"))

    def _mostrar_metricas(self, estado: EstadoModuloPrincipal) -> None:
        while self._grid_metricas.count():
            item = self._grid_metricas.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()
        self._tarjetas_metricas.clear()
        self._orden_metricas.clear()

        for metrica in estado.metricas:
            icono, color_acento, color_fondo, etiqueta = self._resolver_visual_metrica(
                metrica.codigo
            )
            tarjeta = TarjetaMetricaEjecutiva(
                icono=icono,
                color_acento=color_acento,
                color_fondo=color_fondo,
                etiqueta_contexto=etiqueta,
                nombre_tema=self._tema_actual,
            )
            tarjeta.actualizar(metrica.titulo, metrica.valor, metrica.detalle)
            self._tarjetas_metricas[metrica.codigo] = tarjeta
            self._orden_metricas.append(metrica.codigo)
        self._actualizar_disposicion_metricas()

    def _mostrar_analitica(self, analitica: AnaliticaDashboard) -> None:
        self._construir_insights(analitica.insights)
        self._grafica_tendencia.setChart(self._crear_chart_tendencia(analitica.recaudacion_mensual))
        self._grafica_estados.setChart(self._crear_chart_estados(analitica.estados_servicio))
        self._grafica_barrios.setChart(self._crear_chart_deuda_por_barrio(analitica.deuda_por_barrio))
        self._grafica_distribucion.setChart(
            self._crear_chart_distribucion_deuda(analitica.antiguedad_deuda)
        )

    def _ancho_disponible_dashboard(self) -> int:
        if hasattr(self, "_scroll_dashboard") and self._scroll_dashboard is not None:
            return max(0, self._scroll_dashboard.viewport().width())
        return max(0, self.width())

    def _actualizar_disposicion_dashboard(self) -> None:
        if not hasattr(self, "_layout_paneles_dashboard"):
            return
        ancho_actual = self._ancho_disponible_dashboard()
        if ancho_actual <= 0 or ancho_actual == self._ultimo_ancho_dashboard:
            return
        self._ultimo_ancho_dashboard = ancho_actual
        self._actualizar_disposicion_metricas()
        self._actualizar_disposicion_paneles_dashboard()

    def _actualizar_disposicion_metricas(self) -> None:
        if not hasattr(self, "_grid_metricas") or not self._orden_metricas:
            return

        while self._grid_metricas.count():
            self._grid_metricas.takeAt(0)

        ancho = self._ancho_disponible_dashboard()
        if ancho >= ANCHO_RUPTURA_METRICAS_4_COLUMNAS:
            columnas_metricas = 4
        elif ancho >= ANCHO_RUPTURA_METRICAS_3_COLUMNAS:
            columnas_metricas = 3
        elif ancho >= ANCHO_RUPTURA_METRICAS_2_COLUMNAS:
            columnas_metricas = 2
        else:
            columnas_metricas = 1

        for indice, codigo_metrica in enumerate(self._orden_metricas):
            tarjeta = self._tarjetas_metricas.get(codigo_metrica)
            if tarjeta is None:
                continue
            fila, columna = divmod(indice, columnas_metricas)
            self._grid_metricas.addWidget(tarjeta, fila, columna)

        for columna in range(columnas_metricas):
            self._grid_metricas.setColumnStretch(columna, 1)

    def _actualizar_disposicion_paneles_dashboard(self) -> None:
        while self._layout_paneles_dashboard.count():
            self._layout_paneles_dashboard.takeAt(0)

        ancho = self._ancho_disponible_dashboard()
        limite_expandido = 16777215

        if ancho >= ANCHO_RUPTURA_DASHBOARD_AMPLIO:
            self._modo_dashboard_actual = "amplio"
            self._aplicar_alturas_paneles_dashboard(
                tendencia=324,
                ranking=290,
                estados=324,
                distribucion=290,
                insights=338,
            )
            self._panel_ranking.setMaximumWidth(limite_expandido)
            self._panel_insights.setMaximumWidth(limite_expandido)
            self._layout_paneles_dashboard.addWidget(self._panel_tendencia, 0, 0, 1, 2)
            self._layout_paneles_dashboard.addWidget(self._panel_estados, 0, 2)
            self._layout_paneles_dashboard.addWidget(self._panel_ranking, 1, 0)
            self._layout_paneles_dashboard.addWidget(self._panel_distribucion, 1, 1)
            self._layout_paneles_dashboard.addWidget(self._panel_insights, 1, 2)
            self._layout_paneles_dashboard.setColumnStretch(0, 3)
            self._layout_paneles_dashboard.setColumnStretch(1, 3)
            self._layout_paneles_dashboard.setColumnStretch(2, 2)
            return

        self._panel_ranking.setMaximumWidth(limite_expandido)
        self._panel_insights.setMaximumWidth(limite_expandido)

        if ancho >= ANCHO_RUPTURA_DASHBOARD_MEDIO:
            self._modo_dashboard_actual = "medio"
            self._aplicar_alturas_paneles_dashboard(
                tendencia=308,
                ranking=272,
                estados=252,
                distribucion=252,
                insights=322,
            )
            self._layout_paneles_dashboard.addWidget(self._panel_tendencia, 0, 0, 1, 2)
            self._layout_paneles_dashboard.addWidget(self._panel_estados, 1, 0)
            self._layout_paneles_dashboard.addWidget(self._panel_distribucion, 1, 1)
            self._layout_paneles_dashboard.addWidget(self._panel_ranking, 2, 0)
            self._layout_paneles_dashboard.addWidget(self._panel_insights, 2, 1)
            self._layout_paneles_dashboard.setColumnStretch(0, 1)
            self._layout_paneles_dashboard.setColumnStretch(1, 1)
            return

        self._modo_dashboard_actual = "compacto"
        self._aplicar_alturas_paneles_dashboard(
            tendencia=292,
            ranking=258,
            estados=236,
            distribucion=236,
            insights=336,
        )
        self._layout_paneles_dashboard.addWidget(self._panel_tendencia, 0, 0)
        self._layout_paneles_dashboard.addWidget(self._panel_estados, 1, 0)
        self._layout_paneles_dashboard.addWidget(self._panel_distribucion, 2, 0)
        self._layout_paneles_dashboard.addWidget(self._panel_ranking, 3, 0)
        self._layout_paneles_dashboard.addWidget(self._panel_insights, 4, 0)
        self._layout_paneles_dashboard.setColumnStretch(0, 1)

    def _aplicar_alturas_paneles_dashboard(
        self,
        *,
        tendencia: int,
        ranking: int,
        estados: int,
        distribucion: int,
        insights: int,
    ) -> None:
        self._establecer_altura_panel(self._panel_tendencia, tendencia)
        self._establecer_altura_panel(self._panel_ranking, ranking)
        self._establecer_altura_panel(self._panel_estados, estados)
        self._establecer_altura_panel(self._panel_distribucion, distribucion)
        self._establecer_altura_panel(self._panel_insights, insights)

    @staticmethod
    def _establecer_altura_panel(panel: QWidget, altura: int) -> None:
        panel.setMinimumHeight(altura)
        panel.setMaximumHeight(altura)

    def _reconstruir_sidebar(self, modulos: tuple[ModuloNavegacion, ...]) -> None:
        while self._contenedor_botones.count():
            item = self._contenedor_botones.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()
        self._botones_modulos.clear()
        self._secciones_sidebar.clear()
        secciones: dict[str, list[ModuloNavegacion]] = {
            "Vista general": [],
            "Registro y control": [],
            "Cobranza": [],
            "Administración": [],
            "Soporte": [],
            "Otros": [],
        }

        for modulo in modulos:
            if modulo.codigo == "mantenimiento":
                continue
            secciones[self._resolver_categoria_sidebar(modulo.codigo)].append(modulo)

        for titulo_seccion, modulos_seccion in secciones.items():
            if not modulos_seccion:
                continue
            widget_seccion = SeccionSidebarDesplegable(titulo_seccion)
            self._secciones_sidebar[titulo_seccion] = widget_seccion

            for modulo in modulos_seccion:
                boton = self._crear_boton_sidebar(modulo, tipo="modulo")
                boton.clicked.connect(
                    lambda checked=False, codigo=modulo.codigo: self._solicitar_modulo(codigo)
                )
                widget_seccion.agregar_boton(modulo.codigo, boton)
                self._botones_modulos[modulo.codigo] = boton

            expandida = self._estado_secciones_sidebar.get(titulo_seccion, True)
            widget_seccion.establecer_expandida(expandida, forzar=True)
            widget_seccion.marcar_modulo_activo(self._modulo_activo)
            self._contenedor_botones.addWidget(widget_seccion)

        self._contenedor_botones.addStretch(1)

    def _solicitar_modulo(self, codigo: str) -> None:
        self.modulo_solicitado.emit(codigo)
        self.mostrar_modulo(codigo)

    def _registrar_estado_seccion_sidebar(self, titulo: str, expandida: bool) -> None:
        self._estado_secciones_sidebar[titulo] = expandida

    def _alternar_panel_perfil_usuario(self) -> None:
        if self._panel_perfil_usuario.isVisible():
            self._panel_perfil_usuario.hide()
            return
        self._panel_perfil_usuario.mostrar_desde(self._boton_perfil_header)

    def _crear_boton_sidebar(self, modulo: ModuloNavegacion, tipo: str = "modulo") -> QPushButton:
        boton = crear_boton_operativo(modulo.titulo)
        boton.setObjectName("botonSidebar")
        boton.setProperty("tipoSidebar", tipo)
        boton.setProperty("iconoSidebar", modulo.icono)
        boton.setIcon(
            obtener_icono_tabler_coloreado(
                modulo.icono,
                str(self._paleta_tema["icono_tema_inactivo"]),
                tamano=18,
            )
        )
        boton.setIconSize(boton.iconSize())
        boton.setToolTip(modulo.descripcion or modulo.titulo)
        return boton

    def _crear_encabezado_sidebar(self) -> QWidget:
        encabezado = QWidget()
        encabezado.setObjectName("encabezadoSidebar")
        layout = QVBoxLayout(encabezado)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        contenedor = QFrame()
        contenedor.setObjectName("contenedorMarcaSidebar")
        layout_contenedor = QVBoxLayout(contenedor)
        layout_contenedor.setContentsMargins(16, 14, 16, 12)
        layout_contenedor.setSpacing(2)

        titulo = EtiquetaMarcaGradiente("SICAP")
        titulo.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        titulo.setContentsMargins(0, 0, 0, 0)
        subtitulo = QLabel("Sistema de Control Administrativo")
        subtitulo.setObjectName("subtituloMarca")
        subtitulo.setWordWrap(True)
        subtitulo.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)

        bloque_texto = QVBoxLayout()
        bloque_texto.setContentsMargins(0, 0, 0, 0)
        bloque_texto.setSpacing(1)
        bloque_texto.addWidget(titulo)
        bloque_texto.addWidget(subtitulo)

        layout_contenedor.addLayout(bloque_texto)
        layout.addWidget(contenedor)
        return encabezado

    @staticmethod
    def _resolver_categoria_sidebar(codigo_modulo: str) -> str:
        if codigo_modulo == "dashboard":
            return "Vista general"
        if codigo_modulo in {"barrios", "abonados", "casas", "atencion_abonado", "conexion_reconexion"}:
            return "Registro y control"
        if codigo_modulo in {"pagos", "historial_pagos", "morosidad", "planes_pago"}:
            return "Cobranza"
        if codigo_modulo in {"usuarios", "configuracion", "reportes"}:
            return "Administración"
        if codigo_modulo in {"ayuda_soporte"}:
            return "Soporte"
        return "Otros"

    def _construir_insights(self, insights: tuple[InsightDashboard, ...]) -> None:
        while self._layout_insights.count():
            item = self._layout_insights.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()
        self._tarjetas_insight.clear()

        for insight in insights:
            tarjeta = TarjetaInsight()
            tarjeta.actualizar(insight)
            self._tarjetas_insight.append(tarjeta)
            self._layout_insights.addWidget(tarjeta)

    def _crear_fuente_chart(self, tamano: int, peso: int = 500) -> QFont:
        fuente = QFont(str(self._paleta_tema["familia_tipografica"]), tamano)
        fuente.setWeight(QFont.Weight(peso))
        return fuente

    def _aplicar_estilo_chart(
        self,
        chart: QChart,
        *,
        mostrar_leyenda: bool,
        alineacion_leyenda: Qt.AlignmentFlag = Qt.AlignmentFlag.AlignBottom,
    ) -> None:
        paleta = self._paleta_tema
        chart.setTheme(QChart.ChartTheme.ChartThemeLight)
        chart.setBackgroundVisible(False)
        chart.setBackgroundBrush(QBrush(QColor(0, 0, 0, 0)))
        chart.setBackgroundPen(QPen(QColor(0, 0, 0, 0), 0))
        chart.setDropShadowEnabled(False)
        chart.setBackgroundRoundness(0)
        chart.setMargins(QMargins(4, 4, 4, 4))
        chart.setPlotAreaBackgroundVisible(False)
        legend = chart.legend()
        legend.setVisible(mostrar_leyenda)
        if mostrar_leyenda:
            legend.setAlignment(alineacion_leyenda)
            legend.setLabelColor(QColor(str(paleta["grafica_texto"])))
            legend.setBackgroundVisible(False)
            legend.setFont(self._crear_fuente_chart(8, 600))

    def _crear_chart_tendencia(
        self,
        serie_base: tuple[PuntoSerieDashboard, ...],
    ) -> QChart:
        serie = serie_base or (
            PuntoSerieDashboard("Ene", 0.0),
            PuntoSerieDashboard("Feb", 0.0),
            PuntoSerieDashboard("Mar", 0.0),
        )

        actual = QLineSeries()
        actual.setName("Actual")
        color_linea = QColor(str(self._paleta_tema["grafica_linea"]))
        actual.setColor(color_linea)
        actual.setPen(QPen(color_linea, 2.6))

        referencia = QLineSeries()
        referencia.setName("Promedio")
        pen_referencia = QPen(QColor(str(self._paleta_tema["icono_tarjeta_info"])), 2.0)
        pen_referencia.setStyle(Qt.PenStyle.DotLine)
        referencia.setPen(pen_referencia)

        valores = [punto.valor for punto in serie]
        promedio = fmean(valores) if valores else 0.0

        for indice, punto in enumerate(serie):
            actual.append(indice, punto.valor)
            referencia.append(indice, (punto.valor * 0.45) + (promedio * 0.55))

        chart = QChart()
        chart.addSeries(actual)
        chart.addSeries(referencia)
        self._aplicar_estilo_chart(
            chart,
            mostrar_leyenda=True,
            alineacion_leyenda=Qt.AlignmentFlag.AlignTop,
        )

        eje_x = QBarCategoryAxis()
        eje_x.append([punto.etiqueta for punto in serie])
        eje_x.setLabelsColor(QColor(str(self._paleta_tema["grafica_texto"])))
        eje_x.setGridLineVisible(False)
        eje_x.setLabelsFont(self._crear_fuente_chart(8, 600))

        eje_y = QValueAxis()
        maximo = max(valores + [promedio, 1.0])
        eje_y.setRange(0, maximo * 1.25)
        eje_y.setTickCount(5)
        eje_y.setMinorTickCount(1)
        eje_y.setLabelsColor(QColor(str(self._paleta_tema["grafica_texto"])))
        eje_y.setGridLineColor(QColor(str(self._paleta_tema["grafica_grid"])))
        eje_y.setLabelFormat("%.0f")
        eje_y.setLabelsFont(self._crear_fuente_chart(8, 600))

        chart.addAxis(eje_x, Qt.AlignmentFlag.AlignBottom)
        chart.addAxis(eje_y, Qt.AlignmentFlag.AlignLeft)
        actual.attachAxis(eje_x)
        actual.attachAxis(eje_y)
        referencia.attachAxis(eje_x)
        referencia.attachAxis(eje_y)
        return chart

    def _crear_chart_estados(self, categorias: tuple[CategoriaDashboard, ...]) -> QChart:
        datos = categorias or (CategoriaDashboard("Sin datos", 0.0),)
        barset = QBarSet("Casas")
        colores = list(self._paleta_tema["grafica_pie_colores"])
        for indice, categoria in enumerate(datos):
            barset.append(categoria.valor)
            if indice < len(colores):
                barset.setColor(QColor(colores[indice]))

        serie = QBarSeries()
        serie.append(barset)
        chart = QChart()
        chart.addSeries(serie)
        self._aplicar_estilo_chart(chart, mostrar_leyenda=False)

        eje_x = QBarCategoryAxis()
        eje_x.append([categoria.etiqueta.title() for categoria in datos])
        eje_x.setLabelsColor(QColor(str(self._paleta_tema["grafica_texto"])))
        eje_x.setGridLineVisible(False)
        eje_x.setLabelsFont(self._crear_fuente_chart(8, 600))

        eje_y = QValueAxis()
        maximo = max((categoria.valor for categoria in datos), default=1.0) or 1.0
        eje_y.setRange(0, maximo * 1.25)
        eje_y.setTickCount(5)
        eje_y.setMinorTickCount(1)
        eje_y.setLabelsColor(QColor(str(self._paleta_tema["grafica_texto"])))
        eje_y.setGridLineColor(QColor(str(self._paleta_tema["grafica_grid"])))
        eje_y.setLabelFormat("%.0f")
        eje_y.setLabelsFont(self._crear_fuente_chart(8, 600))

        chart.addAxis(eje_x, Qt.AlignmentFlag.AlignBottom)
        chart.addAxis(eje_y, Qt.AlignmentFlag.AlignLeft)
        serie.attachAxis(eje_x)
        serie.attachAxis(eje_y)
        return chart

    def _crear_chart_deuda_por_barrio(
        self,
        categorias: tuple[CategoriaDashboard, ...],
    ) -> QChart:
        datos = categorias or (CategoriaDashboard("Sin deuda", 0.0),)
        barset = QBarSet("Deuda")
        color_barra = QColor(str(self._paleta_tema["grafica_barras"]))
        barset.setColor(color_barra)
        for categoria in datos:
            barset.append(max(categoria.valor, 0.0))

        serie = QHorizontalBarSeries()
        serie.append(barset)
        chart = QChart()
        chart.addSeries(serie)
        self._aplicar_estilo_chart(chart, mostrar_leyenda=False)

        eje_y = QBarCategoryAxis()
        eje_y.append([categoria.etiqueta for categoria in datos])
        eje_y.setLabelsColor(QColor(str(self._paleta_tema["grafica_texto"])))
        eje_y.setLabelsFont(self._crear_fuente_chart(8, 600))
        eje_y.setGridLineVisible(False)

        eje_x = QValueAxis()
        maximo = max((categoria.valor for categoria in datos), default=1.0) or 1.0
        eje_x.setRange(0, maximo * 1.18)
        eje_x.setTickCount(5)
        eje_x.setMinorTickCount(1)
        eje_x.setLabelsColor(QColor(str(self._paleta_tema["grafica_texto"])))
        eje_x.setGridLineColor(QColor(str(self._paleta_tema["grafica_grid"])))
        eje_x.setLabelsFont(self._crear_fuente_chart(8, 600))
        eje_x.setLabelFormat("L %.0f")

        chart.addAxis(eje_y, Qt.AlignmentFlag.AlignLeft)
        chart.addAxis(eje_x, Qt.AlignmentFlag.AlignBottom)
        serie.attachAxis(eje_y)
        serie.attachAxis(eje_x)
        return chart

    def _crear_chart_distribucion_deuda(
        self,
        categorias: tuple[CategoriaDashboard, ...],
    ) -> QChart:
        datos = categorias or (CategoriaDashboard("Sin deuda", 1.0),)
        serie = QPieSeries()
        serie.setHoleSize(0.58)
        colores = list(self._paleta_tema["grafica_pie_colores"])
        for indice, categoria in enumerate(datos):
            trozo = serie.append(categoria.etiqueta, max(categoria.valor, 0.01))
            trozo.setColor(QColor(colores[indice % len(colores)]))
            trozo.setLabelVisible(False)
            trozo.setBorderColor(QColor(str(self._paleta_tema["grafica_borde_trozo"])))
            trozo.setBorderWidth(1)

        chart = QChart()
        chart.addSeries(serie)
        self._aplicar_estilo_chart(
            chart,
            mostrar_leyenda=True,
            alineacion_leyenda=Qt.AlignmentFlag.AlignRight,
        )
        return chart

    @staticmethod
    def _crear_chart_view() -> QChartView:
        view = QChartView()
        view.setObjectName("chartViewDashboard")
        view.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        view.setFrameShape(QFrame.Shape.NoFrame)
        view.setContentsMargins(0, 0, 0, 0)
        view.setAutoFillBackground(False)
        view.viewport().setAutoFillBackground(False)
        view.setBackgroundBrush(QBrush(QColor(0, 0, 0, 0)))
        view.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        view.setStyleSheet("background: transparent; border: none;")
        return view

    def _animar_aparicion_dashboard(self) -> None:
        widgets = [
            *self._tarjetas_metricas.values(),
            *self._filas_ranking,
            *self._tarjetas_insight,
        ]
        for animacion_activa in self._animaciones_activas:
            if isinstance(animacion_activa, QSequentialAnimationGroup):
                animacion_activa.stop()
        for widget in widgets:
            if widget.graphicsEffect() is not None:
                widget.setGraphicsEffect(None)
        self._animaciones_activas.clear()
        for indice, widget in enumerate(widgets):
            efecto = QGraphicsOpacityEffect(widget)
            widget.setGraphicsEffect(efecto)
            efecto.setOpacity(0.0)
            animacion = QPropertyAnimation(efecto, b"opacity", self)
            animacion.setDuration(220)
            animacion.setStartValue(0.0)
            animacion.setEndValue(1.0)
            animacion.setEasingCurve(QEasingCurve.Type.OutCubic)
            grupo = QSequentialAnimationGroup(self)
            grupo.addAnimation(QPauseAnimation(indice * 35, grupo))
            grupo.addAnimation(animacion)

            def _finalizar_animacion(
                widget_animado: QWidget = widget,
                grupo_animado: QSequentialAnimationGroup = grupo,
            ) -> None:
                widget_animado.setGraphicsEffect(None)
                if grupo_animado in self._animaciones_activas:
                    self._animaciones_activas.remove(grupo_animado)
                grupo_animado.deleteLater()

            grupo.finished.connect(_finalizar_animacion)
            self._animaciones_activas.append(grupo)
            grupo.start()

    @staticmethod
    def _formatear_moneda(valor: float) -> str:
        return f"L {valor:,.0f}"

    def _aplicar_estilos(self) -> None:
        paleta = self._paleta_tema
        fondo_header_destacado = obtener_fondo_header_destacado(self._tema_actual)
        self.setStyleSheet(
            f"""
            QWidget#vistaModuloPrincipal {{
                background: transparent;
                font-family: "{paleta["familia_tipografica"]}";
            }}
            QWidget#panelPrincipal,
            QWidget#paginaDashboard,
            QWidget#contenidoDashboard,
            QScrollArea#scrollDashboard,
            QScrollArea#scrollDashboard > QWidget > QWidget {{
                background: transparent;
            }}
            QScrollArea#scrollDashboard {{
                border: none;
            }}
            QFrame#sidebarPrincipal {{
                background: {fondo_header_destacado};
                border: 1px solid {paleta["borde_suave"]};
                border-radius: 22px;
            }}
            QFrame#headerPrincipal {{
                background: {fondo_header_destacado};
                border: 1px solid {paleta["borde_principal"]};
                border-radius: 22px;
            }}
            QFrame#tarjetaPanel {{
                background: {paleta["fondo_superficie"]};
                border: 1px solid {paleta["borde_principal"]};
                border-radius: 24px;
            }}
            QWidget#encabezadoSidebar,
            QWidget#contenedorNavegacionSidebar,
            QScrollArea#scrollNavegacionSidebar {{
                background: transparent;
                border: none;
            }}
            QFrame#contenedorMarcaSidebar {{
                background: {paleta["fondo_superficie_muy_suave"]};
                border: 1px solid {paleta["borde_suave"]};
                border-radius: 18px;
            }}
            QFrame#seccionSidebarCard,
            QFrame#panelAccionesSidebar {{
                background: transparent;
                border: none;
            }}
            QPushButton#botonPerfilHeader {{
                min-width: 48px;
                max-width: 48px;
                min-height: 48px;
                max-height: 48px;
                background: {paleta["fondo_superficie_suave"]};
                border: 1px solid {paleta["borde_suave"]};
                border-radius: 24px;
            }}
            QPushButton#botonPerfilHeader:hover {{
                background: {paleta["fondo_superficie"]};
                border-color: {paleta["borde_principal"]};
            }}
            QLabel#avatarPerfilHeader {{
                background: {paleta["fondo_avatar"]};
                border: 1px solid {paleta["borde_avatar"]};
                border-radius: 20px;
                color: {paleta["texto_principal"]};
                font-size: 13px;
                font-weight: 900;
            }}
            QWidget#contenedorItemsSidebar {{
                background: transparent;
            }}
            QLabel#logoSidebar {{
                background: transparent;
                border: none;
                border-radius: 0;
            }}
            QLabel#marcaPrincipal {{
                font-size: {paleta["tamano_titulo_modulo"] + 7}px;
                font-weight: {paleta["peso_titulo"]};
                min-height: 38px;
            }}
            QLabel#subtituloMarca,
            QLabel#descripcionPrincipal {{
                color: {paleta["texto_secundario"]};
                font-size: {paleta["tamano_fuente_base"] - 1}px;
                font-weight: {paleta["peso_cuerpo"]};
            }}
            QLabel#subtituloMarca {{
                padding: 0 10px;
            }}
            QLabel#descripcionPrincipal {{
                font-size: {paleta["tamano_fuente_base"] + 1}px;
            }}
            QLabel#descripcionPanel,
            QLabel#tabsSuaves {{
                color: {paleta["texto_panel_detalle"]};
                font-size: {paleta["tamano_fuente_base"] + 2}px;
                font-weight: {paleta["peso_cuerpo"]};
            }}
            QLabel#tituloPrincipal {{
                color: {paleta["texto_principal"]};
            }}
            QLabel#tituloSeccionSidebar {{
                color: {paleta["texto_menu_seccion"]};
                font-size: {paleta["tamano_fuente_base"]}px;
                font-weight: {paleta["peso_titulo"]};
                letter-spacing: 0.8px;
                padding: 2px 6px 4px 6px;
            }}
            QLabel#tituloSeccionSidebar[activa="true"] {{
                color: {paleta["texto_menu_activo"]};
            }}
            QLabel#tituloPrincipal {{
                font-size: {paleta["tamano_titulo_modulo"] + 3}px;
                font-weight: {paleta["peso_titulo"]};
            }}
            QLabel#tituloPanel {{
                color: {paleta["texto_panel_principal"]};
                font-size: {paleta["tamano_titulo_panel"] + 1}px;
                font-weight: {paleta["peso_titulo"]};
            }}
            QLabel#badgePanelDashboard {{
                background: {paleta["fondo_badge"]};
                color: {paleta["texto_badge"]};
                border: 1px solid {paleta["borde_badge_activo"]};
                border-radius: 11px;
                padding: 4px 10px;
                font-size: 10px;
                font-weight: 800;
                letter-spacing: 0.06em;
            }}
            QPushButton#botonSidebar {{
                min-height: 34px;
                border: 1px solid {paleta["borde_suave"]};
                border-radius: 12px;
                background: transparent;
                color: {paleta["texto_menu_normal"]};
                font-size: {paleta["tamano_fuente_base"] + 1}px;
                font-weight: {paleta["peso_titulo"]};
                text-align: left;
                padding: 0 11px;
            }}
            QPushButton#botonSidebar[tipoSidebar="modulo"] {{
                margin-left: 0;
                padding-left: 12px;
            }}
            QPushButton#botonSidebar[tipoSidebar="accion"] {{
                background: {paleta["fondo_superficie_muy_suave"]};
            }}
            QPushButton#botonSidebar:hover {{
                background: {paleta["fondo_menu_hover"]};
                border-color: {paleta["borde_principal"]};
            }}
            QPushButton#botonSidebar[activo="true"] {{
                background: {paleta["fondo_menu_activo"]};
                border-color: {paleta["borde_menu_activo"]};
                color: {paleta["texto_menu_activo"]};
                font-weight: 900;
            }}
            QWidget#tarjetaInsight {{
                background: {paleta["fondo_superficie_suave"]};
                border: 1px solid {paleta["borde_suave"]};
                border-radius: 16px;
            }}
            QLabel#insightTitulo {{
                color: {paleta["texto_panel_secundario"]};
                font-size: {paleta["tamano_fuente_base"] + 2}px;
                font-weight: {paleta["peso_subtitulo"]};
            }}
            QLabel#insightValor {{
                color: {paleta["texto_panel_fuerte"]};
                font-size: 22px;
                font-weight: {paleta["peso_titulo"]};
            }}
            QLabel#insightDetalle {{
                color: {paleta["texto_panel_detalle"]};
                font-size: {paleta["tamano_fuente_base"] + 1}px;
            }}
            QFrame#filaRanking {{
                background: transparent;
            }}
            QLabel#rankingEtiqueta {{
                color: {paleta["texto_panel_fuerte"]};
                font-size: {paleta["tamano_fuente_base"] + 2}px;
                font-weight: {paleta["peso_cuerpo"]};
            }}
            QLabel#rankingValor {{
                color: {paleta["texto_panel_fuerte"]};
                font-size: {paleta["tamano_fuente_base"] + 2}px;
                font-weight: {paleta["peso_subtitulo"]};
            }}
            QProgressBar#rankingBarra {{
                background: {paleta["ranking_barra"]};
                border: none;
                border-radius: 5px;
            }}
            QProgressBar#rankingBarra::chunk {{
                background: {paleta["ranking_chunk"]};
                border-radius: 5px;
            }}
            QFrame#panelPerfilUsuario {{
                background: {paleta["fondo_superficie"]};
                border: 1px solid {paleta["borde_principal"]};
                border-radius: 22px;
            }}
            QFrame#encabezadoPanelPerfil,
            QFrame#bloquePanelPerfil,
            QFrame#piePanelPerfil {{
                background: {paleta["fondo_superficie_suave"]};
                border: 1px solid {paleta["borde_suave"]};
                border-radius: 18px;
            }}
            QLabel#avatarPanelPerfil {{
                background: {paleta["fondo_avatar"]};
                border: 1px solid {paleta["borde_avatar"]};
                border-radius: 27px;
                color: {paleta["texto_principal"]};
                font-size: 18px;
                font-weight: 900;
            }}
            QLabel#nombrePanelPerfil {{
                color: {paleta["texto_principal"]};
                font-size: 16px;
                font-weight: 900;
            }}
            QLabel#rolPanelPerfil,
            QLabel#tituloDatoPerfil,
            QLabel#detallePanelPerfil {{
                color: {paleta["texto_secundario"]};
                font-size: 12px;
                font-weight: {paleta["peso_cuerpo"]};
            }}
            QLabel#valorDatoPerfil,
            QLabel#sistemaPanelPerfil {{
                color: {paleta["texto_panel_principal"]};
                font-size: 13px;
                font-weight: {paleta["peso_titulo"]};
            }}
            QLabel#sistemaPanelPerfil {{
                font-size: 14px;
            }}
            QLabel#iconoDatoPerfil {{
                background: {paleta["fondo_superficie_suave"]};
                border: 1px solid {paleta["borde_suave"]};
                border-radius: 12px;
            }}
            """
        )
