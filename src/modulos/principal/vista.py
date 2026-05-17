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
from PySide6.QtGui import QColor, QPaintEvent, QPainter, QPen, QPixmap, QResizeEvent
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
    obtener_paleta_tema,
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
ANCHO_RUPTURA_METRICAS_4_COLUMNAS = 1380
ANCHO_RUPTURA_METRICAS_3_COLUMNAS = 1040
ANCHO_RUPTURA_METRICAS_2_COLUMNAS = 760


class TarjetaMetricaEjecutiva(QFrame):
    """Tarjeta KPI con acento pastel para el dashboard ejecutivo."""

    def __init__(self, color_fondo: str, nombre_tema: str = TEMA_SICAP_PREDETERMINADO) -> None:
        super().__init__()
        self._color_fondo = color_fondo
        self._tema_actual = nombre_tema
        self.setObjectName("tarjetaMetricaEjecutiva")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(90)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)

        self._titulo = QLabel("")
        self._titulo.setObjectName("tituloMetricaEjecutiva")
        self._valor = QLabel("")
        self._valor.setObjectName("valorMetricaEjecutiva")
        self._detalle = QLabel("")
        self._detalle.setObjectName("detalleMetricaEjecutiva")

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
        tono_superior = QColor(color_base)
        tono_superior.setAlpha(150 if self._tema_actual == "claro" else 164)
        tono_inferior = QColor(255, 255, 255, 186 if self._tema_actual == "claro" else 104)
        self.setStyleSheet(
            f"""
            QFrame#tarjetaMetricaEjecutiva {{
                background: qlineargradient(
                    x1: 0, y1: 0,
                    x2: 1, y2: 1,
                    stop: 0 rgba({tono_superior.red()}, {tono_superior.green()}, {tono_superior.blue()}, {tono_superior.alpha()}),
                    stop: 1 rgba({tono_inferior.red()}, {tono_inferior.green()}, {tono_inferior.blue()}, {tono_inferior.alpha()})
                );
                border: 1px solid {paleta["tarjeta_panel_borde"]};
                border-radius: 17px;
            }}
            QLabel#tituloMetricaEjecutiva {{
                color: {paleta["texto_panel_principal"]};
                font-size: 11px;
                font-weight: 700;
            }}
            QLabel#valorMetricaEjecutiva {{
                color: {paleta["texto_panel_fuerte"]};
                font-size: 26px;
                font-weight: 900;
            }}
            QLabel#detalleMetricaEjecutiva {{
                color: {paleta["texto_panel_detalle"]};
                font-size: 11px;
                font-weight: 600;
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
                "SICAP\nVersi\u00f3n 2.0.0\nJunta de Agua de Yarumela",
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
        etiqueta_institucion = QLabel("Junta de Agua de Yarumela")
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
        return BotonAccionContextual(texto, icono, variante)

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
        titulo.setStyleSheet("color: #ffffff; font-size: 22px; font-weight: 900;")
        descripcion = QLabel(self._descripcion_modal)
        descripcion.setWordWrap(True)
        descripcion.setStyleSheet("color: rgba(240, 244, 255, 0.88); font-size: 13px; font-weight: 700;")

        etiqueta = QLabel(self._etiqueta_tecnica)
        etiqueta.setWordWrap(True)
        etiqueta.setStyleSheet(
            "color: rgba(247, 249, 255, 0.82);"
            "background: rgba(255, 255, 255, 0.08);"
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
            QLabel("Color sólido base #565384, misma familia visual que el flujo actual.")
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
            "border: 1px solid rgba(255, 255, 255, 0.14);"
            "border-radius: 4px;"
            "}"
        )
        self._construir_panel_contenido(
            panel,
            COLOR_FONDO_DIALOGO,
            4,
            "rgba(255, 255, 255, 0.14)",
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
            "rgba(255, 255, 255, 0.14)",
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
            "rgba(255, 255, 255, 0.14)",
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
            "border: 1px solid rgba(255, 255, 255, 0.18);"
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
            "rgba(255, 255, 255, 0.18)",
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
        painter.setBrush(QColor(str(self._paleta_tema["fondo_principal"])))
        painter.drawRect(self.rect())
        painter.end()

        super().paintEvent(evento)

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
        momento_actual = datetime.now().strftime("%d/%m/%Y %I:%M %p")
        self._panel_perfil_usuario.actualizar(
            nombre_completo=estado.nombre_completo,
            rol=estado.perfil,
            correo=self._correo_usuario_actual,
            ultimo_acceso=momento_actual,
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
        self._tema_actual = TEMA_SICAP_PREDETERMINADO
        self._paleta_tema = obtener_paleta_tema(self._tema_actual)
        establecer_tema_actual(self._tema_actual)
        self._aplicar_estilos()
        self._aplicar_tema_a_descendientes()
        if self._ultimo_estado_mostrado is not None:
            self._mostrar_metricas(self._ultimo_estado_mostrado)
            self._mostrar_analitica(self._ultimo_estado_mostrado.analitica)
        self.update()

    def _aplicar_tema_a_descendientes(self) -> None:
        for tarjeta in self._tarjetas_metricas.values():
            tarjeta.aplicar_tema(self._tema_actual)
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

        contenedor_perfil = QVBoxLayout()
        contenedor_perfil.setContentsMargins(0, 0, 0, 0)
        contenedor_perfil.setSpacing(0)
        contenedor_perfil.addWidget(
            self._boton_perfil_header,
            alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight,
        )
        contenedor_perfil.addStretch(1)

        layout_header.addLayout(bloque_titulo, 3)
        layout_header.addLayout(contenedor_perfil)

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
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        self._grid_metricas = QGridLayout()
        self._grid_metricas.setHorizontalSpacing(10)
        self._grid_metricas.setVerticalSpacing(10)
        layout.addLayout(self._grid_metricas)

        self._layout_paneles_dashboard = QGridLayout()
        self._layout_paneles_dashboard.setHorizontalSpacing(12)
        self._layout_paneles_dashboard.setVerticalSpacing(12)
        layout.addLayout(self._layout_paneles_dashboard)

        self._panel_tendencia = QFrame()
        self._panel_tendencia.setObjectName("tarjetaPanel")
        self._panel_tendencia.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout_tendencia = QVBoxLayout(self._panel_tendencia)
        layout_tendencia.setContentsMargins(16, 14, 16, 14)
        layout_tendencia.setSpacing(8)

        fila_titulo = QHBoxLayout()
        fila_titulo.setSpacing(10)
        self._titulo_tendencia = QLabel("Rendimiento de recaudacion")
        self._titulo_tendencia.setObjectName("tituloPanel")
        tabs = QLabel("Este periodo   |   Promedio")
        tabs.setObjectName("tabsSuaves")
        fila_titulo.addWidget(self._titulo_tendencia)
        fila_titulo.addStretch(1)
        fila_titulo.addWidget(tabs)

        self._grafica_tendencia = self._crear_chart_view()
        self._grafica_tendencia.setMinimumHeight(212)
        layout_tendencia.addLayout(fila_titulo)
        layout_tendencia.addWidget(self._grafica_tendencia, 1)

        self._panel_ranking = QFrame()
        self._panel_ranking.setObjectName("tarjetaPanel")
        self._panel_ranking.setMinimumWidth(224)
        self._panel_ranking.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        layout_ranking = QVBoxLayout(self._panel_ranking)
        layout_ranking.setContentsMargins(14, 14, 14, 14)
        layout_ranking.setSpacing(8)
        titulo_ranking = QLabel("Deuda por barrio")
        titulo_ranking.setObjectName("tituloPanel")
        descripcion_ranking = QLabel("Zonas con mayor saldo pendiente.")
        descripcion_ranking.setObjectName("descripcionPanel")
        layout_ranking.addWidget(titulo_ranking)
        layout_ranking.addWidget(descripcion_ranking)
        self._layout_ranking = QVBoxLayout()
        self._layout_ranking.setSpacing(10)
        layout_ranking.addLayout(self._layout_ranking)
        layout_ranking.addStretch(1)

        self._panel_estados = QFrame()
        self._panel_estados.setObjectName("tarjetaPanel")
        self._panel_estados.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout_estados = QVBoxLayout(self._panel_estados)
        layout_estados.setContentsMargins(16, 14, 16, 14)
        layout_estados.setSpacing(8)
        titulo_estados = QLabel("Estado del servicio")
        titulo_estados.setObjectName("tituloPanel")
        descripcion_estados = QLabel("Distribucion de casas por estado operativo.")
        descripcion_estados.setObjectName("descripcionPanel")
        self._grafica_estados = self._crear_chart_view()
        self._grafica_estados.setMinimumHeight(170)
        layout_estados.addWidget(titulo_estados)
        layout_estados.addWidget(descripcion_estados)
        layout_estados.addWidget(self._grafica_estados, 1)

        self._panel_insights = QFrame()
        self._panel_insights.setObjectName("tarjetaPanel")
        self._panel_insights.setMinimumWidth(248)
        self._panel_insights.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        layout_insights = QVBoxLayout(self._panel_insights)
        layout_insights.setContentsMargins(14, 14, 14, 14)
        layout_insights.setSpacing(8)
        titulo_insights = QLabel("Lecturas clave")
        titulo_insights.setObjectName("tituloPanel")
        descripcion_insights = QLabel("Indicadores ejecutivos para seguimiento rapido.")
        descripcion_insights.setObjectName("descripcionPanel")
        self._layout_insights = QVBoxLayout()
        self._layout_insights.setSpacing(10)
        layout_insights.addWidget(titulo_insights)
        layout_insights.addWidget(descripcion_insights)
        layout_insights.addLayout(self._layout_insights)
        layout_insights.addStretch(1)

        self._panel_distribucion = QFrame()
        self._panel_distribucion.setObjectName("tarjetaPanel")
        self._panel_distribucion.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout_distribucion = QVBoxLayout(self._panel_distribucion)
        layout_distribucion.setContentsMargins(16, 14, 16, 14)
        layout_distribucion.setSpacing(8)
        titulo_distribucion = QLabel("Distribucion de deuda")
        titulo_distribucion.setObjectName("tituloPanel")
        descripcion_distribucion = QLabel("Peso relativo del saldo pendiente por barrio.")
        descripcion_distribucion.setObjectName("descripcionPanel")
        self._grafica_distribucion = self._crear_chart_view()
        self._grafica_distribucion.setMinimumHeight(170)
        layout_distribucion.addWidget(titulo_distribucion)
        layout_distribucion.addWidget(descripcion_distribucion)
        layout_distribucion.addWidget(self._grafica_distribucion, 1)

        layout.addStretch(1)
        self._scroll_dashboard.setWidget(self._contenido_dashboard)
        layout_pagina.addWidget(self._scroll_dashboard)
        self._actualizar_disposicion_dashboard()
        return pagina

    def _mostrar_metricas(self, estado: EstadoModuloPrincipal) -> None:
        colores = ("#e9eeff", "#e8f1ff", "#eef0ff", "#eaf3ff", "#edf3ff")
        while self._grid_metricas.count():
            item = self._grid_metricas.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()
        self._tarjetas_metricas.clear()
        self._orden_metricas.clear()

        for indice, metrica in enumerate(estado.metricas):
            tarjeta = TarjetaMetricaEjecutiva(
                colores[indice % len(colores)],
                nombre_tema=self._tema_actual,
            )
            tarjeta.actualizar(metrica.titulo, metrica.valor, metrica.detalle)
            self._tarjetas_metricas[metrica.codigo] = tarjeta
            self._orden_metricas.append(metrica.codigo)
        self._actualizar_disposicion_metricas()

    def _mostrar_analitica(self, analitica: AnaliticaDashboard) -> None:
        self._construir_ranking(analitica.deuda_por_barrio)
        self._construir_insights(analitica.insights)
        self._grafica_tendencia.setChart(self._crear_chart_tendencia(analitica.recaudacion_mensual))
        self._grafica_estados.setChart(self._crear_chart_estados(analitica.estados_servicio))
        self._grafica_distribucion.setChart(
            self._crear_chart_distribucion_deuda(analitica.deuda_por_barrio)
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
                tendencia=320,
                ranking=320,
                estados=276,
                distribucion=276,
                insights=276,
            )
            self._panel_ranking.setMaximumWidth(286)
            self._panel_insights.setMaximumWidth(286)
            self._layout_paneles_dashboard.addWidget(self._panel_tendencia, 0, 0, 1, 2)
            self._layout_paneles_dashboard.addWidget(self._panel_ranking, 0, 2)
            self._layout_paneles_dashboard.addWidget(self._panel_estados, 1, 0)
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
                tendencia=302,
                ranking=158,
                estados=258,
                distribucion=258,
                insights=224,
            )
            self._layout_paneles_dashboard.addWidget(self._panel_tendencia, 0, 0, 1, 2)
            self._layout_paneles_dashboard.addWidget(self._panel_ranking, 1, 0, 1, 2)
            self._layout_paneles_dashboard.addWidget(self._panel_estados, 2, 0)
            self._layout_paneles_dashboard.addWidget(self._panel_distribucion, 2, 1)
            self._layout_paneles_dashboard.addWidget(self._panel_insights, 3, 0, 1, 2)
            self._layout_paneles_dashboard.setColumnStretch(0, 1)
            self._layout_paneles_dashboard.setColumnStretch(1, 1)
            return

        self._modo_dashboard_actual = "compacto"
        self._aplicar_alturas_paneles_dashboard(
            tendencia=288,
            ranking=154,
            estados=244,
            distribucion=244,
            insights=218,
        )
        self._layout_paneles_dashboard.addWidget(self._panel_tendencia, 0, 0)
        self._layout_paneles_dashboard.addWidget(self._panel_ranking, 1, 0)
        self._layout_paneles_dashboard.addWidget(self._panel_estados, 2, 0)
        self._layout_paneles_dashboard.addWidget(self._panel_distribucion, 3, 0)
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
        layout = QHBoxLayout(encabezado)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        label_logo = QLabel()
        label_logo.setObjectName("logoSidebar")
        label_logo.setFixedSize(56, 56)
        label_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ruta_logo = self._gestor_rutas.obtener_ruta_logo_marca()
        if ruta_logo.exists():
            pixmap_logo = QPixmap(str(ruta_logo))
            if not pixmap_logo.isNull():
                label_logo.setPixmap(
                    pixmap_logo.scaled(
                        44,
                        44,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )

        bloque_texto = QVBoxLayout()
        bloque_texto.setContentsMargins(0, 0, 0, 0)
        bloque_texto.setSpacing(0)

        titulo = QLabel("SICAP")
        titulo.setObjectName("marcaPrincipal")
        bloque_texto.addWidget(titulo)
        bloque_texto.addStretch(1)

        layout.addWidget(label_logo, alignment=Qt.AlignmentFlag.AlignVCenter)
        layout.addLayout(bloque_texto, 1)
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

    def _construir_ranking(self, categorias: tuple[CategoriaDashboard, ...]) -> None:
        while self._layout_ranking.count():
            item = self._layout_ranking.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()
        self._filas_ranking.clear()

        if not categorias:
            categorias = (CategoriaDashboard("Sin deuda registrada", 0.0),)
        valor_maximo = max((categoria.valor for categoria in categorias), default=0.0) or 1.0

        for categoria in categorias:
            fila = FilaRanking()
            fila.actualizar(
                categoria.etiqueta,
                (categoria.valor / valor_maximo) * 100.0,
                self._formatear_moneda(categoria.valor),
            )
            self._filas_ranking.append(fila)
            self._layout_ranking.addWidget(fila)

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
        actual.setPen(QPen(color_linea, 2.1))

        referencia = QLineSeries()
        referencia.setName("Promedio")
        pen_referencia = QPen(QColor(str(self._paleta_tema["icono_tarjeta_info"])), 1.8)
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
        chart.setBackgroundVisible(False)
        chart.legend().hide()
        chart.setMargins(QMargins(0, 0, 0, 0))

        eje_x = QBarCategoryAxis()
        eje_x.append([punto.etiqueta for punto in serie])
        eje_x.setLabelsColor(QColor(str(self._paleta_tema["grafica_texto"])))
        eje_x.setGridLineVisible(False)

        eje_y = QValueAxis()
        maximo = max(valores + [promedio, 1.0])
        eje_y.setRange(0, maximo * 1.25)
        eje_y.setTickCount(5)
        eje_y.setLabelsColor(QColor(str(self._paleta_tema["grafica_texto"])))
        eje_y.setGridLineColor(QColor(str(self._paleta_tema["grafica_grid"])))
        eje_y.setLabelFormat("%.0f")

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
        chart.setBackgroundVisible(False)
        chart.legend().hide()
        chart.setMargins(QMargins(0, 0, 0, 0))

        eje_x = QBarCategoryAxis()
        eje_x.append([categoria.etiqueta.title() for categoria in datos])
        eje_x.setLabelsColor(QColor(str(self._paleta_tema["grafica_texto"])))
        eje_x.setGridLineVisible(False)

        eje_y = QValueAxis()
        maximo = max((categoria.valor for categoria in datos), default=1.0) or 1.0
        eje_y.setRange(0, maximo * 1.25)
        eje_y.setTickCount(5)
        eje_y.setLabelsColor(QColor(str(self._paleta_tema["grafica_texto"])))
        eje_y.setGridLineColor(QColor(str(self._paleta_tema["grafica_grid"])))
        eje_y.setLabelFormat("%.0f")

        chart.addAxis(eje_x, Qt.AlignmentFlag.AlignBottom)
        chart.addAxis(eje_y, Qt.AlignmentFlag.AlignLeft)
        serie.attachAxis(eje_x)
        serie.attachAxis(eje_y)
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
        chart.setBackgroundVisible(False)
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignmentFlag.AlignRight)
        chart.legend().setLabelColor(QColor(str(self._paleta_tema["grafica_texto"])))
        chart.setMargins(QMargins(0, 0, 0, 0))
        return chart

    @staticmethod
    def _crear_chart_view() -> QChartView:
        view = QChartView()
        view.setRenderHint(QPainter.RenderHint.Antialiasing, True)
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
        self.setStyleSheet(
            """
            QWidget#vistaModuloPrincipal {
                background: transparent;
            }
            QWidget#panelPrincipal,
            QWidget#paginaDashboard,
            QWidget#contenidoDashboard,
            QScrollArea#scrollDashboard,
            QScrollArea#scrollDashboard > QWidget > QWidget {
                background: transparent;
            }
            QScrollArea#scrollDashboard {
                border: none;
            }
            QFrame#sidebarPrincipal {
                background: #393379;
                border: 1px solid rgba(255, 255, 255, 0.10);
                border-radius: 22px;
            }
            QFrame#headerPrincipal {
                background: rgba(255, 255, 255, 0.12);
                border: 1px solid rgba(255, 255, 255, 0.18);
                border-radius: 22px;
            }
            QFrame#tarjetaPanel {
                background: qlineargradient(
                    x1: 0, y1: 0,
                    x2: 1, y2: 1,
                    stop: 0 rgba(255, 255, 255, 138),
                    stop: 0.52 rgba(246, 252, 255, 118),
                    stop: 1 rgba(225, 241, 249, 96)
                );
                border: 1px solid rgba(255, 255, 255, 156);
                border-radius: 24px;
            }
            QWidget#encabezadoSidebar,
            QWidget#contenedorNavegacionSidebar,
            QScrollArea#scrollNavegacionSidebar {
                background: transparent;
                border: none;
            }
            QFrame#seccionSidebarCard,
            QFrame#panelAccionesSidebar,
            QFrame#panelUsuarioHeader {
                background: transparent;
                border: none;
                border-radius: 0;
            }
            QPushButton#botonPerfilHeader {
                min-width: 48px;
                max-width: 48px;
                min-height: 48px;
                max-height: 48px;
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 24px;
            }
            QPushButton#botonPerfilHeader:hover {
                background: rgba(255, 255, 255, 0.12);
                border-color: rgba(109, 241, 220, 0.24);
            }
            QLabel#avatarPerfilHeader {
                background: rgba(109, 241, 220, 0.18);
                border: 1px solid rgba(109, 241, 220, 0.24);
                border-radius: 20px;
                color: #ffffff;
                font-size: 13px;
                font-weight: 900;
            }
            QWidget#contenedorItemsSidebar {
                background: transparent;
            }
            QLabel#logoSidebar {
                background: rgba(255, 255, 255, 0.08);
                border: none;
                border-radius: 16px;
            }
            QLabel#marcaPrincipal {
                color: #ffffff;
                font-size: 22px;
                font-weight: 900;
            }
            QLabel#subtituloMarca,
            QLabel#descripcionPrincipal {
                color: rgba(235, 242, 248, 0.76);
                font-size: 10px;
                font-weight: 600;
            }
            QLabel#descripcionPrincipal {
                font-size: 11px;
            }
            QLabel#descripcionPanel,
            QLabel#tabsSuaves {
                color: #8b96a8;
                font-size: 11px;
                font-weight: 600;
            }
            QLabel#tituloPrincipal {
                color: #ffffff;
            }
            QLabel#tituloSeccionSidebar {
                color: rgba(235, 242, 248, 0.62);
                font-size: 10px;
                font-weight: 900;
                letter-spacing: 0.8px;
                padding: 2px 6px 4px 6px;
            }
            QLabel#tituloSeccionSidebar[activa="true"] {
                color: #ffffff;
            }
            QLabel#tituloPrincipal {
                font-size: 21px;
                font-weight: 900;
            }
            QLabel#tituloPanel {
                color: #1b2430;
                font-size: 14px;
                font-weight: 800;
            }
            QPushButton#botonSidebar {
                min-height: 34px;
                border: 1px solid rgba(255, 255, 255, 0.03);
                border-radius: 12px;
                background: rgba(255, 255, 255, 0.05);
                color: rgba(245, 251, 255, 0.94);
                font-size: 11px;
                font-weight: 800;
                text-align: left;
                padding: 0 11px;
            }
            QPushButton#botonSidebar[tipoSidebar="modulo"] {
                margin-left: 0;
                padding-left: 12px;
            }
            QPushButton#botonSidebar[tipoSidebar="accion"] {
                background: rgba(255, 255, 255, 0.06);
            }
            QPushButton#botonSidebar:hover {
                background: rgba(255, 255, 255, 0.10);
                border-color: rgba(255, 255, 255, 0.12);
            }
            QPushButton#botonSidebar[activo="true"] {
                background: rgba(123, 194, 255, 0.30);
                border-color: rgba(146, 209, 255, 0.36);
                color: #ffffff;
            }
            QWidget#tarjetaInsight {
                background: qlineargradient(
                    x1: 0, y1: 0,
                    x2: 1, y2: 1,
                    stop: 0 rgba(255, 255, 255, 0.18),
                    stop: 1 rgba(237, 247, 252, 0.10)
                );
                border: 1px solid rgba(255, 255, 255, 0.24);
                border-radius: 16px;
            }
            QLabel#insightTitulo {
                color: rgba(64, 78, 98, 196);
                font-size: 11px;
                font-weight: 700;
            }
            QLabel#insightValor {
                color: #1b2430;
                font-size: 20px;
                font-weight: 900;
            }
            QLabel#insightDetalle {
                color: #6d7889;
                font-size: 11px;
            }
            QFrame#filaRanking {
                background: transparent;
            }
            QLabel#rankingEtiqueta {
                color: #374151;
                font-size: 11px;
                font-weight: 600;
            }
            QLabel#rankingValor {
                color: #1f2530;
                font-size: 11px;
                font-weight: 700;
            }
            QProgressBar#rankingBarra {
                background: rgba(255, 255, 255, 0.18);
                border: none;
                border-radius: 4px;
            }
            QProgressBar#rankingBarra::chunk {
                background: rgba(31, 37, 48, 0.72);
                border-radius: 4px;
            }
            QFrame#panelPerfilUsuario {
                background: #2c2966;
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 22px;
            }
            QFrame#encabezadoPanelPerfil,
            QFrame#bloquePanelPerfil,
            QFrame#piePanelPerfil {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.10);
                border-radius: 18px;
            }
            QLabel#avatarPanelPerfil {
                background: rgba(109, 241, 220, 0.16);
                border: 1px solid rgba(109, 241, 220, 0.24);
                border-radius: 27px;
                color: #ffffff;
                font-size: 18px;
                font-weight: 900;
            }
            QLabel#nombrePanelPerfil {
                color: #ffffff;
                font-size: 16px;
                font-weight: 900;
            }
            QLabel#rolPanelPerfil,
            QLabel#tituloDatoPerfil,
            QLabel#detallePanelPerfil {
                color: rgba(235, 242, 248, 0.70);
                font-size: 12px;
                font-weight: 600;
            }
            QLabel#valorDatoPerfil,
            QLabel#sistemaPanelPerfil {
                color: #f5fbff;
                font-size: 13px;
                font-weight: 800;
            }
            QLabel#sistemaPanelPerfil {
                font-size: 14px;
            }
            QLabel#iconoDatoPerfil {
                background: rgba(255, 255, 255, 0.06);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 12px;
            }
            """
        )
        if self._tema_actual == "claro":
            paleta = self._paleta_tema
            self.setStyleSheet(
                self.styleSheet()
                + f"""
                QFrame#sidebarPrincipal,
                QFrame#headerPrincipal {{
                    background: {paleta["fondo_superficie"]};
                    border: 1px solid {paleta["borde_principal"]};
                }}
                QFrame#tarjetaPanel {{
                    background: qlineargradient(
                        x1: 0, y1: 0,
                        x2: 1, y2: 1,
                        stop: 0 {paleta["tarjeta_panel_stop_1"]},
                        stop: 0.52 {paleta["tarjeta_panel_stop_2"]},
                        stop: 1 {paleta["tarjeta_panel_stop_3"]}
                    );
                    border: 1px solid {paleta["tarjeta_panel_borde"]};
                }}
                QFrame#seccionSidebarCard,
                QFrame#panelAccionesSidebar,
                QFrame#panelUsuarioHeader,
                QFrame#panelPerfilUsuario,
                QFrame#encabezadoPanelPerfil,
                QFrame#bloquePanelPerfil,
                QFrame#piePanelPerfil {{
                    background: {paleta["fondo_superficie_suave"]};
                    border: 1px solid {paleta["borde_suave"]};
                }}
                QPushButton#botonPerfilHeader {{
                    background: {paleta["fondo_superficie_suave"]};
                    border: 1px solid {paleta["borde_suave"]};
                    color: {paleta["texto_input"]};
                }}
                QPushButton#botonPerfilHeader:hover {{
                    background: {paleta["fondo_superficie"]};
                    border-color: {paleta["borde_principal"]};
                }}
                QLabel#avatarPerfilHeader,
                QLabel#avatarPanelPerfil {{
                    background: {paleta["fondo_avatar"]};
                    border: 1px solid {paleta["borde_avatar"]};
                    color: {paleta["texto_principal"]};
                }}
                QLabel#marcaPrincipal,
                QLabel#tituloPrincipal,
                QLabel#usuarioActivo,
                QLabel#nombrePanelPerfil {{
                    color: {paleta["texto_principal"]};
                }}
                QLabel#subtituloMarca,
                QLabel#descripcionPrincipal,
                QLabel#perfilActivo,
                QLabel#periodoHeader,
                QLabel#rolPanelPerfil,
                QLabel#tituloDatoPerfil,
                QLabel#detallePanelPerfil,
                QLabel#descripcionPanel,
                QLabel#tabsSuaves {{
                    color: {paleta["texto_secundario"]};
                }}
                QLabel#tituloPanel,
                QLabel#valorDatoPerfil,
                QLabel#sistemaPanelPerfil {{
                    color: {paleta["texto_panel_principal"]};
                }}
                QLabel#tituloSeccionSidebar {{
                    color: {paleta["texto_secundario"]};
                }}
                QLabel#tituloSeccionSidebar[activa="true"] {{
                    color: {paleta["texto_principal"]};
                }}
                QPushButton#botonSidebar {{
                    background: {paleta["fondo_superficie_muy_suave"]};
                    color: {paleta["texto_input"]};
                }}
                QPushButton#botonSidebar[tipoSidebar="accion"] {{
                    background: {paleta["fondo_panel_accion"]};
                }}
                QPushButton#botonSidebar:hover {{
                    background: {paleta["fondo_superficie"]};
                    border-color: {paleta["borde_principal"]};
                }}
                QPushButton#botonSidebar[activo="true"] {{
                    background: {paleta["fondo_badge_activo"]};
                    border-color: {paleta["borde_badge_activo"]};
                    color: {paleta["texto_principal"]};
                }}
                QWidget#tarjetaInsight {{
                    background: {paleta["fondo_superficie_suave"]};
                    border: 1px solid {paleta["borde_principal"]};
                }}
                QLabel#insightTitulo,
                QLabel#rankingEtiqueta,
                QLabel#rankingValor,
                QLabel#insightDetalle {{
                    color: {paleta["texto_panel_detalle"]};
                }}
                QLabel#insightValor {{
                    color: {paleta["texto_panel_fuerte"]};
                }}
                QProgressBar#rankingBarra {{
                    background: {paleta["ranking_barra"]};
                }}
                QProgressBar#rankingBarra::chunk {{
                    background: {paleta["ranking_chunk"]};
                }}
                QLabel#iconoDatoPerfil,
                QLabel#logoSidebar {{
                    background: {paleta["fondo_superficie_suave"]};
                    border: 1px solid {paleta["borde_suave"]};
                }}
                """
            )
