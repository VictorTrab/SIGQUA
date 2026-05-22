"""Vista PySide6 del modulo de abonados."""

from __future__ import annotations

from typing import Iterable

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
from comun.ui.componentes import COLOR_FONDO_DIALOGO, RADIO_TARJETA_DIALOGO
from comun.ui.temas import (
    TEMA_SICAP_PREDETERMINADO,
    obtener_fondo_header_destacado,
    obtener_paleta_tema,
)
from modulos.abonados.entidades import (
    Abonado,
    FILTRO_ABONADOS_CON_MORA,
    FILTRO_ABONADOS_CON_PLAN,
    FILTRO_ABONADOS_SIN_MORA,
    FILTRO_ABONADOS_TODOS,
    FormularioAbonado,
    OpcionBarrio,
    PaginaAbonados,
    ResumenAbonados,
)


class TarjetaResumenAbonado(QFrame):
    """Tarjeta de resumen para el encabezado del modulo."""

    def __init__(self, icono: str, color_icono: str) -> None:
        super().__init__()
        self.setObjectName("tarjetaResumenAbonados")
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


class BotonIconoFilaAbonado(QToolButton):
    """Boton de accion compacto para filas del listado."""

    COLOR_BASE = "#c8d6f1"
    INTERVALO_TOOLTIP_MS = 1600

    def __init__(self, icono: str, color_hover: str, tooltip: str) -> None:
        super().__init__()
        self._icono = icono
        self._color_hover = color_hover
        self._color_base = self.COLOR_BASE
        self._temporizador_tooltip = QElapsedTimer()
        self.setObjectName("botonIconoFilaAbonado")
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


class DialogoFormularioAbonado(DialogoBaseSicap):
    """Modal para crear o editar abonados."""

    def __init__(
        self,
        barrios: Iterable[OpcionBarrio],
        abonado: Abonado | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._barrios = list(barrios)
        self._abonado = abonado
        self.setMinimumWidth(620)
        self.setMinimumHeight(560)
        self._construir_ui()

    def obtener_formulario(self) -> FormularioAbonado:
        barrio_id = self._combo_barrio.currentData()
        return FormularioAbonado(
            identificador=None if self._abonado is None else self._abonado.identificador,
            dni=self._campo_dni.text(),
            nombre_completo=self._campo_nombre.text(),
            telefono=self._campo_telefono.text(),
            barrio_id=int(barrio_id) if barrio_id is not None else None,
            direccion_referencia=self._campo_direccion.toPlainText(),
            observaciones=self._campo_observaciones.toPlainText(),
            estado=self._combo_estado.currentText(),
        )

    def accept(self) -> None:
        if len(self._campo_dni.text().strip()) < 8:
            self._mensaje.setText("Indica un DNI valido para continuar.")
            self._mensaje.setVisible(True)
            return
        if not self._campo_nombre.text().strip():
            self._mensaje.setText("Indica el nombre completo del abonado.")
            self._mensaje.setVisible(True)
            return
        if self._combo_barrio.currentData() is None:
            self._mensaje.setText("Selecciona un barrio valido.")
            self._mensaje.setVisible(True)
            return
        self._mensaje.setVisible(False)
        super().accept()

    def _construir_ui(self) -> None:
        titulo = QLabel("Editar abonado" if self._abonado else "Nuevo abonado")
        titulo.setObjectName("tituloDialogoSicap")
        descripcion = QLabel(
            "Completa la informacion principal del abonado y su relacion operativa con el barrio."
        )
        descripcion.setObjectName("descripcionDialogoSicap")
        descripcion.setWordWrap(True)

        formulario = QGridLayout()
        formulario.setContentsMargins(0, 0, 0, 0)
        formulario.setHorizontalSpacing(10)
        formulario.setVerticalSpacing(10)

        self._campo_dni = QLineEdit()
        self._campo_dni.setPlaceholderText("DNI del abonado")
        self._campo_nombre = QLineEdit()
        self._campo_nombre.setPlaceholderText("Nombre completo")
        self._campo_telefono = QLineEdit()
        self._campo_telefono.setPlaceholderText("Telefono")
        self._combo_barrio = QComboBox()
        self._combo_barrio.addItem("Selecciona un barrio", None)
        for barrio in self._barrios:
            self._combo_barrio.addItem(barrio.nombre, barrio.identificador)
        self._combo_estado = QComboBox()
        self._combo_estado.addItems(["ACTIVO", "INACTIVO"])
        self._campo_direccion = QPlainTextEdit()
        self._campo_direccion.setPlaceholderText("Direccion o referencia")
        self._campo_direccion.setFixedHeight(78)
        self._campo_observaciones = QPlainTextEdit()
        self._campo_observaciones.setPlaceholderText("Observaciones")
        self._campo_observaciones.setFixedHeight(78)

        if self._abonado is not None:
            self._campo_dni.setText(self._abonado.dni)
            self._campo_nombre.setText(self._abonado.nombre_completo)
            self._campo_telefono.setText(self._abonado.telefono)
            indice_barrio = self._combo_barrio.findData(self._abonado.barrio_id)
            if indice_barrio >= 0:
                self._combo_barrio.setCurrentIndex(indice_barrio)
            self._combo_estado.setCurrentText(self._abonado.estado)
            self._campo_direccion.setPlainText(self._abonado.direccion_referencia)
            self._campo_observaciones.setPlainText(self._abonado.observaciones)

        formulario.addWidget(self._crear_bloque_formulario("DNI", self._campo_dni), 0, 0)
        formulario.addWidget(
            self._crear_bloque_formulario("Telefono", self._campo_telefono),
            0,
            1,
        )
        formulario.addWidget(
            self._crear_bloque_formulario("Nombre completo", self._campo_nombre),
            1,
            0,
            1,
            2,
        )
        formulario.addWidget(self._crear_bloque_formulario("Barrio", self._combo_barrio), 2, 0)
        formulario.addWidget(self._crear_bloque_formulario("Estado", self._combo_estado), 2, 1)

        panel_datos = self._crear_panel_formulario(
            "Datos personales",
            "Registra identificacion, contacto y pertenencia territorial del abonado.",
        )
        panel_datos.layout().addLayout(formulario)

        panel_notas = self._crear_panel_formulario(
            "Contexto operativo",
            "Completa la direccion de referencia y cualquier observacion administrativa.",
        )
        notas_layout = QVBoxLayout()
        notas_layout.setContentsMargins(0, 0, 0, 0)
        notas_layout.setSpacing(10)
        notas_layout.addWidget(
            self._crear_bloque_formulario("Direccion", self._campo_direccion)
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


class DialogoDetalleAbonado(DialogoBaseSicap):
    """Modal para consultar detalle del abonado."""

    def __init__(
        self,
        abonado: Abonado,
        fecha_creacion: str,
        fecha_actualizada: str,
        deuda_formateada: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._abonado = abonado
        self._fecha_creacion = fecha_creacion
        self._fecha_actualizada = fecha_actualizada
        self._deuda_formateada = deuda_formateada
        self._accion_resultado = "cerrar"
        self.setMinimumWidth(820)
        self.setMinimumHeight(620)
        self._construir_ui()

    @property
    def accion_resultado(self) -> str:
        return self._accion_resultado

    def _construir_ui(self) -> None:
        titulo = QLabel("Detalle de abonado")
        titulo.setObjectName("tituloDialogoSicap")
        descripcion = QLabel(
            "Consulta informacion principal, ubicacion operativa y estado financiero resumido."
        )
        descripcion.setObjectName("descripcionDialogoSicap")
        descripcion.setWordWrap(True)

        scroll = QScrollArea()
        scroll.setObjectName("scrollDetalleAbonado")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        contenedor_scroll = QWidget()
        contenedor_scroll.setObjectName("contenedorScrollDetalleAbonado")
        layout_scroll = QVBoxLayout(contenedor_scroll)
        layout_scroll.setContentsMargins(0, 0, 0, 0)
        layout_scroll.setSpacing(12)

        panel_detalle = QFrame()
        panel_detalle.setObjectName("panelContenidoDetalleAbonado")
        panel_detalle_layout = QVBoxLayout(panel_detalle)
        panel_detalle_layout.setContentsMargins(18, 18, 18, 18)
        panel_detalle_layout.setSpacing(14)

        fila_superior = QHBoxLayout()
        fila_superior.setSpacing(12)
        bloque_nombre = QVBoxLayout()
        bloque_nombre.setSpacing(4)
        codigo = QLabel(self._abonado.dni)
        codigo.setObjectName("codigoAbonadoDetalle")
        nombre = QLabel(self._abonado.nombre_completo)
        nombre.setObjectName("nombreAbonadoDetalle")
        bloque_nombre.addWidget(codigo)
        bloque_nombre.addWidget(nombre)

        estado = QLabel(self._abonado.estado.title())
        estado.setObjectName("badgeDetalleAbonado")
        estado.setProperty("activo", self._abonado.estado == "ACTIVO")
        estado.style().unpolish(estado)
        estado.style().polish(estado)

        fila_superior.addLayout(bloque_nombre, 1)
        fila_superior.addWidget(estado, alignment=Qt.AlignmentFlag.AlignTop)

        encabezado_contexto = self._crear_encabezado_seccion_detalle(
            "Contexto operativo",
            "Consulta contacto, barrio y fechas operativas principales del abonado.",
        )
        grid_info = QGridLayout()
        grid_info.setHorizontalSpacing(14)
        grid_info.setVerticalSpacing(14)
        grid_info.addWidget(
            self._crear_campo_detalle("Telefono", self._abonado.telefono or "Sin telefono"),
            0,
            0,
        )
        grid_info.addWidget(
            self._crear_campo_detalle("Barrio", self._abonado.barrio_nombre or "Sin barrio"),
            0,
            1,
        )
        grid_info.addWidget(
            self._crear_campo_detalle("Plan activo", "Si" if self._abonado.tiene_plan_activo else "No"),
            1,
            0,
        )
        grid_info.addWidget(self._crear_campo_detalle("Creado", self._fecha_creacion), 1, 1)
        grid_info.addWidget(
            self._crear_campo_detalle("Ultima actualizacion", self._fecha_actualizada),
            2,
            0,
            1,
            2,
        )

        encabezado_finanzas = self._crear_encabezado_seccion_detalle(
            "Resumen financiero",
            "Visualiza rapidamente casas asociadas, mora y deuda pendiente.",
        )
        fila_metricas = QHBoxLayout()
        fila_metricas.setSpacing(12)
        fila_metricas.addWidget(
            self._crear_tarjeta_detalle("Casas", str(self._abonado.total_casas)),
            1,
        )
        fila_metricas.addWidget(
            self._crear_tarjeta_detalle("Meses en mora", str(self._abonado.meses_en_mora)),
            1,
        )
        fila_metricas.addWidget(
            self._crear_tarjeta_detalle("Deuda", self._deuda_formateada),
            1,
        )

        direccion = self._crear_campo_detalle(
            "Direccion",
            self._abonado.direccion_referencia or "Sin referencia registrada.",
        )
        direccion.setObjectName("campoDetalleAbonadoAmplio")
        observaciones = self._crear_campo_detalle(
            "Observaciones",
            self._abonado.observaciones or "Sin observaciones registradas.",
        )
        observaciones.setObjectName("campoDetalleAbonadoAmplio")

        separador_acciones = QFrame()
        separador_acciones.setObjectName("separadorDetalleAbonado")
        separador_acciones.setFixedHeight(1)

        fila_acciones = QHBoxLayout()
        fila_acciones.setSpacing(10)
        variante_cerrar = resolver_variante_boton_modal("Cerrar", "neutro")
        boton_cerrar = BotonAccionContextual(
            "Cerrar",
            variante=variante_cerrar,
            centrado=True,
            mostrar_icono=False,
        )
        boton_editar = BotonAccionContextual(
            "Editar",
            variante="edicion",
            centrado=True,
            mostrar_icono=False,
        )
        boton_ver_casas = BotonAccionContextual(
            "Ver casas",
            variante="informacion",
            centrado=True,
            mostrar_icono=False,
        )
        boton_cerrar.setMinimumWidth(124)
        boton_ver_casas.setMinimumWidth(132)
        boton_editar.setMinimumWidth(124)
        boton_cerrar.clicked.connect(self.reject)
        boton_ver_casas.clicked.connect(self._abrir_casas)
        boton_editar.clicked.connect(self._solicitar_edicion)
        fila_acciones.addWidget(boton_cerrar)
        fila_acciones.addStretch(1)
        fila_acciones.addWidget(boton_ver_casas)
        fila_acciones.addWidget(boton_editar)

        panel_detalle_layout.addLayout(fila_superior)
        panel_detalle_layout.addWidget(
            self._crear_bloque_seccion_detalle(encabezado_contexto, grid_info)
        )
        panel_detalle_layout.addWidget(
            self._crear_bloque_seccion_detalle(encabezado_finanzas, fila_metricas)
        )
        panel_detalle_layout.addWidget(
            self._crear_bloque_seccion_detalle(
                self._crear_encabezado_seccion_detalle(
                    "Ubicacion y notas",
                    "Incluye la referencia operativa y observaciones administrativas del abonado.",
                ),
                [direccion, observaciones],
            )
        )
        panel_detalle_layout.addWidget(separador_acciones)
        panel_detalle_layout.addLayout(fila_acciones)
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
        label_titulo.setObjectName("tituloSeccionDetalleAbonado")
        label_descripcion = QLabel(descripcion)
        label_descripcion.setObjectName("descripcionSeccionDetalleAbonado")
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
        bloque.setObjectName("seccionDetalleAbonado")
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
        tarjeta.setObjectName("campoDetalleAbonado")
        layout = QVBoxLayout(tarjeta)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(5)

        label_etiqueta = QLabel(etiqueta)
        label_etiqueta.setObjectName("etiquetaDetalleAbonado")
        label_valor = QLabel(valor)
        label_valor.setObjectName("valorDetalleAbonado")
        label_valor.setWordWrap(True)

        layout.addWidget(label_etiqueta)
        layout.addWidget(label_valor)
        return tarjeta

    def _crear_tarjeta_detalle(self, titulo: str, valor: str) -> QFrame:
        tarjeta = QFrame()
        tarjeta.setObjectName("tarjetaMiniDetalleAbonado")
        layout = QVBoxLayout(tarjeta)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(4)

        label_titulo = QLabel(titulo)
        label_titulo.setObjectName("etiquetaDetalleAbonado")
        label_valor = QLabel(valor)
        label_valor.setObjectName("valorTarjetaMiniDetalleAbonado")
        layout.addWidget(label_titulo)
        layout.addWidget(label_valor)
        return tarjeta

    def _solicitar_edicion(self) -> None:
        self._accion_resultado = "editar"
        self.accept()

    def _abrir_casas(self) -> None:
        self._accion_resultado = "ver_casas"
        self.accept()

    def _aplicar_estilos(self) -> None:
        radio = RADIO_TARJETA_DIALOGO
        paleta = self._paleta_tema
        self.setStyleSheet(
            self.styleSheet()
            + f"""
            QScrollArea#scrollDetalleAbonado,
            QWidget#contenedorScrollDetalleAbonado {{
                background: transparent;
                border: none;
            }}
            QFrame#panelContenidoDetalleAbonado {{
                background: {self._color_fondo_dialogo};
                border: 1px solid {paleta["borde_principal"]};
                border-radius: {radio}px;
            }}
            QFrame#seccionDetalleAbonado {{
                background: {paleta["fondo_superficie"]};
                border: 1px solid {paleta["borde_principal"]};
                border-radius: {radio}px;
            }}
            QFrame#campoDetalleAbonado,
            QFrame#campoDetalleAbonadoAmplio,
            QFrame#tarjetaMiniDetalleAbonado {{
                background: {paleta["fondo_superficie_suave"]};
                border: 1px solid {paleta["borde_suave"]};
                border-radius: {radio}px;
            }}
            QFrame#separadorDetalleAbonado {{
                background: {paleta["borde_principal"]};
                border: none;
            }}
            QLabel#tituloSeccionDetalleAbonado {{
                color: {paleta["texto_principal"]};
                font-size: 14px;
                font-weight: 800;
            }}
            QLabel#descripcionSeccionDetalleAbonado {{
                color: {paleta["texto_suave"]};
                font-size: 11px;
                font-weight: 600;
            }}
            QLabel#codigoAbonadoDetalle {{
                color: {paleta["icono_tarjeta_info"]};
                font-size: 12px;
                font-weight: 800;
                letter-spacing: 0.08em;
            }}
            QLabel#nombreAbonadoDetalle {{
                color: {paleta["texto_principal"]};
                font-size: 19px;
                font-weight: 900;
            }}
            QLabel#badgeDetalleAbonado {{
                border-radius: {radio}px;
                padding: 6px 10px;
                font-size: 12px;
                font-weight: 800;
                color: {paleta["texto_badge"]};
                background: {paleta["fondo_badge"]};
                border: 1px solid {paleta["borde_suave"]};
            }}
            QLabel#badgeDetalleAbonado[activo="true"] {{
                color: {paleta["texto_badge_activo"]};
                background: {paleta["fondo_badge_activo"]};
                border-color: {paleta["borde_badge_activo"]};
            }}
            QLabel#etiquetaDetalleAbonado {{
                color: {paleta["texto_muted"]};
                font-size: 11px;
                font-weight: 700;
            }}
            QLabel#valorDetalleAbonado {{
                color: {paleta["texto_input"]};
                font-size: 12px;
                font-weight: 700;
            }}
            QLabel#valorTarjetaMiniDetalleAbonado {{
                color: {paleta["texto_principal"]};
                font-size: 20px;
                font-weight: 900;
            }}
            """
        )


class DialogoConfirmacionEstadoAbonado(DialogoConfirmacionSicap):
    """Modal de confirmacion para activar o inactivar abonados."""

    def __init__(self, abonado: Abonado, parent: QWidget | None = None) -> None:
        nuevo_estado = "inactivar" if abonado.estado == "ACTIVO" else "activar"
        detalle_casas = (
            f"{abonado.total_casas} casa(s) vinculada(s) pasaran a estado suspendido."
            if nuevo_estado == "inactivar" and abonado.total_casas > 0
            else (
                "No hay casas vinculadas que se vean afectadas por este cambio."
                if nuevo_estado == "inactivar"
                else (
                    f"{abonado.total_casas} casa(s) suspendida(s) por abonado inactivo "
                    "podrian volver a operativa."
                    if abonado.total_casas > 0
                    else "No hay casas vinculadas que reactivar con este cambio."
                )
            )
        )
        super().__init__(
            titulo="Confirmar cambio de estado",
            descripcion=(
                f"Estas a punto de {nuevo_estado} el abonado seleccionado. "
                "Verifica los datos antes de confirmar."
            ),
            detalles=(
                ("Abonado", abonado.nombre_completo),
                ("DNI", abonado.dni),
                ("Estado actual", abonado.estado.title()),
                ("Casas afectadas", detalle_casas),
                ("Accion", nuevo_estado.title()),
            ),
            texto_confirmar=nuevo_estado.title(),
            icono="alert-triangle.svg",
            variante_confirmar="salida" if nuevo_estado == "inactivar" else "primario",
            parent=parent,
        )


class VistaAbonados(QWidget):
    """Pantalla principal del modulo de abonados."""

    RADIO_PANEL_TABLA = 18
    ANCHO_COLUMNA_ACCIONES = 198
    DURACION_MENSAJE_MS = 5200

    filtro_texto_cambiado = Signal(str)
    filtro_rapido_cambiado = Signal(str)
    pagina_cambiada = Signal(int)
    exportar_solicitado = Signal()
    nuevo_abonado_solicitado = Signal()
    detalle_abonado_solicitado = Signal(int)
    editar_abonado_solicitado = Signal(int)
    cambio_estado_solicitado = Signal(int)
    ver_casas_abonado_solicitado = Signal(int)

    def __init__(self) -> None:
        super().__init__()
        self._tema_actual = TEMA_SICAP_PREDETERMINADO
        self._paleta_tema = obtener_paleta_tema(self._tema_actual)
        self._pagina_actual = 1
        self._total_paginas = 1
        self._temporizador_mensaje = QTimer(self)
        self._temporizador_mensaje.setSingleShot(True)
        self._temporizador_mensaje.timeout.connect(self._ocultar_mensaje)
        self._construir_ui()
        self._aplicar_estilos()

    def aplicar_tema(self, nombre_tema: str) -> None:
        self._tema_actual = nombre_tema if nombre_tema in ("oscuro", "claro") else TEMA_SICAP_PREDETERMINADO
        self._paleta_tema = obtener_paleta_tema(self._tema_actual)
        self._aplicar_estilos()
        for boton in self.findChildren(QPushButton):
            if boton.objectName() == "botonOperativo":
                aplicar_estilo_boton_operativo(boton, principal=False)
            elif boton.objectName() == "botonOperativoPrimario":
                aplicar_estilo_boton_operativo(boton, principal=True)
        for boton_icono in self.findChildren(BotonIconoFilaAbonado):
            boton_icono.aplicar_tema(self._tema_actual)

    def mostrar_resumen(self, resumen: ResumenAbonados) -> None:
        self._tarjeta_total.actualizar(
            "Total de abonados",
            str(resumen.total_abonados),
            "Base operativa registrada en el sistema.",
        )
        self._tarjeta_activos.actualizar(
            "Activos",
            str(resumen.abonados_activos),
            "Registros habilitados para gestion operativa.",
        )
        self._tarjeta_con_deuda.actualizar(
            "Con deuda",
            str(resumen.abonados_con_deuda),
            "Abonados con saldo pendiente en cargos vigentes.",
        )
        self._tarjeta_morosos.actualizar(
            "Morosos",
            str(resumen.abonados_morosos),
            "Con al menos un periodo vencido registrado.",
        )

    def mostrar_abonados(self, pagina: PaginaAbonados) -> None:
        self._pagina_actual = pagina.pagina_actual
        self._total_paginas = pagina.total_paginas
        self._tabla.setRowCount(0)

        for abonado in pagina.items:
            fila = self._tabla.rowCount()
            self._tabla.insertRow(fila)
            self._tabla.setItem(fila, 0, crear_item_tabla(abonado.dni))
            self._tabla.setItem(fila, 1, crear_item_tabla(abonado.nombre_completo))
            self._tabla.setItem(fila, 2, crear_item_tabla(abonado.telefono or "-"))
            self._tabla.setItem(fila, 3, crear_item_tabla(abonado.barrio_nombre))
            self._tabla.setItem(fila, 4, crear_item_tabla(abonado.total_casas))
            self._tabla.setItem(fila, 5, crear_item_tabla(abonado.meses_en_mora))
            self._tabla.setCellWidget(fila, 6, self._crear_badge_estado(abonado.estado))
            self._tabla.setCellWidget(fila, 7, self._crear_acciones_fila(abonado))

        self._tabla.resizeRowsToContents()
        self._tabla.setColumnWidth(7, max(self._tabla.columnWidth(7), self.ANCHO_COLUMNA_ACCIONES))
        self._actualizar_estado_vacio(pagina.total_registros == 0)
        self._label_paginacion.setText(
            f"Mostrando {pagina.indice_inicio}-{pagina.indice_fin} de {pagina.total_registros} registros"
        )
        self._label_numero_pagina.setText(
            f"Pagina {self._pagina_actual} de {self._total_paginas}"
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

    def solicitar_datos_abonado(
        self,
        barrios: Iterable[OpcionBarrio],
        abonado: Abonado | None = None,
    ) -> FormularioAbonado | None:
        dialogo = DialogoFormularioAbonado(barrios=barrios, abonado=abonado, parent=self)
        if dialogo.exec() != QDialog.DialogCode.Accepted:
            return None
        return dialogo.obtener_formulario()

    def mostrar_detalle_abonado(
        self,
        abonado: Abonado,
        fecha_creacion: str,
        fecha_actualizada: str,
        deuda_formateada: str,
    ) -> str:
        dialogo = DialogoDetalleAbonado(
            abonado=abonado,
            fecha_creacion=fecha_creacion,
            fecha_actualizada=fecha_actualizada,
            deuda_formateada=deuda_formateada,
            parent=self,
        )
        dialogo.exec()
        return dialogo.accion_resultado

    def confirmar_cambio_estado_abonado(self, abonado: Abonado) -> bool:
        dialogo = DialogoConfirmacionEstadoAbonado(abonado=abonado, parent=self)
        return dialogo.exec() == QDialog.DialogCode.Accepted

    def aplicar_busqueda_externa(self, texto: str) -> None:
        texto_normalizado = texto.strip()
        if self._campo_busqueda.text() != texto_normalizado:
            self._campo_busqueda.setText(texto_normalizado)
            return
        self.filtro_texto_cambiado.emit(texto_normalizado)

    def solicitar_ruta_exportacion(self) -> str:
        ruta, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar abonados",
            "abonados.csv",
            "Archivos CSV (*.csv)",
        )
        return ruta

    def _construir_ui(self) -> None:
        self.setObjectName("vistaAbonados")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 6)
        layout.setSpacing(12)

        encabezado = QHBoxLayout()
        encabezado.setSpacing(10)

        fila_acciones = QHBoxLayout()
        fila_acciones.setSpacing(8)
        fila_acciones.addStretch(1)
        boton_exportar = crear_boton_operativo("Exportar")
        boton_nuevo = crear_boton_operativo("Nuevo abonado", principal=True)
        boton_exportar.clicked.connect(self.exportar_solicitado.emit)
        boton_nuevo.clicked.connect(self.nuevo_abonado_solicitado.emit)
        fila_acciones.addWidget(boton_exportar)
        fila_acciones.addWidget(boton_nuevo)

        encabezado.addStretch(1)
        encabezado.addLayout(fila_acciones)

        self._mensaje = QLabel("")
        self._mensaje.setObjectName("mensajeAbonados")
        self._mensaje.setVisible(False)
        self._mensaje.setWordWrap(True)

        fila_tarjetas = QGridLayout()
        fila_tarjetas.setHorizontalSpacing(10)
        fila_tarjetas.setVerticalSpacing(10)
        self._tarjeta_total = TarjetaResumenAbonado("user.svg", "#8ec9ff")
        self._tarjeta_activos = TarjetaResumenAbonado("circle-check.svg", "#8de8c7")
        self._tarjeta_con_deuda = TarjetaResumenAbonado("alert-triangle.svg", "#f7cc7a")
        self._tarjeta_morosos = TarjetaResumenAbonado("clock.svg", "#c6b6ff")
        fila_tarjetas.addWidget(self._tarjeta_total, 0, 0)
        fila_tarjetas.addWidget(self._tarjeta_activos, 0, 1)
        fila_tarjetas.addWidget(self._tarjeta_con_deuda, 0, 2)
        fila_tarjetas.addWidget(self._tarjeta_morosos, 0, 3)

        panel_filtros = QFrame()
        panel_filtros.setObjectName("panelOperativoAbonados")
        layout_filtros = QVBoxLayout(panel_filtros)
        layout_filtros.setContentsMargins(14, 14, 14, 14)
        layout_filtros.setSpacing(10)

        self._campo_busqueda = QLineEdit()
        self._campo_busqueda.setPlaceholderText("Buscar por DNI o nombre del abonado")
        self._campo_busqueda.textChanged.connect(self.filtro_texto_cambiado.emit)

        fila_chips = QHBoxLayout()
        fila_chips.setSpacing(6)
        self._grupo_filtros = QButtonGroup(self)
        self._grupo_filtros.setExclusive(True)
        self._botones_filtros: dict[str, QPushButton] = {}
        for codigo, texto in (
            (FILTRO_ABONADOS_TODOS, "Todos"),
            (FILTRO_ABONADOS_CON_MORA, "Con mora"),
            (FILTRO_ABONADOS_SIN_MORA, "Sin mora"),
            (FILTRO_ABONADOS_CON_PLAN, "Con plan"),
        ):
            boton = QPushButton(texto)
            boton.setObjectName("chipFiltroAbonado")
            boton.setCheckable(True)
            boton.setCursor(Qt.CursorShape.PointingHandCursor)
            boton.clicked.connect(
                lambda checked=False, valor=codigo: self.filtro_rapido_cambiado.emit(valor)
            )
            self._grupo_filtros.addButton(boton)
            self._botones_filtros[codigo] = boton
            fila_chips.addWidget(boton)
        self._botones_filtros[FILTRO_ABONADOS_TODOS].setChecked(True)
        fila_chips.addStretch(1)

        layout_filtros.addWidget(self._campo_busqueda)
        layout_filtros.addLayout(fila_chips)

        panel_tabla = QFrame()
        panel_tabla.setObjectName("panelTablaAbonados")
        layout_tabla = QVBoxLayout(panel_tabla)
        layout_tabla.setContentsMargins(14, 14, 14, 14)
        layout_tabla.setSpacing(10)

        self._tabla = QTableWidget(0, 8)
        self._tabla.setObjectName("tablaAbonados")
        configurar_tabla_operativa(
            self._tabla,
            [
                "DNI",
                "Abonado",
                "Telefono",
                "Barrio",
                "Casas",
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
        self._tabla.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self._tabla.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self._tabla.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        self._tabla.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.Interactive)
        self._tabla.setColumnWidth(7, self.ANCHO_COLUMNA_ACCIONES)
        self._tabla.verticalHeader().setDefaultSectionSize(58)
        self._tabla.setFrameShape(QFrame.Shape.NoFrame)
        self._tabla.setViewportMargins(0, 0, 0, self.RADIO_PANEL_TABLA)
        self._tabla.viewport().setObjectName("viewportTablaAbonados")
        self._tabla.viewport().setAutoFillBackground(False)

        self._estado_vacio = QLabel("No hay abonados que coincidan con los filtros actuales.")
        self._estado_vacio.setObjectName("estadoVacioAbonados")
        self._estado_vacio.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._estado_vacio.setVisible(False)

        pie_tabla = QHBoxLayout()
        pie_tabla.setSpacing(8)
        self._label_paginacion = QLabel("Mostrando 0-0 de 0 registros")
        self._label_paginacion.setObjectName("textoPieAbonados")
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
        self._label_numero_pagina.setObjectName("textoPieAbonados")
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
        badge.setObjectName("badgeEstadoAbonado")
        badge.setProperty("activo", estado == "ACTIVO")
        badge.style().unpolish(badge)
        badge.style().polish(badge)
        layout.addWidget(badge, alignment=Qt.AlignmentFlag.AlignCenter)
        return contenedor

    def _crear_acciones_fila(self, abonado: Abonado) -> QWidget:
        contenedor = QWidget()
        contenedor.setObjectName("contenedorAccionesAbonado")
        contenedor.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        contenedor.setMinimumWidth(self.ANCHO_COLUMNA_ACCIONES)
        contenedor.setMinimumHeight(58)
        layout = QHBoxLayout(contenedor)
        layout.setContentsMargins(0, 0, 0, 14)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        boton_accion_detalle = BotonIconoFilaAbonado("eye.svg", "#4fa3ff", "Ver detalle")
        boton_ver_casas = BotonIconoFilaAbonado("home.svg", "#8de8c7", "Ver casas")
        boton_accion_editar = BotonIconoFilaAbonado("key.svg", "#4fa3ff", "Editar")
        accion_desactiva = abonado.estado == "ACTIVO"
        boton_accion_estado = BotonIconoFilaAbonado(
            "lock.svg" if accion_desactiva else "circle-check.svg",
            "#ff625c" if accion_desactiva else "#4fa3ff",
            "Desactivar" if accion_desactiva else "Activar",
        )

        boton_accion_detalle.clicked.connect(
            lambda checked=False, identificador=abonado.identificador: self.detalle_abonado_solicitado.emit(
                int(identificador or 0)
            )
        )
        boton_ver_casas.clicked.connect(
            lambda checked=False, identificador=abonado.identificador: self.ver_casas_abonado_solicitado.emit(
                int(identificador or 0)
            )
        )
        boton_accion_editar.clicked.connect(
            lambda checked=False, identificador=abonado.identificador: self.editar_abonado_solicitado.emit(
                int(identificador or 0)
            )
        )
        boton_accion_estado.clicked.connect(
            lambda checked=False, identificador=abonado.identificador: self.cambio_estado_solicitado.emit(
                int(identificador or 0)
            )
        )

        layout.addWidget(boton_accion_detalle)
        layout.addWidget(boton_ver_casas)
        layout.addWidget(boton_accion_editar)
        layout.addWidget(boton_accion_estado)
        return contenedor

    def _actualizar_estado_vacio(self, sin_datos: bool) -> None:
        self._estado_vacio.setVisible(sin_datos)
        self._tabla.setVisible(not sin_datos)

    def _aplicar_estilos(self) -> None:
        radio_panel_tabla = self.RADIO_PANEL_TABLA
        fondo_header_destacado = obtener_fondo_header_destacado(self._tema_actual)
        self.setStyleSheet(
            """
            QWidget#vistaAbonados {
                background: transparent;
            }
            QLabel#tituloModulo {
                color: #ffffff;
                font-size: 19px;
                font-weight: 900;
            }
            QLabel#descripcionModulo,
            QLabel#textoPieAbonados,
            QLabel#detalleTarjetaResumen {
                color: rgba(235, 242, 248, 0.76);
                font-size: 11px;
                font-weight: 600;
            }
            QLabel#mensajeAbonados {
                color: #d9fff5;
                font-size: 12px;
                font-weight: 700;
                padding: 8px 10px;
                border-radius: 12px;
                background-color: rgba(16, 120, 98, 0.16);
                border: 1px solid rgba(158, 231, 214, 0.26);
            }
            QLabel#mensajeAbonados[error="true"] {
                color: #ffd4cf;
                background-color: rgba(180, 35, 24, 0.15);
                border: 1px solid rgba(255, 205, 199, 0.28);
            }
            QFrame#panelOperativoAbonados,
            QFrame#tarjetaResumenAbonados {
                background: """
            + fondo_header_destacado
            + """;
                border: 1px solid rgba(255, 255, 255, 0.16);
                border-radius: 18px;
            }
            QFrame#panelTablaAbonados {
                background: """
            + fondo_header_destacado
            + """;
                border: 1px solid rgba(255, 255, 255, 0.16);
                border-radius: """
            + str(radio_panel_tabla)
            + """px;
            }
            QTableWidget#tablaAbonados {
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
            QWidget#viewportTablaAbonados {
                background: transparent;
                border: none;
                border-bottom-left-radius: """
            + str(radio_panel_tabla)
            + """px;
                border-bottom-right-radius: """
            + str(radio_panel_tabla)
            + """px;
            }
            QTableWidget#tablaAbonados QHeaderView::section:first {
                border-top-left-radius: """
            + str(radio_panel_tabla)
            + """px;
            }
            QTableWidget#tablaAbonados QHeaderView::section {
                background: """
            + self._paleta_tema["fondo_tabla_header_destacado"]
            + """;
                color: #f7fbff;
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
            QTableWidget#tablaAbonados QHeaderView::section:last {
                border-top-right-radius: """
            + str(radio_panel_tabla)
            + """px;
            }
            QTableWidget#tablaAbonados::item {
                padding: 9px 12px;
                border-bottom: 1px solid """
            + self._paleta_tema["borde_tabla"]
            + """;
                background: """
            + self._paleta_tema["fondo_tabla_fila"]
            + """;
            }
            QTableWidget#tablaAbonados::item:alternate {
                background: """
            + self._paleta_tema["fondo_tabla_fila_alterna"]
            + """;
            }
            QTableWidget#tablaAbonados::item:selected {
                background: """
            + self._paleta_tema["fondo_tabla_seleccion"]
            + """;
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
            QPushButton#chipFiltroAbonado {
                min-height: 30px;
                border-radius: 11px;
                padding: 0 12px;
                background: rgba(255, 255, 255, 0.06);
                border: 1px solid rgba(255, 255, 255, 0.14);
                color: #ecf5ff;
                font-size: 11px;
                font-weight: 700;
            }
            QPushButton#chipFiltroAbonado:hover {
                background: rgba(255, 255, 255, 0.12);
            }
            QPushButton#chipFiltroAbonado:checked {
                color: #0f2d43;
                background: #d2f4f2;
                border-color: rgba(255, 255, 255, 0.18);
            }
            QLabel#badgeEstadoAbonado {
                border-radius: 11px;
                padding: 6px 10px;
                font-size: 11px;
                font-weight: 800;
                color: #f4f8fb;
                background: rgba(132, 146, 166, 0.22);
                border: 1px solid rgba(255, 255, 255, 0.12);
            }
            QLabel#badgeEstadoAbonado[activo="true"] {
                color: #d9fff5;
                background: rgba(16, 120, 98, 0.22);
                border-color: rgba(158, 231, 214, 0.26);
            }
            QWidget#contenedorAccionesAbonado {
                background: transparent;
            }
            QToolButton#botonIconoFilaAbonado {
                background: transparent;
                border: none;
                border-radius: 8px;
                padding: 0px;
                margin: 0px;
            }
            QToolButton#botonIconoFilaAbonado:hover {
                background: transparent;
                border: none;
            }
            QLabel#estadoVacioAbonados {
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
                QLabel#nombreAbonadoDetalle {{
                    color: {paleta["texto_principal"]};
                }}
                QLabel#descripcionModulo,
                QLabel#detalleTarjetaResumen,
                QLabel#textoPieAbonados,
                QLabel#etiquetaDetalleAbonado {{
                    color: {paleta["texto_secundario"]};
                }}
                QLabel#mensajeAbonados[error="false"] {{
                    color: {paleta["texto_exito"]};
                    background-color: {paleta["fondo_exito"]};
                    border: 1px solid {paleta["borde_exito"]};
                }}
                QLabel#mensajeAbonados[error="true"] {{
                    color: {paleta["texto_error"]};
                    background-color: {paleta["fondo_error"]};
                    border: 1px solid {paleta["borde_error"]};
                }}
                QFrame#panelOperativoAbonados,
                QFrame#panelTablaAbonados,
                QFrame#tarjetaResumenAbonados {{
                    background: {paleta["fondo_superficie"]};
                    border: 1px solid {paleta["borde_principal"]};
                }}
                QTableWidget#tablaAbonados {{
                    background: {paleta["fondo_superficie_muy_suave"]};
                    /*
                    Tema claro pendiente:
                    background: {paleta["fondo_tabla_cuerpo"]};
                    alternate-background-color: {paleta["fondo_tabla_fila_alterna"]};
                    */
                }}
                QTableWidget#tablaAbonados QHeaderView::section {{
                    background: {paleta["fondo_tabla_header"]};
                    /* Tema claro pendiente: background: {paleta["fondo_tabla_header_destacado"]}; */
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
                QPushButton#chipFiltroAbonado {{
                    background: {paleta["fondo_chip"]};
                    border: 1px solid {paleta["borde_suave"]};
                    color: {paleta["texto_chip"]};
                }}
                QPushButton#chipFiltroAbonado:hover {{
                    background: {paleta["fondo_chip_hover"]};
                }}
                QPushButton#chipFiltroAbonado:checked {{
                    color: {paleta["texto_chip_activo"]};
                    background: {paleta["fondo_chip_activo"]};
                    border-color: {paleta["borde_chip_activo"]};
                }}
                QLabel#badgeEstadoAbonado {{
                    color: {paleta["texto_badge"]};
                    background: {paleta["fondo_badge"]};
                    border: 1px solid {paleta["borde_suave"]};
                }}
                QLabel#badgeEstadoAbonado[activo="true"] {{
                    color: {paleta["texto_badge_activo"]};
                    background: {paleta["fondo_badge_activo"]};
                    border-color: {paleta["borde_badge_activo"]};
                }}
                QLabel#estadoVacioAbonados {{
                    color: {paleta["texto_secundario"]};
                }}
                QLabel#tituloTarjetaResumen,
                QLabel#codigoAbonadoDetalle {{
                    color: {paleta["texto_panel_secundario"]};
                }}
                """
            )
