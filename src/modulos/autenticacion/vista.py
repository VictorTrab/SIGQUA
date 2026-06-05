"""Vista PySide6 del modulo de autenticacion."""

from __future__ import annotations

from PySide6.QtCore import (
    QEasingCurve,
    QParallelAnimationGroup,
    QPropertyAnimation,
    QSize,
    Qt,
    QTimer,
    QVariantAnimation,
    Signal,
)
from PySide6.QtGui import (
    QColor,
)
from PySide6.QtWidgets import (
    QGraphicsBlurEffect,
    QFrame,
    QGraphicsDropShadowEffect,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from comun.configuracion.gestor_rutas import VERSION_SISTEMA, GestorRutas
from comun.ui import (
    obtener_icono_tabler_coloreado,
    obtener_pixmap_marca,
    obtener_pixmap_tabler_coloreado,
)
from modulos.autenticacion.entidades import SesionIniciada, UsuarioAutenticado


ANCHO_MAXIMO_TARJETA = 410
UMBRAL_PANEL_INSTITUCIONAL = 720
COLOR_GRADIENTE_INICIAL = "#001D39"
COLOR_GRADIENTE_FINAL = "#7BBDE8"
COLOR_ICONO_INPUT = "#0A6F8F"
COLOR_ICONO_PRIMARIO = "#FFFFFF"
COLOR_ICONO_SECUNDARIO = "#0A4174"
COLOR_ICONO_ESTADO = "#75C7F0"
COLOR_ICONO_ADVERTENCIA = "#F5B84B"
TAMANO_ICONO_ACCION_INPUT = 18
TAMANO_AREA_ACCION_INPUT = 28
DESPLAZAMIENTO_ACCION_DERECHA_INPUT = 14


def _interpolar_color(color_inicial: QColor, color_final: QColor, progreso: float) -> QColor:
    progreso_normalizado = max(0.0, min(1.0, progreso))
    return QColor(
        int(color_inicial.red() + (color_final.red() - color_inicial.red()) * progreso_normalizado),
        int(color_inicial.green() + (color_final.green() - color_inicial.green()) * progreso_normalizado),
        int(color_inicial.blue() + (color_final.blue() - color_inicial.blue()) * progreso_normalizado),
        int(color_inicial.alpha() + (color_final.alpha() - color_inicial.alpha()) * progreso_normalizado),
    )


class CampoAnimado(QLineEdit):
    """Input con realce suave para foco compatible con PySide6."""

    def __init__(self) -> None:
        super().__init__()
        self._progreso_realce = 0.0
        self._desplazamiento_accion_derecha = 0
        self._animacion_realce = QVariantAnimation(self)
        self._animacion_realce.setDuration(160)
        self._animacion_realce.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._animacion_realce.valueChanged.connect(self._actualizar_progreso_realce)

        self._sombra = QGraphicsDropShadowEffect(self)
        self._sombra.setOffset(0, 8)
        self._sombra.setBlurRadius(16)
        self._sombra.setColor(QColor(56, 189, 248, 0))
        self.setGraphicsEffect(self._sombra)
        self._aplicar_estilo_animado()
        QTimer.singleShot(0, self._ajustar_accion_derecha)

    def focusInEvent(self, evento) -> None:
        super().focusInEvent(evento)
        self._animar_realce_hacia(1.0)

    def focusOutEvent(self, evento) -> None:
        super().focusOutEvent(evento)
        self._animar_realce_hacia(0.0)

    def resizeEvent(self, evento) -> None:
        super().resizeEvent(evento)
        self._ajustar_accion_derecha()

    def showEvent(self, evento) -> None:
        super().showEvent(evento)
        QTimer.singleShot(0, self._ajustar_accion_derecha)

    def configurar_desplazamiento_accion_derecha(self, pixeles: int) -> None:
        self._desplazamiento_accion_derecha = max(0, pixeles)
        QTimer.singleShot(0, self._ajustar_accion_derecha)

    def _animar_realce_hacia(self, destino: float) -> None:
        self._animacion_realce.stop()
        self._animacion_realce.setStartValue(self._progreso_realce)
        self._animacion_realce.setEndValue(destino)
        self._animacion_realce.start()

    def _ajustar_accion_derecha(self) -> None:
        botones_accion = [
            boton for boton in self.findChildren(QToolButton) if boton.isVisible()
        ]
        if not botones_accion:
            return

        for boton in botones_accion:
            boton.setAutoRaise(True)
            boton.setCursor(Qt.CursorShape.PointingHandCursor)
            boton.setFixedSize(TAMANO_AREA_ACCION_INPUT, TAMANO_AREA_ACCION_INPUT)
            boton.setIconSize(QSize(TAMANO_ICONO_ACCION_INPUT, TAMANO_ICONO_ACCION_INPUT))
            boton.setStyleSheet(
                "QToolButton {"
                "background: transparent;"
                "border: none;"
                "padding: 0;"
                "margin: 0;"
                "}"
            )
            boton.move(boton.x(), max(0, (self.height() - boton.height()) // 2))

        if self._desplazamiento_accion_derecha <= 0:
            return

        boton_derecho = max(botones_accion, key=lambda boton: boton.x())
        posicion_x = self.width() - boton_derecho.width() - self._desplazamiento_accion_derecha
        boton_derecho.move(max(0, posicion_x), max(0, (self.height() - boton_derecho.height()) // 2))

    def _actualizar_progreso_realce(self, valor: object) -> None:
        self._progreso_realce = float(valor)
        self._aplicar_estilo_animado()

    def _aplicar_estilo_animado(self) -> None:
        borde = _interpolar_color(
            QColor(209, 213, 219, 255),
            QColor(0, 175, 160, 255),
            self._progreso_realce,
        )
        fondo = _interpolar_color(
            QColor(255, 255, 255, 255),
            QColor(244, 250, 255, 255),
            self._progreso_realce,
        )
        sombra = _interpolar_color(
            QColor(10, 111, 143, 0),
            QColor(10, 111, 143, 28),
            self._progreso_realce,
        )
        self._sombra.setBlurRadius(12 + (self._progreso_realce * 8))
        self._sombra.setColor(sombra)
        self.setStyleSheet(
            "QLineEdit {"
            "min-height: 52px;"
            "padding: 0 16px;"
            f"border: 1px solid rgba({borde.red()}, {borde.green()}, {borde.blue()}, {borde.alpha()});"
            "border-radius: 14px;"
            f"background-color: rgba({fondo.red()}, {fondo.green()}, {fondo.blue()}, {fondo.alpha()});"
            "color: #172A3A;"
            "selection-background-color: #0A6F8F;"
            "selection-color: #FFFFFF;"
            "font-size: 15px;"
            "}"
        )


class BotonAnimado(QPushButton):
    """Boton con transiciones discretas para hover y pressed."""

    def __init__(self, texto: str, variante: str) -> None:
        super().__init__(texto)
        self._variante = variante
        self._progreso_interaccion = 0.0
        self._animacion_interaccion = QVariantAnimation(self)
        self._animacion_interaccion.setDuration(140)
        self._animacion_interaccion.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._animacion_interaccion.valueChanged.connect(self._actualizar_progreso_interaccion)

        self._sombra = QGraphicsDropShadowEffect(self)
        self._sombra.setOffset(0, 10)
        self._sombra.setBlurRadius(18)
        self._sombra.setColor(QColor(10, 23, 40, 0))
        self.setGraphicsEffect(self._sombra)
        self._aplicar_estilo_animado()

    def enterEvent(self, evento) -> None:
        super().enterEvent(evento)
        self._animar_interaccion_hacia(1.0)

    def leaveEvent(self, evento) -> None:
        super().leaveEvent(evento)
        self._animar_interaccion_hacia(0.0)

    def mousePressEvent(self, evento) -> None:
        super().mousePressEvent(evento)
        self._animar_interaccion_hacia(1.9)

    def mouseReleaseEvent(self, evento) -> None:
        super().mouseReleaseEvent(evento)
        self._animar_interaccion_hacia(1.0 if self.rect().contains(evento.position().toPoint()) else 0.0)

    def _animar_interaccion_hacia(self, destino: float) -> None:
        self._animacion_interaccion.stop()
        self._animacion_interaccion.setStartValue(self._progreso_interaccion)
        self._animacion_interaccion.setEndValue(destino)
        self._animacion_interaccion.start()

    def _actualizar_progreso_interaccion(self, valor: object) -> None:
        self._progreso_interaccion = float(valor)
        self._aplicar_estilo_animado()

    def _aplicar_estilo_animado(self) -> None:
        if self._variante == "primario":
            self._aplicar_estilo_primario()
            return
        self._aplicar_estilo_secundario()

    def _aplicar_estilo_primario(self) -> None:
        base = QColor(0, 191, 166, 255)
        hover = QColor(0, 168, 145, 255)
        pressed = QColor(0, 140, 122, 255)
        color_actual = self._color_por_progreso(base, hover, pressed)
        sombra = _interpolar_color(
            QColor(0, 191, 166, 0),
            QColor(0, 191, 166, 72),
            min(self._progreso_interaccion, 1.0),
        )
        self._sombra.setBlurRadius(18 + min(self._progreso_interaccion, 1.0) * 10)
        self._sombra.setColor(sombra)
        self.setStyleSheet(
            "QPushButton {"
            "min-height: 50px;"
            "border: none;"
            "border-radius: 8px;"
            f"background-color: rgba({color_actual.red()}, {color_actual.green()}, {color_actual.blue()}, {color_actual.alpha()});"
            "color: #FFFFFF;"
            "font-size: 15px;"
            "font-weight: 700;"
            "padding: 0 18px;"
            "}"
            "QPushButton:disabled {"
            "background-color: rgba(0, 191, 166, 0.52);"
            "color: rgba(255, 255, 255, 0.92);"
            "}"
        )

    def _aplicar_estilo_secundario(self) -> None:
        base_fondo = QColor(255, 255, 255, 0)
        hover_fondo = QColor(0, 191, 166, 14)
        pressed_fondo = QColor(0, 191, 166, 24)
        base_borde = QColor(255, 255, 255, 0)
        hover_borde = QColor(255, 255, 255, 0)
        pressed_borde = QColor(255, 255, 255, 0)
        fondo_actual = self._color_por_progreso(base_fondo, hover_fondo, pressed_fondo)
        borde_actual = self._color_por_progreso(base_borde, hover_borde, pressed_borde)
        sombra = _interpolar_color(
            QColor(10, 23, 40, 0),
            QColor(10, 23, 40, 72),
            min(self._progreso_interaccion, 1.0),
        )
        self._sombra.setBlurRadius(14 + min(self._progreso_interaccion, 1.0) * 6)
        self._sombra.setColor(sombra)
        self.setStyleSheet(
            "QPushButton {"
            "min-height: 36px;"
            f"border: 1px solid rgba({borde_actual.red()}, {borde_actual.green()}, {borde_actual.blue()}, {borde_actual.alpha()});"
            "border-radius: 8px;"
            f"background-color: rgba({fondo_actual.red()}, {fondo_actual.green()}, {fondo_actual.blue()}, {fondo_actual.alpha()});"
            "color: #00AFA0;"
            "font-size: 13px;"
            "font-weight: 600;"
            "padding: 0 10px;"
            "}"
            "QPushButton:disabled {"
            "border-color: rgba(255, 255, 255, 0);"
            "background-color: transparent;"
            "color: rgba(0, 175, 160, 0.5);"
            "}"
        )

    def _color_por_progreso(self, base: QColor, hover: QColor, pressed: QColor) -> QColor:
        if self._progreso_interaccion <= 1.0:
            return _interpolar_color(base, hover, self._progreso_interaccion)
        return _interpolar_color(hover, pressed, self._progreso_interaccion - 1.0)


class VistaAutenticacion(QWidget):
    """Renderiza el flujo local de autenticacion usando layouts adaptables."""

    iniciar_sesion_solicitada = Signal(str, str)
    ir_a_olvido_solicitado = Signal()
    restablecimiento_solicitado = Signal(str, str, str)
    volver_a_login_solicitado = Signal()
    autenticacion_exitosa = Signal(object)

    def __init__(self, gestor_rutas: GestorRutas | None = None) -> None:
        super().__init__()
        self._gestor_rutas = gestor_rutas or GestorRutas()
        self._usuario_restablecimiento_actual = ""
        self._login_en_progreso = False
        self._tarjetas_por_pagina: dict[QWidget, QFrame] = {}
        self._paneles_institucionales: list[QFrame] = []
        self._animaciones_activas: list[object] = []

        self.setObjectName("vistaAutenticacion")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumSize(0, 0)
        self._aplicar_estilos()

        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.setSpacing(0)
        layout_principal.setSizeConstraint(QVBoxLayout.SizeConstraint.SetNoConstraint)

        self._stack = QStackedWidget()
        self._stack.setObjectName("stackAutenticacion")
        self._stack.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout_principal.addWidget(self._stack)

        self._pagina_login = self._construir_pagina_login()
        self._pagina_olvido = self._construir_pagina_olvido()
        self._pagina_restablecer = self._construir_pagina_restablecer()

        for pagina in (
            self._pagina_login,
            self._pagina_olvido,
            self._pagina_restablecer,
        ):
            self._stack.addWidget(pagina)

        QTimer.singleShot(0, lambda: self._animar_entrada_pagina(self._pagina_login))

    def resizeEvent(self, evento) -> None:
        super().resizeEvent(evento)
        self._actualizar_paneles_institucionales()

    def mostrar_login(self, mensaje: str | None = None, es_exito: bool = False) -> None:
        self._usuario_restablecimiento_actual = ""
        self.restablecer_estado_login()
        self._limpiar_mensaje(self._mensaje_olvido)
        self._limpiar_mensaje(self._mensaje_restablecer)
        self._campo_usuario.clear()
        self._campo_contrasena.clear()
        self._campo_nueva_contrasena.clear()
        self._campo_confirmacion_contrasena.clear()
        self._mostrar_pagina(self._pagina_login, self._campo_usuario)
        if mensaje:
            self._mostrar_mensaje(self._mensaje_login, mensaje, es_exito=es_exito)
        else:
            self._limpiar_mensaje(self._mensaje_login)

    def mostrar_error_login(self, mensaje: str) -> None:
        self.restablecer_estado_login()
        self._mostrar_mensaje(self._mensaje_login, mensaje, es_exito=False)

    def mostrar_olvido_contrasena(self) -> None:
        self.restablecer_estado_login()
        self._limpiar_mensaje(self._mensaje_olvido)
        self._mostrar_pagina(self._pagina_olvido)

    def mostrar_restablecer(
        self,
        nombre_usuario: str,
        mensaje: str | None = None,
    ) -> None:
        self.restablecer_estado_login()
        self._usuario_restablecimiento_actual = nombre_usuario.strip()
        self._campo_nueva_contrasena.clear()
        self._campo_confirmacion_contrasena.clear()
        self._mostrar_pagina(self._pagina_restablecer, self._campo_nueva_contrasena)
        self._label_usuario_restablecer.setText(
            f"Usuario a actualizar: {self._usuario_restablecimiento_actual or 'Pendiente'}"
        )
        if mensaje:
            self._mostrar_mensaje(self._mensaje_restablecer, mensaje, es_exito=True)
        else:
            self._limpiar_mensaje(self._mensaje_restablecer)

    def mostrar_error_restablecer(self, mensaje: str) -> None:
        self._mostrar_mensaje(self._mensaje_restablecer, mensaje, es_exito=False)

    def mostrar_exito(self, mensaje: str) -> None:
        self.mostrar_login(mensaje=mensaje, es_exito=True)

    def mostrar_estado_validando_login(self) -> None:
        self._establecer_estado_acceso_login(True, "Verificando credenciales...")

    def mostrar_estado_arranque_login(self, mensaje: str) -> None:
        self._establecer_estado_acceso_login(True, mensaje.strip() or "Accediendo...")

    def restablecer_estado_login(self) -> None:
        self._establecer_estado_acceso_login(False)

    def login_en_progreso(self) -> bool:
        return self._login_en_progreso

    def limpiar_campos_sensibles(self) -> None:
        self._campo_contrasena.clear()
        self._campo_nueva_contrasena.clear()
        self._campo_confirmacion_contrasena.clear()

    def notificar_autenticacion_exitosa(
        self,
        usuario: UsuarioAutenticado,
        token_sesion: str,
    ) -> None:
        self.autenticacion_exitosa.emit(
            SesionIniciada(usuario=usuario, token_sesion=token_sesion)
        )

    def _construir_pagina_login(self) -> QWidget:
        pagina, _, contenido = self._crear_pagina_base()
        self._agregar_encabezado(
            contenido,
            contexto="Acceso seguro",
            titulo="Bienvenido",
            subtitulo="Inicia sesión para continuar",
            alineacion=Qt.AlignmentFlag.AlignLeft,
        )
        contenido.addSpacing(8)

        self._campo_usuario = self._crear_input(
            placeholder="Nombre de usuario",
            icono=None,
        )
        self._campo_contrasena = self._crear_input(
            placeholder="Ingrese su contraseña",
            icono=None,
            es_password=True,
        )
        self._campo_contrasena.returnPressed.connect(self._emitir_login)

        contenido.addLayout(self._crear_bloque_campo("Usuario", self._campo_usuario))
        contenido.addLayout(
            self._crear_bloque_campo("Contraseña", self._campo_contrasena)
        )

        self._mensaje_login = self._crear_label_mensaje()
        contenido.addWidget(self._mensaje_login)
        contenido.addSpacing(2)

        self._boton_login = self._crear_boton_primario(
            texto="Iniciar sesión",
            icono="login-2.svg",
            accion=self._emitir_login,
        )
        contenido.addWidget(self._boton_login)
        self._texto_boton_login = self._boton_login.text()
        self._icono_boton_login = self._boton_login.icon()
        contenido.addSpacing(6)

        self._estado_acceso_login = self._crear_estado_acceso_login()
        contenido.addWidget(self._estado_acceso_login)
        contenido.addSpacing(4)

        self._bloque_ayuda_login = self._crear_bloque_ayuda_login()
        contenido.addLayout(self._bloque_ayuda_login)

        self._label_pie_login = QLabel("")
        self._label_pie_login.setObjectName("pieLogin")
        self._label_pie_login.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label_pie_login.setWordWrap(True)
        self._label_pie_login.setText(
            f"Junta de Agua de Yarumela · Versión {VERSION_SISTEMA}"
        )
        contenido.addSpacing(10)
        contenido.addWidget(self._label_pie_login)
        return pagina

    def _construir_pagina_olvido(self) -> QWidget:
        pagina, _, contenido = self._crear_pagina_base()
        self._agregar_encabezado(
            contenido,
            contexto="",
            titulo="Asistencia de acceso",
            subtitulo=(
                "El restablecimiento de acceso se gestiona por soporte o administración. "
                "Solicita asistencia para habilitar tu cambio de contraseña."
            ),
            icono="alert-triangle.svg",
            color_icono=COLOR_ICONO_ADVERTENCIA,
        )

        self._mensaje_olvido = self._crear_label_mensaje()
        contenido.addWidget(self._mensaje_olvido)
        contenido.addSpacing(8)
        contenido.addWidget(
            self._crear_boton_primario(
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
            contexto="",
            titulo="Actualizar contraseña",
            subtitulo=(
                "Define una nueva contraseña para continuar con tu acceso."
            ),
            icono="key.svg",
        )

        self._label_usuario_restablecer = QLabel("Usuario a actualizar: Pendiente")
        self._label_usuario_restablecer.setObjectName("textoExplicativo")
        self._label_usuario_restablecer.setWordWrap(True)
        contenido.addWidget(self._label_usuario_restablecer)

        self._campo_nueva_contrasena = self._crear_input(
            placeholder="Nueva contraseña",
            icono="lock.svg",
            es_password=True,
        )
        self._campo_confirmacion_contrasena = self._crear_input(
            placeholder="Confirmar contraseña",
            icono="lock.svg",
            es_password=True,
        )
        self._campo_confirmacion_contrasena.returnPressed.connect(
            self._emitir_restablecimiento
        )

        contenido.addLayout(
            self._crear_bloque_campo("Nueva contraseña", self._campo_nueva_contrasena)
        )
        contenido.addLayout(
            self._crear_bloque_campo(
                "Confirmar contraseña",
                self._campo_confirmacion_contrasena,
            )
        )

        self._mensaje_restablecer = self._crear_label_mensaje()
        contenido.addWidget(self._mensaje_restablecer)

        contenido.addWidget(
            self._crear_boton_primario(
                texto="Actualizar contraseña",
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

    def _crear_pagina_base(self) -> tuple[QWidget, QFrame, QVBoxLayout]:
        pagina = QWidget()
        pagina.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        pagina.setObjectName("paginaAutenticacion")
        pagina.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        pagina.setMinimumSize(0, 0)
        layout_raiz = QVBoxLayout(pagina)
        layout_raiz.setContentsMargins(0, 0, 0, 0)
        layout_raiz.setSpacing(0)
        layout_raiz.setSizeConstraint(QVBoxLayout.SizeConstraint.SetNoConstraint)

        fila_centrada = QHBoxLayout()
        fila_centrada.setContentsMargins(0, 0, 0, 0)
        fila_centrada.setSpacing(0)

        contenedor = QFrame()
        contenedor.setObjectName("contenedorAutenticacion")
        contenedor.setMinimumWidth(0)
        contenedor.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        contenedor.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        layout_contenedor = QHBoxLayout(contenedor)
        layout_contenedor.setContentsMargins(0, 0, 0, 0)
        layout_contenedor.setSpacing(0)

        panel_institucional = self._crear_panel_institucional_login()
        self._paneles_institucionales.append(panel_institucional)

        tarjeta = QFrame()
        tarjeta.setObjectName("panelFormularioLogin")
        tarjeta.setMaximumWidth(ANCHO_MAXIMO_TARJETA)
        tarjeta.setMinimumWidth(360)
        tarjeta.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        tarjeta.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        layout_tarjeta = QVBoxLayout(tarjeta)
        layout_tarjeta.setContentsMargins(42, 40, 42, 34)
        layout_tarjeta.setSpacing(0)
        layout_tarjeta.addStretch(1)

        layout_formulario = QVBoxLayout()
        layout_formulario.setContentsMargins(0, 0, 0, 0)
        layout_formulario.setSpacing(13)
        layout_tarjeta.addLayout(layout_formulario)
        layout_tarjeta.addStretch(1)

        layout_contenedor.addWidget(panel_institucional, 62)
        layout_contenedor.addWidget(tarjeta, 38)

        fila_centrada.addWidget(contenedor, 1)
        layout_raiz.addLayout(fila_centrada)
        self._tarjetas_por_pagina[pagina] = tarjeta
        QTimer.singleShot(0, self._actualizar_paneles_institucionales)
        return pagina, tarjeta, layout_formulario

    def _crear_panel_institucional_login(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("panelInstitucionalLogin")
        panel.setMinimumWidth(0)
        panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        panel.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self._crear_auroras_panel_login(panel)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(48, 84, 48, 64)
        layout.setSpacing(0)

        self._agregar_logo_institucional(layout)
        layout.addSpacing(28)

        subtitulo = QLabel("Sistema Integrado de Gestión\npara Juntas de Agua")
        subtitulo.setObjectName("subtituloSistemaLogin")
        subtitulo.setWordWrap(True)
        subtitulo.setMaximumWidth(560)
        layout.addWidget(subtitulo)
        layout.addSpacing(24)

        texto = QLabel(
            "Control local de abonados, casas, pagos y reportes en una "
            "plataforma administrativa segura."
        )
        texto.setObjectName("textoPrincipalLogin")
        texto.setWordWrap(True)
        texto.setMaximumWidth(560)
        layout.addWidget(texto)
        layout.addSpacing(34)

        fila_chips = QHBoxLayout()
        fila_chips.setContentsMargins(0, 0, 0, 0)
        fila_chips.setSpacing(12)
        fila_chips.addWidget(self._crear_chip_login("Abonados"))
        fila_chips.addWidget(self._crear_chip_login("Casas"))
        fila_chips.addWidget(self._crear_chip_login("Pagos"))
        fila_chips.addWidget(self._crear_chip_login("Reportes"))
        fila_chips.addStretch(1)
        layout.addLayout(fila_chips)

        layout.addStretch(1)

        separador = QFrame()
        separador.setObjectName("separadorPanelInstitucional")
        separador.setFixedHeight(1)
        separador.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        layout.addWidget(separador)
        layout.addSpacing(26)

        fila_footer = QHBoxLayout()
        fila_footer.setContentsMargins(0, 0, 0, 0)
        fila_footer.setSpacing(10)
        copyright_login = QLabel(f"© 2026 SIGQUA. Todos los derechos reservados.")
        copyright_login.setObjectName("copyrightLogin")
        fila_footer.addWidget(copyright_login)
        fila_footer.addStretch(1)
        estado_local = QLabel("●  Sistema local")
        estado_local.setObjectName("estadoLocalLogin")
        fila_footer.addWidget(estado_local)
        layout.addLayout(fila_footer)
        return panel

    @staticmethod
    def _crear_auroras_panel_login(panel: QFrame) -> None:
        auroras = (
            ("auroraLoginSuperior", -72, -54, 250, 250, 86),
            ("auroraLoginMedia", 218, 162, 330, 194, 98),
            ("auroraLoginInferior", 286, 478, 252, 252, 94),
        )
        for object_name, x, y, ancho, alto, blur in auroras:
            aurora = QFrame(panel)
            aurora.setObjectName(object_name)
            aurora.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
            aurora.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
            aurora.setGeometry(x, y, ancho, alto)
            efecto_blur = QGraphicsBlurEffect(aurora)
            efecto_blur.setBlurRadius(blur)
            aurora.setGraphicsEffect(efecto_blur)
            aurora.lower()

    @staticmethod
    def _crear_chip_login(texto: str) -> QLabel:
        chip = QLabel(texto)
        chip.setObjectName("chipLogin")
        chip.setAlignment(Qt.AlignmentFlag.AlignCenter)
        chip.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        chip.setMinimumHeight(38)
        chip.setMinimumWidth(
            {
                "Abonados": 96,
                "Casas": 74,
                "Pagos": 74,
                "Reportes": 96,
            }.get(texto, 84)
        )
        return chip

    def _agregar_logo_institucional(self, layout_destino: QVBoxLayout) -> None:
        ruta_logo = self._gestor_rutas.obtener_ruta_logo_marca()
        if not ruta_logo.exists():
            return

        pixmap_logo = obtener_pixmap_marca(
            ruta_marca=ruta_logo,
            ancho_logico=194,
            factor_escala=self.devicePixelRatioF(),
        )
        if pixmap_logo.isNull():
            return

        label_logo = QLabel()
        label_logo.setObjectName("logoMarcaLoginInstitucional")
        label_logo.setAlignment(Qt.AlignmentFlag.AlignLeft)
        label_logo.setPixmap(pixmap_logo)
        layout_destino.addWidget(label_logo, 0, Qt.AlignmentFlag.AlignLeft)

    def _actualizar_paneles_institucionales(self) -> None:
        mostrar_panel = self.width() >= UMBRAL_PANEL_INSTITUCIONAL
        for panel in self._paneles_institucionales:
            panel.setVisible(mostrar_panel)

    def _agregar_encabezado(
        self,
        layout_destino: QVBoxLayout,
        contexto: str,
        titulo: str,
        subtitulo: str,
        icono: str | None = None,
        color_icono: str = COLOR_ICONO_ESTADO,
        alineacion: Qt.AlignmentFlag = Qt.AlignmentFlag.AlignCenter,
    ) -> None:
        if contexto:
            layout_destino.addWidget(self._crear_badge_contexto(contexto), 0, alineacion)

        if icono:
            label_icono = QLabel()
            label_icono.setObjectName("emblemaPagina")
            pixmap = obtener_pixmap_tabler_coloreado(
                nombre_icono=icono,
                color_hexadecimal=color_icono,
                tamano=42,
            )
            label_icono.setPixmap(pixmap)
            label_icono.setAlignment(alineacion)
            layout_destino.addWidget(label_icono)

        if titulo:
            label_titulo = QLabel(titulo)
            label_titulo.setObjectName("tituloPagina")
            label_titulo.setAlignment(alineacion)
            label_titulo.setWordWrap(True)
            layout_destino.addWidget(label_titulo)

        if subtitulo:
            label_subtitulo = QLabel(subtitulo)
            label_subtitulo.setObjectName("subtituloPagina")
            label_subtitulo.setAlignment(alineacion)
            label_subtitulo.setWordWrap(True)
            layout_destino.addWidget(label_subtitulo)

    def _crear_bloque_campo(self, etiqueta: str, campo: QLineEdit) -> QVBoxLayout:
        layout = QVBoxLayout()
        layout.setSpacing(6)
        label = QLabel(etiqueta)
        label.setObjectName("etiquetaCampo")
        layout.addWidget(label)
        layout.addWidget(campo)
        return layout

    def _crear_input(
        self,
        placeholder: str,
        icono: str | None,
        es_password: bool = False,
        icono_a_la_derecha: bool = False,
    ) -> QLineEdit:
        campo = CampoAnimado()
        campo.setPlaceholderText(placeholder)
        campo.setClearButtonEnabled(False)
        campo.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        if icono:
            accion_icono = campo.addAction(
                obtener_icono_tabler_coloreado(icono, COLOR_ICONO_INPUT, tamano=18),
                (
                    QLineEdit.ActionPosition.TrailingPosition
                    if icono_a_la_derecha
                    else QLineEdit.ActionPosition.LeadingPosition
                ),
            )
            if icono_a_la_derecha:
                accion_icono.setObjectName("accionIconoUsuarioDerecha")
                campo.setProperty("icono_usuario_a_la_derecha", True)
        if es_password:
            campo.setEchoMode(QLineEdit.EchoMode.Password)
            accion_visibilidad = campo.addAction(
                obtener_icono_tabler_coloreado(
                    "eye.svg",
                    COLOR_ICONO_INPUT,
                    tamano=TAMANO_ICONO_ACCION_INPUT,
                ),
                QLineEdit.ActionPosition.TrailingPosition,
            )
            accion_visibilidad.setObjectName("accionVisibilidadContrasena")
            campo.configurar_desplazamiento_accion_derecha(DESPLAZAMIENTO_ACCION_DERECHA_INPUT)
            accion_visibilidad.setToolTip("Mostrar contraseña")
            accion_visibilidad.triggered.connect(
                lambda checked=False, line_edit=campo, accion=accion_visibilidad: (
                    self._alternar_visibilidad_contrasena(line_edit, accion)
                )
            )
        else:
            accion_limpiar = campo.addAction(
                obtener_icono_tabler_coloreado(
                    "x.svg",
                    COLOR_ICONO_INPUT,
                    tamano=TAMANO_ICONO_ACCION_INPUT,
                ),
                (
                    QLineEdit.ActionPosition.LeadingPosition
                    if icono_a_la_derecha
                    else QLineEdit.ActionPosition.TrailingPosition
                ),
            )
            accion_limpiar.setObjectName("accionLimpiarCampo")
            accion_limpiar.setToolTip("Limpiar campo")
            accion_limpiar.setVisible(False)
            accion_limpiar.triggered.connect(campo.clear)
            campo.textChanged.connect(
                lambda texto, accion=accion_limpiar, line_edit=campo: (
                    accion.setVisible(bool(texto)),
                    QTimer.singleShot(0, line_edit._ajustar_accion_derecha),
                )
            )
            campo.configurar_desplazamiento_accion_derecha(
                14 if icono_a_la_derecha else DESPLAZAMIENTO_ACCION_DERECHA_INPUT
            )
        return campo

    def _crear_boton_primario(
        self,
        texto: str,
        icono: str,
        accion: object,
    ) -> QPushButton:
        boton = BotonAnimado(texto, variante="primario")
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
        icono: str | None,
        accion: object,
    ) -> QPushButton:
        boton = BotonAnimado(texto, variante="secundario")
        boton.setObjectName("botonSecundario")
        boton.setCursor(Qt.CursorShape.PointingHandCursor)
        if icono:
            boton.setIcon(
                obtener_icono_tabler_coloreado(icono, COLOR_ICONO_SECUNDARIO, tamano=18)
            )
            boton.setIconSize(QSize(18, 18))
        boton.clicked.connect(accion)
        return boton

    def _crear_bloque_ayuda_login(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        layout.addStretch(1)

        texto_estatico = QLabel("¿Necesitas ayuda?")
        texto_estatico.setObjectName("textoAyudaLogin")
        texto_estatico.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(texto_estatico)

        enlace = QPushButton("Contacta al administrador")
        enlace.setObjectName("enlaceAyudaLogin")
        enlace.setCursor(Qt.CursorShape.PointingHandCursor)
        enlace.setFlat(True)
        enlace.clicked.connect(self.ir_a_olvido_solicitado.emit)
        self._enlace_ayuda_login = enlace
        layout.addWidget(enlace)

        layout.addStretch(1)
        return layout

    def _crear_estado_acceso_login(self) -> QFrame:
        contenedor = QFrame()
        contenedor.setObjectName("estadoAccesoLogin")
        contenedor.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        contenedor.setVisible(False)

        layout = QVBoxLayout(contenedor)
        layout.setContentsMargins(12, 9, 12, 9)
        layout.setSpacing(7)

        self._label_estado_acceso_login = QLabel("Accediendo...")
        self._label_estado_acceso_login.setObjectName("textoEstadoAccesoLogin")
        self._label_estado_acceso_login.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label_estado_acceso_login.setWordWrap(True)
        layout.addWidget(self._label_estado_acceso_login)

        self._barra_estado_acceso_login = QProgressBar()
        self._barra_estado_acceso_login.setObjectName("barraProgresoAccesoLogin")
        self._barra_estado_acceso_login.setRange(0, 0)
        self._barra_estado_acceso_login.setTextVisible(False)
        self._barra_estado_acceso_login.setFixedHeight(4)
        layout.addWidget(self._barra_estado_acceso_login)
        return contenedor

    def _establecer_estado_acceso_login(self, activo: bool, mensaje: str = "") -> None:
        if not hasattr(self, "_estado_acceso_login"):
            return

        self._login_en_progreso = activo
        self._campo_usuario.setEnabled(not activo)
        self._campo_contrasena.setEnabled(not activo)
        self._boton_login.setEnabled(not activo)
        self._enlace_ayuda_login.setEnabled(not activo)

        if activo:
            self._limpiar_mensaje(self._mensaje_login)
            self._label_estado_acceso_login.setText(mensaje or "Accediendo...")
            self._estado_acceso_login.setVisible(True)
            self._boton_login.setText("Accediendo...")
            self._boton_login.setIcon(self._icono_boton_login)
            return

        self._estado_acceso_login.setVisible(False)
        self._label_estado_acceso_login.setText("Accediendo...")
        self._boton_login.setText(self._texto_boton_login)
        self._boton_login.setIcon(self._icono_boton_login)

    def _crear_badge_contexto(self, texto: str) -> QWidget:
        contenedor = QFrame()
        contenedor.setObjectName("badgeContexto")
        contenedor.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        layout = QHBoxLayout(contenedor)
        layout.setContentsMargins(14, 6, 14, 6)
        layout.setSpacing(6)

        icono = QLabel()
        icono.setObjectName("badgeContextoIcono")
        icono.setPixmap(
            obtener_pixmap_tabler_coloreado(
                nombre_icono="lock.svg",
                color_hexadecimal="#008C7A",
                tamano=12,
            )
        )
        layout.addWidget(icono, 0, Qt.AlignmentFlag.AlignVCenter)

        label = QLabel(texto)
        label.setObjectName("badgeContextoTexto")
        layout.addWidget(label, 0, Qt.AlignmentFlag.AlignVCenter)
        return contenedor

    @staticmethod
    def _alternar_visibilidad_contrasena(campo: QLineEdit, accion_visibilidad: object) -> None:
        es_visible = campo.echoMode() == QLineEdit.EchoMode.Normal
        if es_visible:
            campo.setEchoMode(QLineEdit.EchoMode.Password)
            accion_visibilidad.setIcon(
                obtener_icono_tabler_coloreado(
                    "eye.svg",
                    COLOR_ICONO_INPUT,
                    tamano=TAMANO_ICONO_ACCION_INPUT,
                )
            )
            accion_visibilidad.setToolTip("Mostrar contraseña")
            return

        campo.setEchoMode(QLineEdit.EchoMode.Normal)
        accion_visibilidad.setIcon(
            obtener_icono_tabler_coloreado(
                "eye-off.svg",
                COLOR_ICONO_INPUT,
                tamano=TAMANO_ICONO_ACCION_INPUT,
            )
        )
        accion_visibilidad.setToolTip("Ocultar contraseña")

    @staticmethod
    def _crear_label_mensaje() -> QLabel:
        label = QLabel()
        label.setWordWrap(True)
        label.setMaximumHeight(0)
        label.setVisible(False)
        return label

    def _mostrar_mensaje(self, label: QLabel, mensaje: str, es_exito: bool) -> None:
        color_borde = "rgba(25, 135, 84, 0.22)" if es_exito else "rgba(180, 55, 55, 0.26)"
        color_texto = "#0F5132" if es_exito else "#842029"
        color_fondo = "rgba(55, 211, 153, 0.11)" if es_exito else "rgba(242, 116, 116, 0.13)"
        label.setStyleSheet(
            "QLabel {"
            f"border: 1px solid {color_borde};"
            f"color: {color_texto};"
            f"background-color: {color_fondo};"
            "border-radius: 10px;"
            "padding: 7px 12px;"
            "font-size: 12px;"
            "font-weight: 700;"
            "}"
        )
        label.setText(mensaje)
        label.setVisible(True)
        self._animar_mensaje(label)

    @staticmethod
    def _limpiar_mensaje(label: QLabel) -> None:
        label.clear()
        label.setVisible(False)
        label.setStyleSheet("")
        label.setMaximumHeight(0)
        label.setGraphicsEffect(None)

    def _emitir_login(self) -> None:
        if self._login_en_progreso:
            return
        self.iniciar_sesion_solicitada.emit(
            self._campo_usuario.text(),
            self._campo_contrasena.text(),
        )

    def _emitir_restablecimiento(self) -> None:
        self.restablecimiento_solicitado.emit(
            self._usuario_restablecimiento_actual,
            self._campo_nueva_contrasena.text(),
            self._campo_confirmacion_contrasena.text(),
        )

    def _mostrar_pagina(self, pagina: QWidget, campo_foco: QWidget | None = None) -> None:
        self._stack.setCurrentWidget(pagina)
        self._animar_entrada_pagina(pagina)
        if campo_foco is not None:
            QTimer.singleShot(110, campo_foco.setFocus)

    def _animar_entrada_pagina(self, pagina: QWidget) -> None:
        tarjeta = self._tarjetas_por_pagina.get(pagina)
        if tarjeta is None:
            return

        efecto_fade = QGraphicsOpacityEffect(tarjeta)
        tarjeta.setGraphicsEffect(efecto_fade)
        efecto_fade.setOpacity(0.0)

        animacion_opacidad = QPropertyAnimation(efecto_fade, b"opacity", tarjeta)
        animacion_opacidad.setDuration(220)
        animacion_opacidad.setStartValue(0.0)
        animacion_opacidad.setEndValue(1.0)
        animacion_opacidad.setEasingCurve(QEasingCurve.Type.OutCubic)

        grupo = QParallelAnimationGroup(tarjeta)
        grupo.addAnimation(animacion_opacidad)
        grupo._efecto_fade = efecto_fade

        def _limpiar_efecto() -> None:
            tarjeta.setGraphicsEffect(None)
            if grupo in self._animaciones_activas:
                self._animaciones_activas.remove(grupo)

        grupo.finished.connect(_limpiar_efecto)
        self._animaciones_activas.append(grupo)
        grupo.start()

    def _animar_mensaje(self, label: QLabel) -> None:
        efecto_opacidad = QGraphicsOpacityEffect(label)
        label.setGraphicsEffect(efecto_opacidad)
        efecto_opacidad.setOpacity(0.0)
        altura_destino = max(label.sizeHint().height() + 8, 38)
        label.setMaximumHeight(0)

        animacion_opacidad = QPropertyAnimation(efecto_opacidad, b"opacity", label)
        animacion_opacidad.setDuration(180)
        animacion_opacidad.setStartValue(0.0)
        animacion_opacidad.setEndValue(1.0)
        animacion_opacidad.setEasingCurve(QEasingCurve.Type.OutCubic)

        animacion_altura = QPropertyAnimation(label, b"maximumHeight", label)
        animacion_altura.setDuration(180)
        animacion_altura.setStartValue(0)
        animacion_altura.setEndValue(altura_destino)
        animacion_altura.setEasingCurve(QEasingCurve.Type.OutCubic)

        grupo = QParallelAnimationGroup(label)
        grupo.addAnimation(animacion_opacidad)
        grupo.addAnimation(animacion_altura)
        grupo._efecto_opacidad = efecto_opacidad

        def _liberar_animacion() -> None:
            label.setMaximumHeight(16777215)
            label.setGraphicsEffect(None)
            if grupo in self._animaciones_activas:
                self._animaciones_activas.remove(grupo)

        grupo.finished.connect(_liberar_animacion)
        self._animaciones_activas.append(grupo)
        grupo.start()

    def _aplicar_estilos(self) -> None:
        self.setStyleSheet(
            f"""
            QWidget#vistaAutenticacion {{
                background: qlineargradient(
                    x1: 0, y1: 0,
                    x2: 1, y2: 1,
                    stop: 0 #E8F4FA,
                    stop: 0.58 #F7FBFE,
                    stop: 1 #D7ECF6
                );
            }}
            QStackedWidget#stackAutenticacion,
            QWidget#paginaAutenticacion {{
                background: transparent;
            }}
            QFrame#contenedorAutenticacion {{
                background: transparent;
            }}
            QFrame#panelInstitucionalLogin {{
                background: qlineargradient(
                    x1: 0, y1: 0,
                    x2: 1, y2: 1,
                    stop: 0 #081C2E,
                    stop: 0.40 #123A50,
                    stop: 0.72 #087B82,
                    stop: 1 #00BFA6
                );
            }}
            QFrame#auroraLoginSuperior {{
                background: rgba(70, 218, 255, 0.18);
                border-radius: 125px;
            }}
            QFrame#auroraLoginMedia {{
                background: rgba(0, 191, 166, 0.16);
                border-radius: 97px;
            }}
            QFrame#auroraLoginInferior {{
                background: rgba(27, 161, 255, 0.16);
                border-radius: 126px;
            }}
            QFrame#panelFormularioLogin {{
                background: #FFFFFF;
            }}
            QLabel#logoMarcaLoginInstitucional {{
                margin-bottom: 0;
            }}
            QLabel#subtituloSistemaLogin {{
                color: #FFFFFF;
                font-size: 29px;
                font-weight: 900;
                line-height: 1.14;
            }}
            QLabel#textoPrincipalLogin {{
                color: rgba(222, 240, 252, 0.92);
                font-size: 18px;
                font-weight: 500;
                line-height: 1.35;
            }}
            QLabel#chipLogin {{
                color: #00D0B8;
                background-color: rgba(0, 208, 184, 0.13);
                border: 1px solid rgba(0, 208, 184, 0.30);
                border-radius: 16px;
                font-size: 11px;
                font-weight: 800;
                padding: 6px 10px;
            }}
            QFrame#separadorPanelInstitucional {{
                background: rgba(222, 240, 252, 0.18);
            }}
            QLabel#copyrightLogin {{
                color: rgba(222, 240, 252, 0.95);
                font-size: 13px;
                font-weight: 500;
            }}
            QLabel#estadoLocalLogin {{
                color: rgba(222, 240, 252, 0.95);
                font-size: 13px;
                font-weight: 600;
            }}
            QFrame#badgeContexto {{
                color: #008C7A;
                background-color: rgba(0, 191, 166, 0.08);
                border: 1px solid rgba(0, 191, 166, 0.28);
                border-radius: 12px;
                margin: 0 0 6px 0;
            }}
            QLabel#badgeContextoIcono {{
                color: #008C7A;
                margin: 0;
                padding: 0;
            }}
            QLabel#badgeContextoTexto {{
                color: #008C7A;
                font-size: 10px;
                font-weight: 800;
                letter-spacing: 0.3px;
            }}
            QLabel#emblemaPagina {{
                color: {COLOR_ICONO_SECUNDARIO};
                margin-bottom: -2px;
            }}
            QLabel#tituloPagina {{
                color: #0F172A;
                font-size: 32px;
                font-weight: 900;
                letter-spacing: 0.1px;
            }}
            QLabel#subtituloPagina,
            QLabel#textoExplicativo {{
                color: #5F5665;
                font-size: 16px;
                line-height: 1.25;
            }}
            QLabel#pieLogin {{
                color: #8D93A3;
                font-size: 12px;
                font-weight: 600;
                padding-top: 4px;
            }}
            QLabel#etiquetaCampo {{
                color: #111827;
                font-size: 13px;
                font-weight: 800;
                letter-spacing: 0.1px;
            }}
            QLabel#textoAyudaLogin {{
                color: #5F5665;
                font-size: 13px;
                font-weight: 500;
            }}
            QFrame#estadoAccesoLogin {{
                background: rgba(240, 249, 255, 0.96);
                border: 1px solid rgba(14, 165, 233, 0.14);
                border-radius: 12px;
            }}
            QLabel#textoEstadoAccesoLogin {{
                color: #0F5F73;
                font-size: 12px;
                font-weight: 700;
            }}
            QProgressBar#barraProgresoAccesoLogin {{
                border: none;
                border-radius: 2px;
                background: rgba(14, 165, 233, 0.12);
            }}
            QProgressBar#barraProgresoAccesoLogin::chunk {{
                border-radius: 2px;
                background: qlineargradient(
                    x1: 0, y1: 0,
                    x2: 1, y2: 0,
                    stop: 0 #00BFA6,
                    stop: 1 #38BDF8
                );
            }}
            QPushButton#enlaceAyudaLogin {{
                background: transparent;
                border: none;
                border-radius: 6px;
                color: #00AFA0;
                font-size: 13px;
                font-weight: 800;
                padding: 0 2px;
                text-align: left;
            }}
            QPushButton#enlaceAyudaLogin:hover {{
                background: rgba(0, 191, 166, 0.06);
                color: #009685;
            }}
            QPushButton#enlaceAyudaLogin:pressed {{
                background: rgba(0, 191, 166, 0.09);
                color: #008C7A;
            }}
            QPushButton#enlaceAyudaLogin:disabled {{
                background: transparent;
                color: #90A3B2;
            }}
            QLineEdit,
            QPushButton#botonPrimario,
            QPushButton#botonSecundario,
            QPushButton#enlaceAyudaLogin {{
                outline: none;
            }}
            """
        )
