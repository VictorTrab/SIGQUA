"""Vista PySide6 del modulo de casas."""

from __future__ import annotations

from typing import Callable, Iterable

from PySide6.QtCore import QElapsedTimer, QEvent, QSize, Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
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
    DialogoBaseSicap,
    DialogoConfirmacionSicap,
    aplicar_estilo_boton_operativo,
    configurar_tabla_operativa,
    crear_boton_operativo,
    crear_item_tabla,
    obtener_icono_tabler_coloreado,
    resolver_variante_boton_modal,
)
from comun.ui.componentes import RADIO_TARJETA_DIALOGO
from comun.ui.temas import TEMA_SICAP_PREDETERMINADO, obtener_paleta_tema
from modulos.casas.entidades import (
    Casa,
    DetalleCasa,
    FILTRO_CASAS_ACTIVAS,
    FILTRO_CASAS_CON_MORA,
    FILTRO_CASAS_SIN_PROPIETARIO,
    FILTRO_CASAS_SUSPENDIDAS,
    FILTRO_CASAS_TODAS,
    FormularioCasa,
    HistorialPropietarioCasa,
    OpcionAbonado,
    OpcionBarrio,
    PaginaCasas,
    ResumenCasas,
)


class TarjetaResumenCasa(QFrame):
    """Tarjeta de resumen para el encabezado del modulo."""

    def __init__(self, icono: str, color_icono: str) -> None:
        super().__init__()
        self.setObjectName("tarjetaResumenCasas")
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


class BotonIconoFilaCasa(QToolButton):
    """Boton de accion compacto para filas del listado."""

    COLOR_BASE = "#c8d6f1"
    INTERVALO_TOOLTIP_MS = 1600

    def __init__(self, icono: str, color_hover: str, tooltip: str) -> None:
        super().__init__()
        self._icono = icono
        self._color_hover = color_hover
        self._color_base = self.COLOR_BASE
        self._temporizador_tooltip = QElapsedTimer()
        self.setObjectName("botonIconoFilaCasa")
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


class DialogoFormularioCasa(DialogoBaseSicap):
    """Modal para crear o editar casas."""

    def __init__(
        self,
        barrios: Iterable[OpcionBarrio],
        abonados: Iterable[OpcionAbonado],
        casa: Casa | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._barrios = list(barrios)
        self._abonados = list(abonados)
        self._casa = casa
        self.setMinimumWidth(640)
        self.setMinimumHeight(560)
        self._construir_ui()

    def obtener_formulario(self) -> FormularioCasa:
        barrio_id = self._combo_barrio.currentData()
        abonado_id = self._combo_abonado.currentData()
        return FormularioCasa(
            identificador=None if self._casa is None else self._casa.identificador,
            abonado_id=int(abonado_id) if abonado_id is not None else None,
            barrio_id=int(barrio_id) if barrio_id is not None else None,
            direccion_referencia=self._campo_direccion.toPlainText(),
            observaciones=self._campo_observaciones.toPlainText(),
            estado_servicio=self._combo_estado.currentText(),
        )

    def accept(self) -> None:
        if self._combo_abonado.currentData() is None:
            self._mensaje.setText("Selecciona un abonado valido para la casa.")
            self._mensaje.setVisible(True)
            return
        if self._combo_barrio.currentData() is None:
            self._mensaje.setText("Selecciona un barrio valido.")
            self._mensaje.setVisible(True)
            return
        self._mensaje.setVisible(False)
        super().accept()

    def _construir_ui(self) -> None:
        titulo = QLabel("Editar casa" if self._casa else "Nueva casa")
        titulo.setObjectName("tituloDialogoSicap")
        descripcion = QLabel(
            "Configura la casa, su barrio y el propietario operativo actual."
        )
        descripcion.setObjectName("descripcionDialogoSicap")
        descripcion.setWordWrap(True)

        formulario = QGridLayout()
        formulario.setContentsMargins(0, 0, 0, 0)
        formulario.setHorizontalSpacing(10)
        formulario.setVerticalSpacing(10)

        self._combo_abonado = QComboBox()
        self._combo_abonado.addItem("Selecciona un abonado", None)
        for abonado in self._abonados:
            self._combo_abonado.addItem(abonado.etiqueta, abonado.identificador)

        self._combo_barrio = QComboBox()
        self._combo_barrio.addItem("Selecciona un barrio", None)
        for barrio in self._barrios:
            self._combo_barrio.addItem(barrio.nombre, barrio.identificador)

        self._combo_estado = QComboBox()
        self._combo_estado.addItems(["ACTIVO", "CORTADO", "SUSPENDIDO", "INACTIVO"])
        self._campo_direccion = QPlainTextEdit()
        self._campo_direccion.setPlaceholderText("Direccion o referencia de la casa")
        self._campo_direccion.setFixedHeight(78)
        self._campo_observaciones = QPlainTextEdit()
        self._campo_observaciones.setPlaceholderText("Observaciones")
        self._campo_observaciones.setFixedHeight(78)

        if self._casa is not None:
            indice_abonado = self._combo_abonado.findData(self._casa.abonado_id)
            if indice_abonado < 0 and self._casa.abonado_id is not None:
                etiqueta_abonado = self._casa.resumen_propietario
                if self._casa.abonado_dni:
                    etiqueta_abonado = f"{etiqueta_abonado} | {self._casa.abonado_dni}"
                self._combo_abonado.addItem(etiqueta_abonado, self._casa.abonado_id)
                indice_abonado = self._combo_abonado.findData(self._casa.abonado_id)
            if indice_abonado >= 0:
                self._combo_abonado.setCurrentIndex(indice_abonado)
            indice_barrio = self._combo_barrio.findData(self._casa.barrio_id)
            if indice_barrio < 0 and self._casa.barrio_id is not None and self._casa.barrio_nombre:
                self._combo_barrio.addItem(self._casa.barrio_nombre, self._casa.barrio_id)
                indice_barrio = self._combo_barrio.findData(self._casa.barrio_id)
            if indice_barrio >= 0:
                self._combo_barrio.setCurrentIndex(indice_barrio)
            self._combo_estado.setCurrentText(self._casa.estado_servicio)
            self._campo_direccion.setPlainText(self._casa.direccion_referencia)
            self._campo_observaciones.setPlainText(self._casa.observaciones)
            self._combo_abonado.setEnabled(False)

        formulario.addWidget(
            self._crear_bloque_formulario("Abonado actual", self._combo_abonado),
            0,
            0,
            1,
            2,
        )
        formulario.addWidget(self._crear_bloque_formulario("Barrio", self._combo_barrio), 1, 0)
        formulario.addWidget(
            self._crear_bloque_formulario("Estado del servicio", self._combo_estado),
            1,
            1,
        )

        panel_datos = self._crear_panel_formulario(
            "Datos principales",
            "Define el propietario actual, barrio y estado de servicio.",
        )
        panel_datos.layout().addLayout(formulario)

        panel_notas = self._crear_panel_formulario(
            "Contexto operativo",
            "Completa la referencia de la casa y cualquier nota administrativa relevante.",
        )
        notas_layout = QVBoxLayout()
        notas_layout.setContentsMargins(0, 0, 0, 0)
        notas_layout.setSpacing(10)
        notas_layout.addWidget(
            self._crear_bloque_formulario("Referencia", self._campo_direccion)
        )
        notas_layout.addWidget(
            self._crear_bloque_formulario("Observaciones", self._campo_observaciones)
        )
        panel_notas.layout().addLayout(notas_layout)

        self._mensaje = QLabel("")
        self._mensaje.setObjectName("mensajeErrorDialogoSicap")
        self._mensaje.setVisible(False)

        fila_acciones = QHBoxLayout()
        fila_acciones.setSpacing(10)
        boton_cancelar = BotonAccionContextual(
            "Cancelar",
            variante=resolver_variante_boton_modal("Cancelar", "neutro"),
            centrado=True,
            mostrar_icono=False,
        )
        boton_guardar = BotonAccionContextual(
            "Guardar cambios",
            variante=resolver_variante_boton_modal("Guardar cambios", "primario"),
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

        self.layout_cabecera.addWidget(titulo)
        self.layout_cabecera.addWidget(descripcion)
        self.layout_cuerpo.addWidget(panel_datos)
        self.layout_cuerpo.addWidget(panel_notas)
        self.layout_cuerpo.addWidget(self._mensaje)
        self.layout_pie.addLayout(fila_acciones)

    def _crear_bloque_formulario(self, etiqueta: str, campo: QWidget) -> QWidget:
        bloque = QWidget()
        layout = QVBoxLayout(bloque)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        label = QLabel(etiqueta)
        label.setObjectName("etiquetaDatoDialogoSicap")
        layout.addWidget(label)
        layout.addWidget(campo)
        return bloque

    def _crear_panel_formulario(self, titulo: str, descripcion: str) -> QFrame:
        panel = QFrame()
        panel.setObjectName("bloqueDialogoSicap")
        layout_panel = QVBoxLayout(panel)
        layout_panel.setContentsMargins(14, 14, 14, 14)
        layout_panel.setSpacing(10)
        label_titulo = QLabel(titulo)
        label_titulo.setObjectName("etiquetaDatoDialogoSicap")
        label_descripcion = QLabel(descripcion)
        label_descripcion.setObjectName("descripcionDialogoSicap")
        label_descripcion.setWordWrap(True)
        layout_panel.addWidget(label_titulo)
        layout_panel.addWidget(label_descripcion)
        return panel


class DialogoCambioDuenoCasa(DialogoBaseSicap):
    """Modal para reasignar el propietario actual de una casa."""

    def __init__(
        self,
        casa: Casa,
        abonados: Iterable[OpcionAbonado],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._casa = casa
        self._abonados = [abonado for abonado in abonados if abonado.identificador != casa.abonado_id]
        self.setMinimumWidth(620)
        self.setMinimumHeight(520)
        self._construir_ui()

    @property
    def nuevo_abonado_id(self) -> int | None:
        valor = self._combo_abonado.currentData()
        return int(valor) if valor is not None else None

    @property
    def motivo(self) -> str:
        return self._campo_motivo.toPlainText().strip()

    def accept(self) -> None:
        if self._combo_abonado.currentData() is None:
            self._mensaje.setText("Selecciona el nuevo abonado.")
            self._mensaje.setVisible(True)
            return
        if not self.motivo:
            self._mensaje.setText("Indica el motivo del cambio de propietario.")
            self._mensaje.setVisible(True)
            return
        self._mensaje.setVisible(False)
        super().accept()

    def _construir_ui(self) -> None:
        titulo = QLabel("Cambiar dueno de casa")
        titulo.setObjectName("tituloDialogoSicap")
        descripcion = QLabel(
            "La deuda pendiente y el plan activo de la casa se migraran al nuevo abonado."
        )
        descripcion.setObjectName("descripcionDialogoSicap")
        descripcion.setWordWrap(True)

        resumen = QLabel(
            f"{self._casa.codigo} | {self._casa.resumen_propietario} | "
            f"{self._casa.barrio_nombre or 'Sin barrio'}"
        )
        resumen.setObjectName("descripcionDialogoSicap")
        resumen.setWordWrap(True)

        self._combo_abonado = QComboBox()
        self._combo_abonado.addItem("Selecciona el nuevo abonado", None)
        for abonado in self._abonados:
            if abonado.estado == "ACTIVO":
                self._combo_abonado.addItem(abonado.etiqueta, abonado.identificador)

        self._campo_motivo = QPlainTextEdit()
        self._campo_motivo.setPlaceholderText("Motivo u observacion del cambio")
        self._campo_motivo.setFixedHeight(96)

        panel_resumen = self._crear_panel_formulario(
            "Casa seleccionada",
            "Confirma la casa actual antes de transferir deuda y plan activo.",
        )
        panel_resumen.layout().addWidget(resumen)

        panel_destino = self._crear_panel_formulario(
            "Nuevo propietario",
            "Selecciona el abonado activo que asumira la casa y sus compromisos pendientes.",
        )
        panel_destino.layout().addWidget(
            self._crear_bloque_formulario("Nuevo abonado", self._combo_abonado)
        )

        panel_motivo = self._crear_panel_formulario(
            "Trazabilidad",
            "Deja constancia clara del motivo para mantener el historial administrativo.",
        )
        panel_motivo.layout().addWidget(self._crear_bloque_formulario("Motivo", self._campo_motivo))

        self._mensaje = QLabel("")
        self._mensaje.setObjectName("mensajeErrorDialogoSicap")
        self._mensaje.setVisible(False)

        fila_acciones = QHBoxLayout()
        fila_acciones.setSpacing(10)
        boton_cancelar = BotonAccionContextual(
            "Cancelar",
            variante=resolver_variante_boton_modal("Cancelar", "neutro"),
            centrado=True,
            mostrar_icono=False,
        )
        boton_confirmar = BotonAccionContextual(
            "Aplicar cambio",
            variante="edicion",
            centrado=True,
            mostrar_icono=False,
        )
        boton_cancelar.clicked.connect(self.reject)
        boton_confirmar.clicked.connect(self.accept)
        fila_acciones.addWidget(boton_cancelar)
        fila_acciones.addStretch(1)
        fila_acciones.addWidget(boton_confirmar)

        self.layout_cabecera.addWidget(titulo)
        self.layout_cabecera.addWidget(descripcion)
        self.layout_cuerpo.addWidget(panel_resumen)
        self.layout_cuerpo.addWidget(panel_destino)
        self.layout_cuerpo.addWidget(panel_motivo)
        self.layout_cuerpo.addWidget(self._mensaje)
        self.layout_pie.addLayout(fila_acciones)

    def _crear_bloque_formulario(self, etiqueta: str, campo: QWidget) -> QWidget:
        bloque = QWidget()
        layout = QVBoxLayout(bloque)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        label = QLabel(etiqueta)
        label.setObjectName("etiquetaDatoDialogoSicap")
        layout.addWidget(label)
        layout.addWidget(campo)
        return bloque

    def _crear_panel_formulario(self, titulo: str, descripcion: str) -> QFrame:
        panel = QFrame()
        panel.setObjectName("bloqueDialogoSicap")
        layout_panel = QVBoxLayout(panel)
        layout_panel.setContentsMargins(14, 14, 14, 14)
        layout_panel.setSpacing(10)
        label_titulo = QLabel(titulo)
        label_titulo.setObjectName("etiquetaDatoDialogoSicap")
        label_descripcion = QLabel(descripcion)
        label_descripcion.setObjectName("descripcionDialogoSicap")
        label_descripcion.setWordWrap(True)
        layout_panel.addWidget(label_titulo)
        layout_panel.addWidget(label_descripcion)
        return panel


class DialogoHistorialPropietariosCasa(DialogoBaseSicap):
    """Modal para consultar el historial de propietarios de una casa."""

    def __init__(
        self,
        casa: Casa,
        historial: Iterable[HistorialPropietarioCasa],
        formateador_fecha: Callable[[str], str],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._casa = casa
        self._historial = list(historial)
        self._formateador_fecha = formateador_fecha
        self.setMinimumWidth(860)
        self.setMinimumHeight(560)
        self._construir_ui()

    def _construir_ui(self) -> None:
        titulo = QLabel("Historial de propietarios")
        titulo.setObjectName("tituloDialogoSicap")
        descripcion = QLabel(
            f"Traza de cambios registrada para {self._casa.codigo}."
        )
        descripcion.setObjectName("descripcionDialogoSicap")
        descripcion.setWordWrap(True)

        tarjeta_resumen = QFrame()
        tarjeta_resumen.setObjectName("bloqueDialogoSicap")
        layout_resumen = QHBoxLayout(tarjeta_resumen)
        layout_resumen.setContentsMargins(14, 12, 14, 12)
        layout_resumen.setSpacing(14)
        layout_resumen.addWidget(self._crear_resumen_historial("Casa", self._casa.codigo))
        layout_resumen.addWidget(
            self._crear_resumen_historial("Propietario actual", self._casa.resumen_propietario),
            1,
        )
        layout_resumen.addWidget(
            self._crear_resumen_historial("Cambios", str(len(self._historial))),
        )

        panel_tabla = QFrame()
        panel_tabla.setObjectName("panelHistorialCasa")
        layout_panel_tabla = QVBoxLayout(panel_tabla)
        layout_panel_tabla.setContentsMargins(14, 14, 14, 14)
        layout_panel_tabla.setSpacing(10)

        encabezado_tabla = QVBoxLayout()
        encabezado_tabla.setContentsMargins(0, 0, 0, 0)
        encabezado_tabla.setSpacing(3)
        titulo_tabla = QLabel("Movimientos registrados")
        titulo_tabla.setObjectName("tituloSeccionDetalleCasa")
        subtitulo_tabla = QLabel(
            "Consulta la trazabilidad de cambios de propietario, motivo y usuario responsable."
        )
        subtitulo_tabla.setObjectName("descripcionSeccionDetalleCasa")
        subtitulo_tabla.setWordWrap(True)
        encabezado_tabla.addWidget(titulo_tabla)
        encabezado_tabla.addWidget(subtitulo_tabla)

        self._tabla_historial = QTableWidget(0, 5)
        self._tabla_historial.setObjectName("tablaHistorialCasa")
        configurar_tabla_operativa(
            self._tabla_historial,
            ["Fecha", "Propietario anterior", "Propietario nuevo", "Motivo", "Usuario"],
        )
        self._tabla_historial.horizontalHeader().setStretchLastSection(False)
        self._tabla_historial.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        self._tabla_historial.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        self._tabla_historial.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents
        )
        self._tabla_historial.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.Stretch
        )
        self._tabla_historial.horizontalHeader().setSectionResizeMode(
            4, QHeaderView.ResizeMode.ResizeToContents
        )
        self._tabla_historial.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self._tabla_historial.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._tabla_historial.verticalHeader().setDefaultSectionSize(56)
        self._tabla_historial.setFrameShape(QFrame.Shape.NoFrame)
        self._tabla_historial.setViewportMargins(0, 0, 0, 8)
        self._tabla_historial.viewport().setObjectName("viewportTablaHistorialCasa")
        self._tabla_historial.setMinimumHeight(300)

        for item in self._historial:
            fila = self._tabla_historial.rowCount()
            self._tabla_historial.insertRow(fila)
            self._tabla_historial.setItem(
                fila, 0, crear_item_tabla(self._formateador_fecha(item.fecha_cambio))
            )
            self._tabla_historial.setItem(fila, 1, crear_item_tabla(item.abonado_anterior_nombre))
            self._tabla_historial.setItem(fila, 2, crear_item_tabla(item.abonado_nuevo_nombre))
            self._tabla_historial.setItem(fila, 3, crear_item_tabla(item.motivo or "Sin detalle"))
            self._tabla_historial.setItem(fila, 4, crear_item_tabla(item.usuario_nombre or "Sistema"))

        estado_vacio = QLabel("No hay cambios de propietario registrados para esta casa.")
        estado_vacio.setObjectName("estadoVacioCasas")
        estado_vacio.setAlignment(Qt.AlignmentFlag.AlignCenter)
        estado_vacio.setVisible(not self._historial)
        self._tabla_historial.setVisible(bool(self._historial))

        boton_cerrar = BotonAccionContextual(
            "Cerrar",
            variante=resolver_variante_boton_modal("Cerrar", "neutro"),
            centrado=True,
            mostrar_icono=False,
        )
        boton_cerrar.clicked.connect(self.accept)

        fila_acciones = QHBoxLayout()
        fila_acciones.addStretch(1)
        fila_acciones.addWidget(boton_cerrar)

        self.layout_cabecera.addWidget(titulo)
        self.layout_cabecera.addWidget(descripcion)
        layout_panel_tabla.addLayout(encabezado_tabla)
        layout_panel_tabla.addWidget(self._tabla_historial)
        self.layout_cuerpo.addWidget(tarjeta_resumen)
        self.layout_cuerpo.addWidget(panel_tabla)
        self.layout_cuerpo.addWidget(estado_vacio)
        self.layout_pie.addLayout(fila_acciones)
        self._aplicar_estilos()

    def _crear_resumen_historial(self, etiqueta: str, valor: str) -> QWidget:
        bloque = QWidget()
        layout = QVBoxLayout(bloque)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        label_etiqueta = QLabel(etiqueta)
        label_etiqueta.setObjectName("etiquetaDetalleCasa")
        label_valor = QLabel(valor)
        label_valor.setObjectName("valorResumenHistorialCasa")
        label_valor.setWordWrap(True)
        layout.addWidget(label_etiqueta)
        layout.addWidget(label_valor)
        return bloque

    def _aplicar_estilos(self) -> None:
        paleta = self._paleta_tema
        self.setStyleSheet(
            self.styleSheet()
            + f"""
            QFrame#panelHistorialCasa {{
                background: {paleta["fondo_superficie_suave"]};
                border: 1px solid {paleta["borde_principal"]};
                border-radius: 4px;
            }}
            QLabel#tituloSeccionDetalleCasa {{
                color: {paleta["texto_principal"]};
                font-size: 14px;
                font-weight: 800;
            }}
            QLabel#descripcionSeccionDetalleCasa {{
                color: {paleta["texto_suave"]};
                font-size: 11px;
                font-weight: 600;
            }}
            QLabel#valorResumenHistorialCasa {{
                color: {paleta["texto_principal"]};
                font-size: 13px;
                font-weight: 800;
            }}
            QTableWidget#tablaHistorialCasa {{
                background: {paleta["fondo_input"]};
                border: none;
                border-radius: 4px;
                alternate-background-color: {paleta["fondo_superficie_suave"]};
                color: {paleta["texto_input"]};
                padding: 0 0 8px 0;
            }}
            QWidget#viewportTablaHistorialCasa {{
                background: transparent;
                border: none;
            }}
            QTableWidget#tablaHistorialCasa QHeaderView::section {{
                background: {paleta["fondo_tabla_header"]};
                color: {paleta["texto_input"]};
                border: none;
                border-right: 1px solid {paleta["borde_suave"]};
                border-bottom: 1px solid {paleta["borde_suave"]};
                padding: 10px 12px;
                font-size: 12px;
                font-weight: 800;
            }}
            QTableWidget#tablaHistorialCasa::item {{
                padding: 10px 12px;
                border-bottom: 1px solid {paleta["borde_suave"]};
            }}
            """
        )


class DialogoDetalleCasa(DialogoBaseSicap):
    """Modal para consultar el detalle operativo de una casa."""

    def __init__(
        self,
        detalle: DetalleCasa,
        formateador_fecha: Callable[[str], str],
        formateador_moneda: Callable[[int], str],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._detalle = detalle
        self._formateador_fecha = formateador_fecha
        self._formateador_moneda = formateador_moneda
        self._accion_resultado = "cerrar"
        self.setMinimumWidth(820)
        self.setMinimumHeight(660)
        self._construir_ui()

    @property
    def accion_resultado(self) -> str:
        return self._accion_resultado

    def _construir_ui(self) -> None:
        casa = self._detalle.casa
        titulo = QLabel("Detalle de casa")
        titulo.setObjectName("tituloDialogoSicap")
        descripcion = QLabel(
            "Consulta estado de servicio, deuda, plan activo y trazabilidad de propietarios."
        )
        descripcion.setObjectName("descripcionDialogoSicap")
        descripcion.setWordWrap(True)

        scroll = QScrollArea()
        scroll.setObjectName("scrollDetalleCasa")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        contenedor_scroll = QWidget()
        contenedor_scroll.setObjectName("contenedorScrollDetalleCasa")
        layout_scroll = QVBoxLayout(contenedor_scroll)
        layout_scroll.setContentsMargins(0, 0, 0, 0)
        layout_scroll.setSpacing(12)

        panel_detalle = QFrame()
        panel_detalle.setObjectName("panelContenidoDetalleCasa")
        layout_panel = QVBoxLayout(panel_detalle)
        layout_panel.setContentsMargins(18, 18, 18, 18)
        layout_panel.setSpacing(14)

        fila_superior = QHBoxLayout()
        fila_superior.setSpacing(12)
        bloque_nombre = QVBoxLayout()
        bloque_nombre.setSpacing(4)
        codigo = QLabel(casa.codigo)
        codigo.setObjectName("codigoCasaDetalle")
        nombre = QLabel(casa.resumen_propietario)
        nombre.setObjectName("nombreCasaDetalle")
        bloque_nombre.addWidget(codigo)
        bloque_nombre.addWidget(nombre)

        estado = QLabel(casa.estado_servicio.title())
        estado.setObjectName("badgeDetalleCasa")
        estado.setProperty("activo", casa.estado_servicio == "ACTIVO")
        estado.style().unpolish(estado)
        estado.style().polish(estado)

        fila_superior.addLayout(bloque_nombre, 1)
        fila_superior.addWidget(estado, alignment=Qt.AlignmentFlag.AlignTop)

        encabezado_seccion_contexto = self._crear_encabezado_seccion_detalle(
            "Contexto operativo",
            "Identifica el propietario actual, barrio y fecha del ultimo cambio registrado.",
        )
        grid_info = QGridLayout()
        grid_info.setHorizontalSpacing(14)
        grid_info.setVerticalSpacing(14)
        grid_info.addWidget(
            self._crear_campo_detalle("DNI del abonado", casa.abonado_dni or "Sin registro"),
            0,
            0,
        )
        grid_info.addWidget(
            self._crear_campo_detalle("Barrio", casa.barrio_nombre or "Sin barrio"),
            0,
            1,
        )
        grid_info.addWidget(
            self._crear_campo_detalle(
                "Propietario operativo",
                "Si" if casa.propietario_operativo else "No",
            ),
            1,
            0,
        )
        grid_info.addWidget(
            self._crear_campo_detalle(
                "Ultimo cambio de dueno",
                self._formateador_fecha(self._detalle.ultima_fecha_cambio_dueno),
            ),
            1,
            1,
        )

        encabezado_seccion_finanzas = self._crear_encabezado_seccion_detalle(
            "Estado financiero",
            "Resume periodos pendientes, mora y deuda acumulada de la casa.",
        )
        fila_metricas = QHBoxLayout()
        fila_metricas.setSpacing(12)
        fila_metricas.addWidget(
            self._crear_tarjeta_detalle("Meses pendientes", str(casa.meses_pendientes)),
            1,
        )
        fila_metricas.addWidget(
            self._crear_tarjeta_detalle("Meses en mora", str(casa.meses_en_mora)),
            1,
        )
        fila_metricas.addWidget(
            self._crear_tarjeta_detalle("Deuda", self._formateador_moneda(casa.deuda_total_centavos)),
            1,
        )

        plan_texto = "Sin plan activo asociado."
        if self._detalle.plan_activo is not None:
            plan = self._detalle.plan_activo
            plan_texto = (
                f"{plan.codigo} | Cuota {self._formateador_moneda(plan.cuota_regular_centavos)} | "
                f"Pendientes {plan.cuotas_pendientes} | "
                f"Saldo {self._formateador_moneda(plan.saldo_pendiente_centavos)} | "
                f"Proxima fecha {self._formateador_fecha(plan.proxima_fecha)}"
            )

        plan = self._crear_campo_detalle("Plan activo", plan_texto)
        plan.setObjectName("campoDetalleCasaAmplio")
        direccion = self._crear_campo_detalle(
            "Referencia",
            casa.direccion_referencia or "Sin referencia registrada.",
        )
        direccion.setObjectName("campoDetalleCasaAmplio")

        if self._detalle.historial_propietarios:
            primera_linea = self._detalle.historial_propietarios[0]
            historial_texto = (
                f"{self._formateador_fecha(primera_linea.fecha_cambio)} | "
                f"{primera_linea.abonado_anterior_nombre} -> {primera_linea.abonado_nuevo_nombre}"
            )
        else:
            historial_texto = "Sin cambios de propietario registrados."
        historial = self._crear_campo_detalle("Historial reciente", historial_texto)
        historial.setObjectName("campoDetalleCasaAmplio")

        observaciones = self._crear_campo_detalle(
            "Observaciones",
            casa.observaciones or "Sin observaciones registradas.",
        )
        observaciones.setObjectName("campoDetalleCasaAmplio")

        separador = QFrame()
        separador.setObjectName("separadorDetalleCasa")
        separador.setFixedHeight(1)

        fila_acciones = QHBoxLayout()
        fila_acciones.setSpacing(10)
        boton_cerrar = BotonAccionContextual(
            "Cerrar",
            variante=resolver_variante_boton_modal("Cerrar", "neutro"),
            centrado=True,
            mostrar_icono=False,
        )
        boton_historial = BotonAccionContextual(
            "Ver historial",
            variante="informacion",
            centrado=True,
            mostrar_icono=False,
        )
        boton_dueno = BotonAccionContextual(
            "Cambiar dueno",
            variante="edicion",
            centrado=True,
            mostrar_icono=False,
        )
        boton_editar = BotonAccionContextual(
            "Editar",
            variante="edicion",
            centrado=True,
            mostrar_icono=False,
        )
        boton_cerrar.clicked.connect(self.reject)
        boton_historial.clicked.connect(self._abrir_historial)
        boton_dueno.clicked.connect(self._abrir_cambio_dueno)
        boton_editar.clicked.connect(self._solicitar_edicion)
        fila_acciones.addWidget(boton_cerrar)
        fila_acciones.addStretch(1)
        fila_acciones.addWidget(boton_historial)
        fila_acciones.addWidget(boton_dueno)
        fila_acciones.addWidget(boton_editar)

        layout_panel.addLayout(fila_superior)
        layout_panel.addWidget(
            self._crear_bloque_seccion_detalle(encabezado_seccion_contexto, grid_info)
        )
        layout_panel.addWidget(
            self._crear_bloque_seccion_detalle(encabezado_seccion_finanzas, fila_metricas)
        )
        layout_panel.addWidget(
            self._crear_bloque_seccion_detalle(
                self._crear_encabezado_seccion_detalle(
                    "Plan y localizacion",
                    "Muestra el plan activo vinculado y la referencia operativa de la casa.",
                ),
                [plan, direccion],
            )
        )
        layout_panel.addWidget(
            self._crear_bloque_seccion_detalle(
                self._crear_encabezado_seccion_detalle(
                    "Trazabilidad",
                    "Conserva el ultimo movimiento y las observaciones administrativas de la casa.",
                ),
                [historial, observaciones],
            )
        )
        layout_panel.addWidget(separador)
        layout_panel.addLayout(fila_acciones)
        layout_scroll.addWidget(panel_detalle)
        scroll.setWidget(contenedor_scroll)

        self.layout_cabecera.addWidget(titulo)
        self.layout_cabecera.addWidget(descripcion)
        self.layout_cuerpo.addWidget(scroll)
        self._pie.setVisible(False)
        self._aplicar_estilos()

    def _crear_encabezado_seccion_detalle(self, titulo: str, descripcion: str) -> QWidget:
        bloque = QWidget()
        layout = QVBoxLayout(bloque)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        label_titulo = QLabel(titulo)
        label_titulo.setObjectName("tituloSeccionDetalleCasa")
        label_descripcion = QLabel(descripcion)
        label_descripcion.setObjectName("descripcionSeccionDetalleCasa")
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
        bloque.setObjectName("seccionDetalleCasa")
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

    def _crear_campo_detalle(self, etiqueta: str, valor: str) -> QFrame:
        tarjeta = QFrame()
        tarjeta.setObjectName("campoDetalleCasa")
        layout = QVBoxLayout(tarjeta)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(5)

        label_etiqueta = QLabel(etiqueta)
        label_etiqueta.setObjectName("etiquetaDetalleCasa")
        label_valor = QLabel(valor)
        label_valor.setObjectName("valorDetalleCasa")
        label_valor.setWordWrap(True)

        layout.addWidget(label_etiqueta)
        layout.addWidget(label_valor)
        return tarjeta

    def _crear_tarjeta_detalle(self, titulo: str, valor: str) -> QFrame:
        tarjeta = QFrame()
        tarjeta.setObjectName("tarjetaMiniDetalleCasa")
        layout = QVBoxLayout(tarjeta)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(4)

        label_titulo = QLabel(titulo)
        label_titulo.setObjectName("etiquetaDetalleCasa")
        label_valor = QLabel(valor)
        label_valor.setObjectName("valorTarjetaMiniDetalleCasa")
        layout.addWidget(label_titulo)
        layout.addWidget(label_valor)
        return tarjeta

    def _solicitar_edicion(self) -> None:
        self._accion_resultado = "editar"
        self.accept()

    def _abrir_historial(self) -> None:
        self._accion_resultado = "historial"
        self.accept()

    def _abrir_cambio_dueno(self) -> None:
        self._accion_resultado = "cambiar_dueno"
        self.accept()

    def _aplicar_estilos(self) -> None:
        radio = RADIO_TARJETA_DIALOGO
        paleta = self._paleta_tema
        self.setStyleSheet(
            self.styleSheet()
            + f"""
            QScrollArea#scrollDetalleCasa,
            QWidget#contenedorScrollDetalleCasa {{
                background: transparent;
                border: none;
            }}
            QFrame#panelContenidoDetalleCasa {{
                background: {self._color_fondo_dialogo};
                border: 1px solid {paleta["borde_principal"]};
                border-radius: {radio}px;
            }}
            QFrame#seccionDetalleCasa {{
                background: {paleta["fondo_superficie"]};
                border: 1px solid {paleta["borde_principal"]};
                border-radius: {radio}px;
            }}
            QFrame#campoDetalleCasa,
            QFrame#campoDetalleCasaAmplio,
            QFrame#tarjetaMiniDetalleCasa {{
                background: {paleta["fondo_superficie_suave"]};
                border: 1px solid {paleta["borde_suave"]};
                border-radius: {radio}px;
            }}
            QFrame#separadorDetalleCasa {{
                background: {paleta["borde_principal"]};
                border: none;
            }}
            QLabel#tituloSeccionDetalleCasa {{
                color: {paleta["texto_principal"]};
                font-size: 14px;
                font-weight: 800;
            }}
            QLabel#descripcionSeccionDetalleCasa {{
                color: {paleta["texto_suave"]};
                font-size: 11px;
                font-weight: 600;
            }}
            QLabel#codigoCasaDetalle {{
                color: {paleta["icono_tarjeta_info"]};
                font-size: 12px;
                font-weight: 800;
                letter-spacing: 0.08em;
            }}
            QLabel#nombreCasaDetalle {{
                color: {paleta["texto_principal"]};
                font-size: 19px;
                font-weight: 900;
            }}
            QLabel#badgeDetalleCasa {{
                border-radius: {radio}px;
                padding: 6px 10px;
                font-size: 12px;
                font-weight: 800;
                color: {paleta["texto_badge"]};
                background: {paleta["fondo_badge"]};
                border: 1px solid {paleta["borde_suave"]};
            }}
            QLabel#badgeDetalleCasa[activo="true"] {{
                color: {paleta["texto_badge_activo"]};
                background: {paleta["fondo_badge_activo"]};
                border-color: {paleta["borde_badge_activo"]};
            }}
            QLabel#etiquetaDetalleCasa {{
                color: {paleta["texto_muted"]};
                font-size: 11px;
                font-weight: 700;
            }}
            QLabel#valorDetalleCasa {{
                color: {paleta["texto_input"]};
                font-size: 12px;
                font-weight: 700;
            }}
            QLabel#valorTarjetaMiniDetalleCasa {{
                color: {paleta["texto_principal"]};
                font-size: 20px;
                font-weight: 900;
            }}
            """
        )


class DialogoConfirmacionEstadoCasa(DialogoConfirmacionSicap):
    """Modal de confirmacion para activar o suspender casas."""

    def __init__(self, casa: Casa, parent: QWidget | None = None) -> None:
        nuevo_estado = "suspender" if casa.estado_servicio == "ACTIVO" else "activar"
        super().__init__(
            titulo="Confirmar cambio de estado",
            descripcion=(
                f"Estas a punto de {nuevo_estado} la casa seleccionada. "
                "Verifica la situacion administrativa antes de confirmar."
            ),
            detalles=(
                ("Casa", casa.codigo),
                ("Abonado actual", casa.resumen_propietario),
                ("Barrio", casa.barrio_nombre),
                ("Estado actual", casa.estado_servicio.title()),
            ),
            texto_confirmar=nuevo_estado.title(),
            icono="alert-triangle.svg",
            variante_confirmar="salida" if nuevo_estado == "suspender" else "primario",
            parent=parent,
        )


class VistaCasas(QWidget):
    """Pantalla principal del modulo de casas."""

    DURACION_MENSAJE_MS = 3200
    RADIO_PANEL_TABLA = 16
    ANCHO_COLUMNA_ACCIONES = 230

    filtro_texto_cambiado = Signal(str)
    filtro_rapido_cambiado = Signal(str)
    pagina_cambiada = Signal(int)
    exportar_solicitado = Signal()
    nueva_casa_solicitada = Signal()
    detalle_casa_solicitado = Signal(int)
    editar_casa_solicitado = Signal(int)
    cambio_estado_solicitado = Signal(int)
    historial_casa_solicitado = Signal(int)
    cambio_dueno_solicitado = Signal(int)

    def __init__(self) -> None:
        super().__init__()
        self._pagina_actual = 1
        self._total_paginas = 1
        self._tema_actual = TEMA_SICAP_PREDETERMINADO
        self._paleta_tema = obtener_paleta_tema(self._tema_actual)
        self._temporizador_mensaje = QTimer(self)
        self._temporizador_mensaje.setSingleShot(True)
        self._temporizador_mensaje.timeout.connect(self._ocultar_mensaje)
        self._construir_ui()
        self._aplicar_estilos()

    def aplicar_tema(self, nombre_tema: str) -> None:
        self._tema_actual = (
            nombre_tema if nombre_tema in ("oscuro", "claro") else TEMA_SICAP_PREDETERMINADO
        )
        self._paleta_tema = obtener_paleta_tema(self._tema_actual)
        self._aplicar_estilos()
        for boton in self.findChildren(QPushButton):
            if boton.objectName() == "botonOperativo":
                aplicar_estilo_boton_operativo(boton, principal=False)
            elif boton.objectName() == "botonOperativoPrimario":
                aplicar_estilo_boton_operativo(boton, principal=True)
        for boton_icono in self.findChildren(BotonIconoFilaCasa):
            boton_icono.aplicar_tema(self._tema_actual)

    def mostrar_resumen(self, resumen: ResumenCasas) -> None:
        self._tarjeta_total.actualizar(
            "Total de casas",
            str(resumen.total_casas),
            "Base operativa registrada en el sistema.",
        )
        self._tarjeta_activos.actualizar(
            "Activas",
            str(resumen.casas_activas),
            "Casas operando normalmente dentro del sistema.",
        )
        self._tarjeta_con_deuda.actualizar(
            "Con deuda",
            str(resumen.casas_con_deuda),
            "Casas con saldo pendiente en cargos vigentes.",
        )
        self._tarjeta_morosos.actualizar(
            "Morosas",
            str(resumen.casas_morosas),
            "Casas con al menos un periodo vencido registrado.",
        )

    def mostrar_casas(self, pagina: PaginaCasas) -> None:
        self._pagina_actual = pagina.pagina_actual
        self._total_paginas = pagina.total_paginas
        self._tabla.setRowCount(0)

        for casa in pagina.items:
            fila = self._tabla.rowCount()
            self._tabla.insertRow(fila)
            self._tabla.setItem(fila, 0, crear_item_tabla(casa.codigo))
            self._tabla.setItem(fila, 1, crear_item_tabla(casa.resumen_propietario))
            self._tabla.setItem(fila, 2, crear_item_tabla(casa.abonado_dni or "-"))
            self._tabla.setItem(fila, 3, crear_item_tabla(casa.barrio_nombre))
            self._tabla.setItem(fila, 4, crear_item_tabla(casa.direccion_referencia or "-"))
            self._tabla.setItem(fila, 5, crear_item_tabla(casa.meses_en_mora))
            self._tabla.setCellWidget(fila, 6, self._crear_badge_estado(casa.estado_servicio))
            self._tabla.setCellWidget(fila, 7, self._crear_acciones_fila(casa))

        self._tabla.resizeRowsToContents()
        self._tabla.setColumnWidth(7, max(self._tabla.columnWidth(7), self.ANCHO_COLUMNA_ACCIONES))
        self._actualizar_estado_vacio(pagina.total_registros == 0)
        self._label_paginacion.setText(
            f"Mostrando {pagina.indice_inicio}-{pagina.indice_fin} de {pagina.total_registros} registros"
        )
        self._label_numero_pagina.setText(f"Pagina {self._pagina_actual} de {self._total_paginas}")
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

    def solicitar_datos_casa(
        self,
        barrios: Iterable[OpcionBarrio],
        abonados: Iterable[OpcionAbonado],
        casa: Casa | None = None,
    ) -> FormularioCasa | None:
        dialogo = DialogoFormularioCasa(
            barrios=barrios,
            abonados=abonados,
            casa=casa,
            parent=self,
        )
        if dialogo.exec() != QDialog.DialogCode.Accepted:
            return None
        return dialogo.obtener_formulario()

    def solicitar_cambio_dueno(
        self,
        casa: Casa,
        abonados: Iterable[OpcionAbonado],
    ) -> DialogoCambioDuenoCasa | None:
        dialogo = DialogoCambioDuenoCasa(casa=casa, abonados=abonados, parent=self)
        if dialogo.exec() != QDialog.DialogCode.Accepted:
            return None
        return dialogo

    def mostrar_detalle_casa(
        self,
        detalle: DetalleCasa,
        formateador_fecha: Callable[[str], str],
        formateador_moneda: Callable[[int], str],
    ) -> str:
        dialogo = DialogoDetalleCasa(
            detalle=detalle,
            formateador_fecha=formateador_fecha,
            formateador_moneda=formateador_moneda,
            parent=self,
        )
        dialogo.exec()
        return dialogo.accion_resultado

    def mostrar_historial_propietarios(
        self,
        casa: Casa,
        historial: Iterable[HistorialPropietarioCasa],
        formateador_fecha: Callable[[str], str],
    ) -> None:
        DialogoHistorialPropietariosCasa(
            casa=casa,
            historial=historial,
            formateador_fecha=formateador_fecha,
            parent=self,
        ).exec()

    def confirmar_cambio_estado_casa(self, casa: Casa) -> bool:
        dialogo = DialogoConfirmacionEstadoCasa(casa=casa, parent=self)
        return dialogo.exec() == QDialog.DialogCode.Accepted

    def solicitar_ruta_exportacion(self) -> str:
        ruta, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar casas",
            "casas.csv",
            "Archivos CSV (*.csv)",
        )
        return ruta

    def _ocultar_mensaje(self) -> None:
        self._mensaje.clear()
        self._mensaje.setVisible(False)

    def _construir_ui(self) -> None:
        self.setObjectName("vistaCasas")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 6)
        layout.setSpacing(12)

        encabezado = QHBoxLayout()
        encabezado.setSpacing(10)
        bloque_titulo = QVBoxLayout()
        bloque_titulo.setSpacing(2)
        titulo = QLabel("Casas")
        titulo.setObjectName("tituloModulo")
        descripcion = QLabel("Gestion de casas, estado de servicio y propietarios operativos")
        descripcion.setObjectName("descripcionModulo")
        descripcion.setWordWrap(True)
        bloque_titulo.addWidget(titulo)
        bloque_titulo.addWidget(descripcion)

        fila_acciones = QHBoxLayout()
        fila_acciones.setSpacing(8)
        fila_acciones.addStretch(1)
        boton_exportar = crear_boton_operativo("Exportar")
        boton_nuevo = crear_boton_operativo("Nueva casa", principal=True)
        boton_exportar.clicked.connect(self.exportar_solicitado.emit)
        boton_nuevo.clicked.connect(self.nueva_casa_solicitada.emit)
        fila_acciones.addWidget(boton_exportar)
        fila_acciones.addWidget(boton_nuevo)

        encabezado.addLayout(bloque_titulo, 1)
        encabezado.addLayout(fila_acciones)

        self._mensaje = QLabel("")
        self._mensaje.setObjectName("mensajeCasas")
        self._mensaje.setVisible(False)
        self._mensaje.setWordWrap(True)

        fila_tarjetas = QGridLayout()
        fila_tarjetas.setHorizontalSpacing(10)
        fila_tarjetas.setVerticalSpacing(10)
        self._tarjeta_total = TarjetaResumenCasa("home.svg", "#8ec9ff")
        self._tarjeta_activos = TarjetaResumenCasa("circle-check.svg", "#8de8c7")
        self._tarjeta_con_deuda = TarjetaResumenCasa("alert-triangle.svg", "#f7cc7a")
        self._tarjeta_morosos = TarjetaResumenCasa("clock.svg", "#c6b6ff")
        fila_tarjetas.addWidget(self._tarjeta_total, 0, 0)
        fila_tarjetas.addWidget(self._tarjeta_activos, 0, 1)
        fila_tarjetas.addWidget(self._tarjeta_con_deuda, 0, 2)
        fila_tarjetas.addWidget(self._tarjeta_morosos, 0, 3)

        panel_filtros = QFrame()
        panel_filtros.setObjectName("panelOperativoCasas")
        layout_filtros = QVBoxLayout(panel_filtros)
        layout_filtros.setContentsMargins(14, 14, 14, 14)
        layout_filtros.setSpacing(10)

        self._campo_busqueda = QLineEdit()
        self._campo_busqueda.setPlaceholderText("Buscar por codigo, DNI, propietario o referencia")
        self._campo_busqueda.textChanged.connect(self.filtro_texto_cambiado.emit)

        fila_chips = QHBoxLayout()
        fila_chips.setSpacing(6)
        self._grupo_filtros = QButtonGroup(self)
        self._grupo_filtros.setExclusive(True)
        self._botones_filtros: dict[str, QPushButton] = {}
        for codigo, texto in (
            (FILTRO_CASAS_TODAS, "Todas"),
            (FILTRO_CASAS_ACTIVAS, "Activas"),
            (FILTRO_CASAS_SUSPENDIDAS, "Suspendidas"),
            (FILTRO_CASAS_CON_MORA, "Con mora"),
            (FILTRO_CASAS_SIN_PROPIETARIO, "Sin propietario operativo"),
        ):
            boton = QPushButton(texto)
            boton.setObjectName("chipFiltroCasa")
            boton.setCheckable(True)
            boton.setCursor(Qt.CursorShape.PointingHandCursor)
            boton.clicked.connect(
                lambda checked=False, valor=codigo: self.filtro_rapido_cambiado.emit(valor)
            )
            self._grupo_filtros.addButton(boton)
            self._botones_filtros[codigo] = boton
            fila_chips.addWidget(boton)
        self._botones_filtros[FILTRO_CASAS_TODAS].setChecked(True)
        fila_chips.addStretch(1)

        layout_filtros.addWidget(self._campo_busqueda)
        layout_filtros.addLayout(fila_chips)

        panel_tabla = QFrame()
        panel_tabla.setObjectName("panelTablaCasas")
        layout_tabla = QVBoxLayout(panel_tabla)
        layout_tabla.setContentsMargins(14, 14, 14, 14)
        layout_tabla.setSpacing(10)

        self._tabla = QTableWidget(0, 8)
        self._tabla.setObjectName("tablaCasas")
        configurar_tabla_operativa(
            self._tabla,
            [
                "Codigo",
                "Abonado actual",
                "DNI",
                "Barrio",
                "Referencia",
                "Meses en mora",
                "Estado",
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
        self._tabla.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self._tabla.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self._tabla.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        self._tabla.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.Interactive)
        self._tabla.setColumnWidth(7, self.ANCHO_COLUMNA_ACCIONES)
        self._tabla.verticalHeader().setDefaultSectionSize(58)
        self._tabla.setFrameShape(QFrame.Shape.NoFrame)
        self._tabla.setViewportMargins(0, 0, 0, self.RADIO_PANEL_TABLA)
        self._tabla.viewport().setObjectName("viewportTablaCasas")
        self._tabla.viewport().setAutoFillBackground(False)

        self._estado_vacio = QLabel("No hay casas que coincidan con los filtros actuales.")
        self._estado_vacio.setObjectName("estadoVacioCasas")
        self._estado_vacio.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._estado_vacio.setVisible(False)

        pie_tabla = QHBoxLayout()
        pie_tabla.setSpacing(8)
        self._label_paginacion = QLabel("Mostrando 0-0 de 0 registros")
        self._label_paginacion.setObjectName("textoPieCasas")
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
        self._label_numero_pagina = QLabel("Pagina 1 de 1")
        self._label_numero_pagina.setObjectName("textoPieCasas")
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
        badge.setObjectName("badgeEstadoCasa")
        badge.setProperty("activo", estado == "ACTIVO")
        badge.style().unpolish(badge)
        badge.style().polish(badge)
        layout.addWidget(badge, alignment=Qt.AlignmentFlag.AlignCenter)
        return contenedor

    def _crear_acciones_fila(self, casa: Casa) -> QWidget:
        contenedor = QWidget()
        contenedor.setObjectName("contenedorAccionesCasa")
        contenedor.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        contenedor.setMinimumWidth(self.ANCHO_COLUMNA_ACCIONES)
        contenedor.setMinimumHeight(58)
        layout = QHBoxLayout(contenedor)
        layout.setContentsMargins(0, 0, 0, 14)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        boton_detalle = BotonIconoFilaCasa("eye.svg", "#4fa3ff", "Ver detalle")
        boton_editar = BotonIconoFilaCasa("key.svg", "#4fa3ff", "Editar")
        boton_cambio_dueno = BotonIconoFilaCasa("user.svg", "#8de8c7", "Cambiar dueno")
        boton_historial = BotonIconoFilaCasa("clock.svg", "#b48bff", "Ver historial")
        boton_estado = BotonIconoFilaCasa(
            "lock.svg" if casa.estado_servicio == "ACTIVO" else "circle-check.svg",
            "#ff625c" if casa.estado_servicio == "ACTIVO" else "#4fa3ff",
            "Suspender" if casa.estado_servicio == "ACTIVO" else "Activar",
        )

        boton_detalle.clicked.connect(
            lambda checked=False, identificador=casa.identificador: self.detalle_casa_solicitado.emit(
                int(identificador or 0)
            )
        )
        boton_editar.clicked.connect(
            lambda checked=False, identificador=casa.identificador: self.editar_casa_solicitado.emit(
                int(identificador or 0)
            )
        )
        boton_cambio_dueno.clicked.connect(
            lambda checked=False, identificador=casa.identificador: self.cambio_dueno_solicitado.emit(
                int(identificador or 0)
            )
        )
        boton_historial.clicked.connect(
            lambda checked=False, identificador=casa.identificador: self.historial_casa_solicitado.emit(
                int(identificador or 0)
            )
        )
        boton_estado.clicked.connect(
            lambda checked=False, identificador=casa.identificador: self.cambio_estado_solicitado.emit(
                int(identificador or 0)
            )
        )

        layout.addWidget(boton_detalle)
        layout.addWidget(boton_editar)
        layout.addWidget(boton_cambio_dueno)
        layout.addWidget(boton_historial)
        layout.addWidget(boton_estado)
        return contenedor

    def _actualizar_estado_vacio(self, sin_datos: bool) -> None:
        self._estado_vacio.setVisible(sin_datos)
        self._tabla.setVisible(not sin_datos)

    def _aplicar_estilos(self) -> None:
        radio_panel_tabla = self.RADIO_PANEL_TABLA
        self.setStyleSheet(
            """
            QWidget#vistaCasas {
                background: transparent;
            }
            QLabel#tituloModulo {
                color: #ffffff;
                font-size: 19px;
                font-weight: 900;
            }
            QLabel#descripcionModulo,
            QLabel#textoPieCasas,
            QLabel#detalleTarjetaResumen {
                color: rgba(235, 242, 248, 0.76);
                font-size: 11px;
                font-weight: 600;
            }
            QLabel#mensajeCasas {
                color: #d9fff5;
                font-size: 12px;
                font-weight: 700;
                padding: 8px 10px;
                border-radius: 12px;
                background-color: rgba(16, 120, 98, 0.16);
                border: 1px solid rgba(158, 231, 214, 0.26);
            }
            QLabel#mensajeCasas[error="true"] {
                color: #ffd4cf;
                background-color: rgba(180, 35, 24, 0.15);
                border: 1px solid rgba(255, 205, 199, 0.28);
            }
            QFrame#panelOperativoCasas,
            QFrame#tarjetaResumenCasas {
                background: rgba(255, 255, 255, 0.10);
                border: 1px solid rgba(255, 255, 255, 0.16);
                border-radius: 18px;
            }
            QFrame#panelTablaCasas {
                background: rgba(255, 255, 255, 0.10);
                border: 1px solid rgba(255, 255, 255, 0.16);
                border-radius: """
            + str(radio_panel_tabla)
            + """px;
            }
            QTableWidget#tablaCasas {
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
            QWidget#viewportTablaCasas {
                background: transparent;
                border: none;
                border-bottom-left-radius: """
            + str(radio_panel_tabla)
            + """px;
                border-bottom-right-radius: """
            + str(radio_panel_tabla)
            + """px;
            }
            QTableWidget#tablaCasas QHeaderView::section:first {
                border-top-left-radius: """
            + str(radio_panel_tabla)
            + """px;
            }
            QTableWidget#tablaCasas QHeaderView::section {
                background: rgba(255, 255, 255, 0.10);
                color: #f7fbff;
                border: none;
                border-right: 1px solid rgba(255, 255, 255, 0.06);
                border-bottom: 1px solid rgba(255, 255, 255, 0.08);
                padding: 10px 12px;
                font-size: 12px;
                font-weight: 800;
            }
            QTableWidget#tablaCasas QHeaderView::section:last {
                border-top-right-radius: """
            + str(radio_panel_tabla)
            + """px;
            }
            QTableWidget#tablaCasas::item {
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
            QLineEdit {
                min-height: 36px;
                border: 1px solid rgba(255, 255, 255, 0.18);
                border-radius: 12px;
                background: rgba(255, 255, 255, 0.11);
                color: #f5fbff;
                padding: 0 10px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: rgba(109, 241, 220, 0.42);
                background: rgba(255, 255, 255, 0.16);
            }
            QPushButton#chipFiltroCasa {
                min-height: 30px;
                border-radius: 11px;
                padding: 0 12px;
                background: rgba(255, 255, 255, 0.06);
                border: 1px solid rgba(255, 255, 255, 0.14);
                color: #ecf5ff;
                font-size: 11px;
                font-weight: 700;
            }
            QPushButton#chipFiltroCasa:hover {
                background: rgba(255, 255, 255, 0.12);
            }
            QPushButton#chipFiltroCasa:checked {
                color: #0f2d43;
                background: #d2f4f2;
                border-color: rgba(255, 255, 255, 0.18);
            }
            QLabel#badgeEstadoCasa {
                border-radius: 11px;
                padding: 6px 10px;
                font-size: 11px;
                font-weight: 800;
                color: #f4f8fb;
                background: rgba(132, 146, 166, 0.22);
                border: 1px solid rgba(255, 255, 255, 0.12);
            }
            QLabel#badgeEstadoCasa[activo="true"] {
                color: #d9fff5;
                background: rgba(16, 120, 98, 0.22);
                border-color: rgba(158, 231, 214, 0.26);
            }
            QWidget#contenedorAccionesCasa {
                background: transparent;
            }
            QToolButton#botonIconoFilaCasa {
                background: transparent;
                border: none;
                border-radius: 8px;
                padding: 0px;
                margin: 0px;
            }
            QToolButton#botonIconoFilaCasa:hover {
                background: transparent;
                border: none;
            }
            QLabel#estadoVacioCasas {
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
        if self._tema_actual == "claro":
            paleta = self._paleta_tema
            self.setStyleSheet(
                self.styleSheet()
                + f"""
                QWidget {{
                    background: transparent;
                }}
                QLabel#tituloModulo,
                QLabel#valorTarjetaResumen,
                QLabel#nombreCasaDetalle {{
                    color: {paleta["texto_principal"]};
                }}
                QLabel#descripcionModulo,
                QLabel#detalleTarjetaResumen,
                QLabel#textoPieCasas,
                QLabel#etiquetaDetalleCasa {{
                    color: {paleta["texto_secundario"]};
                }}
                QLabel#mensajeCasas[error="false"] {{
                    color: {paleta["texto_exito"]};
                    background-color: {paleta["fondo_exito"]};
                    border: 1px solid {paleta["borde_exito"]};
                }}
                QLabel#mensajeCasas[error="true"] {{
                    color: {paleta["texto_error"]};
                    background-color: {paleta["fondo_error"]};
                    border: 1px solid {paleta["borde_error"]};
                }}
                QFrame#panelOperativoCasas,
                QFrame#panelTablaCasas,
                QFrame#tarjetaResumenCasas {{
                    background: {paleta["fondo_superficie"]};
                    border: 1px solid {paleta["borde_principal"]};
                }}
                QTableWidget#tablaCasas {{
                    background: {paleta["fondo_superficie_muy_suave"]};
                }}
                QTableWidget#tablaCasas QHeaderView::section {{
                    background: {paleta["fondo_tabla_header"]};
                    color: {paleta["texto_input"]};
                    border-right: 1px solid {paleta["borde_suave"]};
                    border-bottom: 1px solid {paleta["borde_suave"]};
                }}
                QLineEdit {{
                    border: 1px solid {paleta["borde_medio"]};
                    background: {paleta["fondo_input"]};
                    color: {paleta["texto_input"]};
                }}
                QLineEdit:focus {{
                    border-color: {paleta["borde_foco_input"]};
                    background: {paleta["fondo_input_focus"]};
                }}
                QPushButton#chipFiltroCasa {{
                    background: {paleta["fondo_chip"]};
                    border: 1px solid {paleta["borde_suave"]};
                    color: {paleta["texto_chip"]};
                }}
                QPushButton#chipFiltroCasa:hover {{
                    background: {paleta["fondo_chip_hover"]};
                }}
                QPushButton#chipFiltroCasa:checked {{
                    color: {paleta["texto_chip_activo"]};
                    background: {paleta["fondo_chip_activo"]};
                    border-color: {paleta["borde_chip_activo"]};
                }}
                QLabel#badgeEstadoCasa {{
                    color: {paleta["texto_badge"]};
                    background: {paleta["fondo_badge"]};
                    border: 1px solid {paleta["borde_suave"]};
                }}
                QLabel#badgeEstadoCasa[activo="true"] {{
                    color: {paleta["texto_badge_activo"]};
                    background: {paleta["fondo_badge_activo"]};
                    border-color: {paleta["borde_badge_activo"]};
                }}
                QLabel#estadoVacioCasas {{
                    color: {paleta["texto_secundario"]};
                }}
                QLabel#tituloTarjetaResumen,
                QLabel#codigoCasaDetalle {{
                    color: {paleta["texto_panel_secundario"]};
                }}
                """
            )
