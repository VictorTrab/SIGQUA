"""Vista PySide6 del modulo de pagos."""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt, QTimer, Signal
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
    CampoMontoMonetario,
    DialogoBaseSigqua,
    DialogoConfirmacionSigqua,
    configurar_tabla_operativa,
    crear_boton_operativo,
    crear_item_tabla,
)
from comun.ui.temas import (
    TEMA_SIGQUA_PREDETERMINADO,
    obtener_fondo_header_destacado,
    obtener_paleta_tema,
    resolver_nombre_tema,
)
from modulos.pagos.entidades import (
    CargoPago,
    CasaPago,
    DiagnosticoPagoActivacion,
    DiagnosticoPagoPlan,
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


class FlujoPagoPlan(QWidget):
    """Flujo guiado para cobrar una o varias cuotas de un plan activo."""

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
        self.setObjectName("flujoPagoPlan")
        self._tema_actual = TEMA_SIGQUA_PREDETERMINADO
        self._paleta = obtener_paleta_tema(self._tema_actual)
        self._casas: tuple[CasaPago, ...] = ()
        self._metodos: tuple[MetodoPago, ...] = ()
        self._casa_seleccionada: CasaPago | None = None
        self._diagnostico_actual: DiagnosticoPagoPlan | None = None
        self._resumen_actual: ResumenConfirmacionPago | None = None
        self._mostrar_resultados_busqueda = False
        self._cuotas_seleccionadas: set[int] = set()
        self._actualizando_tabla_cuotas = False
        self._formatear_moneda: Callable[[int], str] = lambda valor: f"L {valor / 100:,.2f}"
        self._construir_ui()
        self._aplicar_estilos()
        self._actualizar_estado()

    def aplicar_tema(self, nombre_tema: str) -> None:
        self._tema_actual = (
            resolver_nombre_tema(nombre_tema)
        )
        self._paleta = obtener_paleta_tema(self._tema_actual)
        self._aplicar_estilos()

    def mostrar_estado(
        self,
        estado: EstadoModuloPagos,
        formatear_moneda: Callable[[int], str],
        mostrar_casas: bool = False,
    ) -> None:
        self._casas = estado.casas
        self._metodos = estado.metodos_pago
        self._mostrar_resultados_busqueda = mostrar_casas
        self._formatear_moneda = formatear_moneda
        self._llenar_tabla_casas()
        self._llenar_metodos()

    def mostrar_diagnostico(self, casa_id: int, diagnostico: DiagnosticoPagoPlan | None) -> None:
        if self._casa_seleccionada is None or self._casa_seleccionada.casa_id != casa_id:
            return
        self._diagnostico_actual = diagnostico
        self._preseleccionar_cuota_por_defecto()
        self._actualizar_contexto()
        self._actualizar_estado()

    def mostrar_previsualizacion_pago(
        self,
        resumen: ResumenConfirmacionPago | None,
        resultado: ResultadoPago | None,
        formatear_moneda: Callable[[int], str] | None = None,
    ) -> None:
        if resultado is not None:
            self._resumen_actual = None
            self._mostrar_mensaje_formulario(resultado.mensaje, es_error=not resultado.exito)
            self._actualizar_estado()
            return
        if resumen is None:
            return
        formateador = formatear_moneda or self._formatear_moneda
        self._resumen_actual = resumen
        self._resumen_metricas["Casa"].setText(resumen.casa.casa_codigo)
        self._resumen_metricas["Abonado"].setText(resumen.casa.abonado_nombre)
        self._resumen_metricas["Metodo"].setText(resumen.metodo_pago.nombre)
        self._resumen_metricas["Referencia"].setText(resumen.referencia or "No aplica")
        self._resumen_metricas["Saldo anterior"].setText(formateador(resumen.saldo_anterior_centavos))
        self._resumen_metricas["Total"].setText(formateador(resumen.total_pago_centavos))
        self._resumen_metricas["Saldo posterior"].setText(formateador(resumen.saldo_posterior_centavos))
        cuotas = ", ".join(detalle.periodo_nombre for detalle in resumen.detalles)
        self._label_resumen_principal.setText(
            f"Plan {self._codigo_plan_actual()} | {len(resumen.detalles)} cuota(s) seleccionada(s)"
        )
        self._label_resumen_contexto.setText(
            f"Cuotas {cuotas} · Total {formateador(resumen.total_pago_centavos)}"
        )
        detalles = "".join(
            f"<li>{detalle.descripcion} - {formateador(detalle.monto_centavos)}</li>"
            for detalle in resumen.detalles
        )
        self._visor_resumen.setHtml(f"<html><body><ul>{detalles}</ul></body></html>")
        self._mostrar_mensaje_formulario("Resumen de plan preparado correctamente.", es_error=False)
        self._ir_a_paso(self.PASO_RESUMEN)

    def obtener_casa_seleccionada_id(self) -> int | None:
        return self._casa_seleccionada.casa_id if self._casa_seleccionada is not None else None

    def reiniciar_flujo(self) -> None:
        self._casa_seleccionada = None
        self._diagnostico_actual = None
        self._resumen_actual = None
        self._mostrar_resultados_busqueda = False
        self._cuotas_seleccionadas.clear()
        self._input_busqueda.clear()
        self._input_referencia.clear()
        self._input_observaciones.clear()
        self._tabla_casas.setRowCount(0)
        self._tabla_cuotas.setRowCount(0)
        self._combo_metodo.setCurrentIndex(0)
        self._label_total_cuotas.setText("Total seleccionado: L 0.00")
        self._mostrar_mensaje_formulario("Selecciona cuotas y datos del pago para continuar.", es_error=False)
        self._label_resultados.setProperty("estado", "")
        self._label_diagnostico_mensaje.setProperty("estado", "")
        self._label_contexto_datos.setProperty("estado", "")
        self._label_resumen_contexto.setProperty("estado", "")
        self._ir_a_paso(self.PASO_BUSQUEDA)
        self._actualizar_contexto()

    def _construir_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        self._panel_progreso = QFrame()
        self._panel_progreso.setObjectName("panelProgresoPago")
        barra_layout = QVBoxLayout(self._panel_progreso)
        barra_layout.setContentsMargins(18, 16, 18, 16)
        barra_layout.setSpacing(12)

        fila_superior = QHBoxLayout()
        self._label_paso = QLabel("Paso 1 de 4")
        self._label_paso.setObjectName("breadcrumbPago")
        self._boton_reiniciar = crear_boton_operativo("Reiniciar flujo")
        self._boton_reiniciar.clicked.connect(self.reiniciar_flujo)
        fila_superior.addWidget(self._label_paso)
        fila_superior.addStretch(1)
        fila_superior.addWidget(self._boton_reiniciar)

        self._fila_pasos = QHBoxLayout()
        self._fila_pasos.setSpacing(12)
        self._chips_paso: list[QLabel] = []
        for indice, titulo in enumerate(("Buscar casa", "Diagnostico", "Cuotas y pago", "Resumen"), start=1):
            chip = QLabel(f"{indice}. {titulo}")
            chip.setObjectName("chipPasoPago")
            self._chips_paso.append(chip)
            self._fila_pasos.addWidget(chip)

        barra_layout.addLayout(fila_superior)
        barra_layout.addLayout(self._fila_pasos)

        self._stack = QStackedWidget()
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

        titulo = QLabel("Paso 1: Buscar casa con plan activo")
        titulo.setObjectName("tituloPasoPago")
        descripcion = QLabel(
            "Busca por DNI, nombre del abonado, codigo de casa o barrio. Al seleccionar una casa, el flujo valida si existe un unico plan activo cobrable."
        )
        descripcion.setObjectName("textoAyudaPasoPago")
        descripcion.setWordWrap(True)

        fila = QHBoxLayout()
        self._input_busqueda = QLineEdit()
        self._input_busqueda.setPlaceholderText("DNI, nombre, codigo de casa o barrio")
        self._input_busqueda.returnPressed.connect(self._emitir_busqueda)
        boton_buscar = crear_boton_operativo("Buscar")
        boton_buscar.clicked.connect(self._emitir_busqueda)
        fila.addWidget(self._input_busqueda, 1)
        fila.addWidget(boton_buscar)

        self._label_resultados = QLabel("Busca una casa para iniciar el cobro de cuota de plan.")
        self._label_resultados.setObjectName("textoEstadoPasoPago")
        self._label_resultados.setWordWrap(True)

        self._tabla_casas = QTableWidget(0, 5)
        configurar_tabla_operativa(
            self._tabla_casas,
            ["Casa", "Abonado", "Estado", "Plan activo", "Saldo"],
        )
        self._tabla_casas.setObjectName("tablaCasasPagoPlan")
        self._tabla_casas.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._tabla_casas.cellClicked.connect(self._seleccionar_casa)
        self._tabla_casas.setAlternatingRowColors(True)
        self._tabla_casas.setFrameShape(QFrame.Shape.NoFrame)
        self._tabla_casas.setViewportMargins(0, 0, 0, 18)
        self._tabla_casas.viewport().setObjectName("viewportTablaCasasPagoPlan")
        self._tabla_casas.viewport().setAutoFillBackground(False)
        self._tabla_casas.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        layout.addWidget(titulo)
        layout.addWidget(descripcion)
        layout.addLayout(fila)
        layout.addWidget(self._label_resultados)
        layout.addWidget(self._tabla_casas, 1)
        return pagina

    def _crear_paso_diagnostico(self) -> QWidget:
        pagina = QFrame()
        pagina.setObjectName("panelPasoPago")
        layout = QVBoxLayout(pagina)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(14)

        titulo = QLabel("Paso 2: Diagnostico del plan activo")
        titulo.setObjectName("tituloPasoPago")
        descripcion = QLabel(
            "El sistema valida si la casa tiene un unico plan activo y prepara las cuotas cobrables. Si todo esta bien, dejara una cuota preseleccionada por defecto."
        )
        descripcion.setObjectName("textoAyudaPasoPago")
        descripcion.setWordWrap(True)

        self._panel_diagnostico = QFrame()
        self._panel_diagnostico.setObjectName("panelDiagnosticoPago")
        layout_diagnostico = QVBoxLayout(self._panel_diagnostico)
        layout_diagnostico.setContentsMargins(18, 18, 18, 18)
        layout_diagnostico.setSpacing(12)

        self._label_diagnostico_titulo = QLabel("Sin casa seleccionada")
        self._label_diagnostico_titulo.setObjectName("tituloDiagnosticoPago")
        self._label_diagnostico_mensaje = QLabel("Selecciona una casa para revisar el plan.")
        self._label_diagnostico_mensaje.setObjectName("textoEstadoPasoPago")
        self._label_diagnostico_mensaje.setWordWrap(True)

        grilla = QGridLayout()
        grilla.setHorizontalSpacing(12)
        grilla.setVerticalSpacing(10)
        self._metricas_diagnostico: dict[str, QLabel] = {}
        for fila, etiqueta in enumerate(
            ("Codigo plan", "Tipo de plan", "Estado del plan", "Cuotas pendientes", "Cuotas en mora", "Saldo vivo total")
        ):
            label = QLabel(etiqueta)
            label.setObjectName("etiquetaMetricaPago")
            valor = QLabel("-")
            valor.setObjectName("valorMetricaPago")
            self._metricas_diagnostico[etiqueta] = valor
            grilla.addWidget(label, fila, 0)
            grilla.addWidget(valor, fila, 1)

        layout_diagnostico.addWidget(self._label_diagnostico_titulo)
        layout_diagnostico.addWidget(self._label_diagnostico_mensaje)
        layout_diagnostico.addLayout(grilla)

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
        layout.addLayout(fila_acciones)
        return pagina

    def _crear_paso_datos(self) -> QWidget:
        pagina = QFrame()
        pagina.setObjectName("panelPasoPago")
        layout = QVBoxLayout(pagina)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(12)

        titulo = QLabel("Paso 3: Seleccionar cuotas y datos del pago")
        titulo.setObjectName("tituloPasoPago")
        descripcion = QLabel(
            "Selecciona una o varias cuotas del mismo plan. La primera cuota cobrable ya vendra marcada por defecto y el total se recalculara automaticamente."
        )
        descripcion.setObjectName("textoAyudaPasoPago")
        descripcion.setWordWrap(True)

        self._label_contexto_datos = QLabel("Sin casa seleccionada.")
        self._label_contexto_datos.setObjectName("textoEstadoPasoPago")
        self._label_contexto_datos.setWordWrap(True)

        self._tabla_cuotas = QTableWidget(0, 5)
        configurar_tabla_operativa(
            self._tabla_cuotas,
            ["Cobrar", "Cuota", "Vencimiento", "Estado", "Saldo pendiente"],
        )
        self._tabla_cuotas.setObjectName("tablaCuotasPagoPlan")
        self._tabla_cuotas.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self._tabla_cuotas.setAlternatingRowColors(True)
        self._tabla_cuotas.setFrameShape(QFrame.Shape.NoFrame)
        self._tabla_cuotas.setViewportMargins(0, 0, 0, 18)
        self._tabla_cuotas.viewport().setObjectName("viewportTablaCuotasPagoPlan")
        self._tabla_cuotas.viewport().setAutoFillBackground(False)
        self._tabla_cuotas.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._tabla_cuotas.itemChanged.connect(self._manejar_cambio_cuota)

        self._label_total_cuotas = QLabel("Total seleccionado: L 0.00")
        self._label_total_cuotas.setObjectName("tituloDiagnosticoPago")

        formulario = QFrame()
        formulario.setObjectName("panelFormularioPago")
        layout_formulario = QVBoxLayout(formulario)
        layout_formulario.setContentsMargins(18, 18, 18, 18)
        layout_formulario.setSpacing(14)

        self._combo_metodo = QComboBox()
        self._combo_metodo.addItem("Selecciona un metodo", None)
        self._input_referencia = QLineEdit()
        self._input_referencia.setPlaceholderText("Referencia si aplica")
        self._input_observaciones = QLineEdit()
        self._input_observaciones.setPlaceholderText("Observaciones internas opcionales")
        self._mensaje_formulario = QLabel("Selecciona cuotas y completa los datos para continuar.")
        self._mensaje_formulario.setObjectName("textoEstadoPasoPago")
        self._mensaje_formulario.setWordWrap(True)

        grilla = QGridLayout()
        grilla.setHorizontalSpacing(14)
        grilla.setVerticalSpacing(10)
        grilla.addWidget(self._crear_label_campo("Metodo de pago"), 0, 0)
        grilla.addWidget(self._combo_metodo, 1, 0)
        grilla.addWidget(self._crear_label_campo("Referencia"), 2, 0)
        grilla.addWidget(self._input_referencia, 3, 0)
        grilla.addWidget(self._crear_label_campo("Observaciones"), 4, 0)
        grilla.addWidget(self._input_observaciones, 5, 0)

        layout_formulario.addLayout(grilla)
        layout_formulario.addWidget(self._mensaje_formulario)

        fila_acciones = QHBoxLayout()
        boton_anterior = crear_boton_operativo("Anterior")
        boton_anterior.clicked.connect(lambda: self._ir_a_paso(self.PASO_DIAGNOSTICO))
        self._boton_datos_siguiente = crear_boton_operativo("Siguiente", principal=True)
        self._boton_datos_siguiente.clicked.connect(self._emitir_previsualizacion)
        fila_acciones.addWidget(boton_anterior)
        fila_acciones.addStretch(1)
        fila_acciones.addWidget(self._boton_datos_siguiente)

        layout.addWidget(titulo)
        layout.addWidget(descripcion)
        layout.addWidget(self._label_contexto_datos)
        layout.addWidget(self._tabla_cuotas)
        layout.addWidget(self._label_total_cuotas)
        layout.addWidget(formulario)
        layout.addLayout(fila_acciones)
        return pagina

    def _crear_paso_resumen(self) -> QWidget:
        pagina = QFrame()
        pagina.setObjectName("panelPasoPago")
        layout = QVBoxLayout(pagina)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(12)

        titulo = QLabel("Paso 4: Revisar resumen de cuotas")
        titulo.setObjectName("tituloPasoPago")
        descripcion = QLabel(
            "Revisa las cuotas seleccionadas y el total final antes de confirmar. El comprobante se registrara como PLAN_PAGO y mantendra una linea por cuota."
        )
        descripcion.setObjectName("textoAyudaPasoPago")
        descripcion.setWordWrap(True)

        self._label_resumen_principal = QLabel("Sin resumen preparado.")
        self._label_resumen_principal.setObjectName("tituloDiagnosticoPago")
        self._label_resumen_contexto = QLabel("Completa el paso anterior para generar el resumen.")
        self._label_resumen_contexto.setObjectName("textoEstadoPasoPago")
        self._label_resumen_contexto.setWordWrap(True)

        self._resumen_metricas = {
            "Casa": QLabel("-"),
            "Abonado": QLabel("-"),
            "Metodo": QLabel("-"),
            "Referencia": QLabel("-"),
            "Saldo anterior": QLabel("-"),
            "Total": QLabel("-"),
            "Saldo posterior": QLabel("-"),
        }
        for valor in self._resumen_metricas.values():
            valor.setObjectName("valorMetricaPago")
        for etiqueta, valor in self._resumen_metricas.items():
            fila = QHBoxLayout()
            label = QLabel(etiqueta)
            label.setObjectName("etiquetaMetricaPago")
            fila.addWidget(label)
            fila.addStretch(1)
            fila.addWidget(valor)
            layout.addLayout(fila)

        self._visor_resumen = QTextBrowser()
        self._visor_resumen.setObjectName("visorResumenPago")
        self._boton_confirmar = crear_boton_operativo("Confirmar pago", principal=True)
        self._boton_confirmar.clicked.connect(self._emitir_registro)

        fila_acciones = QHBoxLayout()
        boton_anterior = crear_boton_operativo("Anterior")
        boton_anterior.clicked.connect(lambda: self._ir_a_paso(self.PASO_DATOS))
        fila_acciones.addWidget(boton_anterior)
        fila_acciones.addStretch(1)
        fila_acciones.addWidget(self._boton_confirmar)

        layout.addWidget(titulo)
        layout.addWidget(descripcion)
        layout.addWidget(self._label_resumen_principal)
        layout.addWidget(self._label_resumen_contexto)
        layout.addWidget(self._visor_resumen, 1)
        layout.addLayout(fila_acciones)
        return pagina

    def _emitir_busqueda(self) -> None:
        texto = self._input_busqueda.text().strip()
        self._mostrar_resultados_busqueda = bool(texto)
        if not texto:
            self._tabla_casas.setRowCount(0)
            self._label_resultados.setText("Busca una casa para iniciar el cobro de cuota de plan.")
        self.buscar_solicitado.emit(texto)

    def _llenar_tabla_casas(self) -> None:
        if not self._mostrar_resultados_busqueda:
            self._tabla_casas.setRowCount(0)
            self._label_resultados.setText("Busca una casa para iniciar el cobro de cuota de plan.")
            return
        self._tabla_casas.setRowCount(len(self._casas))
        for fila, casa in enumerate(self._casas):
            valores = (
                casa.casa_codigo,
                casa.abonado_nombre,
                f"{casa.estado_servicio} | {casa.estado_administrativo}",
                "Si" if casa.tiene_plan_activo else "No",
                self._formatear_moneda(casa.deuda_total_centavos),
            )
            for columna, valor in enumerate(valores):
                item = crear_item_tabla(valor)
                item.setData(Qt.ItemDataRole.UserRole, casa.casa_id)
                self._tabla_casas.setItem(fila, columna, item)
        self._label_resultados.setText(
            f"Se encontraron {len(self._casas)} casa(s) para revisar en cuota de plan."
            if self._casas
            else "No se encontraron casas con ese criterio de busqueda."
        )

    def _llenar_metodos(self) -> None:
        metodo_actual = self._combo_metodo.currentData()
        self._combo_metodo.blockSignals(True)
        self._combo_metodo.clear()
        self._combo_metodo.addItem("Selecciona un metodo", None)
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

    def _seleccionar_casa(self, fila: int, _columna: int) -> None:
        item = self._tabla_casas.item(fila, 0)
        if item is None:
            return
        casa_id = int(item.data(Qt.ItemDataRole.UserRole))
        casa = next((valor for valor in self._casas if valor.casa_id == casa_id), None)
        if casa is None:
            return
        self._casa_seleccionada = casa
        self._resumen_actual = None
        self._diagnostico_actual = None
        self._cuotas_seleccionadas.clear()
        self.casa_solicitada.emit(casa_id)
        self._ir_a_paso(self.PASO_DIAGNOSTICO)
        self._actualizar_contexto()

    def _preseleccionar_cuota_por_defecto(self) -> None:
        self._cuotas_seleccionadas.clear()
        if self._diagnostico_actual is not None and self._diagnostico_actual.cuotas_cobrables:
            self._cuotas_seleccionadas.add(self._diagnostico_actual.cuotas_cobrables[0].cuota_id)
        self._llenar_tabla_cuotas()

    def _llenar_tabla_cuotas(self) -> None:
        cuotas = self._diagnostico_actual.cuotas_cobrables if self._diagnostico_actual is not None else ()
        self._actualizando_tabla_cuotas = True
        self._tabla_cuotas.setRowCount(len(cuotas))
        for fila, cuota in enumerate(cuotas):
            item_checkbox = crear_item_tabla("")
            item_checkbox.setFlags(
                item_checkbox.flags()
                | Qt.ItemFlag.ItemIsUserCheckable
                | Qt.ItemFlag.ItemIsEnabled
            )
            item_checkbox.setData(Qt.ItemDataRole.UserRole, cuota.cuota_id)
            item_checkbox.setCheckState(
                Qt.CheckState.Checked
                if cuota.cuota_id in self._cuotas_seleccionadas
                else Qt.CheckState.Unchecked
            )
            self._tabla_cuotas.setItem(fila, 0, item_checkbox)
            self._tabla_cuotas.setItem(fila, 1, crear_item_tabla(f"Cuota {cuota.numero_cuota}"))
            self._tabla_cuotas.setItem(fila, 2, crear_item_tabla(cuota.fecha_vencimiento))
            self._tabla_cuotas.setItem(fila, 3, crear_item_tabla(cuota.estado))
            self._tabla_cuotas.setItem(
                fila,
                4,
                crear_item_tabla(self._formatear_moneda(cuota.saldo_pendiente_centavos)),
            )
        self._actualizando_tabla_cuotas = False
        self._actualizar_total_seleccionado()

    def _manejar_cambio_cuota(self, item: object) -> None:
        if self._actualizando_tabla_cuotas or item is None or item.column() != 0:
            return
        cuota_id = item.data(Qt.ItemDataRole.UserRole)
        if cuota_id is None:
            return
        cuota_id = int(cuota_id)
        if item.checkState() == Qt.CheckState.Checked:
            self._cuotas_seleccionadas.add(cuota_id)
        else:
            self._cuotas_seleccionadas.discard(cuota_id)
        self._actualizar_total_seleccionado()
        self._actualizar_estado()

    def _actualizar_total_seleccionado(self) -> None:
        cuotas = self._diagnostico_actual.cuotas_cobrables if self._diagnostico_actual is not None else ()
        total = sum(
            cuota.saldo_pendiente_centavos
            for cuota in cuotas
            if cuota.cuota_id in self._cuotas_seleccionadas
        )
        self._label_total_cuotas.setText(f"Total seleccionado: {self._formatear_moneda(total)}")

    def _actualizar_contexto(self) -> None:
        casa = self._casa_seleccionada
        if casa is None:
            self._label_diagnostico_titulo.setText("Sin casa seleccionada")
            self._label_diagnostico_mensaje.setText("Selecciona una casa para revisar el plan.")
            for valor in self._metricas_diagnostico.values():
                valor.setText("-")
            self._label_contexto_datos.setText("Sin casa seleccionada.")
            self._label_resumen_principal.setText("Sin resumen preparado.")
            self._label_resumen_contexto.setText("Completa el paso anterior para generar el resumen.")
            self._llenar_tabla_cuotas()
            self._aplicar_estado_visual_diagnostico(None)
            return
        self._label_diagnostico_titulo.setText(f"{casa.casa_codigo} | {casa.abonado_nombre}")
        mensaje = (
            self._diagnostico_actual.mensaje_diagnostico
            if self._diagnostico_actual is not None
            else "Esperando diagnostico del plan activo."
        )
        self._label_diagnostico_mensaje.setText(mensaje)
        if self._diagnostico_actual is not None:
            self._metricas_diagnostico["Codigo plan"].setText(self._diagnostico_actual.codigo_plan)
            self._metricas_diagnostico["Tipo de plan"].setText(self._diagnostico_actual.tipo_plan.title())
            self._metricas_diagnostico["Estado del plan"].setText(self._diagnostico_actual.estado_plan)
            self._metricas_diagnostico["Cuotas pendientes"].setText(str(self._diagnostico_actual.cuotas_pendientes))
            self._metricas_diagnostico["Cuotas en mora"].setText(str(self._diagnostico_actual.cuotas_en_mora))
            self._metricas_diagnostico["Saldo vivo total"].setText(
                self._formatear_moneda(self._diagnostico_actual.saldo_vivo_centavos)
            )
        else:
            for valor in self._metricas_diagnostico.values():
                valor.setText("-")
        self._label_contexto_datos.setText(
            f"Casa {casa.casa_codigo} · {casa.abonado_nombre} · Plan {self._codigo_plan_actual()}"
        )
        self._aplicar_estado_visual_diagnostico(self._diagnostico_actual)

    def _emitir_previsualizacion(self) -> None:
        formulario = self._construir_formulario()
        if formulario is None:
            return
        self.preparar_resumen_solicitado.emit(formulario)

    def _emitir_registro(self) -> None:
        formulario = self._construir_formulario()
        if formulario is None or self._resumen_actual is None:
            return
        self.registrar_pago_solicitado.emit(formulario)

    def _construir_formulario(self) -> FormularioPago | None:
        if self._casa_seleccionada is None or self._diagnostico_actual is None:
            self._mostrar_mensaje_formulario("Selecciona una casa con plan activo antes de continuar.", es_error=True)
            return None
        metodo_pago_id = self._combo_metodo.currentData()
        if metodo_pago_id is None:
            self._mostrar_mensaje_formulario("Selecciona un metodo de pago.", es_error=True)
            return None
        cuotas_ids = tuple(sorted(self._cuotas_seleccionadas))
        if not cuotas_ids:
            self._mostrar_mensaje_formulario("Selecciona al menos una cuota del plan.", es_error=True)
            return None
        return FormularioPago(
            casa_id=self._casa_seleccionada.casa_id,
            tipo_pago=TIPO_PAGO_PLAN,
            cantidad_meses=0,
            metodo_pago_id=int(metodo_pago_id),
            referencia=self._input_referencia.text(),
            observaciones=self._input_observaciones.text(),
            plan_pago_id=self._diagnostico_actual.plan_pago_id,
            cuotas_plan_pago_ids=cuotas_ids,
        )

    def _codigo_plan_actual(self) -> str:
        if self._diagnostico_actual is None:
            return "Sin plan"
        return self._diagnostico_actual.codigo_plan

    def _actualizar_estado(self) -> None:
        paso = self._stack.currentIndex()
        self._label_paso.setText(f"Paso {paso + 1} de 4")
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
        permite = bool(self._diagnostico_actual is not None and self._diagnostico_actual.permite_continuar)
        self._boton_diagnostico_siguiente.setEnabled(permite)
        self._boton_datos_siguiente.setEnabled(permite and bool(self._cuotas_seleccionadas))
        self._boton_confirmar.setEnabled(self._resumen_actual is not None)
        self.estado_visual_cambiado.emit(
            self._diagnostico_actual.estado_visual if self._diagnostico_actual is not None else ""
        )

    def _ir_a_paso(self, paso: int) -> None:
        self._stack.setCurrentIndex(paso)
        self._actualizar_estado()

    def _mostrar_mensaje_formulario(self, mensaje: str, es_error: bool) -> None:
        self._mensaje_formulario.setText(mensaje)
        self._mensaje_formulario.setProperty("estado", "error" if es_error else "exito")
        self._mensaje_formulario.style().unpolish(self._mensaje_formulario)
        self._mensaje_formulario.style().polish(self._mensaje_formulario)

    def _aplicar_estado_visual_diagnostico(
        self,
        diagnostico: DiagnosticoPagoPlan | None,
    ) -> None:
        estado = ""
        if diagnostico is not None:
            estado = "error" if diagnostico.estado_visual == ESTADO_VISUAL_PAGO_BLOQUEADO else "exito"
        for widget in (
            self._label_diagnostico_mensaje,
            self._label_resultados,
            self._label_contexto_datos,
            self._label_resumen_contexto,
        ):
            widget.setProperty("estado", estado)
            widget.style().unpolish(widget)
            widget.style().polish(widget)
        self._panel_diagnostico.setProperty("estadoVisual", estado)
        self._panel_diagnostico.style().unpolish(self._panel_diagnostico)
        self._panel_diagnostico.style().polish(self._panel_diagnostico)

    @staticmethod
    def _crear_label_campo(texto: str) -> QLabel:
        label = QLabel(texto)
        label.setObjectName("labelCampoPago")
        return label

    def _aplicar_estilos(self) -> None:
        paleta = self._paleta
        fondo_panel = obtener_fondo_header_destacado(self._tema_actual)
        self.setStyleSheet(
            f"""
            QWidget#flujoPagoPlan {{
                background: transparent;
                color: {paleta["texto_principal"]};
                font-family: "{paleta["familia_tipografica"]}";
            }}
            QFrame#panelProgresoPago,
            QFrame#panelPasoPago,
            QFrame#panelDiagnosticoPago,
            QFrame#panelFormularioPago {{
                background-color: {fondo_panel};
                border: 1px solid rgba(126, 167, 196, 0.48);
                border-radius: 18px;
            }}
            QLabel#breadcrumbPago,
            QLabel#textoAyudaPasoPago {{
                color: {paleta["texto_secundario"]};
                font-size: 12px;
            }}
            QLabel#chipPasoPago {{
                background-color: {paleta["fondo_chip"]};
                border: 1px solid {paleta["borde_suave"]};
                border-radius: 12px;
                color: {paleta["texto_chip"]};
                font-size: 11px;
                font-weight: 700;
                padding: 8px 12px;
            }}
            QLabel#chipPasoPago[activo="true"] {{
                background-color: {paleta["acento_seleccion"]};
                border: 1px solid {paleta["borde_principal"]};
                color: {paleta["texto_principal"]};
            }}
            QLabel#chipPasoPago[habilitado="true"] {{
                background-color: {paleta["fondo_exito"]};
                border: 1px solid {paleta["borde_exito"]};
                color: {paleta["texto_exito"]};
            }}
            QLabel#chipPasoPago[bloqueado="true"] {{
                background-color: {paleta["fondo_error"]};
                border: 1px solid {paleta["borde_error"]};
                color: {paleta["texto_error"]};
            }}
            QLabel#chipPasoPago[completado="true"] {{
                background-color: {paleta["fondo_exito"]};
                border: 1px solid {paleta["borde_exito"]};
                color: {paleta["texto_exito"]};
            }}
            QLabel#tituloPasoPago,
            QLabel#tituloDiagnosticoPago {{
                color: {paleta["texto_principal"]};
                font-size: {paleta["tamano_titulo_panel"] + 2}px;
                font-weight: {paleta["peso_titulo"]};
            }}
            QLabel#textoEstadoPasoPago {{
                background-color: {paleta["fondo_badge"]};
                border: 1px solid {paleta["borde_principal"]};
                border-radius: 12px;
                color: {paleta["texto_principal"]};
                font-size: 12px;
                padding: 10px 12px;
            }}
            QLabel#textoEstadoPasoPago[estado="error"] {{
                background-color: {paleta["fondo_error"]};
                border: 1px solid {paleta["borde_error"]};
                color: {paleta["texto_error"]};
            }}
            QLabel#textoEstadoPasoPago[estado="exito"] {{
                background-color: {paleta["fondo_exito"]};
                border: 1px solid {paleta["borde_exito"]};
                color: {paleta["texto_exito"]};
            }}
            QFrame#panelDiagnosticoPago[estadoVisual="error"] {{
                background-color: {paleta["fondo_error"]};
                border: 1px solid {paleta["borde_error"]};
            }}
            QFrame#panelDiagnosticoPago[estadoVisual="exito"] {{
                background-color: {paleta["fondo_exito"]};
                border: 1px solid {paleta["borde_exito"]};
            }}
            QLabel#etiquetaMetricaPago,
            QLabel#labelCampoPago {{
                color: {paleta["texto_secundario"]};
                font-size: 11px;
                font-weight: 700;
            }}
            QLabel#valorMetricaPago {{
                color: {paleta["texto_principal"]};
                font-size: 13px;
                font-weight: 700;
            }}
            QLineEdit,
            QComboBox {{
                background-color: {paleta["fondo_input"]};
                border: 1px solid {paleta["borde_medio"]};
                border-radius: 12px;
                color: {paleta["texto_input"]};
                min-height: 36px;
                padding: 0 10px;
            }}
            QLineEdit:focus,
            QComboBox:focus {{
                background-color: {paleta["fondo_input_focus"]};
                border-color: {paleta["borde_principal"]};
            }}
            QTableWidget#tablaCasasPagoPlan,
            QTableWidget#tablaCuotasPagoPlan {{
                background-color: {paleta["fondo_tabla_cuerpo"]};
                background-clip: padding;
                alternate-background-color: {paleta["fondo_tabla_fila_alterna"]};
                border: none;
                border-radius: 18px;
                padding: 0 0 18px 0;
                color: {paleta["texto_principal"]};
                gridline-color: transparent;
            }}
            QWidget#viewportTablaCasasPagoPlan,
            QWidget#viewportTablaCuotasPagoPlan {{
                background: transparent;
                border: none;
                border-bottom-left-radius: 18px;
                border-bottom-right-radius: 18px;
            }}
            QTableWidget#tablaCasasPagoPlan QHeaderView::section:first,
            QTableWidget#tablaCuotasPagoPlan QHeaderView::section:first {{
                border-top-left-radius: 18px;
            }}
            QTableWidget#tablaCasasPagoPlan QHeaderView::section:last,
            QTableWidget#tablaCuotasPagoPlan QHeaderView::section:last {{
                border-top-right-radius: 18px;
            }}
            QTableWidget#tablaCasasPagoPlan QTableCornerButton::section,
            QTableWidget#tablaCuotasPagoPlan QTableCornerButton::section {{
                background-color: {paleta["fondo_tabla_header_destacado"]};
                border: none;
            }}
            QTableWidget#tablaCasasPagoPlan::item,
            QTableWidget#tablaCuotasPagoPlan::item {{
                padding: 9px 12px;
                border-bottom: 1px solid {paleta["borde_tabla"]};
                background-color: {paleta["fondo_tabla_fila"]};
            }}
            QHeaderView::section {{
                background-color: {paleta["fondo_tabla_header_destacado"]};
                border: 0;
                color: {paleta["texto_input"]};
                border-right: 1px solid {paleta["borde_tabla"]};
                border-bottom: 1px solid {paleta["borde_tabla"]};
                font-weight: {paleta["peso_titulo"]};
                padding: 8px;
            }}
            QTableWidget::item:selected {{
                background-color: {paleta["fondo_tabla_seleccion"]};
                color: {paleta["texto_principal"]};
            }}
            QTextBrowser#visorResumenPago {{
                background-color: {paleta["fondo_superficie_muy_suave"]};
                border: 1px solid {paleta["borde_suave"]};
                border-radius: 14px;
                color: {paleta["texto_principal"]};
                padding: 12px;
            }}
            QScrollArea {{
                background: transparent;
                border: none;
            }}
            QScrollArea > QWidget > QWidget {{
                background: transparent;
            }}
            QScrollBar:vertical {{
                background: {paleta["fondo_superficie_muy_suave"]};
                width: 10px;
                border-radius: 5px;
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

class FlujoPagoActivacion(QWidget):
    """Flujo guiado para conexion y reconexion con estilo alineado al flujo mensual."""

    buscar_solicitado = Signal(str)
    casa_solicitada = Signal(int)
    preparar_resumen_solicitado = Signal(object)
    registrar_pago_solicitado = Signal(object)
    estado_visual_cambiado = Signal(str)

    PASO_BUSQUEDA = 0
    PASO_DIAGNOSTICO = 1
    PASO_DATOS = 2
    PASO_RESUMEN = 3

    def __init__(self, tipo_pago: str, titulo_tab: str) -> None:
        super().__init__()
        self._tipo_pago = tipo_pago
        self._titulo_tab = titulo_tab
        self.setObjectName(
            "flujoPagoConexion" if tipo_pago == TIPO_PAGO_CONEXION else "flujoPagoReconexion"
        )
        self._tema_actual = TEMA_SIGQUA_PREDETERMINADO
        self._paleta = obtener_paleta_tema(self._tema_actual)
        self._casas: tuple[CasaPago, ...] = ()
        self._metodos: tuple[MetodoPago, ...] = ()
        self._casa_seleccionada: CasaPago | None = None
        self._diagnostico_actual: DiagnosticoPagoActivacion | None = None
        self._resumen_actual: ResumenConfirmacionPago | None = None
        self._mostrar_resultados_busqueda = False
        self._cobrar_prorrateo = False
        self._formatear_moneda: Callable[[int], str] = lambda valor: f"L {valor / 100:,.2f}"
        self._construir_ui()
        self._aplicar_estilos()
        self._actualizar_estado()

    def aplicar_tema(self, nombre_tema: str) -> None:
        self._tema_actual = (
            resolver_nombre_tema(nombre_tema)
        )
        self._paleta = obtener_paleta_tema(self._tema_actual)
        self._aplicar_estilos()

    def mostrar_estado(
        self,
        estado: EstadoModuloPagos,
        formatear_moneda: Callable[[int], str],
        mostrar_casas: bool = False,
    ) -> None:
        self._casas = estado.casas
        self._metodos = estado.metodos_pago
        self._mostrar_resultados_busqueda = mostrar_casas
        self._cobrar_prorrateo = estado.cobrar_mensualidad_prorrateada_activacion
        self._formatear_moneda = formatear_moneda
        self._llenar_tabla_casas()
        self._llenar_metodos()
        self._actualizar_indicador_prorrateo()

    def mostrar_diagnostico(
        self,
        casa_id: int,
        diagnostico: DiagnosticoPagoActivacion | None,
    ) -> None:
        if self._casa_seleccionada is None or self._casa_seleccionada.casa_id != casa_id:
            return
        self._diagnostico_actual = diagnostico
        self._actualizar_contexto()
        self._actualizar_estado()

    def mostrar_previsualizacion_pago(
        self,
        resumen: ResumenConfirmacionPago | None,
        resultado: ResultadoPago | None,
        formatear_moneda: Callable[[int], str] | None = None,
    ) -> None:
        if resultado is not None:
            self._resumen_actual = None
            self._mostrar_mensaje_formulario(resultado.mensaje, es_error=not resultado.exito)
            self._actualizar_estado()
            return
        if resumen is None:
            return
        formateador = formatear_moneda or self._formatear_moneda
        self._resumen_actual = resumen
        self._resumen_metricas["Casa"].setText(resumen.casa.casa_codigo)
        self._resumen_metricas["Abonado"].setText(resumen.casa.abonado_nombre)
        self._resumen_metricas["Metodo"].setText(resumen.metodo_pago.nombre)
        self._resumen_metricas["Referencia"].setText(resumen.referencia or "No aplica")
        self._resumen_metricas["Total"].setText(formateador(resumen.total_pago_centavos))
        self._label_resumen_principal.setText(
            f"{self._etiqueta_tipo_pago(resumen.tipo_pago)} para {resumen.casa.casa_codigo}"
        )
        self._label_resumen_contexto.setText(
            f"Abonado {resumen.casa.abonado_nombre} · Metodo {resumen.metodo_pago.nombre} · Total {formateador(resumen.total_pago_centavos)}"
        )
        detalles = "".join(
            f"<li>{detalle.descripcion} - {formateador(detalle.monto_centavos)}</li>"
            for detalle in resumen.detalles
        )
        self._visor_resumen.setHtml(f"<html><body><ul>{detalles}</ul></body></html>")
        self._mostrar_mensaje_formulario("Resumen preparado correctamente.", es_error=False)
        self._ir_a_paso(self.PASO_RESUMEN)

    def obtener_casa_seleccionada_id(self) -> int | None:
        return self._casa_seleccionada.casa_id if self._casa_seleccionada is not None else None

    def reiniciar_flujo(self) -> None:
        self._casa_seleccionada = None
        self._diagnostico_actual = None
        self._resumen_actual = None
        self._mostrar_resultados_busqueda = False
        self._input_busqueda.clear()
        self._input_fecha_activacion.clear()
        self._input_referencia.clear()
        self._input_observaciones.clear()
        self._input_monto_principal.clear()
        self._tabla_casas.setRowCount(0)
        self._mostrar_mensaje_formulario("Completa los datos para calcular el cobro.", es_error=False)
        self._label_resultados.setProperty("estado", "")
        self._label_diagnostico_mensaje.setProperty("estado", "")
        self._label_contexto_datos.setProperty("estado", "")
        self._label_resumen_contexto.setProperty("estado", "")
        self._ir_a_paso(self.PASO_BUSQUEDA)
        self._actualizar_contexto()

    def _construir_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        self._panel_progreso = QFrame()
        self._panel_progreso.setObjectName("panelProgresoPago")
        barra_layout = QVBoxLayout(self._panel_progreso)
        barra_layout.setContentsMargins(18, 16, 18, 16)
        barra_layout.setSpacing(12)

        fila_superior = QHBoxLayout()
        self._label_paso = QLabel("Paso 1 de 4")
        self._label_paso.setObjectName("breadcrumbPago")
        self._boton_reiniciar = crear_boton_operativo("Reiniciar flujo")
        self._boton_reiniciar.clicked.connect(self.reiniciar_flujo)
        fila_superior.addWidget(self._label_paso)
        fila_superior.addStretch(1)
        fila_superior.addWidget(self._boton_reiniciar)

        self._fila_pasos = QHBoxLayout()
        self._fila_pasos.setSpacing(12)
        self._chips_paso: list[QLabel] = []
        for indice, titulo in enumerate(("Buscar casa", "Diagnostico", "Datos del pago", "Resumen"), start=1):
            chip = QLabel(f"{indice}. {titulo}")
            chip.setObjectName("chipPasoPago")
            self._chips_paso.append(chip)
            self._fila_pasos.addWidget(chip)

        barra_layout.addLayout(fila_superior)
        barra_layout.addLayout(self._fila_pasos)

        self._stack = QStackedWidget()
        self._stack.setObjectName("stackPagoActivacion")
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

        titulo = QLabel(f"Paso 1: Buscar casa para {self._titulo_tab.lower()}")
        titulo.setObjectName("tituloPasoPago")
        descripcion = QLabel(
            "Busca por casa, abonado o DNI. Al seleccionar una casa, el flujo revisa el diagnostico y clasifica si la activacion corresponde a conexion o reconexion."
        )
        descripcion.setObjectName("textoAyudaPasoPago")
        descripcion.setWordWrap(True)

        self._input_busqueda = QLineEdit()
        self._input_busqueda.setPlaceholderText("Busca por casa, abonado o DNI")
        self._input_busqueda.returnPressed.connect(self._emitir_busqueda)
        boton_buscar = crear_boton_operativo("Buscar")
        boton_buscar.clicked.connect(self._emitir_busqueda)
        fila = QHBoxLayout()
        fila.addWidget(self._input_busqueda, 1)
        fila.addWidget(boton_buscar)

        self._tabla_casas = QTableWidget(0, 5)
        configurar_tabla_operativa(
            self._tabla_casas,
            ["Casa", "Abonado", "Estado fisico", "Estado admin", "Antecedente"],
        )
        self._tabla_casas.setObjectName("tablaCasasPagoActivacion")
        self._tabla_casas.cellClicked.connect(self._seleccionar_casa)
        self._tabla_casas.setAlternatingRowColors(True)
        self._tabla_casas.setFrameShape(QFrame.Shape.NoFrame)
        self._tabla_casas.setViewportMargins(0, 0, 0, 18)
        self._tabla_casas.viewport().setObjectName("viewportTablaCasasPagoActivacion")
        self._tabla_casas.viewport().setAutoFillBackground(False)
        self._tabla_casas.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        self._label_resultados = QLabel("Busca una casa para iniciar el flujo de activacion.")
        self._label_resultados.setObjectName("textoEstadoPasoPago")
        self._label_resultados.setWordWrap(True)

        layout.addWidget(titulo)
        layout.addWidget(descripcion)
        layout.addLayout(fila)
        layout.addWidget(self._label_resultados)
        layout.addWidget(self._tabla_casas, 1)
        return pagina

    def _crear_paso_diagnostico(self) -> QWidget:
        pagina = QFrame()
        pagina.setObjectName("panelPasoPago")
        layout = QVBoxLayout(pagina)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(14)

        titulo = QLabel(f"Paso 2: Diagnostico para {self._titulo_tab.lower()}")
        titulo.setObjectName("tituloPasoPago")
        descripcion = QLabel(
            "Revisa estado fisico, estado administrativo, antecedente y bloqueo por plan activo antes de permitir el cobro de activacion."
        )
        descripcion.setObjectName("textoAyudaPasoPago")
        descripcion.setWordWrap(True)

        self._panel_diagnostico = QFrame()
        self._panel_diagnostico.setObjectName("panelDiagnosticoPago")
        layout_diagnostico = QVBoxLayout(self._panel_diagnostico)
        layout_diagnostico.setContentsMargins(18, 18, 18, 18)
        layout_diagnostico.setSpacing(12)

        self._label_diagnostico_titulo = QLabel("Sin casa seleccionada")
        self._label_diagnostico_titulo.setObjectName("tituloDiagnosticoPago")
        self._label_diagnostico_mensaje = QLabel("Selecciona una casa para revisar el diagnostico.")
        self._label_diagnostico_mensaje.setObjectName("textoEstadoPasoPago")
        self._label_diagnostico_mensaje.setWordWrap(True)

        grilla = QGridLayout()
        grilla.setHorizontalSpacing(12)
        grilla.setVerticalSpacing(10)
        self._metricas_diagnostico: dict[str, QLabel] = {}
        for fila, etiqueta in enumerate(
            (
                "Estado fisico",
                "Estado administrativo",
                "Antecedente",
                "Clasificacion calculada",
                "Plan activo",
            )
        ):
            label = QLabel(etiqueta)
            label.setObjectName("etiquetaMetricaPago")
            valor = QLabel("-")
            valor.setObjectName("valorMetricaPago")
            self._metricas_diagnostico[etiqueta] = valor
            grilla.addWidget(label, fila, 0)
            grilla.addWidget(valor, fila, 1)

        self._label_diagnostico_politica = QLabel("")
        self._label_diagnostico_politica.setObjectName("textoAyudaPasoPago")
        self._label_diagnostico_politica.setWordWrap(True)

        layout_diagnostico.addWidget(self._label_diagnostico_titulo)
        layout_diagnostico.addWidget(self._label_diagnostico_mensaje)
        layout_diagnostico.addLayout(grilla)
        layout_diagnostico.addWidget(self._label_diagnostico_politica)

        fila_acciones = QHBoxLayout()
        boton_anterior = crear_boton_operativo("Anterior")
        boton_anterior.clicked.connect(lambda: self._ir_a_paso(self.PASO_BUSQUEDA))
        boton_siguiente = crear_boton_operativo("Siguiente", principal=True)
        boton_siguiente.clicked.connect(lambda: self._ir_a_paso(self.PASO_DATOS))
        self._boton_diagnostico_siguiente = boton_siguiente
        fila_acciones.addWidget(boton_anterior)
        fila_acciones.addStretch(1)
        fila_acciones.addWidget(boton_siguiente)

        layout.addWidget(titulo)
        layout.addWidget(descripcion)
        layout.addWidget(self._panel_diagnostico)
        layout.addLayout(fila_acciones)
        return pagina

    def _crear_paso_datos(self) -> QWidget:
        pagina = QFrame()
        pagina.setObjectName("panelPasoPago")
        layout = QVBoxLayout(pagina)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(12)

        titulo = QLabel(f"Paso 3: Ingresar datos de {self._titulo_tab.lower()}")
        titulo.setObjectName("tituloPasoPago")
        descripcion = QLabel(
            "Captura fecha de activacion, metodo, referencia, monto principal y observaciones. El prorrateo se informa desde la configuracion global."
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

        self._input_fecha_activacion = QLineEdit()
        self._input_fecha_activacion.setPlaceholderText("YYYY-MM-DD")
        self._combo_metodo = QComboBox()
        self._combo_metodo.addItem("Selecciona un metodo", None)
        self._input_referencia = QLineEdit()
        self._input_referencia.setPlaceholderText("Referencia si aplica")
        self._input_observaciones = QLineEdit()
        self._input_observaciones.setPlaceholderText("Observaciones internas opcionales")
        self._input_monto_principal = CampoMontoMonetario()
        self._mensaje_formulario = QLabel("Completa los datos para calcular el cobro.")
        self._mensaje_formulario.setObjectName("textoEstadoPasoPago")
        self._mensaje_formulario.setWordWrap(True)
        self._label_prorrateo = QLabel("")
        self._label_prorrateo.setObjectName("textoAyudaPasoPago")
        self._label_prorrateo.setWordWrap(True)
        boton_resumen = crear_boton_operativo("Siguiente", principal=True)
        boton_resumen.clicked.connect(self._emitir_previsualizacion)

        etiqueta_monto = "Monto de conexion" if self._tipo_pago == TIPO_PAGO_CONEXION else "Monto de reconexion"
        grilla_formulario = QGridLayout()
        grilla_formulario.setHorizontalSpacing(14)
        grilla_formulario.setVerticalSpacing(10)
        grilla_formulario.addWidget(self._crear_label_campo("Fecha de activacion"), 0, 0)
        grilla_formulario.addWidget(self._crear_label_campo("Metodo de pago"), 0, 1)
        grilla_formulario.addWidget(self._input_fecha_activacion, 1, 0)
        grilla_formulario.addWidget(self._combo_metodo, 1, 1)
        grilla_formulario.addWidget(self._crear_label_campo("Referencia"), 2, 0, 1, 2)
        grilla_formulario.addWidget(self._input_referencia, 3, 0, 1, 2)
        grilla_formulario.addWidget(self._crear_label_campo(etiqueta_monto), 4, 0, 1, 2)
        grilla_formulario.addWidget(self._input_monto_principal, 5, 0, 1, 2)
        grilla_formulario.addWidget(self._crear_label_campo("Observaciones"), 6, 0, 1, 2)
        grilla_formulario.addWidget(self._input_observaciones, 7, 0, 1, 2)

        layout_formulario.addLayout(grilla_formulario)
        layout_formulario.addWidget(self._label_prorrateo)
        layout_formulario.addWidget(self._mensaje_formulario)

        fila_acciones = QHBoxLayout()
        boton_anterior = crear_boton_operativo("Anterior")
        boton_anterior.clicked.connect(lambda: self._ir_a_paso(self.PASO_DIAGNOSTICO))
        fila_acciones.addWidget(boton_anterior)
        fila_acciones.addStretch(1)
        fila_acciones.addWidget(boton_resumen)

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

        titulo = QLabel(f"Paso 4: Revisar resumen de {self._titulo_tab.lower()}")
        titulo.setObjectName("tituloPasoPago")
        descripcion = QLabel(
            "Revisa el detalle final antes de confirmar. El comprobante mantendra separados los conceptos de activacion y no se mezclara con otros tipos de cobro."
        )
        descripcion.setObjectName("textoAyudaPasoPago")
        descripcion.setWordWrap(True)

        self._label_resumen_principal = QLabel("Sin resumen preparado.")
        self._label_resumen_principal.setObjectName("tituloDiagnosticoPago")
        self._label_resumen_contexto = QLabel("Completa el paso anterior para generar el resumen.")
        self._label_resumen_contexto.setObjectName("textoEstadoPasoPago")
        self._label_resumen_contexto.setWordWrap(True)

        self._resumen_metricas = {
            "Casa": QLabel("-"),
            "Abonado": QLabel("-"),
            "Metodo": QLabel("-"),
            "Referencia": QLabel("-"),
            "Total": QLabel("-"),
        }
        for etiqueta, valor in self._resumen_metricas.items():
            valor.setObjectName("valorMetricaPago")
            fila = QHBoxLayout()
            label = QLabel(etiqueta)
            label.setObjectName("etiquetaMetricaPago")
            fila.addWidget(label)
            fila.addStretch(1)
            fila.addWidget(valor)
            layout.addLayout(fila)

        self._visor_resumen = QTextBrowser()
        self._visor_resumen.setObjectName("visorResumenPago")
        boton_confirmar = crear_boton_operativo("Confirmar pago", principal=True)
        boton_confirmar.clicked.connect(self._emitir_registro)
        self._boton_confirmar = boton_confirmar

        fila_acciones = QHBoxLayout()
        boton_anterior = crear_boton_operativo("Anterior")
        boton_anterior.clicked.connect(lambda: self._ir_a_paso(self.PASO_DATOS))
        fila_acciones.addWidget(boton_anterior)
        fila_acciones.addStretch(1)
        fila_acciones.addWidget(boton_confirmar)

        layout.addWidget(titulo)
        layout.addWidget(descripcion)
        layout.addWidget(self._label_resumen_principal)
        layout.addWidget(self._label_resumen_contexto)
        layout.addWidget(self._visor_resumen, 1)
        layout.addLayout(fila_acciones)
        return pagina

    def _emitir_busqueda(self) -> None:
        texto = self._input_busqueda.text().strip()
        self._mostrar_resultados_busqueda = bool(texto)
        if not texto:
            self._tabla_casas.setRowCount(0)
            self._label_resultados.setText("Busca una casa para iniciar el flujo de activacion.")
        self.buscar_solicitado.emit(texto)

    def _llenar_tabla_casas(self) -> None:
        if not self._mostrar_resultados_busqueda:
            self._tabla_casas.setRowCount(0)
            self._label_resultados.setText("Busca una casa para iniciar el flujo de activacion.")
            return
        self._tabla_casas.setRowCount(len(self._casas))
        for fila, casa in enumerate(self._casas):
            valores = (
                casa.casa_codigo,
                casa.abonado_nombre,
                casa.estado_servicio,
                casa.estado_administrativo,
                "Ya tuvo servicio" if casa.ha_tenido_servicio_activo else "Primera conexion",
            )
            for columna, valor in enumerate(valores):
                item = crear_item_tabla(valor)
                item.setData(Qt.ItemDataRole.UserRole, casa.casa_id)
                self._tabla_casas.setItem(fila, columna, item)
        self._label_resultados.setText(
            f"Se encontraron {len(self._casas)} casa(s) para revisar en {self._titulo_tab.lower()}."
            if self._casas
            else "No se encontraron casas con ese criterio de busqueda."
        )

    def _llenar_metodos(self) -> None:
        metodo_actual = self._combo_metodo.currentData()
        self._combo_metodo.clear()
        self._combo_metodo.addItem("Selecciona un metodo", None)
        for metodo in self._metodos:
            texto = metodo.nombre
            if metodo.requiere_referencia:
                texto = f"{texto} - requiere referencia"
            self._combo_metodo.addItem(texto, metodo.identificador)
        if metodo_actual is not None:
            indice = self._combo_metodo.findData(metodo_actual)
            if indice >= 0:
                self._combo_metodo.setCurrentIndex(indice)

    def _seleccionar_casa(self, fila: int, _columna: int) -> None:
        item = self._tabla_casas.item(fila, 0)
        if item is None:
            return
        casa_id = int(item.data(Qt.ItemDataRole.UserRole))
        casa = next((valor for valor in self._casas if valor.casa_id == casa_id), None)
        if casa is None:
            return
        self._casa_seleccionada = casa
        self._resumen_actual = None
        self._diagnostico_actual = None
        self.casa_solicitada.emit(casa_id)
        self._ir_a_paso(self.PASO_DIAGNOSTICO)
        self._actualizar_contexto()

    def _actualizar_contexto(self) -> None:
        casa = self._casa_seleccionada
        if casa is None:
            self._label_diagnostico_titulo.setText("Sin casa seleccionada")
            self._label_diagnostico_mensaje.setText("Selecciona una casa para revisar el diagnostico.")
            for valor in self._metricas_diagnostico.values():
                valor.setText("-")
            self._label_contexto_datos.setText("Sin casa seleccionada.")
            self._label_resumen_principal.setText("Sin resumen preparado.")
            self._label_resumen_contexto.setText("Completa el paso anterior para generar el resumen.")
            self._actualizar_indicador_prorrateo()
            self._aplicar_estado_visual_diagnostico(None)
            return
        clasificacion = (
            self._diagnostico_actual.clasificacion
            if self._diagnostico_actual is not None
            else (
                "RECONEXION" if casa.ha_tenido_servicio_activo else "CONEXION"
            )
        )
        self._label_diagnostico_titulo.setText(f"{casa.casa_codigo} | {casa.abonado_nombre}")
        mensaje = (
            self._diagnostico_actual.mensaje_diagnostico
            if self._diagnostico_actual is not None
            else "Esperando diagnostico del servicio."
        )
        self._label_diagnostico_mensaje.setText(mensaje)
        self._metricas_diagnostico["Estado fisico"].setText(casa.estado_servicio)
        self._metricas_diagnostico["Estado administrativo"].setText(casa.estado_administrativo)
        self._metricas_diagnostico["Antecedente"].setText(
            "Ya tuvo servicio" if casa.ha_tenido_servicio_activo else "Nunca ha tenido servicio"
        )
        self._metricas_diagnostico["Clasificacion calculada"].setText(
            self._etiqueta_tipo_pago(clasificacion)
        )
        self._metricas_diagnostico["Plan activo"].setText("Si" if casa.tiene_plan_activo else "No")
        self._label_contexto_datos.setText(
            f"Casa {casa.casa_codigo} · {casa.abonado_nombre} · Estado {casa.estado_servicio} · Clasificacion {self._etiqueta_tipo_pago(clasificacion)}"
        )
        self._actualizar_indicador_prorrateo()
        self._aplicar_estado_visual_diagnostico(self._diagnostico_actual)

    def _emitir_previsualizacion(self) -> None:
        formulario = self._construir_formulario()
        if formulario is None:
            return
        self.preparar_resumen_solicitado.emit(formulario)

    def _emitir_registro(self) -> None:
        formulario = self._construir_formulario()
        if formulario is None or self._resumen_actual is None:
            return
        self.registrar_pago_solicitado.emit(formulario)

    def _construir_formulario(self) -> FormularioPago | None:
        if self._casa_seleccionada is None:
            self._mostrar_mensaje_formulario("Selecciona una casa antes de continuar.", es_error=True)
            return None
        metodo_pago_id = self._combo_metodo.currentData()
        if metodo_pago_id is None:
            self._mostrar_mensaje_formulario("Selecciona un metodo de pago.", es_error=True)
            return None
        monto_principal = self._input_monto_principal.obtener_centavos()
        if monto_principal <= 0:
            self._mostrar_mensaje_formulario(
                "Indica un monto principal valido.",
                es_error=True,
            )
            return None
        return FormularioPago(
            casa_id=self._casa_seleccionada.casa_id,
            tipo_pago=self._tipo_pago,
            cantidad_meses=1,
            metodo_pago_id=int(metodo_pago_id),
            referencia=self._input_referencia.text(),
            observaciones=self._input_observaciones.text(),
            fecha_activacion=self._input_fecha_activacion.text().strip(),
            monto_conexion_centavos=monto_principal if self._tipo_pago == TIPO_PAGO_CONEXION else 0,
            monto_reconexion_centavos=monto_principal if self._tipo_pago == TIPO_PAGO_RECONEXION else 0,
        )

    def _actualizar_estado(self) -> None:
        self._label_paso.setText(f"Paso {self._stack.currentIndex() + 1} de 4")
        paso = self._stack.currentIndex()
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
        permite = bool(self._diagnostico_actual is not None and self._diagnostico_actual.permite_continuar)
        self._boton_diagnostico_siguiente.setEnabled(permite)
        self._boton_confirmar.setEnabled(self._resumen_actual is not None)
        self.estado_visual_cambiado.emit(
            self._diagnostico_actual.estado_visual if self._diagnostico_actual is not None else ""
        )

    def _ir_a_paso(self, paso: int) -> None:
        self._stack.setCurrentIndex(paso)
        self._actualizar_estado()

    def _actualizar_indicador_prorrateo(self) -> None:
        mensaje = (
            "La configuracion global cobrara mensualidad prorrateada en esta activacion."
            if self._cobrar_prorrateo
            else "La configuracion global no cobrara el prorrateo en caja; se generara como primer cargo pendiente."
        )
        if hasattr(self, "_label_prorrateo"):
            self._label_prorrateo.setText(mensaje)
        if hasattr(self, "_label_diagnostico_politica"):
            self._label_diagnostico_politica.setText(mensaje)

    def _mostrar_mensaje_formulario(self, mensaje: str, es_error: bool) -> None:
        self._mensaje_formulario.setText(mensaje)
        self._mensaje_formulario.setProperty("estado", "error" if es_error else "exito")
        self._mensaje_formulario.style().unpolish(self._mensaje_formulario)
        self._mensaje_formulario.style().polish(self._mensaje_formulario)

    def _aplicar_estado_visual_diagnostico(
        self,
        diagnostico: DiagnosticoPagoActivacion | None,
    ) -> None:
        estado = ""
        if diagnostico is not None:
            estado = "error" if diagnostico.estado_visual == ESTADO_VISUAL_PAGO_BLOQUEADO else "exito"
        for widget in (
            self._label_diagnostico_mensaje,
            self._label_resultados,
            self._label_contexto_datos,
            self._label_resumen_contexto,
        ):
            widget.setProperty("estado", estado)
            widget.style().unpolish(widget)
            widget.style().polish(widget)
        self._panel_diagnostico.setProperty("estadoVisual", estado)
        self._panel_diagnostico.style().unpolish(self._panel_diagnostico)
        self._panel_diagnostico.style().polish(self._panel_diagnostico)

    @staticmethod
    def _crear_label_campo(texto: str) -> QLabel:
        label = QLabel(texto)
        label.setObjectName("labelCampoPago")
        return label

    @staticmethod
    def _etiqueta_tipo_pago(tipo_pago: str) -> str:
        etiquetas = {
            TIPO_PAGO_CONEXION: "Conexion",
            TIPO_PAGO_RECONEXION: "Reconexion",
        }
        return etiquetas.get(tipo_pago, tipo_pago)

    def _aplicar_estilos(self) -> None:
        paleta = self._paleta
        fondo_panel = obtener_fondo_header_destacado(self._tema_actual)
        self.setStyleSheet(
            f"""
            QWidget#{self.objectName()} {{
                background: transparent;
                color: {paleta["texto_principal"]};
                font-family: "{paleta["familia_tipografica"]}";
            }}
            QFrame#panelProgresoPago,
            QFrame#panelPasoPago,
            QFrame#panelDiagnosticoPago,
            QFrame#panelFormularioPago {{
                background-color: {fondo_panel};
                border: 1px solid rgba(126, 167, 196, 0.48);
                border-radius: 18px;
            }}
            QLabel#breadcrumbPago,
            QLabel#textoAyudaPasoPago {{
                color: {paleta["texto_secundario"]};
                font-size: 12px;
            }}
            QLabel#chipPasoPago {{
                background-color: {paleta["fondo_chip"]};
                border: 1px solid {paleta["borde_suave"]};
                border-radius: 12px;
                color: {paleta["texto_chip"]};
                font-size: 11px;
                font-weight: 700;
                padding: 8px 12px;
            }}
            QLabel#chipPasoPago[activo="true"] {{
                background-color: {paleta["acento_seleccion"]};
                border: 1px solid {paleta["borde_principal"]};
                color: {paleta["texto_principal"]};
            }}
            QLabel#chipPasoPago[habilitado="true"] {{
                background-color: {paleta["fondo_exito"]};
                border: 1px solid {paleta["borde_exito"]};
                color: {paleta["texto_exito"]};
            }}
            QLabel#chipPasoPago[bloqueado="true"] {{
                background-color: {paleta["fondo_error"]};
                border: 1px solid {paleta["borde_error"]};
                color: {paleta["texto_error"]};
            }}
            QLabel#chipPasoPago[completado="true"] {{
                background-color: {paleta["fondo_exito"]};
                border: 1px solid {paleta["borde_exito"]};
                color: {paleta["texto_exito"]};
            }}
            QLabel#tituloPasoPago,
            QLabel#tituloDiagnosticoPago {{
                color: {paleta["texto_principal"]};
                font-size: {paleta["tamano_titulo_panel"] + 2}px;
                font-weight: {paleta["peso_titulo"]};
            }}
            QLabel#textoEstadoPasoPago {{
                background-color: {paleta["fondo_badge"]};
                border: 1px solid {paleta["borde_principal"]};
                border-radius: 12px;
                color: {paleta["texto_principal"]};
                font-size: 12px;
                padding: 10px 12px;
            }}
            QLabel#textoEstadoPasoPago[estado="error"] {{
                background-color: {paleta["fondo_error"]};
                border: 1px solid {paleta["borde_error"]};
                color: {paleta["texto_error"]};
            }}
            QLabel#textoEstadoPasoPago[estado="exito"] {{
                background-color: {paleta["fondo_exito"]};
                border: 1px solid {paleta["borde_exito"]};
                color: {paleta["texto_exito"]};
            }}
            QFrame#panelDiagnosticoPago[estadoVisual="error"] {{
                background-color: {paleta["fondo_error"]};
                border: 1px solid {paleta["borde_error"]};
            }}
            QFrame#panelDiagnosticoPago[estadoVisual="exito"] {{
                background-color: {paleta["fondo_exito"]};
                border: 1px solid {paleta["borde_exito"]};
            }}
            QLabel#etiquetaMetricaPago,
            QLabel#labelCampoPago {{
                color: {paleta["texto_secundario"]};
                font-size: 11px;
                font-weight: 700;
            }}
            QLabel#valorMetricaPago {{
                color: {paleta["texto_principal"]};
                font-size: 13px;
                font-weight: 700;
            }}
            QLineEdit,
            QComboBox {{
                background-color: {paleta["fondo_input"]};
                border: 1px solid {paleta["borde_medio"]};
                border-radius: 12px;
                color: {paleta["texto_input"]};
                min-height: 36px;
                padding: 0 10px;
            }}
            QLineEdit:focus,
            QComboBox:focus {{
                background-color: {paleta["fondo_input_focus"]};
                border-color: {paleta["borde_principal"]};
            }}
            QTableWidget#tablaCasasPagoActivacion {{
                background-color: {paleta["fondo_tabla_cuerpo"]};
                background-clip: padding;
                alternate-background-color: {paleta["fondo_tabla_fila_alterna"]};
                border: none;
                border-radius: 18px;
                padding: 0 0 18px 0;
                color: {paleta["texto_principal"]};
                gridline-color: transparent;
            }}
            QWidget#viewportTablaCasasPagoActivacion {{
                background: transparent;
                border: none;
                border-bottom-left-radius: 18px;
                border-bottom-right-radius: 18px;
            }}
            QTableWidget#tablaCasasPagoActivacion QHeaderView::section:first {{
                border-top-left-radius: 18px;
            }}
            QTableWidget#tablaCasasPagoActivacion QTableCornerButton::section {{
                background-color: {paleta["fondo_tabla_header_destacado"]};
                border: none;
            }}
            QTableWidget#tablaCasasPagoActivacion QHeaderView::section:last {{
                border-top-right-radius: 18px;
            }}
            QTableWidget#tablaCasasPagoActivacion::item {{
                padding: 9px 12px;
                border-bottom: 1px solid {paleta["borde_tabla"]};
                background-color: {paleta["fondo_tabla_fila"]};
            }}
            QHeaderView::section {{
                background-color: {paleta["fondo_tabla_header_destacado"]};
                border: 0;
                color: {paleta["texto_input"]};
                border-right: 1px solid {paleta["borde_tabla"]};
                border-bottom: 1px solid {paleta["borde_tabla"]};
                font-weight: {paleta["peso_titulo"]};
                padding: 8px;
            }}
            QTableWidget::item:selected {{
                background-color: {paleta["fondo_tabla_seleccion"]};
                color: {paleta["texto_principal"]};
            }}
            QTextBrowser#visorResumenPago {{
                background-color: {paleta["fondo_superficie_muy_suave"]};
                border: 1px solid {paleta["borde_suave"]};
                border-radius: 14px;
                color: {paleta["texto_principal"]};
                padding: 12px;
            }}
            QScrollArea {{
                background: transparent;
                border: none;
            }}
            QScrollArea > QWidget > QWidget {{
                background: transparent;
            }}
            QScrollBar:vertical {{
                background: {paleta["fondo_superficie_muy_suave"]};
                width: 10px;
                border-radius: 5px;
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
        self._tema_actual = TEMA_SIGQUA_PREDETERMINADO
        self._paleta = obtener_paleta_tema(self._tema_actual)
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

    def aplicar_tema(self, nombre_tema: str) -> None:
        self._tema_actual = (
            resolver_nombre_tema(nombre_tema)
        )
        self._paleta = obtener_paleta_tema(self._tema_actual)
        self._aplicar_estilos()

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
        self._tabla_casas.setAlternatingRowColors(True)
        self._tabla_casas.setFrameShape(QFrame.Shape.NoFrame)
        self._tabla_casas.setViewportMargins(0, 0, 0, 18)
        self._tabla_casas.viewport().setObjectName("viewportTablaCasasPagoMensual")
        self._tabla_casas.viewport().setAutoFillBackground(False)
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
        for fila, etiqueta in enumerate(
            (
                "Barrio",
                "Estado fisico",
                "Estado administrativo",
                "Meses pendientes",
                "Meses vencidos",
                "Deuda anterior",
            )
        ):
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
        self._tabla_cargos.setAlternatingRowColors(True)
        self._tabla_cargos.setFrameShape(QFrame.Shape.NoFrame)
        self._tabla_cargos.setViewportMargins(0, 0, 0, 18)
        self._tabla_cargos.viewport().setObjectName("viewportTablaCargosPagoMensual")
        self._tabla_cargos.viewport().setAutoFillBackground(False)
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
                f"{casa.estado_servicio} | {casa.estado_administrativo}",
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
        self._metricas_diagnostico["Estado fisico"].setText(casa.estado_servicio)
        self._metricas_diagnostico["Estado administrativo"].setText(casa.estado_administrativo)
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
        fondo_panel = obtener_fondo_header_destacado(self._tema_actual)
        self.setStyleSheet(
            f"""
            QWidget#flujoPagoMensual {{
                background: transparent;
                color: {paleta["texto_principal"]};
                font-family: "{paleta["familia_tipografica"]}";
            }}
            QFrame#panelProgresoPago,
            QFrame#panelPasoPago,
            QFrame#panelDiagnosticoPago,
            QFrame#panelFormularioPago {{
                background-color: {fondo_panel};
                border: 1px solid rgba(126, 167, 196, 0.48);
                border-radius: 18px;
            }}
            QLabel#breadcrumbPago,
            QLabel#textoAyudaPasoPago {{
                color: {paleta["texto_secundario"]};
                font-size: 12px;
            }}
            QLabel#chipPasoPago {{
                background-color: {paleta["fondo_chip"]};
                border: 1px solid {paleta["borde_suave"]};
                border-radius: 12px;
                color: {paleta["texto_chip"]};
                font-size: 11px;
                font-weight: 700;
                padding: 8px 12px;
            }}
            QLabel#chipPasoPago[activo="true"] {{
                background-color: {paleta["acento_seleccion"]};
                border: 1px solid {paleta["borde_principal"]};
                color: {paleta["texto_principal"]};
            }}
            QLabel#chipPasoPago[habilitado="true"] {{
                background-color: {paleta["fondo_exito"]};
                border: 1px solid {paleta["borde_exito"]};
                color: {paleta["texto_exito"]};
            }}
            QLabel#chipPasoPago[bloqueado="true"] {{
                background-color: {paleta["fondo_error"]};
                border: 1px solid {paleta["borde_error"]};
                color: {paleta["texto_error"]};
            }}
            QLabel#chipPasoPago[completado="true"] {{
                background-color: {paleta["fondo_exito"]};
                border: 1px solid {paleta["borde_exito"]};
                color: {paleta["texto_exito"]};
            }}
            QLabel#tituloPasoPago,
            QLabel#tituloDiagnosticoPago {{
                color: {paleta["texto_principal"]};
                font-size: {paleta["tamano_titulo_panel"] + 2}px;
                font-weight: {paleta["peso_titulo"]};
            }}
            QLabel#textoEstadoPasoPago {{
                background-color: {paleta["fondo_badge"]};
                border: 1px solid {paleta["borde_principal"]};
                border-radius: 12px;
                color: {paleta["texto_principal"]};
                font-size: 12px;
                padding: 10px 12px;
            }}
            QLabel#textoEstadoPasoPago[estado="error"] {{
                background-color: {paleta["fondo_error"]};
                border: 1px solid {paleta["borde_error"]};
                color: {paleta["texto_error"]};
            }}
            QLabel#textoEstadoPasoPago[estado="exito"] {{
                background-color: {paleta["fondo_exito"]};
                border: 1px solid {paleta["borde_exito"]};
                color: {paleta["texto_exito"]};
            }}
            QFrame#panelDiagnosticoPago[estadoVisual="error"] {{
                background-color: {paleta["fondo_error"]};
                border: 1px solid {paleta["borde_error"]};
            }}
            QFrame#panelDiagnosticoPago[estadoVisual="exito"] {{
                background-color: {paleta["fondo_exito"]};
                border: 1px solid {paleta["borde_exito"]};
            }}
            QLabel#etiquetaMetricaPago,
            QLabel#labelCampoPago {{
                color: {paleta["texto_secundario"]};
                font-size: 11px;
                font-weight: 700;
            }}
            QLabel#valorMetricaPago {{
                color: {paleta["texto_principal"]};
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
                background-color: {paleta["fondo_tabla_cuerpo"]};
                background-clip: padding;
                alternate-background-color: {paleta["fondo_tabla_fila_alterna"]};
                border: none;
                border-radius: 18px;
                padding: 0 0 18px 0;
                color: {paleta["texto_principal"]};
                gridline-color: transparent;
            }}
            QWidget#viewportTablaCasasPagoMensual,
            QWidget#viewportTablaCargosPagoMensual {{
                background: transparent;
                border: none;
                border-bottom-left-radius: 18px;
                border-bottom-right-radius: 18px;
            }}
            QTableWidget#tablaCasasPagoMensual QTableCornerButton::section,
            QTableWidget#tablaCargosPagoMensual QTableCornerButton::section {{
                background-color: {paleta["fondo_tabla_header_destacado"]};
                border: none;
            }}
            QTableWidget#tablaCasasPagoMensual QHeaderView::section:first,
            QTableWidget#tablaCargosPagoMensual QHeaderView::section:first {{
                border-top-left-radius: 18px;
            }}
            QTableWidget#tablaCasasPagoMensual::item,
            QTableWidget#tablaCargosPagoMensual::item {{
                padding: 9px 12px;
                border-bottom: 1px solid {paleta["borde_tabla"]};
                background-color: {paleta["fondo_tabla_fila"]};
            }}
            QTableWidget#tablaCasasPagoMensual QHeaderView::section:last,
            QTableWidget#tablaCargosPagoMensual QHeaderView::section:last {{
                border-top-right-radius: 18px;
            }}
            QHeaderView::section {{
                background-color: {paleta["fondo_tabla_header_destacado"]};
                border: 0;
                color: {paleta["texto_input"]};
                border-right: 1px solid {paleta["borde_tabla"]};
                border-bottom: 1px solid {paleta["borde_tabla"]};
                font-weight: {paleta["peso_titulo"]};
                padding: 8px;
            }}
            QTableWidget::item:selected {{
                background-color: {paleta["fondo_tabla_seleccion"]};
                color: {paleta["texto_principal"]};
            }}
            QScrollArea {{
                background: transparent;
                border: none;
            }}
            QScrollArea > QWidget > QWidget {{
                background: transparent;
            }}
            QScrollBar:vertical {{
                background: {paleta["fondo_superficie_muy_suave"]};
                width: 10px;
                border-radius: 5px;
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
    casa_conexion_solicitada = Signal(int)
    casa_reconexion_solicitada = Signal(int)
    casa_plan_solicitada = Signal(int)
    previsualizacion_pago_solicitada = Signal(object)
    previsualizacion_conexion_solicitada = Signal(object)
    previsualizacion_reconexion_solicitada = Signal(object)
    previsualizacion_plan_solicitada = Signal(object)
    registrar_pago_solicitado = Signal(object)
    registrar_pago_conexion_solicitado = Signal(object)
    registrar_pago_reconexion_solicitado = Signal(object)
    registrar_pago_plan_solicitado = Signal(object)
    comprobante_solicitado = Signal(int)
    DURACION_MENSAJE_GENERAL_MS = 6500
    DURACION_MENSAJE_COMPROBANTE_MS = 22000

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("vistaPagos")
        self._tema_actual = TEMA_SIGQUA_PREDETERMINADO
        self._paleta = obtener_paleta_tema(self._tema_actual)
        self._construir_interfaz()
        self._aplicar_estilos()

    def _construir_interfaz(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 14, 20, 18)
        layout.setSpacing(12)

        self.label_mensaje = QLabel("")
        self.label_mensaje.setObjectName("mensajeModulo")
        self.label_mensaje.setVisible(False)
        fila_estado_documental = QHBoxLayout()
        fila_estado_documental.setContentsMargins(0, 0, 0, 0)
        fila_estado_documental.setSpacing(8)
        fila_estado_documental.addStretch(1)
        self._label_estado_apertura = QLabel("ESC/POS")
        self._label_estado_apertura.setObjectName("badgeEstadoDocumentoPago")
        self._label_estado_impresion = QLabel("Pendientes")
        self._label_estado_impresion.setObjectName("badgeEstadoDocumentoPago")
        fila_estado_documental.addWidget(self._label_estado_apertura)
        fila_estado_documental.addWidget(self._label_estado_impresion)

        self._tabs = QTabWidget()
        self._tabs.setObjectName("tabsPagos")

        self._flujo_mensual = FlujoPagoMensual()
        self._flujo_mensual.buscar_solicitado.connect(self.buscar_solicitado)
        self._flujo_mensual.casa_solicitada.connect(self.casa_mensual_solicitada)
        self._flujo_mensual.preparar_resumen_solicitado.connect(self.previsualizacion_pago_solicitada)
        self._flujo_mensual.registrar_pago_solicitado.connect(self.registrar_pago_solicitado)
        self._flujo_mensual.estado_visual_cambiado.connect(self._actualizar_tinte_tab_mensual)

        self._flujo_reconexion = FlujoPagoActivacion(TIPO_PAGO_RECONEXION, "Reconexion")
        self._flujo_reconexion.buscar_solicitado.connect(self.buscar_solicitado)
        self._flujo_reconexion.casa_solicitada.connect(self.casa_reconexion_solicitada)
        self._flujo_reconexion.preparar_resumen_solicitado.connect(
            self.previsualizacion_reconexion_solicitada
        )
        self._flujo_reconexion.registrar_pago_solicitado.connect(
            self.registrar_pago_reconexion_solicitado
        )

        self._flujo_conexion = FlujoPagoActivacion(TIPO_PAGO_CONEXION, "Conexion")
        self._flujo_conexion.buscar_solicitado.connect(self.buscar_solicitado)
        self._flujo_conexion.casa_solicitada.connect(self.casa_conexion_solicitada)
        self._flujo_conexion.preparar_resumen_solicitado.connect(
            self.previsualizacion_conexion_solicitada
        )
        self._flujo_conexion.registrar_pago_solicitado.connect(
            self.registrar_pago_conexion_solicitado
        )

        self._flujo_plan = FlujoPagoPlan()
        self._flujo_plan.buscar_solicitado.connect(self.buscar_solicitado)
        self._flujo_plan.casa_solicitada.connect(self.casa_plan_solicitada)
        self._flujo_plan.preparar_resumen_solicitado.connect(self.previsualizacion_plan_solicitada)
        self._flujo_plan.registrar_pago_solicitado.connect(self.registrar_pago_plan_solicitado)

        self._tabs.addTab(self._flujo_mensual, "Pago mensual")
        self._tabs.addTab(self._flujo_reconexion, "Reconexion")
        self._tabs.addTab(self._flujo_conexion, "Conexion")
        self._tabs.addTab(
            FlujoPestanaPendiente(
                "tabCuotaPlanPendiente",
                "Cuota plan",
                "El flujo guiado de cuota de plan se implementará por pasos en una fase posterior.",
            ),
            "Cuota plan",
        )

        layout.addWidget(self.label_mensaje)
        layout.addLayout(fila_estado_documental)
        layout.addWidget(self._tabs, 1)
        widget_cuota_plan = self._tabs.widget(3)
        if isinstance(widget_cuota_plan, FlujoPestanaPendiente):
            self._tabs.removeTab(3)
            self._tabs.insertTab(3, self._flujo_plan, "Cuota plan")
        self._tabs.currentChanged.connect(lambda _indice: self._actualizar_tinte_tab_mensual())

    def mostrar_estado(
        self,
        estado: EstadoModuloPagos,
        formatear_moneda: Callable[[int], str],
        formatear_fecha: Callable[[str], str],
        mostrar_casas: bool = False,
    ) -> None:
        self._actualizar_estado_documental(
            estado.impresora_termica_configurada,
            estado.comprobantes_pendientes_impresion,
        )
        self._flujo_mensual.mostrar_estado(
            estado,
            formatear_moneda,
            formatear_fecha,
            mostrar_casas=mostrar_casas,
        )
        self._flujo_reconexion.mostrar_estado(
            estado,
            formatear_moneda,
            mostrar_casas=mostrar_casas,
        )
        self._flujo_conexion.mostrar_estado(
            estado,
            formatear_moneda,
            mostrar_casas=mostrar_casas,
        )
        self._flujo_plan.mostrar_estado(
            estado,
            formatear_moneda,
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

    def mostrar_diagnostico_conexion(
        self,
        casa_id: int,
        diagnostico: DiagnosticoPagoActivacion | None,
    ) -> None:
        self._flujo_conexion.mostrar_diagnostico(casa_id, diagnostico)

    def mostrar_diagnostico_reconexion(
        self,
        casa_id: int,
        diagnostico: DiagnosticoPagoActivacion | None,
    ) -> None:
        self._flujo_reconexion.mostrar_diagnostico(casa_id, diagnostico)

    def mostrar_diagnostico_plan(
        self,
        casa_id: int,
        diagnostico: DiagnosticoPagoPlan | None,
    ) -> None:
        self._flujo_plan.mostrar_diagnostico(casa_id, diagnostico)

    def mostrar_previsualizacion_conexion(
        self,
        resumen: ResumenConfirmacionPago | None,
        resultado: ResultadoPago | None,
        formatear_moneda: Callable[[int], str] | None = None,
    ) -> None:
        self._flujo_conexion.mostrar_previsualizacion_pago(resumen, resultado, formatear_moneda)

    def mostrar_previsualizacion_reconexion(
        self,
        resumen: ResumenConfirmacionPago | None,
        resultado: ResultadoPago | None,
        formatear_moneda: Callable[[int], str] | None = None,
    ) -> None:
        self._flujo_reconexion.mostrar_previsualizacion_pago(
            resumen,
            resultado,
            formatear_moneda,
        )

    def mostrar_previsualizacion_plan(
        self,
        resumen: ResumenConfirmacionPago | None,
        resultado: ResultadoPago | None,
        formatear_moneda: Callable[[int], str] | None = None,
    ) -> None:
        self._flujo_plan.mostrar_previsualizacion_pago(resumen, resultado, formatear_moneda)

    def obtener_casa_seleccionada_id(self) -> int | None:
        return self._flujo_mensual.obtener_casa_seleccionada_id()

    def obtener_casa_conexion_seleccionada_id(self) -> int | None:
        return self._flujo_conexion.obtener_casa_seleccionada_id()

    def obtener_casa_reconexion_seleccionada_id(self) -> int | None:
        return self._flujo_reconexion.obtener_casa_seleccionada_id()

    def obtener_casa_plan_seleccionada_id(self) -> int | None:
        return self._flujo_plan.obtener_casa_seleccionada_id()

    def reiniciar_flujo_mensual(self) -> None:
        self._flujo_mensual.reiniciar_flujo()

    def reiniciar_flujo_conexion(self) -> None:
        self._flujo_conexion.reiniciar_flujo()

    def reiniciar_flujo_reconexion(self) -> None:
        self._flujo_reconexion.reiniciar_flujo()

    def reiniciar_flujo_plan(self) -> None:
        self._flujo_plan.reiniciar_flujo()

    def aplicar_tema(self, nombre_tema: str) -> None:
        self._tema_actual = (
            resolver_nombre_tema(nombre_tema)
        )
        self._paleta = obtener_paleta_tema(self._tema_actual)
        self._flujo_mensual.aplicar_tema(self._tema_actual)
        self._flujo_reconexion.aplicar_tema(self._tema_actual)
        self._flujo_conexion.aplicar_tema(self._tema_actual)
        self._flujo_plan.aplicar_tema(self._tema_actual)
        self._aplicar_estilos()

    def confirmar_pago(
        self,
        resumen: ResumenConfirmacionPago,
        formatear_moneda: Callable[[int], str],
    ) -> bool:
        if resumen.tipo_pago == TIPO_PAGO_MENSUALIDAD:
            conceptos = ", ".join(detalle.periodo_nombre for detalle in resumen.detalles[:5])
        else:
            conceptos = ", ".join(detalle.descripcion for detalle in resumen.detalles[:5])
        if len(resumen.detalles) > 5:
            conceptos = f"{conceptos} y {len(resumen.detalles) - 5} mas"
        titulo = {
            TIPO_PAGO_MENSUALIDAD: "Confirmar pago mensual",
            TIPO_PAGO_PLAN: "Confirmar cuota de plan",
            TIPO_PAGO_CONEXION: "Confirmar conexion",
            TIPO_PAGO_RECONEXION: "Confirmar reconexion",
        }.get(resumen.tipo_pago, "Confirmar pago")
        descripcion = (
            "Revisa el resumen antes de guardar. El comprobante usara un correlativo unico y no mezclara otros tipos de pago."
            if resumen.tipo_pago == TIPO_PAGO_MENSUALIDAD
            else (
                "Revisa el resumen antes de guardar. El comprobante registrara una o varias cuotas del mismo plan sin mezclar otros tipos de cobro."
                if resumen.tipo_pago == TIPO_PAGO_PLAN
                else "Revisa el resumen antes de guardar. El comprobante mantendra conceptos separados de activacion y no podra anularse desde el flujo normal."
            )
        )
        detalles = (
            ("Casa", resumen.casa.casa_codigo),
            ("Abonado", resumen.casa.abonado_nombre),
            ("Operacion", self._etiqueta_tipo_pago(resumen.tipo_pago)),
            ("Conceptos", conceptos or "Sin conceptos"),
            ("Metodo", resumen.metodo_pago.nombre),
            ("Referencia", resumen.referencia or "No aplica"),
            ("Fecha activacion", resumen.fecha_activacion or "No aplica"),
            ("Saldo anterior", formatear_moneda(resumen.saldo_anterior_centavos)),
            ("Total a cobrar", formatear_moneda(resumen.total_pago_centavos)),
            ("Saldo posterior", formatear_moneda(resumen.saldo_posterior_centavos)),
            ("Aviso", "Despues de confirmar, el pago no podra anularse dentro del flujo normal del prototipo."),
        )
        dialogo = DialogoConfirmacionSigqua(
            titulo=titulo,
            descripcion=descripcion,
            detalles=detalles,
            texto_confirmar="Guardar pago",
            variante_confirmar="destructivo",
            parent=self,
        )
        return dialogo.exec() == QDialog.DialogCode.Accepted

    def mostrar_resultado_impresion(self, mensaje: str, es_error: bool = False) -> None:
        self.mostrar_mensaje(
            mensaje,
            es_error=es_error,
            duracion_ms=self.DURACION_MENSAJE_COMPROBANTE_MS,
        )

    def mostrar_mensaje(
        self,
        mensaje: str,
        es_error: bool = False,
        duracion_ms: int | None = None,
    ) -> None:
        self.label_mensaje.setText(mensaje)
        self.label_mensaje.setProperty("estado", "error" if es_error else "exito")
        self.label_mensaje.style().unpolish(self.label_mensaje)
        self.label_mensaje.style().polish(self.label_mensaje)
        self.label_mensaje.setVisible(True)
        QTimer.singleShot(duracion_ms or self.DURACION_MENSAJE_GENERAL_MS, self.label_mensaje.hide)

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
        fondo_header_destacado = obtener_fondo_header_destacado(self._tema_actual)
        self.setStyleSheet(
            f"""
            QWidget#vistaPagos {{
                background-color: {paleta["fondo_principal"]};
                color: {paleta["texto_principal"]};
                font-family: "{paleta["familia_tipografica"]}";
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
            QLabel#badgeEstadoDocumentoPago {{
                border-radius: 10px;
                color: #C5DDEE;
                font-size: 10px;
                font-weight: 800;
                padding: 4px 9px;
                background: rgba(142, 168, 188, 0.22);
                border: 1px solid rgba(126, 167, 196, 0.30);
            }}
            QLabel#badgeEstadoDocumentoPago[activo="true"] {{
                color: #DDFBF0;
                background: rgba(55, 211, 153, 0.22);
                border: 1px solid rgba(55, 211, 153, 0.26);
            }}
            QLabel#badgeEstadoDocumentoPago[activo="false"] {{
                color: #FFE3E3;
                background: rgba(242, 116, 116, 0.18);
                border: 1px solid rgba(242, 116, 116, 0.28);
            }}
            QTabWidget#tabsPagos::pane {{
                border: 1px solid rgba(126, 167, 196, 0.48);
                border-radius: 22px;
                background-color: {fondo_header_destacado};
                top: -2px;
                padding: 10px;
            }}
            QTabWidget#tabsPagos QWidget {{
                background: transparent;
            }}
            QTabWidget#tabsPagos QTabBar {{
                left: 12px;
            }}
            QTabWidget#tabsPagos QTabBar::tab {{
                background-color: {paleta["fondo_panel_accion"]};
                border: 1px solid {paleta["borde_suave"]};
                border-bottom: 0;
                border-top-left-radius: 16px;
                border-top-right-radius: 16px;
                color: {paleta["texto_secundario"]};
                font-size: 12px;
                font-weight: 800;
                min-width: 132px;
                min-height: 40px;
                padding: 10px 16px;
                margin-right: 8px;
                margin-top: 6px;
            }}
            QTabWidget#tabsPagos QTabBar::tab:selected {{
                background-color: {paleta["acento_seleccion"]};
                color: #75C7F0;
                border: 2px solid {paleta["borde_principal"]};
                margin-top: 0px;
                padding-top: 12px;
                padding-bottom: 12px;
            }}
            QTabWidget#tabsPagos[estadoMensual="OK"] QTabBar::tab:selected {{
                background-color: {paleta["fondo_exito"]};
                border: 2px solid {paleta["borde_exito"]};
                color: {paleta["texto_exito"]};
            }}
            QTabWidget#tabsPagos[estadoMensual="BLOQUEADO"] QTabBar::tab:selected {{
                background-color: {paleta["fondo_error"]};
                border: 2px solid {paleta["borde_error"]};
                color: {paleta["texto_error"]};
            }}
            QTabWidget#tabsPagos QTabBar::tab:hover {{
                color: {paleta["texto_principal"]};
                border-color: {paleta["borde_principal"]};
            }}
            """
        )

    def _actualizar_estado_documental(
        self,
        impresora_configurada: bool,
        pendientes_impresion: int,
    ) -> None:
        self._label_estado_apertura.setText(
            "ESC/POS listo" if impresora_configurada else "Sin impresora"
        )
        self._label_estado_impresion.setText(f"Pendientes: {pendientes_impresion}")
        for widget, activo in (
            (self._label_estado_apertura, impresora_configurada),
            (self._label_estado_impresion, pendientes_impresion == 0),
        ):
            widget.setProperty("activo", activo)
            widget.style().unpolish(widget)
            widget.style().polish(widget)

