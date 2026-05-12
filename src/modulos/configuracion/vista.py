"""Vista PySide6 del modulo de configuracion."""

from __future__ import annotations

from typing import Callable

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from comun.ui import BotonAccionContextual, crear_boton_operativo
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

    guardar_datos_junta_solicitado = Signal(str, str, str, str)
    guardar_parametros_cobro_solicitado = Signal(int, bool, int, bool)

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
            "Costo base por cada mes de servicio adeudado.",
        )
        self._tarjeta_mora.actualizar(
            "Visible",
            "Los meses vencidos no pagados siguen formando la mora operativa.",
        )
        self._tarjeta_recargo.actualizar(
            "Activa" if estado.parametros_cobro.multa_mora_automatica_activa else "Inactiva",
            "Recargo adicional por mes vencido solo si esta habilitado.",
        )
        self._tarjeta_corte.actualizar(
            "Activo" if estado.parametros_cobro.corte_automatico_activo else "Inactivo",
            "Control global del corte automatico por deuda.",
        )

        self._campo_junta_nombre.setText(estado.datos_junta.nombre)
        self._campo_junta_telefono.setText(estado.datos_junta.telefono)
        self._campo_junta_correo.setText(estado.datos_junta.correo)
        self._campo_junta_direccion.setPlainText(estado.datos_junta.direccion)

        self._campo_precio_mensual.setText(str(estado.parametros_cobro.precio_mensual_centavos))
        self._check_multa_automatica.blockSignals(True)
        self._check_multa_automatica.setChecked(estado.parametros_cobro.multa_mora_automatica_activa)
        self._check_multa_automatica.blockSignals(False)
        self._campo_multa_automatica.setText(
            str(estado.parametros_cobro.multa_mora_automatica_centavos)
        )
        self._check_corte_automatico.setChecked(estado.parametros_cobro.corte_automatico_activo)
        self._actualizar_estado_campos_cobro()

        self._valor_autenticacion.setText("Local")
        self._valor_intentos.setText(str(estado.seguridad.maximo_intentos_fallidos))
        self._valor_sesion.setText(f"{estado.seguridad.duracion_sesion_horas} horas")
        self._valor_restablecimiento.setText("Administrativo")
        self._valor_nombre_sistema.setText(estado.informacion.nombre_sistema)
        self._valor_version_sistema.setText(estado.informacion.version_sistema or "Sin version")
        self._valor_ruta_base.setText(estado.informacion.ruta_base_datos)
        self._valor_modo_operacion.setText(estado.informacion.modo_operacion)
        self._valor_actualizacion.setText(estado.informacion.ultima_actualizacion or "Sin registro")

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
        bloque_titulo = QVBoxLayout()
        bloque_titulo.setSpacing(3)
        titulo = QLabel("Configuracion")
        titulo.setObjectName("tituloModulo")
        descripcion = QLabel(
            "Ajusta datos institucionales y parametros de cobro segun la operacion real actual de SICAP."
        )
        descripcion.setObjectName("descripcionModulo")
        descripcion.setWordWrap(True)
        bloque_titulo.addWidget(titulo)
        bloque_titulo.addWidget(descripcion)
        encabezado.addLayout(bloque_titulo, 1)

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
        self._tarjeta_precio = TarjetaResumenConfiguracion("Precio mensual")
        self._tarjeta_mora = TarjetaResumenConfiguracion("Mora")
        self._tarjeta_recargo = TarjetaResumenConfiguracion("Recargo automatico")
        self._tarjeta_corte = TarjetaResumenConfiguracion("Corte automatico")
        tarjetas.addWidget(self._tarjeta_precio, 0, 0)
        tarjetas.addWidget(self._tarjeta_mora, 0, 1)
        tarjetas.addWidget(self._tarjeta_recargo, 0, 2)
        tarjetas.addWidget(self._tarjeta_corte, 0, 3)

        self._tabs = QTabWidget()
        self._tabs.setObjectName("tabsConfiguracion")
        self._tabs.addTab(self._crear_tab_datos_junta(), "Datos de la junta")
        self._tabs.addTab(self._crear_tab_parametros_cobro(), "Parametros de cobro")
        self._tabs.addTab(self._crear_tab_seguridad(), "Seguridad")
        self._tabs.addTab(self._crear_tab_informacion(), "Informacion")

        layout.addLayout(encabezado)
        layout.addWidget(self._mensaje)
        layout.addLayout(tarjetas)
        layout.addWidget(self._tabs, 1)

    def _crear_tab_datos_junta(self) -> QWidget:
        self._campo_junta_nombre = QLineEdit()
        self._campo_junta_telefono = QLineEdit()
        self._campo_junta_correo = QLineEdit()
        self._campo_junta_direccion = QPlainTextEdit()
        self._campo_junta_direccion.setFixedHeight(90)

        grilla = QGridLayout()
        grilla.setHorizontalSpacing(12)
        grilla.setVerticalSpacing(12)
        grilla.addWidget(self._crear_bloque_campo("Nombre de la junta", self._campo_junta_nombre), 0, 0, 1, 2)
        grilla.addWidget(self._crear_bloque_campo("Telefono", self._campo_junta_telefono), 1, 0)
        grilla.addWidget(self._crear_bloque_campo("Correo", self._campo_junta_correo), 1, 1)
        grilla.addWidget(self._crear_bloque_campo("Direccion", self._campo_junta_direccion), 2, 0, 1, 2)

        boton_guardar = crear_boton_operativo("Guardar datos de la junta", principal=True)
        boton_guardar.clicked.connect(
            lambda: self.guardar_datos_junta_solicitado.emit(
                self._campo_junta_nombre.text(),
                self._campo_junta_telefono.text(),
                self._campo_junta_correo.text(),
                self._campo_junta_direccion.toPlainText(),
            )
        )

        contenido = self._crear_contenedor_scroll()
        contenido.widget().layout().addWidget(
            self._crear_panel(
                "Identidad institucional",
                "Estos datos alimentan el contexto operativo de la junta dentro del sistema local.",
                [grilla],
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

        panel_precio = self._crear_panel(
            "Precio mensual del servicio",
            "Este valor representa el costo por cada mes de servicio y se suma a la deuda de la casa cuando el periodo queda pendiente o vencido.",
            [self._crear_bloque_campo("Precio mensual (centavos)", self._campo_precio_mensual)],
        )
        panel_mora = self._crear_panel(
            "Mora y recargo automatico",
            "La mora sigue existiendo como meses vencidos no pagados. Lo opcional es el recargo automatico adicional por mes vencido.",
            [
                self._check_multa_automatica,
                self._crear_bloque_campo(
                    "Monto del recargo automatico por mes vencido (centavos)",
                    self._campo_multa_automatica,
                ),
            ],
        )
        panel_corte = self._crear_panel(
            "Corte automatico",
            "Activa o desactiva globalmente el corte automatico. Conexion y reconexion no se fijan aqui como tarifas globales porque dependen del caso operativo.",
            [self._check_corte_automatico],
        )

        boton_guardar = crear_boton_operativo("Guardar parametros de cobro", principal=True)
        boton_guardar.clicked.connect(self._emitir_guardado_parametros_cobro)

        contenido = self._crear_contenedor_scroll()
        contenido.widget().layout().addWidget(panel_precio)
        contenido.widget().layout().addWidget(panel_mora)
        contenido.widget().layout().addWidget(panel_corte)
        contenido.widget().layout().addWidget(boton_guardar, alignment=Qt.AlignmentFlag.AlignRight)
        return contenido

    def _crear_tab_seguridad(self) -> QWidget:
        self._valor_autenticacion = self._crear_valor_seguridad()
        self._valor_intentos = self._crear_valor_seguridad()
        self._valor_sesion = self._crear_valor_seguridad()
        self._valor_restablecimiento = self._crear_valor_seguridad()
        panel = self._crear_panel(
            "Reglas activas",
            "Esta pestaña refleja la seguridad vigente de SICAP. En esta version local no se exponen ajustes sensibles que aun dependan de codigo o mantenimiento tecnico.",
            [
                self._crear_fila_resumen("Autenticacion", self._valor_autenticacion),
                self._crear_fila_resumen("Intentos maximos", self._valor_intentos),
                self._crear_fila_resumen("Duracion de sesion", self._valor_sesion),
                self._crear_fila_resumen("Restablecimiento", self._valor_restablecimiento),
            ],
        )
        contenido = self._crear_contenedor_scroll()
        contenido.widget().layout().addWidget(panel)
        return contenido

    def _crear_tab_informacion(self) -> QWidget:
        self._valor_nombre_sistema = self._crear_valor_seguridad()
        self._valor_version_sistema = self._crear_valor_seguridad()
        self._valor_ruta_base = self._crear_valor_seguridad()
        self._valor_modo_operacion = self._crear_valor_seguridad()
        self._valor_actualizacion = self._crear_valor_seguridad()
        panel = self._crear_panel(
            "Informacion del entorno",
            "Resumen util para soporte operativo y validacion del despliegue local actual.",
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
        return contenido

    def _emitir_guardado_parametros_cobro(self) -> None:
        self.guardar_parametros_cobro_solicitado.emit(
            self._leer_entero(self._campo_precio_mensual.text()),
            self._check_multa_automatica.isChecked(),
            self._leer_entero(self._campo_multa_automatica.text()),
            self._check_corte_automatico.isChecked(),
        )

    def _actualizar_estado_campos_cobro(self) -> None:
        self._campo_multa_automatica.setEnabled(self._check_multa_automatica.isChecked())

    def _mostrar_ayuda(self) -> None:
        from comun.ui import DialogoMensajeSicap

        dialogo = DialogoMensajeSicap(
            titulo="Ayuda de configuracion",
            mensaje=(
                "La mora sigue existiendo como meses vencidos no pagados. "
                "Lo que puedes activar o desactivar aqui es el recargo automatico adicional por mora. "
                "Conexion y reconexion se manejan en sus flujos operativos y no como tarifas globales fijas."
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

    def _aplicar_estilos(self) -> None:
        paleta = self._paleta_tema
        oscuro = self._tema_actual != "claro"
        fondo_panel = "rgba(255, 255, 255, 0.10)" if oscuro else paleta["fondo_superficie"]
        borde_panel = "rgba(255, 255, 255, 0.16)" if oscuro else paleta["borde_principal"]
        texto_principal = "#ffffff" if oscuro else paleta["texto_principal"]
        texto_secundario = "rgba(235, 242, 248, 0.76)" if oscuro else paleta["texto_secundario"]
        fondo_input = "rgba(255,255,255,0.11)" if oscuro else paleta["fondo_input"]
        borde_input = "rgba(255,255,255,0.18)" if oscuro else paleta["borde_medio"]
        fondo_tabs = "rgba(255,255,255,0.08)" if oscuro else paleta["fondo_superficie_suave"]
        fondo_tab_activo = "#d2f4f2" if oscuro else paleta["fondo_chip_activo"]
        texto_tab_activo = "#0f2d43" if oscuro else paleta["texto_chip_activo"]
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
            QLabel#detalleTarjetaResumenConfiguracion {{
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
            QFrame#panelConfiguracion {{
                background: {fondo_panel};
                border: 1px solid {borde_panel};
                border-radius: 18px;
            }}
            QLabel#tituloTarjetaResumenConfiguracion {{
                color: {texto_secundario};
                font-size: 11px;
                font-weight: 700;
            }}
            QLabel#valorTarjetaResumenConfiguracion {{
                color: {texto_principal};
                font-size: 20px;
                font-weight: 900;
            }}
            QLabel#tituloPanelConfiguracion {{
                color: {texto_principal};
                font-size: 14px;
                font-weight: 800;
            }}
            QLabel#etiquetaConfiguracion,
            QLabel#etiquetaResumenConfiguracion {{
                color: {texto_secundario};
                font-size: 12px;
                font-weight: 700;
            }}
            QLabel#valorResumenConfiguracion {{
                color: {texto_principal};
                font-size: 13px;
                font-weight: 800;
            }}
            QLineEdit, QPlainTextEdit {{
                border: 1px solid {borde_input};
                border-radius: 12px;
                background: {fondo_input};
                color: {texto_principal};
                padding: 8px 10px;
                font-size: 12px;
            }}
            QLineEdit:disabled {{
                color: {texto_secundario};
            }}
            QCheckBox {{
                color: {texto_principal};
                font-size: 12px;
                font-weight: 700;
            }}
            QTabWidget#tabsConfiguracion::pane {{
                border: 1px solid {borde_panel};
                border-radius: 18px;
                background: {fondo_panel};
                margin-top: 8px;
            }}
            QTabWidget#tabsConfiguracion QTabBar::tab {{
                background: {fondo_tabs};
                border: 1px solid {borde_panel};
                color: {texto_principal};
                padding: 9px 14px;
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
                font-size: 12px;
                font-weight: 700;
                margin-right: 6px;
            }}
            QTabWidget#tabsConfiguracion QTabBar::tab:selected {{
                background: {fondo_tab_activo};
                color: {texto_tab_activo};
            }}
            QScrollArea#scrollConfiguracion {{
                background: transparent;
                border: none;
            }}
            """
        )
