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
    QFrame,
    QGraphicsDropShadowEffect,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
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


ANCHO_MAXIMO_TARJETA = 420
ANCHO_PANEL_AUTENTICACION = 720
UMBRAL_PANEL_INSTITUCIONAL = 720
COLOR_GRADIENTE_INICIAL = "#001D39"
COLOR_GRADIENTE_FINAL = "#7BBDE8"
COLOR_ICONO_INPUT = "#0A6F8F"
COLOR_ICONO_PRIMARIO = "#061525"
COLOR_ICONO_SECUNDARIO = "#0A4174"
COLOR_ICONO_ESTADO = "#75C7F0"
COLOR_ICONO_ADVERTENCIA = "#F5B84B"
TAMANO_ICONO_ACCION_INPUT = 18
TAMANO_AREA_ACCION_INPUT = 30
DESPLAZAMIENTO_ACCION_DERECHA_INPUT = 18


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
            QColor(189, 216, 233, 255),
            QColor(10, 111, 143, 255),
            self._progreso_realce,
        )
        fondo = _interpolar_color(
            QColor(255, 255, 255, 255),
            QColor(244, 250, 255, 255),
            self._progreso_realce,
        )
        sombra = _interpolar_color(
            QColor(10, 111, 143, 0),
            QColor(10, 111, 143, 42),
            self._progreso_realce,
        )
        self._sombra.setBlurRadius(16 + (self._progreso_realce * 12))
        self._sombra.setColor(sombra)
        self.setStyleSheet(
            "QLineEdit {"
            "min-height: 46px;"
            "padding: 0 18px;"
            f"border: 1px solid rgba({borde.red()}, {borde.green()}, {borde.blue()}, {borde.alpha()});"
            "border-radius: 16px;"
            f"background-color: rgba({fondo.red()}, {fondo.green()}, {fondo.blue()}, {fondo.alpha()});"
            "color: #172A3A;"
            "selection-background-color: #0A6F8F;"
            "selection-color: #FFFFFF;"
            "font-size: 13px;"
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
        base = QColor(10, 111, 143, 255)
        hover = QColor(11, 127, 163, 255)
        pressed = QColor(10, 65, 116, 255)
        color_actual = self._color_por_progreso(base, hover, pressed)
        sombra = _interpolar_color(
            QColor(10, 65, 116, 0),
            QColor(10, 65, 116, 66),
            min(self._progreso_interaccion, 1.0),
        )
        self._sombra.setBlurRadius(18 + min(self._progreso_interaccion, 1.0) * 10)
        self._sombra.setColor(sombra)
        self.setStyleSheet(
            "QPushButton {"
            "min-height: 46px;"
            "border: none;"
            "border-radius: 16px;"
            f"background-color: rgba({color_actual.red()}, {color_actual.green()}, {color_actual.blue()}, {color_actual.alpha()});"
            "color: #FFFFFF;"
            "font-size: 13px;"
            "font-weight: 700;"
            "padding: 0 18px;"
            "}"
        )

    def _aplicar_estilo_secundario(self) -> None:
        base_fondo = QColor(255, 255, 255, 255)
        hover_fondo = QColor(232, 245, 252, 255)
        pressed_fondo = QColor(210, 232, 244, 255)
        base_borde = QColor(189, 216, 233, 255)
        hover_borde = QColor(10, 111, 143, 160)
        pressed_borde = QColor(10, 65, 116, 210)
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
            "min-height: 43px;"
            f"border: 1px solid rgba({borde_actual.red()}, {borde_actual.green()}, {borde_actual.blue()}, {borde_actual.alpha()});"
            "border-radius: 16px;"
            f"background-color: rgba({fondo_actual.red()}, {fondo_actual.green()}, {fondo_actual.blue()}, {fondo_actual.alpha()});"
            "color: #0A4174;"
            "font-size: 13px;"
            "font-weight: 600;"
            "padding: 0 18px;"
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
        self._limpiar_mensaje(self._mensaje_olvido)
        self._limpiar_mensaje(self._mensaje_restablecer)
        self._campo_contrasena.clear()
        self._mostrar_pagina(self._pagina_login, self._campo_usuario)
        if mensaje:
            self._mostrar_mensaje(self._mensaje_login, mensaje, es_exito=es_exito)
        else:
            self._limpiar_mensaje(self._mensaje_login)

    def mostrar_error_login(self, mensaje: str) -> None:
        self._mostrar_mensaje(self._mensaje_login, mensaje, es_exito=False)

    def mostrar_olvido_contrasena(self) -> None:
        self._limpiar_mensaje(self._mensaje_olvido)
        self._mostrar_pagina(self._pagina_olvido)

    def mostrar_restablecer(
        self,
        nombre_usuario: str,
        mensaje: str | None = None,
    ) -> None:
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
        self._agregar_logo_compacto_formulario(contenido)
        self._agregar_encabezado(
            contenido,
            contexto="",
            titulo="Iniciar sesion",
            subtitulo="Acceso local al sistema administrativo SIGQUA.",
        )

        self._campo_usuario = self._crear_input(
            placeholder="Nombre de usuario",
            icono="user.svg",
        )
        self._campo_contrasena = self._crear_input(
            placeholder="Contraseña",
            icono="lock.svg",
            es_password=True,
        )
        self._campo_contrasena.returnPressed.connect(self._emitir_login)

        contenido.addLayout(self._crear_bloque_campo("Usuario", self._campo_usuario))
        contenido.addLayout(
            self._crear_bloque_campo("Contraseña", self._campo_contrasena)
        )

        self._mensaje_login = self._crear_label_mensaje()
        contenido.addWidget(self._mensaje_login)

        self._boton_login = self._crear_boton_primario(
            texto="Entrar",
            icono="login-2.svg",
            accion=self._emitir_login,
        )
        contenido.addWidget(self._boton_login)

        contenido.addWidget(
            self._crear_boton_secundario(
                texto="Necesito ayuda para acceder",
                icono="key.svg",
                accion=self.ir_a_olvido_solicitado.emit,
            )
        )

        self._label_pie_login = QLabel("")
        self._label_pie_login.setObjectName("pieLogin")
        self._label_pie_login.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label_pie_login.setWordWrap(True)
        self._label_pie_login.setText(
            f"SIGQUA · Junta de Agua de Yarumela · Versión {VERSION_SISTEMA}"
        )
        contenido.addWidget(self._label_pie_login)
        return pagina

    def _construir_pagina_olvido(self) -> QWidget:
        pagina, _, contenido = self._crear_pagina_base()
        self._agregar_logo_compacto_formulario(contenido)
        self._agregar_encabezado(
            contenido,
            contexto="",
            titulo="Asistencia de acceso",
            subtitulo=(
                "El restablecimiento de acceso se gestiona por soporte o administracion. "
                "Solicita asistencia para habilitar tu cambio de contraseña."
            ),
            icono="alert-triangle.svg",
            color_icono=COLOR_ICONO_ADVERTENCIA,
        )

        self._mensaje_olvido = self._crear_label_mensaje()
        contenido.addWidget(self._mensaje_olvido)
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
        self._agregar_logo_compacto_formulario(contenido)
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
        layout_raiz.setContentsMargins(22, 22, 22, 22)
        layout_raiz.setSpacing(0)
        layout_raiz.setSizeConstraint(QVBoxLayout.SizeConstraint.SetNoConstraint)
        layout_raiz.addStretch(1)

        fila_centrada = QHBoxLayout()
        fila_centrada.setContentsMargins(0, 0, 0, 0)
        fila_centrada.setSpacing(0)
        fila_centrada.addStretch(1)

        contenedor = QFrame()
        contenedor.setObjectName("contenedorAutenticacion")
        contenedor.setMaximumWidth(ANCHO_PANEL_AUTENTICACION)
        contenedor.setMinimumWidth(0)
        contenedor.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        contenedor.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        contenedor.setGraphicsEffect(self._crear_sombra_tarjeta())

        layout_contenedor = QHBoxLayout(contenedor)
        layout_contenedor.setContentsMargins(0, 0, 0, 0)
        layout_contenedor.setSpacing(0)

        panel_institucional = self._crear_panel_institucional_login()
        self._paneles_institucionales.append(panel_institucional)

        tarjeta = QFrame()
        tarjeta.setObjectName("panelFormularioLogin")
        tarjeta.setMaximumWidth(ANCHO_MAXIMO_TARJETA)
        tarjeta.setMinimumWidth(340)
        tarjeta.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        tarjeta.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        layout_tarjeta = QVBoxLayout(tarjeta)
        layout_tarjeta.setContentsMargins(34, 30, 34, 30)
        layout_tarjeta.setSpacing(12)

        layout_contenedor.addWidget(panel_institucional, 1)
        layout_contenedor.addWidget(tarjeta, 1)

        fila_centrada.addWidget(contenedor, 1)
        fila_centrada.addStretch(1)
        layout_raiz.addLayout(fila_centrada)
        layout_raiz.addStretch(1)
        self._tarjetas_por_pagina[pagina] = tarjeta
        QTimer.singleShot(0, self._actualizar_paneles_institucionales)
        return pagina, tarjeta, layout_tarjeta

    def _crear_panel_institucional_login(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("panelInstitucionalLogin")
        panel.setMinimumWidth(0)
        panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        panel.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(34, 32, 30, 32)
        layout.setSpacing(14)

        self._crear_decoracion_login(panel, "decoracionLoginSuperior")
        self._agregar_logo_institucional(layout)

        nombre = QLabel("SIGQUA")
        nombre.setObjectName("nombreSistemaLogin")
        nombre.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(nombre)

        subtitulo = QLabel("Gestion administrativa de la Junta de Agua de Yarumela")
        subtitulo.setObjectName("subtituloSistemaLogin")
        subtitulo.setWordWrap(True)
        layout.addWidget(subtitulo)

        texto = QLabel(
            "Control local de abonados, casas, pagos, morosidad y reportes "
            "en una operacion compacta y segura."
        )
        texto.setObjectName("textoPrincipalLogin")
        texto.setWordWrap(True)
        layout.addWidget(texto)

        fila_chips = QHBoxLayout()
        fila_chips.setContentsMargins(0, 4, 0, 4)
        fila_chips.setSpacing(8)
        fila_chips.addWidget(self._crear_chip_login("Abonados"))
        fila_chips.addWidget(self._crear_chip_login("Pagos"))
        fila_chips.addWidget(self._crear_chip_login("Reportes"))
        fila_chips.addStretch(1)
        layout.addLayout(fila_chips)

        layout.addStretch(1)

        microcopy = QLabel("Autenticacion local · Asistencia administrativa · Sin correo externo")
        microcopy.setObjectName("microcopyLogin")
        microcopy.setWordWrap(True)
        layout.addWidget(microcopy)

        self._crear_decoracion_login(panel, "decoracionLoginInferior")
        return panel

    @staticmethod
    def _crear_chip_login(texto: str) -> QLabel:
        chip = QLabel(texto)
        chip.setObjectName("chipLogin")
        chip.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return chip

    @staticmethod
    def _crear_decoracion_login(panel: QFrame, object_name: str) -> QLabel:
        decoracion = QLabel(panel)
        decoracion.setObjectName(object_name)
        decoracion.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        decoracion.resize(116, 116)
        if object_name.endswith("Superior"):
            decoracion.move(242, 18)
        else:
            decoracion.move(24, 392)
        decoracion.lower()
        return decoracion

    def _agregar_logo_institucional(self, layout_destino: QVBoxLayout) -> None:
        ruta_logo = self._gestor_rutas.obtener_ruta_logo_marca()
        if not ruta_logo.exists():
            return

        pixmap_logo = obtener_pixmap_marca(
            ruta_marca=ruta_logo,
            ancho_logico=176,
            factor_escala=self.devicePixelRatioF(),
        )
        if pixmap_logo.isNull():
            return

        label_logo = QLabel()
        label_logo.setObjectName("logoMarcaLoginInstitucional")
        label_logo.setAlignment(Qt.AlignmentFlag.AlignLeft)
        label_logo.setPixmap(pixmap_logo)
        layout_destino.addWidget(label_logo)

    def _agregar_logo_compacto_formulario(self, layout_destino: QVBoxLayout) -> None:
        ruta_logo = self._gestor_rutas.obtener_ruta_logo_marca()
        if not ruta_logo.exists():
            return

        pixmap_logo = obtener_pixmap_marca(
            ruta_marca=ruta_logo,
            ancho_logico=142,
            factor_escala=self.devicePixelRatioF(),
        )
        if pixmap_logo.isNull():
            return

        bloque_marca = QWidget()
        bloque_marca.setObjectName("bloqueMarcaLogin")
        layout_marca = QVBoxLayout(bloque_marca)
        layout_marca.setContentsMargins(0, 0, 0, 2)
        layout_marca.setSpacing(2)

        label_logo = QLabel()
        label_logo.setObjectName("logoMarcaLogin")
        label_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label_logo.setPixmap(pixmap_logo)
        brillo_logo = QGraphicsDropShadowEffect(label_logo)
        brillo_logo.setBlurRadius(14)
        brillo_logo.setOffset(0, 0)
        brillo_logo.setColor(QColor(10, 111, 143, 40))
        label_logo.setGraphicsEffect(brillo_logo)
        layout_marca.addWidget(label_logo)

        lema = QLabel("Sistema Integrado de Gestión para Juntas de Agua")
        lema.setObjectName("lemaMarcaLogin")
        lema.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lema.setWordWrap(True)
        layout_marca.addWidget(lema)
        layout_destino.addWidget(bloque_marca)

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
    ) -> None:
        if contexto:
            label_contexto = QLabel(contexto)
            label_contexto.setObjectName("badgeContexto")
            label_contexto.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout_destino.addWidget(label_contexto)

        if icono:
            label_icono = QLabel()
            label_icono.setObjectName("emblemaPagina")
            pixmap = obtener_pixmap_tabler_coloreado(
                nombre_icono=icono,
                color_hexadecimal=color_icono,
                tamano=42,
            )
            label_icono.setPixmap(pixmap)
            label_icono.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout_destino.addWidget(label_icono)

        if titulo:
            label_titulo = QLabel(titulo)
            label_titulo.setObjectName("tituloPagina")
            label_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label_titulo.setWordWrap(True)
            layout_destino.addWidget(label_titulo)

        if subtitulo:
            label_subtitulo = QLabel(subtitulo)
            label_subtitulo.setObjectName("subtituloPagina")
            label_subtitulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
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
        icono: str,
        es_password: bool = False,
    ) -> QLineEdit:
        campo = CampoAnimado()
        campo.setPlaceholderText(placeholder)
        campo.setClearButtonEnabled(False)
        campo.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        campo.addAction(
            obtener_icono_tabler_coloreado(icono, COLOR_ICONO_INPUT, tamano=18),
            QLineEdit.ActionPosition.LeadingPosition,
        )
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
                QLineEdit.ActionPosition.TrailingPosition,
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
            campo.configurar_desplazamiento_accion_derecha(DESPLAZAMIENTO_ACCION_DERECHA_INPUT)
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
        icono: str,
        accion: object,
    ) -> QPushButton:
        boton = BotonAnimado(texto, variante="secundario")
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
        sombra.setBlurRadius(78)
        sombra.setOffset(0, 22)
        sombra.setColor(QColor(3, 10, 22, 118))
        return sombra

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
        color_borde = "rgba(25, 135, 84, 0.30)" if es_exito else "rgba(180, 55, 55, 0.30)"
        color_texto = "#0F5132" if es_exito else "#842029"
        color_fondo = "rgba(55, 211, 153, 0.16)" if es_exito else "rgba(242, 116, 116, 0.14)"
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
        self._animar_mensaje(label)

    @staticmethod
    def _limpiar_mensaje(label: QLabel) -> None:
        label.clear()
        label.setVisible(False)
        label.setStyleSheet("")
        label.setMaximumHeight(0)
        label.setGraphicsEffect(None)

    def _emitir_login(self) -> None:
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

        def _restaurar_sombra() -> None:
            tarjeta.setGraphicsEffect(self._crear_sombra_tarjeta())
            if grupo in self._animaciones_activas:
                self._animaciones_activas.remove(grupo)

        grupo.finished.connect(_restaurar_sombra)
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
                border-radius: 28px;
            }}
            QFrame#panelInstitucionalLogin {{
                background: qlineargradient(
                    x1: 0, y1: 0,
                    x2: 1, y2: 1,
                    stop: 0 {COLOR_GRADIENTE_INICIAL},
                    stop: 0.58 #0A4174,
                    stop: 1 {COLOR_GRADIENTE_FINAL}
                );
                border-top-left-radius: 28px;
                border-bottom-left-radius: 28px;
            }}
            QFrame#panelFormularioLogin {{
                background: #F8FCFF;
                border: 1px solid rgba(10, 65, 116, 0.14);
                border-top-right-radius: 28px;
                border-bottom-right-radius: 28px;
            }}
            QWidget#bloqueMarcaLogin {{
                background: transparent;
            }}
            QLabel#logoMarcaLogin {{
                margin-bottom: 0;
            }}
            QLabel#logoMarcaLoginInstitucional {{
                margin-bottom: 2px;
            }}
            QLabel#lemaMarcaLogin {{
                color: #47697F;
                font-size: 11px;
                font-weight: 700;
                padding: 0 6px 0 6px;
            }}
            QLabel#nombreSistemaLogin {{
                color: #FFFFFF;
                font-size: 34px;
                font-weight: 900;
                letter-spacing: 2.2px;
            }}
            QLabel#subtituloSistemaLogin {{
                color: rgba(238, 248, 255, 0.92);
                font-size: 14px;
                font-weight: 800;
                line-height: 1.25;
            }}
            QLabel#textoPrincipalLogin {{
                color: rgba(239, 249, 255, 0.84);
                font-size: 13px;
                font-weight: 600;
                line-height: 1.28;
            }}
            QLabel#chipLogin {{
                color: #EAF8FF;
                background-color: rgba(255, 255, 255, 0.14);
                border: 1px solid rgba(255, 255, 255, 0.24);
                border-radius: 12px;
                font-size: 11px;
                font-weight: 800;
                padding: 5px 10px;
            }}
            QLabel#microcopyLogin {{
                color: rgba(245, 252, 255, 0.78);
                font-size: 11px;
                font-weight: 700;
                line-height: 1.2;
            }}
            QLabel#decoracionLoginSuperior,
            QLabel#decoracionLoginInferior {{
                background: rgba(255, 255, 255, 0.10);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 58px;
            }}
            QLabel#badgeContexto {{
                color: #0A4174;
                background-color: rgba(10, 111, 143, 0.10);
                border: 1px solid rgba(10, 111, 143, 0.18);
                border-radius: 11px;
                font-size: 10px;
                font-weight: 800;
                letter-spacing: 1.4px;
                padding: 5px 10px;
                margin: 0 0 4px 0;
            }}
            QLabel#emblemaPagina {{
                color: {COLOR_ICONO_SECUNDARIO};
                margin-bottom: 0;
            }}
            QLabel#tituloPagina {{
                color: #123044;
                font-size: 22px;
                font-weight: 900;
                letter-spacing: 0.1px;
            }}
            QLabel#subtituloPagina,
            QLabel#textoExplicativo {{
                color: #5D788B;
                font-size: 12px;
                line-height: 1.25;
            }}
            QLabel#pieLogin {{
                color: #6A8798;
                font-size: 11px;
                font-weight: 700;
                padding-top: 0;
            }}
            QLabel#etiquetaCampo {{
                color: #264A60;
                font-size: 12px;
                font-weight: 800;
                letter-spacing: 0.1px;
            }}
            QLineEdit,
            QPushButton#botonPrimario,
            QPushButton#botonSecundario {{
                outline: none;
            }}
            """
        )
