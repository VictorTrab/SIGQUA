"""Vista PySide6 del modulo de historial de pagos."""

from __future__ import annotations

from typing import Callable

from PySide6.QtCore import QDate, QElapsedTimer, QEvent, QSize, Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QButtonGroup,
    QComboBox,
    QDateEdit,
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
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
    DialogoBaseSicap,
    DialogoMensajeSicap,
    configurar_tabla_operativa,
    crear_boton_operativo,
    crear_item_tabla,
    obtener_icono_tabler_coloreado,
    resolver_variante_boton_modal,
)
from comun.ui.temas import TEMA_SICAP_PREDETERMINADO, obtener_paleta_tema
from modulos.historial_pagos.entidades import (
    DetalleHistorialPago,
    FILTRO_HISTORIAL_CONEXION,
    FILTRO_HISTORIAL_MENSUALIDAD,
    FILTRO_HISTORIAL_PLAN,
    FILTRO_HISTORIAL_RECONEXION,
    FILTRO_HISTORIAL_TODOS,
    FILTRO_METODO_DEPOSITO,
    FILTRO_METODO_EFECTIVO,
    FILTRO_METODO_OTRO,
    FILTRO_METODO_TODOS,
    FILTRO_METODO_TRANSFERENCIA,
    FilaHistorialPago,
    PaginaHistorialPagos,
    ResumenHistorialPagos,
)


class TarjetaResumenHistorial(QFrame):
    """Tarjeta de resumen del modulo."""

    def __init__(self, icono: str, color_icono: str) -> None:
        super().__init__()
        self.setObjectName("tarjetaResumenHistorialPagos")
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

        bloque = QVBoxLayout()
        bloque.setContentsMargins(0, 0, 0, 0)
        bloque.setSpacing(2)
        self._titulo = QLabel("")
        self._titulo.setObjectName("tituloTarjetaResumen")
        self._valor = QLabel("")
        self._valor.setObjectName("valorTarjetaResumen")
        self._detalle = QLabel("")
        self._detalle.setObjectName("detalleTarjetaResumen")
        self._detalle.setWordWrap(True)
        bloque.addWidget(self._titulo)
        bloque.addWidget(self._valor)
        bloque.addWidget(self._detalle)
        bloque.addStretch(1)

        layout.addWidget(self._icono, alignment=Qt.AlignmentFlag.AlignTop)
        layout.addLayout(bloque, 1)

    def actualizar(self, titulo: str, valor: str, detalle: str) -> None:
        self._titulo.setText(titulo)
        self._valor.setText(valor)
        self._detalle.setText(detalle)


class BotonIconoFilaHistorial(QToolButton):
    """Boton compacto de acciones por fila."""

    COLOR_BASE = "#c8d6f1"
    INTERVALO_TOOLTIP_MS = 1600

    def __init__(self, icono: str, color_hover: str, tooltip: str) -> None:
        super().__init__()
        self._icono = icono
        self._color_hover = color_hover
        self._color_base = self.COLOR_BASE
        self._temporizador_tooltip = QElapsedTimer()
        self.setObjectName("botonIconoFilaHistorial")
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
            if self._temporizador_tooltip.isValid() and self._temporizador_tooltip.elapsed() < self.INTERVALO_TOOLTIP_MS:
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


class DialogoDetalleHistorialPago(DialogoBaseSicap):
    """Detalle historico del pago con reimpresion."""

    def __init__(
        self,
        detalle: DetalleHistorialPago,
        formateador_moneda: Callable[[int], str],
        formateador_fecha_hora: Callable[[str], str],
        formateador_tipo: Callable[[str], str],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._detalle = detalle
        self._formateador_moneda = formateador_moneda
        self._formateador_fecha_hora = formateador_fecha_hora
        self._formateador_tipo = formateador_tipo
        self._accion_resultado = "cerrar"
        self.setMinimumWidth(820)
        self.setMinimumHeight(620)
        self._construir_ui()

    @property
    def accion_resultado(self) -> str:
        return self._accion_resultado

    def _construir_ui(self) -> None:
        titulo = QLabel("Detalle de pago")
        titulo.setObjectName("tituloDialogoSicap")
        descripcion = QLabel(
            "Consulta la informacion del comprobante, detalle aplicado y datos operativos del pago."
        )
        descripcion.setObjectName("descripcionDialogoSicap")
        descripcion.setWordWrap(True)

        scroll = QScrollArea()
        scroll.setObjectName("scrollDetalleHistorialPago")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        contenedor = QWidget()
        layout_scroll = QVBoxLayout(contenedor)
        layout_scroll.setContentsMargins(0, 0, 0, 0)
        layout_scroll.setSpacing(12)

        panel = QFrame()
        panel.setObjectName("panelContenidoDetalleHistorialPago")
        layout_panel = QVBoxLayout(panel)
        layout_panel.setContentsMargins(18, 18, 18, 18)
        layout_panel.setSpacing(14)

        fila_superior = QHBoxLayout()
        bloque_nombre = QVBoxLayout()
        bloque_nombre.setSpacing(4)
        codigo = QLabel(self._detalle.numero_comprobante)
        codigo.setObjectName("codigoHistorialDetalle")
        nombre = QLabel(self._detalle.abonado_nombre)
        nombre.setObjectName("nombreHistorialDetalle")
        bloque_nombre.addWidget(codigo)
        bloque_nombre.addWidget(nombre)
        badge_tipo = QLabel(self._formateador_tipo(self._detalle.tipo_pago))
        badge_tipo.setObjectName("badgeTipoHistorial")
        fila_superior.addLayout(bloque_nombre, 1)
        fila_superior.addWidget(badge_tipo, alignment=Qt.AlignmentFlag.AlignTop)

        layout_panel.addLayout(fila_superior)
        layout_panel.addWidget(
            self._crear_bloque_seccion(
                "Identificacion del comprobante",
                "Datos principales del recibo emitido.",
                (
                    ("Numero", self._detalle.numero_comprobante),
                    ("Fecha y hora", self._formateador_fecha_hora(self._detalle.fecha_pago)),
                    ("Tipo", self._formateador_tipo(self._detalle.tipo_pago)),
                ),
            )
        )
        layout_panel.addWidget(
            self._crear_bloque_seccion(
                "Datos del servicio",
                "Contexto del abonado y la casa a la que se aplico el pago.",
                (
                    ("Casa", self._detalle.casa_codigo),
                    ("Abonado", self._detalle.abonado_nombre),
                    ("DNI", self._detalle.abonado_dni),
                    ("Barrio", self._detalle.barrio_nombre or "Sin barrio"),
                    ("Direccion", self._detalle.direccion_casa or "Sin referencia"),
                ),
            )
        )
        layout_panel.addWidget(
            self._crear_bloque_seccion(
                "Datos operativos",
                "Metodo, referencia y usuario que registró la operacion.",
                (
                    ("Metodo", self._detalle.metodo_pago),
                    ("Referencia", self._detalle.referencia or "No aplica"),
                    ("Registrado por", self._detalle.usuario_registro or "Sin registro"),
                ),
            )
        )
        layout_panel.addWidget(self._crear_bloque_detalle_lineas())
        layout_panel.addWidget(
            self._crear_bloque_totales(
                (
                    ("Total pagado", self._formateador_moneda(self._detalle.total_pagado_centavos)),
                    ("Saldo posterior", self._formateador_moneda(self._detalle.saldo_posterior_centavos)),
                )
            )
        )

        fila_acciones = QHBoxLayout()
        fila_acciones.setSpacing(10)
        boton_cerrar = BotonAccionContextual(
            "Cerrar",
            variante=resolver_variante_boton_modal("Cerrar", "neutro"),
            centrado=True,
            mostrar_icono=False,
        )
        boton_reimprimir = BotonAccionContextual(
            "Reimprimir copia",
            variante=resolver_variante_boton_modal("Reimprimir copia", "informacion"),
            centrado=True,
            mostrar_icono=False,
        )
        boton_cerrar.setMinimumWidth(124)
        boton_reimprimir.setMinimumWidth(164)
        boton_cerrar.clicked.connect(self.reject)
        boton_reimprimir.clicked.connect(self._solicitar_reimpresion)
        fila_acciones.addWidget(boton_cerrar)
        fila_acciones.addStretch(1)
        fila_acciones.addWidget(boton_reimprimir)
        layout_panel.addLayout(fila_acciones)

        layout_scroll.addWidget(panel)
        scroll.setWidget(contenedor)

        self.layout_cabecera.addWidget(titulo)
        self.layout_cabecera.addWidget(descripcion)
        self.layout_cuerpo.addWidget(scroll)
        self._pie.setVisible(False)
        self._aplicar_estilos()

    def _crear_bloque_seccion(
        self,
        titulo: str,
        descripcion: str,
        filas: tuple[tuple[str, str], ...],
    ) -> QFrame:
        bloque = QFrame()
        bloque.setObjectName("seccionDetalleHistorialPago")
        layout = QVBoxLayout(bloque)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        label_titulo = QLabel(titulo)
        label_titulo.setObjectName("tituloSeccionDetalleHistorialPago")
        label_descripcion = QLabel(descripcion)
        label_descripcion.setObjectName("descripcionSeccionDetalleHistorialPago")
        label_descripcion.setWordWrap(True)
        layout.addWidget(label_titulo)
        layout.addWidget(label_descripcion)

        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(14)
        for indice, (etiqueta, valor) in enumerate(filas):
            grid.addWidget(self._crear_campo_detalle(etiqueta, valor), indice // 2, indice % 2)
        layout.addLayout(grid)
        return bloque

    def _crear_bloque_detalle_lineas(self) -> QFrame:
        bloque = QFrame()
        bloque.setObjectName("seccionDetalleHistorialPago")
        layout = QVBoxLayout(bloque)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)
        titulo = QLabel("Detalle aplicado")
        titulo.setObjectName("tituloSeccionDetalleHistorialPago")
        descripcion = QLabel("Lineas reales registradas en pagos_detalle para este comprobante.")
        descripcion.setObjectName("descripcionSeccionDetalleHistorialPago")
        descripcion.setWordWrap(True)
        tabla = QTableWidget(0, 2)
        tabla.setObjectName("tablaDetalleHistorialPago")
        configurar_tabla_operativa(tabla, ["Concepto", "Monto"])
        tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        tabla.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        tabla.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        tabla.verticalHeader().setDefaultSectionSize(46)
        tabla.setRowCount(len(self._detalle.lineas_detalle))
        for fila, linea in enumerate(self._detalle.lineas_detalle):
            tabla.setItem(fila, 0, crear_item_tabla(linea.descripcion))
            tabla.setItem(fila, 1, crear_item_tabla(self._formateador_moneda(linea.monto_pagado_centavos)))
        tabla.resizeRowsToContents()
        layout.addWidget(titulo)
        layout.addWidget(descripcion)
        layout.addWidget(tabla)
        return bloque

    def _crear_bloque_totales(self, filas: tuple[tuple[str, str], ...]) -> QFrame:
        bloque = QFrame()
        bloque.setObjectName("seccionDetalleHistorialPago")
        layout = QVBoxLayout(bloque)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)
        titulo = QLabel("Totales")
        titulo.setObjectName("tituloSeccionDetalleHistorialPago")
        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(14)
        for indice, (etiqueta, valor) in enumerate(filas):
            grid.addWidget(self._crear_campo_detalle(etiqueta, valor), 0, indice)
        layout.addWidget(titulo)
        layout.addLayout(grid)
        return bloque

    def _crear_campo_detalle(self, etiqueta: str, valor: str) -> QFrame:
        tarjeta = QFrame()
        tarjeta.setObjectName("campoDetalleHistorialPago")
        layout = QVBoxLayout(tarjeta)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(5)
        label_etiqueta = QLabel(etiqueta)
        label_etiqueta.setObjectName("etiquetaDetalleHistorialPago")
        label_valor = QLabel(valor)
        label_valor.setObjectName("valorDetalleHistorialPago")
        label_valor.setWordWrap(True)
        layout.addWidget(label_etiqueta)
        layout.addWidget(label_valor)
        return tarjeta

    def _solicitar_reimpresion(self) -> None:
        self._accion_resultado = "reimprimir"
        self.accept()

    def _aplicar_estilos(self) -> None:
        self.setStyleSheet(
            self.styleSheet()
            + """
            QScrollArea#scrollDetalleHistorialPago {
                background: transparent;
                border: none;
            }
            QFrame#panelContenidoDetalleHistorialPago,
            QFrame#seccionDetalleHistorialPago {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 16px;
            }
            QLabel#codigoHistorialDetalle {
                color: rgba(235, 242, 248, 0.76);
                font-size: 11px;
                font-weight: 800;
            }
            QLabel#nombreHistorialDetalle {
                color: #ffffff;
                font-size: 20px;
                font-weight: 900;
            }
            QLabel#badgeTipoHistorial {
                border-radius: 11px;
                padding: 6px 10px;
                font-size: 11px;
                font-weight: 800;
                color: #d9fff5;
                background: rgba(16, 120, 98, 0.22);
                border: 1px solid rgba(158, 231, 214, 0.26);
            }
            QLabel#tituloSeccionDetalleHistorialPago {
                color: #ffffff;
                font-size: 14px;
                font-weight: 800;
            }
            QLabel#descripcionSeccionDetalleHistorialPago,
            QLabel#etiquetaDetalleHistorialPago {
                color: rgba(235, 242, 248, 0.76);
                font-size: 11px;
                font-weight: 700;
            }
            QFrame#campoDetalleHistorialPago {
                background: rgba(255, 255, 255, 0.04);
                border: 1px solid rgba(255, 255, 255, 0.10);
                border-radius: 14px;
            }
            QLabel#valorDetalleHistorialPago {
                color: #ffffff;
                font-size: 13px;
                font-weight: 700;
            }
            QTableWidget#tablaDetalleHistorialPago {
                background: rgba(255, 255, 255, 0.04);
                border: 1px solid rgba(255, 255, 255, 0.10);
                border-radius: 14px;
            }
            QTableWidget#tablaDetalleHistorialPago QHeaderView::section {
                background: rgba(255, 255, 255, 0.10);
                color: #f7fbff;
                border: none;
                padding: 10px 12px;
                font-size: 12px;
                font-weight: 800;
            }
            """
        )


class VistaHistorialPagos(QWidget):
    """Listado operativo de pagos confirmados."""

    ANCHO_COLUMNA_ACCIONES = 130
    RADIO_PANEL_TABLA = 18
    FECHA_MINIMA = QDate(2000, 1, 1)

    filtro_texto_cambiado = Signal(str)
    filtro_tipo_cambiado = Signal(str)
    filtro_metodo_cambiado = Signal(str)
    rango_fechas_aplicado = Signal(str, str)
    pagina_cambiada = Signal(int)
    detalle_pago_solicitado = Signal(int)
    reimpresion_solicitada = Signal(int)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("vistaHistorialPagos")
        self._tema_actual = TEMA_SICAP_PREDETERMINADO
        self._paleta_tema = obtener_paleta_tema(self._tema_actual)
        self._pagina_actual = 1
        self._items_actuales: list[FilaHistorialPago] = []
        self._construir_ui()
        self._aplicar_estilos()

    def mostrar_resumen(
        self,
        resumen: ResumenHistorialPagos,
        formateador_moneda: Callable[[int], str],
    ) -> None:
        self._tarjeta_total.actualizar(
            "Total de pagos",
            str(resumen.total_pagos),
            "Pagos confirmados segun filtros activos.",
        )
        self._tarjeta_hoy.actualizar(
            "Pagos hoy",
            str(resumen.pagos_hoy),
            "Operaciones registradas en la fecha actual.",
        )
        self._tarjeta_cobrado.actualizar(
            "Total cobrado hoy",
            formateador_moneda(resumen.total_cobrado_hoy_centavos),
            "Monto acumulado hoy segun filtros activos.",
        )
        self._tarjeta_ultimo.actualizar(
            "Ultimo comprobante",
            resumen.ultimo_comprobante or "Sin registro",
            "Correlativo mas reciente dentro del historial visible.",
        )

    def mostrar_historial(
        self,
        pagina: PaginaHistorialPagos,
        formateador_fecha_hora: Callable[[str], str],
        formateador_moneda: Callable[[int], str],
        formateador_tipo: Callable[[str], str],
    ) -> None:
        self._items_actuales = list(pagina.items)
        self._pagina_actual = pagina.pagina_actual
        self._tabla.setRowCount(len(pagina.items))
        for fila, item in enumerate(pagina.items):
            self._tabla.setItem(fila, 0, crear_item_tabla(item.numero_comprobante))
            self._tabla.setItem(fila, 1, crear_item_tabla(formateador_fecha_hora(item.fecha_pago)))
            self._tabla.setItem(fila, 2, crear_item_tabla(formateador_tipo(item.tipo_pago)))
            self._tabla.setItem(fila, 3, crear_item_tabla(item.abonado_nombre))
            self._tabla.setItem(fila, 4, crear_item_tabla(item.casa_codigo))
            self._tabla.setItem(fila, 5, crear_item_tabla(item.metodo_pago))
            self._tabla.setItem(fila, 6, crear_item_tabla(formateador_moneda(item.total_pagado_centavos)))
            self._tabla.setItem(fila, 7, crear_item_tabla(item.usuario_registro or "Sin registro"))
            self._tabla.setCellWidget(fila, 8, self._crear_acciones_fila(item))
        self._tabla.resizeRowsToContents()
        self._label_paginacion.setText(
            f"Mostrando {pagina.indice_inicio}-{pagina.indice_fin} de {pagina.total_registros} registros"
        )
        self._label_numero_pagina.setText(
            f"Pagina {pagina.pagina_actual} de {pagina.total_paginas}"
        )
        self._boton_pagina_anterior.setEnabled(pagina.pagina_actual > 1)
        self._boton_pagina_siguiente.setEnabled(pagina.pagina_actual < pagina.total_paginas)
        self._actualizar_estado_vacio(not bool(pagina.items))

    def mostrar_detalle_pago(
        self,
        detalle: DetalleHistorialPago,
        formateador_moneda: Callable[[int], str],
        formateador_fecha_hora: Callable[[str], str],
        formateador_tipo: Callable[[str], str],
    ) -> str:
        dialogo = DialogoDetalleHistorialPago(
            detalle=detalle,
            formateador_moneda=formateador_moneda,
            formateador_fecha_hora=formateador_fecha_hora,
            formateador_tipo=formateador_tipo,
            parent=self,
        )
        dialogo.exec()
        return dialogo.accion_resultado

    def mostrar_mensaje(self, mensaje: str, es_error: bool = False) -> None:
        self._mensaje.setText(mensaje)
        self._mensaje.setProperty("error", es_error)
        self._mensaje.style().unpolish(self._mensaje)
        self._mensaje.style().polish(self._mensaje)
        self._mensaje.setVisible(True)
        QTimer.singleShot(6500, self._mensaje.hide)

    def _construir_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 24, 26, 24)
        layout.setSpacing(12)

        self._mensaje = QLabel("")
        self._mensaje.setObjectName("mensajeHistorialPagos")
        self._mensaje.setVisible(False)
        self._mensaje.setWordWrap(True)
        layout.addWidget(self._mensaje)

        fila_tarjetas = QGridLayout()
        fila_tarjetas.setHorizontalSpacing(10)
        fila_tarjetas.setVerticalSpacing(10)
        self._tarjeta_total = TarjetaResumenHistorial("receipt-2.svg", "#8ec9ff")
        self._tarjeta_hoy = TarjetaResumenHistorial("clock.svg", "#8de8c7")
        self._tarjeta_cobrado = TarjetaResumenHistorial("calendar-stats.svg", "#f7cc7a")
        self._tarjeta_ultimo = TarjetaResumenHistorial("receipt-2.svg", "#c6b6ff")
        fila_tarjetas.addWidget(self._tarjeta_total, 0, 0)
        fila_tarjetas.addWidget(self._tarjeta_hoy, 0, 1)
        fila_tarjetas.addWidget(self._tarjeta_cobrado, 0, 2)
        fila_tarjetas.addWidget(self._tarjeta_ultimo, 0, 3)
        layout.addLayout(fila_tarjetas)

        panel_filtros = QFrame()
        panel_filtros.setObjectName("panelOperativoHistorialPagos")
        layout_filtros = QVBoxLayout(panel_filtros)
        layout_filtros.setContentsMargins(14, 14, 14, 14)
        layout_filtros.setSpacing(10)

        self._campo_busqueda = QLineEdit()
        self._campo_busqueda.setPlaceholderText("Buscar por comprobante, abonado, DNI, casa o referencia")
        self._campo_busqueda.textChanged.connect(self.filtro_texto_cambiado.emit)
        layout_filtros.addWidget(self._campo_busqueda)

        fila_tipo = QHBoxLayout()
        fila_tipo.setSpacing(6)
        self._grupo_tipo = QButtonGroup(self)
        self._grupo_tipo.setExclusive(True)
        self._botones_tipo: dict[str, QPushButton] = {}
        for codigo, texto in (
            (FILTRO_HISTORIAL_TODOS, "Todos"),
            (FILTRO_HISTORIAL_MENSUALIDAD, "Mensualidad"),
            (FILTRO_HISTORIAL_PLAN, "Plan"),
            (FILTRO_HISTORIAL_CONEXION, "Conexion"),
            (FILTRO_HISTORIAL_RECONEXION, "Reconexion"),
        ):
            boton = QPushButton(texto)
            boton.setObjectName("chipFiltroHistorialPago")
            boton.setCheckable(True)
            boton.setCursor(Qt.CursorShape.PointingHandCursor)
            boton.clicked.connect(lambda checked=False, valor=codigo: self.filtro_tipo_cambiado.emit(valor))
            self._grupo_tipo.addButton(boton)
            self._botones_tipo[codigo] = boton
            fila_tipo.addWidget(boton)
        self._botones_tipo[FILTRO_HISTORIAL_TODOS].setChecked(True)
        fila_tipo.addStretch(1)
        layout_filtros.addLayout(fila_tipo)

        fila_secundaria = QHBoxLayout()
        fila_secundaria.setSpacing(8)
        self._combo_metodo = QComboBox()
        self._combo_metodo.addItem("Todos los metodos", FILTRO_METODO_TODOS)
        self._combo_metodo.addItem("Efectivo", FILTRO_METODO_EFECTIVO)
        self._combo_metodo.addItem("Transferencia", FILTRO_METODO_TRANSFERENCIA)
        self._combo_metodo.addItem("Deposito", FILTRO_METODO_DEPOSITO)
        self._combo_metodo.addItem("Otro", FILTRO_METODO_OTRO)
        self._combo_metodo.currentIndexChanged.connect(
            lambda _indice: self.filtro_metodo_cambiado.emit(str(self._combo_metodo.currentData()))
        )

        self._fecha_desde = self._crear_selector_fecha("Sin limite desde")
        self._fecha_hasta = self._crear_selector_fecha("Sin limite hasta")
        boton_aplicar_fechas = crear_boton_operativo("Aplicar fechas")
        boton_aplicar_fechas.clicked.connect(self._emitir_rango_fechas)

        fila_secundaria.addWidget(self._combo_metodo)
        fila_secundaria.addWidget(self._fecha_desde)
        fila_secundaria.addWidget(self._fecha_hasta)
        fila_secundaria.addWidget(boton_aplicar_fechas)
        layout_filtros.addLayout(fila_secundaria)
        layout.addWidget(panel_filtros)

        panel_tabla = QFrame()
        panel_tabla.setObjectName("panelTablaHistorialPagos")
        layout_tabla = QVBoxLayout(panel_tabla)
        layout_tabla.setContentsMargins(14, 14, 14, 14)
        layout_tabla.setSpacing(10)

        self._tabla = QTableWidget(0, 9)
        self._tabla.setObjectName("tablaHistorialPagos")
        configurar_tabla_operativa(
            self._tabla,
            [
                "Comprobante",
                "Fecha",
                "Tipo",
                "Abonado",
                "Casa",
                "Metodo",
                "Total",
                "Usuario",
                "Acciones",
            ],
        )
        self._tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._tabla.horizontalHeader().setStretchLastSection(False)
        self._tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self._tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self._tabla.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self._tabla.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self._tabla.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self._tabla.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self._tabla.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        self._tabla.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        self._tabla.horizontalHeader().setSectionResizeMode(8, QHeaderView.ResizeMode.Interactive)
        self._tabla.setColumnWidth(8, self.ANCHO_COLUMNA_ACCIONES)
        self._tabla.verticalHeader().setDefaultSectionSize(58)
        self._tabla.setFrameShape(QFrame.Shape.NoFrame)
        self._tabla.setViewportMargins(0, 0, 0, self.RADIO_PANEL_TABLA)
        self._tabla.viewport().setObjectName("viewportTablaHistorialPagos")
        self._tabla.viewport().setAutoFillBackground(False)

        self._estado_vacio = QLabel("No hay pagos que coincidan con los filtros actuales.")
        self._estado_vacio.setObjectName("estadoVacioHistorialPagos")
        self._estado_vacio.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._estado_vacio.setVisible(False)

        pie = QHBoxLayout()
        pie.setSpacing(8)
        self._label_paginacion = QLabel("Mostrando 0-0 de 0 registros")
        self._label_paginacion.setObjectName("textoPieHistorialPagos")
        pie.addWidget(self._label_paginacion)
        pie.addStretch(1)
        self._boton_pagina_anterior = crear_boton_operativo("Anterior")
        self._boton_pagina_siguiente = crear_boton_operativo("Siguiente")
        self._boton_pagina_anterior.clicked.connect(
            lambda: self.pagina_cambiada.emit(max(1, self._pagina_actual - 1))
        )
        self._boton_pagina_siguiente.clicked.connect(
            lambda: self.pagina_cambiada.emit(self._pagina_actual + 1)
        )
        self._label_numero_pagina = QLabel("Pagina 1 de 1")
        self._label_numero_pagina.setObjectName("textoPieHistorialPagos")
        pie.addWidget(self._boton_pagina_anterior)
        pie.addWidget(self._label_numero_pagina)
        pie.addWidget(self._boton_pagina_siguiente)

        layout_tabla.addWidget(self._tabla)
        layout_tabla.addWidget(self._estado_vacio)
        layout_tabla.addLayout(pie)
        layout.addWidget(panel_tabla, 1)

    def _crear_selector_fecha(self, texto_vacio: str) -> QDateEdit:
        campo = QDateEdit()
        campo.setObjectName("campoFechaHistorialPago")
        campo.setDisplayFormat("yyyy-MM-dd")
        campo.setCalendarPopup(True)
        campo.setMinimumDate(self.FECHA_MINIMA)
        campo.setDate(self.FECHA_MINIMA)
        campo.setSpecialValueText(texto_vacio)
        return campo

    def _emitir_rango_fechas(self) -> None:
        fecha_desde = "" if self._fecha_desde.date() == self.FECHA_MINIMA else self._fecha_desde.date().toString("yyyy-MM-dd")
        fecha_hasta = "" if self._fecha_hasta.date() == self.FECHA_MINIMA else self._fecha_hasta.date().toString("yyyy-MM-dd")
        self.rango_fechas_aplicado.emit(fecha_desde, fecha_hasta)

    def _crear_acciones_fila(self, fila: FilaHistorialPago) -> QWidget:
        contenedor = QWidget()
        contenedor.setObjectName("contenedorAccionesHistorialPago")
        contenedor.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        contenedor.setMinimumWidth(self.ANCHO_COLUMNA_ACCIONES)
        contenedor.setMinimumHeight(58)
        layout = QHBoxLayout(contenedor)
        layout.setContentsMargins(0, 0, 0, 14)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        boton_detalle = BotonIconoFilaHistorial("eye.svg", "#4fa3ff", "Ver detalle")
        boton_reimprimir = BotonIconoFilaHistorial("receipt-2.svg", "#8de8c7", "Reimprimir copia")
        boton_detalle.clicked.connect(
            lambda checked=False, pago_id=fila.pago_id: self.detalle_pago_solicitado.emit(pago_id)
        )
        boton_reimprimir.clicked.connect(
            lambda checked=False, pago_id=fila.pago_id: self.reimpresion_solicitada.emit(pago_id)
        )
        layout.addWidget(boton_detalle)
        layout.addWidget(boton_reimprimir)
        return contenedor

    def _actualizar_estado_vacio(self, sin_datos: bool) -> None:
        self._estado_vacio.setVisible(sin_datos)
        self._tabla.setVisible(not sin_datos)

    def _aplicar_estilos(self) -> None:
        radio_panel_tabla = self.RADIO_PANEL_TABLA
        self.setStyleSheet(
            """
            QWidget#vistaHistorialPagos {
                background: transparent;
            }
            QLabel#mensajeHistorialPagos {
                color: #d9fff5;
                font-size: 12px;
                font-weight: 700;
                padding: 8px 10px;
                border-radius: 12px;
                background-color: rgba(16, 120, 98, 0.16);
                border: 1px solid rgba(158, 231, 214, 0.26);
            }
            QLabel#mensajeHistorialPagos[error="true"] {
                color: #ffd4cf;
                background-color: rgba(180, 35, 24, 0.15);
                border: 1px solid rgba(255, 205, 199, 0.28);
            }
            QFrame#panelOperativoHistorialPagos,
            QFrame#tarjetaResumenHistorialPagos {
                background: rgba(255, 255, 255, 0.10);
                border: 1px solid rgba(255, 255, 255, 0.16);
                border-radius: 18px;
            }
            QFrame#panelTablaHistorialPagos {
                background: rgba(255, 255, 255, 0.10);
                border: 1px solid rgba(255, 255, 255, 0.16);
                border-radius: """
            + str(radio_panel_tabla)
            + """px;
            }
            QTableWidget#tablaHistorialPagos {
                background: rgba(255, 255, 255, 0.03);
                background-clip: padding;
                border: none;
                border-radius: """
            + str(radio_panel_tabla)
            + """px;
                padding: 0 0 """
            + str(radio_panel_tabla)
            + """px 0;
            }
            QWidget#viewportTablaHistorialPagos {
                background: transparent;
                border: none;
                border-bottom-left-radius: """
            + str(radio_panel_tabla)
            + """px;
                border-bottom-right-radius: """
            + str(radio_panel_tabla)
            + """px;
            }
            QTableWidget#tablaHistorialPagos QHeaderView::section:first {
                border-top-left-radius: """
            + str(radio_panel_tabla)
            + """px;
            }
            QTableWidget#tablaHistorialPagos QHeaderView::section {
                background: rgba(255, 255, 255, 0.10);
                color: #f7fbff;
                border: none;
                border-right: 1px solid rgba(255, 255, 255, 0.06);
                border-bottom: 1px solid rgba(255, 255, 255, 0.08);
                padding: 10px 12px;
                font-size: 12px;
                font-weight: 800;
            }
            QTableWidget#tablaHistorialPagos QHeaderView::section:last {
                border-top-right-radius: """
            + str(radio_panel_tabla)
            + """px;
            }
            QTableWidget#tablaHistorialPagos::item {
                padding: 9px 12px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.04);
            }
            QLabel#iconoTarjetaResumen {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.10);
                border-radius: 12px;
            }
            QLabel#tituloTarjetaResumen {
                color: rgba(235, 242, 248, 0.72);
                font-size: 11px;
                font-weight: 700;
            }
            QLabel#valorTarjetaResumen {
                color: #ffffff;
                font-size: 20px;
                font-weight: 900;
            }
            QLabel#detalleTarjetaResumen,
            QLabel#textoPieHistorialPagos {
                color: rgba(235, 242, 248, 0.76);
                font-size: 11px;
                font-weight: 600;
            }
            QLineEdit,
            QComboBox,
            QDateEdit#campoFechaHistorialPago {
                min-height: 36px;
                border: 1px solid rgba(255, 255, 255, 0.18);
                border-radius: 12px;
                background: rgba(255, 255, 255, 0.11);
                color: #f5fbff;
                padding: 0 10px;
                font-size: 12px;
            }
            QLineEdit:focus,
            QComboBox:focus,
            QDateEdit#campoFechaHistorialPago:focus {
                border-color: rgba(109, 241, 220, 0.42);
                background: rgba(255, 255, 255, 0.16);
            }
            QPushButton#chipFiltroHistorialPago {
                min-height: 30px;
                border-radius: 11px;
                padding: 0 12px;
                background: rgba(255, 255, 255, 0.06);
                border: 1px solid rgba(255, 255, 255, 0.14);
                color: #ecf5ff;
                font-size: 11px;
                font-weight: 700;
            }
            QPushButton#chipFiltroHistorialPago:hover {
                background: rgba(255, 255, 255, 0.12);
            }
            QPushButton#chipFiltroHistorialPago:checked {
                color: #0f2d43;
                background: #d2f4f2;
                border-color: rgba(255, 255, 255, 0.18);
            }
            QWidget#contenedorAccionesHistorialPago {
                background: transparent;
            }
            QToolButton#botonIconoFilaHistorial {
                background: transparent;
                border: none;
                border-radius: 8px;
                padding: 0px;
                margin: 0px;
            }
            QToolButton#botonIconoFilaHistorial:hover {
                background: transparent;
                border: none;
            }
            QLabel#estadoVacioHistorialPagos {
                color: rgba(235, 242, 248, 0.76);
                font-size: 12px;
                font-weight: 700;
                padding: 20px 14px;
            }
            QLabel {
                color: #f4fbff;
            }
            """
        )
