"""Vista PySide6 del modulo de configuracion."""

from __future__ import annotations

from typing import Callable

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
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

from comun.ui import BotonAccionContextual, crear_boton_operativo
from comun.ui.comprobante_termico import (
    ConfiguracionDocumentoRecibo,
    DatosDocumentoRecibo,
    crear_documento_recibo_termico,
)
from comun.ui.temas import TEMA_SICAP_PREDETERMINADO, obtener_paleta_tema, obtener_tema_actual
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
    )
    guardar_parametros_cobro_solicitado = Signal(int, bool, int, bool, int, bool, int, int, int)
    guardar_operacion_respaldo_solicitado = Signal(bool)

    DURACION_MENSAJE_MS = 3200

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
            "Activo" if estado.operacion.respaldo_automatico else "Inactivo",
            (
                f"Ultimo: {estado.operacion.ultimo_respaldo_en}."
                if estado.operacion.ultimo_respaldo_en
                else "Sin respaldos registrados."
            ),
        )

        self._campo_junta_nombre.setText(estado.datos_junta.nombre)
        self._campo_junta_telefono.setText(estado.datos_junta.telefono)
        self._campo_junta_correo.setText(estado.datos_junta.correo)
        self._campo_junta_direccion.setPlainText(estado.datos_junta.direccion)
        self._campo_junta_identificador.setText(estado.datos_junta.identificador_fiscal)
        self._campo_junta_sitio_web.setText(estado.datos_junta.sitio_web)
        self._campo_junta_mensaje_contacto.setPlainText(estado.datos_junta.mensaje_contacto)

        self._campo_factura_nombre.setText(estado.datos_junta.nombre)
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
        self._valor_total_comprobantes.setText(str(estado.factura.total_comprobantes_emitidos))
        self._valor_proximo_correlativo.setText(estado.factura.proximo_correlativo)

        self._campo_precio_mensual.setText(str(estado.parametros_cobro.precio_mensual_centavos))
        self._check_multa_automatica.blockSignals(True)
        self._check_multa_automatica.setChecked(estado.parametros_cobro.multa_mora_automatica_activa)
        self._check_multa_automatica.blockSignals(False)
        self._campo_multa_automatica.setText(
            str(estado.parametros_cobro.multa_mora_automatica_centavos)
        )
        self._check_corte_automatico.blockSignals(True)
        self._check_corte_automatico.setChecked(estado.parametros_cobro.corte_automatico_activo)
        self._check_corte_automatico.blockSignals(False)
        self._campo_meses_para_corte.setText(str(estado.parametros_cobro.meses_para_corte))
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
            f"Leve: 1-{estado.parametros_cobro.mora_leve_hasta_meses} | "
            f"Media: {estado.parametros_cobro.mora_leve_hasta_meses + 1}-{estado.parametros_cobro.mora_media_hasta_meses} | "
            f"Severa: {estado.parametros_cobro.mora_media_hasta_meses + 1}+"
        )
        self._actualizar_estado_campos_cobro()

        self._check_respaldo_automatico.blockSignals(True)
        self._check_respaldo_automatico.setChecked(estado.operacion.respaldo_automatico)
        self._check_respaldo_automatico.blockSignals(False)
        self._valor_ultimo_respaldo.setText(
            estado.operacion.ultimo_respaldo_en or "Sin registros"
        )
        self._valor_estado_respaldo.setText(estado.operacion.ultimo_respaldo_estado)
        self._valor_total_respaldos.setText(str(estado.operacion.total_respaldos))
        self._valor_ruta_comprobantes.setText(estado.operacion.ruta_exportaciones_comprobantes)
        self._valor_ruta_reportes.setText(estado.operacion.ruta_exportaciones_reportes)

        self._valor_autenticacion.setText("Local")
        self._valor_intentos.setText(str(estado.seguridad.maximo_intentos_fallidos))
        self._valor_sesion.setText(f"{estado.seguridad.duracion_sesion_horas} horas")
        self._valor_restablecimiento.setText("Administrativo")
        self._valor_cambio_clave.setText("Obligatorio cuando hay clave temporal")

        self._valor_nombre_sistema.setText(estado.informacion.nombre_sistema)
        self._valor_version_sistema.setText(estado.informacion.version_sistema or "Sin version")
        self._valor_ruta_base.setText(estado.informacion.ruta_base_datos)
        self._valor_modo_operacion.setText(estado.informacion.modo_operacion)
        self._valor_actualizacion.setText(estado.informacion.ultima_actualizacion or "Sin registro")

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
        self._tema_actual = nombre_tema if nombre_tema in ("oscuro", "claro") else TEMA_SICAP_PREDETERMINADO
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
        boton_info = BotonAccionContextual("Informacion", variante="ayuda", centrado=True, mostrar_icono=False)
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
        self._tarjeta_precio = TarjetaResumenConfiguracion("Precio actual servicio")
        self._tarjeta_correlativo = TarjetaResumenConfiguracion("Correlativo global")
        self._tarjeta_adelantos = TarjetaResumenConfiguracion("Pago adelantado")
        self._tarjeta_respaldo = TarjetaResumenConfiguracion("Respaldo automatico")
        tarjetas.addWidget(self._tarjeta_precio, 0, 0)
        tarjetas.addWidget(self._tarjeta_correlativo, 0, 1)
        tarjetas.addWidget(self._tarjeta_adelantos, 0, 2)
        tarjetas.addWidget(self._tarjeta_respaldo, 0, 3)

        self._tabs = QTabWidget()
        self._tabs.setObjectName("tabsConfiguracion")
        self._tabs.addTab(self._crear_tab_datos_junta(), "Datos de la junta")
        self._tabs.addTab(self._crear_tab_factura(), "Factura y comprobantes")
        self._tabs.addTab(self._crear_tab_parametros_cobro(), "Parametros de cobro")
        self._tabs.addTab(self._crear_tab_operacion_respaldo(), "Control y respaldo")
        self._tabs.addTab(self._crear_tab_informacion(), "Informacion")

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
        grilla.addWidget(self._crear_bloque_campo("Nombre de la junta", self._campo_junta_nombre), 0, 0, 1, 2)
        grilla.addWidget(self._crear_bloque_campo("Telefono", self._campo_junta_telefono), 1, 0)
        grilla.addWidget(self._crear_bloque_campo("Correo", self._campo_junta_correo), 1, 1)
        grilla.addWidget(self._crear_bloque_campo("Identificador fiscal", self._campo_junta_identificador), 2, 0)
        grilla.addWidget(self._crear_bloque_campo("Sitio web", self._campo_junta_sitio_web), 2, 1)
        grilla.addWidget(self._crear_bloque_campo("Direccion", self._campo_junta_direccion), 3, 0, 1, 2)
        grilla.addWidget(
            self._crear_bloque_campo("Mensaje de contacto", self._campo_junta_mensaje_contacto),
            4,
            0,
            1,
            2,
        )

        boton_guardar = crear_boton_operativo("Guardar datos de la junta", principal=True)
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
                "Datos institucionales",
                "Identidad visible en comprobantes, reportes y cabeceras operativas del sistema.",
                [grilla],
            )
        )
        contenido.widget().layout().addWidget(
            self._crear_aviso(
                "Impacta Pagos, Reportes y la vista previa de comprobantes. "
                "No crea reglas nuevas: solo cambia los datos visibles de la junta."
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
        self._combo_formato_salida.addItems(["HTML", "TEXTO", "PDF"])
        self._check_mostrar_correo = QCheckBox("Mostrar correo institucional")
        self._check_mostrar_telefono = QCheckBox("Mostrar telefono institucional")
        self._check_mostrar_direccion = QCheckBox("Mostrar direccion institucional")
        self._check_mostrar_identificador = QCheckBox("Mostrar identificador fiscal")
        self._valor_total_comprobantes = self._crear_valor_seguridad()
        self._valor_proximo_correlativo = self._crear_valor_seguridad()

        grilla_superior = QGridLayout()
        grilla_superior.setHorizontalSpacing(12)
        grilla_superior.setVerticalSpacing(12)
        grilla_superior.addWidget(
            self._crear_bloque_campo("Nombre visible de la junta", self._campo_factura_nombre),
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
            "Recibo y comprobantes",
            "Configuracion operativa del recibo termico monocromatico usado por el flujo real de pagos.",
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
                self._crear_bloque_campo("Formato de salida", self._combo_formato_salida),
            ],
        )

        panel_preview = self._crear_panel(
            "Vista previa operativa",
            "Referencia visual basada en el flujo de pagos y el correlativo global vigente.",
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

        boton_guardar = crear_boton_operativo("Guardar comprobantes", principal=True)
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
            )
        )

        contenido = self._crear_contenedor_scroll()
        contenido.widget().layout().addWidget(panel_factura)
        contenido.widget().layout().addWidget(panel_preview)
        contenido.widget().layout().addWidget(panel_resumen)
        contenido.widget().layout().addWidget(
            self._crear_aviso(
                "El numero del comprobante no se edita aqui. Lo gobierna el correlativo global creado en pagos."
            )
        )
        contenido.widget().layout().addWidget(boton_guardar, alignment=Qt.AlignmentFlag.AlignRight)
        return contenido

    def _crear_tab_parametros_cobro(self) -> QWidget:
        self._campo_precio_mensual = QLineEdit()
        self._campo_precio_mensual.setPlaceholderText("Centavos, por ejemplo 2500 para L 25.00")
        self._check_multa_automatica = QCheckBox("Aplicar recargo automatico por cada mes vencido")
        self._check_multa_automatica.toggled.connect(self._actualizar_estado_campos_cobro)
        self._campo_multa_automatica = QLineEdit()
        self._campo_multa_automatica.setPlaceholderText("Centavos del recargo adicional")
        self._check_corte_automatico = QCheckBox("Permitir corte automatico por deuda")
        self._campo_meses_para_corte = QLineEdit()
        self._campo_meses_para_corte.setPlaceholderText("Meses de deuda para alerta o corte")
        self._check_pago_adelantado = QCheckBox("Permitir pago adelantado")
        self._check_pago_adelantado.toggled.connect(self._actualizar_estado_campos_cobro)
        self._campo_meses_adelanto_maximo = QLineEdit()
        self._campo_meses_adelanto_maximo.setPlaceholderText("Maximo de meses adelantados")
        self._valor_mora_regla = self._crear_valor_seguridad()
        self._valor_rangos_mora = self._crear_valor_seguridad()
        self._campo_mora_leve_hasta = QLineEdit()
        self._campo_mora_leve_hasta.setPlaceholderText("Hasta cuantos meses sigue siendo leve")
        self._campo_mora_media_hasta = QLineEdit()
        self._campo_mora_media_hasta.setPlaceholderText("Hasta cuantos meses sigue siendo media")

        panel_precio = self._crear_panel(
            "Precio mensual del servicio",
            "Segun la regla cerrada, el cambio de tarifa solo afecta cargos nuevos. Nunca recalcula deuda historica.",
            [self._crear_bloque_campo("Precio mensual (centavos)", self._campo_precio_mensual)],
        )
        panel_mora = self._crear_panel(
            "Mora y recargo automatico",
            "La mora sigue existiendo como meses vencidos no pagados. Aqui solo parametrizas el recargo automatico adicional.",
            [
                self._crear_fila_resumen("Regla de mora", self._valor_mora_regla),
                self._crear_fila_resumen("Rangos visuales vigentes", self._valor_rangos_mora),
                self._check_multa_automatica,
                self._crear_bloque_campo(
                    "Monto del recargo automatico por mes vencido (centavos)",
                    self._campo_multa_automatica,
                ),
                self._crear_bloque_campo(
                    "Mora leve hasta (meses)",
                    self._campo_mora_leve_hasta,
                ),
                self._crear_bloque_campo(
                    "Mora media hasta (meses)",
                    self._campo_mora_media_hasta,
                ),
            ],
        )
        panel_corte = self._crear_panel(
            "Corte y alertas por deuda",
            "Control global que afecta diagnostico de casas, morosidad y decision operativa del soporte.",
            [
                self._check_corte_automatico,
                self._crear_bloque_campo("Meses para corte o alerta", self._campo_meses_para_corte),
            ],
        )
        panel_adelantos = self._crear_panel(
            "Pago adelantado",
            "Permite controlar si pagos puede registrar meses futuros y hasta donde, sin anular las reglas de deuda vencida.",
            [
                self._check_pago_adelantado,
                self._crear_bloque_campo("Maximo de meses adelantados", self._campo_meses_adelanto_maximo),
            ],
        )

        boton_guardar = crear_boton_operativo("Guardar parametros de cobro", principal=True)
        boton_guardar.clicked.connect(self._emitir_guardado_parametros_cobro)

        contenido = self._crear_contenedor_scroll()
        contenido.widget().layout().addWidget(panel_precio)
        contenido.widget().layout().addWidget(panel_mora)
        contenido.widget().layout().addWidget(panel_corte)
        contenido.widget().layout().addWidget(panel_adelantos)
        contenido.widget().layout().addWidget(
            self._crear_aviso(
                "Impacta Pagos, Morosidad, Casas y Reportes. "
                "Conexion y reconexion no se configuran como tarifa global en esta pantalla."
            )
        )
        contenido.widget().layout().addWidget(boton_guardar, alignment=Qt.AlignmentFlag.AlignRight)
        return contenido

    def _crear_tab_operacion_respaldo(self) -> QWidget:
        self._check_respaldo_automatico = QCheckBox("Generar respaldo automatico de la base local")
        self._valor_ultimo_respaldo = self._crear_valor_seguridad()
        self._valor_estado_respaldo = self._crear_valor_seguridad()
        self._valor_total_respaldos = self._crear_valor_seguridad()
        self._valor_ruta_comprobantes = self._crear_valor_seguridad()
        self._valor_ruta_reportes = self._crear_valor_seguridad()
        self._valor_autenticacion = self._crear_valor_seguridad()
        self._valor_intentos = self._crear_valor_seguridad()
        self._valor_sesion = self._crear_valor_seguridad()
        self._valor_restablecimiento = self._crear_valor_seguridad()
        self._valor_cambio_clave = self._crear_valor_seguridad()

        panel_control = self._crear_panel(
            "Control y respaldo",
            "Soporte operativo conectado a mantenimiento y rutas reales del proyecto.",
            [
                self._check_respaldo_automatico,
                self._crear_fila_resumen("Ultimo respaldo", self._valor_ultimo_respaldo),
                self._crear_fila_resumen("Estado del ultimo respaldo", self._valor_estado_respaldo),
                self._crear_fila_resumen("Total de respaldos", self._valor_total_respaldos),
                self._crear_fila_resumen(
                    "Ruta exportacion comprobantes",
                    self._valor_ruta_comprobantes,
                ),
                self._crear_fila_resumen("Ruta exportacion reportes", self._valor_ruta_reportes),
            ],
        )
        panel_seguridad = self._crear_panel(
            "Seguridad vigente",
            "Resumen de reglas cerradas. Los cambios sensibles siguen fuera de esta UI.",
            [
                self._crear_fila_resumen("Autenticacion", self._valor_autenticacion),
                self._crear_fila_resumen("Intentos maximos", self._valor_intentos),
                self._crear_fila_resumen("Duracion de sesion", self._valor_sesion),
                self._crear_fila_resumen("Restablecimiento", self._valor_restablecimiento),
                self._crear_fila_resumen("Cambio obligatorio de clave", self._valor_cambio_clave),
            ],
        )
        boton_guardar = crear_boton_operativo("Guardar control de respaldo", principal=True)
        boton_guardar.clicked.connect(
            lambda: self.guardar_operacion_respaldo_solicitado.emit(
                self._check_respaldo_automatico.isChecked()
            )
        )

        contenido = self._crear_contenedor_scroll()
        contenido.widget().layout().addWidget(panel_control)
        contenido.widget().layout().addWidget(panel_seguridad)
        contenido.widget().layout().addWidget(
            self._crear_aviso(
                "El modulo Mantenimiento sigue reservado para SUPERADMINISTRADOR. "
                "Aqui solo se controla la bandera operativa de respaldo automatico."
            )
        )
        contenido.widget().layout().addWidget(boton_guardar, alignment=Qt.AlignmentFlag.AlignRight)
        return contenido

    def _crear_tab_informacion(self) -> QWidget:
        self._valor_nombre_sistema = self._crear_valor_seguridad()
        self._valor_version_sistema = self._crear_valor_seguridad()
        self._valor_ruta_base = self._crear_valor_seguridad()
        self._valor_modo_operacion = self._crear_valor_seguridad()
        self._valor_actualizacion = self._crear_valor_seguridad()
        panel = self._crear_panel(
            "Informacion del sistema",
            "Resumen tecnico defendible del entorno SQLite local actual.",
            [
                self._crear_fila_resumen("Sistema", self._valor_nombre_sistema),
                self._crear_fila_resumen("Version", self._valor_version_sistema),
                self._crear_fila_resumen("Base de datos", self._valor_ruta_base),
                self._crear_fila_resumen("Modo de operacion", self._valor_modo_operacion),
                self._crear_fila_resumen("Ultima actualizacion", self._valor_actualizacion),
            ],
        )
        contenido = self._crear_contenedor_scroll()
        contenido.widget().layout().addWidget(panel)
        contenido.widget().layout().addWidget(
            self._crear_aviso(
                "Configuracion solo expone parametros respaldados por la base real o por reglas cerradas de negocio."
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
        self._preview_documento.setMinimumHeight(500)
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
        if estado.datos_junta.nombre.strip():
            lineas.append(estado.datos_junta.nombre.strip())
        if (
            estado.factura.mostrar_identificador_fiscal
            and estado.datos_junta.identificador_fiscal.strip()
        ):
            lineas.append(f"ID fiscal: {estado.datos_junta.identificador_fiscal.strip()}")
        if estado.factura.mostrar_telefono and estado.datos_junta.telefono.strip():
            lineas.append(estado.datos_junta.telefono.strip())
        if estado.factura.mostrar_correo and estado.datos_junta.correo.strip():
            lineas.append(estado.datos_junta.correo.strip())
        if estado.factura.mostrar_direccion and estado.datos_junta.direccion.strip():
            lineas.append(estado.datos_junta.direccion.strip())
        if estado.datos_junta.sitio_web.strip():
            lineas.append(estado.datos_junta.sitio_web.strip())
        if estado.datos_junta.mensaje_contacto.strip():
            lineas.append(estado.datos_junta.mensaje_contacto.strip())
        return lineas or ["Junta no configurada"]

    def _emitir_guardado_parametros_cobro(self) -> None:
        self.guardar_parametros_cobro_solicitado.emit(
            self._leer_entero(self._campo_precio_mensual.text()),
            self._check_multa_automatica.isChecked(),
            self._leer_entero(self._campo_multa_automatica.text()),
            self._check_corte_automatico.isChecked(),
            self._leer_entero(self._campo_meses_para_corte.text()),
            self._check_pago_adelantado.isChecked(),
            self._leer_entero(self._campo_meses_adelanto_maximo.text()),
            self._leer_entero(self._campo_mora_leve_hasta.text()),
            self._leer_entero(self._campo_mora_media_hasta.text()),
        )

    def _actualizar_estado_campos_cobro(self) -> None:
        self._campo_multa_automatica.setEnabled(self._check_multa_automatica.isChecked())
        self._campo_meses_adelanto_maximo.setEnabled(self._check_pago_adelantado.isChecked())

    def _mostrar_ayuda(self) -> None:
        from comun.ui import DialogoMensajeSicap

        dialogo = DialogoMensajeSicap(
            titulo="Ayuda de configuracion",
            mensaje=(
                "Esta pantalla solo administra parametros reales del sistema. "
                "Precio mensual, recargo automatico, pago adelantado, comprobantes y respaldo afectan modulos operativos. "
                "Las reglas sensibles de seguridad y los procesos tecnicos siguen fuera de esta vista."
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

    def _crear_panel(self, titulo: str, descripcion: str, elementos: list[object]) -> QFrame:
        panel = QFrame()
        panel.setObjectName("panelConfiguracion")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)
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

    @staticmethod
    def _leer_entero(texto: str) -> int:
        try:
            return int((texto or "0").strip())
        except ValueError:
            return -1

    @staticmethod
    def _componer_datos_recibo(estado: EstadoConfiguracion) -> str:
        partes: list[str] = []
        if estado.factura.mostrar_telefono and estado.datos_junta.telefono:
            partes.append(estado.datos_junta.telefono)
        if estado.factura.mostrar_correo and estado.datos_junta.correo:
            partes.append(estado.datos_junta.correo)
        if estado.factura.mostrar_direccion and estado.datos_junta.direccion:
            partes.append(estado.datos_junta.direccion)
        if estado.factura.mostrar_identificador_fiscal and estado.datos_junta.identificador_fiscal:
            partes.append(f"ID fiscal: {estado.datos_junta.identificador_fiscal}")
        if estado.datos_junta.sitio_web:
            partes.append(estado.datos_junta.sitio_web)
        if estado.datos_junta.mensaje_contacto:
            partes.append(estado.datos_junta.mensaje_contacto)
        return " | ".join(partes) if partes else "Sin datos complementarios"

    def _aplicar_estilos(self) -> None:
        paleta = self._paleta_tema
        oscuro = self._tema_actual != "claro"
        fondo_panel = "rgba(255, 255, 255, 0.10)" if oscuro else paleta["fondo_superficie"]
        borde_panel = "rgba(255, 255, 255, 0.16)" if oscuro else paleta["borde_principal"]
        texto_principal = "#ffffff" if oscuro else paleta["texto_principal"]
        texto_secundario = "rgba(235, 242, 248, 0.76)" if oscuro else paleta["texto_secundario"]
        fondo_input = "rgba(255,255,255,0.11)" if oscuro else paleta["fondo_input"]
        borde_input = "rgba(255,255,255,0.18)" if oscuro else paleta["borde_medio"]
        fondo_tabs = "rgba(255,255,255,0.06)" if oscuro else paleta["fondo_superficie_suave"]
        fondo_tab_barra = "rgba(255,255,255,0.04)" if oscuro else paleta["fondo_superficie_muy_suave"]
        fondo_tab_hover = "rgba(255,255,255,0.10)" if oscuro else paleta["fondo_superficie"]
        fondo_tab_activo = "#d2f4f2" if oscuro else paleta["fondo_chip_activo"]
        texto_tab_activo = "#0f2d43" if oscuro else paleta["texto_chip_activo"]
        borde_tab_activo = "rgba(157, 239, 228, 0.34)" if oscuro else paleta["borde_chip_activo"]
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
                color: {'#d9fff5' if oscuro else paleta['texto_exito']};
                font-size: 12px;
                font-weight: 700;
                padding: 8px 10px;
                border-radius: 12px;
                background-color: {'rgba(16, 120, 98, 0.16)' if oscuro else paleta['fondo_exito']};
                border: 1px solid {'rgba(158, 231, 214, 0.26)' if oscuro else paleta['borde_exito']};
            }}
            QLabel#mensajeConfiguracion[error="true"] {{
                color: {'#ffd4cf' if oscuro else paleta['texto_error']};
                background-color: {'rgba(180, 35, 24, 0.15)' if oscuro else paleta['fondo_error']};
                border: 1px solid {'rgba(255, 205, 199, 0.28)' if oscuro else paleta['borde_error']};
            }}
            QFrame#tarjetaResumenConfiguracion,
            QFrame#panelConfiguracion,
            QFrame#avisoConfiguracion {{
                background: {fondo_panel};
                border: 1px solid {borde_panel};
                border-radius: 18px;
            }}
            QFrame#previewComprobanteConfiguracion {{
                background: #ffffff;
                border: 1px solid #1a1a1a;
                border-radius: 8px;
            }}
            QTextEdit#documentoPreviewComprobanteConfiguracion {{
                background: #ffffff;
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
            }}
            QLineEdit:disabled, QPlainTextEdit:disabled, QComboBox:disabled {{
                color: {texto_secundario};
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
                border-color: {borde_tab_activo};
            }}
            QTabWidget#tabsConfiguracion QTabBar::tab:!selected {{
                margin-top: 2px;
            }}
            QScrollArea#scrollConfiguracion {{
                background: transparent;
                border: none;
            }}
            """
        )
