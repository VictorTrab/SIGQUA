"""Vista PySide6 del modulo de configuracion."""

from __future__ import annotations

from typing import Callable

from PySide6.QtCore import Qt, QTimer, Signal, QUrl
from PySide6.QtGui import QDesktopServices
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
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from comun.ui import (
    BotonAccionContextual,
    CampoMontoMonetario,
    crear_boton_operativo,
)
from comun.ui.comprobante_termico import (
    ConfiguracionDocumentoRecibo,
    DatosDocumentoRecibo,
    crear_documento_recibo_termico,
)
from comun.ui.temas import (
    TEMA_SIGQUA_PREDETERMINADO,
    obtener_fondo_header_destacado,
    obtener_paleta_tema,
    obtener_tema_actual,
    resolver_nombre_tema,
)
from modulos.configuracion.entidades import EstadoConfiguracion


class TarjetaResumenConfiguracion(QFrame):
    """Tarjeta de resumen para configuracion."""

    def __init__(self, titulo: str) -> None:
        super().__init__()
        self.setObjectName("tarjetaResumenConfiguracion")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(4)
        self._titulo = QLabel(titulo)
        self._titulo.setObjectName("tituloTarjetaResumenConfiguracion")
        self._valor = QLabel("")
        self._valor.setObjectName("valorTarjetaResumenConfiguracion")
        self._detalle = QLabel("")
        self._detalle.setObjectName("detalleTarjetaResumenConfiguracion")
        self._detalle.setWordWrap(True)
        layout.addWidget(self._titulo)
        layout.addWidget(self._valor)
        layout.addWidget(self._detalle)

    def actualizar(self, valor: str, detalle: str) -> None:
        self._valor.setText(valor)
        self._detalle.setText(detalle)


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
        str,
        bool,
        bool,
        bool,
        bool,
        bool,
        str,
        bool,
        bool,
    )
    guardar_parametros_cobro_solicitado = Signal(int, bool, int, bool, int, bool, bool, int, int, int)
    guardar_operacion_respaldo_solicitado = Signal(
        str,
        str,
        bool,
        bool,
        bool,
        int,
        float,
    )
    crear_respaldo_manual_solicitado = Signal()

    DURACION_MENSAJE_MS = 3200
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
        self._temporizador_mensaje = QTimer(self)
        self._temporizador_mensaje.setSingleShot(True)
        self._temporizador_mensaje.timeout.connect(self._ocultar_mensaje)
        self._construir_ui()
        self._aplicar_estilos()

    def mostrar_estado(
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
        self._campo_junta_sitio_web.setText(estado.identidad_empresa.sitio_web)
        self._campo_junta_mensaje_contacto.setPlainText(estado.identidad_empresa.mensaje_contacto)
        self._valor_estado_identidad.setText(self._resolver_estado_identidad(estado))

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
        self._combo_formato_salida.setCurrentText(estado.factura.formato_salida)
        self._check_mostrar_correo.setChecked(estado.factura.mostrar_correo)
        self._check_mostrar_telefono.setChecked(estado.factura.mostrar_telefono)
        self._check_mostrar_direccion.setChecked(estado.factura.mostrar_direccion)
        self._check_mostrar_identificador.setChecked(estado.factura.mostrar_identificador_fiscal)
        self._check_firma_habilitada.setChecked(estado.factura.firma_habilitada)
        self._check_abrir_pdf_automatico.setChecked(estado.factura.abrir_pdf_automaticamente)
        self._check_imprimir_pdf_automatico.setChecked(estado.factura.imprimir_pdf_automaticamente)
        self._campo_firma_texto_linea.setText(estado.factura.firma_texto_linea)
        self._valor_total_comprobantes.setText(str(estado.factura.total_comprobantes_emitidos))
        self._valor_proximo_correlativo.setText(estado.factura.proximo_correlativo)

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
        self._campo_mora_leve_hasta.setText(str(estado.parametros_cobro.mora_leve_hasta_meses))
        self._campo_mora_media_hasta.setText(str(estado.parametros_cobro.mora_media_hasta_meses))
        self._valor_mora_regla.setText(
            "La mora sigue visible como meses vencidos no pagados."
            if estado.parametros_cobro.mora_visible
            else "No aplica a esta version."
        )
        self._valor_rangos_mora.setText(
            f"Prioridad baja: 1-{estado.parametros_cobro.mora_leve_hasta_meses} | "
            f"Prioridad media: {estado.parametros_cobro.mora_leve_hasta_meses + 1}-{estado.parametros_cobro.mora_media_hasta_meses} | "
            f"Prioridad alta: {estado.parametros_cobro.mora_media_hasta_meses + 1}+"
        )
        self._actualizar_estado_campos_cobro()

        self._campo_ruta_respaldos_principal.setText(estado.operacion.ruta_respaldos_principal)
        self._campo_ruta_respaldos_secundaria.setText(estado.operacion.ruta_respaldos_secundaria)
        self._check_respaldo_secundario.blockSignals(True)
        self._check_respaldo_secundario.setChecked(estado.operacion.respaldo_secundario_activo)
        self._check_respaldo_secundario.blockSignals(False)
        self._check_comprimir_zip.setChecked(estado.operacion.comprimir_zip)
        self._check_organizar_periodo.setChecked(estado.operacion.organizar_por_periodo)
        self._campo_retencion_dias.setText(str(estado.operacion.retencion_dias))
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
        self._valor_retencion.setText(f"{estado.operacion.retencion_dias} dias")
        self._valor_ruta_comprobantes.setText(estado.operacion.ruta_exportaciones_comprobantes)
        self._valor_ruta_reportes.setText(estado.operacion.ruta_exportaciones_reportes)

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
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

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

        tarjetas = QGridLayout()
        tarjetas.setHorizontalSpacing(10)
        tarjetas.setVerticalSpacing(10)
        self._tarjeta_precio = TarjetaResumenConfiguracion("Precio mensual")
        self._tarjeta_correlativo = TarjetaResumenConfiguracion("Proximo recibo")
        self._tarjeta_adelantos = TarjetaResumenConfiguracion("Pago adelantado")
        self._tarjeta_respaldo = TarjetaResumenConfiguracion("Respaldo automatico")
        tarjetas.addWidget(self._tarjeta_precio, 0, 0)
        tarjetas.addWidget(self._tarjeta_correlativo, 0, 1)
        tarjetas.addWidget(self._tarjeta_adelantos, 0, 2)
        tarjetas.addWidget(self._tarjeta_respaldo, 0, 3)

        self._tabs = QTabWidget()
        self._tabs.setObjectName("tabsConfiguracion")
        self._tabs.addTab(self._crear_tab_datos_junta(), "Organización")
        self._tabs.addTab(self._crear_tab_factura(), "Comprobantes")
        self._tabs.addTab(self._crear_tab_parametros_cobro(), "Cobros y morosidad")
        self._tabs.addTab(self._crear_tab_operacion_respaldo(), "Respaldos")
        self._tabs.addTab(self._crear_tab_informacion(), "Sistema")

        layout.addLayout(encabezado)
        layout.addWidget(self._mensaje)
        layout.addLayout(tarjetas)
        layout.addWidget(self._tabs, 1)

    def _crear_tab_datos_junta(self) -> QWidget:
        self._campo_junta_nombre = QLineEdit()
        self._campo_junta_telefono = QLineEdit()
        self._campo_junta_correo = QLineEdit()
        self._campo_junta_identificador = QLineEdit()
        self._campo_junta_sitio_web = QLineEdit()
        self._campo_junta_direccion = QPlainTextEdit()
        self._campo_junta_direccion.setFixedHeight(90)
        self._campo_junta_mensaje_contacto = QPlainTextEdit()
        self._campo_junta_mensaje_contacto.setFixedHeight(76)

        grilla = QGridLayout()
        grilla.setHorizontalSpacing(12)
        grilla.setVerticalSpacing(12)
        self._valor_estado_identidad = self._crear_valor_seguridad()
        grilla.addWidget(
            self._crear_bloque_campo("Nombre legal o comercial", self._campo_junta_nombre),
            0,
            0,
            1,
            2,
        )
        grilla.addWidget(
            self._crear_bloque_campo("Telefono institucional", self._campo_junta_telefono),
            1,
            0,
        )
        grilla.addWidget(
            self._crear_bloque_campo("Correo institucional", self._campo_junta_correo),
            1,
            1,
        )
        grilla.addWidget(self._crear_bloque_campo("Identificador fiscal", self._campo_junta_identificador), 2, 0)
        grilla.addWidget(self._crear_bloque_campo("Sitio web", self._campo_junta_sitio_web), 2, 1)
        grilla.addWidget(
            self._crear_bloque_campo("Direccion fiscal u operativa", self._campo_junta_direccion),
            3,
            0,
            1,
            2,
        )
        grilla.addWidget(
            self._crear_bloque_campo("Mensaje de contacto", self._campo_junta_mensaje_contacto),
            4,
            0,
            1,
            2,
        )

        boton_guardar = crear_boton_operativo("Guardar identidad de la empresa", principal=True)
        boton_guardar.clicked.connect(
            lambda: self.guardar_datos_junta_solicitado.emit(
                self._campo_junta_nombre.text(),
                self._campo_junta_telefono.text(),
                self._campo_junta_correo.text(),
                self._campo_junta_direccion.toPlainText(),
                self._campo_junta_identificador.text(),
                self._campo_junta_sitio_web.text(),
                self._campo_junta_mensaje_contacto.toPlainText(),
            )
        )

        contenido = self._crear_contenedor_scroll()
        contenido.widget().layout().addWidget(
            self._crear_panel(
                "Identidad de la empresa",
                "Datos visibles en comprobantes, reportes PDF, documentos de deuda y cabeceras operativas.",
                [self._crear_fila_resumen("Estado actual", self._valor_estado_identidad), grilla],
            )
        )
        contenido.widget().layout().addWidget(
            self._crear_aviso(
                "Impacta comprobantes, reportes PDF, documentos de deuda y vistas operativas. "
                "No crea reglas nuevas: solo actualiza la identidad visible de la empresa."
            )
        )
        contenido.widget().layout().addWidget(boton_guardar, alignment=Qt.AlignmentFlag.AlignRight)
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
        self._combo_formato_salida = QComboBox()
        self._combo_formato_salida.addItem("PDF")
        self._combo_formato_salida.setEnabled(False)
        self._check_mostrar_correo = QCheckBox("Mostrar correo institucional")
        self._check_mostrar_telefono = QCheckBox("Mostrar telefono institucional")
        self._check_mostrar_direccion = QCheckBox("Mostrar direccion institucional")
        self._check_mostrar_identificador = QCheckBox("Mostrar identificador fiscal")
        self._check_firma_habilitada = QCheckBox("Mostrar línea de firma en documentos")
        self._check_abrir_pdf_automatico = QCheckBox(
            "Abrir automaticamente el comprobante PDF al registrar un pago"
        )
        self._check_imprimir_pdf_automatico = QCheckBox(
            "Enviar automaticamente el comprobante PDF a impresion"
        )
        self._campo_firma_texto_linea = QLineEdit()
        self._campo_firma_texto_linea.setPlaceholderText("Firma autorizada")
        self._valor_total_comprobantes = self._crear_valor_seguridad()
        self._valor_proximo_correlativo = self._crear_valor_seguridad()

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
                self._crear_bloque_campo("Subtitulo del documento", self._campo_subtitulo_documento),
                self._crear_bloque_campo("Texto legal superior", self._campo_texto_legal_superior),
                self._crear_bloque_campo("Texto inferior", self._campo_texto_pie),
                self._crear_bloque_campo("Texto legal inferior", self._campo_texto_legal_inferior),
                self._crear_bloque_campo("Etiqueta de copia", self._campo_etiqueta_copia),
                self._check_mostrar_correo,
                self._check_mostrar_telefono,
                self._check_mostrar_direccion,
                self._check_mostrar_identificador,
                self._check_abrir_pdf_automatico,
                self._check_imprimir_pdf_automatico,
                self._crear_bloque_campo("Formato de salida", self._combo_formato_salida),
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
            ],
        )

        boton_guardar = crear_boton_operativo("Guardar documentos y comprobantes", principal=True)
        boton_guardar.clicked.connect(
            lambda: self.guardar_parametros_factura_solicitado.emit(
                self._campo_titulo_documento.text(),
                self._campo_subtitulo_documento.text(),
                self._campo_texto_legal_superior.toPlainText(),
                self._campo_texto_pie.toPlainText(),
                self._campo_texto_legal_inferior.toPlainText(),
                self._campo_etiqueta_copia.text(),
                self._combo_formato_salida.currentText(),
                self._check_mostrar_correo.isChecked(),
                self._check_mostrar_telefono.isChecked(),
                self._check_mostrar_direccion.isChecked(),
                self._check_mostrar_identificador.isChecked(),
                self._check_firma_habilitada.isChecked(),
                self._campo_firma_texto_linea.text(),
                self._check_abrir_pdf_automatico.isChecked(),
                self._check_imprimir_pdf_automatico.isChecked(),
            )
        )

        contenido = self._crear_contenedor_scroll()
        contenido.widget().layout().addWidget(panel_factura)
        contenido.widget().layout().addWidget(panel_firma)
        contenido.widget().layout().addWidget(panel_preview)
        contenido.widget().layout().addWidget(panel_resumen)
        contenido.widget().layout().addWidget(
            self._crear_aviso(
                "El correlativo no se edita aqui. La firma compartida impacta comprobantes y documentos de deuda."
            )
        )
        contenido.widget().layout().addWidget(boton_guardar, alignment=Qt.AlignmentFlag.AlignRight)
        return contenido

    def _crear_tab_parametros_cobro(self) -> QWidget:
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
        self._valor_mora_regla = self._crear_valor_seguridad()
        self._valor_rangos_mora = self._crear_valor_seguridad()
        self._campo_mora_leve_hasta = QLineEdit()
        self._campo_mora_leve_hasta.setPlaceholderText("Hasta cuantos meses mantiene prioridad baja")
        self._campo_mora_media_hasta = QLineEdit()
        self._campo_mora_media_hasta.setPlaceholderText("Hasta cuantos meses mantiene prioridad media")

        panel_precio = self._crear_panel(
            "Precio mensual del servicio",
            "Segun la regla cerrada, el cambio de tarifa solo afecta cargos nuevos. Nunca recalcula deuda historica.",
            [self._crear_bloque_campo("Precio mensual", self._campo_precio_mensual)],
        )
        panel_mora = self._crear_panel(
            "Mora y recargo automatico",
            "La mora sigue existiendo como meses vencidos no pagados. Aqui solo parametrizas el recargo automatico adicional.",
            [
                self._crear_fila_resumen("Regla de mora", self._valor_mora_regla),
                self._crear_fila_resumen("Rangos visuales vigentes", self._valor_rangos_mora),
                self._check_multa_automatica,
                self._crear_bloque_campo(
                    "Monto del recargo automatico por mes vencido",
                    self._campo_multa_automatica,
                ),
                self._crear_bloque_campo(
                    "Prioridad baja hasta (meses)",
                    self._campo_mora_leve_hasta,
                ),
                self._crear_bloque_campo(
                    "Prioridad media hasta (meses)",
                    self._campo_mora_media_hasta,
                ),
            ],
        )
        panel_corte = self._crear_panel(
            "Corte y alertas por deuda",
            "Control global que afecta diagnostico de casas, morosidad y decision operativa del soporte.",
            [
                self._check_corte_automatico,
                self._crear_bloque_campo("Meses vencidos para sugerir corte", self._campo_meses_para_corte),
            ],
        )
        panel_adelantos = self._crear_panel(
            "Pago adelantado",
            "Permite controlar si pagos puede registrar meses futuros y hasta donde, sin anular las reglas de deuda vencida.",
            [
                self._check_prorrateo_activacion,
                self._check_pago_adelantado,
                self._crear_bloque_campo("Maximo de meses adelantados", self._campo_meses_adelanto_maximo),
            ],
        )

        boton_guardar = crear_boton_operativo("Guardar parametros de cobro", principal=True)
        boton_guardar.clicked.connect(self._emitir_guardado_parametros_cobro)

        grilla_paneles = QGridLayout()
        grilla_paneles.setHorizontalSpacing(12)
        grilla_paneles.setVerticalSpacing(12)
        grilla_paneles.addWidget(panel_precio, 0, 0)
        grilla_paneles.addWidget(panel_mora, 0, 1)
        grilla_paneles.addWidget(panel_corte, 1, 0)
        grilla_paneles.addWidget(panel_adelantos, 1, 1)

        contenido = self._crear_contenedor_scroll()
        contenido.widget().layout().addLayout(grilla_paneles)
        contenido.widget().layout().addWidget(
            self._crear_aviso(
                "Impacta Pagos, Morosidad, Casas y Reportes. "
                "La primera mensualidad de conexion y reconexion se controla aqui como politica global de prorrateo."
            )
        )
        contenido.widget().layout().addWidget(boton_guardar, alignment=Qt.AlignmentFlag.AlignRight)
        return contenido

    def _crear_tab_operacion_respaldo(self) -> QWidget:
        self._check_respaldo_secundario = QCheckBox("Guardar tambien una copia secundaria")
        self._check_respaldo_secundario.toggled.connect(self._actualizar_estado_respaldos)
        self._check_comprimir_zip = QCheckBox("Generar ZIP comprimido")
        self._check_organizar_periodo = QCheckBox("Organizar carpetas por ano y mes")
        self._campo_ruta_respaldos_principal = QLineEdit()
        self._campo_ruta_respaldos_secundaria = QLineEdit()
        self._campo_retencion_dias = QLineEdit()
        self._combo_duracion_sesion = QComboBox()
        for etiqueta, valor in self.OPCIONES_DURACION_SESION:
            self._combo_duracion_sesion.addItem(etiqueta, valor)
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
            "Define la carpeta principal, la copia secundaria y la politica de conservacion.",
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
                self._crear_bloque_campo("Retencion en dias", self._campo_retencion_dias),
            ],
        )
        panel_seguridad = self._crear_panel(
            "Politica de seguridad operativa",
            "Resumen de reglas activas y configuracion del cierre automatico de sesion.",
            [
                self._crear_fila_resumen("Autenticacion", self._valor_autenticacion),
                self._crear_fila_resumen("Intentos maximos", self._valor_intentos),
                self._crear_bloque_campo("Tiempo de cierre automatico de sesion", self._combo_duracion_sesion),
                self._crear_fila_resumen("Duracion actual", self._valor_sesion),
                self._crear_fila_resumen("Restablecimiento", self._valor_restablecimiento),
                self._crear_fila_resumen("Cambio obligatorio de clave", self._valor_cambio_clave),
            ],
        )
        boton_guardar = crear_boton_operativo("Guardar control y respaldo", principal=True)
        boton_guardar.clicked.connect(self._emitir_guardado_respaldo)

        grilla = QGridLayout()
        grilla.setHorizontalSpacing(12)
        grilla.setVerticalSpacing(12)
        grilla.addWidget(panel_estado, 0, 0)
        grilla.addWidget(panel_manual, 0, 1)
        grilla.addWidget(panel_ubicacion, 1, 0, 1, 2)
        grilla.addWidget(panel_seguridad, 2, 0, 1, 2)

        contenido = self._crear_contenedor_scroll()
        contenido.widget().layout().addLayout(grilla)
        contenido.widget().layout().addWidget(
            self._crear_aviso(
                "La restauracion sigue fuera de esta pantalla. Aqui configuras carpetas y ejecutas respaldos locales seguros."
            )
        )
        contenido.widget().layout().addWidget(boton_guardar, alignment=Qt.AlignmentFlag.AlignRight)
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
        contenido = self._crear_contenedor_scroll()
        contenido.widget().layout().addWidget(panel)
        contenido.widget().layout().addWidget(
            self._crear_aviso(
                "Configuracion expone solo parametros reales de operacion, seguridad local y backend documental."
            )
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
                    ("Formato", estado.factura.formato_salida),
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
            self._leer_entero(self._campo_mora_leve_hasta.text()),
            self._leer_entero(self._campo_mora_media_hasta.text()),
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
        layout = QVBoxLayout(bloque)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        label = QLabel(etiqueta)
        label.setObjectName("etiquetaConfiguracion")
        layout.addWidget(label)
        layout.addWidget(campo)
        return bloque

    def _crear_bloque_campo_con_accion(
        self,
        etiqueta: str,
        campo: QWidget,
        texto_boton: str,
        callback: Callable[[], None],
    ) -> QWidget:
        contenedor = QWidget()
        layout = QVBoxLayout(contenedor)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
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

    def _crear_panel(self, titulo: str, descripcion: str, elementos: list[object]) -> QFrame:
        panel = QFrame()
        panel.setObjectName("panelConfiguracion")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(14, 14, 14, 14)
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

    def _crear_contenedor_scroll(self) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setObjectName("scrollConfiguracion")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        contenedor = QWidget()
        layout = QVBoxLayout(contenedor)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        scroll.setWidget(contenedor)
        return scroll

    def _crear_valor_seguridad(self) -> QLabel:
        label = QLabel("")
        label.setObjectName("valorResumenConfiguracion")
        label.setWordWrap(True)
        return label

    def _crear_fila_resumen(self, etiqueta: str, valor: QLabel) -> QWidget:
        fila = QWidget()
        layout = QHBoxLayout(fila)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        label = QLabel(etiqueta)
        label.setObjectName("etiquetaResumenConfiguracion")
        layout.addWidget(label, 1)
        layout.addWidget(valor, 2)
        return fila

    def _emitir_guardado_respaldo(self) -> None:
        self.guardar_operacion_respaldo_solicitado.emit(
            self._campo_ruta_respaldos_principal.text().strip(),
            self._campo_ruta_respaldos_secundaria.text().strip(),
            self._check_respaldo_secundario.isChecked(),
            self._check_comprimir_zip.isChecked(),
            self._check_organizar_periodo.isChecked(),
            self._leer_entero(self._campo_retencion_dias.text()),
            float(self._combo_duracion_sesion.currentData() or 8.0),
        )

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
        fondo_panel = obtener_fondo_header_destacado(self._tema_actual)
        borde_panel = str(paleta["borde_principal"])
        texto_principal = str(paleta["texto_principal"])
        texto_secundario = str(paleta["texto_secundario"])
        fondo_input = str(paleta["fondo_input"])
        borde_input = str(paleta["borde_medio"])
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
            QFrame#tarjetaResumenConfiguracion,
            QFrame#panelConfiguracion,
            QFrame#avisoConfiguracion {{
                background: {fondo_panel};
                border: 1px solid {borde_panel};
                border-radius: 18px;
            }}
            QFrame#previewComprobanteConfiguracion {{
                background: #E4EACC;
                border: 1px solid #1a1a1a;
                border-radius: 8px;
            }}
            QTextEdit#documentoPreviewComprobanteConfiguracion {{
                background: #E4EACC;
                color: #111111;
                border: none;
                padding: 0;
                selection-background-color: #d9d9d9;
            }}
            QLabel#tituloTarjetaResumenConfiguracion {{
                color: {texto_secundario};
                font-size: 11px;
                font-weight: 700;
            }}
            QLabel#valorTarjetaResumenConfiguracion,
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
                border-radius: 12px;
                background: {fondo_input};
                color: {texto_principal};
                padding: 8px 10px;
                font-size: 12px;
                min-height: 18px;
            }}
            QLineEdit:disabled, QPlainTextEdit:disabled, QComboBox:disabled {{
                color: {texto_secundario};
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
                border-radius: 18px;
                background: {fondo_panel};
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
            QScrollArea#scrollConfiguracion QWidget {{
                background: transparent;
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
