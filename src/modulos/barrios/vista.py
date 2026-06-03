"""Vista PySide6 del modulo de barrios."""

from __future__ import annotations

from typing import Callable

from PySide6.QtCore import QElapsedTimer, QEvent, QSize, Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QButtonGroup,
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTableWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from comun.ui import (
    BotonAccionContextual,
    CampoDetalleSigqua,
    DialogoBaseSigqua,
    DialogoConfirmacionSigqua,
    DialogoMensajeSigqua,
    EncabezadoDetalleSigqua,
    SeccionDetalleSigqua,
    TarjetaResumenDetalleSigqua,
    aplicar_estilo_boton_operativo,
    configurar_tabla_operativa,
    crear_badge_estado_detalle_sigqua,
    crear_boton_copiar_detalle_sigqua,
    crear_boton_operativo,
    crear_item_tabla,
    obtener_estilo_detalle_sigqua,
    obtener_icono_tabler_coloreado,
    resolver_variante_boton_modal,
)
from comun.ui.componentes import COLOR_FONDO_DIALOGO, RADIO_TARJETA_DIALOGO
from comun.ui.temas import (
    TEMA_SIGQUA_PREDETERMINADO,
    obtener_fondo_header_destacado,
    obtener_paleta_tema,
    resolver_nombre_tema,
)
from modulos.barrios.entidades import (
    Barrio,
    FILTRO_BARRIOS_ACTIVOS,
    FILTRO_BARRIOS_CON_ABONADOS,
    FILTRO_BARRIOS_INACTIVOS,
    FILTRO_BARRIOS_SIN_ABONADOS,
    FILTRO_BARRIOS_TODOS,
    FormularioBarrio,
    PaginaBarrios,
    ResumenBarrios,
)


class TarjetaResumenBarrio(QFrame):
    """Tarjeta de resumen para el encabezado del modulo."""

    def __init__(self, icono: str, color_icono: str) -> None:
        super().__init__()
        self.setObjectName("tarjetaResumenBarrios")
        self.setMinimumHeight(96)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        self._icono = QLabel("")
        self._icono.setObjectName("iconoTarjetaResumen")
        self._icono.setFixedSize(38, 38)
        self._icono.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icono.setPixmap(
            obtener_icono_tabler_coloreado(icono, color_icono, tamano=18).pixmap(18, 18)
        )
        self._icono.setProperty("colorTarjeta", color_icono)

        bloque_texto = QVBoxLayout()
        bloque_texto.setContentsMargins(0, 0, 0, 0)
        bloque_texto.setSpacing(2)

        self._titulo = QLabel("")
        self._titulo.setObjectName("tituloTarjetaResumen")
        self._valor = QLabel("")
        self._valor.setObjectName("valorTarjetaResumen")
        self._detalle = QLabel("")
        self._detalle.setObjectName("detalleTarjetaResumen")
        self._detalle.setWordWrap(True)

        bloque_texto.addWidget(self._titulo)
        bloque_texto.addWidget(self._valor)
        bloque_texto.addWidget(self._detalle)
        bloque_texto.addStretch(1)

        layout.addWidget(self._icono, alignment=Qt.AlignmentFlag.AlignTop)
        layout.addLayout(bloque_texto, 1)

    def actualizar(self, titulo: str, valor: str, detalle: str) -> None:
        self._titulo.setText(titulo)
        self._valor.setText(valor)
        self._detalle.setText(detalle)


class BotonIconoFilaBarrio(QToolButton):
    """Boton de accion compacto con icono centrado y color en hover."""

    COLOR_BASE = "#c8d6f1"
    INTERVALO_TOOLTIP_MS = 1600

    def __init__(self, icono: str, color_hover: str, tooltip: str) -> None:
        super().__init__()
        self._icono = icono
        self._color_hover = color_hover
        self._color_base = self.COLOR_BASE
        self._temporizador_tooltip = QElapsedTimer()
        self.setObjectName("botonIconoFilaBarrio")
        self.setToolTip(tooltip)
        self.setToolTipDuration(1400)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setAutoRaise(True)
        self.setFixedSize(32, 32)
        self.setIconSize(QSize(18, 18))
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self._actualizar_icono(self.COLOR_BASE)

    def event(self, evento: QEvent) -> bool:
        if evento.type() == QEvent.Type.ToolTip:
            if (
                self._temporizador_tooltip.isValid()
                and self._temporizador_tooltip.elapsed() < self.INTERVALO_TOOLTIP_MS
            ):
                return True
            self._temporizador_tooltip.restart()
        return super().event(evento)

    def enterEvent(self, evento: object) -> None:
        self._actualizar_icono(self._color_hover)
        super().enterEvent(evento)

    def leaveEvent(self, evento: object) -> None:
        self._actualizar_icono(self._color_base)
        super().leaveEvent(evento)

    def _actualizar_icono(self, color_icono: str) -> None:
        self.setIcon(obtener_icono_tabler_coloreado(self._icono, color_icono, tamano=18))

    def aplicar_tema(self, nombre_tema: str) -> None:
        paleta = obtener_paleta_tema(nombre_tema)
        self._color_base = str(paleta["icono_fila_base"])
        self._actualizar_icono(self._color_base)


class DialogoFormularioBarrio(DialogoBaseSigqua):
    """Modal para crear o editar barrios."""

    def __init__(self, barrio: Barrio | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._barrio = barrio
        self.setMinimumWidth(520)
        self.setMinimumHeight(340)
        self._construir_ui()

    def obtener_formulario(self) -> FormularioBarrio:
        return FormularioBarrio(
            identificador=None if self._barrio is None else self._barrio.identificador,
            nombre=self._campo_nombre.text(),
            estado=self._combo_estado.currentText(),
            observaciones=self._campo_observaciones.toPlainText(),
        )

    def accept(self) -> None:
        if not self._campo_nombre.text().strip():
            self._mensaje.setText("Indica el nombre del barrio para continuar.")
            self._mensaje.setVisible(True)
            return
        self._mensaje.setVisible(False)
        super().accept()

    def _construir_ui(self) -> None:
        titulo = QLabel("Editar barrio" if self._barrio else "Nuevo barrio")
        titulo.setObjectName("tituloDialogoSigqua")
        descripcion = QLabel(
            "Completa el formulario con la informacion principal del barrio."
        )
        descripcion.setObjectName("descripcionDialogoSigqua")
        descripcion.setWordWrap(True)

        fila_superior = QHBoxLayout()
        fila_superior.setContentsMargins(0, 0, 0, 0)
        fila_superior.setSpacing(8)

        self._campo_nombre = QLineEdit()
        self._campo_nombre.setPlaceholderText("Nombre del barrio")
        self._combo_estado = QComboBox()
        self._combo_estado.addItems(["ACTIVO", "INACTIVO"])
        self._campo_observaciones = QPlainTextEdit()
        self._campo_observaciones.setPlaceholderText("Observaciones")
        self._campo_observaciones.setFixedHeight(60)

        if self._barrio is not None:
            self._campo_nombre.setText(self._barrio.nombre)
            self._combo_estado.setCurrentText(self._barrio.estado)
            self._campo_observaciones.setPlainText(self._barrio.observaciones)

        fila_superior.addWidget(
            self._crear_bloque_formulario("Nombre del barrio", self._campo_nombre),
            2,
        )
        fila_superior.addWidget(
            self._crear_bloque_formulario("Estado", self._combo_estado),
            1,
        )

        panel_datos = self._crear_panel_formulario(
            "Datos principales",
            "Configura el nombre del barrio y su estado operativo dentro del sistema.",
        )
        panel_datos.layout().addLayout(fila_superior)
        panel_datos.layout().addWidget(
            self._crear_bloque_formulario("Observaciones", self._campo_observaciones)
        )

        self._mensaje = QLabel("")
        self._mensaje.setObjectName("mensajeErrorDialogoSigqua")
        self._mensaje.setVisible(False)

        fila_acciones = QHBoxLayout()
        fila_acciones.setSpacing(10)
        variante_cancelar = resolver_variante_boton_modal("Cancelar", "neutro")
        variante_guardar = resolver_variante_boton_modal("Guardar cambios", "primario")
        boton_cancelar = BotonAccionContextual(
            "Cancelar",
            variante=variante_cancelar,
            centrado=True,
            mostrar_icono=False,
        )
        boton_guardar = BotonAccionContextual(
            "Guardar cambios",
            variante=variante_guardar,
            centrado=True,
            mostrar_icono=False,
        )
        boton_cancelar.setMinimumWidth(132)
        boton_guardar.setMinimumWidth(160)
        boton_cancelar.clicked.connect(self.reject)
        boton_guardar.clicked.connect(self.accept)
        fila_acciones.addWidget(boton_cancelar)
        fila_acciones.addStretch(1)
        fila_acciones.addWidget(boton_guardar)

        contenido_scroll = QWidget()
        layout_scroll = QVBoxLayout(contenido_scroll)
        layout_scroll.setContentsMargins(0, 0, 0, 0)
        layout_scroll.setSpacing(8)
        layout_scroll.addWidget(panel_datos)
        layout_scroll.addWidget(self._mensaje)
        layout_scroll.addStretch(1)

        self.setStyleSheet(
            self.styleSheet()
            + f"""
            QLabel {{
                color: {self._paleta_tema["texto_input"]};
                font-size: 13px;
                font-weight: 700;
            }}
            """
        )
        self.layout_cabecera.addWidget(titulo)
        self.layout_cabecera.addWidget(descripcion)
        self.layout_cuerpo.addWidget(
            self.crear_area_scroll_cuerpo(contenido_scroll, "scrollFormularioBarrio")
        )
        self.layout_pie.addLayout(fila_acciones)

    def _crear_bloque_formulario(self, etiqueta: str, campo: QWidget) -> QWidget:
        bloque = QWidget()
        layout = QVBoxLayout(bloque)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        label = QLabel(etiqueta)
        label.setObjectName("etiquetaDatoDialogoSigqua")
        layout.addWidget(label)
        layout.addWidget(campo)
        return bloque

    def _crear_panel_formulario(self, titulo: str, descripcion: str) -> QFrame:
        panel = QFrame()
        panel.setObjectName("bloqueDialogoSigqua")
        layout_panel = QVBoxLayout(panel)
        layout_panel.setContentsMargins(12, 12, 12, 12)
        layout_panel.setSpacing(6)
        label_titulo = QLabel(titulo)
        label_titulo.setObjectName("etiquetaDatoDialogoSigqua")
        label_descripcion = QLabel(descripcion)
        label_descripcion.setObjectName("descripcionDialogoSigqua")
        label_descripcion.setWordWrap(True)
        layout_panel.addWidget(label_titulo)
        layout_panel.addWidget(label_descripcion)
        return panel


class DialogoDetalleBarrio(DialogoBaseSigqua):
    """Modal para consultar detalle del barrio."""

    def __init__(
        self,
        barrio: Barrio,
        fecha_creacion: str,
        fecha_actualizada: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._barrio = barrio
        self._fecha_creacion = fecha_creacion
        self._fecha_actualizada = fecha_actualizada
        self._accion_resultado = "cerrar"
        self.setMinimumWidth(780)
        self.setMinimumHeight(580)
        self._construir_ui()

    @property
    def accion_resultado(self) -> str:
        return self._accion_resultado

    def _construir_ui(self) -> None:
        titulo = QLabel("Detalle de barrio")
        titulo.setObjectName("tituloDialogoSigqua")
        descripcion = QLabel(
            "Consulta informaciÃ³n general, estado operativo y estadÃ­sticas del barrio."
        )
        descripcion.setObjectName("descripcionDialogoSigqua")
        descripcion.setWordWrap(True)

        contenedor_scroll = QWidget()
        contenedor_scroll.setObjectName("contenedorScrollDetalleBarrio")
        layout_scroll = QVBoxLayout(contenedor_scroll)
        layout_scroll.setContentsMargins(0, 0, 0, 0)
        layout_scroll.setSpacing(12)

        panel_detalle = QFrame()
        panel_detalle.setObjectName("panelDetalleSigqua")
        panel_detalle_layout = QVBoxLayout(panel_detalle)
        panel_detalle_layout.setContentsMargins(18, 18, 18, 18)
        panel_detalle_layout.setSpacing(14)

        encabezado = EncabezadoDetalleSigqua(
            self._barrio.codigo,
            self._barrio.nombre,
            boton_copiar=crear_boton_copiar_detalle_sigqua(
                str(self._barrio.identificador or ""),
                etiqueta="ID interno",
            ),
            badges=(
                crear_badge_estado_detalle_sigqua(
                    self._barrio.estado.title(),
                    "activo" if self._barrio.estado == "ACTIVO" else "info",
                ),
            ),
        )

        grid_info = QGridLayout()
        grid_info.setHorizontalSpacing(14)
        grid_info.setVerticalSpacing(14)
        grid_info.addWidget(CampoDetalleSigqua("Codigo", self._barrio.codigo), 0, 0)
        grid_info.addWidget(CampoDetalleSigqua("Estado", self._barrio.estado.title()), 0, 1)
        grid_info.addWidget(CampoDetalleSigqua("Creado", self._fecha_creacion), 1, 0)
        grid_info.addWidget(CampoDetalleSigqua("Ultima actualizacion", self._fecha_actualizada), 1, 1)

        fila_metricas = QHBoxLayout()
        fila_metricas.setSpacing(12)
        fila_metricas.addWidget(TarjetaResumenDetalleSigqua("Abonados", str(self._barrio.total_abonados)), 1)
        fila_metricas.addWidget(TarjetaResumenDetalleSigqua("Casas", str(self._barrio.total_casas)), 1)

        observaciones = CampoDetalleSigqua(
            "Observaciones",
            self._barrio.observaciones or "Sin observaciones registradas.",
        )

        fila_acciones = QHBoxLayout()
        fila_acciones.setSpacing(10)
        variante_cerrar = resolver_variante_boton_modal("Cerrar", "neutro")
        variante_ver = resolver_variante_boton_modal("Ver detalle", "informacion")
        boton_cerrar = BotonAccionContextual("Cerrar", icono="x.svg", variante=variante_cerrar, centrado=True, mostrar_icono=True)
        boton_ver_abonados = BotonAccionContextual("Ver abonados", icono="users.svg", variante=variante_ver, centrado=True, mostrar_icono=True)
        boton_ver_casas = BotonAccionContextual("Ver casas", icono="home.svg", variante=variante_ver, centrado=True, mostrar_icono=True)
        boton_editar = BotonAccionContextual("Editar", icono="edit.svg", variante="edicion", centrado=True, mostrar_icono=True)
        boton_cerrar.setMinimumWidth(124)
        boton_ver_abonados.setMinimumWidth(140)
        boton_ver_casas.setMinimumWidth(132)
        boton_editar.setMinimumWidth(124)
        boton_cerrar.clicked.connect(self.reject)
        boton_ver_abonados.clicked.connect(self._abrir_abonados)
        boton_ver_casas.clicked.connect(self._abrir_casas)
        boton_editar.clicked.connect(self._solicitar_edicion)
        fila_acciones.addWidget(boton_cerrar)
        fila_acciones.addStretch(1)
        fila_acciones.addWidget(boton_ver_abonados)
        fila_acciones.addWidget(boton_ver_casas)
        fila_acciones.addWidget(boton_editar)

        panel_detalle_layout.addWidget(encabezado)
        panel_detalle_layout.addWidget(SeccionDetalleSigqua("Contexto territorial", "Consulta el codigo, estado operativo y las fechas base del barrio.", grid_info))
        panel_detalle_layout.addWidget(SeccionDetalleSigqua("Cobertura operativa", "Resume la cantidad de abonados y casas relacionadas con el barrio.", fila_metricas))
        panel_detalle_layout.addWidget(SeccionDetalleSigqua("Observaciones", "Notas administrativas o contexto adicional del barrio.", [observaciones]))
        layout_scroll.addWidget(panel_detalle)

        self.layout_cabecera.addWidget(titulo)
        self.layout_cabecera.addWidget(descripcion)
        self.layout_cuerpo.addWidget(self.crear_area_scroll_cuerpo(contenedor_scroll, "scrollDetalleBarrio"))
        self.layout_pie.addLayout(fila_acciones)
        self._aplicar_estilos()
        return

        contenedor_scroll = QWidget()
        contenedor_scroll.setObjectName("contenedorScrollDetalleBarrio")
        layout_scroll = QVBoxLayout(contenedor_scroll)
        layout_scroll.setContentsMargins(0, 0, 0, 0)
        layout_scroll.setSpacing(12)

        panel_detalle = QFrame()
        panel_detalle.setObjectName("panelDetalleSigqua")
        panel_detalle_layout = QVBoxLayout(panel_detalle)
        panel_detalle_layout.setContentsMargins(18, 18, 18, 18)
        panel_detalle_layout.setSpacing(14)

        fila_superior = QHBoxLayout()
        fila_superior.setSpacing(12)
        bloque_nombre = QVBoxLayout()
        bloque_nombre.setSpacing(4)
        fila_codigo = QHBoxLayout()
        fila_codigo.setContentsMargins(0, 0, 0, 0)
        fila_codigo.setSpacing(6)
        codigo = QLabel(self._barrio.codigo)
        codigo.setObjectName("codigoBarrioDetalle")
        boton_copiar_id = self._crear_boton_copiar_id(self._barrio.identificador)
        nombre = QLabel(self._barrio.nombre)
        nombre.setObjectName("nombreBarrioDetalle")
        fila_codigo.addWidget(codigo)
        fila_codigo.addWidget(boton_copiar_id, alignment=Qt.AlignmentFlag.AlignVCenter)
        fila_codigo.addStretch(1)
        bloque_nombre.addLayout(fila_codigo)
        bloque_nombre.addWidget(nombre)

        estado = QLabel(self._barrio.estado.title())
        estado.setObjectName("badgeDetalleBarrio")
        estado.setProperty("activo", self._barrio.estado == "ACTIVO")
        estado.style().unpolish(estado)
        estado.style().polish(estado)

        fila_superior.addLayout(bloque_nombre, 1)
        fila_superior.addWidget(estado, alignment=Qt.AlignmentFlag.AlignTop)

        encabezado_contexto = self._crear_encabezado_seccion_detalle(
            "Contexto territorial",
            "Consulta el cÃ³digo, estado operativo y las fechas base del barrio.",
        )
        grid_info = QGridLayout()
        grid_info.setHorizontalSpacing(14)
        grid_info.setVerticalSpacing(14)
        grid_info.addWidget(self._crear_campo_detalle("CÃ³digo", self._barrio.codigo, "barcode.svg"), 0, 0)
        grid_info.addWidget(self._crear_campo_detalle("Estado", self._barrio.estado.title(), "circle-check.svg"), 0, 1)
        grid_info.addWidget(
            self._crear_campo_detalle("Creado", self._fecha_creacion, "calendar-plus.svg"),
            1,
            0,
        )
        grid_info.addWidget(
            self._crear_campo_detalle("Ãšltima actualizaciÃ³n", self._fecha_actualizada, "calendar-time.svg"),
            1,
            1,
        )

        encabezado_metricas = self._crear_encabezado_seccion_detalle(
            "Cobertura operativa",
            "Resume la cantidad de abonados y casas relacionadas con el barrio.",
        )
        fila_metricas = QHBoxLayout()
        fila_metricas.setSpacing(12)
        fila_metricas.addWidget(
            self._crear_tarjeta_detalle("Abonados", str(self._barrio.total_abonados), "users.svg"),
            1,
        )
        fila_metricas.addWidget(
            self._crear_tarjeta_detalle("Casas", str(self._barrio.total_casas), "home.svg"),
            1,
        )

        observaciones = self._crear_campo_detalle(
            "Observaciones",
            self._barrio.observaciones or "Sin observaciones registradas.",
            "notes.svg",
        )
        observaciones.setObjectName("campoDetalleBarrioAmplio")

        fila_acciones = QHBoxLayout()
        fila_acciones.setSpacing(10)
        variante_cerrar = resolver_variante_boton_modal("Cerrar", "neutro")
        variante_ver = resolver_variante_boton_modal("Ver detalle", "informacion")
        boton_cerrar = BotonAccionContextual(
            "Cerrar",
            icono="x.svg",
            variante=variante_cerrar,
            centrado=True,
            mostrar_icono=True,
        )
        boton_ver_abonados = BotonAccionContextual(
            "Ver abonados",
            icono="users.svg",
            variante=variante_ver,
            centrado=True,
            mostrar_icono=True,
        )
        boton_ver_casas = BotonAccionContextual(
            "Ver casas",
            icono="home.svg",
            variante=variante_ver,
            centrado=True,
            mostrar_icono=True,
        )
        boton_editar = BotonAccionContextual(
            "Editar",
            icono="edit.svg",
            variante="edicion",
            centrado=True,
            mostrar_icono=True,
        )
        boton_cerrar.setMinimumWidth(124)
        boton_ver_abonados.setMinimumWidth(140)
        boton_ver_casas.setMinimumWidth(132)
        boton_editar.setMinimumWidth(124)

        boton_cerrar.clicked.connect(self.reject)
        boton_ver_abonados.clicked.connect(self._abrir_abonados)
        boton_ver_casas.clicked.connect(self._abrir_casas)
        boton_editar.clicked.connect(self._solicitar_edicion)

        fila_acciones.addWidget(boton_cerrar)
        fila_acciones.addStretch(1)
        fila_acciones.addWidget(boton_ver_abonados)
        fila_acciones.addWidget(boton_ver_casas)
        fila_acciones.addWidget(boton_editar)

        panel_detalle_layout.addLayout(fila_superior)
        panel_detalle_layout.addWidget(
            self._crear_bloque_seccion_detalle(encabezado_contexto, grid_info)
        )
        panel_detalle_layout.addWidget(
            self._crear_bloque_seccion_detalle(encabezado_metricas, fila_metricas)
        )
        panel_detalle_layout.addWidget(
            self._crear_bloque_seccion_detalle(
                self._crear_encabezado_seccion_detalle(
                    "Observaciones",
                    "Notas administrativas o contexto adicional del barrio.",
                ),
                [observaciones],
            )
        )
        layout_scroll.addWidget(panel_detalle)
        scroll.setWidget(contenedor_scroll)

        self.layout_cabecera.addWidget(titulo)
        self.layout_cabecera.addWidget(descripcion)
        self.layout_cuerpo.addWidget(scroll)
        self.layout_pie.addLayout(fila_acciones)
        self._aplicar_estilos()

    def _crear_encabezado_seccion_detalle(self, titulo: str, descripcion: str) -> QWidget:
        bloque = QWidget()
        layout = QVBoxLayout(bloque)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        label_titulo = QLabel(titulo)
        label_titulo.setObjectName("tituloSeccionDetalleBarrio")
        label_descripcion = QLabel(descripcion)
        label_descripcion.setObjectName("descripcionSeccionDetalleBarrio")
        label_descripcion.setWordWrap(True)
        layout.addWidget(label_titulo)
        layout.addWidget(label_descripcion)
        return bloque

    def _crear_bloque_seccion_detalle(
        self,
        encabezado: QWidget,
        contenido: QGridLayout | QHBoxLayout | list[QWidget],
    ) -> QFrame:
        bloque = QFrame()
        bloque.setObjectName("seccionDetalleBarrio")
        layout = QVBoxLayout(bloque)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)
        layout.addWidget(encabezado)
        if isinstance(contenido, list):
            for widget in contenido:
                layout.addWidget(widget)
        else:
            layout.addLayout(contenido)
        return bloque

    def _crear_campo_detalle(self, etiqueta: str, valor: str, icono: str | None = None) -> QFrame:
        tarjeta = QFrame()
        tarjeta.setObjectName("campoDetalleBarrio")
        layout = QHBoxLayout(tarjeta)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)

        if icono:
            label_icono = QLabel("")
            label_icono.setObjectName("iconoCampoDetalleBarrio")
            label_icono.setFixedSize(34, 34)
            label_icono.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label_icono.setPixmap(
                obtener_icono_tabler_coloreado(icono, str(self._paleta_tema["modal_icono_campo"]), tamano=18).pixmap(18, 18)
            )
            layout.addWidget(label_icono, alignment=Qt.AlignmentFlag.AlignTop)

        bloque_texto = QVBoxLayout()
        bloque_texto.setContentsMargins(0, 0, 0, 0)
        bloque_texto.setSpacing(5)

        label_etiqueta = QLabel(etiqueta)
        label_etiqueta.setObjectName("etiquetaDetalleBarrio")
        label_valor = QLabel(valor)
        label_valor.setObjectName("valorDetalleBarrio")
        label_valor.setWordWrap(True)

        bloque_texto.addWidget(label_etiqueta)
        bloque_texto.addWidget(label_valor)
        layout.addLayout(bloque_texto, 1)
        return tarjeta

    def _crear_tarjeta_detalle(self, titulo: str, valor: str, icono: str | None = None) -> QFrame:
        tarjeta = QFrame()
        tarjeta.setObjectName("tarjetaMiniDetalleBarrio")
        layout = QHBoxLayout(tarjeta)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)

        if icono:
            label_icono = QLabel("")
            label_icono.setObjectName("iconoCampoDetalleBarrio")
            label_icono.setFixedSize(38, 38)
            label_icono.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label_icono.setPixmap(
                obtener_icono_tabler_coloreado(icono, str(self._paleta_tema["icono_tarjeta_info"]), tamano=19).pixmap(19, 19)
            )
            layout.addWidget(label_icono, alignment=Qt.AlignmentFlag.AlignTop)

        bloque_texto = QVBoxLayout()
        bloque_texto.setContentsMargins(0, 0, 0, 0)
        bloque_texto.setSpacing(4)

        label_titulo = QLabel(titulo)
        label_titulo.setObjectName("etiquetaDetalleBarrio")
        label_valor = QLabel(valor)
        label_valor.setObjectName("valorTarjetaMiniDetalle")
        bloque_texto.addWidget(label_titulo)
        bloque_texto.addWidget(label_valor)
        layout.addLayout(bloque_texto, 1)
        return tarjeta

    def _crear_boton_copiar_id(self, identificador: int | None) -> QToolButton:
        boton = QToolButton()
        boton.setObjectName("botonCopiarIdDetalle")
        boton.setText("COPIAR")
        boton.setProperty("copiado", False)
        boton.setCursor(Qt.CursorShape.PointingHandCursor)
        boton.setToolTip(f"Copiar ID interno: {int(identificador or 0)}")
        boton.setAutoRaise(False)
        boton.setEnabled(bool(identificador))
        boton.clicked.connect(
            lambda checked=False, valor=int(identificador or 0), control=boton: self._copiar_identificador(valor, control)
        )
        return boton

    def _copiar_identificador(self, identificador: int, boton: QToolButton) -> None:
        QApplication.clipboard().setText(str(identificador))
        boton.setText("OK")
        boton.setProperty("copiado", True)
        boton.style().unpolish(boton)
        boton.style().polish(boton)
        boton.setToolTip(f"ID copiado: {identificador}")
        QTimer.singleShot(900, lambda: self._restaurar_boton_copiar_id(boton, identificador))

    @staticmethod
    def _restaurar_boton_copiar_id(boton: QToolButton, identificador: int) -> None:
        boton.setText("COPIAR")
        boton.setProperty("copiado", False)
        boton.style().unpolish(boton)
        boton.style().polish(boton)
        boton.setToolTip(f"Copiar ID interno: {identificador}")

    def _abrir_abonados(self) -> None:
        self._accion_resultado = "ver_abonados"
        self.accept()

    def _abrir_casas(self) -> None:
        self._accion_resultado = "ver_casas"
        self.accept()

    def _solicitar_edicion(self) -> None:
        self._accion_resultado = "editar"
        self.accept()

    def _aplicar_estilos(self) -> None:
        self.setStyleSheet(
            self.styleSheet()
            + f"""
            QScrollArea#scrollDetalleBarrio,
            QWidget#contenedorScrollDetalleBarrio {{
                background: transparent;
                border: none;
            }}
            """
            + obtener_estilo_detalle_sigqua(self._nombre_tema)
        )
        return

        radio = RADIO_TARJETA_DIALOGO
        paleta = self._paleta_tema
        self.setStyleSheet(
            self.styleSheet()
            + f"""
            QScrollArea#scrollDetalleBarrio,
            QWidget#contenedorScrollDetalleBarrio {{
                background: transparent;
                border: none;
            }}
            QFrame#panelContenidoDetalleBarrio {{
                background: {self._color_fondo_dialogo};
                border: 1px solid {paleta["borde_principal"]};
                border-radius: {radio}px;
            }}
            QFrame#seccionDetalleBarrio {{
                background: {paleta["fondo_superficie"]};
                border: 1px solid {paleta["borde_principal"]};
                border-radius: {radio}px;
            }}
            QFrame#campoDetalleBarrio,
            QFrame#campoDetalleBarrioAmplio,
            QFrame#tarjetaMiniDetalleBarrio {{
                background: {paleta["fondo_superficie_suave"]};
                border: 1px solid {paleta["borde_suave"]};
                border-radius: {radio}px;
            }}
            QLabel#iconoCampoDetalleBarrio {{
                background: {paleta["fondo_superficie_muy_suave"]};
                border: 1px solid {paleta["borde_suave"]};
                border-radius: {radio}px;
            }}
            QLabel#tituloSeccionDetalleBarrio {{
                color: {paleta["texto_principal"]};
                font-size: 14px;
                font-weight: 800;
            }}
            QLabel#descripcionSeccionDetalleBarrio {{
                color: {paleta["texto_suave"]};
                font-size: 11px;
                font-weight: 600;
            }}
            QLabel#codigoBarrioDetalle {{
                color: {paleta["icono_tarjeta_info"]};
                font-size: 12px;
                font-weight: 800;
                letter-spacing: 0.08em;
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
            QLabel#nombreBarrioDetalle {{
                color: {paleta["texto_principal"]};
                font-size: 19px;
                font-weight: 900;
            }}
            QLabel#badgeDetalleBarrio {{
                border-radius: {radio}px;
                padding: 6px 10px;
                font-size: 12px;
                font-weight: 800;
                color: {paleta["texto_badge"]};
                background: {paleta["fondo_badge"]};
                border: 1px solid {paleta["borde_suave"]};
            }}
            QLabel#badgeDetalleBarrio[activo="true"] {{
                color: {paleta["texto_badge_activo"]};
                background: {paleta["fondo_badge_activo"]};
                border-color: {paleta["borde_badge_activo"]};
            }}
            QLabel#etiquetaDetalleBarrio {{
                color: {paleta["texto_muted"]};
                font-size: 11px;
                font-weight: 700;
            }}
            QLabel#valorDetalleBarrio {{
                color: {paleta["texto_input"]};
                font-size: 12px;
                font-weight: 700;
            }}
            QLabel#valorTarjetaMiniDetalle {{
                color: {paleta["texto_principal"]};
                font-size: 20px;
                font-weight: 900;
            }}
            """
        )


class DialogoConfirmacionEstadoBarrio(DialogoConfirmacionSigqua):
    """Modal de confirmacion para activar o inactivar barrios."""

    def __init__(self, barrio: Barrio, parent: QWidget | None = None) -> None:
        self._barrio = barrio
        nuevo_estado = "inactivar" if self._barrio.estado == "ACTIVO" else "activar"
        super().__init__(
            titulo="Confirmar cambio de estado",
            descripcion=(
                f"Estas a punto de {nuevo_estado} el barrio seleccionado. "
                "Verifica los datos antes de confirmar."
            ),
            detalles=(
                ("Barrio", self._barrio.nombre),
                ("CÃ³digo", self._barrio.codigo),
                ("Estado actual", self._barrio.estado.title()),
                ("AcciÃ³n", nuevo_estado.title()),
            ),
            texto_confirmar=nuevo_estado.title(),
            icono="alert-triangle.svg",
            variante_confirmar="salida" if nuevo_estado == "inactivar" else "primario",
            parent=parent,
        )


class VistaBarrios(QWidget):
    """Pantalla principal del modulo de barrios."""

    RADIO_PANEL_TABLA = 18
    ANCHO_COLUMNA_ACCIONES = 234
    DURACION_MENSAJE_MS = 5200

    filtro_texto_cambiado = Signal(str)
    filtro_rapido_cambiado = Signal(str)
    pagina_cambiada = Signal(int)
    exportar_solicitado = Signal()
    nuevo_barrio_solicitado = Signal()
    detalle_barrio_solicitado = Signal(int)
    editar_barrio_solicitado = Signal(int)
    cambio_estado_solicitado = Signal(int)
    ver_abonados_barrio_solicitado = Signal(int)
    ver_casas_barrio_solicitado = Signal(int)

    def __init__(self) -> None:
        super().__init__()
        self._tema_actual = TEMA_SIGQUA_PREDETERMINADO
        self._paleta_tema = obtener_paleta_tema(self._tema_actual)
        self._pagina_actual = 1
        self._total_paginas = 1
        self._temporizador_mensaje = QTimer(self)
        self._temporizador_mensaje.setSingleShot(True)
        self._temporizador_mensaje.timeout.connect(self._ocultar_mensaje)
        self._construir_ui()
        self._aplicar_estilos()

    def aplicar_tema(self, nombre_tema: str) -> None:
        self._tema_actual = resolver_nombre_tema(nombre_tema)
        self._paleta_tema = obtener_paleta_tema(self._tema_actual)
        self._aplicar_estilos()
        for boton in self.findChildren(QPushButton):
            if boton.objectName() == "botonOperativo":
                aplicar_estilo_boton_operativo(boton, principal=False)
            elif boton.objectName() == "botonOperativoPrimario":
                aplicar_estilo_boton_operativo(boton, principal=True)
        for boton_icono in self.findChildren(BotonIconoFilaBarrio):
            boton_icono.aplicar_tema(self._tema_actual)

    def mostrar_resumen(self, resumen: ResumenBarrios) -> None:
        self._tarjeta_total.actualizar(
            "Total de barrios",
            str(resumen.total_barrios),
            "Cobertura territorial registrada.",
        )
        self._tarjeta_activos.actualizar(
            "Barrios activos",
            str(resumen.barrios_activos),
            "Disponibles para operaciÃ³n diaria.",
        )
        self._tarjeta_con_abonados.actualizar(
            "Barrios con abonados",
            str(resumen.barrios_con_abonados),
            "Zonas con relacion operativa vigente.",
        )
        detalle_destacado = (
            f"{resumen.cantidad_maxima_abonados} abonados registrados"
            if resumen.cantidad_maxima_abonados > 0
            else "Sin abonados vinculados"
        )
        self._tarjeta_destacado.actualizar(
            "Barrio con mas abonados",
            resumen.barrio_con_mas_abonados,
            detalle_destacado,
        )

    def mostrar_barrios(
        self,
        pagina: PaginaBarrios,
        formateador_fecha: Callable[[str], str],
    ) -> None:
        self._pagina_actual = pagina.pagina_actual
        self._total_paginas = pagina.total_paginas
        self._tabla.setRowCount(0)

        for barrio in pagina.items:
            fila = self._tabla.rowCount()
            self._tabla.insertRow(fila)
            self._tabla.setItem(fila, 0, crear_item_tabla(barrio.codigo))
            self._tabla.setItem(fila, 1, crear_item_tabla(barrio.nombre))
            self._tabla.setItem(fila, 2, crear_item_tabla(barrio.total_abonados))
            self._tabla.setItem(fila, 3, crear_item_tabla(barrio.total_casas))
            self._tabla.setCellWidget(fila, 4, self._crear_badge_estado(barrio.estado))
            self._tabla.setItem(fila, 5, crear_item_tabla(formateador_fecha(barrio.actualizado_en)))
            self._tabla.setCellWidget(fila, 6, self._crear_acciones_fila(barrio))

        self._tabla.resizeRowsToContents()
        self._tabla.setColumnWidth(6, max(self._tabla.columnWidth(6), self.ANCHO_COLUMNA_ACCIONES))
        self._actualizar_estado_vacio(pagina.total_registros == 0)
        self._label_paginacion.setText(
            f"Mostrando {pagina.indice_inicio}-{pagina.indice_fin} de {pagina.total_registros} registros"
        )
        self._label_numero_pagina.setText(
            f"PÃ¡gina {self._pagina_actual} de {self._total_paginas}"
        )
        self._boton_pagina_anterior.setEnabled(self._pagina_actual > 1)
        self._boton_pagina_siguiente.setEnabled(self._pagina_actual < self._total_paginas)

    def mostrar_mensaje(self, mensaje: str, es_error: bool = False) -> None:
        self._temporizador_mensaje.stop()
        self._mensaje.setText(mensaje)
        self._mensaje.setVisible(bool(mensaje))
        self._mensaje.setProperty("error", es_error)
        self._mensaje.style().unpolish(self._mensaje)
        self._mensaje.style().polish(self._mensaje)
        if mensaje:
            self._temporizador_mensaje.start(self.DURACION_MENSAJE_MS)

    def _ocultar_mensaje(self) -> None:
        self._mensaje.clear()
        self._mensaje.setVisible(False)

    def solicitar_datos_barrio(self, barrio: Barrio | None = None) -> FormularioBarrio | None:
        dialogo = DialogoFormularioBarrio(barrio=barrio, parent=self)
        if dialogo.exec() != QDialog.DialogCode.Accepted:
            return None
        return dialogo.obtener_formulario()

    def mostrar_detalle_barrio(
        self,
        barrio: Barrio,
        fecha_creacion: str,
        fecha_actualizada: str,
    ) -> str:
        dialogo = DialogoDetalleBarrio(
            barrio=barrio,
            fecha_creacion=fecha_creacion,
            fecha_actualizada=fecha_actualizada,
            parent=self,
        )
        dialogo.exec()
        return dialogo.accion_resultado

    def confirmar_cambio_estado_barrio(self, barrio: Barrio) -> bool:
        dialogo = DialogoConfirmacionEstadoBarrio(barrio=barrio, parent=self)
        return dialogo.exec() == QDialog.DialogCode.Accepted

    def solicitar_ruta_exportacion(self) -> str:
        ruta, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar barrios",
            "barrios.csv",
            "Archivos CSV (*.csv)",
        )
        return ruta

    def _construir_ui(self) -> None:
        self.setObjectName("vistaBarrios")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 6)
        layout.setSpacing(12)

        encabezado = QHBoxLayout()
        encabezado.setSpacing(10)

        fila_acciones = QHBoxLayout()
        fila_acciones.setSpacing(8)
        fila_acciones.addStretch(1)
        boton_exportar = crear_boton_operativo("Exportar")
        boton_nuevo = crear_boton_operativo("Nuevo barrio", principal=True)
        boton_exportar.clicked.connect(self.exportar_solicitado.emit)
        boton_nuevo.clicked.connect(self.nuevo_barrio_solicitado.emit)
        fila_acciones.addWidget(boton_exportar)
        fila_acciones.addWidget(boton_nuevo)

        encabezado.addStretch(1)
        encabezado.addLayout(fila_acciones)

        self._mensaje = QLabel("")
        self._mensaje.setObjectName("mensajeBarrios")
        self._mensaje.setVisible(False)
        self._mensaje.setWordWrap(True)

        fila_tarjetas = QGridLayout()
        fila_tarjetas.setHorizontalSpacing(10)
        fila_tarjetas.setVerticalSpacing(10)
        self._tarjeta_total = TarjetaResumenBarrio("map-pin.svg", "#75C7F0")
        self._tarjeta_activos = TarjetaResumenBarrio("circle-check.svg", "#8de8c7")
        self._tarjeta_con_abonados = TarjetaResumenBarrio("user.svg", "#f7cc7a")
        self._tarjeta_destacado = TarjetaResumenBarrio("home.svg", "#37D399")
        fila_tarjetas.addWidget(self._tarjeta_total, 0, 0)
        fila_tarjetas.addWidget(self._tarjeta_activos, 0, 1)
        fila_tarjetas.addWidget(self._tarjeta_con_abonados, 0, 2)
        fila_tarjetas.addWidget(self._tarjeta_destacado, 0, 3)

        panel_filtros = QFrame()
        panel_filtros.setObjectName("panelOperativoBarrios")
        layout_filtros = QVBoxLayout(panel_filtros)
        layout_filtros.setContentsMargins(14, 14, 14, 14)
        layout_filtros.setSpacing(10)

        self._campo_busqueda = QLineEdit()
        self._campo_busqueda.setPlaceholderText("Buscar barrio")
        self._campo_busqueda.textChanged.connect(self.filtro_texto_cambiado.emit)

        fila_chips = QHBoxLayout()
        fila_chips.setSpacing(6)
        self._grupo_filtros = QButtonGroup(self)
        self._grupo_filtros.setExclusive(True)
        self._botones_filtros: dict[str, QPushButton] = {}
        for codigo, texto in (
            (FILTRO_BARRIOS_TODOS, "Todos"),
            (FILTRO_BARRIOS_ACTIVOS, "Activos"),
            (FILTRO_BARRIOS_INACTIVOS, "Inactivos"),
            (FILTRO_BARRIOS_CON_ABONADOS, "Con abonados"),
            (FILTRO_BARRIOS_SIN_ABONADOS, "Sin abonados"),
        ):
            boton = QPushButton(texto)
            boton.setObjectName("chipFiltroBarrio")
            boton.setCheckable(True)
            boton.setCursor(Qt.CursorShape.PointingHandCursor)
            boton.clicked.connect(
                lambda checked=False, valor=codigo: self.filtro_rapido_cambiado.emit(valor)
            )
            self._grupo_filtros.addButton(boton)
            self._botones_filtros[codigo] = boton
            fila_chips.addWidget(boton)
        self._botones_filtros[FILTRO_BARRIOS_TODOS].setChecked(True)
        fila_chips.addStretch(1)

        layout_filtros.addWidget(self._campo_busqueda)
        layout_filtros.addLayout(fila_chips)

        panel_tabla = QFrame()
        panel_tabla.setObjectName("panelTablaBarrios")
        layout_tabla = QVBoxLayout(panel_tabla)
        layout_tabla.setContentsMargins(14, 14, 14, 14)
        layout_tabla.setSpacing(10)

        self._tabla = QTableWidget(0, 7)
        self._tabla.setObjectName("tablaBarrios")
        configurar_tabla_operativa(
            self._tabla,
            [
                "CÃ³digo",
                "Barrio",
                "Abonados",
                "Casas",
                "Estado",
                "Ãšltima actualizaciÃ³n",
                "Acciones",
            ],
        )
        self._tabla.horizontalHeader().setStretchLastSection(False)
        self._tabla.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self._tabla.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self._tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._tabla.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self._tabla.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self._tabla.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self._tabla.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self._tabla.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Interactive)
        self._tabla.setColumnWidth(6, self.ANCHO_COLUMNA_ACCIONES)
        self._tabla.verticalHeader().setDefaultSectionSize(58)
        self._tabla.setAlternatingRowColors(True)
        self._tabla.setFrameShape(QFrame.Shape.NoFrame)
        self._tabla.setViewportMargins(0, 0, 0, self.RADIO_PANEL_TABLA)
        self._tabla.viewport().setObjectName("viewportTablaBarrios")
        self._tabla.viewport().setAutoFillBackground(False)

        self._estado_vacio = QLabel("No hay barrios que coincidan con los filtros actuales.")
        self._estado_vacio.setObjectName("estadoVacioBarrios")
        self._estado_vacio.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._estado_vacio.setVisible(False)

        pie_tabla = QHBoxLayout()
        pie_tabla.setSpacing(8)
        self._label_paginacion = QLabel("Mostrando 0-0 de 0 registros")
        self._label_paginacion.setObjectName("textoPieBarrios")
        pie_tabla.addWidget(self._label_paginacion)
        pie_tabla.addStretch(1)

        self._boton_pagina_anterior = crear_boton_operativo("Anterior")
        self._boton_pagina_siguiente = crear_boton_operativo("Siguiente")
        self._boton_pagina_anterior.clicked.connect(
            lambda: self.pagina_cambiada.emit(max(1, self._pagina_actual - 1))
        )
        self._boton_pagina_siguiente.clicked.connect(
            lambda: self.pagina_cambiada.emit(self._pagina_actual + 1)
        )
        self._label_numero_pagina = QLabel("PÃ¡gina 1 de 1")
        self._label_numero_pagina.setObjectName("textoPieBarrios")
        pie_tabla.addWidget(self._boton_pagina_anterior)
        pie_tabla.addWidget(self._label_numero_pagina)
        pie_tabla.addWidget(self._boton_pagina_siguiente)

        layout_tabla.addWidget(self._tabla)
        layout_tabla.addWidget(self._estado_vacio)
        layout_tabla.addLayout(pie_tabla)

        layout.addLayout(encabezado)
        layout.addWidget(self._mensaje)
        layout.addLayout(fila_tarjetas)
        layout.addWidget(panel_filtros)
        layout.addWidget(panel_tabla, 1)

    def _crear_badge_estado(self, estado: str) -> QWidget:
        contenedor = QWidget()
        layout = QHBoxLayout(contenedor)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        badge = QLabel(estado.title())
        badge.setObjectName("badgeEstadoBarrio")
        badge.setProperty("activo", estado == "ACTIVO")
        badge.style().unpolish(badge)
        badge.style().polish(badge)
        layout.addWidget(badge, alignment=Qt.AlignmentFlag.AlignCenter)
        return contenedor

    def _crear_acciones_fila(self, barrio: Barrio) -> QWidget:
        contenedor = QWidget()
        contenedor.setObjectName("contenedorAccionesBarrio")
        contenedor.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        contenedor.setMinimumWidth(self.ANCHO_COLUMNA_ACCIONES)
        contenedor.setMinimumHeight(58)
        layout = QHBoxLayout(contenedor)
        layout.setContentsMargins(0, 0, 0, 14)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        boton_accion_detalle = BotonIconoFilaBarrio(
            "eye.svg",
            "#4fa3ff",
            "Ver informacion",
        )
        boton_ver_abonados = BotonIconoFilaBarrio(
            "user.svg",
            "#8de8c7",
            "Ver abonados",
        )
        boton_ver_casas = BotonIconoFilaBarrio(
            "home.svg",
            "#92B6CC",
            "Ver casas",
        )
        boton_accion_editar = BotonIconoFilaBarrio(
            "key.svg",
            "#4fa3ff",
            "Editar",
        )
        accion_desactiva = barrio.estado == "ACTIVO"
        boton_accion_estado = BotonIconoFilaBarrio(
            "lock.svg" if accion_desactiva else "circle-check.svg",
            "#ff625c" if accion_desactiva else "#4fa3ff",
            "Desactivar" if accion_desactiva else "Activar",
        )

        boton_accion_detalle.clicked.connect(
            lambda checked=False, identificador=barrio.identificador: self.detalle_barrio_solicitado.emit(
                int(identificador or 0)
            )
        )
        boton_ver_abonados.clicked.connect(
            lambda checked=False, identificador=barrio.identificador: self.ver_abonados_barrio_solicitado.emit(
                int(identificador or 0)
            )
        )
        boton_ver_casas.clicked.connect(
            lambda checked=False, identificador=barrio.identificador: self.ver_casas_barrio_solicitado.emit(
                int(identificador or 0)
            )
        )
        boton_accion_editar.clicked.connect(
            lambda checked=False, identificador=barrio.identificador: self.editar_barrio_solicitado.emit(
                int(identificador or 0)
            )
        )
        boton_accion_estado.clicked.connect(
            lambda checked=False, identificador=barrio.identificador: self.cambio_estado_solicitado.emit(
                int(identificador or 0)
            )
        )

        layout.addWidget(boton_accion_detalle)
        layout.addWidget(boton_ver_abonados)
        layout.addWidget(boton_ver_casas)
        layout.addWidget(boton_accion_editar)
        layout.addWidget(boton_accion_estado)
        return contenedor

    def aplicar_busqueda_externa(self, texto: str) -> None:
        texto_normalizado = texto.strip()
        if self._campo_busqueda.text() != texto_normalizado:
            self._campo_busqueda.setText(texto_normalizado)
            return
        self.filtro_texto_cambiado.emit(texto_normalizado)

    def _actualizar_estado_vacio(self, sin_datos: bool) -> None:
        self._estado_vacio.setVisible(sin_datos)
        self._tabla.setVisible(not sin_datos)

    def _aplicar_estilos(self) -> None:
        radio_panel_tabla = self.RADIO_PANEL_TABLA
        fondo_header_destacado = obtener_fondo_header_destacado(self._tema_actual)
        self.setStyleSheet(
            """
            QWidget#vistaBarrios {
                background: transparent;
            }
            QLabel#tituloModulo {
                color: #75C7F0;
                font-size: 19px;
                font-weight: 900;
            }
            QLabel#descripcionModulo,
            QLabel#textoPieBarrios,
            QLabel#detalleTarjetaResumen {
                color: #C5DDEE;
                font-size: 11px;
                font-weight: 600;
            }
            QLabel#mensajeBarrios {
                color: #DDFBF0;
                font-size: 12px;
                font-weight: 700;
                padding: 8px 10px;
                border-radius: 12px;
                background-color: rgba(55, 211, 153, 0.16);
                border: 1px solid rgba(55, 211, 153, 0.26);
            }
            QLabel#mensajeBarrios[error="true"] {
                color: #FFE3E3;
                background-color: rgba(242, 116, 116, 0.15);
                border: 1px solid rgba(242, 116, 116, 0.28);
            }
            QFrame#panelOperativoBarrios,
            QFrame#tarjetaResumenBarrios {
                background: """
            + fondo_header_destacado
            + """;
                border: 1px solid rgba(126, 167, 196, 0.48);
                border-radius: 18px;
            }
            QFrame#panelTablaBarrios {
                background: """
            + fondo_header_destacado
            + """;
                border: 1px solid rgba(126, 167, 196, 0.48);
                border-radius: """
            + str(radio_panel_tabla)
            + """px;
            }
            QTableWidget#tablaBarrios {
                background: """
            + self._paleta_tema["fondo_tabla_cuerpo"]
            + """;
                background-clip: padding;
                border: none;
                border-radius: """
            + str(radio_panel_tabla)
            + """px;
                padding: 0 0 """
            + str(radio_panel_tabla)
            + """px 0;
            }
            QWidget#viewportTablaBarrios {
                background: transparent;
                border: none;
                border-bottom-left-radius: """
            + str(radio_panel_tabla)
            + """px;
                border-bottom-right-radius: """
            + str(radio_panel_tabla)
            + """px;
            }
            QTableWidget#tablaBarrios QHeaderView::section:first {
                border-top-left-radius: """
            + str(radio_panel_tabla)
            + """px;
            }
            QTableWidget#tablaBarrios QHeaderView::section {
                background: """
            + self._paleta_tema["fondo_tabla_header_destacado"]
            + """;
                color: #75C7F0;
                border: none;
                border-right: 1px solid """
            + self._paleta_tema["borde_tabla"]
            + """;
                border-bottom: 1px solid """
            + self._paleta_tema["borde_tabla"]
            + """;
                padding: 10px 12px;
                font-size: 12px;
                font-weight: 800;
            }
            QTableWidget#tablaBarrios QHeaderView::section:last {
                border-top-right-radius: """
            + str(radio_panel_tabla)
            + """px;
            }
            QTableWidget#tablaBarrios::item {
                padding: 9px 12px;
                border-bottom: 1px solid """
            + self._paleta_tema["borde_tabla"]
            + """;
                background: """
            + self._paleta_tema["fondo_tabla_fila"]
            + """;
            }
            QTableWidget#tablaBarrios::item:alternate {
                background: """
            + self._paleta_tema["fondo_tabla_fila_alterna"]
            + """;
            }
            QTableWidget#tablaBarrios::item:selected {
                background: """
            + self._paleta_tema["fondo_tabla_seleccion"]
            + """;
            }
            QLabel#iconoTarjetaResumen {
                background: rgba(13, 42, 69, 0.78);
                border: 1px solid rgba(126, 167, 196, 0.30);
                border-radius: 12px;
            }
            QLabel#tituloTarjetaResumen {
                color: #C5DDEE;
                font-size: 11px;
                font-weight: 700;
            }
            QLabel#valorTarjetaResumen {
                color: #75C7F0;
                font-size: 20px;
                font-weight: 900;
            }
            QLineEdit {
                min-height: 36px;
                border: 1px solid rgba(126, 167, 196, 0.55);
                border-radius: 12px;
                background: rgba(8, 34, 56, 0.98);
                color: #75C7F0;
                padding: 0 10px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: rgba(117, 199, 240, 0.55);
                background: rgba(126, 167, 196, 0.48);
            }
            QPushButton#chipFiltroBarrio {
                min-height: 30px;
                border-radius: 11px;
                padding: 0 12px;
                background: rgba(13, 42, 69, 0.88);
                border: 1px solid rgba(126, 167, 196, 0.30);
                color: #F4FAFF;
                font-size: 11px;
                font-weight: 700;
            }
            QPushButton#chipFiltroBarrio:hover {
                background: rgba(126, 167, 196, 0.30);
            }
            QPushButton#chipFiltroBarrio:checked {
                color: #75C7F0;
                background: #49A9DC;
                border-color: rgba(126, 167, 196, 0.55);
            }
            QLabel#badgeEstadoBarrio {
                border-radius: 11px;
                padding: 6px 10px;
                font-size: 11px;
                font-weight: 800;
                color: #C5DDEE;
                background: rgba(142, 168, 188, 0.22);
                border: 1px solid rgba(126, 167, 196, 0.30);
            }
            QLabel#badgeEstadoBarrio[activo="true"] {
                color: #DDFBF0;
                background: rgba(55, 211, 153, 0.22);
                border-color: rgba(55, 211, 153, 0.26);
            }
            QWidget#contenedorAccionesBarrio {
                background: transparent;
            }
            QToolButton#botonIconoFilaBarrio {
                background: transparent;
                border: none;
                border-radius: 8px;
                padding: 0px;
                margin: 0px;
            }
            QToolButton#botonIconoFilaBarrio:hover {
                background: transparent;
                border: none;
            }
            QLabel#estadoVacioBarrios {
                color: #C5DDEE;
                font-size: 12px;
                font-weight: 700;
                padding: 20px 14px;
            }
            QLabel {
                color: #75C7F0;
            }
            """
        )


