"""Vista PySide6 del modulo de reportes administrativos."""

from __future__ import annotations

from PySide6.QtCore import QDate, Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTableWidget,
    QVBoxLayout,
    QWidget,
)

from comun.ui import (
    CampoBusquedaSeleccionSigqua,
    ContenedorTarjetasResumenOperativo,
    TarjetaResumenOperativa,
    configurar_tabla_operativa,
    crear_boton_operativo,
    crear_item_tabla,
    obtener_icono_tabler_coloreado,
)
from comun.ui.temas import (
    TEMA_SIGQUA_PREDETERMINADO,
    obtener_fondo_header_destacado,
    obtener_paleta_tema,
    resolver_nombre_tema,
)
from modulos.reportes.entidades import (
    EstadoReportes,
    FiltroReporte,
    REPORTE_DEUDA_ABONADOS_ESTADO,
    TablaReporte,
    TarjetaReporte,
    TIPO_FILTRO_BUSQUEDA,
)


class TarjetaSeleccionReporte(QPushButton):
    """Tarjeta visual para seleccionar un reporte administrativo."""

    ALTURA = 164

    def __init__(self, tarjeta: TarjetaReporte, color_icono: str) -> None:
        super().__init__()
        self.codigo = tarjeta.codigo
        self._tarjeta = tarjeta
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setObjectName("tarjetaReporteAdmin")
        self.setMinimumHeight(self.ALTURA)
        self.setMaximumHeight(self.ALTURA)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(8)
        icono = QLabel()
        icono.setObjectName("iconoTarjetaReporte")
        icono.setFixedSize(38, 38)
        icono.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icono.setPixmap(obtener_icono_tabler_coloreado(tarjeta.icono, color_icono, tamano=20).pixmap(20, 20))
        titulo = QLabel(tarjeta.titulo)
        titulo.setObjectName("tituloTarjetaReporte")
        titulo.setWordWrap(True)
        titulo.setMinimumWidth(0)
        titulo.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        descripcion = QLabel(tarjeta.descripcion)
        descripcion.setObjectName("descripcionTarjetaReporte")
        descripcion.setWordWrap(True)
        descripcion.setMinimumWidth(0)
        descripcion.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        resumen = QLabel(tarjeta.resumen)
        resumen.setObjectName("resumenTarjetaReporte")
        resumen.setWordWrap(True)
        resumen.setMinimumWidth(0)
        resumen.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        layout.addWidget(icono, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(titulo)
        layout.addWidget(descripcion)
        layout.addStretch(1)
        layout.addWidget(resumen)


class VistaReportes(QWidget):
    """Catalogo visual y vista previa de reportes administrativos."""

    reporte_seleccionado = Signal(str)
    filtros_aplicados = Signal(str, object)
    exportar_solicitado = Signal(str, object)
    exportar_en_solicitado = Signal(str, object, str)
    DURACION_MENSAJE_MS = 10000

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("vistaReportes")
        self._tema_actual = TEMA_SIGQUA_PREDETERMINADO
        self._paleta = obtener_paleta_tema(self._tema_actual)
        self._tarjetas: dict[str, TarjetaSeleccionReporte] = {}
        self._filtros_widgets: dict[str, QWidget] = {}
        self._filtros_actuales: dict[str, str] = {}
        self._reporte_actual_codigo = REPORTE_DEUDA_ABONADOS_ESTADO
        self._tabla_actual: TablaReporte | None = None
        self._temporizador_mensaje = QTimer(self)
        self._temporizador_mensaje.setSingleShot(True)
        self._temporizador_mensaje.timeout.connect(lambda: self._mensaje.setVisible(False))
        self._construir_ui()
        self._aplicar_estilos()

    def mostrar_estado(self, estado: EstadoReportes) -> None:
        self._reporte_actual_codigo = estado.reporte_actual
        self._filtros_actuales = dict(estado.filtros_aplicados)
        self._mostrar_indicadores(estado)
        self._renderizar_catalogo(estado.catalogo)
        self._renderizar_filtros(estado.filtros_visibles)
        self._mostrar_tabla_actual(estado.tabla_actual)

    def mostrar_mensaje(self, mensaje: str, es_error: bool = False) -> None:
        self._mensaje.setText(mensaje)
        self._mensaje.setProperty("error", es_error)
        self._mensaje.style().unpolish(self._mensaje)
        self._mensaje.style().polish(self._mensaje)
        self._mensaje.setVisible(bool(mensaje))
        if mensaje:
            self._temporizador_mensaje.start(self.DURACION_MENSAJE_MS)

    def solicitar_ruta_exportacion(self, codigo_reporte: str) -> str:
        return QFileDialog.getExistingDirectory(
            self,
            "Guardar reporte en",
            "",
        )

    def establecer_exportacion_en_curso(self, en_curso: bool) -> None:
        self._boton_exportar.setEnabled(not en_curso)
        self._boton_guardar_en.setEnabled(not en_curso)

    def _construir_ui(self) -> None:
        layout_raiz = QVBoxLayout(self)
        layout_raiz.setContentsMargins(0, 0, 0, 0)
        layout_raiz.setSpacing(0)

        scroll = QScrollArea()
        scroll.setObjectName("scrollReportes")
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        contenido = QWidget()
        contenido.setObjectName("contenidoReportes")
        layout = QVBoxLayout(contenido)
        layout.setContentsMargins(6, 4, 6, 6)
        layout.setSpacing(12)

        self._mensaje = QLabel("")
        self._mensaje.setObjectName("mensajeReportes")
        self._mensaje.setVisible(False)
        layout.addWidget(self._mensaje)

        contenedor_indicadores = ContenedorTarjetasResumenOperativo()
        iconos_indicadores = ("chart-bar.svg", "users.svg", "home.svg", "receipt-2.svg", "alert-triangle.svg")
        colores_indicadores = ("#75C7F0", "#8de8c7", "#92B6CC", "#f7cc7a", "#F5B84B")
        self._indicadores: list[TarjetaResumenOperativa] = [
            TarjetaResumenOperativa(icono, color)
            for icono, color in zip(iconos_indicadores, colores_indicadores, strict=True)
        ]
        contenedor_indicadores.establecer_tarjetas(tuple(self._indicadores))
        layout.addWidget(contenedor_indicadores)

        titulo_selector = QLabel("Seleccione el tipo de reporte")
        titulo_selector.setObjectName("tituloSeccionReportes")
        layout.addWidget(titulo_selector)

        self._contenedor_tarjetas = QWidget()
        self._contenedor_tarjetas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._grilla_tarjetas = QGridLayout(self._contenedor_tarjetas)
        self._grilla_tarjetas.setContentsMargins(0, 0, 0, 0)
        self._grilla_tarjetas.setHorizontalSpacing(12)
        self._grilla_tarjetas.setVerticalSpacing(12)
        layout.addWidget(self._contenedor_tarjetas)

        self._panel_filtros = QFrame()
        self._panel_filtros.setObjectName("panelFiltrosReportes")
        self._panel_filtros.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        panel_filtros_layout = QVBoxLayout(self._panel_filtros)
        panel_filtros_layout.setContentsMargins(16, 16, 16, 16)
        panel_filtros_layout.setSpacing(12)
        self._titulo_preview = QLabel("Selecciona un reporte")
        self._titulo_preview.setObjectName("tituloReporte")
        self._descripcion_preview = QLabel("")
        self._descripcion_preview.setObjectName("descripcionReporte")
        self._descripcion_preview.setWordWrap(True)
        self._grilla_filtros = QGridLayout()
        self._grilla_filtros.setHorizontalSpacing(12)
        self._grilla_filtros.setVerticalSpacing(10)
        self._grilla_filtros.setColumnStretch(0, 1)
        self._grilla_filtros.setColumnStretch(1, 1)
        fila_acciones = QHBoxLayout()
        fila_acciones.addStretch(1)
        boton_aplicar = crear_boton_operativo("Aplicar filtros")
        boton_aplicar.clicked.connect(self._emitir_filtros)
        self._boton_guardar_en = crear_boton_operativo("Guardar en...")
        self._boton_guardar_en.clicked.connect(self._emitir_exportacion_en)
        self._boton_exportar = crear_boton_operativo("Generar PDF", principal=True)
        self._boton_exportar.clicked.connect(self._emitir_exportacion)
        fila_acciones.addWidget(self._boton_guardar_en)
        fila_acciones.addWidget(boton_aplicar)
        fila_acciones.addWidget(self._boton_exportar)
        panel_filtros_layout.addWidget(self._titulo_preview)
        panel_filtros_layout.addWidget(self._descripcion_preview)
        panel_filtros_layout.addLayout(self._grilla_filtros)
        panel_filtros_layout.addLayout(fila_acciones)
        layout.addWidget(self._panel_filtros)

        panel_tabla = QFrame()
        panel_tabla.setObjectName("panelTablaReportes")
        panel_tabla.setMinimumHeight(240)
        layout_tabla = QVBoxLayout(panel_tabla)
        layout_tabla.setContentsMargins(16, 16, 16, 16)
        self._tabla = QTableWidget()
        self._tabla.setObjectName("tablaOperativaOscura")
        self._tabla.setFrameShape(QFrame.Shape.NoFrame)
        self._tabla.setAlternatingRowColors(True)
        self._tabla.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._tabla.setViewportMargins(0, 0, 0, 18)
        self._tabla.viewport().setObjectName("viewportTablaReportes")
        self._tabla.viewport().setAutoFillBackground(False)
        layout_tabla.addWidget(self._tabla)
        layout.addWidget(panel_tabla)
        scroll.setWidget(contenido)
        layout_raiz.addWidget(scroll)

    def _renderizar_catalogo(self, catalogo: tuple[TarjetaReporte, ...]) -> None:
        while self._grilla_tarjetas.count():
            item = self._grilla_tarjetas.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self._tarjetas.clear()
        color_icono = str(self._paleta["texto_principal"])
        for indice, tarjeta in enumerate(catalogo):
            widget = TarjetaSeleccionReporte(tarjeta, color_icono)
            widget.clicked.connect(lambda checked=False, codigo=tarjeta.codigo: self.reporte_seleccionado.emit(codigo))
            widget.setChecked(tarjeta.codigo == self._reporte_actual_codigo)
            self._tarjetas[tarjeta.codigo] = widget
            self._grilla_tarjetas.addWidget(widget, indice // 4, indice % 4)
        filas = max(1, (len(catalogo) + 3) // 4)
        alto_tarjetas = (
            filas * TarjetaSeleccionReporte.ALTURA
            + max(0, filas - 1) * self._grilla_tarjetas.verticalSpacing()
        )
        self._contenedor_tarjetas.setMinimumHeight(alto_tarjetas)
        self._contenedor_tarjetas.setMaximumHeight(alto_tarjetas)

    def _renderizar_filtros(self, filtros: tuple[FiltroReporte, ...]) -> None:
        while self._grilla_filtros.count():
            item = self._grilla_filtros.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self._filtros_widgets.clear()
        for indice, filtro in enumerate(filtros):
            etiqueta = QLabel(filtro.etiqueta)
            etiqueta.setObjectName("labelFiltroReporte")
            widget = self._crear_widget_filtro(filtro)
            self._filtros_widgets[filtro.clave] = widget
            fila = (indice // 2) * 2
            columna = indice % 2
            self._grilla_filtros.addWidget(etiqueta, fila, columna)
            self._grilla_filtros.addWidget(widget, fila + 1, columna)

    def _crear_widget_filtro(self, filtro: FiltroReporte) -> QWidget:
        if filtro.tipo == TIPO_FILTRO_BUSQUEDA:
            campo = CampoBusquedaSeleccionSigqua(
                texto_sin_resultados=f"No se encontraron opciones para {filtro.etiqueta.lower()}",
                placeholder=f"Todos. Escribe para buscar {filtro.etiqueta.lower()}",
            )
            opciones = [
                (int(opcion.valor), opcion.etiqueta)
                for opcion in filtro.opciones
                if opcion.valor != "TODOS" and opcion.valor.isdigit()
            ]
            campo.establecer_opciones(opciones)
            if filtro.valor != "TODOS" and filtro.valor.isdigit():
                etiqueta = next(
                    (
                        opcion.etiqueta
                        for opcion in filtro.opciones
                        if opcion.valor == filtro.valor
                    ),
                    "",
                )
                campo.seleccionar_por_id(int(filtro.valor), etiqueta)
            return campo
        if filtro.tipo == "combo":
            combo = QComboBox()
            combo.setObjectName("campoFiltroReporte")
            for opcion in filtro.opciones:
                combo.addItem(opcion.etiqueta, opcion.valor)
            indice = combo.findData(filtro.valor)
            if indice >= 0:
                combo.setCurrentIndex(indice)
            return combo
        if filtro.tipo == "fecha":
            campo = QDateEdit()
            campo.setObjectName("campoFechaReporte")
            campo.setDisplayFormat("yyyy-MM-dd")
            campo.setCalendarPopup(True)
            valor = filtro.valor or QDate.currentDate().toString("yyyy-MM-dd")
            campo.setDate(QDate.fromString(valor, "yyyy-MM-dd"))
            return campo
        check = QCheckBox("Incluir en el calculo")
        check.setObjectName("checkFiltroReporte")
        check.setChecked(filtro.valor != "0")
        return check

    def _mostrar_indicadores(self, estado: EstadoReportes) -> None:
        for indice, tarjeta in enumerate(self._indicadores):
            if indice < len(estado.indicadores):
                indicador = estado.indicadores[indice]
                tarjeta.actualizar(indicador.titulo, indicador.valor, indicador.detalle)
            else:
                tarjeta.actualizar("-", "0", "")

    def _mostrar_tabla_actual(self, tabla: TablaReporte | None) -> None:
        self._tabla_actual = tabla
        if tabla is None:
            self._titulo_preview.setText("Selecciona un reporte")
            self._descripcion_preview.setText("")
            self._tabla.setRowCount(0)
            self._tabla.setColumnCount(0)
            return
        self._titulo_preview.setText(tabla.titulo)
        self._descripcion_preview.setText(tabla.descripcion)
        configurar_tabla_operativa(self._tabla, list(tabla.columnas))
        self._tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self._tabla.setRowCount(len(tabla.filas))
        for fila, valores in enumerate(tabla.filas):
            for columna, valor in enumerate(valores):
                self._tabla.setItem(fila, columna, crear_item_tabla(valor))
        self._tabla.resizeRowsToContents()

    def _emitir_filtros(self) -> None:
        filtros = self._capturar_filtros()
        self.filtros_aplicados.emit(self._reporte_actual_codigo, filtros)

    def _emitir_exportacion(self) -> None:
        self.exportar_solicitado.emit(self._reporte_actual_codigo, self._capturar_filtros())

    def _emitir_exportacion_en(self) -> None:
        directorio = self.solicitar_ruta_exportacion(self._reporte_actual_codigo)
        if directorio:
            self.exportar_en_solicitado.emit(
                self._reporte_actual_codigo,
                self._capturar_filtros(),
                directorio,
            )

    def _capturar_filtros(self) -> dict[str, str]:
        valores: dict[str, str] = {}
        for clave, widget in self._filtros_widgets.items():
            if isinstance(widget, CampoBusquedaSeleccionSigqua):
                identificador = widget.identificador_seleccionado()
                valores[clave] = str(identificador) if identificador is not None else "TODOS"
            elif isinstance(widget, QComboBox):
                valores[clave] = str(widget.currentData() or "TODOS")
            elif isinstance(widget, QDateEdit):
                valores[clave] = widget.date().toString("yyyy-MM-dd")
            elif isinstance(widget, QCheckBox):
                valores[clave] = "1" if widget.isChecked() else "0"
        return valores

    def aplicar_tema(self, nombre_tema: str) -> None:
        self._tema_actual = resolver_nombre_tema(nombre_tema)
        self._paleta = obtener_paleta_tema(self._tema_actual)
        self._aplicar_estilos()

    def _aplicar_estilos(self) -> None:
        paleta = self._paleta
        fondo_panel = obtener_fondo_header_destacado(self._tema_actual)
        self.setStyleSheet(
            f"""
            QWidget#vistaReportes {{
                background-color: {paleta["fondo_principal"]};
                color: {paleta["texto_principal"]};
                font-family: "{paleta["familia_tipografica"]}";
            }}
            QScrollArea#scrollReportes,
            QWidget#contenidoReportes {{
                background-color: {paleta["fondo_principal"]};
                border: none;
            }}
            QLabel#tituloModuloReportes {{
                font-size: {paleta["tamano_titulo_panel"] + 6}px;
                font-weight: {paleta["peso_titulo"]};
                color: {paleta["texto_principal"]};
            }}
            QLabel#descripcionModuloReportes,
            QLabel#descripcionReporte,
            QLabel#descripcionTarjetaReporte,
            QLabel#tarjetaDetalle,
            QLabel#resumenTarjetaReporte {{
                color: {paleta["texto_secundario"]};
                font-size: 12px;
            }}
            QLabel#tituloSeccionReportes,
            QLabel#tituloReporte,
            QLabel#tituloTarjetaReporte {{
                color: {paleta["texto_principal"]};
                font-size: {paleta["tamano_titulo_panel"]}px;
                font-weight: {paleta["peso_titulo"]};
            }}
            QLabel#mensajeReportes {{
                border-radius: 12px;
                padding: 10px 12px;
                font-size: 12px;
                font-weight: 700;
            }}
            QLabel#mensajeReportes[error="false"] {{
                background-color: {paleta["fondo_exito"]};
                border: 1px solid {paleta["borde_exito"]};
                color: {paleta["texto_exito"]};
            }}
            QLabel#mensajeReportes[error="true"] {{
                background-color: {paleta["fondo_error"]};
                border: 1px solid {paleta["borde_error"]};
                color: {paleta["texto_error"]};
            }}
            QFrame#panelFiltrosReportes,
            QFrame#panelTablaReportes,
            QFrame#tarjetaResumenSimple {{
                background-color: {fondo_panel};
                border: 1px solid {paleta["borde_principal"]};
                border-radius: 18px;
            }}
            QPushButton#tarjetaReporteAdmin {{
                background-color: {paleta["fondo_superficie_suave"]};
                border: 1px solid {paleta["borde_medio"]};
                border-radius: 12px;
                text-align: left;
            }}
            QPushButton#tarjetaReporteAdmin:hover {{
                background-color: {paleta["fondo_superficie_destacada"]};
                border: 1px solid {paleta["acento_hover"]};
            }}
            QPushButton#tarjetaReporteAdmin:checked {{
                background-color: {paleta["fondo_menu_activo"]};
                border: 2px solid {paleta["acento_primario"]};
            }}
            QPushButton#tarjetaReporteAdmin:checked QLabel#tituloTarjetaReporte,
            QPushButton#tarjetaReporteAdmin:checked QLabel#resumenTarjetaReporte {{
                color: {paleta["texto_principal"]};
            }}
            QLabel#iconoTarjetaReporte {{
                background-color: {paleta["fondo_superficie_muy_suave"]};
                border: 1px solid {paleta["borde_suave"]};
                border-radius: 8px;
            }}
            QLabel#tarjetaTitulo {{
                color: {paleta["texto_secundario"]};
                font-size: 11px;
                font-weight: 700;
            }}
            QLabel#tarjetaValor {{
                color: {paleta["texto_principal"]};
                font-size: {paleta["tamano_titulo_tarjeta"]}px;
                font-weight: {paleta["peso_titulo"]};
            }}
            QComboBox#campoFiltroReporte,
            QDateEdit#campoFechaReporte,
            QWidget#campoBusquedaSeleccionSigqua QLineEdit#campoBusquedaSeleccionSigqua {{
                background-color: {paleta["fondo_input"]};
                border: 1px solid {paleta["borde_medio"]};
                border-radius: 8px;
                color: {paleta["texto_input"]};
                min-height: 36px;
                padding: 0 10px;
            }}
            QComboBox#campoFiltroReporte:focus,
            QDateEdit#campoFechaReporte:focus,
            QWidget#campoBusquedaSeleccionSigqua QLineEdit#campoBusquedaSeleccionSigqua:focus {{
                background-color: {paleta["fondo_input_focus"]};
                border: 1px solid {paleta["borde_foco_input"]};
            }}
            QListView#popupBusquedaSeleccionSigqua {{
                background-color: {paleta["fondo_superficie"]};
                border: 1px solid {paleta["borde_medio"]};
                color: {paleta["texto_principal"]};
                outline: none;
                padding: 3px;
            }}
            QListView#popupBusquedaSeleccionSigqua::item {{
                min-height: 28px;
                padding: 5px 8px;
            }}
            QListView#popupBusquedaSeleccionSigqua::item:selected {{
                background-color: {paleta["fondo_menu_activo"]};
                color: {paleta["texto_principal"]};
            }}
            QCheckBox#checkFiltroReporte {{
                color: {paleta["texto_principal"]};
            }}
            QTableWidget#tablaOperativaOscura {{
                background-color: {paleta["fondo_tabla_cuerpo"]};
                alternate-background-color: {paleta["fondo_tabla_fila_alterna"]};
                border: none;
                border-radius: 18px;
                padding: 0 0 18px 0;
                color: {paleta["texto_principal"]};
            }}
            QWidget#viewportTablaReportes {{
                background: transparent;
                border: none;
                border-bottom-left-radius: 18px;
                border-bottom-right-radius: 18px;
            }}
            QTableWidget#tablaOperativaOscura QHeaderView::section:first {{
                border-top-left-radius: 18px;
            }}
            QTableWidget#tablaOperativaOscura QHeaderView::section:last {{
                border-top-right-radius: 18px;
            }}
            QHeaderView::section {{
                background-color: {paleta["fondo_tabla_header_destacado"]};
                border: 0;
                color: {paleta["texto_input"]};
                border-right: 1px solid {paleta["borde_tabla"]};
                border-bottom: 1px solid {paleta["borde_tabla"]};
                font-weight: {paleta["peso_titulo"]};
                padding: 8px;
            }}
            QTableWidget::item:selected {{
                background-color: {paleta["fondo_tabla_seleccion"]};
                color: {paleta["texto_principal"]};
            }}
            """
        )
