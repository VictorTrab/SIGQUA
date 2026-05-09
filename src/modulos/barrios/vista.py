"""Vista PySide6 del modulo de barrios."""

from __future__ import annotations

from typing import Callable

from PySide6.QtCore import QElapsedTimer, QEvent, QSize, Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QButtonGroup,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
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
    DialogoMensajeSicap,
    configurar_tabla_operativa,
    crear_boton_operativo,
    crear_item_tabla,
    obtener_icono_tabler_coloreado,
)
from comun.ui.componentes import COLOR_FONDO_DIALOGO, RADIO_TARJETA_DIALOGO
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
        self._actualizar_icono(self.COLOR_BASE)
        super().leaveEvent(evento)

    def _actualizar_icono(self, color_icono: str) -> None:
        self.setIcon(obtener_icono_tabler_coloreado(self._icono, color_icono, tamano=18))


class DialogoFormularioBarrio(DialogoBaseSicap):
    """Modal para crear o editar barrios."""

    def __init__(self, barrio: Barrio | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._barrio = barrio
        self.setMinimumWidth(460)
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
        titulo.setObjectName("tituloDialogoSicap")
        descripcion = QLabel(
            "Completa el formulario con la informacion principal del barrio."
        )
        descripcion.setObjectName("descripcionDialogoSicap")
        descripcion.setWordWrap(True)

        panel_formulario = QFrame()
        panel_formulario.setObjectName("bloqueDialogoSicap")
        layout_panel_formulario = QVBoxLayout(panel_formulario)
        layout_panel_formulario.setContentsMargins(18, 18, 18, 18)
        layout_panel_formulario.setSpacing(14)

        formulario = QFormLayout()
        formulario.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        formulario.setFormAlignment(Qt.AlignmentFlag.AlignTop)
        formulario.setHorizontalSpacing(12)
        formulario.setVerticalSpacing(12)

        self._campo_nombre = QLineEdit()
        self._campo_nombre.setPlaceholderText("Nombre del barrio")
        self._combo_estado = QComboBox()
        self._combo_estado.addItems(["ACTIVO", "INACTIVO"])
        self._campo_observaciones = QPlainTextEdit()
        self._campo_observaciones.setPlaceholderText("Observaciones")
        self._campo_observaciones.setFixedHeight(112)

        if self._barrio is not None:
            self._campo_nombre.setText(self._barrio.nombre)
            self._combo_estado.setCurrentText(self._barrio.estado)
            self._campo_observaciones.setPlainText(self._barrio.observaciones)

        formulario.addRow("Nombre del barrio", self._campo_nombre)
        formulario.addRow("Estado", self._combo_estado)
        formulario.addRow("Observaciones", self._campo_observaciones)
        layout_panel_formulario.addLayout(formulario)

        self._mensaje = QLabel("")
        self._mensaje.setObjectName("mensajeErrorDialogoSicap")
        self._mensaje.setVisible(False)

        fila_acciones = QHBoxLayout()
        fila_acciones.setSpacing(10)
        boton_cancelar = BotonAccionContextual(
            "Cancelar",
            "arrow-left.svg",
            "neutro",
            centrado=True,
        )
        boton_guardar = BotonAccionContextual(
            "Guardar cambios",
            "circle-check.svg",
            "primario",
            centrado=True,
        )
        boton_cancelar.setMinimumWidth(148)
        boton_guardar.setMinimumWidth(176)
        boton_cancelar.clicked.connect(self.reject)
        boton_guardar.clicked.connect(self.accept)
        fila_acciones.addWidget(boton_cancelar)
        fila_acciones.addStretch(1)
        fila_acciones.addWidget(boton_guardar)

        self.setStyleSheet(
            self.styleSheet()
            + """
            QLabel {
                color: #f5fbff;
                font-size: 13px;
                font-weight: 700;
            }
            """
        )
        self.layout_cabecera.addWidget(titulo)
        self.layout_cabecera.addWidget(descripcion)
        self.layout_cuerpo.addWidget(panel_formulario)
        self.layout_cuerpo.addWidget(self._mensaje)
        self.layout_pie.addLayout(fila_acciones)


class DialogoDetalleBarrio(DialogoBaseSicap):
    """Modal para consultar detalle del barrio."""

    def __init__(
        self,
        barrio: Barrio,
        fecha_actualizada: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._barrio = barrio
        self._fecha_actualizada = fecha_actualizada
        self._accion_resultado = "cerrar"
        self.setMinimumWidth(560)
        self._construir_ui()

    @property
    def accion_resultado(self) -> str:
        return self._accion_resultado

    def _construir_ui(self) -> None:
        titulo = QLabel("Detalle de barrio")
        titulo.setObjectName("tituloDialogoSicap")
        descripcion = QLabel(
            "Consulta informacion general, estado operativo y estadisticas del barrio."
        )
        descripcion.setObjectName("descripcionDialogoSicap")
        descripcion.setWordWrap(True)

        panel_detalle = QFrame()
        panel_detalle.setObjectName("panelContenidoDetalleBarrio")
        panel_detalle_layout = QVBoxLayout(panel_detalle)
        panel_detalle_layout.setContentsMargins(16, 16, 16, 16)
        panel_detalle_layout.setSpacing(14)

        fila_superior = QHBoxLayout()
        fila_superior.setSpacing(12)
        bloque_nombre = QVBoxLayout()
        bloque_nombre.setSpacing(4)
        codigo = QLabel(self._barrio.codigo)
        codigo.setObjectName("codigoBarrioDetalle")
        nombre = QLabel(self._barrio.nombre)
        nombre.setObjectName("nombreBarrioDetalle")
        bloque_nombre.addWidget(codigo)
        bloque_nombre.addWidget(nombre)

        estado = QLabel(self._barrio.estado.title())
        estado.setObjectName("badgeDetalleBarrio")
        estado.setProperty("activo", self._barrio.estado == "ACTIVO")
        estado.style().unpolish(estado)
        estado.style().polish(estado)

        fila_superior.addLayout(bloque_nombre, 1)
        fila_superior.addWidget(estado, alignment=Qt.AlignmentFlag.AlignTop)

        grid_info = QGridLayout()
        grid_info.setHorizontalSpacing(12)
        grid_info.setVerticalSpacing(12)
        grid_info.addWidget(self._crear_campo_detalle("Codigo", self._barrio.codigo), 0, 0)
        grid_info.addWidget(self._crear_campo_detalle("Estado", self._barrio.estado.title()), 0, 1)
        grid_info.addWidget(
            self._crear_campo_detalle("Ultima actualizacion", self._fecha_actualizada),
            1,
            0,
            1,
            2,
        )

        fila_metricas = QHBoxLayout()
        fila_metricas.setSpacing(12)
        fila_metricas.addWidget(
            self._crear_tarjeta_detalle("Abonados", str(self._barrio.total_abonados)),
            1,
        )
        fila_metricas.addWidget(
            self._crear_tarjeta_detalle("Casas", str(self._barrio.total_casas)),
            1,
        )

        observaciones = self._crear_campo_detalle(
            "Observaciones",
            self._barrio.observaciones or "Sin observaciones registradas.",
        )
        observaciones.setObjectName("campoDetalleBarrioAmplio")

        separador_acciones = QFrame()
        separador_acciones.setObjectName("separadorDetalleBarrio")
        separador_acciones.setFixedHeight(1)

        fila_acciones = QHBoxLayout()
        fila_acciones.setSpacing(10)
        boton_cerrar = BotonAccionContextual(
            "Cerrar",
            "arrow-left.svg",
            "neutro",
            centrado=True,
        )
        boton_ver_abonados = BotonAccionContextual(
            "Ver abonados",
            "user.svg",
            "informacion",
            centrado=True,
        )
        boton_ver_casas = BotonAccionContextual(
            "Ver casas",
            "home.svg",
            "informacion",
            centrado=True,
        )
        boton_editar = BotonAccionContextual("Editar", "key.svg", "edicion", centrado=True)
        boton_cerrar.setMinimumWidth(136)
        boton_ver_abonados.setMinimumWidth(156)
        boton_ver_casas.setMinimumWidth(140)
        boton_editar.setMinimumWidth(132)

        boton_cerrar.clicked.connect(self.reject)
        boton_ver_abonados.clicked.connect(self._mostrar_aviso_abonados)
        boton_ver_casas.clicked.connect(self._mostrar_aviso_casas)
        boton_editar.clicked.connect(self._solicitar_edicion)

        fila_acciones.addWidget(boton_cerrar)
        fila_acciones.addStretch(1)
        fila_acciones.addWidget(boton_ver_abonados)
        fila_acciones.addWidget(boton_ver_casas)
        fila_acciones.addWidget(boton_editar)

        panel_detalle_layout.addLayout(fila_superior)
        panel_detalle_layout.addLayout(grid_info)
        panel_detalle_layout.addLayout(fila_metricas)
        panel_detalle_layout.addWidget(observaciones)
        panel_detalle_layout.addWidget(separador_acciones)
        panel_detalle_layout.addLayout(fila_acciones)

        self.layout_cabecera.addWidget(titulo)
        self.layout_cabecera.addWidget(descripcion)
        self.layout_cuerpo.addWidget(panel_detalle)
        self._pie.setVisible(False)
        self._aplicar_estilos()

    def _crear_campo_detalle(self, etiqueta: str, valor: str) -> QFrame:
        tarjeta = QFrame()
        tarjeta.setObjectName("campoDetalleBarrio")
        layout = QVBoxLayout(tarjeta)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(4)

        label_etiqueta = QLabel(etiqueta)
        label_etiqueta.setObjectName("etiquetaDetalleBarrio")
        label_valor = QLabel(valor)
        label_valor.setObjectName("valorDetalleBarrio")
        label_valor.setWordWrap(True)

        layout.addWidget(label_etiqueta)
        layout.addWidget(label_valor)
        return tarjeta

    def _crear_tarjeta_detalle(self, titulo: str, valor: str) -> QFrame:
        tarjeta = QFrame()
        tarjeta.setObjectName("tarjetaMiniDetalleBarrio")
        layout = QVBoxLayout(tarjeta)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(4)

        label_titulo = QLabel(titulo)
        label_titulo.setObjectName("etiquetaDetalleBarrio")
        label_valor = QLabel(valor)
        label_valor.setObjectName("valorTarjetaMiniDetalle")
        layout.addWidget(label_titulo)
        layout.addWidget(label_valor)
        return tarjeta

    def _mostrar_aviso_abonados(self) -> None:
        DialogoMensajeSicap(
            "Ver abonados",
            "La navegacion hacia el modulo de abonados se integrara en el siguiente hito.",
            icono="user.svg",
            variante="informacion",
            parent=self.parentWidget() or self,
        ).exec()

    def _mostrar_aviso_casas(self) -> None:
        DialogoMensajeSicap(
            "Ver casas",
            "La navegacion hacia el modulo de casas se integrara en el siguiente hito.",
            icono="home.svg",
            variante="informacion",
            parent=self.parentWidget() or self,
        ).exec()

    def _solicitar_edicion(self) -> None:
        self._accion_resultado = "editar"
        self.accept()

    def _aplicar_estilos(self) -> None:
        radio = RADIO_TARJETA_DIALOGO
        self.setStyleSheet(
            self.styleSheet()
            + f"""
            QFrame#panelContenidoDetalleBarrio {{
                background: {COLOR_FONDO_DIALOGO};
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: {radio}px;
            }}
            QFrame#campoDetalleBarrio,
            QFrame#campoDetalleBarrioAmplio,
            QFrame#tarjetaMiniDetalleBarrio {{
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.10);
                border-radius: {radio}px;
            }}
            QFrame#separadorDetalleBarrio {{
                background: rgba(255, 255, 255, 0.12);
                border: none;
            }}
            QLabel#codigoBarrioDetalle {{
                color: #8ec9ff;
                font-size: 12px;
                font-weight: 800;
                letter-spacing: 0.08em;
            }}
            QLabel#nombreBarrioDetalle {{
                color: #ffffff;
                font-size: 22px;
                font-weight: 900;
            }}
            QLabel#badgeDetalleBarrio {{
                border-radius: {radio}px;
                padding: 8px 12px;
                font-size: 12px;
                font-weight: 800;
                color: #ffffff;
                background: rgba(160, 174, 192, 0.22);
                border: 1px solid rgba(255, 255, 255, 0.12);
            }}
            QLabel#badgeDetalleBarrio[activo="true"] {{
                color: #d9fff5;
                background: rgba(16, 120, 98, 0.24);
                border-color: rgba(158, 231, 214, 0.26);
            }}
            QLabel#etiquetaDetalleBarrio {{
                color: rgba(232, 239, 249, 0.72);
                font-size: 12px;
                font-weight: 700;
            }}
            QLabel#valorDetalleBarrio {{
                color: #f7fbff;
                font-size: 14px;
                font-weight: 700;
            }}
            QLabel#valorTarjetaMiniDetalle {{
                color: #ffffff;
                font-size: 24px;
                font-weight: 900;
            }}
            """
        )


class DialogoConfirmacionEstadoBarrio(DialogoConfirmacionSicap):
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
                ("Codigo", self._barrio.codigo),
                ("Estado actual", self._barrio.estado.title()),
                ("Accion", nuevo_estado.title()),
            ),
            texto_confirmar="Confirmar",
            icono="alert-triangle.svg",
            variante_confirmar="advertencia",
            parent=parent,
        )


class VistaBarrios(QWidget):
    """Pantalla principal del modulo de barrios."""

    RADIO_PANEL_TABLA = 18
    ANCHO_COLUMNA_ACCIONES = 164
    DURACION_MENSAJE_MS = 5200

    filtro_texto_cambiado = Signal(str)
    filtro_rapido_cambiado = Signal(str)
    pagina_cambiada = Signal(int)
    exportar_solicitado = Signal()
    nuevo_barrio_solicitado = Signal()
    detalle_barrio_solicitado = Signal(int)
    editar_barrio_solicitado = Signal(int)
    cambio_estado_solicitado = Signal(int)

    def __init__(self) -> None:
        super().__init__()
        self._pagina_actual = 1
        self._total_paginas = 1
        self._temporizador_mensaje = QTimer(self)
        self._temporizador_mensaje.setSingleShot(True)
        self._temporizador_mensaje.timeout.connect(self._ocultar_mensaje)
        self._construir_ui()
        self._aplicar_estilos()

    def mostrar_resumen(self, resumen: ResumenBarrios) -> None:
        self._tarjeta_total.actualizar(
            "Total de barrios",
            str(resumen.total_barrios),
            "Cobertura territorial registrada.",
        )
        self._tarjeta_activos.actualizar(
            "Barrios activos",
            str(resumen.barrios_activos),
            "Disponibles para operacion diaria.",
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

    def solicitar_datos_barrio(self, barrio: Barrio | None = None) -> FormularioBarrio | None:
        dialogo = DialogoFormularioBarrio(barrio=barrio, parent=self)
        if dialogo.exec() != QDialog.DialogCode.Accepted:
            return None
        return dialogo.obtener_formulario()

    def mostrar_detalle_barrio(self, barrio: Barrio, fecha_actualizada: str) -> str:
        dialogo = DialogoDetalleBarrio(barrio=barrio, fecha_actualizada=fecha_actualizada, parent=self)
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
        bloque_titulo = QVBoxLayout()
        bloque_titulo.setSpacing(2)
        titulo = QLabel("Barrios")
        titulo.setObjectName("tituloModulo")
        descripcion = QLabel("Gestion de barrios y organizacion territorial")
        descripcion.setObjectName("descripcionModulo")
        descripcion.setWordWrap(True)
        bloque_titulo.addWidget(titulo)
        bloque_titulo.addWidget(descripcion)

        fila_acciones = QHBoxLayout()
        fila_acciones.setSpacing(8)
        fila_acciones.addStretch(1)
        boton_exportar = crear_boton_operativo("Exportar")
        boton_nuevo = crear_boton_operativo("Nuevo barrio", principal=True)
        boton_exportar.clicked.connect(self.exportar_solicitado.emit)
        boton_nuevo.clicked.connect(self.nuevo_barrio_solicitado.emit)
        fila_acciones.addWidget(boton_exportar)
        fila_acciones.addWidget(boton_nuevo)

        encabezado.addLayout(bloque_titulo, 1)
        encabezado.addLayout(fila_acciones)

        self._mensaje = QLabel("")
        self._mensaje.setObjectName("mensajeBarrios")
        self._mensaje.setVisible(False)
        self._mensaje.setWordWrap(True)

        fila_tarjetas = QGridLayout()
        fila_tarjetas.setHorizontalSpacing(10)
        fila_tarjetas.setVerticalSpacing(10)
        self._tarjeta_total = TarjetaResumenBarrio("map-pin.svg", "#8ec9ff")
        self._tarjeta_activos = TarjetaResumenBarrio("circle-check.svg", "#8de8c7")
        self._tarjeta_con_abonados = TarjetaResumenBarrio("user.svg", "#f7cc7a")
        self._tarjeta_destacado = TarjetaResumenBarrio("home.svg", "#c6b6ff")
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
                "Codigo",
                "Barrio",
                "Abonados",
                "Casas",
                "Estado",
                "Ultima actualizacion",
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
        self._label_numero_pagina = QLabel("Pagina 1 de 1")
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
        layout.addWidget(boton_accion_editar)
        layout.addWidget(boton_accion_estado)
        return contenedor

    def _actualizar_estado_vacio(self, sin_datos: bool) -> None:
        self._estado_vacio.setVisible(sin_datos)
        self._tabla.setVisible(not sin_datos)

    def _aplicar_estilos(self) -> None:
        radio_panel_tabla = self.RADIO_PANEL_TABLA
        self.setStyleSheet(
            """
            QWidget#vistaBarrios {
                background: transparent;
            }
            QLabel#tituloModulo {
                color: #ffffff;
                font-size: 19px;
                font-weight: 900;
            }
            QLabel#descripcionModulo,
            QLabel#textoPieBarrios,
            QLabel#detalleTarjetaResumen {
                color: rgba(235, 242, 248, 0.76);
                font-size: 11px;
                font-weight: 600;
            }
            QLabel#mensajeBarrios {
                color: #d9fff5;
                font-size: 12px;
                font-weight: 700;
                padding: 8px 10px;
                border-radius: 12px;
                background-color: rgba(16, 120, 98, 0.16);
                border: 1px solid rgba(158, 231, 214, 0.26);
            }
            QLabel#mensajeBarrios[error="true"] {
                color: #ffd4cf;
                background-color: rgba(180, 35, 24, 0.15);
                border: 1px solid rgba(255, 205, 199, 0.28);
            }
            QFrame#panelOperativoBarrios,
            QFrame#tarjetaResumenBarrios {
                background: rgba(255, 255, 255, 0.10);
                border: 1px solid rgba(255, 255, 255, 0.16);
                border-radius: 18px;
            }
            QFrame#panelTablaBarrios {
                background: rgba(255, 255, 255, 0.10);
                border: 1px solid rgba(255, 255, 255, 0.16);
                border-radius: """
            + str(radio_panel_tabla)
            + """px;
            }
            QTableWidget#tablaBarrios {
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
                background: rgba(255, 255, 255, 0.10);
                color: #f7fbff;
                border: none;
                border-right: 1px solid rgba(255, 255, 255, 0.06);
                border-bottom: 1px solid rgba(255, 255, 255, 0.08);
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
            QPushButton#chipFiltroBarrio {
                min-height: 30px;
                border-radius: 11px;
                padding: 0 12px;
                background: rgba(255, 255, 255, 0.06);
                border: 1px solid rgba(255, 255, 255, 0.14);
                color: #ecf5ff;
                font-size: 11px;
                font-weight: 700;
            }
            QPushButton#chipFiltroBarrio:hover {
                background: rgba(255, 255, 255, 0.12);
            }
            QPushButton#chipFiltroBarrio:checked {
                color: #0f2d43;
                background: #d2f4f2;
                border-color: rgba(255, 255, 255, 0.18);
            }
            QLabel#badgeEstadoBarrio {
                border-radius: 11px;
                padding: 6px 10px;
                font-size: 11px;
                font-weight: 800;
                color: #f4f8fb;
                background: rgba(132, 146, 166, 0.22);
                border: 1px solid rgba(255, 255, 255, 0.12);
            }
            QLabel#badgeEstadoBarrio[activo="true"] {
                color: #d9fff5;
                background: rgba(16, 120, 98, 0.22);
                border-color: rgba(158, 231, 214, 0.26);
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
