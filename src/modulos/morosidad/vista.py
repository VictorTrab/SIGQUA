"""Vista PySide6 del modulo de morosidad."""

from __future__ import annotations

from typing import Callable

from PySide6.QtCore import QDate, QElapsedTimer, QEvent, QSize, Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QButtonGroup,
    QCheckBox,
    QComboBox,
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
    ContenedorTarjetasResumenOperativo,
    DialogoBaseSigqua,
    DialogoMensajeSigqua,
    TarjetaResumenOperativa,
    configurar_tabla_operativa,
    crear_boton_operativo,
    crear_item_tabla,
    obtener_estilo_detalle_sigqua,
    obtener_icono_tabler_coloreado,
    resolver_variante_boton_modal,
)
from comun.ui.temas import (
    TEMA_SIGQUA_PREDETERMINADO,
    obtener_fondo_header_destacado,
    obtener_paleta_tema,
    resolver_nombre_tema,
)
from modulos.morosidad.entidades import (
    DetalleMorosidad,
    FILTRO_MOROSIDAD_LEVE,
    FILTRO_MOROSIDAD_LISTO_CORTE,
    FILTRO_MOROSIDAD_MEDIA,
    FILTRO_MOROSIDAD_SEVERA,
    FILTRO_MOROSIDAD_TODOS,
    FilaMorosidad,
    PaginaMorosidad,
    ResumenMorosidad,
)


class TarjetaResumenMorosidad(TarjetaResumenOperativa):
    """Adaptador del resumen comun para mantener nombres del modulo."""


class BotonIconoFilaMorosidad(QToolButton):
    """Boton compacto de acciones por fila."""

    COLOR_BASE = "#c8d6f1"
    INTERVALO_TOOLTIP_MS = 1600

    def __init__(self, icono: str, color_hover: str, tooltip: str) -> None:
        super().__init__()
        self._icono = icono
        self._color_hover = color_hover
        self._temporizador_tooltip = QElapsedTimer()
        self.setObjectName("botonIconoFilaMorosidad")
        self.setToolTip(tooltip)
        self.setToolTipDuration(1400)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setAutoRaise(True)
        self.setFixedSize(32, 32)
        self.setIconSize(QSize(18, 18))
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
        self._actualizar_icono(self.COLOR_BASE)
        super().leaveEvent(evento)

    def aplicar_tema(self, nombre_tema: str) -> None:
        paleta = obtener_paleta_tema(nombre_tema)
        self._actualizar_icono(str(paleta["icono_fila_base"]))

    def _actualizar_icono(self, color_icono: str) -> None:
        self.setIcon(obtener_icono_tabler_coloreado(self._icono, color_icono, tamano=18))


class DialogoDetalleMorosidad(DialogoBaseSigqua):
    """Detalle operativo del abonado en mora."""

    def __init__(
        self,
        detalle: DetalleMorosidad,
        formateador_moneda: Callable[[int], str],
        formateador_fecha: Callable[[str], str],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._detalle = detalle
        self._formateador_moneda = formateador_moneda
        self._formateador_fecha = formateador_fecha
        self._accion = "cerrar"
        self.setMinimumWidth(860)
        self.setMinimumHeight(660)
        self._construir_ui()

    @property
    def accion_resultado(self) -> str:
        return self._accion

    def _construir_ui(self) -> None:
        titulo = QLabel("Detalle de morosidad")
        titulo.setObjectName("tituloDialogoSigqua")
        descripcion = QLabel(
            "Consulta las casas vinculadas al abonado, el vencimiento más antiguo y la deuda operativa actual."
        )
        descripcion.setObjectName("descripcionDialogoSigqua")
        descripcion.setWordWrap(True)

        scroll = QScrollArea()
        scroll.setObjectName("scrollDetalleMorosidad")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.viewport().setAutoFillBackground(False)

        contenedor = QWidget()
        contenedor.setObjectName("contenedorScrollDetalleMorosidad")
        contenedor.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        layout_scroll = QVBoxLayout(contenedor)
        layout_scroll.setContentsMargins(0, 0, 0, 0)
        layout_scroll.setSpacing(12)

        panel = QFrame()
        panel.setObjectName("panelDetalleMorosidad")
        layout_panel = QVBoxLayout(panel)
        layout_panel.setContentsMargins(18, 18, 18, 18)
        layout_panel.setSpacing(12)

        layout_panel.addWidget(
            self._crear_seccion_campos(
                "Identificación del abonado",
                (
                    ("Abonado", self._detalle.abonado_nombre),
                    ("DNI", self._detalle.abonado_dni),
                    ("Casas con mora", str(len(self._detalle.casas))),
                ),
            )
        )
        for casa in self._detalle.casas:
            layout_panel.addWidget(self._crear_seccion_casa(casa))

        fila_acciones = QHBoxLayout()
        boton_cerrar = BotonAccionContextual(
            "Cerrar",
            icono="x.svg",
            variante=resolver_variante_boton_modal("Cerrar", "neutro"),
            centrado=True,
            mostrar_icono=True,
        )
        boton_emitir = BotonAccionContextual(
            "Emitir deuda",
            icono="receipt-2.svg",
            variante=resolver_variante_boton_modal("Emitir deuda", "informacion"),
            centrado=True,
            mostrar_icono=True,
        )
        boton_cerrar.clicked.connect(self.reject)
        boton_emitir.clicked.connect(self._solicitar_documento)
        fila_acciones.addWidget(boton_cerrar)
        fila_acciones.addStretch(1)
        fila_acciones.addWidget(boton_emitir)

        layout_scroll.addWidget(panel)
        layout_scroll.addStretch(1)
        scroll.setWidget(contenedor)
        self.layout_cabecera.addWidget(titulo)
        self.layout_cabecera.addWidget(descripcion)
        self.layout_cuerpo.addWidget(scroll)
        self.layout_pie.addLayout(fila_acciones)
        self._aplicar_estilos()

    def _crear_seccion_campos(self, titulo: str, filas: tuple[tuple[str, str], ...]) -> QFrame:
        bloque = QFrame()
        bloque.setObjectName("seccionDetalleMorosidad")
        layout = QVBoxLayout(bloque)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)
        label_titulo = QLabel(titulo)
        label_titulo.setObjectName("tituloSeccionMorosidad")
        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(12)
        for indice, (etiqueta, valor) in enumerate(filas):
            grid.addWidget(self._crear_campo(etiqueta, valor), indice // 2, indice % 2)
        layout.addWidget(label_titulo)
        layout.addLayout(grid)
        return bloque

    def _crear_seccion_casa(self, casa: object) -> QFrame:
        bloque = QFrame()
        bloque.setObjectName("seccionDetalleMorosidad")
        layout = QVBoxLayout(bloque)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)
        titulo = QLabel(f"{casa.casa_codigo} · {casa.barrio_nombre or 'Sin barrio'}")
        titulo.setObjectName("tituloSeccionMorosidad")
        detalle = QLabel(
            f"{casa.direccion_casa or 'Sin referencia'} | Estado {casa.estado_servicio} | "
            f"Vencido desde {self._formateador_fecha(casa.vencimiento_mas_antiguo)} | "
            f"{casa.dias_en_mora} dia(s) en mora | Prioridad {casa.prioridad}"
        )
        detalle.setObjectName("descripcionSeccionMorosidad")
        detalle.setWordWrap(True)
        tabla = QTableWidget(0, 3)
        tabla.setObjectName("tablaDetalleMorosidad")
        configurar_tabla_operativa(tabla, ["Concepto", "Vencimiento", "Saldo"])
        tabla.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        tabla.setAlternatingRowColors(True)
        tabla.setFrameShape(QFrame.Shape.NoFrame)
        tabla.setViewportMargins(0, 0, 0, 18)
        tabla.viewport().setObjectName("viewportTablaDetalleMorosidad")
        tabla.viewport().setAutoFillBackground(False)
        tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        tabla.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        tabla.setRowCount(len(casa.lineas_detalle))
        for fila, linea in enumerate(casa.lineas_detalle):
            tabla.setItem(fila, 0, crear_item_tabla(linea.descripcion))
            tabla.setItem(fila, 1, crear_item_tabla(self._formateador_fecha(linea.fecha_vencimiento)))
            tabla.setItem(fila, 2, crear_item_tabla(self._formateador_moneda(linea.saldo_pendiente_centavos)))
        tabla.resizeRowsToContents()
        totales = self._crear_seccion_campos(
            "Totales de la casa",
            (
                ("Meses vencidos", str(casa.meses_vencidos)),
                ("Dias en mora", str(casa.dias_en_mora)),
                ("Prioridad", casa.prioridad),
                ("Deuda base", self._formateador_moneda(casa.deuda_base_centavos)),
                ("Recargo mora", self._formateador_moneda(casa.recargo_mora_centavos)),
                ("Total casa", self._formateador_moneda(casa.deuda_total_centavos)),
            ),
        )
        layout.addWidget(titulo)
        layout.addWidget(detalle)
        layout.addWidget(tabla)
        layout.addWidget(totales)
        return bloque

    def _crear_campo(self, etiqueta: str, valor: str) -> QFrame:
        bloque = QFrame()
        bloque.setObjectName("campoDetalleMorosidad")
        layout = QVBoxLayout(bloque)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(4)
        label = QLabel(etiqueta)
        label.setObjectName("etiquetaCampoMorosidad")
        contenido = QLabel(valor)
        contenido.setObjectName("valorCampoMorosidad")
        contenido.setWordWrap(True)
        layout.addWidget(label)
        layout.addWidget(contenido)
        return bloque

    def _solicitar_documento(self) -> None:
        self._accion = "emitir"
        self.accept()

    def _aplicar_estilos(self) -> None:
        paleta = self._paleta_tema
        self.setStyleSheet(
            self.styleSheet()
            + f"""
            QScrollArea#scrollDetalleMorosidad {{
                background: transparent;
                border: none;
            }}
            QWidget#contenedorScrollDetalleMorosidad {{
                background: transparent;
                border: none;
            }}
            QFrame#panelDetalleMorosidad {{
                background: {paleta["fondo_dialogo"]};
                border: 1px solid {paleta["borde_principal"]};
                border-radius: 4px;
            }}
            QFrame#seccionDetalleMorosidad {{
                background: {paleta["fondo_superficie"]};
                border: 1px solid {paleta["borde_principal"]};
                border-radius: 4px;
            }}
            QFrame#campoDetalleMorosidad {{
                background: {paleta["fondo_superficie_suave"]};
                border: 1px solid {paleta["borde_suave"]};
                border-radius: 4px;
            }}
            QLabel#tituloSeccionMorosidad {{
                color: {paleta["texto_principal"]};
                font-size: 14px;
                font-weight: 800;
            }}
            QLabel#descripcionSeccionMorosidad,
            QLabel#etiquetaCampoMorosidad {{
                color: {paleta["texto_suave"]};
                font-size: 11px;
                font-weight: 600;
            }}
            QLabel#valorCampoMorosidad {{
                color: {paleta["texto_principal"]};
                font-size: 13px;
                font-weight: 700;
            }}
            """
            + obtener_estilo_detalle_sigqua(self._nombre_tema)
            + f"""
            QTableWidget#tablaDetalleMorosidad {{
                background: {paleta["fondo_tabla_cuerpo"]};
                border: 1px solid {paleta["borde_tabla"]};
                border-radius: 4px;
            }}
            QTableWidget#tablaDetalleMorosidad QHeaderView::section {{
                background: {paleta["fondo_tabla_header_destacado"]};
                color: {paleta["texto_input"]};
                border: none;
                border-right: 1px solid {paleta["borde_tabla"]};
                border-bottom: 1px solid {paleta["borde_tabla"]};
                padding: 10px 12px;
                font-size: 12px;
                font-weight: 800;
            }}
            QTableWidget#tablaDetalleMorosidad::item {{
                background: {paleta["fondo_tabla_fila"]};
                border-bottom: 1px solid {paleta["borde_tabla"]};
            }}
            QTableWidget#tablaDetalleMorosidad::item:alternate {{
                background: {paleta["fondo_tabla_fila_alterna"]};
            }}
            QTableWidget#tablaDetalleMorosidad::item:selected {{
                background: {paleta["fondo_tabla_seleccion"]};
            }}
            QScrollBar:vertical {{
                background: transparent;
                width: 10px;
                margin: 2px;
            }}
            QScrollBar::handle:vertical {{
                background: {paleta["borde_chip_activo"]};
                border-radius: 5px;
                min-height: 28px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {paleta["acento_hover"]};
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical,
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {{
                background: transparent;
                border: none;
                height: 0px;
            }}
            """
        )


class DialogoSeleccionDocumentoMorosidad(DialogoBaseSigqua):
    """Permite elegir casas especificas o emitir deuda total del abonado."""

    def __init__(self, detalle: DetalleMorosidad, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._detalle = detalle
        self._casas: dict[int, QCheckBox] = {}
        self._emitir_total = False
        self.setMinimumWidth(640)
        self._construir_ui()

    @property
    def seleccion(self) -> tuple[bool, tuple[int, ...]]:
        seleccionadas = tuple(
            casa_id for casa_id, check in self._casas.items() if check.isChecked()
        )
        return self._emitir_total, seleccionadas

    def _construir_ui(self) -> None:
        titulo = QLabel("Emitir documento de deuda")
        titulo.setObjectName("tituloDialogoSigqua")
        descripcion = QLabel(
            "Selecciona casas específicas del abonado o genera el consolidado total con toda la deuda vigente."
        )
        descripcion.setObjectName("descripcionDialogoSigqua")
        descripcion.setWordWrap(True)

        total = QCheckBox("Emitir deuda total del abonado")
        total.setObjectName("checkMorosidadDocumento")
        total.stateChanged.connect(self._alternar_total)

        panel = QFrame()
        panel.setObjectName("panelSeleccionDocumentoMorosidad")
        layout_panel = QVBoxLayout(panel)
        layout_panel.setContentsMargins(14, 14, 14, 14)
        layout_panel.setSpacing(10)
        for casa in self._detalle.casas:
            check = QCheckBox(
                f"{casa.casa_codigo} · {casa.barrio_nombre or 'Sin barrio'} · {casa.meses_vencidos} mes(es)"
            )
            check.setObjectName("checkMorosidadDocumento")
            self._casas[casa.casa_id] = check
            layout_panel.addWidget(check)

        boton_cancelar = BotonAccionContextual(
            "Cancelar",
            variante=resolver_variante_boton_modal("Cancelar", "neutro"),
            centrado=True,
            mostrar_icono=False,
        )
        boton_emitir = BotonAccionContextual(
            "Generar documento",
            icono="receipt-2.svg",
            variante=resolver_variante_boton_modal("Generar documento", "informacion"),
            centrado=True,
            mostrar_icono=True,
        )
        boton_cancelar.clicked.connect(self.reject)
        boton_emitir.clicked.connect(self._validar_y_aceptar)
        fila = QHBoxLayout()
        fila.addWidget(boton_cancelar)
        fila.addStretch(1)
        fila.addWidget(boton_emitir)

        self.layout_cabecera.addWidget(titulo)
        self.layout_cabecera.addWidget(descripcion)
        self.layout_cuerpo.addWidget(total)
        self.layout_cuerpo.addWidget(panel)
        self.layout_pie.addLayout(fila)

    def _alternar_total(self, estado: int) -> None:
        self._emitir_total = estado == int(Qt.CheckState.Checked.value)
        for check in self._casas.values():
            check.setEnabled(not self._emitir_total)

    def _validar_y_aceptar(self) -> None:
        emitir_total, casas = self.seleccion
        if not emitir_total and not casas:
            DialogoMensajeSigqua(
                titulo="Seleccion requerida",
                mensaje="Selecciona al menos una casa o usa la opcion de total del abonado.",
                texto_boton="Entendido",
                parent=self,
            ).exec()
            return
        self.accept()


class VistaMorosidad(QWidget):
    """Listado operativo de morosidad con detalle y emision documental."""

    filtro_texto_cambiado = Signal(str)
    filtro_severidad_cambiado = Signal(str)
    pagina_cambiada = Signal(int)
    detalle_solicitado = Signal(int)
    emitir_documento_solicitado = Signal(int)

    DURACION_MENSAJE_MS = 3200

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("vistaMorosidad")
        self._tema_actual = TEMA_SIGQUA_PREDETERMINADO
        self._paleta = obtener_paleta_tema(self._tema_actual)
        self._timer_mensaje = QTimer(self)
        self._timer_mensaje.setSingleShot(True)
        self._timer_mensaje.timeout.connect(self._ocultar_mensaje)
        self._fila_por_abonado: dict[int, int] = {}
        self._item_por_casa: dict[int, FilaMorosidad] = {}
        self._filtro_severidad_actual = FILTRO_MOROSIDAD_TODOS
        self._construir_ui()
        self._aplicar_estilos()

    def mostrar_resumen(self, resumen: ResumenMorosidad, formatear_moneda: Callable[[int], str]) -> None:
        self._tarjeta_total.actualizar("Casas con mora", str(resumen.total_casas), "Filas activas en el listado.")
        self._tarjeta_abonados.actualizar(
            "Abonados afectados",
            str(resumen.total_abonados),
            "Abonados con al menos una casa vencida.",
        )
        self._tarjeta_total_deuda.actualizar(
            "Deuda total vencida",
            formatear_moneda(resumen.deuda_total_centavos),
            f"Base {formatear_moneda(resumen.deuda_base_centavos)} | Mora {formatear_moneda(resumen.recargo_mora_centavos)}",
        )
        self._tarjeta_severos.actualizar(
            "Casos severos",
            str(resumen.casos_severos),
            "Casas sobre el umbral más alto de mora.",
        )

    def mostrar_listado(
        self,
        pagina: PaginaMorosidad,
        formatear_moneda: Callable[[int], str],
        formatear_fecha: Callable[[str], str],
    ) -> None:
        self._tabla.setRowCount(len(pagina.items))
        self._fila_por_abonado.clear()
        self._item_por_casa.clear()
        for fila, item in enumerate(pagina.items):
            self._fila_por_abonado[item.abonado_id] = fila
            self._item_por_casa[item.casa_id] = item
            valores = (
                item.casa_codigo,
                item.abonado_nombre,
                item.barrio_nombre,
                item.meses_vencidos,
                item.dias_en_mora,
                item.prioridad,
                formatear_moneda(item.deuda_total_centavos),
                formatear_fecha(item.vencimiento_mas_antiguo),
            )
            for columna, valor in enumerate(valores):
                tabla_item = crear_item_tabla(valor)
                tabla_item.setData(Qt.ItemDataRole.UserRole, item.abonado_id)
                self._tabla.setItem(fila, columna, tabla_item)
            self._tabla.setCellWidget(fila, 8, self._crear_acciones_fila(item))
        self._tabla.resizeRowsToContents()
        self._label_paginacion.setText(
            f"Mostrando {pagina.indice_inicio}-{pagina.indice_fin} de {pagina.total_registros} registros"
        )
        self._boton_anterior.setEnabled(pagina.pagina_actual > 1)
        self._boton_siguiente.setEnabled(pagina.pagina_actual < pagina.total_paginas)
        self._pagina_actual = pagina.pagina_actual

    def establecer_filtro_severidad(self, severidad: str) -> None:
        self._filtro_severidad_actual = severidad
        for codigo, boton in self._botones_filtro.items():
            boton.setChecked(codigo == severidad)

    def mostrar_mensaje(self, mensaje: str, es_error: bool = False) -> None:
        self._mensaje.setText(mensaje)
        self._mensaje.setProperty("estado", "error" if es_error else "exito")
        self._mensaje.style().unpolish(self._mensaje)
        self._mensaje.style().polish(self._mensaje)
        self._mensaje.setVisible(True)
        self._timer_mensaje.start(self.DURACION_MENSAJE_MS)

    def mostrar_detalle(
        self,
        detalle: DetalleMorosidad,
        formateador_moneda: Callable[[int], str],
        formateador_fecha: Callable[[str], str],
    ) -> str:
        dialogo = DialogoDetalleMorosidad(
            detalle=detalle,
            formateador_moneda=formateador_moneda,
            formateador_fecha=formateador_fecha,
            parent=self,
        )
        dialogo.exec()
        return dialogo.accion_resultado

    def seleccionar_casas_documento(self, detalle: DetalleMorosidad) -> tuple[bool, tuple[int, ...]] | None:
        dialogo = DialogoSeleccionDocumentoMorosidad(detalle=detalle, parent=self)
        if dialogo.exec() != int(QDialog.DialogCode.Accepted):
            return None
        return dialogo.seleccion

    def _construir_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 6)
        layout.setSpacing(12)

        self._mensaje = QLabel("")
        self._mensaje.setObjectName("mensajeMorosidad")
        self._mensaje.setVisible(False)
        self._mensaje.setWordWrap(True)
        layout.addWidget(self._mensaje)

        contenedor_tarjetas = ContenedorTarjetasResumenOperativo()
        self._tarjeta_total = TarjetaResumenMorosidad("home-2.svg", "#facc15")
        self._tarjeta_abonados = TarjetaResumenMorosidad("users.svg", "#7dd3fc")
        self._tarjeta_total_deuda = TarjetaResumenMorosidad("urgent.svg", "#fb923c")
        self._tarjeta_severos = TarjetaResumenMorosidad("alert-triangle.svg", "#f87171")
        contenedor_tarjetas.establecer_tarjetas(
            (self._tarjeta_total, self._tarjeta_abonados, self._tarjeta_total_deuda, self._tarjeta_severos)
        )
        layout.addWidget(contenedor_tarjetas)

        panel_filtros = QFrame()
        panel_filtros.setObjectName("panelFiltrosMorosidad")
        layout_filtros = QVBoxLayout(panel_filtros)
        layout_filtros.setContentsMargins(16, 16, 16, 16)
        layout_filtros.setSpacing(12)
        fila_superior = QHBoxLayout()
        self._input_busqueda = QLineEdit()
        self._input_busqueda.setPlaceholderText("Buscar por abonado, DNI, casa, barrio o direccion")
        self._input_busqueda.returnPressed.connect(self._emitir_filtro_texto)
        boton_buscar = crear_boton_operativo("Buscar")
        boton_buscar.clicked.connect(self._emitir_filtro_texto)
        fila_superior.addWidget(self._input_busqueda, 1)
        fila_superior.addWidget(boton_buscar)
        layout_filtros.addLayout(fila_superior)

        fila_filtros = QHBoxLayout()
        fila_filtros.setSpacing(8)
        self._grupo_severidad = QButtonGroup(self)
        self._grupo_severidad.setExclusive(True)
        self._botones_filtro: dict[str, QPushButton] = {}
        for codigo, etiqueta in (
            (FILTRO_MOROSIDAD_TODOS, "Todos"),
            (FILTRO_MOROSIDAD_LEVE, "Baja"),
            (FILTRO_MOROSIDAD_MEDIA, "Media"),
            (FILTRO_MOROSIDAD_SEVERA, "Alta"),
            (FILTRO_MOROSIDAD_LISTO_CORTE, "Critica"),
        ):
            boton = QPushButton(etiqueta)
            boton.setCheckable(True)
            boton.setObjectName("chipFiltroMorosidad")
            boton.clicked.connect(
                lambda checked=False, codigo_filtro=codigo: self._emitir_filtro_severidad(codigo_filtro)
            )
            self._grupo_severidad.addButton(boton)
            self._botones_filtro[codigo] = boton
            fila_filtros.addWidget(boton)
        fila_filtros.addStretch(1)
        layout_filtros.addLayout(fila_filtros)
        layout.addWidget(panel_filtros)

        panel_tabla = QFrame()
        panel_tabla.setObjectName("panelTablaMorosidad")
        layout_tabla = QVBoxLayout(panel_tabla)
        layout_tabla.setContentsMargins(14, 14, 14, 14)
        layout_tabla.setSpacing(10)

        self._tabla = QTableWidget()
        configurar_tabla_operativa(
            self._tabla,
            ["Casa", "Abonado", "Barrio", "Meses", "Dias", "Prioridad", "Total", "Mas antiguo", "Acciones"],
        )
        self._tabla.setObjectName("tablaMorosidad")
        self._tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._tabla.verticalHeader().setDefaultSectionSize(52)
        self._tabla.setAlternatingRowColors(True)
        self._tabla.setFrameShape(QFrame.Shape.NoFrame)
        self._tabla.setViewportMargins(0, 0, 0, 18)
        self._tabla.viewport().setObjectName("viewportTablaMorosidad")
        self._tabla.viewport().setAutoFillBackground(False)
        self._tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._tabla.horizontalHeader().setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents)
        layout_tabla.addWidget(self._tabla)

        fila_pie = QHBoxLayout()
        self._label_paginacion = QLabel("Mostrando 0-0 de 0 registros")
        self._label_paginacion.setObjectName("textoPaginacionMorosidad")
        self._boton_anterior = crear_boton_operativo("Anterior")
        self._boton_siguiente = crear_boton_operativo("Siguiente")
        self._boton_anterior.clicked.connect(lambda: self.pagina_cambiada.emit(max(1, self._pagina_actual - 1)))
        self._boton_siguiente.clicked.connect(lambda: self.pagina_cambiada.emit(self._pagina_actual + 1))
        fila_pie.addWidget(self._label_paginacion)
        fila_pie.addStretch(1)
        fila_pie.addWidget(self._boton_anterior)
        fila_pie.addWidget(self._boton_siguiente)
        layout_tabla.addLayout(fila_pie)
        layout.addWidget(panel_tabla, 1)
        self.establecer_filtro_severidad(FILTRO_MOROSIDAD_TODOS)
        self._pagina_actual = 1

    def _crear_acciones_fila(self, item: FilaMorosidad) -> QWidget:
        contenedor = QWidget()
        contenedor.setObjectName("contenedorAccionesMorosidad")
        layout = QHBoxLayout(contenedor)
        layout.setContentsMargins(4, 0, 4, 0)
        layout.setSpacing(4)
        boton_detalle = BotonIconoFilaMorosidad("eye.svg", "#8be9fd", "Ver detalle")
        boton_emitir = BotonIconoFilaMorosidad("receipt-2.svg", "#facc15", "Emitir deuda")
        boton_detalle.clicked.connect(lambda: self.detalle_solicitado.emit(item.abonado_id))
        boton_emitir.clicked.connect(lambda: self.emitir_documento_solicitado.emit(item.abonado_id))
        layout.addWidget(boton_detalle)
        layout.addWidget(boton_emitir)
        layout.addStretch(1)
        return contenedor

    def _emitir_filtro_texto(self) -> None:
        self.filtro_texto_cambiado.emit(self._input_busqueda.text().strip())

    def _emitir_filtro_severidad(self, severidad: str) -> None:
        self._filtro_severidad_actual = severidad
        self.filtro_severidad_cambiado.emit(severidad)

    def _ocultar_mensaje(self) -> None:
        self._mensaje.clear()
        self._mensaje.setVisible(False)

    def aplicar_tema(self, nombre_tema: str) -> None:
        self._tema_actual = (
            resolver_nombre_tema(nombre_tema)
        )
        self._paleta = obtener_paleta_tema(self._tema_actual)
        for boton in self.findChildren(BotonIconoFilaMorosidad):
            boton.aplicar_tema(self._tema_actual)
        self._aplicar_estilos()

    def _aplicar_estilos(self) -> None:
        paleta = self._paleta
        fondo_panel_destacado = obtener_fondo_header_destacado(self._tema_actual)
        borde_panel_destacado = paleta["borde_principal"]
        self.setStyleSheet(
            f"""
            QWidget#vistaMorosidad {{
                background: transparent;
                color: {paleta["texto_principal"]};
                font-family: "{paleta["familia_tipografica"]}";
            }}
            QLabel#mensajeMorosidad {{
                background: {paleta["fondo_exito"]};
                border: 1px solid {paleta["borde_exito"]};
                border-radius: 12px;
                color: {paleta["texto_exito"]};
                padding: 10px 12px;
                font-size: {paleta["tamano_fuente_base"] + 2}px;
                font-weight: {paleta["peso_subtitulo"]};
            }}
            QLabel#mensajeMorosidad[estado="error"] {{
                background: {paleta["fondo_error"]};
                border-color: {paleta["borde_error"]};
                color: {paleta["texto_error"]};
            }}
            QFrame#tarjetaResumenMorosidad,
            QFrame#panelFiltrosMorosidad,
            QFrame#panelTablaMorosidad,
            QFrame#panelSeleccionDocumentoMorosidad {{
                background: {fondo_panel_destacado};
                border: 1px solid {borde_panel_destacado};
                border-radius: 18px;
            }}
            QLabel#tituloTarjetaResumenMorosidad,
            QLabel#detalleTarjetaResumenMorosidad,
            QLabel#textoPaginacionMorosidad {{
                color: {paleta["texto_secundario"]};
                font-size: 11px;
            }}
            QLabel#valorTarjetaResumenMorosidad {{
                color: {paleta["texto_principal"]};
                font-size: {paleta["tamano_titulo_tarjeta"] + 2}px;
                font-weight: {paleta["peso_titulo"]};
            }}
            QLabel#iconoTarjetaResumenMorosidad {{
                background: {paleta["fondo_superficie_muy_suave"]};
                border-radius: 12px;
            }}
            QLineEdit {{
                min-height: 38px;
                border: 1px solid {paleta["borde_medio"]};
                border-radius: 12px;
                background: {paleta["fondo_input"]};
                color: {paleta["texto_input"]};
                padding: 0 12px;
            }}
            QLineEdit:focus {{
                border-color: {paleta["borde_foco_input"]};
                background: {paleta["fondo_input_focus"]};
            }}
            QPushButton#chipFiltroMorosidad {{
                min-height: 30px;
                padding: 0 14px;
                border-radius: 11px;
                border: 1px solid {paleta["borde_suave"]};
                background: {paleta["fondo_chip"]};
                color: {paleta["texto_chip"]};
                font-size: 11px;
                font-weight: 700;
            }}
            QPushButton#chipFiltroMorosidad:hover {{
                background: {paleta["fondo_chip_hover"]};
                color: {paleta["texto_principal"]};
            }}
            QPushButton#chipFiltroMorosidad:checked {{
                background: {paleta["fondo_chip_activo"]};
                border-color: {paleta["borde_chip_activo"]};
                color: {paleta["texto_chip_activo"]};
            }}
            QTableWidget#tablaMorosidad,
            QTableWidget#tablaDetalleMorosidad {{
                background: {paleta["fondo_tabla_cuerpo"]};
                background-clip: padding;
                alternate-background-color: {paleta["fondo_tabla_fila_alterna"]};
                border: none;
                border-radius: 18px;
                padding: 0 0 18px 0;
                color: {paleta["texto_input"]};
                gridline-color: {paleta["borde_tabla"]};
            }}
            QWidget#viewportTablaMorosidad {{
                background: transparent;
                border: none;
                border-bottom-left-radius: 18px;
                border-bottom-right-radius: 18px;
            }}
            QWidget#viewportTablaDetalleMorosidad {{
                background: transparent;
                border: none;
                border-bottom-left-radius: 18px;
                border-bottom-right-radius: 18px;
            }}
            QTableWidget#tablaMorosidad::item,
            QTableWidget#tablaDetalleMorosidad::item {{
                padding: 8px;
                background: {paleta["fondo_tabla_fila"]};
                border-bottom: 1px solid {paleta["borde_tabla"]};
            }}
            QTableWidget#tablaMorosidad::item:alternate,
            QTableWidget#tablaDetalleMorosidad::item:alternate {{
                background: {paleta["fondo_tabla_fila_alterna"]};
            }}
            QTableWidget#tablaMorosidad::item:selected,
            QTableWidget#tablaDetalleMorosidad::item:selected {{
                background: {paleta["fondo_tabla_seleccion"]};
                color: {paleta["texto_input"]};
            }}
            QTableWidget#tablaMorosidad QHeaderView::section:first,
            QTableWidget#tablaDetalleMorosidad QHeaderView::section:first {{
                border-top-left-radius: 18px;
            }}
            QHeaderView::section {{
                background: {paleta["fondo_tabla_header_destacado"]};
                color: {paleta["texto_input"]};
                border: none;
                border-right: 1px solid {paleta["borde_tabla"]};
                border-bottom: 1px solid {paleta["borde_tabla"]};
                padding: 10px 8px;
                font-size: 11px;
                font-weight: {paleta["peso_titulo"]};
            }}
            QTableWidget#tablaMorosidad QHeaderView::section:last,
            QTableWidget#tablaDetalleMorosidad QHeaderView::section:last {{
                border-top-right-radius: 18px;
            }}
            QScrollArea,
            QScrollBar:vertical {{
                background: transparent;
            }}
            QScrollBar:vertical {{
                width: 10px;
                margin: 2px;
            }}
            QScrollBar::handle:vertical {{
                background: {paleta["borde_chip_activo"]};
                border-radius: 5px;
                min-height: 28px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {paleta["acento_hover"]};
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical,
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {{
                background: transparent;
                border: none;
                height: 0px;
            }}
            QCheckBox#checkMorosidadDocumento {{
                color: {paleta["texto_principal"]};
                font-size: 12px;
                font-weight: 600;
                spacing: 8px;
            }}
            QWidget#contenedorAccionesMorosidad {{
                background: transparent;
            }}
            QToolButton#botonIconoFilaMorosidad {{
                background: transparent;
                border: none;
                border-radius: 8px;
                padding: 0px;
                margin: 0px;
            }}
            QToolButton#botonIconoFilaMorosidad:hover {{
                background: transparent;
                border: none;
            }}
            """
        )
