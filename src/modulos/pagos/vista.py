"""Vista PySide6 del modulo de pagos."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QTextDocument
from PySide6.QtPrintSupport import QPrintDialog, QPrinter
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QFrame,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTextBrowser,
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
from comun.ui.temas import TEMA_SICAP_PREDETERMINADO, obtener_paleta_tema
from modulos.pagos.entidades import (
    CasaPago,
    ComprobantePago,
    EstadoModuloPagos,
    FormularioPago,
    MetodoPago,
    ResumenConfirmacionPago,
    TIPO_PAGO_CONEXION,
    TIPO_PAGO_MENSUALIDAD,
    TIPO_PAGO_PLAN,
    TIPO_PAGO_RECONEXION,
)


class DialogoVistaDocumentoComprobante(DialogoBaseSicap):
    """Previsualizacion ampliada del comprobante."""

    def __init__(self, titulo: str, html: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumWidth(760)
        self.setMinimumHeight(720)

        encabezado = QLabel(titulo)
        encabezado.setObjectName("tituloDialogoSicap")
        descripcion = QLabel("Vista ampliada lista para revisar antes de imprimir o exportar.")
        descripcion.setObjectName("descripcionDialogoSicap")
        descripcion.setWordWrap(True)

        visor = QTextBrowser()
        visor.setObjectName("visorComprobantePago")
        visor.setHtml(html)
        visor.setOpenExternalLinks(False)

        fila_acciones = QHBoxLayout()
        boton_cerrar = BotonAccionContextual(
            "Cerrar",
            variante="neutro",
            centrado=True,
            mostrar_icono=False,
        )
        boton_cerrar.clicked.connect(self.accept)
        fila_acciones.addStretch(1)
        fila_acciones.addWidget(boton_cerrar)

        self.layout_cabecera.addWidget(encabezado)
        self.layout_cabecera.addWidget(descripcion)
        self.layout_cuerpo.addWidget(visor)
        self.layout_pie.addLayout(fila_acciones)


class DialogoComprobantePago(DialogoBaseSicap):
    """Dialogo compacto del comprobante con acciones operativas reales."""

    def __init__(
        self,
        comprobante: ComprobantePago,
        html: str,
        texto: str,
        ruta_sugerida: str,
        exportador: Callable[[str], str],
        formatear_moneda: Callable[[int], str],
        formatear_fecha: Callable[[str], str],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._comprobante = comprobante
        self._html = html
        self._texto = texto
        self._ruta_sugerida = ruta_sugerida
        self._exportador = exportador
        self._formatear_moneda = formatear_moneda
        self._formatear_fecha = formatear_fecha
        self._mensaje = QLabel("")
        self._mensaje.setObjectName("mensajeComprobantePago")
        self._mensaje.setVisible(False)
        self.setMinimumWidth(560)
        self._construir_ui()

    def _construir_ui(self) -> None:
        titulo = QLabel("Comprobante generado")
        titulo.setObjectName("tituloDialogoSicap")
        descripcion = QLabel("El pago quedo registrado y ya puedes revisar, imprimir o exportar el comprobante.")
        descripcion.setObjectName("descripcionDialogoSicap")
        descripcion.setWordWrap(True)

        datos = (
            ("Recibo", self._comprobante.numero_comprobante),
            ("Tipo", VistaPagos._etiqueta_tipo_pago(self._comprobante.tipo_comprobante)),
            ("Casa", self._comprobante.casa_codigo),
            ("Abonado", self._comprobante.abonado_nombre),
            ("Metodo", self._comprobante.metodo_pago),
            ("Referencia", self._comprobante.referencia or "No aplica"),
            ("Detalle", "\n".join(self._comprobante.detalles) or "Sin detalle registrado."),
            ("Total pagado", self._formatear_moneda(self._comprobante.total_pagado_centavos)),
            ("Saldo posterior", self._formatear_moneda(self._comprobante.saldo_posterior_centavos)),
            ("Fecha", self._formatear_fecha(self._comprobante.generado_en)),
        )
        panel = QFrame()
        panel.setObjectName("panelComprobantePago")
        layout_panel = QVBoxLayout(panel)
        layout_panel.setContentsMargins(16, 16, 16, 16)
        layout_panel.setSpacing(10)
        for etiqueta, valor in datos:
            fila = QHBoxLayout()
            fila.setSpacing(10)
            label = QLabel(etiqueta)
            label.setObjectName("etiquetaComprobantePago")
            contenido = QLabel(valor)
            contenido.setObjectName("valorComprobantePago")
            contenido.setWordWrap(True)
            fila.addWidget(label, 1)
            fila.addWidget(contenido, 2)
            layout_panel.addLayout(fila)

        fila_acciones = QHBoxLayout()
        fila_acciones.setSpacing(10)
        boton_ver = BotonAccionContextual("Ver", variante="neutro", centrado=True, mostrar_icono=False)
        boton_imprimir = BotonAccionContextual("Imprimir", variante="edicion", centrado=True, mostrar_icono=False)
        boton_exportar = BotonAccionContextual("Exportar", variante="primario", centrado=True, mostrar_icono=False)
        boton_ver.clicked.connect(self._ver)
        boton_imprimir.clicked.connect(self._imprimir)
        boton_exportar.clicked.connect(self._exportar)
        fila_acciones.addWidget(boton_ver)
        fila_acciones.addWidget(boton_imprimir)
        fila_acciones.addStretch(1)
        fila_acciones.addWidget(boton_exportar)

        self.layout_cabecera.addWidget(titulo)
        self.layout_cabecera.addWidget(descripcion)
        self.layout_cuerpo.addWidget(panel)
        self.layout_cuerpo.addWidget(self._mensaje)
        self.layout_pie.addLayout(fila_acciones)
        self._aplicar_estilos_comprobante()

    def _ver(self) -> None:
        dialogo = DialogoVistaDocumentoComprobante(
            titulo=self._comprobante.numero_comprobante,
            html=self._html,
            parent=self,
        )
        dialogo.exec()

    def _imprimir(self) -> None:
        impresora = QPrinter(QPrinter.PrinterMode.HighResolution)
        dialogo = QPrintDialog(impresora, self)
        if dialogo.exec() != QDialog.DialogCode.Accepted:
            return
        documento = QTextDocument()
        documento.setHtml(self._html)
        documento.print_(impresora)
        self._mostrar_mensaje("Se envio el comprobante al dialogo de impresion.", es_error=False)

    def _exportar(self) -> None:
        ruta, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar comprobante",
            self._ruta_sugerida,
            "HTML (*.html);;Texto (*.txt)",
        )
        if not ruta:
            return
        try:
            ruta_guardada = self._exportador(ruta)
        except OSError as error:
            self._mostrar_mensaje(f"No fue posible exportar el comprobante. {error}", es_error=True)
            return
        self._mostrar_mensaje(f"Comprobante exportado en {ruta_guardada}.", es_error=False)

    def _mostrar_mensaje(self, mensaje: str, es_error: bool) -> None:
        self._mensaje.setText(mensaje)
        self._mensaje.setProperty("error", es_error)
        self._mensaje.style().unpolish(self._mensaje)
        self._mensaje.style().polish(self._mensaje)
        self._mensaje.setVisible(True)

    def _aplicar_estilos_comprobante(self) -> None:
        paleta = obtener_paleta_tema(TEMA_SICAP_PREDETERMINADO)
        self.setStyleSheet(
            self.styleSheet()
            + f"""
            QFrame#panelComprobantePago {{
                background-color: {paleta["fondo_superficie_suave"]};
                border: 1px solid {paleta["borde_suave"]};
                border-radius: 16px;
            }}
            QLabel#etiquetaComprobantePago {{
                color: {paleta["texto_secundario"]};
                font-size: 11px;
                font-weight: 700;
            }}
            QLabel#valorComprobantePago {{
                color: #ffffff;
                font-size: 13px;
                font-weight: 700;
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
            QTextBrowser#visorComprobantePago {{
                background-color: {paleta["fondo_superficie_muy_suave"]};
                border: 1px solid {paleta["borde_suave"]};
                border-radius: 14px;
                color: {paleta["texto_principal"]};
                padding: 12px;
            }}
            """
        )


class VistaPagos(QWidget):
    """Pantalla operativa para registrar mensualidades y adelantos."""

    buscar_solicitado = Signal(str)
    registrar_pago_solicitado = Signal(object)
    comprobante_solicitado = Signal(int)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("vistaPagos")
        self._paleta = obtener_paleta_tema(TEMA_SICAP_PREDETERMINADO)
        self._casas: tuple[CasaPago, ...] = ()
        self._metodos: tuple[MetodoPago, ...] = ()
        self._casa_seleccionada: CasaPago | None = None
        self._formatear_moneda: Callable[[int], str] = lambda valor: f"L {valor / 100:,.2f}"
        self._formatear_fecha: Callable[[str], str] = lambda valor: valor
        self._construir_interfaz()
        self._aplicar_estilos()

    def mostrar_estado(
        self,
        estado: EstadoModuloPagos,
        formatear_moneda: Callable[[int], str],
        formatear_fecha: Callable[[str], str],
    ) -> None:
        """Renderiza casas, metodos e historial del modulo."""
        self._casas = estado.casas
        self._metodos = estado.metodos_pago
        self._formatear_moneda = formatear_moneda
        self._formatear_fecha = formatear_fecha
        casa_id_previa = self._casa_seleccionada.casa_id if self._casa_seleccionada else None
        self._llenar_metodos()
        self._llenar_casas()
        self._llenar_historial(estado)
        self._restaurar_o_seleccionar_casa(casa_id_previa)
        self._actualizar_resumen()

    def confirmar_pago(
        self,
        resumen: ResumenConfirmacionPago,
        formatear_moneda: Callable[[int], str],
    ) -> bool:
        """Solicita confirmacion explicita antes de persistir un pago."""
        conceptos = ", ".join(detalle.periodo_nombre for detalle in resumen.detalles[:5])
        if len(resumen.detalles) > 5:
            conceptos = f"{conceptos} y {len(resumen.detalles) - 5} mas"
        detalles = (
            ("Casa", resumen.casa.casa_codigo),
            ("Abonado", resumen.casa.abonado_nombre),
            ("Operacion", self._etiqueta_tipo_pago(resumen.tipo_pago)),
            ("Conceptos", conceptos or "Sin conceptos"),
            ("Metodo", resumen.metodo_pago.nombre),
            ("Referencia", resumen.referencia or "No aplica"),
            ("Saldo anterior", formatear_moneda(resumen.saldo_anterior_centavos)),
            ("Total a cobrar", formatear_moneda(resumen.total_pago_centavos)),
            ("Saldo posterior", formatear_moneda(resumen.saldo_posterior_centavos)),
            ("Aviso", "El prototipo no expone anulacion normal de pagos."),
        )
        dialogo = DialogoConfirmacionSicap(
            titulo="Confirmar pago definitivo",
            descripcion=(
                "Revisa el resumen antes de guardar. El comprobante tendra un "
                "correlativo unico y no mezclara otros tipos de pago."
            ),
            detalles=detalles,
            texto_confirmar="Guardar pago",
            variante_confirmar="destructivo",
            parent=self,
        )
        return dialogo.exec() == QDialog.DialogCode.Accepted

    def mostrar_mensaje(self, mensaje: str, es_error: bool = False) -> None:
        self.label_mensaje.setText(mensaje)
        self.label_mensaje.setProperty("estado", "error" if es_error else "exito")
        self.label_mensaje.style().unpolish(self.label_mensaje)
        self.label_mensaje.style().polish(self.label_mensaje)
        self.label_mensaje.setVisible(True)
        QTimer.singleShot(6500, self.label_mensaje.hide)

    def mostrar_comprobante(
        self,
        comprobante: ComprobantePago,
        html: str,
        texto: str,
        ruta_sugerida: str,
        exportador: Callable[[str], str],
        formatear_moneda: Callable[[int], str],
        formatear_fecha: Callable[[str], str],
    ) -> None:
        dialogo = DialogoComprobantePago(
            comprobante=comprobante,
            html=html,
            texto=texto,
            ruta_sugerida=ruta_sugerida,
            exportador=exportador,
            formatear_moneda=formatear_moneda,
            formatear_fecha=formatear_fecha,
            parent=self,
        )
        dialogo.exec()

    def _construir_interfaz(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 24, 26, 24)
        layout.setSpacing(18)

        encabezado = self._crear_encabezado()
        cuerpo = QHBoxLayout()
        cuerpo.setSpacing(16)
        cuerpo.addWidget(self._crear_panel_busqueda(), 5)
        cuerpo.addWidget(self._crear_panel_operacion(), 4)
        cuerpo.addWidget(self._crear_panel_resumen(), 3)

        self.tabla_historial = QTableWidget()
        configurar_tabla_operativa(
            self.tabla_historial,
            ["Recibo", "Tipo", "Casa", "Abonado", "Metodo", "Total", "Fecha"],
        )
        self.tabla_historial.setObjectName("tablaPagos")
        self.tabla_historial.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.tabla_historial.cellDoubleClicked.connect(self._emitir_comprobante_desde_historial)

        layout.addLayout(encabezado)
        layout.addLayout(cuerpo, 1)
        layout.addWidget(QLabel("Historial reciente de comprobantes"))
        layout.addWidget(self.tabla_historial, 1)

    def _crear_encabezado(self) -> QHBoxLayout:
        encabezado = QHBoxLayout()
        bloque_titulo = QVBoxLayout()
        descripcion = QLabel(
            "Cobra mensualidades desde la deuda mas antigua, genera recibo unico y evita pagos mixtos."
        )
        descripcion.setObjectName("descripcionModulo")
        descripcion.setWordWrap(True)
        self.label_mensaje = QLabel("")
        self.label_mensaje.setObjectName("mensajeModulo")
        self.label_mensaje.setVisible(False)
        bloque_titulo.addWidget(descripcion)
        bloque_titulo.addWidget(self.label_mensaje)
        encabezado.addLayout(bloque_titulo, 1)
        return encabezado

    def _crear_panel_busqueda(self) -> QFrame:
        panel = self._crear_panel("panelBusquedaPagos")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        titulo = QLabel("1. Buscar abonado o casa")
        titulo.setObjectName("tituloPanel")
        self.input_busqueda = QLineEdit()
        self.input_busqueda.setPlaceholderText("DNI, nombre, codigo de casa o barrio")
        self.input_busqueda.returnPressed.connect(self._emitir_busqueda)
        boton_buscar = crear_boton_operativo("Buscar")
        boton_buscar.clicked.connect(self._emitir_busqueda)

        fila_busqueda = QHBoxLayout()
        fila_busqueda.addWidget(self.input_busqueda, 1)
        fila_busqueda.addWidget(boton_buscar)

        self.tabla_casas = QTableWidget()
        configurar_tabla_operativa(
            self.tabla_casas,
            ["Casa", "Abonado", "Estado", "Vencidos", "Deuda"],
        )
        self.tabla_casas.setObjectName("tablaPagos")
        self.tabla_casas.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabla_casas.cellClicked.connect(self._seleccionar_casa)
        self.tabla_casas.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )

        layout.addWidget(titulo)
        layout.addLayout(fila_busqueda)
        layout.addWidget(self.tabla_casas, 1)
        return panel

    def _crear_panel_operacion(self) -> QFrame:
        panel = self._crear_panel("panelOperacionPagos")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        titulo = QLabel("2. Operacion de pago")
        titulo.setObjectName("tituloPanel")
        self.combo_tipo_pago = QComboBox()
        self.combo_tipo_pago.addItem("Mensualidad", TIPO_PAGO_MENSUALIDAD)
        self.combo_tipo_pago.addItem("Plan de pago (fase 6)", TIPO_PAGO_PLAN)
        self.combo_tipo_pago.addItem("Conexion (fase 6)", TIPO_PAGO_CONEXION)
        self.combo_tipo_pago.addItem("Reconexion (fase 6)", TIPO_PAGO_RECONEXION)
        self.combo_tipo_pago.currentIndexChanged.connect(self._actualizar_aviso_operacion)

        self.input_cantidad_meses = QSpinBox()
        self.input_cantidad_meses.setRange(1, 36)
        self.input_cantidad_meses.setValue(1)
        self.input_cantidad_meses.setSuffix(" mes(es)")
        self.combo_metodo_pago = QComboBox()
        self.input_referencia = QLineEdit()
        self.input_referencia.setPlaceholderText("Referencia de transferencia/deposito")
        self.input_observaciones = QLineEdit()
        self.input_observaciones.setPlaceholderText("Observaciones internas opcionales")
        self.label_aviso_operacion = QLabel("")
        self.label_aviso_operacion.setObjectName("avisoOperacion")
        self.label_aviso_operacion.setWordWrap(True)
        self.boton_registrar = crear_boton_operativo("Preparar pago", principal=True)
        self.boton_registrar.clicked.connect(self._emitir_registro)

        layout.addWidget(titulo)
        layout.addWidget(self._crear_label_campo("Tipo de operacion"))
        layout.addWidget(self.combo_tipo_pago)
        layout.addWidget(self._crear_label_campo("Cantidad a cubrir"))
        layout.addWidget(self.input_cantidad_meses)
        layout.addWidget(self._crear_label_campo("Metodo de pago"))
        layout.addWidget(self.combo_metodo_pago)
        layout.addWidget(self._crear_label_campo("Referencia"))
        layout.addWidget(self.input_referencia)
        layout.addWidget(self._crear_label_campo("Observaciones"))
        layout.addWidget(self.input_observaciones)
        layout.addWidget(self.label_aviso_operacion)
        layout.addStretch(1)
        layout.addWidget(self.boton_registrar)
        self._actualizar_aviso_operacion()
        return panel

    def _crear_panel_resumen(self) -> QFrame:
        panel = self._crear_panel("panelResumenPagos")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        titulo = QLabel("3. Resumen fijo")
        titulo.setObjectName("tituloPanel")
        self.label_casa = QLabel("Sin casa seleccionada")
        self.label_casa.setObjectName("resumenCasa")
        self.label_abonado = QLabel("")
        self.label_abonado.setObjectName("resumenTexto")
        self.label_estado = QLabel("")
        self.label_estado.setObjectName("resumenBadge")

        self.resumen_valores: dict[str, QLabel] = {}
        grilla = QGridLayout()
        grilla.setHorizontalSpacing(10)
        grilla.setVerticalSpacing(8)
        for fila, etiqueta in enumerate(("Barrio", "Pendientes", "Vencidos", "Deuda total")):
            label = QLabel(etiqueta)
            label.setObjectName("resumenEtiqueta")
            valor = QLabel("-")
            valor.setObjectName("resumenValor")
            grilla.addWidget(label, fila, 0)
            grilla.addWidget(valor, fila, 1)
            self.resumen_valores[etiqueta] = valor

        ayuda = QLabel(
            "El sistema aplica meses automaticamente desde el vencimiento mas antiguo. "
            "No hay seleccion manual arbitraria de meses ni boton de anulacion."
        )
        ayuda.setObjectName("resumenAyuda")
        ayuda.setWordWrap(True)

        layout.addWidget(titulo)
        layout.addWidget(self.label_casa)
        layout.addWidget(self.label_abonado)
        layout.addWidget(self.label_estado)
        layout.addLayout(grilla)
        layout.addStretch(1)
        layout.addWidget(ayuda)
        return panel

    @staticmethod
    def _crear_panel(nombre: str) -> QFrame:
        panel = QFrame()
        panel.setObjectName(nombre)
        return panel

    @staticmethod
    def _crear_label_campo(texto: str) -> QLabel:
        label = QLabel(texto)
        label.setObjectName("labelCampo")
        return label

    def _llenar_metodos(self) -> None:
        metodo_previo = self.combo_metodo_pago.currentData()
        self.combo_metodo_pago.blockSignals(True)
        self.combo_metodo_pago.clear()
        self.combo_metodo_pago.addItem("Seleccionar metodo", None)
        for metodo in self._metodos:
            etiqueta = metodo.nombre
            if metodo.requiere_referencia:
                etiqueta = f"{etiqueta} - requiere referencia"
            self.combo_metodo_pago.addItem(etiqueta, metodo.identificador)
        if metodo_previo is not None:
            indice = self.combo_metodo_pago.findData(metodo_previo)
            if indice >= 0:
                self.combo_metodo_pago.setCurrentIndex(indice)
        self.combo_metodo_pago.blockSignals(False)

    def _llenar_casas(self) -> None:
        self.tabla_casas.setRowCount(len(self._casas))
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
                self.tabla_casas.setItem(fila, columna, item)

    def _llenar_historial(self, estado: EstadoModuloPagos) -> None:
        self.tabla_historial.setRowCount(len(estado.historial))
        for fila, pago in enumerate(estado.historial):
            valores = (
                pago.numero_comprobante,
                self._etiqueta_tipo_pago(pago.tipo_pago),
                pago.casa_codigo,
                pago.abonado_nombre,
                pago.metodo_pago,
                self._formatear_moneda(pago.total_pagado_centavos),
                self._formatear_fecha(pago.fecha_pago),
            )
            for columna, valor in enumerate(valores):
                item = crear_item_tabla(valor)
                item.setData(Qt.ItemDataRole.UserRole, pago.pago_id)
                self.tabla_historial.setItem(fila, columna, item)

    def _restaurar_o_seleccionar_casa(self, casa_id_previa: int | None) -> None:
        self._casa_seleccionada = None
        objetivo = casa_id_previa
        if objetivo is None and self._casas:
            objetivo = self._casas[0].casa_id
        if objetivo is None:
            return
        for fila, casa in enumerate(self._casas):
            if casa.casa_id == objetivo:
                self._casa_seleccionada = casa
                self.tabla_casas.selectRow(fila)
                return

    def _seleccionar_casa(self, fila: int, _columna: int = 0) -> None:
        item = self.tabla_casas.item(fila, 0)
        if item is None:
            return
        casa_id = int(item.data(Qt.ItemDataRole.UserRole))
        self._casa_seleccionada = next(
            (casa for casa in self._casas if casa.casa_id == casa_id),
            None,
        )
        self._actualizar_resumen()

    def _actualizar_resumen(self) -> None:
        casa = self._casa_seleccionada
        if casa is None:
            self.label_casa.setText("Sin casa seleccionada")
            self.label_abonado.setText("")
            self.label_estado.setText("")
            for valor in self.resumen_valores.values():
                valor.setText("-")
            return
        self.label_casa.setText(casa.casa_codigo)
        self.label_abonado.setText(f"{casa.abonado_nombre} | DNI {casa.abonado_dni}")
        self.label_estado.setText(casa.estado_servicio)
        self.resumen_valores["Barrio"].setText(casa.barrio_nombre or "Sin barrio")
        self.resumen_valores["Pendientes"].setText(str(casa.meses_pendientes))
        self.resumen_valores["Vencidos"].setText(str(casa.meses_vencidos))
        self.resumen_valores["Deuda total"].setText(
            self._formatear_moneda(casa.deuda_total_centavos)
        )

    def _emitir_busqueda(self) -> None:
        self.buscar_solicitado.emit(self.input_busqueda.text().strip())

    def _emitir_registro(self) -> None:
        tipo_pago = str(self.combo_tipo_pago.currentData() or TIPO_PAGO_MENSUALIDAD)
        casa_id = self._casa_seleccionada.casa_id if self._casa_seleccionada else None
        metodo_pago_id = self.combo_metodo_pago.currentData()
        formulario = FormularioPago(
            casa_id=casa_id,
            tipo_pago=tipo_pago,
            cantidad_meses=int(self.input_cantidad_meses.value()),
            metodo_pago_id=int(metodo_pago_id) if metodo_pago_id is not None else None,
            referencia=self.input_referencia.text(),
            observaciones=self.input_observaciones.text(),
        )
        self.registrar_pago_solicitado.emit(formulario)

    def _emitir_comprobante_desde_historial(self, fila: int, _columna: int = 0) -> None:
        item = self.tabla_historial.item(fila, 0)
        if item is None:
            return
        pago_id = int(item.data(Qt.ItemDataRole.UserRole) or 0)
        if pago_id > 0:
            self.comprobante_solicitado.emit(pago_id)

    def _actualizar_aviso_operacion(self) -> None:
        tipo_pago = str(self.combo_tipo_pago.currentData() or TIPO_PAGO_MENSUALIDAD)
        if tipo_pago == TIPO_PAGO_MENSUALIDAD:
            self.label_aviso_operacion.setText(
                "Activo: mensualidades y adelantos. Se cobra siempre desde la deuda mas antigua."
            )
            self.input_cantidad_meses.setEnabled(True)
            return
        self.label_aviso_operacion.setText(
            "Pendiente por fase: este tipo queda visible para diseno, pero el servicio lo bloquea."
        )
        self.input_cantidad_meses.setEnabled(False)

    @staticmethod
    def _etiqueta_tipo_pago(tipo_pago: str) -> str:
        etiquetas = {
            TIPO_PAGO_MENSUALIDAD: "Mensualidad",
            TIPO_PAGO_PLAN: "Plan",
            TIPO_PAGO_CONEXION: "Conexion",
            TIPO_PAGO_RECONEXION: "Reconexion",
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
            QLabel#descripcionModulo,
            QLabel#resumenTexto,
            QLabel#resumenAyuda,
            QLabel#avisoOperacion {{
                color: {paleta["texto_secundario"]};
                font-size: 12px;
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
            QFrame#panelBusquedaPagos,
            QFrame#panelOperacionPagos,
            QFrame#panelResumenPagos {{
                background-color: {paleta["fondo_superficie_suave"]};
                border: 1px solid {paleta["borde_suave"]};
                border-radius: 20px;
            }}
            QLabel#tituloPanel {{
                color: #ffffff;
                font-size: 15px;
                font-weight: 800;
            }}
            QLabel#labelCampo,
            QLabel#resumenEtiqueta {{
                color: {paleta["texto_secundario"]};
                font-size: 11px;
                font-weight: 700;
            }}
            QLabel#resumenCasa {{
                color: #ffffff;
                font-size: 24px;
                font-weight: 800;
            }}
            QLabel#resumenBadge {{
                background-color: {paleta["fondo_badge_activo"]};
                border: 1px solid {paleta["borde_exito"]};
                border-radius: 10px;
                color: {paleta["texto_exito"]};
                padding: 6px 10px;
                font-weight: 800;
            }}
            QLabel#resumenValor {{
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
            QTableWidget#tablaPagos {{
                background-color: {paleta["fondo_superficie_muy_suave"]};
                alternate-background-color: {paleta["fondo_superficie_suave"]};
                border: 1px solid {paleta["borde_suave"]};
                border-radius: 14px;
                color: {paleta["texto_principal"]};
                gridline-color: transparent;
            }}
            QHeaderView::section {{
                background-color: {paleta["fondo_tabla_header"]};
                border: 0;
                color: #ffffff;
                font-weight: 800;
                padding: 8px;
            }}
            QTableWidget::item {{
                padding: 8px;
            }}
            QTableWidget::item:selected {{
                background-color: rgba(45, 212, 191, 0.24);
                color: #ffffff;
            }}
            """
        )
