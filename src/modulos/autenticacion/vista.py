"""Vista PySide6 del modulo de autenticacion."""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QColor, QLinearGradient, QPaintEvent, QPainter, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from comun.configuracion.gestor_rutas import GestorRutas
from comun.ui import (
    obtener_icono_tabler_coloreado,
    obtener_pixmap_tabler_coloreado,
)
from modulos.autenticacion.entidades import UsuarioAutenticado


ANCHO_MAXIMO_TARJETA = 548
COLOR_GRADIENTE_INICIAL = "#1abc9c"
COLOR_GRADIENTE_FINAL = "#1f2c51"
COLOR_ICONO_INPUT = "#486278"
COLOR_ICONO_PRIMARIO = "#ffffff"
COLOR_ICONO_SECUNDARIO = "#17324d"
COLOR_ICONO_ESTADO = "#1f2c51"


class VistaAutenticacion(QWidget):
    """Renderiza el flujo completo de autenticacion usando layouts adaptables."""

    iniciar_sesion_solicitada = Signal(str, str)
    ir_a_olvido_solicitado = Signal()
    recuperacion_solicitada = Signal(str)
    token_prueba_solicitado = Signal(str)
    restablecimiento_solicitado = Signal(str, str, str)
    volver_a_login_solicitado = Signal()
    autenticacion_exitosa = Signal(object)

    def __init__(self, gestor_rutas: GestorRutas | None = None) -> None:
        super().__init__()
        self._gestor_rutas = gestor_rutas or GestorRutas()
        self._token_recuperacion_actual = ""
        self._token_prueba_visible = ""

        self.setObjectName("vistaAutenticacion")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._aplicar_estilos()

        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.setSpacing(0)

        self._stack = QStackedWidget()
        self._stack.setObjectName("stackAutenticacion")
        layout_principal.addWidget(self._stack)

        self._pagina_login = self._construir_pagina_login()
        self._pagina_olvido = self._construir_pagina_olvido()
        self._pagina_correo_enviado = self._construir_pagina_correo_enviado()
        self._pagina_restablecer = self._construir_pagina_restablecer()
        self._pagina_exito = self._construir_pagina_exito()
        self._pagina_enlace_invalido = self._construir_pagina_enlace_invalido()

        for pagina in (
            self._pagina_login,
            self._pagina_olvido,
            self._pagina_correo_enviado,
            self._pagina_restablecer,
            self._pagina_exito,
            self._pagina_enlace_invalido,
        ):
            self._stack.addWidget(pagina)

    def paintEvent(self, evento: QPaintEvent) -> None:
        """Pinta un degradado horizontal estable en toda la vista."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        painter.setPen(Qt.PenStyle.NoPen)

        gradiente = QLinearGradient(0, 0, self.width(), 0)
        gradiente.setColorAt(0.0, QColor(COLOR_GRADIENTE_INICIAL))
        gradiente.setColorAt(1.0, QColor(COLOR_GRADIENTE_FINAL))
        painter.setBrush(gradiente)
        painter.drawRect(self.rect())
        painter.end()

        super().paintEvent(evento)

    def mostrar_login(self, mensaje: str | None = None, es_exito: bool = False) -> None:
        self._token_recuperacion_actual = ""
        self._limpiar_mensaje(self._mensaje_olvido)
        self._limpiar_mensaje(self._mensaje_restablecer)
        self._campo_contrasena.clear()
        self._stack.setCurrentWidget(self._pagina_login)
        self._campo_usuario.setFocus()
        if mensaje:
            self._mostrar_mensaje(self._mensaje_login, mensaje, es_exito=es_exito)
        else:
            self._limpiar_mensaje(self._mensaje_login)

    def mostrar_error_login(self, mensaje: str) -> None:
        self._mostrar_mensaje(self._mensaje_login, mensaje, es_exito=False)

    def mostrar_olvido_contrasena(self) -> None:
        self._campo_correo.clear()
        self._limpiar_mensaje(self._mensaje_olvido)
        self._stack.setCurrentWidget(self._pagina_olvido)
        self._campo_correo.setFocus()

    def mostrar_error_olvido(self, mensaje: str) -> None:
        self._mostrar_mensaje(self._mensaje_olvido, mensaje, es_exito=False)

    def mostrar_correo_enviado(self, mensaje: str, token_prueba: str | None = None) -> None:
        self._stack.setCurrentWidget(self._pagina_correo_enviado)
        self._mensaje_correo_enviado.setText(mensaje)
        self._token_prueba_visible = token_prueba or ""
        hay_token = bool(self._token_prueba_visible)
        self._contenedor_token_prueba.setVisible(hay_token)
        self._campo_token_prueba.setText(self._token_prueba_visible)

    def mostrar_restablecer(self, token: str, mensaje: str | None = None) -> None:
        self._token_recuperacion_actual = token.strip()
        self._campo_nueva_contrasena.clear()
        self._campo_confirmacion_contrasena.clear()
        self._stack.setCurrentWidget(self._pagina_restablecer)
        self._campo_nueva_contrasena.setFocus()
        if mensaje:
            self._mostrar_mensaje(self._mensaje_restablecer, mensaje, es_exito=True)
        else:
            self._limpiar_mensaje(self._mensaje_restablecer)

    def mostrar_error_restablecer(self, mensaje: str) -> None:
        self._mostrar_mensaje(self._mensaje_restablecer, mensaje, es_exito=False)

    def mostrar_exito(self, mensaje: str) -> None:
        self._mensaje_exito.setText(mensaje)
        self._stack.setCurrentWidget(self._pagina_exito)

    def mostrar_enlace_invalido(self, mensaje: str) -> None:
        self._mensaje_enlace_invalido.setText(mensaje)
        self._stack.setCurrentWidget(self._pagina_enlace_invalido)

    def limpiar_campos_sensibles(self) -> None:
        self._campo_contrasena.clear()
        self._campo_nueva_contrasena.clear()
        self._campo_confirmacion_contrasena.clear()

    def notificar_autenticacion_exitosa(self, usuario: UsuarioAutenticado) -> None:
        self.autenticacion_exitosa.emit(usuario)

    def _construir_pagina_login(self) -> QWidget:
        pagina, tarjeta, contenido = self._crear_pagina_base()
        self._agregar_logo(tarjeta)
        self._agregar_encabezado(
            contenido,
            titulo="Accede a SICAP",
            subtitulo=(
                "Sistema Integral de Control de Abonados y Pagos\n\n"
                "Junta de Agua de Yarumela."
            ),
        )

        self._campo_usuario = self._crear_input(
            placeholder="Nombre de usuario",
            icono="user.svg",
        )
        self._campo_contrasena = self._crear_input(
            placeholder="Contrasena",
            icono="lock.svg",
            es_password=True,
        )
        self._campo_contrasena.returnPressed.connect(self._emitir_login)

        contenido.addLayout(self._crear_bloque_campo("Usuario", self._campo_usuario))
        contenido.addLayout(
            self._crear_bloque_campo("Contrasena", self._campo_contrasena)
        )

        self._mensaje_login = self._crear_label_mensaje()
        contenido.addWidget(self._mensaje_login)

        self._boton_login = self._crear_boton_primario(
            texto="Iniciar sesion",
            icono="login-2.svg",
            accion=self._emitir_login,
        )
        contenido.addWidget(self._boton_login)

        boton_olvido = self._crear_boton_secundario(
            texto="Olvide mi contrasena",
            icono="key.svg",
            accion=self.ir_a_olvido_solicitado.emit,
        )
        contenido.addWidget(boton_olvido)

        self._label_pie_login = QLabel("SICAP 1.0  |  Creador: Victor Lopez")
        self._label_pie_login.setObjectName("pieLogin")
        self._label_pie_login.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label_pie_login.setWordWrap(True)
        contenido.addWidget(self._label_pie_login)
        return pagina

    def _construir_pagina_olvido(self) -> QWidget:
        pagina, _, contenido = self._crear_pagina_base()
        self._agregar_encabezado(
            contenido,
            titulo="Recupera tu acceso",
            subtitulo="Ingresa tu correo y prepararemos el enlace de restablecimiento.",
            icono="mail.svg",
        )

        self._campo_correo = self._crear_input(
            placeholder="correo@ejemplo.com",
            icono="mail.svg",
        )
        self._campo_correo.returnPressed.connect(self._emitir_recuperacion)
        contenido.addLayout(self._crear_bloque_campo("Correo", self._campo_correo))

        self._mensaje_olvido = self._crear_label_mensaje()
        contenido.addWidget(self._mensaje_olvido)

        contenido.addWidget(
            self._crear_boton_primario(
                texto="Preparar recuperacion",
                icono="mail.svg",
                accion=self._emitir_recuperacion,
            )
        )
        contenido.addWidget(
            self._crear_boton_secundario(
                texto="Volver al login",
                icono="arrow-left.svg",
                accion=self.volver_a_login_solicitado.emit,
            )
        )
        return pagina

    def _construir_pagina_correo_enviado(self) -> QWidget:
        pagina, _, contenido = self._crear_pagina_base()
        self._agregar_encabezado(
            contenido,
            titulo="Correo preparado",
            subtitulo="El sistema ya dejo lista la recuperacion para continuar con seguridad.",
            icono="circle-check.svg",
        )

        self._mensaje_correo_enviado = QLabel()
        self._mensaje_correo_enviado.setWordWrap(True)
        self._mensaje_correo_enviado.setObjectName("textoExplicativo")
        contenido.addWidget(self._mensaje_correo_enviado)

        self._contenedor_token_prueba = QFrame()
        self._contenedor_token_prueba.setObjectName("panelTokenPrueba")
        layout_token = QVBoxLayout(self._contenedor_token_prueba)
        layout_token.setContentsMargins(16, 16, 16, 16)
        layout_token.setSpacing(10)

        etiqueta_token = QLabel(
            "Token de prueba disponible solo en desarrollo para continuar sin envio real."
        )
        etiqueta_token.setWordWrap(True)
        etiqueta_token.setObjectName("textoExplicativo")
        layout_token.addWidget(etiqueta_token)

        self._campo_token_prueba = self._crear_input(
            placeholder="Token de prueba",
            icono="key.svg",
        )
        self._campo_token_prueba.setReadOnly(True)
        layout_token.addWidget(self._campo_token_prueba)
        layout_token.addWidget(
            self._crear_boton_primario(
                texto="Continuar con token de prueba",
                icono="key.svg",
                accion=self._emitir_token_prueba,
            )
        )
        self._contenedor_token_prueba.setVisible(False)
        contenido.addWidget(self._contenedor_token_prueba)

        contenido.addWidget(
            self._crear_boton_secundario(
                texto="Volver al login",
                icono="arrow-left.svg",
                accion=self.volver_a_login_solicitado.emit,
            )
        )
        return pagina

    def _construir_pagina_restablecer(self) -> QWidget:
        pagina, _, contenido = self._crear_pagina_base()
        self._agregar_encabezado(
            contenido,
            titulo="Restablece tu contrasena",
            subtitulo="Crea una nueva contrasena para cerrar este flujo de recuperacion.",
            icono="key.svg",
        )

        self._campo_nueva_contrasena = self._crear_input(
            placeholder="Nueva contrasena",
            icono="lock.svg",
            es_password=True,
        )
        self._campo_confirmacion_contrasena = self._crear_input(
            placeholder="Confirmar contrasena",
            icono="lock.svg",
            es_password=True,
        )
        self._campo_confirmacion_contrasena.returnPressed.connect(
            self._emitir_restablecimiento
        )

        contenido.addLayout(
            self._crear_bloque_campo("Nueva contrasena", self._campo_nueva_contrasena)
        )
        contenido.addLayout(
            self._crear_bloque_campo(
                "Confirmar contrasena",
                self._campo_confirmacion_contrasena,
            )
        )

        self._mensaje_restablecer = self._crear_label_mensaje()
        contenido.addWidget(self._mensaje_restablecer)

        contenido.addWidget(
            self._crear_boton_primario(
                texto="Guardar nueva contrasena",
                icono="key.svg",
                accion=self._emitir_restablecimiento,
            )
        )
        contenido.addWidget(
            self._crear_boton_secundario(
                texto="Volver al login",
                icono="arrow-left.svg",
                accion=self.volver_a_login_solicitado.emit,
            )
        )
        return pagina

    def _construir_pagina_exito(self) -> QWidget:
        pagina, _, contenido = self._crear_pagina_base()
        self._agregar_encabezado(
            contenido,
            titulo="Contrasena actualizada",
            subtitulo="Tu acceso ya quedo listo para volver a ingresar al sistema.",
            icono="circle-check.svg",
        )

        self._mensaje_exito = QLabel()
        self._mensaje_exito.setWordWrap(True)
        self._mensaje_exito.setObjectName("textoExplicativo")
        contenido.addWidget(self._mensaje_exito)
        contenido.addWidget(
            self._crear_boton_primario(
                texto="Volver al login",
                icono="login-2.svg",
                accion=self.volver_a_login_solicitado.emit,
            )
        )
        return pagina

    def _construir_pagina_enlace_invalido(self) -> QWidget:
        pagina, _, contenido = self._crear_pagina_base()
        self._agregar_encabezado(
            contenido,
            titulo="Enlace invalido",
            subtitulo="El token ya no puede usarse o no corresponde a una recuperacion vigente.",
            icono="alert-triangle.svg",
        )

        self._mensaje_enlace_invalido = QLabel()
        self._mensaje_enlace_invalido.setWordWrap(True)
        self._mensaje_enlace_invalido.setObjectName("textoExplicativo")
        contenido.addWidget(self._mensaje_enlace_invalido)
        contenido.addWidget(
            self._crear_boton_secundario(
                texto="Volver al login",
                icono="arrow-left.svg",
                accion=self.volver_a_login_solicitado.emit,
            )
        )
        return pagina

    def _crear_pagina_base(self) -> tuple[QWidget, QFrame, QVBoxLayout]:
        pagina = QWidget()
        pagina.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        pagina.setObjectName("paginaAutenticacion")
        layout_raiz = QVBoxLayout(pagina)
        layout_raiz.setContentsMargins(48, 40, 48, 40)
        layout_raiz.setSpacing(0)
        layout_raiz.addStretch(1)

        fila_centrada = QHBoxLayout()
        fila_centrada.setContentsMargins(0, 0, 0, 0)
        fila_centrada.setSpacing(0)
        fila_centrada.addStretch(1)

        tarjeta = QFrame()
        tarjeta.setObjectName("tarjetaAutenticacion")
        tarjeta.setMaximumWidth(ANCHO_MAXIMO_TARJETA)
        tarjeta.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Maximum,
        )
        tarjeta.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        tarjeta.setGraphicsEffect(self._crear_sombra_tarjeta())

        layout_tarjeta = QVBoxLayout(tarjeta)
        layout_tarjeta.setContentsMargins(38, 38, 38, 38)
        layout_tarjeta.setSpacing(18)

        fila_centrada.addWidget(tarjeta, 1)
        fila_centrada.addStretch(1)
        layout_raiz.addLayout(fila_centrada)
        layout_raiz.addStretch(1)
        return pagina, tarjeta, layout_tarjeta

    def _agregar_logo(self, tarjeta: QFrame) -> None:
        ruta_logo = self._gestor_rutas.obtener_ruta_logo_marca()
        if not ruta_logo.exists():
            return

        pixmap_logo = QPixmap(str(ruta_logo))
        if pixmap_logo.isNull():
            return

        label_logo = QLabel()
        label_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label_logo.setPixmap(
            pixmap_logo.scaledToWidth(156, Qt.TransformationMode.SmoothTransformation)
        )
        tarjeta.layout().addWidget(label_logo)

    def _agregar_encabezado(
        self,
        layout_destino: QVBoxLayout,
        titulo: str,
        subtitulo: str,
        icono: str | None = None,
    ) -> None:
        if icono:
            label_icono = QLabel()
            label_icono.setObjectName("emblemaPagina")
            pixmap = obtener_pixmap_tabler_coloreado(
                nombre_icono=icono,
                color_hexadecimal=COLOR_ICONO_ESTADO,
                tamano=42,
            )
            label_icono.setPixmap(pixmap)
            label_icono.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout_destino.addWidget(label_icono)

        label_titulo = QLabel(titulo)
        label_titulo.setObjectName("tituloPagina")
        label_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label_titulo.setWordWrap(True)
        layout_destino.addWidget(label_titulo)

        label_subtitulo = QLabel(subtitulo)
        label_subtitulo.setObjectName("subtituloPagina")
        label_subtitulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label_subtitulo.setWordWrap(True)
        layout_destino.addWidget(label_subtitulo)

    def _crear_bloque_campo(self, etiqueta: str, campo: QLineEdit) -> QVBoxLayout:
        layout = QVBoxLayout()
        layout.setSpacing(8)
        label = QLabel(etiqueta)
        label.setObjectName("etiquetaCampo")
        layout.addWidget(label)
        layout.addWidget(campo)
        return layout

    def _crear_input(
        self,
        placeholder: str,
        icono: str,
        es_password: bool = False,
    ) -> QLineEdit:
        campo = QLineEdit()
        campo.setPlaceholderText(placeholder)
        campo.setClearButtonEnabled(not es_password)
        campo.addAction(
            obtener_icono_tabler_coloreado(icono, COLOR_ICONO_INPUT, tamano=18),
            QLineEdit.ActionPosition.LeadingPosition,
        )
        if es_password:
            campo.setEchoMode(QLineEdit.EchoMode.Password)
            accion_visibilidad = campo.addAction(
                obtener_icono_tabler_coloreado("eye.svg", COLOR_ICONO_INPUT, tamano=18),
                QLineEdit.ActionPosition.TrailingPosition,
            )
            accion_visibilidad.setToolTip("Mostrar contrasena")
            accion_visibilidad.triggered.connect(
                lambda checked=False, line_edit=campo, accion=accion_visibilidad: (
                    self._alternar_visibilidad_contrasena(line_edit, accion)
                )
            )
        return campo

    def _crear_boton_primario(
        self,
        texto: str,
        icono: str,
        accion: object,
    ) -> QPushButton:
        boton = QPushButton(texto)
        boton.setObjectName("botonPrimario")
        boton.setCursor(Qt.CursorShape.PointingHandCursor)
        boton.setIcon(
            obtener_icono_tabler_coloreado(icono, COLOR_ICONO_PRIMARIO, tamano=18)
        )
        boton.setIconSize(QSize(18, 18))
        boton.clicked.connect(accion)
        return boton

    def _crear_boton_secundario(
        self,
        texto: str,
        icono: str,
        accion: object,
    ) -> QPushButton:
        boton = QPushButton(texto)
        boton.setObjectName("botonSecundario")
        boton.setCursor(Qt.CursorShape.PointingHandCursor)
        boton.setIcon(
            obtener_icono_tabler_coloreado(icono, COLOR_ICONO_SECUNDARIO, tamano=18)
        )
        boton.setIconSize(QSize(18, 18))
        boton.clicked.connect(accion)
        return boton

    @staticmethod
    def _crear_sombra_tarjeta() -> QGraphicsDropShadowEffect:
        sombra = QGraphicsDropShadowEffect()
        sombra.setBlurRadius(38)
        sombra.setOffset(0, 18)
        sombra.setColor(QColor(15, 31, 57, 68))
        return sombra

    @staticmethod
    def _alternar_visibilidad_contrasena(campo: QLineEdit, accion_visibilidad: object) -> None:
        es_visible = campo.echoMode() == QLineEdit.EchoMode.Normal
        if es_visible:
            campo.setEchoMode(QLineEdit.EchoMode.Password)
            accion_visibilidad.setIcon(
                obtener_icono_tabler_coloreado("eye.svg", COLOR_ICONO_INPUT, tamano=18)
            )
            accion_visibilidad.setToolTip("Mostrar contrasena")
            return

        campo.setEchoMode(QLineEdit.EchoMode.Normal)
        accion_visibilidad.setIcon(
            obtener_icono_tabler_coloreado("eye-off.svg", COLOR_ICONO_INPUT, tamano=18)
        )
        accion_visibilidad.setToolTip("Ocultar contrasena")

    @staticmethod
    def _crear_label_mensaje() -> QLabel:
        label = QLabel()
        label.setWordWrap(True)
        label.setVisible(False)
        return label

    @staticmethod
    def _mostrar_mensaje(label: QLabel, mensaje: str, es_exito: bool) -> None:
        color_borde = "#0f9f6e" if es_exito else "#d14343"
        color_texto = "#0f5132" if es_exito else "#8f1d1d"
        color_fondo = "#ebfff5" if es_exito else "#fff3f3"
        label.setStyleSheet(
            "QLabel {"
            f"border: 1px solid {color_borde};"
            f"color: {color_texto};"
            f"background-color: {color_fondo};"
            "border-radius: 12px;"
            "padding: 12px 14px;"
            "}"
        )
        label.setText(mensaje)
        label.setVisible(True)

    @staticmethod
    def _limpiar_mensaje(label: QLabel) -> None:
        label.clear()
        label.setVisible(False)
        label.setStyleSheet("")

    def _emitir_login(self) -> None:
        self.iniciar_sesion_solicitada.emit(
            self._campo_usuario.text(),
            self._campo_contrasena.text(),
        )

    def _emitir_recuperacion(self) -> None:
        self.recuperacion_solicitada.emit(self._campo_correo.text())

    def _emitir_token_prueba(self) -> None:
        if self._token_prueba_visible:
            self.token_prueba_solicitado.emit(self._token_prueba_visible)

    def _emitir_restablecimiento(self) -> None:
        self.restablecimiento_solicitado.emit(
            self._token_recuperacion_actual,
            self._campo_nueva_contrasena.text(),
            self._campo_confirmacion_contrasena.text(),
        )

    def _aplicar_estilos(self) -> None:
        self.setStyleSheet(
            """
            QWidget#vistaAutenticacion {
                background: transparent;
            }
            QStackedWidget#stackAutenticacion,
            QWidget#paginaAutenticacion {
                background: transparent;
            }
            QFrame#tarjetaAutenticacion {
                background: qlineargradient(
                    x1: 0, y1: 0,
                    x2: 0.95, y2: 1,
                    stop: 0 rgba(255, 255, 255, 0.985),
                    stop: 1 rgba(243, 248, 252, 0.965)
                );
                border: 1px solid rgba(232, 241, 248, 0.95);
                border-radius: 28px;
            }
            QLabel#emblemaPagina {
                color: #1f2c51;
                margin-bottom: 6px;
            }
            QLabel#tituloPagina {
                color: #10233d;
                font-size: 30px;
                font-weight: 700;
            }
            QLabel#subtituloPagina,
            QLabel#textoExplicativo {
                color: #4a6279;
                font-size: 14px;
                line-height: 1.4;
            }
            QLabel#pieLogin {
                color: #6d8094;
                font-size: 12px;
                font-weight: 500;
                padding-top: 6px;
            }
            QLabel#etiquetaCampo {
                color: #17324d;
                font-size: 13px;
                font-weight: 600;
            }
            QLineEdit {
                min-height: 46px;
                padding: 0 12px;
                border: 1px solid #c4d1dd;
                border-radius: 15px;
                background-color: #f8fbfd;
                color: #10233d;
                selection-background-color: #cfe3ff;
            }
            QLineEdit:focus {
                border: 1px solid #1abc9c;
                background-color: #ffffff;
            }
            QPushButton#botonPrimario {
                min-height: 46px;
                border: none;
                border-radius: 15px;
                background-color: #1f2c51;
                color: #ffffff;
                font-size: 14px;
                font-weight: 600;
                padding: 0 16px;
            }
            QPushButton#botonPrimario:hover {
                background-color: #22345f;
            }
            QPushButton#botonPrimario:pressed {
                background-color: #17213d;
            }
            QPushButton#botonSecundario {
                min-height: 42px;
                border: 1px solid #c4d1dd;
                border-radius: 15px;
                background-color: rgba(255, 255, 255, 0.85);
                color: #17324d;
                font-size: 14px;
                font-weight: 600;
                padding: 0 16px;
            }
            QPushButton#botonSecundario:hover {
                background-color: rgba(247, 250, 252, 0.98);
            }
            QFrame#panelTokenPrueba {
                border: 1px dashed #93aac6;
                border-radius: 16px;
                background-color: #f5fbff;
            }
            """
        )
