"""Vista del shell principal de SICAP."""

from __future__ import annotations

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
from PySide6.QtCore import QEasingCurve, QMargins, QPropertyAnimation, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QPaintEvent, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QFrame,
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
from comun.ui import VistaPlaceholderModulo, crear_boton_operativo, obtener_icono_tabler_coloreado
from modulos.principal.entidades import (
    AnaliticaDashboard,
    CategoriaDashboard,
    EstadoModuloPrincipal,
    InsightDashboard,
    ModuloNavegacion,
    PuntoSerieDashboard,
)


COLOR_FONDO_PRINCIPAL = "#2c2966"


class TarjetaMetricaEjecutiva(QFrame):
    """Tarjeta KPI con acento pastel para el dashboard ejecutivo."""

    def __init__(self, color_fondo: str) -> None:
        super().__init__()
        self._color_fondo = color_fondo
        self.setObjectName("tarjetaMetricaEjecutiva")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(102)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(6)

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
        color_base = QColor(self._color_fondo)
        tono_superior = QColor(color_base)
        tono_superior.setAlpha(164)
        tono_inferior = QColor(255, 255, 255, 104)
        self.setStyleSheet(
            f"""
            QFrame#tarjetaMetricaEjecutiva {{
                background: qlineargradient(
                    x1: 0, y1: 0,
                    x2: 1, y2: 1,
                    stop: 0 rgba({tono_superior.red()}, {tono_superior.green()}, {tono_superior.blue()}, {tono_superior.alpha()}),
                    stop: 1 rgba({tono_inferior.red()}, {tono_inferior.green()}, {tono_inferior.blue()}, {tono_inferior.alpha()})
                );
                border: 1px solid rgba(255, 255, 255, 162);
                border-radius: 17px;
            }}
            QLabel#tituloMetricaEjecutiva {{
                color: rgba(27, 36, 48, 220);
                font-size: 12px;
                font-weight: 700;
            }}
            QLabel#valorMetricaEjecutiva {{
                color: #1b2430;
                font-size: 30px;
                font-weight: 900;
            }}
            QLabel#detalleMetricaEjecutiva {{
                color: #55606f;
                font-size: 12px;
                font-weight: 600;
            }}
            """
        )


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
        self._botones_modulos: dict[str, QPushButton] = {}
        self._paginas_modulos: dict[str, QWidget] = {}
        self._tarjetas_metricas: dict[str, TarjetaMetricaEjecutiva] = {}
        self._filas_ranking: list[FilaRanking] = []
        self._tarjetas_insight: list[TarjetaInsight] = []
        self._animaciones_activas: list[object] = []
        self._aplicar_estilos()
        self._construir_ui()

    def paintEvent(self, evento: QPaintEvent) -> None:
        """Pinta el fondo principal del shell."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(COLOR_FONDO_PRINCIPAL))
        painter.drawRect(self.rect())
        painter.end()

        super().paintEvent(evento)

    def registrar_modulo(self, codigo: str, widget: QWidget) -> None:
        if codigo in self._paginas_modulos:
            return
        self._paginas_modulos[codigo] = widget
        self._stack_contenido.addWidget(widget)

    def mostrar_estado(self, estado: EstadoModuloPrincipal) -> None:
        primer_nombre = estado.nombre_completo.split()[0] if estado.nombre_completo else estado.nombre_usuario
        self._label_bienvenida.setText(f"Resumen general, {primer_nombre}")
        self._label_subresumen.setText(
            "Monitorea ingresos, deuda pendiente y estabilidad operativa desde un solo tablero."
        )
        self._label_usuario.setText(estado.nombre_completo)
        self._label_perfil.setText(estado.perfil)
        self._reconstruir_sidebar(estado.modulos)
        self._mostrar_metricas(estado)
        self._mostrar_analitica(estado.analitica)
        self._boton_mantenimiento.setVisible(estado.puede_abrir_mantenimiento)
        self.mostrar_modulo("dashboard")
        self._animar_aparicion_dashboard()

    def mostrar_modulo(self, codigo: str) -> None:
        pagina = self._paginas_modulos.get(codigo)
        if pagina is None:
            return
        self._stack_contenido.setCurrentWidget(pagina)
        for codigo_boton, boton in self._botones_modulos.items():
            boton.setProperty("activo", codigo_boton == codigo)
            boton.style().unpolish(boton)
            boton.style().polish(boton)

    def _construir_ui(self) -> None:
        layout_raiz = QHBoxLayout(self)
        layout_raiz.setContentsMargins(18, 18, 18, 18)
        layout_raiz.setSpacing(14)

        self._sidebar = QFrame()
        self._sidebar.setObjectName("sidebarPrincipal")
        self._sidebar.setFixedWidth(278)
        layout_sidebar = QVBoxLayout(self._sidebar)
        layout_sidebar.setContentsMargins(18, 18, 18, 18)
        layout_sidebar.setSpacing(14)

        layout_sidebar.addWidget(self._crear_encabezado_sidebar())

        separador_superior = QFrame()
        separador_superior.setObjectName("separadorSidebar")
        separador_superior.setFrameShape(QFrame.Shape.HLine)
        layout_sidebar.addWidget(separador_superior)

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
        self._contenedor_botones.setSpacing(10)
        self._scroll_navegacion.setWidget(contenedor_navegacion)
        layout_sidebar.addWidget(self._scroll_navegacion, 1)

        panel_acciones_sidebar = QFrame()
        panel_acciones_sidebar.setObjectName("panelAccionesSidebar")
        layout_acciones_sidebar = QVBoxLayout(panel_acciones_sidebar)
        layout_acciones_sidebar.setContentsMargins(12, 12, 12, 12)
        layout_acciones_sidebar.setSpacing(10)

        self._boton_mantenimiento = self._crear_boton_sidebar(
            ModuloNavegacion("mantenimiento", "Mantenimiento", "", "lock.svg")
        )
        self._boton_mantenimiento.clicked.connect(self.abrir_mantenimiento_solicitado.emit)
        self._boton_mantenimiento.setVisible(False)
        layout_acciones_sidebar.addWidget(self._boton_mantenimiento)

        self._boton_cerrar_sesion = self._crear_boton_sidebar(
            ModuloNavegacion("logout", "Cerrar sesion", "", "arrow-left.svg")
        )
        self._boton_cerrar_sesion.clicked.connect(self.cerrar_sesion_solicitada.emit)
        layout_acciones_sidebar.addWidget(self._boton_cerrar_sesion)
        layout_sidebar.addWidget(panel_acciones_sidebar)

        panel = QWidget()
        panel.setObjectName("panelPrincipal")
        layout_panel = QVBoxLayout(panel)
        layout_panel.setContentsMargins(0, 0, 0, 0)
        layout_panel.setSpacing(16)

        header = QFrame()
        header.setObjectName("headerPrincipal")
        layout_header = QHBoxLayout(header)
        layout_header.setContentsMargins(18, 18, 18, 18)
        layout_header.setSpacing(16)

        bloque_titulo = QVBoxLayout()
        bloque_titulo.setSpacing(4)
        self._label_bienvenida = QLabel("Resumen general")
        self._label_bienvenida.setObjectName("tituloPrincipal")
        self._label_subresumen = QLabel("")
        self._label_subresumen.setObjectName("descripcionPrincipal")
        self._label_subresumen.setWordWrap(True)
        bloque_titulo.addWidget(self._label_bienvenida)
        bloque_titulo.addWidget(self._label_subresumen)

        panel_usuario_header = QFrame()
        panel_usuario_header.setObjectName("panelUsuarioHeader")
        bloque_usuario = QVBoxLayout(panel_usuario_header)
        bloque_usuario.setContentsMargins(14, 12, 14, 12)
        bloque_usuario.setSpacing(2)
        self._label_periodo = QLabel("Hoy")
        self._label_periodo.setObjectName("periodoHeader")
        self._label_usuario = QLabel("")
        self._label_usuario.setObjectName("usuarioActivo")
        self._label_perfil = QLabel("")
        self._label_perfil.setObjectName("perfilActivo")
        bloque_usuario.addWidget(self._label_periodo, alignment=Qt.AlignmentFlag.AlignRight)
        bloque_usuario.addWidget(self._label_usuario, alignment=Qt.AlignmentFlag.AlignRight)
        bloque_usuario.addWidget(self._label_perfil, alignment=Qt.AlignmentFlag.AlignRight)

        layout_header.addLayout(bloque_titulo, 1)
        layout_header.addWidget(panel_usuario_header, alignment=Qt.AlignmentFlag.AlignTop)

        self._stack_contenido = QStackedWidget()
        self._stack_contenido.setObjectName("stackPrincipal")

        self._pagina_dashboard = self._crear_dashboard()
        self.registrar_modulo("dashboard", self._pagina_dashboard)

        layout_panel.addWidget(header)
        layout_panel.addWidget(self._stack_contenido, 1)

        layout_raiz.addWidget(self._sidebar)
        layout_raiz.addWidget(panel, 1)

    def _crear_dashboard(self) -> QWidget:
        pagina = QWidget()
        pagina.setObjectName("paginaDashboard")
        layout = QVBoxLayout(pagina)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        self._grid_metricas = QGridLayout()
        self._grid_metricas.setHorizontalSpacing(14)
        self._grid_metricas.setVerticalSpacing(14)
        layout.addLayout(self._grid_metricas)

        fila_superior = QHBoxLayout()
        fila_superior.setSpacing(16)

        panel_tendencia = QFrame()
        panel_tendencia.setObjectName("tarjetaPanel")
        layout_tendencia = QVBoxLayout(panel_tendencia)
        layout_tendencia.setContentsMargins(20, 18, 20, 18)
        layout_tendencia.setSpacing(10)

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
        self._grafica_tendencia.setMinimumHeight(268)
        layout_tendencia.addLayout(fila_titulo)
        layout_tendencia.addWidget(self._grafica_tendencia, 1)

        panel_ranking = QFrame()
        panel_ranking.setObjectName("tarjetaPanel")
        panel_ranking.setFixedWidth(272)
        layout_ranking = QVBoxLayout(panel_ranking)
        layout_ranking.setContentsMargins(18, 17, 18, 18)
        layout_ranking.setSpacing(10)
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

        fila_superior.addWidget(panel_tendencia, 1)
        fila_superior.addWidget(panel_ranking)
        layout.addLayout(fila_superior)

        fila_inferior = QHBoxLayout()
        fila_inferior.setSpacing(16)

        panel_estados = QFrame()
        panel_estados.setObjectName("tarjetaPanel")
        layout_estados = QVBoxLayout(panel_estados)
        layout_estados.setContentsMargins(20, 18, 20, 18)
        layout_estados.setSpacing(10)
        titulo_estados = QLabel("Estado del servicio")
        titulo_estados.setObjectName("tituloPanel")
        descripcion_estados = QLabel("Distribucion de casas por estado operativo.")
        descripcion_estados.setObjectName("descripcionPanel")
        self._grafica_estados = self._crear_chart_view()
        self._grafica_estados.setMinimumHeight(210)
        layout_estados.addWidget(titulo_estados)
        layout_estados.addWidget(descripcion_estados)
        layout_estados.addWidget(self._grafica_estados, 1)

        panel_insights = QFrame()
        panel_insights.setObjectName("tarjetaPanel")
        panel_insights.setFixedWidth(308)
        layout_insights = QVBoxLayout(panel_insights)
        layout_insights.setContentsMargins(18, 17, 18, 18)
        layout_insights.setSpacing(10)
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

        panel_distribucion = QFrame()
        panel_distribucion.setObjectName("tarjetaPanel")
        layout_distribucion = QVBoxLayout(panel_distribucion)
        layout_distribucion.setContentsMargins(20, 18, 20, 18)
        layout_distribucion.setSpacing(10)
        titulo_distribucion = QLabel("Distribucion de deuda")
        titulo_distribucion.setObjectName("tituloPanel")
        descripcion_distribucion = QLabel("Peso relativo del saldo pendiente por barrio.")
        descripcion_distribucion.setObjectName("descripcionPanel")
        self._grafica_distribucion = self._crear_chart_view()
        self._grafica_distribucion.setMinimumHeight(210)
        layout_distribucion.addWidget(titulo_distribucion)
        layout_distribucion.addWidget(descripcion_distribucion)
        layout_distribucion.addWidget(self._grafica_distribucion, 1)

        fila_inferior.addWidget(panel_estados, 1)
        fila_inferior.addWidget(panel_distribucion, 1)
        fila_inferior.addWidget(panel_insights)
        layout.addLayout(fila_inferior)
        return pagina

    def _mostrar_metricas(self, estado: EstadoModuloPrincipal) -> None:
        colores = ("#e9eeff", "#e8f1ff", "#eef0ff", "#eaf3ff", "#edf3ff")
        while self._grid_metricas.count():
            item = self._grid_metricas.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()
        self._tarjetas_metricas.clear()

        for indice, metrica in enumerate(estado.metricas):
            tarjeta = TarjetaMetricaEjecutiva(colores[indice % len(colores)])
            tarjeta.actualizar(metrica.titulo, metrica.valor, metrica.detalle)
            self._tarjetas_metricas[metrica.codigo] = tarjeta
            self._grid_metricas.addWidget(tarjeta, 0, indice)

    def _mostrar_analitica(self, analitica: AnaliticaDashboard) -> None:
        self._construir_ranking(analitica.deuda_por_barrio)
        self._construir_insights(analitica.insights)
        self._grafica_tendencia.setChart(self._crear_chart_tendencia(analitica.recaudacion_mensual))
        self._grafica_estados.setChart(self._crear_chart_estados(analitica.estados_servicio))
        self._grafica_distribucion.setChart(
            self._crear_chart_distribucion_deuda(analitica.deuda_por_barrio)
        )

    def _reconstruir_sidebar(self, modulos: tuple[ModuloNavegacion, ...]) -> None:
        while self._contenedor_botones.count():
            item = self._contenedor_botones.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()
        self._botones_modulos.clear()
        secciones: dict[str, list[ModuloNavegacion]] = {
            "Vista general": [],
            "Barrios": [],
            "Abonados": [],
            "Casas": [],
            "Cobranza y control": [],
            "Administracion": [],
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
            widget_seccion = QFrame()
            widget_seccion.setObjectName("seccionSidebarCard")
            layout_seccion = QVBoxLayout(widget_seccion)
            layout_seccion.setContentsMargins(12, 12, 12, 12)
            layout_seccion.setSpacing(8)

            etiqueta = QLabel(titulo_seccion.upper())
            etiqueta.setObjectName("categoriaSidebar")
            layout_seccion.addWidget(etiqueta)

            for modulo in modulos_seccion:
                boton = self._crear_boton_sidebar(modulo)
                boton.clicked.connect(
                    lambda checked=False, codigo=modulo.codigo: self._solicitar_modulo(codigo)
                )
                layout_seccion.addWidget(boton)
                self._botones_modulos[modulo.codigo] = boton

            self._contenedor_botones.addWidget(widget_seccion)

        self._contenedor_botones.addStretch(1)

    def _solicitar_modulo(self, codigo: str) -> None:
        self.modulo_solicitado.emit(codigo)
        self.mostrar_modulo(codigo)

    def _crear_boton_sidebar(self, modulo: ModuloNavegacion) -> QPushButton:
        boton = crear_boton_operativo(modulo.titulo)
        boton.setObjectName("botonSidebar")
        boton.setIcon(obtener_icono_tabler_coloreado(modulo.icono, "#eef6ff", tamano=18))
        boton.setIconSize(boton.iconSize())
        boton.setToolTip(modulo.descripcion or modulo.titulo)
        return boton

    def _crear_encabezado_sidebar(self) -> QWidget:
        encabezado = QWidget()
        encabezado.setObjectName("encabezadoSidebar")
        layout = QHBoxLayout(encabezado)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        label_logo = QLabel()
        label_logo.setObjectName("logoSidebar")
        label_logo.setFixedSize(42, 42)
        label_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ruta_logo = self._gestor_rutas.obtener_ruta_logo_marca()
        if ruta_logo.exists():
            pixmap_logo = QPixmap(str(ruta_logo))
            if not pixmap_logo.isNull():
                label_logo.setPixmap(
                    pixmap_logo.scaled(
                        34,
                        34,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )

        bloque_texto = QVBoxLayout()
        bloque_texto.setContentsMargins(0, 0, 0, 0)
        bloque_texto.setSpacing(2)

        titulo = QLabel("SICAP")
        titulo.setObjectName("marcaPrincipal")
        subtitulo = QLabel("Sistema de Control")
        subtitulo.setObjectName("subtituloMarca")
        bloque_texto.addWidget(titulo)
        bloque_texto.addWidget(subtitulo)

        layout.addWidget(label_logo, alignment=Qt.AlignmentFlag.AlignTop)
        layout.addLayout(bloque_texto, 1)
        return encabezado

    @staticmethod
    def _resolver_categoria_sidebar(codigo_modulo: str) -> str:
        if codigo_modulo == "dashboard":
            return "Vista general"
        if codigo_modulo == "barrios":
            return "Barrios"
        if codigo_modulo in {"abonados", "atencion_abonado", "conexion_reconexion"}:
            return "Abonados"
        if codigo_modulo == "casas":
            return "Casas"
        if codigo_modulo in {"pagos", "historial_pagos", "morosidad", "planes_pago", "reportes"}:
            return "Cobranza y control"
        if codigo_modulo in {"usuarios", "configuracion"}:
            return "Administracion"
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
        actual.setColor(QColor("#1f2530"))
        actual.setPen(QPen(QColor("#1f2530"), 2.1))

        referencia = QLineSeries()
        referencia.setName("Promedio")
        pen_referencia = QPen(QColor("#8ab4ff"), 1.8)
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
        eje_x.setLabelsColor(QColor("#8b96a8"))
        eje_x.setGridLineVisible(False)

        eje_y = QValueAxis()
        maximo = max(valores + [promedio, 1.0])
        eje_y.setRange(0, maximo * 1.25)
        eje_y.setTickCount(5)
        eje_y.setLabelsColor(QColor("#8b96a8"))
        eje_y.setGridLineColor(QColor("#eef2f7"))
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
        colores = ["#8fb2ec", "#61d4c8", "#000000", "#7ab1f2", "#b598ea", "#75d685"]
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
        eje_x.setLabelsColor(QColor("#8b96a8"))
        eje_x.setGridLineVisible(False)

        eje_y = QValueAxis()
        maximo = max((categoria.valor for categoria in datos), default=1.0) or 1.0
        eje_y.setRange(0, maximo * 1.25)
        eje_y.setTickCount(5)
        eje_y.setLabelsColor(QColor("#8b96a8"))
        eje_y.setGridLineColor(QColor("#eef2f7"))
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
        colores = ["#000000", "#8fb2ec", "#9ee4c4", "#7fb8ff", "#c5d2dd"]
        for indice, categoria in enumerate(datos):
            trozo = serie.append(categoria.etiqueta, max(categoria.valor, 0.01))
            trozo.setColor(QColor(colores[indice % len(colores)]))
            trozo.setLabelVisible(False)
            trozo.setBorderColor(QColor("#ffffff"))
            trozo.setBorderWidth(1)

        chart = QChart()
        chart.addSeries(serie)
        chart.setBackgroundVisible(False)
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignmentFlag.AlignRight)
        chart.legend().setLabelColor(QColor("#687588"))
        chart.setMargins(QMargins(0, 0, 0, 0))
        return chart

    @staticmethod
    def _crear_chart_view() -> QChartView:
        view = QChartView()
        view.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        view.setStyleSheet("background: transparent; border: none;")
        return view

    def _animar_aparicion_dashboard(self) -> None:
        self._animaciones_activas.clear()
        widgets = [
            *self._tarjetas_metricas.values(),
            *self._filas_ranking,
            *self._tarjetas_insight,
        ]
        for indice, widget in enumerate(widgets):
            efecto = QGraphicsOpacityEffect(widget)
            widget.setGraphicsEffect(efecto)
            animacion = QPropertyAnimation(efecto, b"opacity", self)
            animacion.setDuration(220)
            animacion.setStartValue(0.0)
            animacion.setEndValue(1.0)
            animacion.setEasingCurve(QEasingCurve.Type.OutCubic)
            self._animaciones_activas.append((efecto, animacion))
            QTimer.singleShot(indice * 35, animacion.start)

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
            QWidget#paginaDashboard {
                background: transparent;
            }
            QFrame#sidebarPrincipal,
            QFrame#headerPrincipal {
                background: rgba(255, 255, 255, 0.10);
                border: 1px solid rgba(255, 255, 255, 0.16);
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
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.10);
                border-radius: 18px;
            }
            QLabel#logoSidebar {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.10);
                border-radius: 14px;
            }
            QFrame#separadorSidebar {
                color: rgba(255, 255, 255, 0.10);
                background: rgba(255, 255, 255, 0.10);
                max-height: 1px;
                border: none;
            }
            QLabel#marcaPrincipal {
                color: #ffffff;
                font-size: 22px;
                font-weight: 900;
            }
            QLabel#subtituloMarca,
            QLabel#descripcionPrincipal,
            QLabel#perfilActivo,
            QLabel#periodoHeader {
                color: rgba(235, 242, 248, 0.76);
                font-size: 12px;
                font-weight: 600;
            }
            QLabel#descripcionPanel,
            QLabel#tabsSuaves {
                color: #8b96a8;
                font-size: 12px;
                font-weight: 600;
            }
            QLabel#tituloPrincipal,
            QLabel#usuarioActivo {
                color: #ffffff;
            }
            QLabel#categoriaSidebar {
                color: rgba(235, 242, 248, 0.68);
                font-size: 11px;
                font-weight: 800;
                letter-spacing: 0.8px;
                padding: 2px 4px 4px 4px;
            }
            QLabel#tituloPrincipal {
                font-size: 22px;
                font-weight: 900;
            }
            QLabel#tituloPanel {
                color: #1b2430;
                font-size: 15px;
                font-weight: 800;
            }
            QLabel#usuarioActivo {
                font-size: 14px;
                font-weight: 800;
            }
            QPushButton#botonSidebar {
                min-height: 44px;
                border: 1px solid transparent;
                border-radius: 16px;
                background: rgba(255, 255, 255, 0.04);
                color: rgba(245, 251, 255, 0.94);
                font-size: 13px;
                font-weight: 800;
                text-align: left;
                padding: 0 16px;
            }
            QPushButton#botonSidebar:hover {
                background: rgba(255, 255, 255, 0.10);
                border-color: rgba(255, 255, 255, 0.14);
            }
            QPushButton#botonSidebar[activo="true"] {
                background: rgba(109, 241, 220, 0.16);
                border-color: rgba(109, 241, 220, 0.30);
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
                border-radius: 18px;
            }
            QLabel#insightTitulo {
                color: rgba(64, 78, 98, 196);
                font-size: 12px;
                font-weight: 700;
            }
            QLabel#insightValor {
                color: #1b2430;
                font-size: 23px;
                font-weight: 900;
            }
            QLabel#insightDetalle {
                color: #6d7889;
                font-size: 12px;
            }
            QFrame#filaRanking {
                background: transparent;
            }
            QLabel#rankingEtiqueta {
                color: #374151;
                font-size: 12px;
                font-weight: 600;
            }
            QLabel#rankingValor {
                color: #1f2530;
                font-size: 12px;
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
            """
        )
