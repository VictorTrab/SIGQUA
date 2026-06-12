"""Vista PySide6 del modulo de abonados."""

from __future__ import annotations

from typing import Iterable

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
    CampoDetalleSigqua,
    EncabezadoDetalleSigqua,
    DialogoBaseSigqua,
    DialogoConfirmacionSigqua,
    SeccionDetalleSigqua,
    ContenedorTarjetasResumenOperativo,
    TarjetaResumenOperativa,
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
from comun.pagos_adelantados import EstadoFinancieroCasaAbonado
from comun.ui.temas import (
    TEMA_SIGQUA_PREDETERMINADO,
    obtener_fondo_header_destacado,
    obtener_paleta_tema,
    resolver_nombre_tema,
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


class TarjetaResumenAbonado(TarjetaResumenOperativa):
    """Adaptador del resumen comun para mantener nombres del modulo."""


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


class DialogoFormularioAbonado(DialogoBaseSigqua):
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
        self.setMinimumWidth(580)
        self.setMinimumHeight(460)
        self._construir_ui()

    def obtener_formulario(self) -> FormularioAbonado:
        barrio_id = self._campo_barrio.identificador_seleccionado()
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
        if self._campo_barrio.identificador_seleccionado() is None:
            self._mensaje.setText("Selecciona un barrio valido.")
            self._mensaje.setVisible(True)
            return
        self._mensaje.setVisible(False)
        super().accept()

    def _construir_ui(self) -> None:
        titulo = QLabel("Editar abonado" if self._abonado else "Nuevo abonado")
        titulo.setObjectName("tituloDialogoSigqua")
        descripcion = QLabel(
            "Completa la informacion principal del abonado y su relacion operativa con el barrio."
        )
        descripcion.setObjectName("descripcionDialogoSigqua")
        descripcion.setWordWrap(True)

        formulario = QGridLayout()
        formulario.setContentsMargins(0, 0, 0, 0)
        formulario.setHorizontalSpacing(8)
        formulario.setVerticalSpacing(8)

        self._campo_dni = QLineEdit()
        self._campo_dni.setPlaceholderText("DNI del abonado")
        self._campo_nombre = QLineEdit()
        self._campo_nombre.setPlaceholderText("Nombre completo")
        self._campo_telefono = QLineEdit()
        self._campo_telefono.setPlaceholderText("Telefono")
        self._campo_barrio = CampoBusquedaSeleccionSigqua(
            texto_sin_resultados="No se encontraron barrios",
            placeholder="Escribe para buscar un barrio",
        )
        self._campo_barrio.establecer_opciones(
            [(barrio.identificador, barrio.nombre) for barrio in self._barrios]
        )
        self._combo_estado = QComboBox()
        self._combo_estado.addItems(["ACTIVO", "INACTIVO"])
        self._campo_direccion = QPlainTextEdit()
        self._campo_direccion.setPlaceholderText("Direccion o referencia")
        self._campo_direccion.setFixedHeight(60)
        self._campo_observaciones = QPlainTextEdit()
        self._campo_observaciones.setPlaceholderText("Observaciones")
        self._campo_observaciones.setFixedHeight(60)

        if self._abonado is not None:
            self._campo_dni.setText(self._abonado.dni)
            self._campo_nombre.setText(self._abonado.nombre_completo)
            self._campo_telefono.setText(self._abonado.telefono)
            self._campo_barrio.seleccionar_por_id(
                self._abonado.barrio_id,
                self._abonado.barrio_nombre,
            )
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
        formulario.addWidget(self._crear_bloque_formulario("Barrio", self._campo_barrio), 2, 0)
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
        notas_layout.setSpacing(8)
        notas_layout.addWidget(
            self._crear_bloque_formulario("Direccion", self._campo_direccion)
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
        layout_scroll.addWidget(panel_notas)
        layout_scroll.addWidget(self._mensaje)
        layout_scroll.addStretch(1)

        self.layout_cabecera.addWidget(titulo)
        self.layout_cabecera.addWidget(descripcion)
        self.layout_cuerpo.addWidget(
            self.crear_area_scroll_cuerpo(contenido_scroll, "scrollFormularioAbonado")
        )
        self.layout_pie.addLayout(fila_acciones)

    def _crear_bloque_formulario(self, etiqueta: str, campo: QWidget) -> QWidget:
        bloque = QWidget()
        layout = QVBoxLayout(bloque)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)

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
        layout_panel.setSpacing(8)
        label_titulo = QLabel(titulo)
        label_titulo.setObjectName("etiquetaDatoDialogoSigqua")
        label_descripcion = QLabel(descripcion)
        label_descripcion.setObjectName("descripcionDialogoSigqua")
        label_descripcion.setWordWrap(True)
        layout_panel.addWidget(label_titulo)
        layout_panel.addWidget(label_descripcion)
        return panel


class DialogoDetalleAbonado(DialogoBaseSigqua):
    """Modal para consultar detalle del abonado."""

    def __init__(
        self,
        abonado: Abonado,
        fecha_creacion: str,
        fecha_actualizada: str,
        deuda_formateada: str,
        estados_casas: tuple[EstadoFinancieroCasaAbonado, ...] = (),
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._abonado = abonado
        self._fecha_creacion = fecha_creacion
        self._fecha_actualizada = fecha_actualizada
        self._deuda_formateada = deuda_formateada
        self._estados_casas = estados_casas
        self._accion_resultado = "cerrar"
        self.setMinimumWidth(820)
        self.setMinimumHeight(620)
        self._construir_ui()

    @property
    def accion_resultado(self) -> str:
        return self._accion_resultado

    def _construir_ui(self) -> None:
        titulo = QLabel("Detalle de abonado")
        titulo.setObjectName("tituloDialogoSigqua")
        descripcion = QLabel(
            "Consulta informacion principal, ubicacion operativa y estado financiero resumido."
        )
        descripcion.setObjectName("descripcionDialogoSigqua")
        descripcion.setWordWrap(True)

        contenedor_scroll = QWidget()
        contenedor_scroll.setObjectName("contenedorScrollDetalleAbonado")
        layout_scroll = QVBoxLayout(contenedor_scroll)
        layout_scroll.setContentsMargins(0, 0, 0, 0)
        layout_scroll.setSpacing(12)

        panel_detalle = QFrame()
        panel_detalle.setObjectName("panelDetalleSigqua")
        panel_detalle_layout = QVBoxLayout(panel_detalle)
        panel_detalle_layout.setContentsMargins(18, 18, 18, 18)
        panel_detalle_layout.setSpacing(14)

        encabezado = EncabezadoDetalleSigqua(
            self._abonado.dni,
            self._abonado.nombre_completo,
            boton_copiar=crear_boton_copiar_detalle_sigqua(
                self._abonado.dni,
                etiqueta="DNI",
            ),
            badges=(
                crear_badge_estado_detalle_sigqua(
                    self._abonado.estado.title(),
                    "activo" if self._abonado.estado == "ACTIVO" else "info",
                ),
            ),
        )

        grid_info = QGridLayout()
        grid_info.setHorizontalSpacing(14)
        grid_info.setVerticalSpacing(14)
        grid_info.addWidget(
            CampoDetalleSigqua("Telefono", self._abonado.telefono or "Sin telefono"),
            0,
            0,
        )
        grid_info.addWidget(
            CampoDetalleSigqua("Barrio", self._abonado.barrio_nombre or "Sin barrio"),
            0,
            1,
        )
        grid_info.addWidget(
            CampoDetalleSigqua(
                "Plan activo",
                "Si" if self._abonado.tiene_plan_activo else "No",
            ),
            1,
            0,
        )
        grid_info.addWidget(CampoDetalleSigqua("Creado", self._fecha_creacion), 1, 1)
        grid_info.addWidget(
            CampoDetalleSigqua("Ultima actualizacion", self._fecha_actualizada),
            2,
            0,
            1,
            2,
        )

        fila_metricas = QHBoxLayout()
        fila_metricas.setSpacing(12)
        fila_metricas.addWidget(
            TarjetaResumenDetalleSigqua("Casas", str(self._abonado.total_casas)),
            1,
        )
        fila_metricas.addWidget(
            TarjetaResumenDetalleSigqua(
                "Meses en mora",
                str(self._abonado.meses_en_mora),
            ),
            1,
        )
        fila_metricas.addWidget(
            TarjetaResumenDetalleSigqua("Deuda", self._deuda_formateada),
            1,
        )

        direccion = CampoDetalleSigqua(
            "Direccion",
            self._abonado.direccion_referencia or "Sin referencia registrada.",
        )
        observaciones = CampoDetalleSigqua(
            "Observaciones",
            self._abonado.observaciones or "Sin observaciones registradas.",
        )

        tabla_casas = QTableWidget()
        configurar_tabla_operativa(tabla_casas, ["Casa", "Estado financiero"])
        tabla_casas.setObjectName("tablaCasasDetalleAbonado")
        tabla_casas.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        tabla_casas.setRowCount(len(self._estados_casas))
        tabla_casas.setMinimumHeight(max(120, min(250, 48 + (len(self._estados_casas) * 34))))
        tabla_casas.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        for fila, estado_casa in enumerate(self._estados_casas):
            if estado_casa.meses_pendientes > 0:
                estado_texto = f"Debe {estado_casa.meses_pendientes} mes(es)"
            elif estado_casa.resumen_adelanto.ultimo_periodo_cubierto:
                estado_texto = (
                    "Adelantado hasta "
                    f"{estado_casa.resumen_adelanto.ultimo_periodo_cubierto}"
                )
            else:
                estado_texto = "Al dia"
            tabla_casas.setItem(fila, 0, crear_item_tabla(estado_casa.casa_codigo))
            tabla_casas.setItem(fila, 1, crear_item_tabla(estado_texto))

        fila_acciones = QHBoxLayout()
        fila_acciones.setSpacing(10)
        variante_cerrar = resolver_variante_boton_modal("Cerrar", "neutro")
        boton_cerrar = BotonAccionContextual(
            "Cerrar",
            icono="x.svg",
            variante=variante_cerrar,
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
        boton_ver_casas = BotonAccionContextual(
            "Ver casas",
            icono="home.svg",
            variante="informacion",
            centrado=True,
            mostrar_icono=True,
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

        panel_detalle_layout.addWidget(encabezado)
        panel_detalle_layout.addWidget(
            SeccionDetalleSigqua(
                "Contexto operativo",
                "Consulta contacto, barrio y fechas operativas principales del abonado.",
                grid_info,
            )
        )
        panel_detalle_layout.addWidget(
            SeccionDetalleSigqua(
                "Resumen financiero",
                "Visualiza rapidamente casas asociadas, mora y deuda pendiente.",
                fila_metricas,
            )
        )
        panel_detalle_layout.addWidget(
            SeccionDetalleSigqua(
                "Casas asociadas",
                "La deuda pendiente tiene prioridad sobre la cobertura adelantada.",
                tabla_casas,
            )
        )
        panel_detalle_layout.addWidget(
            SeccionDetalleSigqua(
                "Ubicacion y notas",
                "Incluye la referencia operativa y observaciones administrativas del abonado.",
                [direccion, observaciones],
            )
        )
        layout_scroll.addWidget(panel_detalle)

        self.layout_cabecera.addWidget(titulo)
        self.layout_cabecera.addWidget(descripcion)
        self.layout_cuerpo.addWidget(
            self.crear_area_scroll_cuerpo(contenedor_scroll, "scrollDetalleAbonado")
        )
        self.layout_pie.addLayout(fila_acciones)
        self._aplicar_estilos()

    def _solicitar_edicion(self) -> None:
        self._accion_resultado = "editar"
        self.accept()

    def _abrir_casas(self) -> None:
        self._accion_resultado = "ver_casas"
        self.accept()

    def _aplicar_estilos(self) -> None:
        self.setStyleSheet(
            self.styleSheet()
            + f"""
            QScrollArea#scrollDetalleAbonado,
            QWidget#contenedorScrollDetalleAbonado {{
                background: transparent;
                border: none;
            }}
            """
            + obtener_estilo_detalle_sigqua(self._nombre_tema)
        )


class DialogoConfirmacionEstadoAbonado(DialogoConfirmacionSigqua):
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
        estados_casas: tuple[EstadoFinancieroCasaAbonado, ...] = (),
    ) -> str:
        dialogo = DialogoDetalleAbonado(
            abonado=abonado,
            fecha_creacion=fecha_creacion,
            fecha_actualizada=fecha_actualizada,
            deuda_formateada=deuda_formateada,
            estados_casas=estados_casas,
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

        contenedor_tarjetas = ContenedorTarjetasResumenOperativo()
        self._tarjeta_total = TarjetaResumenAbonado("user.svg", "#75C7F0")
        self._tarjeta_activos = TarjetaResumenAbonado("circle-check.svg", "#8de8c7")
        self._tarjeta_con_deuda = TarjetaResumenAbonado("alert-triangle.svg", "#f7cc7a")
        self._tarjeta_morosos = TarjetaResumenAbonado("clock.svg", "#F5B84B")
        contenedor_tarjetas.establecer_tarjetas(
            (self._tarjeta_total, self._tarjeta_activos, self._tarjeta_con_deuda, self._tarjeta_morosos)
        )

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
        layout.addWidget(contenedor_tarjetas)
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
                color: #75C7F0;
                font-size: 19px;
                font-weight: 900;
            }
            QLabel#descripcionModulo,
            QLabel#textoPieAbonados,
            QLabel#detalleTarjetaResumen {
                color: #C5DDEE;
                font-size: 11px;
                font-weight: 600;
            }
            QLabel#mensajeAbonados {
                color: #DDFBF0;
                font-size: 12px;
                font-weight: 700;
                padding: 8px 10px;
                border-radius: 12px;
                background-color: rgba(55, 211, 153, 0.16);
                border: 1px solid rgba(55, 211, 153, 0.26);
            }
            QLabel#mensajeAbonados[error="true"] {
                color: #FFE3E3;
                background-color: rgba(242, 116, 116, 0.15);
                border: 1px solid rgba(242, 116, 116, 0.28);
            }
            QFrame#panelOperativoAbonados,
            QFrame#tarjetaResumenAbonados {
                background: """
            + fondo_header_destacado
            + """;
                border: 1px solid rgba(126, 167, 196, 0.48);
                border-radius: 18px;
            }
            QFrame#panelTablaAbonados {
                background: """
            + fondo_header_destacado
            + """;
                border: 1px solid rgba(126, 167, 196, 0.48);
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
                border: 1px solid """
            + self._paleta_tema["borde_medio"]
            + """;
                border-radius: 12px;
                background: """
            + self._paleta_tema["fondo_input"]
            + """;
                color: """
            + self._paleta_tema["texto_input"]
            + """;
                padding: 0 10px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: """
            + self._paleta_tema["borde_foco_input"]
            + """;
                background: """
            + self._paleta_tema["fondo_input_focus"]
            + """;
            }
            QPushButton#chipFiltroAbonado {
                min-height: 30px;
                border-radius: 11px;
                padding: 0 12px;
                background: """
            + self._paleta_tema["fondo_chip"]
            + """;
                border: 1px solid """
            + self._paleta_tema["borde_suave"]
            + """;
                color: """
            + self._paleta_tema["texto_chip"]
            + """;
                font-size: 11px;
                font-weight: 700;
            }
            QPushButton#chipFiltroAbonado:hover {
                background: """
            + self._paleta_tema["fondo_chip_hover"]
            + """;
            }
            QPushButton#chipFiltroAbonado:checked {
                color: """
            + self._paleta_tema["texto_chip_activo"]
            + """;
                background: """
            + self._paleta_tema["fondo_chip_activo"]
            + """;
                border-color: """
            + self._paleta_tema["borde_chip_activo"]
            + """;
            }
            QLabel#badgeEstadoAbonado {
                border-radius: 11px;
                padding: 6px 10px;
                font-size: 11px;
                font-weight: 800;
                color: #C5DDEE;
                background: rgba(142, 168, 188, 0.22);
                border: 1px solid rgba(126, 167, 196, 0.30);
            }
            QLabel#badgeEstadoAbonado[activo="true"] {
                color: #DDFBF0;
                background: rgba(55, 211, 153, 0.22);
                border-color: rgba(55, 211, 153, 0.26);
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

