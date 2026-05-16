"""Vista PySide6 del modulo de planes de pago."""

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
    DialogoMensajeSicap,
    aplicar_estilo_boton_operativo,
    configurar_tabla_operativa,
    crear_boton_operativo,
    crear_item_tabla,
    obtener_icono_tabler_coloreado,
    resolver_variante_boton_modal,
)
from comun.ui.temas import TEMA_SICAP_PREDETERMINADO, obtener_paleta_tema, obtener_tema_actual
from modulos.planes_pago.entidades import (
    DetallePlanPago,
    FILTRO_PLANES_ACTIVOS,
    FILTRO_PLANES_CON_MORA,
    FILTRO_PLANES_SERVICIO,
    FILTRO_PLANES_TODOS,
    FormularioPlanPago,
    OpcionCasaPlanPago,
    PaginaPlanesPago,
    PlanPago,
    ResumenPlanesPago,
    TIPOS_PLAN_VALIDOS,
)


class TarjetaResumenPlanPago(QFrame):
    def __init__(self, icono: str, color_icono: str) -> None:
        super().__init__()
        self.setObjectName("tarjetaResumenPlanes")
        self.setMinimumHeight(96)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)
        self._icono = QLabel("")
        self._icono.setObjectName("iconoTarjetaResumen")
        self._icono.setFixedSize(38, 38)
        self._icono.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icono.setPixmap(obtener_icono_tabler_coloreado(icono, color_icono, tamano=18).pixmap(18, 18))
        bloque = QVBoxLayout()
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
        layout.addWidget(self._icono, alignment=Qt.AlignmentFlag.AlignTop)
        layout.addLayout(bloque, 1)

    def actualizar(self, titulo: str, valor: str, detalle: str) -> None:
        self._titulo.setText(titulo)
        self._valor.setText(valor)
        self._detalle.setText(detalle)


class BotonIconoFilaPlan(QToolButton):
    COLOR_BASE = "#c8d6f1"
    INTERVALO_TOOLTIP_MS = 1600

    def __init__(self, icono: str, color_hover: str, tooltip: str) -> None:
        super().__init__()
        self._icono = icono
        self._color_hover = color_hover
        self._color_base = self.COLOR_BASE
        self._temporizador_tooltip = QElapsedTimer()
        self.setObjectName("botonIconoFilaPlan")
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
        self._actualizar_icono(self._color_base)
        super().leaveEvent(evento)

    def aplicar_tema(self, nombre_tema: str) -> None:
        paleta = obtener_paleta_tema(nombre_tema)
        self._color_base = str(paleta["icono_fila_base"])
        self._actualizar_icono(self._color_base)

    def _actualizar_icono(self, color: str) -> None:
        self.setIcon(obtener_icono_tabler_coloreado(self._icono, color, tamano=18))


class DialogoFormularioPlanPago(DialogoBaseSicap):
    def __init__(
        self,
        casas: Iterable[OpcionCasaPlanPago],
        plan: PlanPago | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._casas = list(casas)
        self._plan = plan
        self.setMinimumWidth(680)
        self.setMinimumHeight(620)
        self._construir_ui()

    def obtener_formulario(self) -> FormularioPlanPago:
        return FormularioPlanPago(
            identificador=None if self._plan is None else self._plan.identificador,
            casa_id=self._combo_casa.currentData(),
            tipo_plan=self._combo_tipo_plan.currentText(),
            concepto_financiado=self._combo_concepto.currentText(),
            prima_centavos=self._leer_entero(self._campo_prima.text()),
            saldo_financiado_centavos=self._leer_entero(self._campo_saldo.text()),
            cuota_regular_centavos=self._leer_entero(self._campo_cuota.text()),
            cantidad_cuotas=self._leer_entero(self._campo_cantidad.text()),
            estado=self._combo_estado.currentText(),
            observaciones=self._campo_observaciones.toPlainText(),
        )

    def accept(self) -> None:
        formulario = self.obtener_formulario()
        if formulario.casa_id is None:
            self._mensaje.setText("Selecciona una casa para continuar.")
            self._mensaje.setVisible(True)
            return
        if formulario.saldo_financiado_centavos <= 0:
            self._mensaje.setText("Indica el saldo financiado del plan.")
            self._mensaje.setVisible(True)
            return
        if formulario.cuota_regular_centavos <= 0:
            self._mensaje.setText("Indica la cuota regular del plan.")
            self._mensaje.setVisible(True)
            return
        if formulario.cantidad_cuotas <= 0:
            self._mensaje.setText("Indica la cantidad de cuotas.")
            self._mensaje.setVisible(True)
            return
        self._mensaje.setVisible(False)
        super().accept()

    def _construir_ui(self) -> None:
        titulo = QLabel("Editar plan de pago" if self._plan else "Nuevo plan de pago")
        titulo.setObjectName("tituloDialogoSicap")
        descripcion = QLabel(
            "Crea o ajusta planes asociados solo a conexion o reconexion segun la regla cerrada vigente."
        )
        descripcion.setObjectName("descripcionDialogoSicap")
        descripcion.setWordWrap(True)

        self._combo_casa = QComboBox()
        self._combo_casa.addItem("Selecciona una casa", None)
        for casa in self._casas:
            self._combo_casa.addItem(casa.etiqueta, casa.casa_id)
        self._combo_tipo_plan = QComboBox()
        self._combo_tipo_plan.addItems(TIPOS_PLAN_VALIDOS)
        self._combo_concepto = QComboBox()
        self._combo_concepto.addItems(TIPOS_PLAN_VALIDOS)
        self._combo_estado = QComboBox()
        self._combo_estado.addItems(["ACTIVO", "FINALIZADO", "CANCELADO", "ANULADO"])
        self._campo_prima = QLineEdit()
        self._campo_prima.setPlaceholderText("0")
        self._campo_saldo = QLineEdit()
        self._campo_saldo.setPlaceholderText("35000")
        self._campo_cuota = QLineEdit()
        self._campo_cuota.setPlaceholderText("17500")
        self._campo_cantidad = QLineEdit()
        self._campo_cantidad.setPlaceholderText("2")
        self._campo_observaciones = QPlainTextEdit()
        self._campo_observaciones.setFixedHeight(90)

        if self._plan is not None:
            indice_casa = self._combo_casa.findData(self._plan.casa_id)
            if indice_casa >= 0:
                self._combo_casa.setCurrentIndex(indice_casa)
            self._combo_tipo_plan.setCurrentText(self._plan.tipo_plan)
            self._combo_concepto.setCurrentText(self._plan.concepto_financiado)
            self._combo_estado.setCurrentText(self._plan.estado)
            self._campo_prima.setText(str(self._plan.prima_centavos))
            self._campo_saldo.setText(str(self._plan.saldo_financiado_centavos))
            self._campo_cuota.setText(str(self._plan.cuota_regular_centavos))
            self._campo_cantidad.setText(str(self._plan.cantidad_cuotas))
            self._campo_observaciones.setPlainText(self._plan.observaciones)

        grilla = QGridLayout()
        grilla.setHorizontalSpacing(10)
        grilla.setVerticalSpacing(10)
        grilla.addWidget(self._crear_bloque("Casa asociada", self._combo_casa), 0, 0, 1, 2)
        grilla.addWidget(self._crear_bloque("Tipo de plan", self._combo_tipo_plan), 1, 0)
        grilla.addWidget(self._crear_bloque("Concepto financiado", self._combo_concepto), 1, 1)
        grilla.addWidget(self._crear_bloque("Prima (centavos)", self._campo_prima), 2, 0)
        grilla.addWidget(self._crear_bloque("Saldo financiado (centavos)", self._campo_saldo), 2, 1)
        grilla.addWidget(self._crear_bloque("Cuota (centavos)", self._campo_cuota), 3, 0)
        grilla.addWidget(self._crear_bloque("Cantidad de cuotas", self._campo_cantidad), 3, 1)
        grilla.addWidget(self._crear_bloque("Estado", self._combo_estado), 4, 0, 1, 2)

        panel_principal = self._crear_panel(
            "Estructura del plan",
            "Define el acuerdo de servicio y su estructura base. El prototipo cierra primero tipos de plan de conexion o reconexion.",
        )
        panel_principal.layout().addLayout(grilla)

        panel_notas = self._crear_panel(
            "Observaciones",
            "Usa este espacio para dejar el contexto administrativo del acuerdo.",
        )
        panel_notas.layout().addWidget(self._crear_bloque("Notas del plan", self._campo_observaciones))

        self._mensaje = QLabel("")
        self._mensaje.setObjectName("mensajeErrorDialogoSicap")
        self._mensaje.setVisible(False)

        fila_acciones = QHBoxLayout()
        fila_acciones.setSpacing(10)
        boton_cancelar = BotonAccionContextual("Cancelar", variante="neutro", centrado=True, mostrar_icono=False)
        boton_guardar = BotonAccionContextual("Guardar cambios", variante="primario", centrado=True, mostrar_icono=False)
        boton_cancelar.setMinimumWidth(132)
        boton_guardar.setMinimumWidth(160)
        boton_cancelar.clicked.connect(self.reject)
        boton_guardar.clicked.connect(self.accept)
        fila_acciones.addWidget(boton_cancelar)
        fila_acciones.addStretch(1)
        fila_acciones.addWidget(boton_guardar)

        self.layout_cabecera.addWidget(titulo)
        self.layout_cabecera.addWidget(descripcion)
        self.layout_cuerpo.addWidget(panel_principal)
        self.layout_cuerpo.addWidget(panel_notas)
        self.layout_cuerpo.addWidget(self._mensaje)
        self.layout_pie.addLayout(fila_acciones)

    def _crear_bloque(self, etiqueta: str, campo: QWidget) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        label = QLabel(etiqueta)
        label.setObjectName("etiquetaDatoDialogoSicap")
        layout.addWidget(label)
        layout.addWidget(campo)
        return widget

    def _crear_panel(self, titulo: str, descripcion: str) -> QFrame:
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

    @staticmethod
    def _leer_entero(texto: str) -> int:
        try:
            return int((texto or "0").strip())
        except ValueError:
            return -1


class DialogoDetallePlanPago(DialogoBaseSicap):
    def __init__(
        self,
        detalle: DetallePlanPago,
        formateador_moneda: Callable[[int], str],
        formateador_fecha: Callable[[str], str],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._detalle = detalle
        self._formateador_moneda = formateador_moneda
        self._formateador_fecha = formateador_fecha
        self._accion_resultado = "cerrar"
        self.setMinimumWidth(840)
        self.setMinimumHeight(640)
        self._construir_ui()

    @property
    def accion_resultado(self) -> str:
        return self._accion_resultado

    def _construir_ui(self) -> None:
        plan = self._detalle.plan
        titulo = QLabel("Detalle de plan de pago")
        titulo.setObjectName("tituloDialogoSicap")
        descripcion = QLabel(
            "Consulta estructura, cuotas, saldo pendiente y conceptos vinculados del plan."
        )
        descripcion.setObjectName("descripcionDialogoSicap")
        descripcion.setWordWrap(True)
        scroll = QScrollArea()
        scroll.setObjectName("scrollDetallePlan")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        contenedor = QWidget()
        layout_scroll = QVBoxLayout(contenedor)
        layout_scroll.setContentsMargins(0, 0, 0, 0)
        layout_scroll.setSpacing(12)

        panel = QFrame()
        panel.setObjectName("panelContenidoDetallePlan")
        layout_panel = QVBoxLayout(panel)
        layout_panel.setContentsMargins(18, 18, 18, 18)
        layout_panel.setSpacing(14)

        fila_superior = QHBoxLayout()
        bloque = QVBoxLayout()
        codigo = QLabel(plan.codigo)
        codigo.setObjectName("codigoPlanDetalle")
        nombre = QLabel(plan.abonado_nombre)
        nombre.setObjectName("nombrePlanDetalle")
        bloque.addWidget(codigo)
        bloque.addWidget(nombre)
        badge = QLabel(plan.estado.title())
        badge.setObjectName("badgeDetallePlan")
        badge.setProperty("activo", plan.estado == "ACTIVO")
        badge.style().unpolish(badge)
        badge.style().polish(badge)
        fila_superior.addLayout(bloque, 1)
        fila_superior.addWidget(badge, alignment=Qt.AlignmentFlag.AlignTop)

        datos = QGridLayout()
        datos.setHorizontalSpacing(12)
        datos.setVerticalSpacing(12)
        datos.addWidget(self._crear_campo("Casa", plan.casa_codigo), 0, 0)
        datos.addWidget(self._crear_campo("DNI", plan.abonado_dni), 0, 1)
        datos.addWidget(self._crear_campo("Tipo de plan", plan.tipo_plan.replace("_", " ").title()), 1, 0)
        datos.addWidget(self._crear_campo("Concepto", plan.concepto_financiado.replace("_", " ").title()), 1, 1)
        datos.addWidget(self._crear_campo("Prima", self._formateador_moneda(plan.prima_centavos)), 2, 0)
        datos.addWidget(self._crear_campo("Saldo financiado", self._formateador_moneda(plan.saldo_financiado_centavos)), 2, 1)
        datos.addWidget(self._crear_campo("Cuota", self._formateador_moneda(plan.cuota_regular_centavos)), 3, 0)
        datos.addWidget(self._crear_campo("Proxima fecha", self._formateador_fecha(plan.proxima_fecha)), 3, 1)

        fila_metricas = QHBoxLayout()
        fila_metricas.setSpacing(12)
        fila_metricas.addWidget(self._crear_tarjeta("Pendientes", str(plan.cuotas_pendientes)), 1)
        fila_metricas.addWidget(self._crear_tarjeta("En mora", str(plan.cuotas_en_mora)), 1)
        fila_metricas.addWidget(self._crear_tarjeta("Saldo", self._formateador_moneda(plan.saldo_pendiente_centavos)), 1)

        tabla = QTableWidget(0, 4)
        tabla.setObjectName("tablaCuotasPlan")
        configurar_tabla_operativa(tabla, ["Cuota", "Vencimiento", "Saldo", "Estado"])
        tabla.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        tabla.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        tabla.horizontalHeader().setStretchLastSection(True)
        tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        tabla.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        tabla.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        tabla.setRowCount(len(self._detalle.cuotas))
        for fila, cuota in enumerate(self._detalle.cuotas):
            tabla.setItem(fila, 0, crear_item_tabla(f"#{cuota.numero_cuota}"))
            tabla.setItem(fila, 1, crear_item_tabla(self._formateador_fecha(cuota.fecha_vencimiento)))
            tabla.setItem(fila, 2, crear_item_tabla(self._formateador_moneda(cuota.saldo_pendiente_centavos)))
            tabla.setItem(fila, 3, crear_item_tabla(cuota.estado.title()))

        cargos = QLabel(
            "\n".join(self._detalle.cargos_vinculados) if self._detalle.cargos_vinculados else "Sin cargos vinculados automaticamente."
        )
        cargos.setObjectName("textoCargosPlan")
        cargos.setWordWrap(True)

        fila_acciones = QHBoxLayout()
        fila_acciones.setSpacing(10)
        boton_cerrar = BotonAccionContextual("Cerrar", variante="neutro", centrado=True, mostrar_icono=False)
        boton_editar = BotonAccionContextual("Editar", variante="edicion", centrado=True, mostrar_icono=False)
        boton_cerrar.setMinimumWidth(124)
        boton_editar.setMinimumWidth(124)
        boton_cerrar.clicked.connect(self.reject)
        boton_editar.clicked.connect(self._solicitar_edicion)
        fila_acciones.addWidget(boton_cerrar)
        fila_acciones.addStretch(1)
        fila_acciones.addWidget(boton_editar)

        layout_panel.addLayout(fila_superior)
        layout_panel.addWidget(self._crear_seccion("Contexto del plan", "Resumen principal del acuerdo y su relacion con la casa.", [datos]))
        layout_panel.addWidget(self._crear_seccion("Estado financiero", "Cuotas pendientes, mora y saldo vivo del plan.", [fila_metricas]))
        layout_panel.addWidget(self._crear_seccion("Cuotas del plan", "Detalle de cada cuota actualmente registrada.", [tabla]))
        layout_panel.addWidget(self._crear_seccion("Cargos vinculados", "Cargos reales de la casa que el plan intenta cubrir cuando aplica.", [cargos]))
        layout_panel.addLayout(fila_acciones)
        layout_scroll.addWidget(panel)
        scroll.setWidget(contenedor)

        self.layout_cabecera.addWidget(titulo)
        self.layout_cabecera.addWidget(descripcion)
        self.layout_cuerpo.addWidget(scroll)
        self._pie.setVisible(False)
        self._aplicar_estilos_detalle()

    def _solicitar_edicion(self) -> None:
        self._accion_resultado = "editar"
        self.accept()

    def _crear_seccion(self, titulo: str, descripcion: str, elementos: list[object]) -> QFrame:
        seccion = QFrame()
        seccion.setObjectName("seccionDetallePlan")
        layout = QVBoxLayout(seccion)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)
        label_titulo = QLabel(titulo)
        label_titulo.setObjectName("tituloSeccionDetallePlan")
        label_desc = QLabel(descripcion)
        label_desc.setObjectName("descripcionSeccionDetallePlan")
        label_desc.setWordWrap(True)
        layout.addWidget(label_titulo)
        layout.addWidget(label_desc)
        for elemento in elementos:
            if isinstance(elemento, (QGridLayout, QHBoxLayout, QVBoxLayout)):
                layout.addLayout(elemento)
            elif isinstance(elemento, QWidget):
                layout.addWidget(elemento)
        return seccion

    def _crear_campo(self, etiqueta: str, valor: str) -> QFrame:
        tarjeta = QFrame()
        tarjeta.setObjectName("campoDetallePlan")
        layout = QVBoxLayout(tarjeta)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)
        lbl_etiqueta = QLabel(etiqueta)
        lbl_etiqueta.setObjectName("etiquetaDetallePlan")
        lbl_valor = QLabel(valor)
        lbl_valor.setObjectName("valorDetallePlan")
        lbl_valor.setWordWrap(True)
        layout.addWidget(lbl_etiqueta)
        layout.addWidget(lbl_valor)
        return tarjeta

    def _crear_tarjeta(self, titulo: str, valor: str) -> QFrame:
        tarjeta = QFrame()
        tarjeta.setObjectName("tarjetaMiniDetallePlan")
        layout = QVBoxLayout(tarjeta)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(3)
        lbl_titulo = QLabel(titulo)
        lbl_titulo.setObjectName("etiquetaDetallePlan")
        lbl_valor = QLabel(valor)
        lbl_valor.setObjectName("valorTarjetaMiniDetallePlan")
        lbl_valor.setWordWrap(True)
        layout.addWidget(lbl_titulo)
        layout.addWidget(lbl_valor)
        return tarjeta

    def _aplicar_estilos_detalle(self) -> None:
        paleta = self._paleta_tema
        oscuro = self._tema_actual != "claro"
        self.setStyleSheet(
            self.styleSheet()
            + f"""
            QScrollArea#scrollDetallePlan {{
                background: transparent;
                border: none;
            }}
            QFrame#panelContenidoDetallePlan,
            QFrame#seccionDetallePlan,
            QFrame#campoDetallePlan,
            QFrame#tarjetaMiniDetallePlan {{
                background: {'rgba(255,255,255,0.08)' if oscuro else paleta['fondo_superficie']};
                border: 1px solid {'rgba(255,255,255,0.12)' if oscuro else paleta['borde_principal']};
                border-radius: 14px;
            }}
            QLabel#codigoPlanDetalle,
            QLabel#etiquetaDetallePlan,
            QLabel#descripcionSeccionDetallePlan,
            QLabel#textoCargosPlan {{
                color: {'rgba(235,242,248,0.76)' if oscuro else paleta['texto_secundario']};
            }}
            QLabel#nombrePlanDetalle,
            QLabel#valorDetallePlan,
            QLabel#valorTarjetaMiniDetallePlan,
            QLabel#tituloSeccionDetallePlan {{
                color: {'#ffffff' if oscuro else paleta['texto_principal']};
            }}
            QLabel#badgeDetallePlan {{
                border-radius: 11px;
                padding: 6px 10px;
                font-size: 11px;
                font-weight: 800;
                color: {'#f4f8fb' if oscuro else paleta['texto_badge']};
                background: {'rgba(132, 146, 166, 0.22)' if oscuro else paleta['fondo_badge']};
                border: 1px solid {'rgba(255,255,255,0.12)' if oscuro else paleta['borde_suave']};
            }}
            QLabel#badgeDetallePlan[activo="true"] {{
                color: {'#d9fff5' if oscuro else paleta['texto_badge_activo']};
                background: {'rgba(16, 120, 98, 0.22)' if oscuro else paleta['fondo_badge_activo']};
                border-color: {'rgba(158, 231, 214, 0.26)' if oscuro else paleta['borde_badge_activo']};
            }}
            QTableWidget#tablaCuotasPlan {{
                background: {'rgba(255,255,255,0.03)' if oscuro else paleta['fondo_superficie_muy_suave']};
                border: none;
                border-radius: 14px;
            }}
            QTableWidget#tablaCuotasPlan QHeaderView::section {{
                background: {'rgba(255,255,255,0.10)' if oscuro else paleta['fondo_tabla_header']};
                color: {'#f7fbff' if oscuro else paleta['texto_input']};
                border: none;
                padding: 10px 12px;
                font-size: 12px;
                font-weight: 800;
            }}
            """
        )


class VistaPlanesPago(QWidget):
    filtro_texto_cambiado = Signal(str)
    filtro_rapido_cambiado = Signal(str)
    pagina_cambiada = Signal(int)
    nuevo_plan_solicitado = Signal()
    detalle_plan_solicitado = Signal(int)
    editar_plan_solicitado = Signal(int)
    exportar_solicitado = Signal()

    ANCHO_COLUMNA_ACCIONES = 116
    RADIO_PANEL_TABLA = 16
    DURACION_MENSAJE_MS = 3200

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("vistaPlanesPago")
        self._tema_actual = obtener_tema_actual()
        self._paleta_tema = obtener_paleta_tema(self._tema_actual)
        self._pagina_actual = 1
        self._temporizador_mensaje = QTimer(self)
        self._temporizador_mensaje.setSingleShot(True)
        self._temporizador_mensaje.timeout.connect(self._ocultar_mensaje)
        self._construir_ui()
        self._aplicar_estilos()

    def mostrar_resumen(
        self,
        resumen: ResumenPlanesPago,
        formateador_moneda: Callable[[int], str],
    ) -> None:
        self._tarjeta_total.actualizar("Total de planes", str(resumen.total_planes), "Planes registrados en la base local.")
        self._tarjeta_activos.actualizar("Activos", str(resumen.planes_activos), "Acuerdos que siguen vigentes.")
        self._tarjeta_mora.actualizar("Con mora", str(resumen.planes_con_mora), "Planes con cuotas vencidas sin pagar.")
        self._tarjeta_saldo.actualizar("Saldo pendiente", formateador_moneda(resumen.saldo_pendiente_centavos), "Saldo vivo total de los planes.")

    def mostrar_planes(
        self,
        pagina: PaginaPlanesPago,
        formateador_moneda: Callable[[int], str],
        formateador_fecha: Callable[[str], str],
    ) -> None:
        self._pagina_actual = pagina.pagina_actual
        self._tabla.setRowCount(len(pagina.items))
        for fila, plan in enumerate(pagina.items):
            self._tabla.setItem(fila, 0, crear_item_tabla(plan.codigo))
            self._tabla.setItem(fila, 1, crear_item_tabla(plan.casa_codigo))
            self._tabla.setItem(fila, 2, crear_item_tabla(plan.abonado_nombre))
            self._tabla.setItem(fila, 3, crear_item_tabla(plan.tipo_plan.replace("_", " ").title()))
            self._tabla.setItem(fila, 4, crear_item_tabla(plan.resumen_concepto))
            self._tabla.setItem(fila, 5, crear_item_tabla(formateador_moneda(plan.cuota_regular_centavos)))
            self._tabla.setItem(fila, 6, crear_item_tabla(str(plan.cuotas_pendientes)))
            self._tabla.setCellWidget(fila, 7, self._crear_badge_estado(plan.estado))
            self._tabla.setCellWidget(fila, 8, self._crear_acciones_fila(plan))
        sin_datos = len(pagina.items) == 0
        self._tabla.setVisible(not sin_datos)
        self._estado_vacio.setVisible(sin_datos)
        self._label_paginacion.setText(
            f"Mostrando {pagina.indice_inicio}-{pagina.indice_fin} de {pagina.total_registros} registros"
        )
        self._label_numero_pagina.setText(f"Pagina {pagina.pagina_actual} de {pagina.total_paginas}")
        self._boton_pagina_anterior.setEnabled(pagina.pagina_actual > 1)
        self._boton_pagina_siguiente.setEnabled(pagina.pagina_actual < pagina.total_paginas)

    def mostrar_mensaje(self, mensaje: str, es_error: bool = False) -> None:
        self._mensaje.setText(mensaje)
        self._mensaje.setProperty("error", es_error)
        self._mensaje.style().unpolish(self._mensaje)
        self._mensaje.style().polish(self._mensaje)
        self._mensaje.setVisible(bool(mensaje))
        if mensaje:
            self._temporizador_mensaje.start(self.DURACION_MENSAJE_MS)

    def solicitar_datos_plan(
        self,
        casas: Iterable[OpcionCasaPlanPago],
        plan: PlanPago | None = None,
    ) -> FormularioPlanPago | None:
        dialogo = DialogoFormularioPlanPago(casas=casas, plan=plan, parent=self)
        return dialogo.obtener_formulario() if dialogo.exec() == QDialog.DialogCode.Accepted else None

    def mostrar_detalle_plan(
        self,
        detalle: DetallePlanPago,
        formateador_moneda: Callable[[int], str],
        formateador_fecha: Callable[[str], str],
    ) -> str:
        dialogo = DialogoDetallePlanPago(
            detalle=detalle,
            formateador_moneda=formateador_moneda,
            formateador_fecha=formateador_fecha,
            parent=self,
        )
        dialogo.exec()
        return dialogo.accion_resultado

    def solicitar_ruta_exportacion(self) -> str:
        ruta, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar planes de pago",
            "planes_pago.csv",
            "CSV (*.csv)",
        )
        return ruta

    def aplicar_tema(self, nombre_tema: str) -> None:
        self._tema_actual = nombre_tema if nombre_tema in ("oscuro", "claro") else TEMA_SICAP_PREDETERMINADO
        self._paleta_tema = obtener_paleta_tema(self._tema_actual)
        self._aplicar_estilos()

    def _construir_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        encabezado = QHBoxLayout()
        fila_acciones = QHBoxLayout()
        fila_acciones.setSpacing(8)
        boton_info = BotonAccionContextual("Informacion", variante="ayuda", centrado=True, mostrar_icono=False)
        boton_exportar = crear_boton_operativo("Exportar")
        boton_nuevo = crear_boton_operativo("Nuevo plan", principal=True)
        boton_info.clicked.connect(self._mostrar_ayuda)
        boton_exportar.clicked.connect(self.exportar_solicitado.emit)
        boton_nuevo.clicked.connect(self.nuevo_plan_solicitado.emit)
        fila_acciones.addWidget(boton_info)
        fila_acciones.addWidget(boton_exportar)
        fila_acciones.addWidget(boton_nuevo)

        encabezado.addStretch(1)
        encabezado.addLayout(fila_acciones)

        self._mensaje = QLabel("")
        self._mensaje.setObjectName("mensajePlanes")
        self._mensaje.setVisible(False)
        self._mensaje.setWordWrap(True)

        tarjetas = QGridLayout()
        tarjetas.setHorizontalSpacing(10)
        tarjetas.setVerticalSpacing(10)
        self._tarjeta_total = TarjetaResumenPlanPago("key.svg", "#8ec9ff")
        self._tarjeta_activos = TarjetaResumenPlanPago("circle-check.svg", "#8de8c7")
        self._tarjeta_mora = TarjetaResumenPlanPago("clock.svg", "#f7cc7a")
        self._tarjeta_saldo = TarjetaResumenPlanPago("alert-triangle.svg", "#c6b6ff")
        tarjetas.addWidget(self._tarjeta_total, 0, 0)
        tarjetas.addWidget(self._tarjeta_activos, 0, 1)
        tarjetas.addWidget(self._tarjeta_mora, 0, 2)
        tarjetas.addWidget(self._tarjeta_saldo, 0, 3)

        panel_filtros = QFrame()
        panel_filtros.setObjectName("panelOperativoPlanes")
        layout_filtros = QVBoxLayout(panel_filtros)
        layout_filtros.setContentsMargins(14, 14, 14, 14)
        layout_filtros.setSpacing(10)
        self._campo_busqueda = QLineEdit()
        self._campo_busqueda.setPlaceholderText("Buscar por codigo, casa, DNI o abonado")
        self._campo_busqueda.textChanged.connect(self.filtro_texto_cambiado.emit)
        fila_chips = QHBoxLayout()
        fila_chips.setSpacing(6)
        self._grupo_filtros = QButtonGroup(self)
        self._botones_filtro: dict[str, QPushButton] = {}
        for codigo, texto in (
            (FILTRO_PLANES_TODOS, "Todos"),
            (FILTRO_PLANES_ACTIVOS, "Activos"),
            (FILTRO_PLANES_CON_MORA, "Cuotas vencidas"),
            (FILTRO_PLANES_SERVICIO, "Conexion / reconexion"),
        ):
            boton = QPushButton(texto)
            boton.setObjectName("chipFiltroPlan")
            boton.setCheckable(True)
            boton.setCursor(Qt.CursorShape.PointingHandCursor)
            boton.clicked.connect(lambda checked=False, valor=codigo: self.filtro_rapido_cambiado.emit(valor))
            self._grupo_filtros.addButton(boton)
            self._botones_filtro[codigo] = boton
            fila_chips.addWidget(boton)
        self._botones_filtro[FILTRO_PLANES_TODOS].setChecked(True)
        fila_chips.addStretch(1)
        layout_filtros.addWidget(self._campo_busqueda)
        layout_filtros.addLayout(fila_chips)

        panel_tabla = QFrame()
        panel_tabla.setObjectName("panelTablaPlanes")
        layout_tabla = QVBoxLayout(panel_tabla)
        layout_tabla.setContentsMargins(14, 14, 14, 14)
        layout_tabla.setSpacing(10)
        self._tabla = QTableWidget(0, 9)
        self._tabla.setObjectName("tablaPlanes")
        configurar_tabla_operativa(
            self._tabla,
            [
                "Codigo",
                "Casa",
                "Abonado",
                "Tipo",
                "Concepto",
                "Cuota",
                "Pendientes",
                "Estado",
                "Acciones",
            ],
        )
        self._tabla.horizontalHeader().setStretchLastSection(False)
        self._tabla.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self._tabla.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self._tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self._tabla.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self._tabla.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self._tabla.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self._tabla.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self._tabla.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        self._tabla.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        self._tabla.horizontalHeader().setSectionResizeMode(8, QHeaderView.ResizeMode.Interactive)
        self._tabla.setColumnWidth(8, self.ANCHO_COLUMNA_ACCIONES)
        self._tabla.verticalHeader().setDefaultSectionSize(58)
        self._tabla.setFrameShape(QFrame.Shape.NoFrame)
        self._tabla.setViewportMargins(0, 0, 0, self.RADIO_PANEL_TABLA)
        self._tabla.viewport().setObjectName("viewportTablaPlanes")
        self._tabla.viewport().setAutoFillBackground(False)

        self._estado_vacio = QLabel("No hay planes de pago que coincidan con los filtros actuales.")
        self._estado_vacio.setObjectName("estadoVacioPlanes")
        self._estado_vacio.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._estado_vacio.setVisible(False)

        pie = QHBoxLayout()
        self._label_paginacion = QLabel("Mostrando 0-0 de 0 registros")
        self._label_paginacion.setObjectName("textoPiePlanes")
        pie.addWidget(self._label_paginacion)
        pie.addStretch(1)
        self._boton_pagina_anterior = crear_boton_operativo("Anterior")
        self._boton_pagina_siguiente = crear_boton_operativo("Siguiente")
        self._label_numero_pagina = QLabel("Pagina 1 de 1")
        self._label_numero_pagina.setObjectName("textoPiePlanes")
        self._boton_pagina_anterior.clicked.connect(lambda: self.pagina_cambiada.emit(max(1, self._pagina_actual - 1)))
        self._boton_pagina_siguiente.clicked.connect(lambda: self.pagina_cambiada.emit(self._pagina_actual + 1))
        pie.addWidget(self._boton_pagina_anterior)
        pie.addWidget(self._label_numero_pagina)
        pie.addWidget(self._boton_pagina_siguiente)

        layout_tabla.addWidget(self._tabla)
        layout_tabla.addWidget(self._estado_vacio)
        layout_tabla.addLayout(pie)

        layout.addLayout(encabezado)
        layout.addWidget(self._mensaje)
        layout.addLayout(tarjetas)
        layout.addWidget(panel_filtros)
        layout.addWidget(panel_tabla, 1)

    def _crear_badge_estado(self, estado: str) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        badge = QLabel(estado.title())
        badge.setObjectName("badgeEstadoPlan")
        badge.setProperty("activo", estado == "ACTIVO")
        badge.style().unpolish(badge)
        badge.style().polish(badge)
        layout.addWidget(badge, alignment=Qt.AlignmentFlag.AlignCenter)
        return widget

    def _crear_acciones_fila(self, plan: PlanPago) -> QWidget:
        contenedor = QWidget()
        contenedor.setObjectName("contenedorAccionesPlan")
        contenedor.setMinimumWidth(self.ANCHO_COLUMNA_ACCIONES)
        contenedor.setMinimumHeight(58)
        layout = QHBoxLayout(contenedor)
        layout.setContentsMargins(0, 0, 0, 14)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        boton_detalle = BotonIconoFilaPlan("eye.svg", "#4fa3ff", "Ver detalle")
        boton_editar = BotonIconoFilaPlan("key.svg", "#f7cc7a", "Editar")
        boton_detalle.clicked.connect(lambda checked=False, identificador=plan.identificador: self.detalle_plan_solicitado.emit(int(identificador or 0)))
        boton_editar.clicked.connect(lambda checked=False, identificador=plan.identificador: self.editar_plan_solicitado.emit(int(identificador or 0)))
        layout.addWidget(boton_detalle)
        layout.addWidget(boton_editar)
        return contenedor

    def _mostrar_ayuda(self) -> None:
        dialogo = DialogoMensajeSicap(
            titulo="Ayuda del modulo",
            mensaje=(
                "Este modulo sirve para consultar, crear y editar planes de pago del servicio. "
                "La regla vigente del prototipo solo admite conexion o reconexion como concepto financiado. "
                "Las cuotas vencidas del plan se muestran aqui como seguimiento operativo."
            ),
            parent=self,
        )
        dialogo.exec()

    def _ocultar_mensaje(self) -> None:
        self._mensaje.clear()
        self._mensaje.setVisible(False)

    def _aplicar_estilos(self) -> None:
        radio = self.RADIO_PANEL_TABLA
        paleta = self._paleta_tema
        oscuro = self._tema_actual != "claro"
        self.setStyleSheet(
            f"""
            QWidget#vistaPlanesPago {{
                background: transparent;
            }}
            QLabel#tituloModulo {{
                color: {'#ffffff' if oscuro else paleta['texto_principal']};
                font-size: 19px;
                font-weight: 900;
            }}
            QLabel#descripcionModulo,
            QLabel#textoPiePlanes,
            QLabel#detalleTarjetaResumen {{
                color: {'rgba(235, 242, 248, 0.76)' if oscuro else paleta['texto_secundario']};
                font-size: 11px;
                font-weight: 600;
            }}
            QLabel#mensajePlanes {{
                color: {'#d9fff5' if oscuro else paleta['texto_exito']};
                font-size: 12px;
                font-weight: 700;
                padding: 8px 10px;
                border-radius: 12px;
                background-color: {'rgba(16, 120, 98, 0.16)' if oscuro else paleta['fondo_exito']};
                border: 1px solid {'rgba(158, 231, 214, 0.26)' if oscuro else paleta['borde_exito']};
            }}
            QLabel#mensajePlanes[error="true"] {{
                color: {'#ffd4cf' if oscuro else paleta['texto_error']};
                background-color: {'rgba(180, 35, 24, 0.15)' if oscuro else paleta['fondo_error']};
                border: 1px solid {'rgba(255, 205, 199, 0.28)' if oscuro else paleta['borde_error']};
            }}
            QFrame#panelOperativoPlanes,
            QFrame#tarjetaResumenPlanes {{
                background: {'rgba(255,255,255,0.10)' if oscuro else paleta['fondo_superficie']};
                border: 1px solid {'rgba(255,255,255,0.16)' if oscuro else paleta['borde_principal']};
                border-radius: 18px;
            }}
            QFrame#panelTablaPlanes {{
                background: {'rgba(255,255,255,0.10)' if oscuro else paleta['fondo_superficie']};
                border: 1px solid {'rgba(255,255,255,0.16)' if oscuro else paleta['borde_principal']};
                border-radius: {radio}px;
            }}
            QTableWidget#tablaPlanes {{
                background: {'rgba(255,255,255,0.03)' if oscuro else paleta['fondo_superficie_muy_suave']};
                border: none;
                border-radius: {radio}px;
                padding: 0 0 {radio}px 0;
            }}
            QWidget#viewportTablaPlanes {{
                background: transparent;
                border: none;
                border-bottom-left-radius: {radio}px;
                border-bottom-right-radius: {radio}px;
            }}
            QTableWidget#tablaPlanes QHeaderView::section {{
                background: {'rgba(255,255,255,0.10)' if oscuro else paleta['fondo_tabla_header']};
                color: {'#f7fbff' if oscuro else paleta['texto_input']};
                border: none;
                padding: 10px 12px;
                font-size: 12px;
                font-weight: 800;
            }}
            QTableWidget#tablaPlanes::item {{
                padding: 9px 12px;
                border-bottom: 1px solid {'rgba(255,255,255,0.04)' if oscuro else paleta['borde_suave']};
            }}
            QLabel#iconoTarjetaResumen {{
                background: {'rgba(255,255,255,0.08)' if oscuro else paleta['fondo_superficie_suave']};
                border: 1px solid {'rgba(255,255,255,0.10)' if oscuro else paleta['borde_suave']};
                border-radius: 12px;
            }}
            QLabel#tituloTarjetaResumen {{
                color: {'rgba(235,242,248,0.72)' if oscuro else paleta['texto_secundario']};
                font-size: 11px;
                font-weight: 700;
            }}
            QLabel#valorTarjetaResumen {{
                color: {'#ffffff' if oscuro else paleta['texto_principal']};
                font-size: 20px;
                font-weight: 900;
            }}
            QLineEdit {{
                min-height: 36px;
                border: 1px solid {'rgba(255,255,255,0.18)' if oscuro else paleta['borde_medio']};
                border-radius: 12px;
                background: {'rgba(255,255,255,0.11)' if oscuro else paleta['fondo_input']};
                color: {'#f5fbff' if oscuro else paleta['texto_input']};
                padding: 0 10px;
                font-size: 12px;
            }}
            QPushButton#chipFiltroPlan {{
                min-height: 30px;
                border-radius: 11px;
                padding: 0 12px;
                background: {'rgba(255,255,255,0.06)' if oscuro else paleta['fondo_chip']};
                border: 1px solid {'rgba(255,255,255,0.14)' if oscuro else paleta['borde_suave']};
                color: {'#ecf5ff' if oscuro else paleta['texto_chip']};
                font-size: 11px;
                font-weight: 700;
            }}
            QPushButton#chipFiltroPlan:checked {{
                color: {'#0f2d43' if oscuro else paleta['texto_chip_activo']};
                background: {'#d2f4f2' if oscuro else paleta['fondo_chip_activo']};
                border-color: {'rgba(255,255,255,0.18)' if oscuro else paleta['borde_chip_activo']};
            }}
            QLabel#badgeEstadoPlan {{
                border-radius: 11px;
                padding: 6px 10px;
                font-size: 11px;
                font-weight: 800;
                color: {'#f4f8fb' if oscuro else paleta['texto_badge']};
                background: {'rgba(132,146,166,0.22)' if oscuro else paleta['fondo_badge']};
                border: 1px solid {'rgba(255,255,255,0.12)' if oscuro else paleta['borde_suave']};
            }}
            QLabel#badgeEstadoPlan[activo="true"] {{
                color: {'#d9fff5' if oscuro else paleta['texto_badge_activo']};
                background: {'rgba(16,120,98,0.22)' if oscuro else paleta['fondo_badge_activo']};
                border-color: {'rgba(158,231,214,0.26)' if oscuro else paleta['borde_badge_activo']};
            }}
            QWidget#contenedorAccionesPlan {{
                background: transparent;
            }}
            QToolButton#botonIconoFilaPlan {{
                background: transparent;
                border: none;
                border-radius: 8px;
            }}
            QLabel#estadoVacioPlanes {{
                color: {'rgba(235,242,248,0.76)' if oscuro else paleta['texto_secundario']};
                font-size: 12px;
                font-weight: 700;
                padding: 20px 14px;
            }}
            """
        )
