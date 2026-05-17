"""Vista PySide6 del modulo de pagos."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtPrintSupport import QPrintDialog, QPrinterInfo
from PySide6.QtWidgets import (
    QAbstractItemView,
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
    QSpinBox,
    QStackedWidget,
    QTableWidget,
    QTextBrowser,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from comun.ui import (
    BotonAccionContextual,
    DialogoBaseSicap,
    DialogoConfirmacionSicap,
    configurar_tabla_operativa,
    crear_boton_operativo,
    crear_item_tabla,
)
from comun.ui.comprobante_termico import (
    DatosDocumentoRecibo,
    crear_documento_recibo_termico,
    crear_impresora_recibo_termico,
    preparar_documento_para_printer,
)
from comun.ui.temas import TEMA_SICAP_PREDETERMINADO, obtener_paleta_tema
from modulos.pagos.entidades import (
    CargoPago,
    CasaPago,
    DiagnosticoPagoMensual,
    ESTADO_VISUAL_PAGO_BLOQUEADO,
    ESTADO_VISUAL_PAGO_OK,
    EstadoModuloPagos,
    FormularioPago,
    MetodoPago,
    ResumenConfirmacionPago,
    ResultadoPago,
    TIPO_PAGO_CONEXION,
    TIPO_PAGO_MENSUALIDAD,
    TIPO_PAGO_PLAN,
    TIPO_PAGO_RECONEXION,
)


class DialogoVistaPreviaImpresionComprobante(QWidget):
    """Compatibilidad temporal: el backend documental ya no renderiza comprobantes en UI."""

    def __init__(self, datos_documento: DatosDocumentoRecibo, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._documento_base = crear_documento_recibo_termico(datos_documento)
        self.setWindowTitle(f"{datos_documento.numero_comprobante} | Comprobante de pago")
        self.setMinimumWidth(860)
        self.setMinimumHeight(760)
        self._mensaje = QLabel("")
        self._mensaje.setObjectName("mensajeComprobantePago")
        self._mensaje.setVisible(False)

        titulo = QLabel(datos_documento.numero_comprobante)
        titulo.setObjectName("tituloDialogoSicap")
        descripcion = QLabel("Vista previa final del comprobante. Esta misma versión es la que se enviará a impresión.")
        descripcion.setObjectName("descripcionDialogoSicap")
        descripcion.setWordWrap(True)

        panel_ticket = QFrame()
        panel_ticket.setObjectName("panelTicketComprobante")
        layout_ticket = QVBoxLayout(panel_ticket)
        layout_ticket.setContentsMargins(10, 10, 10, 10)
        layout_ticket.setSpacing(0)

        self._visor = QTextBrowser()
        self._visor.setObjectName("visorComprobantePago")
        self._visor.setOpenExternalLinks(False)
        self._visor.setMinimumWidth(330)
        self._visor.setMaximumWidth(330)
        self._visor.setDocument(self._documento_base.clone())
        layout_ticket.addWidget(self._visor)

        contenedor_ticket = QHBoxLayout()
        contenedor_ticket.setContentsMargins(0, 0, 0, 0)
        contenedor_ticket.addStretch(1)
        contenedor_ticket.addWidget(panel_ticket, 0, Qt.AlignmentFlag.AlignTop)
        contenedor_ticket.addStretch(1)

        fila_acciones = QHBoxLayout()
        boton_cerrar = BotonAccionContextual("Cerrar", variante="neutro", centrado=True, mostrar_icono=False)
        boton_imprimir = BotonAccionContextual("Imprimir", variante="primario", centrado=True, mostrar_icono=False)
        boton_cerrar.clicked.connect(self.accept)
        boton_imprimir.clicked.connect(self._imprimir)
        fila_acciones.addWidget(boton_imprimir)
        fila_acciones.addStretch(1)
        fila_acciones.addWidget(boton_cerrar)

        self.layout_cabecera.addWidget(titulo)
        self.layout_cabecera.addWidget(descripcion)
        self.layout_cuerpo.addLayout(contenedor_ticket)
        self.layout_cuerpo.addWidget(self._mensaje)
        self.layout_pie.addLayout(fila_acciones)
        self._aplicar_estilos()

        if not QPrinterInfo.availablePrinters():
            self._mostrar_mensaje(
                "No se detectó una impresora instalada. Puedes revisar el comprobante, pero la impresión no estará disponible hasta configurar una.",
                es_error=True,
            )

    def _imprimir(self) -> None:
        if not QPrinterInfo.availablePrinters():
            self._mostrar_mensaje(
                "No hay impresoras disponibles para enviar el comprobante.",
                es_error=True,
            )
            return
        impresora = crear_impresora_recibo_termico()
        dialogo = QPrintDialog(impresora, self)
        dialogo.setWindowTitle("Imprimir comprobante")
        if dialogo.exec() != QDialog.DialogCode.Accepted:
            return
        documento = preparar_documento_para_printer(self._documento_base, impresora)
        documento.print_(impresora)
        self._mostrar_mensaje("Comprobante enviado a impresión.", es_error=False)

    def _mostrar_mensaje(self, mensaje: str, es_error: bool) -> None:
        self._mensaje.setText(mensaje)
        self._mensaje.setProperty("error", es_error)
        self._mensaje.style().unpolish(self._mensaje)
        self._mensaje.style().polish(self._mensaje)
        self._mensaje.setVisible(True)

    def _aplicar_estilos(self) -> None:
        paleta = obtener_paleta_tema(TEMA_SICAP_PREDETERMINADO)
        self.setStyleSheet(
            self.styleSheet()
            + f"""
            QFrame#panelTicketComprobante {{
                background-color: #ffffff;
                border: 1px solid #d4d4d8;
                border-radius: 10px;
            }}
            QTextBrowser#visorComprobantePago {{
                background-color: #ffffff;
                border: none;
                border-radius: 0px;
                color: #111111;
                padding: 0px;
            }}
            QLabel#mensajeComprobantePago {{
                border-radius: 12px;
                padding: 10px 12px;
                font-size: 12px;
                font-weight: 700;
            }}
            QLabel#mensajeComprobantePago[error="false"] {{
                background-color: {paleta["fondo_exito"]};
                border: 1px solid {paleta["borde_exito"]};
                color: {paleta["texto_exito"]};
            }}
            QLabel#mensajeComprobantePago[error="true"] {{
                background-color: {paleta["fondo_error"]};
                border: 1px solid {paleta["borde_error"]};
                color: {paleta["texto_error"]};
            }}
            """
        )


class FlujoPestanaPendiente(QWidget):
    """Pestana placeholder reservada para fases posteriores."""

    def __init__(self, object_name: str, titulo: str, descripcion: str) -> None:
        super().__init__()
        self.setObjectName(object_name)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        progreso = QFrame()
        progreso.setObjectName("panelProgresoPago")
        layout_progreso = QHBoxLayout(progreso)
        layout_progreso.setContentsMargins(18, 14, 18, 14)
        layout_progreso.setSpacing(10)
        badge = QLabel("Flujo reservado")
        badge.setObjectName("badgePasoPago")
        texto = QLabel("Esta pestaña usará el mismo patrón guiado de un paso visible por vez.")
        texto.setObjectName("textoAyudaPasoPago")
        texto.setWordWrap(True)
        layout_progreso.addWidget(badge, 0)
        layout_progreso.addWidget(texto, 1)

        cuerpo = QFrame()
        cuerpo.setObjectName("panelPasoPago")
        layout_cuerpo = QVBoxLayout(cuerpo)
        layout_cuerpo.setContentsMargins(26, 24, 26, 24)
        layout_cuerpo.setSpacing(12)
        titulo_label = QLabel(titulo)
        titulo_label.setObjectName("tituloPasoPago")
        descripcion_label = QLabel(descripcion)
        descripcion_label.setObjectName("textoAyudaPasoPago")
        descripcion_label.setWordWrap(True)
        ayuda = QLabel(
            "Mantendrá indicador de progreso, navegación entre pasos, confirmación modal y comprobante final en su fase correspondiente."
        )
        ayuda.setObjectName("textoAyudaPasoPago")
        ayuda.setWordWrap(True)
        layout_cuerpo.addWidget(titulo_label)
        layout_cuerpo.addWidget(descripcion_label)
        layout_cuerpo.addWidget(ayuda)
        layout_cuerpo.addStretch(1)

        layout.addWidget(progreso)
        layout.addWidget(cuerpo, 1)


class FlujoPagoMensual(QWidget):
    """Flujo guiado de pago mensual con un solo paso visible por vez."""

    buscar_solicitado = Signal(str)
    casa_solicitada = Signal(int)
    preparar_resumen_solicitado = Signal(object)
    registrar_pago_solicitado = Signal(object)
    estado_visual_cambiado = Signal(str)

    PASO_BUSQUEDA = 0
    PASO_DIAGNOSTICO = 1
    PASO_DATOS = 2
    PASO_RESUMEN = 3

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("flujoPagoMensual")
        self._paleta = obtener_paleta_tema(TEMA_SICAP_PREDETERMINADO)
        self._casas: tuple[CasaPago, ...] = ()
        self._metodos: tuple[MetodoPago, ...] = ()
        self._cargos: tuple[CargoPago, ...] = ()
        self._casa_seleccionada: CasaPago | None = None
        self._resumen_actual: ResumenConfirmacionPago | None = None
        self._diagnostico_actual: DiagnosticoPagoMensual | None = None
        self._mostrar_resultados_busqueda = False
        self._formatear_moneda: Callable[[int], str] = lambda valor: f"L {valor / 100:,.2f}"
        self._formatear_fecha: Callable[[str], str] = lambda valor: valor
        self._construir_ui()
        self._aplicar_estilos()
        self._actualizar_estado_flujo()

    def _construir_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        self._panel_progreso = QFrame()
        self._panel_progreso.setObjectName("panelProgresoPago")
        layout_progreso = QVBoxLayout(self._panel_progreso)
        layout_progreso.setContentsMargins(18, 16, 18, 16)
        layout_progreso.setSpacing(12)

        fila_superior = QHBoxLayout()
        self._label_breadcrumb = QLabel("Paso 1 de 4")
        self._label_breadcrumb.setObjectName("breadcrumbPago")
        self._boton_reiniciar = crear_boton_operativo("Reiniciar flujo")
        self._boton_reiniciar.clicked.connect(self.reiniciar_flujo)
        fila_superior.addWidget(self._label_breadcrumb)
        fila_superior.addStretch(1)
        fila_superior.addWidget(self._boton_reiniciar)

        self._fila_pasos = QHBoxLayout()
        self._fila_pasos.setSpacing(12)
        self._chips_paso: list[QLabel] = []
        for indice, titulo in enumerate(("Buscar casa", "Diagnóstico", "Datos del pago", "Resumen"), start=1):
            chip = QLabel(f"{indice}. {titulo}")
            chip.setObjectName("chipPasoPago")
            self._chips_paso.append(chip)
            self._fila_pasos.addWidget(chip)

        layout_progreso.addLayout(fila_superior)
        layout_progreso.addLayout(self._fila_pasos)

        self._stack = QStackedWidget()
        self._stack.setObjectName("stackPagoMensual")
        self._stack.addWidget(self._envolver_paso_en_scroll(self._crear_paso_busqueda()))
        self._stack.addWidget(self._envolver_paso_en_scroll(self._crear_paso_diagnostico()))
        self._stack.addWidget(self._envolver_paso_en_scroll(self._crear_paso_datos()))
        self._stack.addWidget(self._envolver_paso_en_scroll(self._crear_paso_resumen()))

        layout.addWidget(self._panel_progreso)
        layout.addWidget(self._stack, 1)

    @staticmethod
    def _envolver_paso_en_scroll(contenido: QWidget) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(contenido)
        return scroll

    def _crear_paso_busqueda(self) -> QWidget:
        pagina = QFrame()
        pagina.setObjectName("panelPasoPago")
        layout = QVBoxLayout(pagina)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(12)

        titulo = QLabel("Paso 1: Buscar casa")
        titulo.setObjectName("tituloPasoPago")
        descripcion = QLabel(
            "Busca por DNI, nombre del abonado, código de casa o barrio. Al seleccionar una casa, el flujo avanza al diagnóstico."
        )
        descripcion.setObjectName("textoAyudaPasoPago")
        descripcion.setWordWrap(True)

        fila_busqueda = QHBoxLayout()
        self._input_busqueda = QLineEdit()
        self._input_busqueda.setPlaceholderText("DNI, nombre, código de casa o barrio")
        self._input_busqueda.returnPressed.connect(self._emitir_busqueda)
        boton_buscar = crear_boton_operativo("Buscar")
        boton_buscar.clicked.connect(self._emitir_busqueda)
        fila_busqueda.addWidget(self._input_busqueda, 1)
        fila_busqueda.addWidget(boton_buscar)

        self._label_resultados = QLabel("Busca una casa para iniciar el pago mensual.")
        self._label_resultados.setObjectName("textoEstadoPasoPago")
        self._label_resultados.setWordWrap(True)

        self._tabla_casas = QTableWidget()
        configurar_tabla_operativa(
            self._tabla_casas,
            ["Casa", "Abonado", "Estado", "Vencidos", "Deuda"],
        )
        self._tabla_casas.setObjectName("tablaCasasPagoMensual")
        self._tabla_casas.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._tabla_casas.cellClicked.connect(self._seleccionar_casa)
        self._tabla_casas.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        layout.addWidget(titulo)
        layout.addWidget(descripcion)
        layout.addLayout(fila_busqueda)
        layout.addWidget(self._label_resultados)
        layout.addWidget(self._tabla_casas, 1)
        return pagina

    def _crear_paso_diagnostico(self) -> QWidget:
        pagina = QFrame()
        pagina.setObjectName("panelPasoPago")
        layout = QVBoxLayout(pagina)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(14)

        titulo = QLabel("Paso 2: Diagnóstico de casa y cargos pendientes")
        titulo.setObjectName("tituloPasoPago")
        descripcion = QLabel(
            "Revisa el estado actual de la casa, la deuda acumulada y los cargos mensuales pendientes que serán cobrados desde el período más antiguo."
        )
        descripcion.setObjectName("textoAyudaPasoPago")
        descripcion.setWordWrap(True)

        self._panel_diagnostico = QFrame()
        self._panel_diagnostico.setObjectName("panelDiagnosticoPago")
        layout_diagnostico = QVBoxLayout(self._panel_diagnostico)
        layout_diagnostico.setContentsMargins(18, 18, 18, 18)
        layout_diagnostico.setSpacing(12)

        self._label_casa_diagnostico = QLabel("Sin casa seleccionada")
        self._label_casa_diagnostico.setObjectName("tituloDiagnosticoPago")
        self._label_abonado_diagnostico = QLabel("")
        self._label_abonado_diagnostico.setObjectName("textoAyudaPasoPago")
        self._label_alerta_diagnostico = QLabel(
            "Aquí aparecerán alertas y validaciones relevantes antes del cobro mensual."
        )
        self._label_alerta_diagnostico.setObjectName("textoEstadoPasoPago")
        self._label_alerta_diagnostico.setWordWrap(True)

        grilla = QGridLayout()
        grilla.setHorizontalSpacing(12)
        grilla.setVerticalSpacing(10)
        self._metricas_diagnostico: dict[str, QLabel] = {}
        for fila, etiqueta in enumerate(("Barrio", "Estado del servicio", "Meses pendientes", "Meses vencidos", "Deuda anterior")):
            label = QLabel(etiqueta)
            label.setObjectName("etiquetaMetricaPago")
            valor = QLabel("-")
            valor.setObjectName("valorMetricaPago")
            self._metricas_diagnostico[etiqueta] = valor
            grilla.addWidget(label, fila, 0)
            grilla.addWidget(valor, fila, 1)

        layout_diagnostico.addWidget(self._label_casa_diagnostico)
        layout_diagnostico.addWidget(self._label_abonado_diagnostico)
        layout_diagnostico.addLayout(grilla)
        layout_diagnostico.addWidget(self._label_alerta_diagnostico)

        ayuda_cargos = QLabel(
            "Regla activa: el sistema cobra desde el período más antiguo, no permite saltar meses vencidos y solo muestra adelantos después de cubrir vencidos."
        )
        ayuda_cargos.setObjectName("textoAyudaPasoPago")
        ayuda_cargos.setWordWrap(True)

        self._tabla_cargos = QTableWidget()
        configurar_tabla_operativa(
            self._tabla_cargos,
            ["Período", "Descripción", "Estado", "Saldo", "Etiqueta"],
        )
        self._tabla_cargos.setObjectName("tablaCargosPagoMensual")
        self._tabla_cargos.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self._tabla_cargos.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        self._label_estado_cargos = QLabel("Selecciona una casa para ver sus cargos.")
        self._label_estado_cargos.setObjectName("textoEstadoPasoPago")
        self._label_estado_cargos.setWordWrap(True)

        fila_acciones = QHBoxLayout()
        boton_anterior = crear_boton_operativo("Anterior")
        boton_anterior.clicked.connect(lambda: self._ir_a_paso(self.PASO_BUSQUEDA))
        self._boton_diagnostico_siguiente = crear_boton_operativo("Siguiente", principal=True)
        self._boton_diagnostico_siguiente.clicked.connect(lambda: self._ir_a_paso(self.PASO_DATOS))
        fila_acciones.addWidget(boton_anterior)
        fila_acciones.addStretch(1)
        fila_acciones.addWidget(self._boton_diagnostico_siguiente)

        layout.addWidget(titulo)
        layout.addWidget(descripcion)
        layout.addWidget(self._panel_diagnostico)
        layout.addWidget(ayuda_cargos)
        layout.addWidget(self._label_estado_cargos)
        layout.addWidget(self._tabla_cargos, 1)
        layout.addLayout(fila_acciones)
        return pagina

    def _crear_paso_datos(self) -> QWidget:
        pagina = QFrame()
        pagina.setObjectName("panelPasoPago")
        layout = QVBoxLayout(pagina)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(12)

        titulo = QLabel("Paso 3: Ingresar datos del pago")
        titulo.setObjectName("tituloPasoPago")
        descripcion = QLabel(
            "Captura la cantidad de meses, método de pago, referencia y observaciones. Desde aquí se prepara el resumen real antes de confirmar."
        )
        descripcion.setObjectName("textoAyudaPasoPago")
        descripcion.setWordWrap(True)

        self._label_contexto_datos = QLabel("Sin casa seleccionada.")
        self._label_contexto_datos.setObjectName("textoEstadoPasoPago")
        self._label_contexto_datos.setWordWrap(True)

        formulario = QFrame()
        formulario.setObjectName("panelFormularioPago")
        layout_formulario = QVBoxLayout(formulario)
        layout_formulario.setContentsMargins(18, 18, 18, 18)
        layout_formulario.setSpacing(14)

        self._input_cantidad_meses = QSpinBox()
        self._input_cantidad_meses.setRange(1, 36)
        self._input_cantidad_meses.setValue(1)
        self._input_cantidad_meses.setSuffix(" mes(es)")
        self._combo_metodo = QComboBox()
        self._input_referencia = QLineEdit()
        self._input_referencia.setPlaceholderText("Referencia para transferencia o depósito, si aplica")
        self._input_observaciones = QLineEdit()
        self._input_observaciones.setPlaceholderText("Observaciones internas opcionales")
        self._mensaje_formulario = QLabel("Completa los datos y continúa para revisar el resumen.")
        self._mensaje_formulario.setObjectName("textoEstadoPasoPago")
        self._mensaje_formulario.setWordWrap(True)

        grilla_formulario = QGridLayout()
        grilla_formulario.setHorizontalSpacing(14)
        grilla_formulario.setVerticalSpacing(10)
        grilla_formulario.addWidget(self._crear_label_campo("Cantidad de meses a cubrir"), 0, 0)
        grilla_formulario.addWidget(self._crear_label_campo("Método de pago"), 0, 1)
        grilla_formulario.addWidget(self._input_cantidad_meses, 1, 0)
        grilla_formulario.addWidget(self._combo_metodo, 1, 1)
        grilla_formulario.addWidget(self._crear_label_campo("Referencia"), 2, 0, 1, 2)
        grilla_formulario.addWidget(self._input_referencia, 3, 0, 1, 2)
        grilla_formulario.addWidget(self._crear_label_campo("Observaciones"), 4, 0, 1, 2)
        grilla_formulario.addWidget(self._input_observaciones, 5, 0, 1, 2)

        layout_formulario.addLayout(grilla_formulario)
        layout_formulario.addWidget(self._mensaje_formulario)

        fila_acciones = QHBoxLayout()
        boton_anterior = crear_boton_operativo("Anterior")
        boton_anterior.clicked.connect(lambda: self._ir_a_paso(self.PASO_DIAGNOSTICO))
        self._boton_datos_siguiente = crear_boton_operativo("Siguiente", principal=True)
        self._boton_datos_siguiente.clicked.connect(self._solicitar_preparacion_resumen)
        fila_acciones.addWidget(boton_anterior)
        fila_acciones.addStretch(1)
        fila_acciones.addWidget(self._boton_datos_siguiente)

        layout.addWidget(titulo)
        layout.addWidget(descripcion)
        layout.addWidget(self._label_contexto_datos)
        layout.addWidget(formulario)
        layout.addLayout(fila_acciones)
        return pagina

    def _crear_paso_resumen(self) -> QWidget:
        pagina = QFrame()
        pagina.setObjectName("panelPasoPago")
        layout = QVBoxLayout(pagina)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(12)

        titulo = QLabel("Paso 4: Revisar resumen")
        titulo.setObjectName("tituloPasoPago")
        descripcion = QLabel(
            "Revisa el detalle final antes de confirmar. El pago no debe mezclar conceptos y no podrá anularse en el flujo normal del prototipo."
        )
        descripcion.setObjectName("textoAyudaPasoPago")
        descripcion.setWordWrap(True)

        self._label_resumen_principal = QLabel("Sin resumen preparado.")
        self._label_resumen_principal.setObjectName("tituloDiagnosticoPago")
        self._label_resumen_contexto = QLabel("Completa el paso anterior para generar el resumen.")
        self._label_resumen_contexto.setObjectName("textoEstadoPasoPago")
        self._label_resumen_contexto.setWordWrap(True)

        grilla = QGridLayout()
        grilla.setHorizontalSpacing(12)
        grilla.setVerticalSpacing(10)
        self._metricas_resumen: dict[str, QLabel] = {}
        for fila, etiqueta in enumerate(("Casa", "Abonado", "Barrio", "Método", "Referencia", "Saldo anterior", "Total", "Saldo posterior")):
            label = QLabel(etiqueta)
            label.setObjectName("etiquetaMetricaPago")
            valor = QLabel("-")
            valor.setObjectName("valorMetricaPago")
            self._metricas_resumen[etiqueta] = valor
            grilla.addWidget(label, fila, 0)
            grilla.addWidget(valor, fila, 1)

        self._visor_resumen = QTextBrowser()
        self._visor_resumen.setObjectName("visorResumenPago")
        self._visor_resumen.setOpenExternalLinks(False)

        fila_acciones = QHBoxLayout()
        boton_anterior = crear_boton_operativo("Anterior")
        boton_anterior.clicked.connect(lambda: self._ir_a_paso(self.PASO_DATOS))
        self._boton_confirmar = crear_boton_operativo("Confirmar pago", principal=True)
        self._boton_confirmar.clicked.connect(self._emitir_registro)
        fila_acciones.addWidget(boton_anterior)
        fila_acciones.addStretch(1)
        fila_acciones.addWidget(self._boton_confirmar)

        layout.addWidget(titulo)
        layout.addWidget(descripcion)
        layout.addWidget(self._label_resumen_principal)
        layout.addWidget(self._label_resumen_contexto)
        layout.addLayout(grilla)
        layout.addWidget(self._visor_resumen, 1)
        layout.addLayout(fila_acciones)
        return pagina

    @staticmethod
    def _crear_label_campo(texto: str) -> QLabel:
        label = QLabel(texto)
        label.setObjectName("labelCampoPago")
        return label

    def mostrar_estado(
        self,
        estado: EstadoModuloPagos,
        formatear_moneda: Callable[[int], str],
        formatear_fecha: Callable[[str], str],
        mostrar_casas: bool = False,
    ) -> None:
        self._casas = estado.casas
        self._metodos = estado.metodos_pago
        self._mostrar_resultados_busqueda = mostrar_casas
        self._formatear_moneda = formatear_moneda
        self._formatear_fecha = formatear_fecha
        self._llenar_casas()
        self._llenar_metodos()
        if self._casa_seleccionada is not None:
            casa = next((item for item in self._casas if item.casa_id == self._casa_seleccionada.casa_id), None)
            if casa is not None:
                self._casa_seleccionada = casa
                self._marcar_casa_en_tabla(casa.casa_id)
                self._actualizar_contexto_casa()
            else:
                self.reiniciar_flujo()
        self._actualizar_estado_flujo()

    def mostrar_cargos_mensuales(
        self,
        casa_id: int,
        cargos: tuple[CargoPago, ...],
        diagnostico: DiagnosticoPagoMensual | None = None,
    ) -> None:
        if self._casa_seleccionada is None or self._casa_seleccionada.casa_id != casa_id:
            return
        self._cargos = cargos
        self._diagnostico_actual = diagnostico
        self._tabla_cargos.setRowCount(len(cargos))
        if not cargos:
            self._label_estado_cargos.setText("No hay cargos mensuales pendientes para esta casa.")
        else:
            self._label_estado_cargos.setText(
                f"Se encontraron {len(cargos)} cargo(s) mensual(es) para el flujo de pago mensual."
            )
        for fila, cargo in enumerate(cargos):
            valores = (
                cargo.periodo_nombre,
                cargo.descripcion,
                cargo.estado,
                self._formatear_moneda(cargo.saldo_pendiente_centavos),
                self._resolver_etiqueta_cargo(cargo),
            )
            for columna, valor in enumerate(valores):
                self._tabla_cargos.setItem(fila, columna, crear_item_tabla(valor))
        self._actualizar_contexto_casa()
        self._actualizar_estado_flujo()

    def mostrar_previsualizacion_pago(
        self,
        resumen: ResumenConfirmacionPago | None,
        resultado: ResultadoPago | None,
        formatear_moneda: Callable[[int], str] | None = None,
    ) -> None:
        if resultado is not None:
            self._resumen_actual = None
            self._mensaje_formulario.setText(resultado.mensaje)
            self._mensaje_formulario.setProperty("estado", "error")
            self._mensaje_formulario.style().unpolish(self._mensaje_formulario)
            self._mensaje_formulario.style().polish(self._mensaje_formulario)
            self._actualizar_estado_flujo()
            return
        if resumen is None:
            return
        formateador = formatear_moneda or self._formatear_moneda
        self._resumen_actual = resumen
        self._label_resumen_principal.setText("Resumen mensual listo para confirmar")
        self._label_resumen_contexto.setText(
            "Revisa los cargos cubiertos, los posibles adelantos y el aviso de no anulación antes de confirmar."
        )
        self._metricas_resumen["Casa"].setText(resumen.casa.casa_codigo)
        self._metricas_resumen["Abonado"].setText(resumen.casa.abonado_nombre)
        self._metricas_resumen["Barrio"].setText(resumen.casa.barrio_nombre or "Sin barrio")
        self._metricas_resumen["Método"].setText(resumen.metodo_pago.nombre)
        self._metricas_resumen["Referencia"].setText(resumen.referencia or "No aplica")
        self._metricas_resumen["Saldo anterior"].setText(formateador(resumen.saldo_anterior_centavos))
        self._metricas_resumen["Total"].setText(formateador(resumen.total_pago_centavos))
        self._metricas_resumen["Saldo posterior"].setText(formateador(resumen.saldo_posterior_centavos))
        self._visor_resumen.setHtml(self._renderizar_resumen_html(resumen, formateador))
        self._mensaje_formulario.setText("Resumen preparado correctamente.")
        self._mensaje_formulario.setProperty("estado", "exito")
        self._mensaje_formulario.style().unpolish(self._mensaje_formulario)
        self._mensaje_formulario.style().polish(self._mensaje_formulario)
        self._ir_a_paso(self.PASO_RESUMEN)

    def obtener_casa_seleccionada_id(self) -> int | None:
        return self._casa_seleccionada.casa_id if self._casa_seleccionada is not None else None

    def reiniciar_flujo(self) -> None:
        self._casa_seleccionada = None
        self._cargos = ()
        self._resumen_actual = None
        self._input_busqueda.clear()
        self._input_cantidad_meses.setValue(1)
        self._combo_metodo.setCurrentIndex(0)
        self._input_referencia.clear()
        self._input_observaciones.clear()
        self._mostrar_resultados_busqueda = False
        self._diagnostico_actual = None
        self._tabla_casas.clearSelection()
        self._tabla_casas.setRowCount(0)
        self._tabla_cargos.setRowCount(0)
        self._label_resultados.setText("Busca una casa para iniciar el pago mensual.")
        self._mensaje_formulario.setText("Completa los datos y continúa para revisar el resumen.")
        self._mensaje_formulario.setProperty("estado", "")
        self._actualizar_contexto_casa()
        self._ir_a_paso(self.PASO_BUSQUEDA)

    def _emitir_busqueda(self) -> None:
        texto = self._input_busqueda.text().strip()
        self._mostrar_resultados_busqueda = bool(texto)
        if not texto:
            self._tabla_casas.setRowCount(0)
            self._label_resultados.setText("Busca una casa para iniciar el pago mensual.")
        self.buscar_solicitado.emit(texto)

    def _seleccionar_casa(self, fila: int, _columna: int = 0) -> None:
        item = self._tabla_casas.item(fila, 0)
        if item is None:
            return
        casa_id = int(item.data(Qt.ItemDataRole.UserRole))
        casa = next((valor for valor in self._casas if valor.casa_id == casa_id), None)
        if casa is None:
            return
        self._casa_seleccionada = casa
        self._cargos = ()
        self._resumen_actual = None
        self._diagnostico_actual = None
        self._actualizar_contexto_casa()
        self.casa_solicitada.emit(casa_id)
        self._ir_a_paso(self.PASO_DIAGNOSTICO)

    def _solicitar_preparacion_resumen(self) -> None:
        if not self._permite_pago_mensual_directo():
            self._mostrar_error_formulario(
                "El pago mensual directo solo está disponible para casas ACTIVAS con abonado responsable ACTIVO."
            )
            return
        formulario = self._construir_formulario()
        if formulario is None:
            return
        self.preparar_resumen_solicitado.emit(formulario)

    def _emitir_registro(self) -> None:
        if not self._permite_pago_mensual_directo():
            self._mostrar_error_formulario(
                "El pago mensual directo solo está disponible para casas ACTIVAS con abonado responsable ACTIVO."
            )
            return
        formulario = self._construir_formulario()
        if formulario is None or self._resumen_actual is None:
            return
        self.registrar_pago_solicitado.emit(formulario)

    def _construir_formulario(self) -> FormularioPago | None:
        if self._casa_seleccionada is None:
            self._mostrar_error_formulario("Selecciona una casa antes de continuar.")
            return None
        metodo_pago_id = self._combo_metodo.currentData()
        if metodo_pago_id is None:
            self._mostrar_error_formulario("Selecciona un método de pago.")
            return None
        return FormularioPago(
            casa_id=self._casa_seleccionada.casa_id,
            tipo_pago=TIPO_PAGO_MENSUALIDAD,
            cantidad_meses=int(self._input_cantidad_meses.value()),
            metodo_pago_id=int(metodo_pago_id),
            referencia=self._input_referencia.text(),
            observaciones=self._input_observaciones.text(),
        )

    def _mostrar_error_formulario(self, mensaje: str) -> None:
        self._mensaje_formulario.setText(mensaje)
        self._mensaje_formulario.setProperty("estado", "error")
        self._mensaje_formulario.style().unpolish(self._mensaje_formulario)
        self._mensaje_formulario.style().polish(self._mensaje_formulario)

    def _llenar_casas(self) -> None:
        if not self._mostrar_resultados_busqueda:
            self._tabla_casas.setRowCount(0)
            self._label_resultados.setText("Busca una casa para iniciar el pago mensual.")
            return
        self._tabla_casas.setRowCount(len(self._casas))
        for fila, casa in enumerate(self._casas):
            valores = (
                casa.casa_codigo,
                casa.abonado_nombre,
                casa.estado_servicio,
                casa.meses_vencidos,
                self._formatear_moneda(casa.deuda_total_centavos),
            )
            for columna, valor in enumerate(valores):
                item = crear_item_tabla(valor)
                item.setData(Qt.ItemDataRole.UserRole, casa.casa_id)
                self._tabla_casas.setItem(fila, columna, item)
        self._label_resultados.setText(
            f"Se encontraron {len(self._casas)} casa(s) disponibles para iniciar el flujo mensual."
            if self._casas
            else "No se encontraron casas con ese criterio de búsqueda."
        )

    def _llenar_metodos(self) -> None:
        metodo_actual = self._combo_metodo.currentData()
        self._combo_metodo.blockSignals(True)
        self._combo_metodo.clear()
        self._combo_metodo.addItem("Selecciona un método", None)
        for metodo in self._metodos:
            etiqueta = metodo.nombre
            if metodo.requiere_referencia:
                etiqueta = f"{etiqueta} - requiere referencia"
            self._combo_metodo.addItem(etiqueta, metodo.identificador)
        if metodo_actual is not None:
            indice = self._combo_metodo.findData(metodo_actual)
            if indice >= 0:
                self._combo_metodo.setCurrentIndex(indice)
        self._combo_metodo.blockSignals(False)

    def _marcar_casa_en_tabla(self, casa_id: int) -> None:
        for fila in range(self._tabla_casas.rowCount()):
            item = self._tabla_casas.item(fila, 0)
            if item is not None and int(item.data(Qt.ItemDataRole.UserRole)) == casa_id:
                self._tabla_casas.selectRow(fila)
                return

    def _actualizar_contexto_casa(self) -> None:
        casa = self._casa_seleccionada
        if casa is None:
            self._label_casa_diagnostico.setText("Sin casa seleccionada")
            self._label_abonado_diagnostico.setText("")
            self._label_alerta_diagnostico.setText(
                "Aquí aparecerán alertas y validaciones relevantes antes del cobro mensual."
            )
            self._label_contexto_datos.setText("Sin casa seleccionada.")
            for valor in self._metricas_diagnostico.values():
                valor.setText("-")
            self._aplicar_estado_visual_diagnostico(None)
            return
        self._label_casa_diagnostico.setText(casa.casa_codigo)
        self._label_abonado_diagnostico.setText(
            f"{casa.abonado_nombre} | DNI {casa.abonado_dni}"
        )
        self._label_alerta_diagnostico.setText(
            self._diagnostico_actual.mensaje_diagnostico
            if self._diagnostico_actual is not None
            else "Aquí aparecerán alertas y validaciones relevantes antes del cobro mensual."
        )
        self._metricas_diagnostico["Barrio"].setText(casa.barrio_nombre or "Sin barrio")
        self._metricas_diagnostico["Estado del servicio"].setText(casa.estado_servicio)
        self._metricas_diagnostico["Meses pendientes"].setText(str(casa.meses_pendientes))
        self._metricas_diagnostico["Meses vencidos"].setText(str(casa.meses_vencidos))
        self._metricas_diagnostico["Deuda anterior"].setText(
            self._formatear_moneda(casa.deuda_total_centavos)
        )
        self._label_contexto_datos.setText(
            f"Casa {casa.casa_codigo} · {casa.abonado_nombre} · Estado {casa.estado_servicio}"
        )
        self._aplicar_estado_visual_diagnostico(self._diagnostico_actual)

    def _ir_a_paso(self, paso: int) -> None:
        self._stack.setCurrentIndex(paso)
        self._actualizar_estado_flujo()

    def _actualizar_estado_flujo(self) -> None:
        paso = self._stack.currentIndex()
        self._label_breadcrumb.setText(f"Paso {paso + 1} de 4")
        self._boton_reiniciar.setVisible(paso > self.PASO_BUSQUEDA or self._casa_seleccionada is not None)
        for indice, chip in enumerate(self._chips_paso):
            chip.setProperty("activo", indice == paso)
            chip.setProperty("completado", indice < paso)
            if indice == self.PASO_DIAGNOSTICO and self._diagnostico_actual is not None:
                chip.setProperty(
                    "bloqueado",
                    self._diagnostico_actual.estado_visual == ESTADO_VISUAL_PAGO_BLOQUEADO,
                )
                chip.setProperty(
                    "habilitado",
                    self._diagnostico_actual.estado_visual == ESTADO_VISUAL_PAGO_OK,
                )
            else:
                chip.setProperty("bloqueado", False)
                chip.setProperty("habilitado", False)
            chip.style().unpolish(chip)
            chip.style().polish(chip)
        permite_mensualidad = self._permite_pago_mensual_directo()
        self._boton_diagnostico_siguiente.setEnabled(permite_mensualidad)
        self._boton_datos_siguiente.setEnabled(permite_mensualidad)
        self._boton_confirmar.setEnabled(self._resumen_actual is not None)
        self.estado_visual_cambiado.emit(
            self._diagnostico_actual.estado_visual if self._diagnostico_actual is not None else ""
        )

    def _permite_pago_mensual_directo(self) -> bool:
        return bool(self._diagnostico_actual is not None and self._diagnostico_actual.permite_continuar)

    def _aplicar_estado_visual_diagnostico(
        self,
        diagnostico: DiagnosticoPagoMensual | None,
    ) -> None:
        estado = ""
        if diagnostico is not None:
            estado = "error" if diagnostico.estado_visual == ESTADO_VISUAL_PAGO_BLOQUEADO else "exito"
        for widget in (
            self._label_alerta_diagnostico,
            self._label_estado_cargos,
            self._label_contexto_datos,
        ):
            widget.setProperty("estado", estado)
            widget.style().unpolish(widget)
            widget.style().polish(widget)
        self._panel_diagnostico.setProperty("estadoVisual", estado)
        self._panel_diagnostico.style().unpolish(self._panel_diagnostico)
        self._panel_diagnostico.style().polish(self._panel_diagnostico)

    @staticmethod
    def _resolver_etiqueta_cargo(cargo: CargoPago) -> str:
        if cargo.estado == "VENCIDO":
            return "Vencido"
        if cargo.estado == "PARCIAL":
            return "Parcial"
        return "Pendiente"

    @staticmethod
    def _renderizar_resumen_html(
        resumen: ResumenConfirmacionPago,
        formatear_moneda: Callable[[int], str],
    ) -> str:
        detalles = []
        for detalle in resumen.detalles:
            detalles.append(
                "<li><strong>{periodo}</strong> · {etiqueta} · {descripcion} · {monto}</li>".format(
                    periodo=detalle.periodo_nombre,
                    etiqueta=detalle.etiqueta,
                    descripcion=detalle.descripcion,
                    monto=formatear_moneda(detalle.monto_centavos),
                )
            )
        return (
            "<html><body>"
            "<p><strong>Detalle de cargos y meses que serán cubiertos:</strong></p>"
            f"<ul>{''.join(detalles) or '<li>Sin detalle.</li>'}</ul>"
            "<p><strong>Aviso:</strong> este pago se registrará como mensualidad, no mezclará otros conceptos y no podrá anularse dentro del flujo normal del prototipo.</p>"
            "</body></html>"
        )

    def _aplicar_estilos(self) -> None:
        paleta = self._paleta
        self.setStyleSheet(
            f"""
            QWidget#flujoPagoMensual {{
                background: transparent;
                color: {paleta["texto_principal"]};
            }}
            QFrame#panelProgresoPago,
            QFrame#panelPasoPago,
            QFrame#panelDiagnosticoPago,
            QFrame#panelFormularioPago {{
                background-color: {paleta["fondo_superficie_suave"]};
                border: 1px solid {paleta["borde_suave"]};
                border-radius: 18px;
            }}
            QLabel#breadcrumbPago,
            QLabel#textoAyudaPasoPago {{
                color: {paleta["texto_secundario"]};
                font-size: 12px;
            }}
            QLabel#chipPasoPago {{
                background-color: rgba(71, 85, 105, 0.22);
                border: 1px solid {paleta["borde_suave"]};
                border-radius: 12px;
                color: {paleta["texto_secundario"]};
                font-size: 11px;
                font-weight: 700;
                padding: 8px 12px;
            }}
            QLabel#chipPasoPago[activo="true"] {{
                background-color: rgba(45, 212, 191, 0.18);
                border: 1px solid {paleta["borde_principal"]};
                color: #ffffff;
            }}
            QLabel#chipPasoPago[habilitado="true"] {{
                background-color: rgba(16, 120, 98, 0.22);
                border: 1px solid {paleta["borde_exito"]};
                color: {paleta["texto_exito"]};
            }}
            QLabel#chipPasoPago[bloqueado="true"] {{
                background-color: rgba(180, 35, 24, 0.18);
                border: 1px solid {paleta["borde_error"]};
                color: {paleta["texto_error"]};
            }}
            QLabel#chipPasoPago[completado="true"] {{
                background-color: rgba(34, 197, 94, 0.16);
                border: 1px solid {paleta["borde_exito"]};
                color: {paleta["texto_exito"]};
            }}
            QLabel#tituloPasoPago,
            QLabel#tituloDiagnosticoPago {{
                color: #ffffff;
                font-size: 16px;
                font-weight: 800;
            }}
            QLabel#textoEstadoPasoPago {{
                background-color: rgba(44, 58, 92, 0.54);
                border: 1px solid rgba(125, 170, 236, 0.28);
                border-radius: 12px;
                color: {paleta["texto_principal"]};
                font-size: 12px;
                padding: 10px 12px;
            }}
            QLabel#textoEstadoPasoPago[estado="error"] {{
                background-color: rgba(166, 40, 40, 0.18);
                border: 1px solid rgba(248, 113, 113, 0.36);
                color: {paleta["texto_error"]};
            }}
            QLabel#textoEstadoPasoPago[estado="exito"] {{
                background-color: rgba(18, 119, 97, 0.18);
                border: 1px solid rgba(109, 241, 220, 0.34);
                color: {paleta["texto_exito"]};
            }}
            QFrame#panelDiagnosticoPago[estadoVisual="error"] {{
                background-color: rgba(144, 32, 32, 0.14);
                border: 1px solid rgba(248, 113, 113, 0.30);
            }}
            QFrame#panelDiagnosticoPago[estadoVisual="exito"] {{
                background-color: rgba(16, 120, 98, 0.16);
                border: 1px solid rgba(109, 241, 220, 0.28);
            }}
            QLabel#etiquetaMetricaPago,
            QLabel#labelCampoPago {{
                color: {paleta["texto_secundario"]};
                font-size: 11px;
                font-weight: 700;
            }}
            QLabel#valorMetricaPago {{
                color: #ffffff;
                font-size: 13px;
                font-weight: 700;
            }}
            QLineEdit,
            QComboBox,
            QSpinBox {{
                background-color: {paleta["fondo_input"]};
                border: 1px solid {paleta["borde_medio"]};
                border-radius: 12px;
                color: {paleta["texto_input"]};
                min-height: 36px;
                padding: 0 10px;
            }}
            QLineEdit:focus,
            QComboBox:focus,
            QSpinBox:focus {{
                background-color: {paleta["fondo_input_focus"]};
                border-color: {paleta["borde_principal"]};
            }}
            QTableWidget#tablaCasasPagoMensual,
            QTableWidget#tablaCargosPagoMensual {{
                background-color: {paleta["fondo_superficie_muy_suave"]};
                alternate-background-color: {paleta["fondo_superficie_suave"]};
                border: 1px solid {paleta["borde_suave"]};
                border-radius: 14px;
                color: {paleta["texto_principal"]};
                gridline-color: transparent;
            }}
            QTableWidget#tablaCasasPagoMensual QTableCornerButton::section,
            QTableWidget#tablaCargosPagoMensual QTableCornerButton::section {{
                background-color: {paleta["fondo_tabla_header"]};
                border: none;
            }}
            QTableWidget#tablaCasasPagoMensual::item,
            QTableWidget#tablaCargosPagoMensual::item {{
                padding: 9px 12px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.04);
            }}
            QHeaderView::section {{
                background-color: {paleta["fondo_tabla_header"]};
                border: 0;
                color: #ffffff;
                font-weight: 800;
                padding: 8px;
            }}
            QTableWidget::item:selected {{
                background-color: rgba(45, 212, 191, 0.24);
                color: #ffffff;
            }}
            QScrollArea {{
                background: transparent;
                border: none;
            }}
            QScrollArea > QWidget > QWidget {{
                background: transparent;
            }}
            QScrollBar:vertical {{
                background: rgba(255, 255, 255, 0.06);
                width: 10px;
                border-radius: 5px;
                margin: 2px;
            }}
            QScrollBar::handle:vertical {{
                background: rgba(210, 244, 242, 0.42);
                border-radius: 5px;
                min-height: 28px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: rgba(210, 244, 242, 0.62);
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical,
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {{
                background: transparent;
                border: none;
                height: 0px;
            }}
            QTextBrowser#visorResumenPago {{
                background-color: {paleta["fondo_superficie_muy_suave"]};
                border: 1px solid {paleta["borde_suave"]};
                border-radius: 14px;
                color: {paleta["texto_principal"]};
                padding: 12px;
            }}
            """
        )


class VistaPagos(QWidget):
    """Pantalla operativa de pagos con flujo mensual guiado."""

    buscar_solicitado = Signal(str)
    casa_mensual_solicitada = Signal(int)
    previsualizacion_pago_solicitada = Signal(object)
    registrar_pago_solicitado = Signal(object)
    comprobante_solicitado = Signal(int)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("vistaPagos")
        self._paleta = obtener_paleta_tema(TEMA_SICAP_PREDETERMINADO)
        self._construir_interfaz()
        self._aplicar_estilos()

    def _construir_interfaz(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 14, 20, 18)
        layout.setSpacing(12)

        self.label_mensaje = QLabel("")
        self.label_mensaje.setObjectName("mensajeModulo")
        self.label_mensaje.setVisible(False)

        self._tabs = QTabWidget()
        self._tabs.setObjectName("tabsPagos")

        self._flujo_mensual = FlujoPagoMensual()
        self._flujo_mensual.buscar_solicitado.connect(self.buscar_solicitado)
        self._flujo_mensual.casa_solicitada.connect(self.casa_mensual_solicitada)
        self._flujo_mensual.preparar_resumen_solicitado.connect(self.previsualizacion_pago_solicitada)
        self._flujo_mensual.registrar_pago_solicitado.connect(self.registrar_pago_solicitado)
        self._flujo_mensual.estado_visual_cambiado.connect(self._actualizar_tinte_tab_mensual)

        self._tabs.addTab(self._flujo_mensual, "Pago mensual")
        self._tabs.addTab(
            FlujoPestanaPendiente(
                "tabReconexionPendiente",
                "Reconexión",
                "El flujo guiado de reconexión se implementará por pasos en una fase posterior.",
            ),
            "Reconexión",
        )
        self._tabs.addTab(
            FlujoPestanaPendiente(
                "tabConexionPendiente",
                "Conexión",
                "El flujo guiado de conexión se implementará por pasos en una fase posterior.",
            ),
            "Conexión",
        )
        self._tabs.addTab(
            FlujoPestanaPendiente(
                "tabCuotaPlanPendiente",
                "Cuota plan",
                "El flujo guiado de cuota de plan se implementará por pasos en una fase posterior.",
            ),
            "Cuota plan",
        )

        layout.addWidget(self.label_mensaje)
        layout.addWidget(self._tabs, 1)
        self._tabs.currentChanged.connect(lambda _indice: self._actualizar_tinte_tab_mensual())

    def mostrar_estado(
        self,
        estado: EstadoModuloPagos,
        formatear_moneda: Callable[[int], str],
        formatear_fecha: Callable[[str], str],
        mostrar_casas: bool = False,
    ) -> None:
        self._flujo_mensual.mostrar_estado(
            estado,
            formatear_moneda,
            formatear_fecha,
            mostrar_casas=mostrar_casas,
        )

    def mostrar_cargos_mensuales(
        self,
        casa_id: int,
        cargos: tuple[CargoPago, ...],
        diagnostico: DiagnosticoPagoMensual | None = None,
    ) -> None:
        self._flujo_mensual.mostrar_cargos_mensuales(casa_id, cargos, diagnostico)

    def mostrar_previsualizacion_pago(
        self,
        resumen: ResumenConfirmacionPago | None,
        resultado: ResultadoPago | None,
        formatear_moneda: Callable[[int], str] | None = None,
    ) -> None:
        self._flujo_mensual.mostrar_previsualizacion_pago(resumen, resultado, formatear_moneda)

    def obtener_casa_seleccionada_id(self) -> int | None:
        return self._flujo_mensual.obtener_casa_seleccionada_id()

    def reiniciar_flujo_mensual(self) -> None:
        self._flujo_mensual.reiniciar_flujo()

    def confirmar_pago(
        self,
        resumen: ResumenConfirmacionPago,
        formatear_moneda: Callable[[int], str],
    ) -> bool:
        conceptos = ", ".join(detalle.periodo_nombre for detalle in resumen.detalles[:5])
        if len(resumen.detalles) > 5:
            conceptos = f"{conceptos} y {len(resumen.detalles) - 5} más"
        detalles = (
            ("Casa", resumen.casa.casa_codigo),
            ("Abonado", resumen.casa.abonado_nombre),
            ("Operación", self._etiqueta_tipo_pago(resumen.tipo_pago)),
            ("Conceptos", conceptos or "Sin conceptos"),
            ("Método", resumen.metodo_pago.nombre),
            ("Referencia", resumen.referencia or "No aplica"),
            ("Saldo anterior", formatear_moneda(resumen.saldo_anterior_centavos)),
            ("Total a cobrar", formatear_moneda(resumen.total_pago_centavos)),
            ("Saldo posterior", formatear_moneda(resumen.saldo_posterior_centavos)),
            ("Aviso", "Después de confirmar, el pago no podrá anularse dentro del flujo normal del prototipo."),
        )
        dialogo = DialogoConfirmacionSicap(
            titulo="Confirmar pago mensual",
            descripcion=(
                "Revisa el resumen antes de guardar. El comprobante usará un correlativo único y no mezclará otros tipos de pago."
            ),
            detalles=detalles,
            texto_confirmar="Guardar pago",
            variante_confirmar="destructivo",
            parent=self,
        )
        return dialogo.exec() == QDialog.DialogCode.Accepted

    def mostrar_comprobante(
        self,
        ruta_documento: str,
    ) -> None:
        nombre_archivo = Path(ruta_documento).name
        self.mostrar_mensaje(
            f"Comprobante PDF generado correctamente: {nombre_archivo}",
            es_error=False,
        )

    def mostrar_mensaje(self, mensaje: str, es_error: bool = False) -> None:
        self.label_mensaje.setText(mensaje)
        self.label_mensaje.setProperty("estado", "error" if es_error else "exito")
        self.label_mensaje.style().unpolish(self.label_mensaje)
        self.label_mensaje.style().polish(self.label_mensaje)
        self.label_mensaje.setVisible(True)
        QTimer.singleShot(6500, self.label_mensaje.hide)

    def _actualizar_tinte_tab_mensual(self, estado_visual: str | None = None) -> None:
        estado = estado_visual if isinstance(estado_visual, str) else ""
        if self._tabs.currentIndex() != 0:
            estado = ""
        self._tabs.setProperty("estadoMensual", estado)
        self._tabs.style().unpolish(self._tabs)
        self._tabs.style().polish(self._tabs)

    @staticmethod
    def _etiqueta_tipo_pago(tipo_pago: str) -> str:
        etiquetas = {
            TIPO_PAGO_MENSUALIDAD: "Mensualidad",
            TIPO_PAGO_PLAN: "Plan",
            TIPO_PAGO_CONEXION: "Conexión",
            TIPO_PAGO_RECONEXION: "Reconexión",
        }
        return etiquetas.get(tipo_pago, tipo_pago)

    def _aplicar_estilos(self) -> None:
        paleta = self._paleta
        self.setStyleSheet(
            f"""
            QWidget#vistaPagos {{
                background-color: {paleta["fondo_principal"]};
                color: {paleta["texto_principal"]};
            }}
            QLabel#mensajeModulo {{
                border-radius: 12px;
                padding: 10px 12px;
                font-weight: 700;
            }}
            QLabel#mensajeModulo[estado="exito"] {{
                background-color: {paleta["fondo_exito"]};
                color: {paleta["texto_exito"]};
                border: 1px solid {paleta["borde_exito"]};
            }}
            QLabel#mensajeModulo[estado="error"] {{
                background-color: {paleta["fondo_error"]};
                color: {paleta["texto_error"]};
                border: 1px solid {paleta["borde_error"]};
            }}
            QTabWidget#tabsPagos::pane {{
                border: 1px solid {paleta["borde_suave"]};
                border-radius: 18px;
                background-color: rgba(34, 32, 84, 0.42);
                top: -1px;
            }}
            QTabWidget#tabsPagos QWidget {{
                background: transparent;
            }}
            QTabWidget#tabsPagos QTabBar::tab {{
                background-color: rgba(75, 73, 142, 0.78);
                border: 1px solid {paleta["borde_suave"]};
                border-bottom: 0;
                border-top-left-radius: 14px;
                border-top-right-radius: 14px;
                color: {paleta["texto_secundario"]};
                font-size: 12px;
                font-weight: 800;
                min-width: 124px;
                padding: 9px 12px;
                margin-right: 8px;
            }}
            QTabWidget#tabsPagos QTabBar::tab:selected {{
                background-color: {paleta["fondo_superficie_suave"]};
                color: #ffffff;
            }}
            QTabWidget#tabsPagos[estadoMensual="OK"] QTabBar::tab:selected {{
                background-color: rgba(16, 120, 98, 0.30);
                border-color: {paleta["borde_exito"]};
                color: {paleta["texto_exito"]};
            }}
            QTabWidget#tabsPagos[estadoMensual="BLOQUEADO"] QTabBar::tab:selected {{
                background-color: rgba(180, 35, 24, 0.24);
                border-color: {paleta["borde_error"]};
                color: {paleta["texto_error"]};
            }}
            QTabWidget#tabsPagos QTabBar::tab:hover {{
                color: #ffffff;
                border-color: {paleta["borde_principal"]};
            }}
            """
        )
