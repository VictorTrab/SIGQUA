"""Vista PySide6 del modulo de configuracion."""

from __future__ import annotations

from typing import Callable

from PySide6.QtCore import Qt, QTimer, Signal, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtPrintSupport import QPrinterInfo
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from comun.ui import (
    BotonAccionContextual,
    CampoMontoMonetario,
    ContenedorTarjetasResumenOperativo,
    DialogoConfirmacionSigqua,
    TarjetaResumenOperativa,
    crear_boton_operativo,
)
from comun.ui.comprobante_termico import (
    ConfiguracionDocumentoRecibo,
    DatosDocumentoRecibo,
    crear_documento_recibo_termico,
)
from comun.ui.temas import (
    TEMA_SIGQUA_PREDETERMINADO,
    obtener_paleta_tema,
    obtener_tema_actual,
    resolver_nombre_tema,
)
from modulos.configuracion.entidades import EstadoConfiguracion


class TarjetaResumenConfiguracion(TarjetaResumenOperativa):
    """Tarjeta de resumen para configuracion."""

    def __init__(self, titulo: str, icono: str, color_icono: str) -> None:
        super().__init__(icono, color_icono)
        self.setObjectName("tarjetaResumenConfiguracion")
        self.setMinimumHeight(82)
        self.setMaximumHeight(82)
        self._titulo_fijo = titulo

    def actualizar(self, valor: str, detalle: str) -> None:
        super().actualizar(self._titulo_fijo, valor, detalle)


class VistaConfiguracion(QWidget):
    """Pantalla operativa del modulo de configuracion."""

    guardar_datos_junta_solicitado = Signal(str, str, str, str, str, str, str)
    guardar_parametros_factura_solicitado = Signal(
        str,
        str,
        str,
        str,
        str,
        str,
        bool,
        bool,
        bool,
        bool,
        bool,
        str,
        str,
        int,
        bool,
        str,
        str,
    )
    guardar_parametros_cobro_solicitado = Signal(int, bool, int, bool, int, bool, bool, int, int, int)
    probar_impresora_comprobantes_solicitado = Signal(str)
    probar_impresora_reportes_solicitado = Signal(str)
    guardar_operacion_respaldo_solicitado = Signal(
        str,
        str,
        bool,
        bool,
        bool,
    )
    crear_respaldo_manual_solicitado = Signal()
    restaurar_respaldo_solicitado = Signal(int)
    guardar_duracion_sesion_solicitado = Signal(float)
    guardar_reportes_pdf_solicitado = Signal(str, bool, bool, str)

    DURACION_MENSAJE_MS = 3200
    MORA_BAJA_HASTA_VERSION = 2
    MORA_MEDIA_HASTA_VERSION = 5
    OPCIONES_DURACION_SESION = (
        ("30 minutos", 0.5),
        ("1 hora", 1.0),
        ("2 horas", 2.0),
        ("4 horas", 4.0),
        ("8 horas", 8.0),
        ("12 horas", 12.0),
    )
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("vistaConfiguracion")
        self._tema_actual = obtener_tema_actual()
        self._paleta_tema = obtener_paleta_tema(self._tema_actual)
        self._cargando_estado = False
        self._hay_cambios_pendientes = False
        self._indice_tab_anterior = 0
        self._ultimo_estado_configuracion: EstadoConfiguracion | None = None
        self._ultimo_formateador_moneda: Callable[[int], str] | None = None
        self._temporizador_mensaje = QTimer(self)
        self._temporizador_mensaje.setSingleShot(True)
        self._temporizador_mensaje.timeout.connect(self._ocultar_mensaje)
        self._construir_ui()
        self._conectar_controles_cambios_pendientes()
        self._aplicar_estilos()

    def mostrar_estado(
        self,
        estado: EstadoConfiguracion,
        formateador_moneda: Callable[[int], str],
    ) -> None:
        self._cargando_estado = True
        try:
            self._aplicar_estado_configuracion(estado, formateador_moneda)
        finally:
            self._cargando_estado = False
        self._ultimo_estado_configuracion = estado
        self._ultimo_formateador_moneda = formateador_moneda
        self._hay_cambios_pendientes = False

    def _aplicar_estado_configuracion(
        self,
        estado: EstadoConfiguracion,
        formateador_moneda: Callable[[int], str],
    ) -> None:
        self._tarjeta_precio.actualizar(
            formateador_moneda(estado.parametros_cobro.precio_mensual_centavos),
            "Afecta cargos mensuales nuevos en pagos, morosidad y reportes.",
        )
        self._tarjeta_correlativo.actualizar(
            estado.factura.correlativo_actual,
            f"Proximo recibo: {estado.factura.proximo_correlativo}.",
        )
        self._tarjeta_adelantos.actualizar(
            "Activos" if estado.parametros_cobro.permitir_pago_adelantado else "Bloqueados",
            (
                f"Hasta {estado.parametros_cobro.meses_adelanto_maximo} meses."
                if estado.parametros_cobro.permitir_pago_adelantado
                else "Pagos adelantados deshabilitados desde configuracion."
            ),
        )
        self._tarjeta_respaldo.actualizar(
            "Activo",
            (
                f"Al cerrar sesion. Ultimo: {estado.operacion.ultimo_respaldo_en}."
                if estado.operacion.ultimo_respaldo_en
                else "Al cerrar sesion. Sin respaldos registrados."
            ),
        )

        self._campo_junta_nombre.setText(estado.identidad_empresa.nombre)
        self._campo_junta_telefono.setText(estado.identidad_empresa.telefono)
        self._campo_junta_correo.setText(estado.identidad_empresa.correo)
        self._campo_junta_direccion.setPlainText(estado.identidad_empresa.direccion)
        self._campo_junta_identificador.setText(estado.identidad_empresa.identificador_fiscal)
        self._campo_junta_mensaje_contacto.setPlainText(estado.identidad_empresa.mensaje_contacto)
        self._campo_factura_nombre.setText(estado.identidad_empresa.nombre)
        self._campo_factura_datos.setText(self._componer_datos_recibo(estado))
        self._valor_correlativo_actual.setText(estado.factura.correlativo_actual)
        self._valor_ultimo_comprobante.setText(estado.factura.ultimo_comprobante_emitido)
        self._campo_titulo_documento.setText(estado.factura.titulo_documento)
        self._campo_subtitulo_documento.setText(estado.factura.subtitulo_documento)
        self._campo_texto_legal_superior.setPlainText(estado.factura.texto_legal_superior)
        self._campo_texto_pie.setPlainText(estado.factura.texto_pie)
        self._campo_texto_legal_inferior.setPlainText(estado.factura.texto_legal_inferior)
        self._campo_etiqueta_copia.setText(estado.factura.etiqueta_copia)
        self._seleccionar_impresora(self._combo_impresora_comprobantes, estado.factura.impresora_termica_nombre)
        self._combo_ancho_termico.setCurrentText(f"{estado.factura.impresora_termica_ancho_mm} mm")
        self._check_corte_termico.setChecked(estado.factura.impresora_termica_corte_automatico)
        self._campo_codigo_pagina_termico.setText(estado.factura.impresora_termica_codigo_pagina)
        self._seleccionar_impresora(self._combo_impresora_reportes, estado.factura.impresora_reportes_nombre)
        self._check_mostrar_correo.setChecked(estado.factura.mostrar_correo)
        self._check_mostrar_telefono.setChecked(estado.factura.mostrar_telefono)
        self._check_mostrar_direccion.setChecked(estado.factura.mostrar_direccion)
        self._check_mostrar_identificador.setChecked(estado.factura.mostrar_identificador_fiscal)
        self._check_firma_habilitada.setChecked(estado.factura.firma_habilitada)
        self._campo_firma_texto_linea.setText(estado.factura.firma_texto_linea)
        self._valor_total_comprobantes.setText(str(estado.factura.total_comprobantes_emitidos))
        self._valor_proximo_correlativo.setText(estado.factura.proximo_correlativo)
        self._valor_pendientes_impresion.setText(str(estado.factura.comprobantes_pendientes_impresion))

        self._campo_precio_mensual.establecer_desde_centavos(
            estado.parametros_cobro.precio_mensual_centavos
        )
        self._check_multa_automatica.blockSignals(True)
        self._check_multa_automatica.setChecked(estado.parametros_cobro.multa_mora_automatica_activa)
        self._check_multa_automatica.blockSignals(False)
        self._campo_multa_automatica.establecer_desde_centavos(
            estado.parametros_cobro.multa_mora_automatica_centavos
        )
        self._check_corte_automatico.blockSignals(True)
        self._check_corte_automatico.setChecked(estado.parametros_cobro.corte_automatico_activo)
        self._check_corte_automatico.blockSignals(False)
        self._campo_meses_para_corte.setText(str(estado.parametros_cobro.meses_para_corte))
        self._check_prorrateo_activacion.blockSignals(True)
        self._check_prorrateo_activacion.setChecked(
            estado.parametros_cobro.cobrar_mensualidad_prorrateada_activacion
        )
        self._check_prorrateo_activacion.blockSignals(False)
        self._check_pago_adelantado.blockSignals(True)
        self._check_pago_adelantado.setChecked(estado.parametros_cobro.permitir_pago_adelantado)
        self._check_pago_adelantado.blockSignals(False)
        self._campo_meses_adelanto_maximo.setText(
            str(estado.parametros_cobro.meses_adelanto_maximo)
        )
        self._actualizar_estado_campos_cobro()

        self._campo_ruta_respaldos_principal.setText(estado.operacion.ruta_respaldos_principal)
        self._campo_ruta_respaldos_secundaria.setText(estado.operacion.ruta_respaldos_secundaria)
        self._check_respaldo_secundario.blockSignals(True)
        self._check_respaldo_secundario.setChecked(estado.operacion.respaldo_secundario_activo)
        self._check_respaldo_secundario.blockSignals(False)
        self._check_comprimir_zip.setChecked(estado.operacion.comprimir_zip)
        self._check_organizar_periodo.setChecked(estado.operacion.organizar_por_periodo)
        self._seleccionar_duracion_sesion(estado.seguridad.duracion_sesion_horas)
        self._valor_ultimo_respaldo.setText(
            estado.operacion.ultimo_respaldo_en or "Sin registros"
        )
        self._valor_estado_respaldo.setText(estado.operacion.ultimo_respaldo_estado)
        self._valor_total_respaldos.setText(str(estado.operacion.total_respaldos))
        self._valor_archivo_respaldo.setText(estado.operacion.ultimo_respaldo_archivo or "Sin archivo")
        self._valor_tamano_respaldo.setText(
            self._formatear_tamano_bytes(estado.operacion.ultimo_respaldo_tamano_bytes)
        )
        self._valor_respaldo_automatico.setText("Activo al cerrar sesion")
        self._valor_respaldo_generado_por.setText(estado.operacion.ultimo_respaldo_generado_por)
        self._valor_ruta_respaldos.setText(estado.operacion.ruta_respaldos_principal)
        self._valor_retencion.setText(f"{estado.operacion.retencion_maxima} respaldos recientes")
        self._valor_ruta_comprobantes.setText(estado.operacion.ruta_exportaciones_comprobantes)
        self._valor_ruta_reportes.setText(estado.operacion.ruta_exportaciones_reportes)
        self._campo_ruta_reportes_pdf.setText(estado.reportes_pdf.ruta_salida)
        self._ruta_reportes_predeterminada = estado.reportes_pdf.ruta_predeterminada
        self._check_abrir_reportes_pdf.setChecked(estado.reportes_pdf.abrir_automaticamente)
        self._check_firma_reportes_pdf.setChecked(estado.reportes_pdf.firma_habilitada)
        self._campo_firma_reportes_pdf.setText(estado.reportes_pdf.firma_texto_linea)
        self._actualizar_estado_firma_reportes_pdf()
        self._actualizar_respaldos_disponibles(estado)

        self._valor_autenticacion.setText("Local")
        self._valor_intentos.setText(str(estado.seguridad.maximo_intentos_fallidos))
        self._valor_sesion.setText(self._texto_duracion_sesion(estado.seguridad.duracion_sesion_horas))
        self._valor_restablecimiento.setText("Administrativo")
        self._valor_cambio_clave.setText("Obligatorio cuando hay clave temporal")

        self._valor_nombre_sistema.setText(estado.informacion.nombre_sistema)
        self._valor_version_sistema.setText(estado.informacion.version_sistema or "Sin version")
        self._valor_ruta_base.setText(estado.informacion.ruta_base_datos)
        self._valor_ruta_respaldos_activa.setText(estado.operacion.ruta_respaldos_principal)
        self._valor_modo_operacion.setText(estado.informacion.modo_operacion)
        self._valor_duracion_sesion_info.setText(self._texto_duracion_sesion(estado.seguridad.duracion_sesion_horas))
        self._valor_actualizacion.setText(estado.informacion.ultima_actualizacion or "Sin registro")
        self._valor_actualizado_por.setText(estado.informacion.actualizado_por)

        self._actualizar_estado_respaldos()
        self._actualizar_preview_comprobante(estado, formateador_moneda)

    def _conectar_controles_cambios_pendientes(self) -> None:
        campos_texto = (
            self._campo_junta_nombre,
            self._campo_junta_telefono,
            self._campo_junta_correo,
            self._campo_junta_identificador,
            self._campo_junta_sitio_web,
            self._campo_junta_direccion,
            self._campo_junta_mensaje_contacto,
            self._campo_titulo_documento,
            self._campo_subtitulo_documento,
            self._campo_texto_legal_superior,
            self._campo_texto_pie,
            self._campo_texto_legal_inferior,
            self._campo_etiqueta_copia,
            self._campo_codigo_pagina_termico,
            self._campo_firma_texto_linea,
            self._campo_precio_mensual,
            self._campo_multa_automatica,
            self._campo_meses_para_corte,
            self._campo_meses_adelanto_maximo,
            self._campo_ruta_reportes_pdf,
            self._campo_firma_reportes_pdf,
            self._campo_ruta_respaldos_principal,
            self._campo_ruta_respaldos_secundaria,
        )
        for campo in campos_texto:
            campo.textChanged.connect(self._marcar_cambios_pendientes)

        for combo in (
            self._combo_impresora_comprobantes,
            self._combo_impresora_reportes,
            self._combo_ancho_termico,
            self._combo_duracion_sesion,
        ):
            combo.currentIndexChanged.connect(self._marcar_cambios_pendientes)
            combo.currentTextChanged.connect(self._marcar_cambios_pendientes)

        for check in (
            self._check_corte_termico,
            self._check_mostrar_correo,
            self._check_mostrar_telefono,
            self._check_mostrar_direccion,
            self._check_mostrar_identificador,
            self._check_firma_habilitada,
            self._check_multa_automatica,
            self._check_corte_automatico,
            self._check_prorrateo_activacion,
            self._check_pago_adelantado,
            self._check_abrir_reportes_pdf,
            self._check_firma_reportes_pdf,
            self._check_respaldo_secundario,
            self._check_comprimir_zip,
            self._check_organizar_periodo,
        ):
            check.toggled.connect(self._marcar_cambios_pendientes)

        self._tabs.currentChanged.connect(self._confirmar_cambio_pestana)

    def _marcar_cambios_pendientes(self, *args: object) -> None:
        if self._cargando_estado:
            return
        self._hay_cambios_pendientes = True

    def _confirmar_cambio_pestana(self, indice_nuevo: int) -> None:
        if indice_nuevo == self._indice_tab_anterior:
            return
        if not self._hay_cambios_pendientes:
            self._indice_tab_anterior = indice_nuevo
            return
        if (
            self._ultimo_estado_configuracion is None
            or self._ultimo_formateador_moneda is None
        ):
            self._indice_tab_anterior = indice_nuevo
            return

        self._cambiar_pestana_sin_confirmar(self._indice_tab_anterior)
        if self._mostrar_confirmacion_descartar_cambios():
            self.mostrar_estado(
                self._ultimo_estado_configuracion,
                self._ultimo_formateador_moneda,
            )
            self._cambiar_pestana_sin_confirmar(indice_nuevo)
            self._indice_tab_anterior = indice_nuevo

    def _cambiar_pestana_sin_confirmar(self, indice: int) -> None:
        self._tabs.blockSignals(True)
        self._tabs.setCurrentIndex(indice)
        self._tabs.blockSignals(False)

    def _mostrar_confirmacion_descartar_cambios(self) -> bool:
        dialogo = DialogoConfirmacionSigqua(
            titulo="Cambios sin guardar",
            descripcion=(
                "Hay cambios pendientes en esta pestaña. "
                "¿Deseas descartarlos y cambiar de sección?"
            ),
            texto_confirmar="Descartar cambios",
            texto_cancelar="Seguir editando",
            variante_confirmar="peligro",
            parent=self,
        )
        return bool(dialogo.exec())

    def mostrar_mensaje(self, mensaje: str, es_error: bool = False) -> None:
        self._mensaje.setText(mensaje)
        self._mensaje.setProperty("error", es_error)
        self._mensaje.style().unpolish(self._mensaje)
        self._mensaje.style().polish(self._mensaje)
        self._mensaje.setVisible(bool(mensaje))
        if mensaje:
            self._temporizador_mensaje.start(self.DURACION_MENSAJE_MS)

    def aplicar_tema(self, nombre_tema: str) -> None:
        self._tema_actual = resolver_nombre_tema(nombre_tema)
        self._paleta_tema = obtener_paleta_tema(self._tema_actual)
        self._aplicar_estilos()

    def _construir_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 6)
        layout.setSpacing(8)

        encabezado = QHBoxLayout()
        encabezado.setSpacing(12)
        encabezado.addStretch(1)

        fila_acciones = QHBoxLayout()
        fila_acciones.setSpacing(8)
        boton_info = BotonAccionContextual("Información", variante="ayuda", centrado=True, mostrar_icono=False)
        boton_info.setMinimumWidth(132)
        boton_info.clicked.connect(self._mostrar_ayuda)
        fila_acciones.addWidget(boton_info)
        encabezado.addLayout(fila_acciones)

        self._mensaje = QLabel("")
        self._mensaje.setObjectName("mensajeConfiguracion")
        self._mensaje.setVisible(False)
        self._mensaje.setWordWrap(True)

        tarjetas = ContenedorTarjetasResumenOperativo()
        self._tarjeta_precio = TarjetaResumenConfiguracion("Precio mensual", "receipt-2.svg", "#75C7F0")
        self._tarjeta_correlativo = TarjetaResumenConfiguracion("Proximo recibo", "barcode.svg", "#8de8c7")
        self._tarjeta_adelantos = TarjetaResumenConfiguracion("Pago adelantado", "calendar-plus.svg", "#f7cc7a")
        self._tarjeta_respaldo = TarjetaResumenConfiguracion("Respaldo automatico", "tool.svg", "#92B6CC")
        tarjetas.establecer_tarjetas(
            (self._tarjeta_precio, self._tarjeta_correlativo, self._tarjeta_adelantos, self._tarjeta_respaldo)
        )

        self._tabs = QTabWidget()
        self._tabs.setObjectName("tabsConfiguracion")
        self._tabs.addTab(self._crear_tab_datos_junta(), "Organización")
        self._tabs.addTab(self._crear_tab_operacion_respaldo(), "Respaldos")
        self._tabs.addTab(self._crear_tab_informacion(), "Sistema")
        self._tabs.addTab(self._crear_tab_factura(), "Comprobantes")
        self._tabs.addTab(self._crear_tab_impresoras(), "Impresoras")
        self._tabs.addTab(self._crear_tab_cobros(), "Cobros")
        self._tabs.addTab(self._crear_tab_morosidad(), "Morosidad")
        self._tabs.addTab(self._crear_tab_reportes_pdf(), "Reportes PDF")

        layout.addLayout(encabezado)
        layout.addWidget(self._mensaje)
        layout.addWidget(tarjetas)
        layout.addWidget(self._tabs, 1)

    def _crear_tab_datos_junta(self) -> QWidget:
        self._campo_junta_nombre = QLineEdit()
        self._campo_junta_telefono = QLineEdit()
        self._campo_junta_correo = QLineEdit()
        self._campo_junta_identificador = QLineEdit()
        self._campo_junta_sitio_web = QLineEdit()
        self._campo_junta_direccion = QPlainTextEdit()
        self._campo_junta_direccion.setFixedHeight(72)
        self._campo_junta_mensaje_contacto = QPlainTextEdit()
        self._campo_junta_mensaje_contacto.setFixedHeight(72)

        grilla_general = QGridLayout()
        grilla_general.setHorizontalSpacing(12)
        grilla_general.setVerticalSpacing(10)
        grilla_general.addWidget(
            self._crear_bloque_campo("Nombre legal o comercial", self._campo_junta_nombre),
            0,
            0,
            1,
            2,
        )

        subtitulo_contacto = self._crear_subtitulo_grupo("Contacto institucional")

        grilla_contacto = QGridLayout()
        grilla_contacto.setHorizontalSpacing(12)
        grilla_contacto.setVerticalSpacing(10)
        grilla_contacto.addWidget(
            self._crear_bloque_campo("Telefono institucional", self._campo_junta_telefono),
            0,
            0,
        )
        grilla_contacto.addWidget(
            self._crear_bloque_campo("Correo institucional", self._campo_junta_correo),
            0,
            1,
        )
        grilla_contacto.addWidget(
            self._crear_bloque_campo("Identificación institucional", self._campo_junta_identificador),
            1,
            0,
        )

        grilla_ubicacion = QGridLayout()
        grilla_ubicacion.setHorizontalSpacing(12)
        grilla_ubicacion.setVerticalSpacing(10)
        grilla_ubicacion.addWidget(
            self._crear_bloque_campo("Direccion fiscal u operativa", self._campo_junta_direccion),
            0,
            0,
        )
        grilla_ubicacion.addWidget(
            self._crear_bloque_campo("Mensaje de contacto", self._campo_junta_mensaje_contacto),
            0,
            1,
        )

        boton_guardar = crear_boton_operativo("Guardar identidad de la empresa", principal=True)
        boton_guardar.clicked.connect(
            lambda: self.guardar_datos_junta_solicitado.emit(
                self._campo_junta_nombre.text().strip(),
                self._campo_junta_telefono.text().strip(),
                self._campo_junta_correo.text().strip(),
                self._campo_junta_identificador.text().strip(),
                "",
                self._campo_junta_direccion.toPlainText().strip(),
                self._campo_junta_mensaje_contacto.toPlainText().strip(),
            )
        )

        panel_identidad = self._crear_panel(
            "Identidad de la empresa",
            "Datos visibles en comprobantes, reportes y documentos.",
            [
                grilla_general,
                subtitulo_contacto,
                grilla_contacto,
                grilla_ubicacion,
            ],
        )

        contenido = self._crear_contenedor_scroll()
        contenido.widget().layout().addWidget(panel_identidad)
        self._agregar_cierre_tab_compacto(
            contenido,
            (
                "Impacta comprobantes, reportes PDF, documentos de deuda y vistas operativas. "
                "Solo actualiza la identidad visible de la empresa."
            ),
            boton_guardar,
        )
        return contenido

    def _crear_tab_factura(self) -> QWidget:
        self._campo_factura_nombre = QLineEdit()
        self._campo_factura_nombre.setReadOnly(True)
        self._campo_factura_datos = QLineEdit()
        self._campo_factura_datos.setReadOnly(True)
        self._valor_correlativo_actual = self._crear_valor_seguridad()
        self._valor_ultimo_comprobante = self._crear_valor_seguridad()
        self._campo_titulo_documento = QLineEdit()
        self._campo_subtitulo_documento = QLineEdit()
        self._campo_texto_legal_superior = QPlainTextEdit()
        self._campo_texto_legal_superior.setFixedHeight(64)
        self._campo_texto_pie = QPlainTextEdit()
        self._campo_texto_pie.setFixedHeight(76)
        self._campo_texto_legal_inferior = QPlainTextEdit()
        self._campo_texto_legal_inferior.setFixedHeight(64)
        self._campo_etiqueta_copia = QLineEdit()
        self._combo_impresora_comprobantes = self._crear_combo_impresoras()
        self._combo_impresora_reportes = self._crear_combo_impresoras()
        self._combo_ancho_termico = QComboBox()
        self._combo_ancho_termico.addItems(["80 mm", "58 mm"])
        self._check_corte_termico = QCheckBox("Cortar papel automaticamente")
        self._campo_codigo_pagina_termico = QLineEdit()
        self._campo_codigo_pagina_termico.setPlaceholderText("cp850")
        self._check_mostrar_correo = QCheckBox("Mostrar correo institucional")
        self._check_mostrar_telefono = QCheckBox("Mostrar telefono institucional")
        self._check_mostrar_direccion = QCheckBox("Mostrar direccion institucional")
        self._check_mostrar_identificador = QCheckBox("Mostrar identificador fiscal")
        self._check_firma_habilitada = QCheckBox("Mostrar línea de firma en documentos")
        self._campo_firma_texto_linea = QLineEdit()
        self._campo_firma_texto_linea.setPlaceholderText("Firma autorizada")
        self._valor_total_comprobantes = self._crear_valor_seguridad()
        self._valor_proximo_correlativo = self._crear_valor_seguridad()
        self._valor_pendientes_impresion = self._crear_valor_seguridad()

        grilla_superior = QGridLayout()
        grilla_superior.setHorizontalSpacing(12)
        grilla_superior.setVerticalSpacing(12)
        grilla_superior.addWidget(
            self._crear_bloque_campo("Nombre visible de la empresa", self._campo_factura_nombre),
            0,
            0,
            1,
            2,
        )
        grilla_superior.addWidget(
            self._crear_bloque_campo("Datos de contacto en comprobante", self._campo_factura_datos),
            1,
            0,
            1,
            2,
        )

        panel_factura = self._crear_panel(
            "Documentos y comprobantes",
            "Configuracion operativa del backend documental usado por comprobantes, deuda y reportes PDF.",
            [
                grilla_superior,
                self._crear_fila_resumen("Correlativo actual", self._valor_correlativo_actual),
                self._crear_fila_resumen("Ultimo comprobante emitido", self._valor_ultimo_comprobante),
                self._crear_bloque_campo("Titulo del documento", self._campo_titulo_documento),
                self._crear_bloque_campo("Texto inferior", self._campo_texto_pie),
                self._crear_bloque_campo("Etiqueta de copia", self._campo_etiqueta_copia),
                self._check_mostrar_correo,
                self._check_mostrar_telefono,
                self._check_mostrar_direccion,
                self._check_mostrar_identificador,
            ],
        )
        self._panel_impresoras = self._crear_panel(
            "Impresoras",
            "Impresoras predeterminadas independientes para tickets termicos y reportes PDF en carta.",
            [
                self._crear_bloque_campo_con_accion(
                    "Impresora de comprobantes",
                    self._combo_impresora_comprobantes,
                    "Probar",
                    lambda: self.probar_impresora_comprobantes_solicitado.emit(
                        self._combo_impresora_comprobantes.currentText()
                    ),
                ),
                self._crear_bloque_campo("Ancho de papel termico", self._combo_ancho_termico),
                self._check_corte_termico,
                self._crear_bloque_campo("Codigo de pagina ESC/POS", self._campo_codigo_pagina_termico),
                self._crear_bloque_campo_con_accion(
                    "Impresora de reportes",
                    self._combo_impresora_reportes,
                    "Probar",
                    lambda: self.probar_impresora_reportes_solicitado.emit(
                        self._combo_impresora_reportes.currentText()
                    ),
                ),
            ],
        )
        panel_firma = self._crear_panel(
            "Firma visual",
            "Solo imprime una linea de firma y el texto bajo la linea. No guarda cargos, identificadores ni credenciales.",
            [
                self._check_firma_habilitada,
                self._crear_bloque_campo("Texto bajo la firma", self._campo_firma_texto_linea),
            ],
        )

        panel_preview = self._crear_panel(
            "Vista previa operativa",
            "Referencia visual del comprobante segun la configuracion documental vigente.",
            [self._crear_vista_previa_comprobante()],
        )

        panel_resumen = self._crear_panel(
            "Resumen de emision",
            "Datos reales de la base para pagos y reportes.",
            [
                self._crear_fila_resumen("Total de comprobantes", self._valor_total_comprobantes),
                self._crear_fila_resumen("Proximo correlativo", self._valor_proximo_correlativo),
                self._crear_fila_resumen("Pendientes de impresion", self._valor_pendientes_impresion),
            ],
        )

        boton_guardar = crear_boton_operativo("Guardar documentos y comprobantes", principal=True)
        boton_guardar.clicked.connect(self._emitir_guardado_parametros_factura)

        grilla_secundaria = self._crear_grilla_paneles_compacta(
            ((panel_firma, 2), (panel_resumen, 3))
        )

        contenido = self._crear_contenedor_scroll()
        contenido.widget().layout().addWidget(panel_factura)
        contenido.widget().layout().addLayout(grilla_secundaria)
        contenido.widget().layout().addWidget(panel_preview)
        self._agregar_cierre_tab_compacto(
            contenido,
            (
                "El correlativo no se edita aqui. La firma compartida impacta "
                "comprobantes y documentos de deuda."
            ),
            boton_guardar,
        )
        return contenido

    def _crear_tab_impresoras(self) -> QWidget:
        contenido = self._crear_contenedor_scroll()
        contenido.widget().layout().addWidget(self._panel_impresoras)
        boton_guardar = crear_boton_operativo("Guardar impresoras", principal=True)
        boton_guardar.clicked.connect(self._emitir_guardado_parametros_factura)
        self._agregar_cierre_tab_compacto(
            contenido,
            (
                "Sin impresora termica, el pago queda registrado y el comprobante "
                "permanece pendiente de impresion."
            ),
            boton_guardar,
        )
        return contenido

    def _crear_tab_cobros(self) -> QWidget:
        self._campo_precio_mensual = CampoMontoMonetario()
        self._check_multa_automatica = QCheckBox("Aplicar recargo automatico por cada mes vencido")
        self._check_multa_automatica.toggled.connect(self._actualizar_estado_campos_cobro)
        self._campo_multa_automatica = CampoMontoMonetario()
        self._check_corte_automatico = QCheckBox("Sugerir corte por deuda")
        self._campo_meses_para_corte = QLineEdit()
        self._campo_meses_para_corte.setPlaceholderText("Meses de deuda para alerta o corte")
        self._check_prorrateo_activacion = QCheckBox(
            "Cobrar primera mensualidad prorrateada en conexion y reconexion"
        )
        self._check_pago_adelantado = QCheckBox("Permitir pago adelantado")
        self._check_pago_adelantado.toggled.connect(self._actualizar_estado_campos_cobro)
        self._campo_meses_adelanto_maximo = QLineEdit()
        self._campo_meses_adelanto_maximo.setPlaceholderText("Maximo de meses adelantados")

        panel_precio = self._crear_panel(
            "Precio mensual del servicio",
            "Afecta cargos nuevos. No recalcula deuda historica.",
            [self._crear_bloque_campo("Precio mensual", self._campo_precio_mensual)],
        )
        panel_recargo = self._crear_panel(
            "Recargo automatico",
            "Opcion avanzada por cada mes vencido.",
            [
                self._check_multa_automatica,
                self._crear_bloque_campo(
                    "Monto por mes vencido",
                    self._campo_multa_automatica,
                ),
            ],
        )
        self._panel_corte = self._crear_panel(
            "Sugerencia de corte por deuda",
            "Apoyo operativo. El corte real sigue siendo manual.",
            [
                self._check_corte_automatico,
                self._crear_bloque_campo("Meses vencidos para sugerencia", self._campo_meses_para_corte),
            ],
        )
        panel_adelantos = self._crear_panel(
            "Pago adelantado",
            "Controla pagos de meses futuros.",
            [
                self._check_prorrateo_activacion,
                self._check_pago_adelantado,
                self._crear_bloque_campo("Maximo de meses adelantados", self._campo_meses_adelanto_maximo),
            ],
        )

        boton_guardar = crear_boton_operativo("Guardar parametros de cobro", principal=True)
        boton_guardar.clicked.connect(self._emitir_guardado_parametros_cobro)

        grilla_paneles = QGridLayout()
        grilla_paneles.setContentsMargins(0, 0, 0, 0)
        grilla_paneles.setHorizontalSpacing(12)
        grilla_paneles.setVerticalSpacing(10)
        grilla_paneles.addWidget(panel_precio, 0, 0)
        grilla_paneles.addWidget(panel_recargo, 0, 1)
        grilla_paneles.addWidget(panel_adelantos, 1, 0, 1, 2)
        grilla_paneles.setColumnStretch(0, 1)
        grilla_paneles.setColumnStretch(1, 1)

        contenido = self._crear_contenedor_scroll()
        contenido.widget().layout().addLayout(grilla_paneles)
        self._agregar_cierre_tab_compacto(
            contenido,
            (
                "Impacta Pagos, Casas y Reportes. "
                "La primera mensualidad de conexion y reconexion se controla aqui como politica global de prorrateo."
            ),
            boton_guardar,
        )
        return contenido

    def _crear_tab_morosidad(self) -> QWidget:
        grilla_rangos = QGridLayout()
        grilla_rangos.setContentsMargins(0, 0, 0, 0)
        grilla_rangos.setHorizontalSpacing(10)
        grilla_rangos.setVerticalSpacing(10)
        grilla_rangos.addWidget(
            self._crear_fila_rango_morosidad(
                "Prioridad baja",
                "1-2 meses",
                "Seguimiento normal.",
            ),
            0,
            0,
        )
        grilla_rangos.addWidget(
            self._crear_fila_rango_morosidad(
                "Prioridad media",
                "3-5 meses",
                "Priorizar gestion.",
            ),
            0,
            1,
        )
        grilla_rangos.addWidget(
            self._crear_fila_rango_morosidad(
                "Prioridad alta",
                "6+ meses",
                "Atencion inmediata.",
            ),
            0,
            2,
        )
        grilla_rangos.setColumnStretch(0, 1)
        grilla_rangos.setColumnStretch(1, 1)
        grilla_rangos.setColumnStretch(2, 1)

        panel_rangos = self._crear_panel(
            "Rangos de prioridad",
            "Clasificacion fija segun meses vencidos.",
            [grilla_rangos],
        )
        panel_rangos.setObjectName("panelMorosidadRangos")
        self._panel_corte.setObjectName("panelMorosidadCorte")
        panel_rangos.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Maximum,
        )
        self._panel_corte.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Maximum,
        )
        altura_paneles = max(
            panel_rangos.sizeHint().height(),
            self._panel_corte.sizeHint().height(),
            164,
        )
        panel_rangos.setMinimumHeight(altura_paneles)
        self._panel_corte.setMinimumHeight(altura_paneles)

        grilla_paneles = QGridLayout()
        grilla_paneles.setContentsMargins(0, 0, 0, 0)
        grilla_paneles.setHorizontalSpacing(12)
        grilla_paneles.setVerticalSpacing(10)
        grilla_paneles.addWidget(panel_rangos, 0, 0)
        grilla_paneles.addWidget(self._panel_corte, 0, 1)
        grilla_paneles.setColumnStretch(0, 3)
        grilla_paneles.setColumnStretch(1, 2)

        boton_guardar = crear_boton_operativo("Guardar morosidad", principal=True)
        boton_guardar.clicked.connect(self._emitir_guardado_parametros_cobro)

        aviso = self._crear_aviso_compacto(
            "Los rangos son fijos en esta version. El corte se ejecuta manualmente desde Casas."
        )
        aviso.setObjectName("avisoMorosidadCompacto")

        contenido = self._crear_contenedor_scroll()
        contenido.widget().layout().setSpacing(7)
        contenido.widget().layout().addLayout(grilla_paneles)
        contenido.widget().layout().addWidget(aviso)
        contenido.widget().layout().addWidget(boton_guardar, alignment=Qt.AlignmentFlag.AlignRight)
        contenido.widget().layout().addStretch(1)
        return contenido

    def _crear_tab_reportes_pdf(self) -> QWidget:
        self._ruta_reportes_predeterminada = ""
        self._campo_ruta_reportes_pdf = QLineEdit()
        self._campo_ruta_reportes_pdf.setReadOnly(True)
        self._check_abrir_reportes_pdf = QCheckBox(
            "Abrir reporte automaticamente despues de generarlo"
        )
        self._check_firma_reportes_pdf = QCheckBox(
            "Mostrar linea de firma en reportes"
        )
        self._check_firma_reportes_pdf.toggled.connect(
            self._actualizar_estado_firma_reportes_pdf
        )
        self._campo_firma_reportes_pdf = QLineEdit()
        self._campo_firma_reportes_pdf.setPlaceholderText("Firma autorizada")

        boton_seleccionar = crear_boton_operativo("Seleccionar carpeta")
        boton_seleccionar.clicked.connect(self._seleccionar_carpeta_reportes_pdf)
        boton_restaurar = crear_boton_operativo("Restaurar predeterminada")
        boton_restaurar.clicked.connect(self._restaurar_ruta_reportes_pdf)
        fila_ruta = QHBoxLayout()
        fila_ruta.setSpacing(8)
        fila_ruta.addWidget(self._campo_ruta_reportes_pdf, 1)
        fila_ruta.addWidget(boton_seleccionar)
        fila_ruta.addWidget(boton_restaurar)

        panel_salida = self._crear_panel(
            "Salida de reportes",
            "Carpeta usada por Generar PDF. Guardar en permite elegir otra carpeta solo para una exportacion.",
            [
                self._crear_bloque_campo("Ruta actual", self._envolver_layout(fila_ruta)),
                self._check_abrir_reportes_pdf,
            ],
        )
        panel_firma = self._crear_panel(
            "Firma de reportes",
            "Configuracion independiente de comprobantes termicos y documentos de deuda.",
            [
                self._check_firma_reportes_pdf,
                self._crear_bloque_campo(
                    "Texto bajo la firma",
                    self._campo_firma_reportes_pdf,
                ),
            ],
        )
        boton_guardar = crear_boton_operativo("Guardar reportes PDF", principal=True)
        boton_guardar.clicked.connect(self._emitir_guardado_reportes_pdf)

        grilla_paneles = self._crear_grilla_paneles_compacta(
            ((panel_salida, 3), (panel_firma, 2))
        )

        contenido = self._crear_contenedor_scroll()
        contenido.widget().layout().addLayout(grilla_paneles)
        self._agregar_cierre_tab_compacto(
            contenido,
            (
                "Los reportes se generan bajo demanda. No modifica comprobantes "
                "ESC/POS ni agrega reportes nuevos."
            ),
            boton_guardar,
        )
        self._actualizar_estado_firma_reportes_pdf()
        return contenido

    def _crear_tab_operacion_respaldo(self) -> QWidget:
        self._check_respaldo_secundario = QCheckBox("Guardar tambien una copia secundaria")
        self._check_respaldo_secundario.toggled.connect(self._actualizar_estado_respaldos)
        self._check_comprimir_zip = QCheckBox("Generar ZIP comprimido")
        self._check_organizar_periodo = QCheckBox("Organizar carpetas por ano y mes")
        self._campo_ruta_respaldos_principal = QLineEdit()
        self._campo_ruta_respaldos_secundaria = QLineEdit()
        self._combo_duracion_sesion = QComboBox()
        for etiqueta, valor in self.OPCIONES_DURACION_SESION:
            self._combo_duracion_sesion.addItem(etiqueta, valor)
        self._combo_respaldos_restauracion = QComboBox()
        self._valor_respaldo_automatico = self._crear_valor_seguridad()
        self._valor_ultimo_respaldo = self._crear_valor_seguridad()
        self._valor_estado_respaldo = self._crear_valor_seguridad()
        self._valor_total_respaldos = self._crear_valor_seguridad()
        self._valor_archivo_respaldo = self._crear_valor_seguridad()
        self._valor_tamano_respaldo = self._crear_valor_seguridad()
        self._valor_respaldo_generado_por = self._crear_valor_seguridad()
        self._valor_ruta_respaldos = self._crear_valor_seguridad()
        self._valor_retencion = self._crear_valor_seguridad()
        self._valor_ruta_comprobantes = self._crear_valor_seguridad()
        self._valor_ruta_reportes = self._crear_valor_seguridad()
        self._valor_autenticacion = self._crear_valor_seguridad()
        self._valor_intentos = self._crear_valor_seguridad()
        self._valor_sesion = self._crear_valor_seguridad()
        self._valor_restablecimiento = self._crear_valor_seguridad()
        self._valor_cambio_clave = self._crear_valor_seguridad()

        panel_estado = self._crear_panel(
            "Estado actual",
            "Resumen de respaldo local ejecutado al cerrar sesion o salir del sistema.",
            [
                self._crear_fila_resumen("Respaldo automatico", self._valor_respaldo_automatico),
                self._crear_fila_resumen("Ultimo respaldo", self._valor_ultimo_respaldo),
                self._crear_fila_resumen("Estado del ultimo respaldo", self._valor_estado_respaldo),
                self._crear_fila_resumen("Total de respaldos", self._valor_total_respaldos),
                self._crear_fila_resumen("Archivo generado", self._valor_archivo_respaldo),
                self._crear_fila_resumen("Tamano", self._valor_tamano_respaldo),
                self._crear_fila_resumen("Generado por", self._valor_respaldo_generado_por),
                self._crear_fila_resumen("Carpeta principal", self._valor_ruta_respaldos),
                self._crear_fila_resumen("Retencion", self._valor_retencion),
            ],
        )
        panel_manual = self._crear_panel(
            "Respaldo manual",
            "Genera una copia segura de SQLite con registro interno e historial operativo.",
            [
                self._crear_fila_resumen(
                    "Ruta exportacion comprobantes",
                    self._valor_ruta_comprobantes,
                ),
                self._crear_fila_resumen("Ruta exportacion reportes", self._valor_ruta_reportes),
                self._crear_fila_botones_respaldo(),
            ],
        )
        panel_ubicacion = self._crear_panel(
            "Ubicacion y retencion",
            "Define carpetas de respaldo. La retencion del prototipo conserva automaticamente los 5 respaldos mas recientes.",
            [
                self._crear_bloque_campo_con_accion(
                    "Carpeta principal de respaldos",
                    self._campo_ruta_respaldos_principal,
                    "Seleccionar",
                    self._seleccionar_carpeta_respaldo_principal,
                ),
                self._check_respaldo_secundario,
                self._crear_bloque_campo_con_accion(
                    "Carpeta secundaria opcional",
                    self._campo_ruta_respaldos_secundaria,
                    "Seleccionar",
                    self._seleccionar_carpeta_respaldo_secundaria,
                ),
                self._check_comprimir_zip,
                self._check_organizar_periodo,
            ],
        )
        panel_restauracion = self._crear_panel(
            "Restauracion desde historial",
            "Restaura un respaldo generado por SIGQUA despues de validar archivo, hash e integridad SQLite.",
            [
                self._crear_bloque_campo("Respaldo disponible", self._combo_respaldos_restauracion),
                self._crear_fila_botones_restauracion(),
            ],
        )
        boton_guardar = crear_boton_operativo("Guardar control y respaldo", principal=True)
        boton_guardar.clicked.connect(self._emitir_guardado_respaldo)

        columna_acciones = QVBoxLayout()
        columna_acciones.setContentsMargins(0, 0, 0, 0)
        columna_acciones.setSpacing(10)
        columna_acciones.addWidget(panel_manual)
        columna_acciones.addWidget(panel_restauracion)
        columna_acciones.addStretch(1)

        contenedor_acciones = QWidget()
        contenedor_acciones.setObjectName("columnaPanelesConfiguracion")
        contenedor_acciones.setLayout(columna_acciones)

        grilla_superior = QGridLayout()
        grilla_superior.setContentsMargins(0, 0, 0, 0)
        grilla_superior.setHorizontalSpacing(12)
        grilla_superior.addWidget(panel_estado, 0, 0)
        grilla_superior.addWidget(contenedor_acciones, 0, 1)
        grilla_superior.setColumnStretch(0, 3)
        grilla_superior.setColumnStretch(1, 2)

        contenido = self._crear_contenedor_scroll()
        contenido.widget().layout().addLayout(grilla_superior)
        contenido.widget().layout().addWidget(panel_ubicacion)
        self._agregar_cierre_tab_compacto(
            contenido,
            (
                "La restauracion reemplaza la base local. SIGQUA genera un respaldo "
                "previo y recomienda reiniciar despues de restaurar."
            ),
            boton_guardar,
        )
        return contenido

    def _crear_tab_informacion(self) -> QWidget:
        self._valor_nombre_sistema = self._crear_valor_seguridad()
        self._valor_version_sistema = self._crear_valor_seguridad()
        self._valor_ruta_base = self._crear_valor_seguridad()
        self._valor_ruta_respaldos_activa = self._crear_valor_seguridad()
        self._valor_modo_operacion = self._crear_valor_seguridad()
        self._valor_duracion_sesion_info = self._crear_valor_seguridad()
        self._valor_actualizacion = self._crear_valor_seguridad()
        self._valor_actualizado_por = self._crear_valor_seguridad()
        panel = self._crear_panel(
            "Informacion del sistema",
            "Resumen tecnico legible del entorno local, las rutas activas y la politica vigente.",
            [
                self._crear_fila_resumen("Sistema", self._valor_nombre_sistema),
                self._crear_fila_resumen("Version", self._valor_version_sistema),
                self._crear_fila_resumen("Base de datos", self._valor_ruta_base),
                self._crear_fila_resumen("Carpeta de respaldos", self._valor_ruta_respaldos_activa),
                self._crear_fila_resumen("Modo de operacion", self._valor_modo_operacion),
                self._crear_fila_resumen("Tiempo de sesion", self._valor_duracion_sesion_info),
                self._crear_fila_resumen("Ultima actualizacion", self._valor_actualizacion),
                self._crear_fila_resumen("Actualizado por", self._valor_actualizado_por),
            ],
        )
        panel_seguridad = self._crear_panel(
            "Seguridad local",
            "Reglas activas de autenticacion local y duracion de sesion operativa.",
            [
                self._crear_fila_resumen("Autenticacion", self._valor_autenticacion),
                self._crear_fila_resumen("Intentos maximos", self._valor_intentos),
                self._crear_bloque_campo("Tiempo de cierre automatico de sesion", self._combo_duracion_sesion),
                self._crear_fila_resumen("Duracion actual", self._valor_sesion),
                self._crear_fila_resumen("Restablecimiento", self._valor_restablecimiento),
                self._crear_fila_resumen("Cambio obligatorio de clave", self._valor_cambio_clave),
            ],
        )
        boton_guardar = crear_boton_operativo("Guardar duracion de sesion", principal=True)
        boton_guardar.clicked.connect(
            lambda: self.guardar_duracion_sesion_solicitado.emit(
                float(self._combo_duracion_sesion.currentData() or 8.0)
            )
        )
        grilla_paneles = self._crear_grilla_paneles_compacta(
            ((panel, 3), (panel_seguridad, 2))
        )

        contenido = self._crear_contenedor_scroll()
        contenido.widget().layout().addLayout(grilla_paneles)
        self._agregar_cierre_tab_compacto(
            contenido,
            (
                "Configuracion expone solo parametros reales de operacion, "
                "seguridad local y backend documental."
            ),
            boton_guardar,
        )
        return contenido

    def _crear_vista_previa_comprobante(self) -> QWidget:
        marco = QFrame()
        marco.setObjectName("previewComprobanteConfiguracion")
        layout = QVBoxLayout(marco)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(6)

        encabezado = QLabel("Vista previa del recibo termico")
        encabezado.setObjectName("tituloPreviewConfiguracion")
        self._preview_documento = QTextEdit()
        self._preview_documento.setObjectName("documentoPreviewComprobanteConfiguracion")
        self._preview_documento.setReadOnly(True)
        self._preview_documento.setMinimumHeight(360)
        self._preview_documento.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._preview_documento.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        layout.addWidget(encabezado)
        layout.addWidget(self._preview_documento)
        return marco

    def _actualizar_preview_comprobante(
        self,
        estado: EstadoConfiguracion,
        formateador_moneda: Callable[[int], str],
    ) -> None:
        documento = crear_documento_recibo_termico(
            DatosDocumentoRecibo(
                numero_comprobante=estado.factura.proximo_correlativo,
                configuracion=ConfiguracionDocumentoRecibo(
                    lineas_encabezado=tuple(self._componer_lineas_encabezado_recibo(estado)),
                    titulo_documento=estado.factura.titulo_documento or "RECIBO DE PAGO",
                    subtitulo_documento=estado.factura.subtitulo_documento or "",
                    texto_legal_superior=estado.factura.texto_legal_superior or "",
                    texto_pie=estado.factura.texto_pie or "",
                    texto_legal_inferior=estado.factura.texto_legal_inferior or "",
                    etiqueta_copia=estado.factura.etiqueta_copia or "ORIGINAL",
                    firma_habilitada=estado.factura.firma_habilitada,
                    firma_texto_linea=estado.factura.firma_texto_linea,
                ),
                bloque_comprobante=(
                    ("Proximo recibo", estado.factura.proximo_correlativo),
                    ("Salida", "Ticket termico ESC/POS"),
                    ("Tipo", "Mensualidad"),
                ),
                bloque_servicio=(
                    ("Casa", "CA-000"),
                    ("Abonado", "Vista previa"),
                    ("DNI", "0000000000000"),
                    ("Barrio", "Sin barrio"),
                    ("Direccion", "Configuracion de comprobante"),
                ),
                bloque_operativo=(
                    ("Metodo", "Catalogo activo"),
                    ("Referencia", "No aplica"),
                    ("Registrado por", "Sistema"),
                ),
                detalles=(
                    f"Mensualidad base configurada - {formateador_moneda(estado.parametros_cobro.precio_mensual_centavos)}",
                ),
                total_pagado=formateador_moneda(estado.parametros_cobro.precio_mensual_centavos),
                saldo_posterior=formateador_moneda(0),
            )
        )
        self._preview_documento.setDocument(documento)

    def _componer_lineas_encabezado_recibo(self, estado: EstadoConfiguracion) -> list[str]:
        lineas: list[str] = []
        if estado.identidad_empresa.nombre.strip():
            lineas.append(estado.identidad_empresa.nombre.strip())
        if (
            estado.factura.mostrar_identificador_fiscal
            and estado.identidad_empresa.identificador_fiscal.strip()
        ):
            lineas.append(f"ID fiscal: {estado.identidad_empresa.identificador_fiscal.strip()}")
        if estado.factura.mostrar_telefono and estado.identidad_empresa.telefono.strip():
            lineas.append(estado.identidad_empresa.telefono.strip())
        if estado.factura.mostrar_correo and estado.identidad_empresa.correo.strip():
            lineas.append(estado.identidad_empresa.correo.strip())
        if estado.factura.mostrar_direccion and estado.identidad_empresa.direccion.strip():
            lineas.append(estado.identidad_empresa.direccion.strip())
        if estado.identidad_empresa.sitio_web.strip():
            lineas.append(estado.identidad_empresa.sitio_web.strip())
        if estado.identidad_empresa.mensaje_contacto.strip():
            lineas.append(estado.identidad_empresa.mensaje_contacto.strip())
        return lineas or ["Empresa no configurada"]

    def _emitir_guardado_parametros_cobro(self) -> None:
        multa_automatica = (
            self._campo_multa_automatica.obtener_centavos()
            if self._check_multa_automatica.isChecked()
            else 0
        )
        self.guardar_parametros_cobro_solicitado.emit(
            self._campo_precio_mensual.obtener_centavos(),
            self._check_multa_automatica.isChecked(),
            multa_automatica,
            self._check_corte_automatico.isChecked(),
            self._leer_entero(self._campo_meses_para_corte.text()),
            self._check_prorrateo_activacion.isChecked(),
            self._check_pago_adelantado.isChecked(),
            self._leer_entero(self._campo_meses_adelanto_maximo.text()),
            self.MORA_BAJA_HASTA_VERSION,
            self.MORA_MEDIA_HASTA_VERSION,
        )

    def _actualizar_estado_campos_cobro(self) -> None:
        self._campo_multa_automatica.setEnabled(self._check_multa_automatica.isChecked())
        self._campo_meses_adelanto_maximo.setEnabled(self._check_pago_adelantado.isChecked())

    def _mostrar_ayuda(self) -> None:
        from comun.ui import DialogoMensajeSigqua

        dialogo = DialogoMensajeSigqua(
            titulo="Ayuda de configuracion",
            mensaje=(
                "Esta pantalla administra identidad institucional, documentos, cobro, respaldo local y seguridad operativa. "
                "Los respaldos usan snapshot seguro de SQLite y la restauracion sigue fuera de este modulo."
            ),
            parent=self,
        )
        dialogo.exec()

    def _ocultar_mensaje(self) -> None:
        self._mensaje.clear()
        self._mensaje.setVisible(False)

    def _crear_bloque_campo(self, etiqueta: str, campo: QWidget) -> QWidget:
        bloque = QWidget()
        bloque.setObjectName("bloqueCampoConfiguracion")
        layout = QVBoxLayout(bloque)
        layout.setContentsMargins(0, 1, 0, 1)
        layout.setSpacing(6)
        label = QLabel(etiqueta)
        label.setObjectName("etiquetaConfiguracion")
        layout.addWidget(label)
        layout.addWidget(campo)
        return bloque

    def _crear_combo_impresoras(self) -> QComboBox:
        combo = QComboBox()
        combo.addItem("")
        for impresora in QPrinterInfo.availablePrinters():
            nombre = impresora.printerName()
            if nombre:
                combo.addItem(nombre)
        combo.setEditable(True)
        return combo

    @staticmethod
    def _seleccionar_impresora(combo: QComboBox, nombre: str) -> None:
        nombre = nombre.strip()
        indice = combo.findText(nombre)
        if indice < 0 and nombre:
            combo.addItem(nombre)
            indice = combo.findText(nombre)
        combo.setCurrentIndex(max(0, indice))

    def _resolver_ancho_termico_actual(self) -> int:
        return 58 if "58" in self._combo_ancho_termico.currentText() else 80

    def _crear_bloque_campo_con_accion(
        self,
        etiqueta: str,
        campo: QWidget,
        texto_boton: str,
        callback: Callable[[], None],
    ) -> QWidget:
        contenedor = QWidget()
        contenedor.setObjectName("bloqueCampoConfiguracion")
        layout = QVBoxLayout(contenedor)
        layout.setContentsMargins(0, 1, 0, 1)
        layout.setSpacing(6)
        label = QLabel(etiqueta)
        label.setObjectName("etiquetaConfiguracion")
        fila = QHBoxLayout()
        fila.setContentsMargins(0, 0, 0, 0)
        fila.setSpacing(8)
        boton = crear_boton_operativo(texto_boton)
        boton.setMinimumWidth(120)
        boton.clicked.connect(callback)
        fila.addWidget(campo, 1)
        fila.addWidget(boton)
        layout.addWidget(label)
        layout.addLayout(fila)
        return contenedor

    def _crear_fila_botones_respaldo(self) -> QWidget:
        contenedor = QWidget()
        layout = QHBoxLayout(contenedor)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        boton_crear = crear_boton_operativo("Crear respaldo ahora", principal=True)
        boton_crear.clicked.connect(self.crear_respaldo_manual_solicitado.emit)
        boton_abrir = crear_boton_operativo("Abrir carpeta de respaldos")
        boton_abrir.clicked.connect(self._abrir_carpeta_respaldos)
        layout.addWidget(boton_crear)
        layout.addWidget(boton_abrir)
        layout.addStretch(1)
        return contenedor

    def _crear_fila_botones_restauracion(self) -> QWidget:
        contenedor = QWidget()
        layout = QHBoxLayout(contenedor)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        boton_restaurar = crear_boton_operativo("Restaurar respaldo", principal=True)
        boton_restaurar.clicked.connect(self._confirmar_restauracion_respaldo)
        layout.addWidget(boton_restaurar)
        layout.addStretch(1)
        return contenedor

    def _crear_panel(self, titulo: str, descripcion: str, elementos: list[object]) -> QFrame:
        panel = QFrame()
        panel.setObjectName("panelConfiguracion")
        panel.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Maximum,
        )
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(14, 13, 14, 13)
        layout.setSpacing(8)
        label_titulo = QLabel(titulo)
        label_titulo.setObjectName("tituloPanelConfiguracion")
        label_descripcion = QLabel(descripcion)
        label_descripcion.setObjectName("descripcionPanelConfiguracion")
        label_descripcion.setWordWrap(True)
        layout.addWidget(label_titulo)
        layout.addWidget(label_descripcion)
        for elemento in elementos:
            if isinstance(elemento, QGridLayout):
                layout.addLayout(elemento)
            elif isinstance(elemento, QWidget):
                layout.addWidget(elemento)
        return panel

    def _crear_fila_rango_morosidad(
        self,
        titulo: str,
        rango: str,
        detalle: str,
    ) -> QFrame:
        fila = QFrame()
        fila.setObjectName("bloqueRangoMorosidad")
        layout = QVBoxLayout(fila)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        etiqueta = QLabel(titulo)
        etiqueta.setObjectName("etiquetaRangoMorosidad")
        valor = QLabel(rango)
        valor.setObjectName("valorRangoMorosidad")
        valor.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        descripcion = QLabel(detalle)
        descripcion.setObjectName("detalleRangoMorosidad")
        descripcion.setWordWrap(True)

        layout.addWidget(etiqueta)
        layout.addWidget(valor)
        layout.addWidget(descripcion)
        return fila

    def _crear_aviso(self, texto: str) -> QFrame:
        panel = QFrame()
        panel.setObjectName("avisoConfiguracion")
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)
        etiqueta = QLabel(texto)
        etiqueta.setObjectName("textoAvisoConfiguracion")
        etiqueta.setWordWrap(True)
        layout.addWidget(etiqueta)
        return panel

    def _crear_aviso_compacto(self, texto: str) -> QFrame:
        aviso = self._crear_aviso(texto)
        aviso.setObjectName("avisoConfiguracionCompacto")
        aviso.layout().setContentsMargins(10, 7, 10, 7)
        aviso.layout().setSpacing(6)
        aviso.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )
        return aviso

    def _crear_grilla_paneles_compacta(
        self,
        paneles: tuple[tuple[QFrame, int], ...],
    ) -> QGridLayout:
        grilla = QGridLayout()
        grilla.setContentsMargins(0, 0, 0, 0)
        grilla.setHorizontalSpacing(12)
        grilla.setVerticalSpacing(10)
        for columna, (panel, proporcion) in enumerate(paneles):
            panel.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Maximum,
            )
            grilla.addWidget(panel, 0, columna)
            grilla.setColumnStretch(columna, proporcion)
        return grilla

    def _agregar_cierre_tab_compacto(
        self,
        contenido: QScrollArea,
        texto_aviso: str,
        boton_guardar: QPushButton,
    ) -> None:
        layout = contenido.widget().layout()
        layout.setSpacing(7)
        layout.addWidget(self._crear_aviso_compacto(texto_aviso))
        layout.addWidget(
            boton_guardar,
            alignment=Qt.AlignmentFlag.AlignRight,
        )
        layout.addStretch(1)

    def _crear_contenedor_scroll(self) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setObjectName("scrollConfiguracion")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.viewport().setObjectName("viewportScrollConfiguracion")
        contenedor = QWidget()
        contenedor.setObjectName("contenidoScrollConfiguracion")
        layout = QVBoxLayout(contenedor)
        layout.setContentsMargins(2, 2, 6, 10)
        layout.setSpacing(8)
        scroll.setWidget(contenedor)
        return scroll

    def _crear_valor_seguridad(self) -> QLabel:
        label = QLabel("")
        label.setObjectName("valorResumenConfiguracion")
        label.setWordWrap(True)
        return label

    def _crear_subtitulo_grupo(self, texto: str) -> QLabel:
        """Crea un subtitulo de grupo para separar bloques logicos dentro de un panel."""
        label = QLabel(texto)
        label.setObjectName("subtituloGrupoConfiguracion")
        return label

    def _crear_fila_resumen(self, etiqueta: str, valor: QLabel) -> QWidget:
        fila = QWidget()
        fila.setObjectName("filaResumenConfiguracion")
        layout = QHBoxLayout(fila)
        layout.setContentsMargins(9, 6, 9, 6)
        layout.setSpacing(12)
        label = QLabel(etiqueta)
        label.setObjectName("etiquetaResumenConfiguracion")
        layout.addWidget(label, 1)
        layout.addWidget(valor, 2)
        return fila

    @staticmethod
    def _envolver_layout(layout_origen: QHBoxLayout) -> QWidget:
        contenedor = QWidget()
        contenedor.setLayout(layout_origen)
        return contenedor

    def _emitir_guardado_parametros_factura(self) -> None:
        self.guardar_parametros_factura_solicitado.emit(
            self._campo_titulo_documento.text(),
            self._campo_subtitulo_documento.text(),
            self._campo_texto_legal_superior.toPlainText(),
            self._campo_texto_pie.toPlainText(),
            self._campo_texto_legal_inferior.toPlainText(),
            self._campo_etiqueta_copia.text(),
            self._check_mostrar_correo.isChecked(),
            self._check_mostrar_telefono.isChecked(),
            self._check_mostrar_direccion.isChecked(),
            self._check_mostrar_identificador.isChecked(),
            self._check_firma_habilitada.isChecked(),
            self._campo_firma_texto_linea.text(),
            self._combo_impresora_comprobantes.currentText(),
            self._resolver_ancho_termico_actual(),
            self._check_corte_termico.isChecked(),
            self._campo_codigo_pagina_termico.text(),
            self._combo_impresora_reportes.currentText(),
        )

    def _emitir_guardado_respaldo(self) -> None:
        self.guardar_operacion_respaldo_solicitado.emit(
            self._campo_ruta_respaldos_principal.text().strip(),
            self._campo_ruta_respaldos_secundaria.text().strip(),
            self._check_respaldo_secundario.isChecked(),
            self._check_comprimir_zip.isChecked(),
            self._check_organizar_periodo.isChecked(),
        )

    def _emitir_guardado_reportes_pdf(self) -> None:
        self.guardar_reportes_pdf_solicitado.emit(
            self._campo_ruta_reportes_pdf.text().strip(),
            self._check_abrir_reportes_pdf.isChecked(),
            self._check_firma_reportes_pdf.isChecked(),
            self._campo_firma_reportes_pdf.text().strip(),
        )

    def _seleccionar_carpeta_reportes_pdf(self) -> None:
        ruta = QFileDialog.getExistingDirectory(
            self,
            "Seleccionar carpeta de reportes PDF",
            self._campo_ruta_reportes_pdf.text().strip(),
        )
        if ruta:
            self._campo_ruta_reportes_pdf.setText(ruta)

    def _restaurar_ruta_reportes_pdf(self) -> None:
        self._campo_ruta_reportes_pdf.setText(self._ruta_reportes_predeterminada)

    def _actualizar_estado_firma_reportes_pdf(self) -> None:
        self._campo_firma_reportes_pdf.setEnabled(
            self._check_firma_reportes_pdf.isChecked()
        )

    def _confirmar_restauracion_respaldo(self) -> None:
        respaldo_id = int(self._combo_respaldos_restauracion.currentData() or 0)
        if respaldo_id <= 0:
            self.mostrar_mensaje("No hay respaldos disponibles para restaurar.", es_error=True)
            return
        dialogo = DialogoConfirmacionSigqua(
            titulo="Restaurar respaldo",
            descripcion=(
                "Esta accion reemplazara la base de datos local por el respaldo seleccionado. "
                "SIGQUA creara un respaldo de seguridad antes de restaurar."
            ),
            detalles=(
                ("Respaldo", self._combo_respaldos_restauracion.currentText()),
                ("Reinicio", "Recomendado despues de restaurar"),
            ),
            texto_confirmar="Restaurar",
            variante_confirmar="peligro",
            parent=self,
        )
        if dialogo.exec():
            self.restaurar_respaldo_solicitado.emit(respaldo_id)

    def _actualizar_respaldos_disponibles(self, estado: EstadoConfiguracion) -> None:
        self._combo_respaldos_restauracion.blockSignals(True)
        self._combo_respaldos_restauracion.clear()
        for respaldo in estado.respaldos_disponibles:
            etiqueta = f"{respaldo.generado_en} - {respaldo.nombre_archivo}"
            self._combo_respaldos_restauracion.addItem(etiqueta, respaldo.identificador)
        if self._combo_respaldos_restauracion.count() == 0:
            self._combo_respaldos_restauracion.addItem("Sin respaldos disponibles", 0)
        self._combo_respaldos_restauracion.blockSignals(False)

    def _seleccionar_carpeta_respaldo_principal(self) -> None:
        ruta = QFileDialog.getExistingDirectory(
            self,
            "Seleccionar carpeta principal de respaldos",
            self._campo_ruta_respaldos_principal.text().strip(),
        )
        if ruta:
            self._campo_ruta_respaldos_principal.setText(ruta)

    def _seleccionar_carpeta_respaldo_secundaria(self) -> None:
        ruta = QFileDialog.getExistingDirectory(
            self,
            "Seleccionar carpeta secundaria de respaldos",
            self._campo_ruta_respaldos_secundaria.text().strip(),
        )
        if ruta:
            self._campo_ruta_respaldos_secundaria.setText(ruta)

    def _abrir_carpeta_respaldos(self) -> None:
        ruta = self._campo_ruta_respaldos_principal.text().strip()
        if ruta:
            QDesktopServices.openUrl(QUrl.fromLocalFile(ruta))

    def _actualizar_estado_respaldos(self) -> None:
        self._campo_ruta_respaldos_secundaria.setEnabled(self._check_respaldo_secundario.isChecked())

    def _seleccionar_duracion_sesion(self, duracion_horas: float) -> None:
        for indice in range(self._combo_duracion_sesion.count()):
            valor = float(self._combo_duracion_sesion.itemData(indice) or 0.0)
            if abs(valor - float(duracion_horas)) < 0.001:
                self._combo_duracion_sesion.setCurrentIndex(indice)
                return
        self._combo_duracion_sesion.setCurrentIndex(4)

    @classmethod
    def _texto_duracion_sesion(cls, duracion_horas: float) -> str:
        for etiqueta, valor in cls.OPCIONES_DURACION_SESION:
            if abs(valor - float(duracion_horas)) < 0.001:
                return etiqueta
        return f"{duracion_horas:g} horas"

    @staticmethod
    def _formatear_tamano_bytes(valor: int) -> str:
        if valor <= 0:
            return "0 B"
        unidades = ("B", "KB", "MB", "GB")
        tamano = float(valor)
        indice = 0
        while tamano >= 1024 and indice < len(unidades) - 1:
            tamano /= 1024.0
            indice += 1
        return f"{tamano:,.1f} {unidades[indice]}"

    @staticmethod
    def _resolver_estado_identidad(estado: EstadoConfiguracion) -> str:
        nombre = estado.identidad_empresa.nombre.strip()
        direccion = estado.identidad_empresa.direccion.strip()
        tiene_opcionales = any(
            (
                estado.identidad_empresa.telefono.strip(),
                estado.identidad_empresa.correo.strip(),
                estado.identidad_empresa.identificador_fiscal.strip(),
                estado.identidad_empresa.sitio_web.strip(),
                estado.identidad_empresa.mensaje_contacto.strip(),
            )
        )
        if nombre and direccion and tiene_opcionales:
            return "Completa"
        if nombre or direccion:
            return "Parcial"
        return "Pendiente"

    @staticmethod
    def _leer_entero(texto: str) -> int:
        try:
            return int((texto or "0").strip())
        except ValueError:
            return -1

    @staticmethod
    def _componer_datos_recibo(estado: EstadoConfiguracion) -> str:
        partes: list[str] = []
        if estado.factura.mostrar_telefono and estado.identidad_empresa.telefono:
            partes.append(estado.identidad_empresa.telefono)
        if estado.factura.mostrar_correo and estado.identidad_empresa.correo:
            partes.append(estado.identidad_empresa.correo)
        if estado.factura.mostrar_direccion and estado.identidad_empresa.direccion:
            partes.append(estado.identidad_empresa.direccion)
        if estado.factura.mostrar_identificador_fiscal and estado.identidad_empresa.identificador_fiscal:
            partes.append(f"ID fiscal: {estado.identidad_empresa.identificador_fiscal}")
        if estado.identidad_empresa.sitio_web:
            partes.append(estado.identidad_empresa.sitio_web)
        if estado.identidad_empresa.mensaje_contacto:
            partes.append(estado.identidad_empresa.mensaje_contacto)
        return " | ".join(partes) if partes else "Sin datos complementarios"

    def _aplicar_estilos(self) -> None:
        paleta = self._paleta_tema
        fondo_panel = str(paleta["fondo_superficie_suave"])
        fondo_tarjeta = str(paleta["fondo_superficie"])
        fondo_aviso = str(paleta["fondo_info"])
        fondo_pane = str(paleta["fondo_superficie_muy_suave"])
        fondo_bloque = str(paleta["fondo_superficie_destacada"])
        borde_panel = str(paleta["borde_medio"])
        texto_principal = str(paleta["texto_principal"])
        texto_secundario = str(paleta["texto_secundario"])
        fondo_input = str(paleta["modal_fondo_campo"])
        fondo_input_focus = str(paleta["fondo_input_focus"])
        borde_input = str(paleta["borde_medio"])
        borde_input_focus = str(paleta["borde_foco_input"])
        fondo_tabs = str(paleta["fondo_chip"])
        fondo_tab_barra = str(paleta["fondo_superficie_muy_suave"])
        fondo_tab_hover = str(paleta["fondo_chip_hover"])
        fondo_tab_activo = str(paleta["fondo_chip_activo"])
        texto_tab_activo = str(paleta["texto_chip_activo"])
        borde_tab_activo = str(paleta["borde_chip_activo"])
        self.setStyleSheet(
            f"""
            QWidget#vistaConfiguracion {{
                background: transparent;
            }}
            QLabel#tituloModulo {{
                color: {texto_principal};
                font-size: 19px;
                font-weight: 900;
            }}
            QLabel#descripcionModulo,
            QLabel#descripcionPanelConfiguracion,
            QLabel#detalleTarjetaResumenConfiguracion,
            QLabel#detallePreviewRecibo,
            QLabel#textoAvisoConfiguracion {{
                color: {texto_secundario};
                font-size: 11px;
                font-weight: 600;
            }}
            QLabel#mensajeConfiguracion {{
                color: {paleta['texto_exito']};
                font-size: 12px;
                font-weight: 700;
                padding: 8px 10px;
                border-radius: 12px;
                background-color: {paleta['fondo_exito']};
                border: 1px solid {paleta['borde_exito']};
            }}
            QLabel#mensajeConfiguracion[error="true"] {{
                color: {paleta['texto_error']};
                background-color: {paleta['fondo_error']};
                border: 1px solid {paleta['borde_error']};
            }}
            QFrame#panelConfiguracion {{
                background: {fondo_panel};
                border: 1px solid {borde_panel};
                border-radius: 12px;
            }}
            QFrame#tarjetaResumenConfiguracion {{
                background: {fondo_tarjeta};
                border: 1px solid {paleta["borde_principal"]};
                border-radius: 10px;
            }}
            QFrame#tarjetaResumenConfiguracion:hover {{
                background: {paleta["fondo_superficie_destacada"]};
                border-color: {paleta["borde_foco_input"]};
            }}
            QFrame#avisoConfiguracion {{
                background: {fondo_aviso};
                border: 1px solid {paleta["borde_info"]};
                border-radius: 9px;
            }}
            QFrame#avisoConfiguracionCompacto {{
                background: {fondo_aviso};
                border: 1px solid {paleta["borde_info"]};
                border-radius: 7px;
            }}
            QFrame#avisoConfiguracionCompacto QLabel#textoAvisoConfiguracion {{
                color: {texto_secundario};
                font-size: 10px;
                font-weight: 700;
            }}
            QWidget#bloqueCampoConfiguracion {{
                background: transparent;
                border: none;
            }}
            QWidget#filaResumenConfiguracion {{
                background: {fondo_bloque};
                border: 1px solid {paleta["borde_suave"]};
                border-radius: 8px;
            }}
            QFrame#panelMorosidadRangos,
            QFrame#panelMorosidadCorte {{
                background: {fondo_panel};
                border: 1px solid {borde_panel};
                border-radius: 12px;
            }}
            QFrame#filaRangoMorosidad,
            QFrame#bloqueRangoMorosidad {{
                background: {paleta["fondo_superficie_destacada"]};
                border: 1px solid {paleta["borde_suave"]};
                border-radius: 8px;
            }}
            QFrame#bloqueRangoMorosidad:hover {{
                background: {fondo_tarjeta};
                border-color: {paleta["borde_foco_input"]};
            }}
            QLabel#etiquetaRangoMorosidad {{
                color: {texto_principal};
                font-size: 12px;
                font-weight: 800;
            }}
            QLabel#valorRangoMorosidad {{
                color: {paleta["texto_destacado"]};
                background: transparent;
                border: none;
                padding: 0;
                font-size: 17px;
                font-weight: 900;
            }}
            QLabel#detalleRangoMorosidad {{
                color: {texto_secundario};
                font-size: 11px;
                font-weight: 700;
            }}
            QFrame#avisoMorosidadCompacto {{
                background: {fondo_aviso};
                border: 1px solid {paleta["borde_info"]};
                border-radius: 7px;
            }}
            QFrame#avisoMorosidadCompacto QLabel#textoAvisoConfiguracion {{
                color: {texto_secundario};
                font-size: 10px;
                font-weight: 700;
            }}
            QFrame#previewComprobanteConfiguracion {{
                background: #75C7F0;
                border: 1px solid #1a1a1a;
                border-radius: 8px;
            }}
            QTextEdit#documentoPreviewComprobanteConfiguracion {{
                background: #75C7F0;
                color: #111111;
                border: none;
                padding: 0;
                selection-background-color: #d9d9d9;
            }}
            QLabel#tituloTarjetaResumenOperativa {{
                color: {texto_secundario};
                font-size: 11px;
                font-weight: 700;
            }}
            QLabel#valorTarjetaResumenOperativa,
            QLabel#tituloPreviewRecibo {{
                color: {texto_principal};
                font-size: 20px;
                font-weight: 900;
            }}
            QLabel#tituloDocumentoPreviewRecibo {{
                color: #111111;
                font-size: 16px;
                font-weight: 900;
            }}
            QLabel#tituloPanelConfiguracion,
            QLabel#tituloPreviewConfiguracion {{
                color: {texto_principal};
                font-size: 14px;
                font-weight: 800;
            }}
            QLabel#etiquetaConfiguracion,
            QLabel#etiquetaResumenConfiguracion,
            QLabel#etiquetaPreviewConfiguracion {{
                color: {texto_secundario};
                font-size: 12px;
                font-weight: 700;
            }}
            QLabel#valorResumenConfiguracion,
            QLabel#valorPreviewConfiguracion {{
                color: {texto_principal};
                font-size: 13px;
                font-weight: 800;
            }}
            QLabel#etiquetaCopiaPreviewRecibo {{
                font-size: 11px;
                font-weight: 900;
                letter-spacing: 0.8px;
            }}
            QLineEdit, QPlainTextEdit, QComboBox {{
                border: 1px solid {borde_input};
                border-radius: 8px;
                background: {fondo_input};
                color: {texto_principal};
                padding: 8px 10px;
                font-size: 12px;
                min-height: 18px;
            }}
            QLineEdit:focus, QPlainTextEdit:focus, QComboBox:focus {{
                border: 2px solid {borde_input_focus};
                background: {fondo_input_focus};
            }}
            QLineEdit:disabled, QPlainTextEdit:disabled, QComboBox:disabled {{
                color: {texto_secundario};
                background: {paleta["fondo_superficie_muy_suave"]};
                border-color: {paleta["borde_suave"]};
            }}
            QLineEdit:read-only, QPlainTextEdit:read-only {{
                color: {texto_secundario};
                background: {paleta["fondo_superficie_muy_suave"]};
                border-color: {paleta["borde_suave"]};
            }}
            QComboBox QAbstractItemView {{
                background: {fondo_panel};
                color: {texto_principal};
                border: 1px solid {borde_panel};
                selection-background-color: {fondo_tab_activo};
                selection-color: {texto_tab_activo};
                padding: 4px;
            }}
            QCheckBox {{
                color: {texto_principal};
                font-size: 12px;
                font-weight: 700;
            }}
            QTabWidget#tabsConfiguracion {{
                background: transparent;
            }}
            QTabWidget#tabsConfiguracion::pane {{
                border: 1px solid {borde_panel};
                border-radius: 12px;
                background: {fondo_pane};
                margin-top: 14px;
                padding: 10px 10px 12px 10px;
            }}
            QTabWidget#tabsConfiguracion QTabBar {{
                background: {fondo_tab_barra};
                border: 1px solid {borde_panel};
                border-radius: 16px;
                padding: 6px;
                left: 0px;
            }}
            QTabWidget#tabsConfiguracion QTabBar::tab {{
                background: {fondo_tabs};
                border: 1px solid transparent;
                color: {texto_secundario};
                padding: 10px 16px;
                border-radius: 12px;
                font-size: 12px;
                font-weight: 700;
                margin-right: 6px;
                min-height: 18px;
            }}
            QTabWidget#tabsConfiguracion QTabBar::tab:hover {{
                background: {fondo_tab_hover};
                color: {texto_principal};
            }}
            QTabWidget#tabsConfiguracion QTabBar::tab:selected {{
                background: {fondo_tab_activo};
                color: {texto_tab_activo};
                border: 2px solid {borde_tab_activo};
                padding-top: 11px;
                padding-bottom: 11px;
            }}
            QTabWidget#tabsConfiguracion QTabBar::tab:!selected {{
                margin-top: 2px;
            }}
            QScrollArea#scrollConfiguracion {{
                background: transparent;
                border: none;
            }}
            QWidget#viewportScrollConfiguracion,
            QWidget#contenidoScrollConfiguracion {{
                background: transparent;
                border: none;
            }}
            QScrollBar:vertical {{
                background: transparent;
                width: 10px;
                margin: 4px 0 4px 0;
            }}
            QScrollBar::handle:vertical {{
                background: rgba(202, 214, 238, 0.28);
                min-height: 28px;
                border-radius: 5px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: rgba(202, 214, 238, 0.42);
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
