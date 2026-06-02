"""Vista PySide6 del modulo de casas."""

from __future__ import annotations

from typing import Callable, Iterable

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
    CampoBusquedaSeleccionSigqua,
    DialogoBaseSigqua,
    DialogoConfirmacionSigqua,
    aplicar_estilo_boton_operativo,
    configurar_tabla_operativa,
    crear_boton_operativo,
    crear_item_tabla,
    obtener_icono_tabler_coloreado,
    resolver_variante_boton_modal,
)
from comun.ui.componentes import RADIO_TARJETA_DIALOGO
from comun.ui.temas import (
    TEMA_SIGQUA_PREDETERMINADO,
    obtener_fondo_header_destacado,
    obtener_paleta_tema,
    resolver_nombre_tema,
)
from modulos.casas.entidades import (
    Casa,
    DetalleCasa,
    ESTADO_ADMINISTRATIVO_OPERATIVA,
    ESTADO_ADMINISTRATIVO_SUSPENDIDA,
    ESTADO_SERVICIO_ACTIVO,
    ESTADO_SERVICIO_CORTADO,
    ESTADO_SERVICIO_INACTIVO,
    FILTRO_CASAS_ACTIVAS,
    FILTRO_CASAS_CON_MORA,
    FILTRO_CASAS_CORTADAS,
    FILTRO_CASAS_DEUDA_MAYOR_5,
    FILTRO_CASAS_SIN_PROPIETARIO,
    FILTRO_CASAS_SUSPENDIDAS,
    FILTRO_CASAS_TODAS,
    FormularioCorteServicioCasa,
    FormularioCasa,
    HistorialPropietarioCasa,
    MOTIVO_CAMBIO_RESPONSABLE_FALLECIMIENTO,
    MOTIVO_ESTADO_ADMINISTRATIVO_ABONADO_INACTIVO,
    MOTIVO_ESTADO_ADMINISTRATIVO_NINGUNO,
    MOTIVO_ESTADO_ADMINISTRATIVO_REASIGNACION_PENDIENTE,
    MOTIVO_ESTADO_ADMINISTRATIVO_REVISION_ADMINISTRATIVA,
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


class DialogoFormularioCasa(DialogoBaseSigqua):
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
        self.setMinimumWidth(760)
        self.setMinimumHeight(500)
        self._construir_ui()

    def obtener_formulario(self) -> FormularioCasa:
        barrio_id = self._campo_barrio.identificador_seleccionado()
        abonado_id = self._campo_abonado.identificador_seleccionado()
        motivo = self._combo_motivo_administrativo.currentData()
        return FormularioCasa(
            identificador=None if self._casa is None else self._casa.identificador,
            abonado_id=int(abonado_id) if abonado_id is not None else None,
            barrio_id=int(barrio_id) if barrio_id is not None else None,
            direccion_referencia=self._campo_direccion.toPlainText(),
            observaciones=self._campo_observaciones.toPlainText(),
            estado_servicio=self._combo_estado.currentText(),
            estado_administrativo=self._combo_estado_administrativo.currentText(),
            motivo_estado_administrativo=str(motivo or MOTIVO_ESTADO_ADMINISTRATIVO_NINGUNO),
            ha_tenido_servicio_activo=self._combo_antecedente.currentData() == 1,
        )

    def accept(self) -> None:
        if self._campo_abonado.identificador_seleccionado() is None:
            self._mensaje.setText("Selecciona un abonado valido para la casa.")
            self._mensaje.setVisible(True)
            return
        if self._campo_barrio.identificador_seleccionado() is None:
            self._mensaje.setText("Selecciona un barrio valido.")
            self._mensaje.setVisible(True)
            return
        if (
            self._combo_estado_administrativo.currentText() == ESTADO_ADMINISTRATIVO_SUSPENDIDA
            and self._combo_motivo_administrativo.currentData() is None
        ):
            self._mensaje.setText("Selecciona el motivo administrativo de la suspension.")
            self._mensaje.setVisible(True)
            return
        self._mensaje.setVisible(False)
        super().accept()

    def _construir_ui(self) -> None:
        titulo = QLabel("Editar casa" if self._casa else "Nueva casa")
        titulo.setObjectName("tituloDialogoSigqua")
        descripcion = QLabel(
            "Configura la casa, su barrio y el propietario operativo actual."
        )
        descripcion.setObjectName("descripcionDialogoSigqua")
        descripcion.setWordWrap(True)

        formulario = QGridLayout()
        formulario.setContentsMargins(0, 0, 0, 0)
        formulario.setHorizontalSpacing(8)
        formulario.setVerticalSpacing(8)

        self._campo_abonado = CampoBusquedaSeleccionSigqua(
            texto_sin_resultados="No se encontraron abonados",
            placeholder="Escribe para buscar un abonado",
        )
        self._campo_abonado.establecer_opciones(
            [(abonado.identificador, abonado.etiqueta) for abonado in self._abonados]
        )

        self._campo_barrio = CampoBusquedaSeleccionSigqua(
            texto_sin_resultados="No se encontraron barrios",
            placeholder="Escribe para buscar un barrio",
        )
        self._campo_barrio.establecer_opciones(
            [(barrio.identificador, barrio.nombre) for barrio in self._barrios]
        )

        self._combo_estado = QComboBox()
        self._combo_estado.addItems(
            [ESTADO_SERVICIO_ACTIVO, ESTADO_SERVICIO_CORTADO, ESTADO_SERVICIO_INACTIVO]
        )
        self._combo_estado.setToolTip(
            "El estado fisico se registra al crear y luego se gestiona con acciones operativas."
        )
        self._combo_estado_administrativo = QComboBox()
        self._combo_estado_administrativo.addItems(
            [ESTADO_ADMINISTRATIVO_OPERATIVA, ESTADO_ADMINISTRATIVO_SUSPENDIDA]
        )
        self._combo_motivo_administrativo = QComboBox()
        self._combo_motivo_administrativo.addItem("Sin motivo", None)
        self._combo_motivo_administrativo.addItem(
            "Abonado inactivo", MOTIVO_ESTADO_ADMINISTRATIVO_ABONADO_INACTIVO
        )
        self._combo_motivo_administrativo.addItem(
            "Reasignacion pendiente", MOTIVO_ESTADO_ADMINISTRATIVO_REASIGNACION_PENDIENTE
        )
        self._combo_motivo_administrativo.addItem(
            "Revision administrativa", MOTIVO_ESTADO_ADMINISTRATIVO_REVISION_ADMINISTRATIVA
        )
        self._combo_antecedente = QComboBox()
        self._combo_antecedente.addItem("Nunca ha tenido servicio", 0)
        self._combo_antecedente.addItem("Ya tuvo servicio antes", 1)
        self._campo_direccion = QPlainTextEdit()
        self._campo_direccion.setPlaceholderText("Direccion o referencia de la casa")
        self._campo_direccion.setFixedHeight(60)
        self._campo_observaciones = QPlainTextEdit()
        self._campo_observaciones.setPlaceholderText("Observaciones")
        self._campo_observaciones.setFixedHeight(60)
        self._combo_estado_administrativo.currentTextChanged.connect(
            self._actualizar_estado_campos_administrativos
        )

        if self._casa is not None:
            etiqueta_abonado = self._casa.resumen_propietario
            if self._casa.abonado_dni:
                etiqueta_abonado = f"{etiqueta_abonado} | {self._casa.abonado_dni}"
            self._campo_abonado.seleccionar_por_id(self._casa.abonado_id, etiqueta_abonado)
            self._campo_barrio.seleccionar_por_id(self._casa.barrio_id, self._casa.barrio_nombre)
            self._combo_estado.setCurrentText(self._casa.estado_servicio)
            self._combo_estado_administrativo.setCurrentText(self._casa.estado_administrativo)
            indice_motivo = self._combo_motivo_administrativo.findData(
                self._casa.motivo_estado_administrativo
            )
            if indice_motivo >= 0:
                self._combo_motivo_administrativo.setCurrentIndex(indice_motivo)
            self._combo_antecedente.setCurrentIndex(1 if self._casa.ha_tenido_servicio_activo else 0)
            self._combo_antecedente.setEnabled(self._casa.antecedente_servicio_editable)
            self._campo_direccion.setPlainText(self._casa.direccion_referencia)
            self._campo_observaciones.setPlainText(self._casa.observaciones)
            self._campo_abonado.setEnabled(False)
            self._combo_estado.setEnabled(False)

        formulario.addWidget(
            self._crear_bloque_formulario("Abonado actual", self._campo_abonado),
            0,
            0,
            1,
            2,
        )
        formulario.addWidget(self._crear_bloque_formulario("Barrio", self._campo_barrio), 1, 0)
        bloque_estado_servicio = self._crear_bloque_formulario(
            "Estado fisico del servicio",
            self._combo_estado,
        )
        if self._casa is not None:
            nota_estado = QLabel(
                "Se muestra solo como referencia. Para cortar el servicio usa la accion operativa del modulo."
            )
            nota_estado.setObjectName("descripcionDialogoSigqua")
            nota_estado.setWordWrap(True)
            bloque_estado_servicio.layout().addWidget(nota_estado)
        formulario.addWidget(bloque_estado_servicio, 1, 1)
        formulario.addWidget(
            self._crear_bloque_formulario(
                "Estado administrativo",
                self._combo_estado_administrativo,
            ),
            2,
            0,
        )
        formulario.addWidget(
            self._crear_bloque_formulario(
                "Antecedente de servicio",
                self._combo_antecedente,
            ),
            2,
            1,
        )
        formulario.addWidget(
            self._crear_bloque_formulario(
                "Motivo administrativo",
                self._combo_motivo_administrativo,
            ),
            3,
            0,
            1,
            2,
        )

        panel_datos = self._crear_panel_formulario(
            "Datos principales",
            "Define el propietario actual, el estado fisico, la dimension administrativa y el antecedente real del servicio.",
        )
        panel_datos.layout().addLayout(formulario)

        panel_notas = self._crear_panel_formulario(
            "Contexto operativo",
            "Completa la referencia de la casa y cualquier nota administrativa relevante.",
        )
        notas_layout = QVBoxLayout()
        notas_layout.setContentsMargins(0, 0, 0, 0)
        notas_layout.setSpacing(8)
        notas_layout.addWidget(
            self._crear_bloque_formulario("Referencia", self._campo_direccion)
        )
        notas_layout.addWidget(
            self._crear_bloque_formulario("Observaciones", self._campo_observaciones)
        )
        panel_notas.layout().addLayout(notas_layout)

        self._mensaje = QLabel("")
        self._mensaje.setObjectName("mensajeErrorDialogoSigqua")
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
        contenido_scroll = QWidget()
        layout_scroll = QVBoxLayout(contenido_scroll)
        layout_scroll.setContentsMargins(0, 0, 0, 0)
        layout_scroll.setSpacing(8)
        fila_paneles = QHBoxLayout()
        fila_paneles.setContentsMargins(0, 0, 0, 0)
        fila_paneles.setSpacing(8)
        fila_paneles.addWidget(panel_datos, 2)
        fila_paneles.addWidget(panel_notas, 1)
        layout_scroll.addLayout(fila_paneles)
        layout_scroll.addWidget(self._mensaje)
        layout_scroll.addStretch(1)
        self.layout_cuerpo.addWidget(
            self.crear_area_scroll_cuerpo(contenido_scroll, "scrollFormularioCasa")
        )
        self.layout_pie.addLayout(fila_acciones)
        self._actualizar_estado_campos_administrativos()

    def _actualizar_estado_campos_administrativos(self) -> None:
        suspendida = self._combo_estado_administrativo.currentText() == ESTADO_ADMINISTRATIVO_SUSPENDIDA
        self._combo_motivo_administrativo.setEnabled(suspendida)
        if not suspendida:
            self._combo_motivo_administrativo.setCurrentIndex(0)

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


class DialogoCambioDuenoCasa(DialogoBaseSigqua):
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
        self.setMinimumHeight(430)
        self._construir_ui()

    @property
    def nuevo_abonado_id(self) -> int | None:
        valor = self._campo_abonado.identificador_seleccionado()
        return int(valor) if valor is not None else None

    @property
    def motivo(self) -> str:
        return str(self._combo_motivo.currentData() or "").strip()

    @property
    def observacion(self) -> str:
        return self._campo_observacion.toPlainText().strip()

    def accept(self) -> None:
        if self._campo_abonado.identificador_seleccionado() is None:
            self._mensaje.setText("Selecciona el nuevo abonado.")
            self._mensaje.setVisible(True)
            return
        if self._combo_motivo.currentData() is None:
            self._mensaje.setText("Selecciona el motivo del cambio de propietario.")
            self._mensaje.setVisible(True)
            return
        self._mensaje.setVisible(False)
        super().accept()

    def _construir_ui(self) -> None:
        titulo = QLabel("Cambiar dueno de casa")
        titulo.setObjectName("tituloDialogoSigqua")
        descripcion = QLabel(
            "La deuda pendiente y el plan activo de la casa se migraran al nuevo abonado."
        )
        descripcion.setObjectName("descripcionDialogoSigqua")
        descripcion.setWordWrap(True)

        resumen = QLabel(
            f"{self._casa.codigo} | {self._casa.resumen_propietario} | "
            f"{self._casa.barrio_nombre or 'Sin barrio'}"
        )
        resumen.setObjectName("descripcionDialogoSigqua")
        resumen.setWordWrap(True)

        self._campo_abonado = CampoBusquedaSeleccionSigqua(
            texto_sin_resultados="No se encontraron abonados",
            placeholder="Escribe para buscar un abonado",
        )
        self._campo_abonado.establecer_opciones(
            [
                (abonado.identificador, abonado.etiqueta)
                for abonado in self._abonados
                if abonado.estado == "ACTIVO"
            ]
        )

        self._combo_motivo = QComboBox()
        self._combo_motivo.addItem("Selecciona un motivo", None)
        self._combo_motivo.addItem("Fallecimiento del abonado", MOTIVO_CAMBIO_RESPONSABLE_FALLECIMIENTO)
        self._combo_motivo.addItem("Venta o traspaso", "VENTA_TRASPASO")
        self._combo_motivo.addItem("Correccion administrativa", "CORRECCION_ADMINISTRATIVA")
        self._combo_motivo.addItem("Solicitud del abonado", "SOLICITUD_ABONADO")
        self._combo_motivo.addItem("Otro motivo documentado", "OTRO")

        self._campo_observacion = QPlainTextEdit()
        self._campo_observacion.setPlaceholderText("Observacion opcional del cambio")
        self._campo_observacion.setFixedHeight(60)

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
            self._crear_bloque_formulario("Nuevo abonado", self._campo_abonado)
        )

        panel_motivo = self._crear_panel_formulario(
            "Trazabilidad",
            "Deja constancia clara del motivo para mantener el historial administrativo.",
        )
        panel_motivo.layout().addWidget(self._crear_bloque_formulario("Motivo", self._combo_motivo))
        panel_motivo.layout().addWidget(
            self._crear_bloque_formulario("Observacion", self._campo_observacion)
        )

        self._mensaje = QLabel("")
        self._mensaje.setObjectName("mensajeErrorDialogoSigqua")
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

        contenido_scroll = QWidget()
        layout_scroll = QVBoxLayout(contenido_scroll)
        layout_scroll.setContentsMargins(0, 0, 0, 0)
        layout_scroll.setSpacing(8)
        layout_scroll.addWidget(panel_resumen)
        layout_scroll.addWidget(panel_destino)
        layout_scroll.addWidget(panel_motivo)
        layout_scroll.addWidget(self._mensaje)
        layout_scroll.addStretch(1)

        self.layout_cabecera.addWidget(titulo)
        self.layout_cabecera.addWidget(descripcion)
        self.layout_cuerpo.addWidget(
            self.crear_area_scroll_cuerpo(contenido_scroll, "scrollCambioDuenoCasa")
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


class DialogoHistorialPropietariosCasa(DialogoBaseSigqua):
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
        titulo.setObjectName("tituloDialogoSigqua")
        descripcion = QLabel(
            f"Traza de cambios registrada para {self._casa.codigo}."
        )
        descripcion.setObjectName("descripcionDialogoSigqua")
        descripcion.setWordWrap(True)

        tarjeta_resumen = QFrame()
        tarjeta_resumen.setObjectName("bloqueDialogoSigqua")
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

        self._tabla_historial = QTableWidget(0, 6)
        self._tabla_historial.setObjectName("tablaHistorialCasa")
        configurar_tabla_operativa(
            self._tabla_historial,
            ["Fecha", "Propietario anterior", "Propietario nuevo", "Motivo", "Observacion", "Usuario"],
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
            4, QHeaderView.ResizeMode.Stretch
        )
        self._tabla_historial.horizontalHeader().setSectionResizeMode(
            5, QHeaderView.ResizeMode.ResizeToContents
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
            self._tabla_historial.setItem(fila, 4, crear_item_tabla(item.observacion or "Sin observacion"))
            self._tabla_historial.setItem(fila, 5, crear_item_tabla(item.usuario_nombre or "Sistema"))

        estado_vacio = QLabel("No hay cambios de propietario registrados para esta casa.")
        estado_vacio.setObjectName("estadoVacioCasas")
        estado_vacio.setAlignment(Qt.AlignmentFlag.AlignCenter)
        estado_vacio.setVisible(not self._historial)
        self._tabla_historial.setVisible(bool(self._historial))

        boton_cerrar = BotonAccionContextual(
            "Cerrar",
            icono="x.svg",
            variante=resolver_variante_boton_modal("Cerrar", "neutro"),
            centrado=True,
            mostrar_icono=True,
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
                background: {paleta["fondo_tabla_cuerpo"]};
                border: none;
                border-radius: 4px;
                alternate-background-color: {paleta["fondo_tabla_fila_alterna"]};
                color: {paleta["texto_input"]};
                padding: 0 0 8px 0;
            }}
            QWidget#viewportTablaHistorialCasa {{
                background: transparent;
                border: none;
            }}
            QTableWidget#tablaHistorialCasa QHeaderView::section {{
                background: {paleta["fondo_tabla_header_destacado"]};
                color: {paleta["texto_input"]};
                border: none;
                border-right: 1px solid {paleta["borde_tabla"]};
                border-bottom: 1px solid {paleta["borde_tabla"]};
                padding: 10px 12px;
                font-size: 12px;
                font-weight: 800;
            }}
            QTableWidget#tablaHistorialCasa::item {{
                padding: 10px 12px;
                border-bottom: 1px solid {paleta["borde_tabla"]};
                background: {paleta["fondo_tabla_fila"]};
            }}
            QTableWidget#tablaHistorialCasa::item:alternate {{
                background: {paleta["fondo_tabla_fila_alterna"]};
            }}
            QTableWidget#tablaHistorialCasa::item:selected {{
                background: {paleta["fondo_tabla_seleccion"]};
            }}
            """
        )


class DialogoDetalleCasa(DialogoBaseSigqua):
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
        self.setMinimumWidth(860)
        self.setMinimumHeight(620)
        self._construir_ui()

    @property
    def accion_resultado(self) -> str:
        return self._accion_resultado

    def _construir_ui(self) -> None:
        casa = self._detalle.casa
        titulo = QLabel("Detalle de casa")
        titulo.setObjectName("tituloDialogoSigqua")
        descripcion = QLabel(
            "Consulta estado de servicio, deuda, plan activo y trazabilidad de propietarios."
        )
        descripcion.setObjectName("descripcionDialogoSigqua")
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
        fila_codigo = QHBoxLayout()
        fila_codigo.setContentsMargins(0, 0, 0, 0)
        fila_codigo.setSpacing(6)
        codigo = QLabel(casa.codigo)
        codigo.setObjectName("codigoCasaDetalle")
        boton_copiar_id = self._crear_boton_copiar_id(casa.identificador)
        nombre = QLabel(casa.resumen_propietario)
        nombre.setObjectName("nombreCasaDetalle")
        fila_codigo.addWidget(codigo)
        fila_codigo.addWidget(boton_copiar_id, alignment=Qt.AlignmentFlag.AlignVCenter)
        fila_codigo.addStretch(1)
        bloque_nombre.addLayout(fila_codigo)
        bloque_nombre.addWidget(nombre)

        estado = QLabel(casa.estado_servicio.title())
        estado.setObjectName("badgeDetalleCasa")
        estado.setProperty("activo", casa.estado_servicio == ESTADO_SERVICIO_ACTIVO)
        estado.style().unpolish(estado)
        estado.style().polish(estado)

        estado_administrativo = QLabel(casa.estado_administrativo.title())
        estado_administrativo.setObjectName("badgeDetalleCasaSecundario")
        estado_administrativo.setProperty(
            "activo",
            casa.estado_administrativo == ESTADO_ADMINISTRATIVO_OPERATIVA,
        )
        estado_administrativo.style().unpolish(estado_administrativo)
        estado_administrativo.style().polish(estado_administrativo)

        fila_superior.addLayout(bloque_nombre, 1)
        fila_badges = QVBoxLayout()
        fila_badges.setContentsMargins(0, 0, 0, 0)
        fila_badges.setSpacing(6)
        fila_badges.addWidget(estado, alignment=Qt.AlignmentFlag.AlignRight)
        fila_badges.addWidget(estado_administrativo, alignment=Qt.AlignmentFlag.AlignRight)
        fila_superior.addLayout(fila_badges)

        encabezado_seccion_contexto = self._crear_encabezado_seccion_detalle(
            "Contexto operativo",
            "Identifica el propietario actual, barrio y trazabilidad base de la casa.",
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
                "Antecedente de servicio",
                casa.resumen_antecedente_servicio,
            ),
            1,
            1,
        )
        grid_info.addWidget(
            self._crear_campo_detalle(
                "Creado",
                self._formateador_fecha(casa.creado_en),
            ),
            2,
            0,
        )
        grid_info.addWidget(
            self._crear_campo_detalle(
                "Ultima actualizacion",
                self._formateador_fecha(casa.actualizado_en),
            ),
            2,
            1,
        )
        grid_info.addWidget(
            self._crear_campo_detalle(
                "Ultimo cambio de dueno",
                self._formateador_fecha(self._detalle.ultima_fecha_cambio_dueno),
            ),
            3,
            0,
        )
        grid_info.addWidget(
            self._crear_campo_detalle(
                "Motivo administrativo",
                casa.motivo_estado_administrativo.replace("_", " ").title()
                if casa.motivo_estado_administrativo != MOTIVO_ESTADO_ADMINISTRATIVO_NINGUNO
                else "Sin bloqueo administrativo",
            ),
            3,
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
        reactivacion = self._crear_campo_detalle(
            "Reactivacion fisica",
            (
                "Resolver desde Pagos > Conexion/Reconexion."
                if casa.estado_servicio == ESTADO_SERVICIO_CORTADO
                else "Disponible desde la accion Cortar servicio cuando corresponda."
            ),
        )
        reactivacion.setObjectName("campoDetalleCasaAmplio")

        fila_acciones = QHBoxLayout()
        fila_acciones.setSpacing(10)
        boton_cerrar = BotonAccionContextual(
            "Cerrar",
            icono="x.svg",
            variante=resolver_variante_boton_modal("Cerrar", "neutro"),
            centrado=True,
            mostrar_icono=True,
        )
        boton_historial = BotonAccionContextual(
            "Ver historial",
            icono="clock.svg",
            variante="informacion",
            centrado=True,
            mostrar_icono=True,
        )
        boton_dueno = BotonAccionContextual(
            "Cambiar dueno",
            icono="user.svg",
            variante="edicion",
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
        boton_corte = BotonAccionContextual(
            "Cortar servicio",
            icono="alert-triangle.svg",
            variante="salida",
            centrado=True,
            mostrar_icono=True,
        )
        boton_cerrar.clicked.connect(self.reject)
        boton_historial.clicked.connect(self._abrir_historial)
        boton_dueno.clicked.connect(self._abrir_cambio_dueno)
        boton_editar.clicked.connect(self._solicitar_edicion)
        boton_corte.clicked.connect(self._solicitar_corte_servicio)
        fila_acciones.addWidget(boton_cerrar)
        fila_acciones.addStretch(1)
        fila_acciones.addWidget(boton_historial)
        fila_acciones.addWidget(boton_dueno)
        if casa.estado_servicio == ESTADO_SERVICIO_ACTIVO:
            fila_acciones.addWidget(boton_corte)
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
                [historial, observaciones, reactivacion],
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
        DialogoHistorialPropietariosCasa(
            casa=self._detalle.casa,
            historial=self._detalle.historial_propietarios,
            formateador_fecha=self._formateador_fecha,
            parent=self,
        ).exec()

    def _abrir_cambio_dueno(self) -> None:
        self._accion_resultado = "cambiar_dueno"
        self.accept()

    def _solicitar_corte_servicio(self) -> None:
        self._accion_resultado = "cortar_servicio"
        self.accept()

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
            QLabel#badgeDetalleCasaSecundario {{
                border-radius: {radio}px;
                padding: 6px 10px;
                font-size: 12px;
                font-weight: 800;
                color: {paleta["texto_badge"]};
                background: {paleta["fondo_badge"]};
                border: 1px solid {paleta["borde_suave"]};
            }}
            QLabel#badgeDetalleCasaSecundario[activo="true"] {{
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


class DialogoConfirmacionEstadoCasa(DialogoConfirmacionSigqua):
    """Modal de confirmacion para cambiar suspension administrativa."""

    def __init__(self, casa: Casa, parent: QWidget | None = None) -> None:
        nuevo_estado = (
            "reactivar"
            if casa.estado_administrativo == ESTADO_ADMINISTRATIVO_SUSPENDIDA
            else "suspender"
        )
        super().__init__(
            titulo="Confirmar cambio administrativo",
            descripcion=(
                f"Estas a punto de {nuevo_estado} administrativamente la casa seleccionada. "
                "Este atajo no cambia el estado fisico del servicio."
            ),
            detalles=(
                ("Casa", casa.codigo),
                ("Abonado actual", casa.resumen_propietario),
                ("Barrio", casa.barrio_nombre),
                ("Estado fisico", casa.estado_servicio.title()),
                ("Estado administrativo", casa.estado_administrativo.title()),
            ),
            texto_confirmar=nuevo_estado.title(),
            icono="alert-triangle.svg",
            variante_confirmar="salida" if nuevo_estado == "suspender" else "primario",
            parent=parent,
        )


class DialogoCorteServicioCasa(DialogoBaseSigqua):
    """Modal para confirmar el corte fisico del servicio."""

    def __init__(
        self,
        detalle: DetalleCasa,
        formateador_moneda: Callable[[int], str],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._detalle = detalle
        self._formateador_moneda = formateador_moneda
        self.setMinimumWidth(640)
        self.setMinimumHeight(520)
        self._construir_ui()

    @property
    def observaciones(self) -> str:
        return self._campo_observaciones.toPlainText().strip()

    def obtener_formulario(self) -> FormularioCorteServicioCasa:
        return FormularioCorteServicioCasa(
            casa_id=int(self._detalle.casa.identificador or 0),
            observaciones=self.observaciones,
        )

    def accept(self) -> None:
        if not self.observaciones:
            self._mensaje.setText("Describe las observaciones del corte antes de continuar.")
            self._mensaje.setVisible(True)
            return
        self._mensaje.setVisible(False)
        super().accept()

    def _construir_ui(self) -> None:
        casa = self._detalle.casa
        titulo = QLabel("Confirmar corte de servicio")
        titulo.setObjectName("tituloDialogoSigqua")
        descripcion = QLabel(
            "Esta accion registra un corte fisico del servicio. La reactivacion posterior se gestiona desde Pagos > Conexión/Reconexion."
        )
        descripcion.setObjectName("descripcionDialogoSigqua")
        descripcion.setWordWrap(True)

        panel_contexto = QFrame()
        panel_contexto.setObjectName("bloqueDialogoSigqua")
        layout_contexto = QVBoxLayout(panel_contexto)
        layout_contexto.setContentsMargins(14, 14, 14, 14)
        layout_contexto.setSpacing(10)

        grid_contexto = QGridLayout()
        grid_contexto.setContentsMargins(0, 0, 0, 0)
        grid_contexto.setHorizontalSpacing(10)
        grid_contexto.setVerticalSpacing(10)
        grid_contexto.addWidget(self._crear_campo_contexto("Casa", casa.codigo), 0, 0)
        grid_contexto.addWidget(
            self._crear_campo_contexto("Abonado actual", casa.resumen_propietario),
            0,
            1,
        )
        grid_contexto.addWidget(
            self._crear_campo_contexto("Barrio", casa.barrio_nombre or "Sin barrio"),
            1,
            0,
        )
        grid_contexto.addWidget(
            self._crear_campo_contexto(
                "Deuda actual",
                self._formateador_moneda(casa.deuda_total_centavos),
            ),
            1,
            1,
        )
        grid_contexto.addWidget(
            self._crear_campo_contexto("Estado fisico", casa.estado_servicio.title()),
            2,
            0,
        )
        grid_contexto.addWidget(
            self._crear_campo_contexto(
                "Estado administrativo",
                casa.estado_administrativo.title(),
            ),
            2,
            1,
        )
        layout_contexto.addLayout(grid_contexto)

        panel_observaciones = QFrame()
        panel_observaciones.setObjectName("bloqueDialogoSigqua")
        layout_observaciones = QVBoxLayout(panel_observaciones)
        layout_observaciones.setContentsMargins(14, 14, 14, 14)
        layout_observaciones.setSpacing(8)
        etiqueta_observaciones = QLabel("Observaciones del corte")
        etiqueta_observaciones.setObjectName("etiquetaDatoDialogoSigqua")
        ayuda_observaciones = QLabel(
            "Explica brevemente por que se realiza el corte o cualquier contexto operativo relevante."
        )
        ayuda_observaciones.setObjectName("descripcionDialogoSigqua")
        ayuda_observaciones.setWordWrap(True)
        self._campo_observaciones = QPlainTextEdit()
        self._campo_observaciones.setPlaceholderText("Ejemplo: corte operativo manual por revision en campo.")
        self._campo_observaciones.setFixedHeight(120)
        layout_observaciones.addWidget(etiqueta_observaciones)
        layout_observaciones.addWidget(ayuda_observaciones)
        layout_observaciones.addWidget(self._campo_observaciones)

        self._mensaje = QLabel("")
        self._mensaje.setObjectName("mensajeErrorDialogoSigqua")
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
            "Cortar servicio",
            variante="salida",
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
        self.layout_cuerpo.addWidget(panel_contexto)
        self.layout_cuerpo.addWidget(panel_observaciones)
        self.layout_cuerpo.addWidget(self._mensaje)
        self.layout_pie.addLayout(fila_acciones)

    def _crear_campo_contexto(self, etiqueta: str, valor: str) -> QWidget:
        bloque = QWidget()
        layout = QVBoxLayout(bloque)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)
        label_etiqueta = QLabel(etiqueta)
        label_etiqueta.setObjectName("etiquetaDatoDialogoSigqua")
        label_valor = QLabel(valor)
        label_valor.setObjectName("valorDetalleCasa")
        label_valor.setWordWrap(True)
        layout.addWidget(label_etiqueta)
        layout.addWidget(label_valor)
        return bloque


class VistaCasas(QWidget):
    """Pantalla principal del modulo de casas."""

    DURACION_MENSAJE_MS = 3200
    RADIO_PANEL_TABLA = 16
    ANCHO_COLUMNA_ACCIONES = 96

    filtro_texto_cambiado = Signal(str)
    filtro_rapido_cambiado = Signal(str)
    pagina_cambiada = Signal(int)
    exportar_solicitado = Signal()
    nueva_casa_solicitada = Signal()
    detalle_casa_solicitado = Signal(int)
    editar_casa_solicitado = Signal(int)
    cambio_estado_solicitado = Signal(int)
    corte_servicio_solicitado = Signal(int)
    historial_casa_solicitado = Signal(int)
    cambio_dueno_solicitado = Signal(int)

    def __init__(self) -> None:
        super().__init__()
        self._pagina_actual = 1
        self._total_paginas = 1
        self._tema_actual = TEMA_SIGQUA_PREDETERMINADO
        self._paleta_tema = obtener_paleta_tema(self._tema_actual)
        self._temporizador_mensaje = QTimer(self)
        self._temporizador_mensaje.setSingleShot(True)
        self._temporizador_mensaje.timeout.connect(self._ocultar_mensaje)
        self._construir_ui()
        self._aplicar_estilos()

    def aplicar_tema(self, nombre_tema: str) -> None:
        self._tema_actual = (
            resolver_nombre_tema(nombre_tema)
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
            self._tabla.setCellWidget(fila, 6, self._crear_badge_servicio(casa))
            self._tabla.setCellWidget(fila, 7, self._crear_badge_operativo(casa))
            self._tabla.setCellWidget(fila, 8, self._crear_acciones_fila(casa))

        self._tabla.resizeRowsToContents()
        self._tabla.setColumnWidth(8, max(self._tabla.columnWidth(8), self.ANCHO_COLUMNA_ACCIONES))
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

    def aplicar_busqueda_externa(self, texto: str) -> None:
        texto_normalizado = texto.strip()
        if self._campo_busqueda.text() != texto_normalizado:
            self._campo_busqueda.setText(texto_normalizado)
            return
        self.filtro_texto_cambiado.emit(texto_normalizado)

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

    def solicitar_corte_servicio(
        self,
        detalle: DetalleCasa,
        formateador_moneda: Callable[[int], str],
    ) -> FormularioCorteServicioCasa | None:
        dialogo = DialogoCorteServicioCasa(
            detalle=detalle,
            formateador_moneda=formateador_moneda,
            parent=self,
        )
        if dialogo.exec() != QDialog.DialogCode.Accepted:
            return None
        return dialogo.obtener_formulario()

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

        fila_acciones = QHBoxLayout()
        fila_acciones.setSpacing(8)
        fila_acciones.addStretch(1)
        boton_exportar = crear_boton_operativo("Exportar")
        boton_nuevo = crear_boton_operativo("Nueva casa", principal=True)
        boton_exportar.clicked.connect(self.exportar_solicitado.emit)
        boton_nuevo.clicked.connect(self.nueva_casa_solicitada.emit)
        fila_acciones.addWidget(boton_exportar)
        fila_acciones.addWidget(boton_nuevo)

        encabezado.addStretch(1)
        encabezado.addLayout(fila_acciones)

        self._mensaje = QLabel("")
        self._mensaje.setObjectName("mensajeCasas")
        self._mensaje.setVisible(False)
        self._mensaje.setWordWrap(True)

        fila_tarjetas = QGridLayout()
        fila_tarjetas.setHorizontalSpacing(10)
        fila_tarjetas.setVerticalSpacing(10)
        self._tarjeta_total = TarjetaResumenCasa("home.svg", "#75C7F0")
        self._tarjeta_activos = TarjetaResumenCasa("circle-check.svg", "#8de8c7")
        self._tarjeta_con_deuda = TarjetaResumenCasa("alert-triangle.svg", "#f7cc7a")
        self._tarjeta_morosos = TarjetaResumenCasa("clock.svg", "#F5B84B")
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
            (FILTRO_CASAS_DEUDA_MAYOR_5, "Deuda > 5 meses"),
            (FILTRO_CASAS_CORTADAS, "Cortadas"),
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

        self._tabla = QTableWidget(0, 9)
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
                "Servicio",
                "Operativo",
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
        self._tabla.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        self._tabla.horizontalHeader().setSectionResizeMode(8, QHeaderView.ResizeMode.Interactive)
        self._tabla.setColumnWidth(8, self.ANCHO_COLUMNA_ACCIONES)
        self._tabla.verticalHeader().setDefaultSectionSize(74)
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

    def _crear_badge_servicio(self, casa: Casa) -> QWidget:
        contenedor = QWidget()
        layout = QVBoxLayout(contenedor)
        layout.setContentsMargins(0, 0, 0, 0)

        badge = QLabel(casa.estado_servicio.title())
        badge.setObjectName("badgeEstadoCasa")
        badge.setProperty("activo", casa.estado_servicio == ESTADO_SERVICIO_ACTIVO)
        badge.style().unpolish(badge)
        badge.style().polish(badge)
        layout.addWidget(badge, alignment=Qt.AlignmentFlag.AlignCenter)
        return contenedor

    def _crear_badge_operativo(self, casa: Casa) -> QWidget:
        contenedor = QWidget()
        layout = QVBoxLayout(contenedor)
        layout.setContentsMargins(0, 0, 0, 0)

        badge_admin = QLabel(casa.estado_administrativo.title())
        badge_admin.setObjectName("badgeEstadoCasaSecundario")
        badge_admin.setProperty(
            "activo",
            casa.estado_administrativo == ESTADO_ADMINISTRATIVO_OPERATIVA,
        )
        badge_admin.style().unpolish(badge_admin)
        badge_admin.style().polish(badge_admin)
        layout.addWidget(badge_admin, alignment=Qt.AlignmentFlag.AlignCenter)
        return contenedor

    def _crear_acciones_fila(self, casa: Casa) -> QWidget:
        contenedor = QWidget()
        contenedor.setObjectName("contenedorAccionesCasa")
        contenedor.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        contenedor.setMinimumWidth(self.ANCHO_COLUMNA_ACCIONES)
        contenedor.setMinimumHeight(74)
        layout = QHBoxLayout(contenedor)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        boton_detalle = BotonIconoFilaCasa("eye.svg", "#4fa3ff", "Ver detalle")
        boton_detalle.clicked.connect(
            lambda checked=False, identificador=casa.identificador: self.detalle_casa_solicitado.emit(
                int(identificador or 0)
            )
        )
        layout.addWidget(boton_detalle)
        return contenedor

    def _actualizar_estado_vacio(self, sin_datos: bool) -> None:
        self._estado_vacio.setVisible(sin_datos)
        self._tabla.setVisible(not sin_datos)

    def _aplicar_estilos(self) -> None:
        radio_panel_tabla = self.RADIO_PANEL_TABLA
        fondo_header_destacado = obtener_fondo_header_destacado(self._tema_actual)
        self.setStyleSheet(
            """
            QWidget#vistaCasas {
                background: transparent;
            }
            QLabel#tituloModulo {
                color: #75C7F0;
                font-size: 19px;
                font-weight: 900;
            }
            QLabel#descripcionModulo,
            QLabel#textoPieCasas,
            QLabel#detalleTarjetaResumen {
                color: #C5DDEE;
                font-size: 11px;
                font-weight: 600;
            }
            QLabel#mensajeCasas {
                color: #DDFBF0;
                font-size: 12px;
                font-weight: 700;
                padding: 8px 10px;
                border-radius: 12px;
                background-color: rgba(55, 211, 153, 0.16);
                border: 1px solid rgba(55, 211, 153, 0.26);
            }
            QLabel#mensajeCasas[error="true"] {
                color: #FFE3E3;
                background-color: rgba(242, 116, 116, 0.15);
                border: 1px solid rgba(242, 116, 116, 0.28);
            }
            QFrame#panelOperativoCasas,
            QFrame#tarjetaResumenCasas {
                background: """
            + fondo_header_destacado
            + """;
                border: 1px solid rgba(126, 167, 196, 0.48);
                border-radius: 18px;
            }
            QFrame#panelTablaCasas {
                background: """
            + fondo_header_destacado
            + """;
                border: 1px solid rgba(126, 167, 196, 0.48);
                border-radius: """
            + str(radio_panel_tabla)
            + """px;
            }
            QTableWidget#tablaCasas {
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
            QTableWidget#tablaCasas QHeaderView::section:last {
                border-top-right-radius: """
            + str(radio_panel_tabla)
            + """px;
            }
            QTableWidget#tablaCasas::item {
                padding: 9px 12px;
                border-bottom: 1px solid """
            + self._paleta_tema["borde_tabla"]
            + """;
                background: """
            + self._paleta_tema["fondo_tabla_fila"]
            + """;
            }
            QTableWidget#tablaCasas::item:alternate {
                background: """
            + self._paleta_tema["fondo_tabla_fila_alterna"]
            + """;
            }
            QTableWidget#tablaCasas::item:selected {
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
            QPushButton#chipFiltroCasa {
                min-height: 30px;
                border-radius: 11px;
                padding: 0 12px;
                background: rgba(13, 42, 69, 0.88);
                border: 1px solid rgba(126, 167, 196, 0.30);
                color: #F4FAFF;
                font-size: 11px;
                font-weight: 700;
            }
            QPushButton#chipFiltroCasa:hover {
                background: rgba(126, 167, 196, 0.30);
            }
            QPushButton#chipFiltroCasa:checked {
                color: #75C7F0;
                background: #49A9DC;
                border-color: rgba(126, 167, 196, 0.55);
            }
            QLabel#badgeEstadoCasa {
                border-radius: 11px;
                padding: 6px 10px;
                font-size: 11px;
                font-weight: 800;
                color: #C5DDEE;
                background: rgba(142, 168, 188, 0.22);
                border: 1px solid rgba(126, 167, 196, 0.30);
            }
            QLabel#badgeEstadoCasa[activo="true"] {
                color: #DDFBF0;
                background: rgba(55, 211, 153, 0.22);
                border-color: rgba(55, 211, 153, 0.26);
            }
            QLabel#badgeEstadoCasaSecundario {
                border-radius: 10px;
                padding: 5px 8px;
                font-size: 10px;
                font-weight: 800;
                color: #C5DDEE;
                background: rgba(142, 168, 188, 0.18);
                border: 1px solid rgba(126, 167, 196, 0.30);
            }
            QLabel#badgeEstadoCasaSecundario[activo="true"] {
                color: #DDFBF0;
                background: rgba(55, 211, 153, 0.18);
                border-color: rgba(55, 211, 153, 0.22);
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

