"""Vista PySide6 del modulo de usuarios."""

from __future__ import annotations

from typing import Callable, Iterable

from PySide6.QtCore import QElapsedTimer, QEvent, QSize, Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QButtonGroup,
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from comun.ui import (
    BotonAccionContextual,
    DialogoBaseSicap,
    DialogoConfirmacionSicap,
    aplicar_estilo_boton_operativo,
    configurar_tabla_operativa,
    crear_boton_operativo,
    crear_item_tabla,
    obtener_icono_tabler_coloreado,
)
from comun.ui.temas import (
    TEMA_SICAP_PREDETERMINADO,
    obtener_fondo_header_destacado,
    obtener_paleta_tema,
)
from modulos.usuarios.entidades import (
    FormularioRol,
    FormularioUsuario,
    PermisoSistema,
    ResumenUsuarios,
    RolSistema,
    UsuarioSistema,
)
from modulos.usuarios.servicio import (
    FILTRO_USUARIOS_ACTIVOS,
    FILTRO_USUARIOS_ADMINISTRADORES,
    FILTRO_USUARIOS_INACTIVOS,
    FILTRO_USUARIOS_TODOS,
)


class TarjetaResumenUsuario(QFrame):
    """Tarjeta resumen del modulo."""

    def __init__(self, icono: str, color_icono: str) -> None:
        super().__init__()
        self.setObjectName("tarjetaResumenUsuarios")
        self.setMinimumHeight(108)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        self._icono = QLabel("")
        self._icono.setObjectName("iconoTarjetaResumenUsuario")
        self._icono.setFixedSize(40, 40)
        self._icono.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icono.setPixmap(
            obtener_icono_tabler_coloreado(icono, color_icono, tamano=18).pixmap(18, 18)
        )

        bloque = QVBoxLayout()
        bloque.setContentsMargins(0, 0, 0, 0)
        bloque.setSpacing(3)
        self._titulo = QLabel("")
        self._titulo.setObjectName("tituloTarjetaResumenUsuario")
        self._valor = QLabel("")
        self._valor.setObjectName("valorTarjetaResumenUsuario")
        self._detalle = QLabel("")
        self._detalle.setObjectName("detalleTarjetaResumenUsuario")
        self._detalle.setWordWrap(True)
        bloque.addWidget(self._titulo)
        bloque.addWidget(self._valor)
        bloque.addWidget(self._detalle)
        bloque.addStretch(1)

        layout.addWidget(self._icono, alignment=Qt.AlignmentFlag.AlignTop)
        layout.addLayout(bloque, 1)

    def actualizar(self, titulo: str, valor: str, detalle: str) -> None:
        self._titulo.setText(titulo)
        self._valor.setText(valor)
        self._detalle.setText(detalle)


class BotonIconoFilaUsuario(QToolButton):
    """Boton de accion compacto para filas de usuarios."""

    COLOR_BASE = "#c8d6f1"
    INTERVALO_TOOLTIP_MS = 1600

    def __init__(self, icono: str, color_hover: str, tooltip: str) -> None:
        super().__init__()
        self._icono = icono
        self._color_hover = color_hover
        self._color_base = self.COLOR_BASE
        self._temporizador_tooltip = QElapsedTimer()
        self.setObjectName("botonIconoFilaUsuario")
        self.setToolTip(tooltip)
        self.setToolTipDuration(1400)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setAutoRaise(True)
        self.setFixedSize(32, 32)
        self.setIconSize(QSize(18, 18))
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self._actualizar_icono(self.COLOR_BASE)

    def event(self, evento: QEvent) -> bool:
        if evento.type() == QEvent.Type.ToolTip:
            if (
                self._temporizador_tooltip.isValid()
                and self._temporizador_tooltip.elapsed() < self.INTERVALO_TOOLTIP_MS
            ):
                return True
            self._temporizador_tooltip.restart()
        return super().event(evento)

    def enterEvent(self, evento: object) -> None:
        self._actualizar_icono(self._color_hover)
        super().enterEvent(evento)

    def leaveEvent(self, evento: object) -> None:
        self._actualizar_icono(self._color_base)
        super().leaveEvent(evento)

    def aplicar_tema(self, nombre_tema: str) -> None:
        paleta = obtener_paleta_tema(nombre_tema)
        self._color_base = str(paleta["icono_fila_base"])
        self._actualizar_icono(self._color_base)

    def _actualizar_icono(self, color_icono: str) -> None:
        self.setIcon(obtener_icono_tabler_coloreado(self._icono, color_icono, tamano=18))


class DialogoFormularioUsuario(DialogoBaseSicap):
    """Formulario modal para crear o editar usuarios."""

    def __init__(
        self,
        roles: Iterable[RolSistema],
        usuario: UsuarioSistema | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._roles = list(roles)
        self._usuario = usuario
        self.setMinimumWidth(660)
        self.setMinimumHeight(600)
        self._construir_ui()

    def obtener_formulario(self) -> FormularioUsuario:
        return FormularioUsuario(
            identificador=None if self._usuario is None else self._usuario.identificador,
            nombre_usuario=self._campo_usuario.text().strip(),
            nombre_completo=self._campo_nombre.text().strip(),
            correo=self._campo_correo.text().strip(),
            estado=self._combo_estado.currentData() or self._combo_estado.currentText(),
            rol_id=int(self._combo_rol.currentData() or 0),
            observaciones=self._campo_observaciones.toPlainText().strip(),
            contrasena_temporal=self._campo_contrasena.text(),
            confirmacion_contrasena=self._campo_confirmacion.text(),
        )

    def accept(self) -> None:
        formulario = self.obtener_formulario()
        if not formulario.nombre_completo:
            self._mostrar_error("Indica el nombre completo del usuario.")
            return
        if not formulario.nombre_usuario:
            self._mostrar_error("Indica el nombre de usuario.")
            return
        if not formulario.correo:
            self._mostrar_error("Indica el correo del usuario.")
            return
        if formulario.rol_id <= 0:
            self._mostrar_error("Selecciona un rol visible para continuar.")
            return
        if self._usuario is None:
            if not formulario.contrasena_temporal or not formulario.confirmacion_contrasena:
                self._mostrar_error("Completa la contrasena temporal y su confirmacion.")
                return
            if formulario.contrasena_temporal != formulario.confirmacion_contrasena:
                self._mostrar_error("Las contrasenas no coinciden.")
                return
        self._mensaje.setVisible(False)
        super().accept()

    def _construir_ui(self) -> None:
        titulo = QLabel("Editar usuario" if self._usuario else "Nuevo usuario")
        titulo.setObjectName("tituloDialogoSicap")
        descripcion = QLabel(
            "Configura la identidad del usuario, su rol visible y el estado operativo."
        )
        descripcion.setObjectName("descripcionDialogoSicap")
        descripcion.setWordWrap(True)

        panel_datos = self._crear_panel("Datos principales", "Informacion base de la cuenta operativa.")
        grid_datos = QGridLayout()
        grid_datos.setHorizontalSpacing(12)
        grid_datos.setVerticalSpacing(12)

        self._campo_nombre = QLineEdit()
        self._campo_nombre.setPlaceholderText("Nombre completo")
        self._campo_usuario = QLineEdit()
        self._campo_usuario.setPlaceholderText("Nombre de usuario")
        self._campo_correo = QLineEdit()
        self._campo_correo.setPlaceholderText("usuario@sicap.hn")
        self._combo_estado = QComboBox()
        self._combo_estado.addItem("Activo", "ACTIVO")
        self._combo_estado.addItem("Inactivo", "INACTIVO")

        grid_datos.addWidget(self._crear_bloque("Nombre completo", self._campo_nombre), 0, 0, 1, 2)
        grid_datos.addWidget(self._crear_bloque("Usuario", self._campo_usuario), 1, 0)
        grid_datos.addWidget(self._crear_bloque("Correo", self._campo_correo), 1, 1)
        grid_datos.addWidget(self._crear_bloque("Estado", self._combo_estado), 2, 0)
        panel_datos.layout().addLayout(grid_datos)

        panel_seguridad = self._crear_panel(
            "Rol y seguridad",
            "Asigna un unico rol visible. Los permisos reales se heredan desde ese rol.",
        )
        grid_seguridad = QGridLayout()
        grid_seguridad.setHorizontalSpacing(12)
        grid_seguridad.setVerticalSpacing(12)

        self._combo_rol = QComboBox()
        self._combo_rol.blockSignals(True)
        self._combo_rol.addItem("Selecciona un rol", 0)
        for rol in self._roles:
            self._combo_rol.addItem(rol.nombre, rol.identificador)
        self._combo_rol.blockSignals(False)

        self._campo_contrasena = QLineEdit()
        self._campo_contrasena.setEchoMode(QLineEdit.EchoMode.Password)
        self._campo_contrasena.setPlaceholderText("Contrasena temporal")
        self._campo_confirmacion = QLineEdit()
        self._campo_confirmacion.setEchoMode(QLineEdit.EchoMode.Password)
        self._campo_confirmacion.setPlaceholderText("Confirmar contrasena")

        grid_seguridad.addWidget(self._crear_bloque("Rol", self._combo_rol), 0, 0, 1, 2)
        grid_seguridad.addWidget(
            self._crear_bloque("Contrasena temporal", self._campo_contrasena),
            1,
            0,
        )
        grid_seguridad.addWidget(
            self._crear_bloque("Confirmar contrasena", self._campo_confirmacion),
            1,
            1,
        )
        panel_seguridad.layout().addLayout(grid_seguridad)

        if self._usuario is not None:
            self._campo_contrasena.setDisabled(True)
            self._campo_confirmacion.setDisabled(True)
            ayuda = QLabel(
                "Para cambiar la contrasena usa la accion de restablecimiento desde la tabla del modulo."
            )
            ayuda.setObjectName("descripcionDialogoSicap")
            ayuda.setWordWrap(True)
            panel_seguridad.layout().addWidget(ayuda)

        self._resumen_rol = QLabel("")
        self._resumen_rol.setObjectName("bloqueInfoRolUsuario")
        self._resumen_rol.setWordWrap(True)
        panel_seguridad.layout().addWidget(self._resumen_rol)
        self._combo_rol.currentIndexChanged.connect(self._actualizar_resumen_rol)

        panel_observaciones = self._crear_panel(
            "Observaciones",
            "Notas administrativas internas sobre esta cuenta.",
        )
        self._campo_observaciones = QPlainTextEdit()
        self._campo_observaciones.setPlaceholderText("Observaciones")
        self._campo_observaciones.setFixedHeight(86)
        panel_observaciones.layout().addWidget(self._campo_observaciones)

        self._mensaje = QLabel("")
        self._mensaje.setObjectName("mensajeErrorDialogoSicap")
        self._mensaje.setVisible(False)

        fila_acciones = QHBoxLayout()
        fila_acciones.setSpacing(10)
        boton_cancelar = BotonAccionContextual(
            "Cancelar",
            variante="neutro",
            centrado=True,
            mostrar_icono=False,
        )
        boton_guardar = BotonAccionContextual(
            "Actualizar usuario" if self._usuario else "Crear usuario",
            variante="primario",
            centrado=True,
            mostrar_icono=False,
        )
        boton_cancelar.setMinimumWidth(132)
        boton_guardar.setMinimumWidth(168)
        boton_cancelar.clicked.connect(self.reject)
        boton_guardar.clicked.connect(self.accept)
        fila_acciones.addWidget(boton_cancelar)
        fila_acciones.addStretch(1)
        fila_acciones.addWidget(boton_guardar)

        if self._usuario is not None:
            self._campo_nombre.setText(self._usuario.nombre_completo)
            self._campo_usuario.setText(self._usuario.nombre_usuario)
            self._campo_correo.setText(self._usuario.correo)
            self._combo_estado.setCurrentIndex(0 if self._usuario.estado == "ACTIVO" else 1)
            self._campo_observaciones.setPlainText(self._usuario.observaciones)
            indice = self._combo_rol.findText(self._usuario.rol_principal, Qt.MatchFlag.MatchExactly)
            if indice >= 0:
                self._combo_rol.setCurrentIndex(indice)

        self.layout_cabecera.addWidget(titulo)
        self.layout_cabecera.addWidget(descripcion)
        self.layout_cuerpo.addWidget(panel_datos)
        self.layout_cuerpo.addWidget(panel_seguridad)
        self.layout_cuerpo.addWidget(panel_observaciones)
        self.layout_cuerpo.addWidget(self._mensaje)
        self.layout_pie.addLayout(fila_acciones)
        self._actualizar_resumen_rol()

    def _crear_panel(self, titulo: str, descripcion: str) -> QFrame:
        panel = QFrame()
        panel.setObjectName("bloqueDialogoSicap")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        label_titulo = QLabel(titulo)
        label_titulo.setObjectName("etiquetaDatoDialogoSicap")
        label_descripcion = QLabel(descripcion)
        label_descripcion.setObjectName("descripcionDialogoSicap")
        label_descripcion.setWordWrap(True)
        layout.addWidget(label_titulo)
        layout.addWidget(label_descripcion)
        return panel

    def _crear_bloque(self, etiqueta: str, widget: QWidget) -> QWidget:
        bloque = QWidget()
        layout = QVBoxLayout(bloque)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        label = QLabel(etiqueta)
        label.setObjectName("etiquetaDatoDialogoSicap")
        layout.addWidget(label)
        layout.addWidget(widget)
        return bloque

    def _mostrar_error(self, mensaje: str) -> None:
        self._mensaje.setText(mensaje)
        self._mensaje.setVisible(True)

    def _actualizar_resumen_rol(self) -> None:
        rol_id = int(self._combo_rol.currentData() or 0)
        rol = next((item for item in self._roles if item.identificador == rol_id), None)
        if rol is None:
            self._resumen_rol.setText("Selecciona un rol para ver sus permisos visibles.")
            return
        modulos = self._modulos_resumidos(rol.permisos)
        detalle = ", ".join(modulos[:6]) if modulos else "Sin permisos visibles"
        if len(modulos) > 6:
            detalle += f" y {len(modulos) - 6} mas"
        self._resumen_rol.setText(
            f"<b>{rol.nombre}</b><br>{rol.descripcion or 'Rol sin descripcion.'}"
            f"<br><br><b>Modulos accesibles:</b> {detalle}"
        )

    @staticmethod
    def _modulos_resumidos(permisos: tuple[PermisoSistema, ...]) -> list[str]:
        modulos: list[str] = []
        vistos: set[str] = set()
        for permiso in permisos:
            nombre_modulo = permiso.modulo.strip()
            if not nombre_modulo or nombre_modulo in vistos:
                continue
            vistos.add(nombre_modulo)
            modulos.append(nombre_modulo)
        return modulos


class DialogoDetalleUsuario(DialogoBaseSicap):
    """Detalle operativo del usuario."""

    def __init__(
        self,
        usuario: UsuarioSistema,
        formateador_fecha: Callable[[str | None], str],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._usuario = usuario
        self._formateador_fecha = formateador_fecha
        self._accion_resultado = "cerrar"
        self.setMinimumWidth(700)
        self.setMinimumHeight(540)
        self._construir_ui()

    @property
    def accion_resultado(self) -> str:
        return self._accion_resultado

    def _construir_ui(self) -> None:
        titulo = QLabel("Detalle de usuario")
        titulo.setObjectName("tituloDialogoSicap")
        descripcion = QLabel(
            "Consulta identidad, rol operativo, actividad reciente y estado de seguridad."
        )
        descripcion.setObjectName("descripcionDialogoSicap")
        descripcion.setWordWrap(True)

        scroll = QScrollArea()
        scroll.setObjectName("scrollDetalleUsuario")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        contenedor = QWidget()
        layout_scroll = QVBoxLayout(contenedor)
        layout_scroll.setContentsMargins(0, 0, 0, 0)
        layout_scroll.setSpacing(12)

        panel = QFrame()
        panel.setObjectName("panelDetalleUsuario")
        layout_panel = QVBoxLayout(panel)
        layout_panel.setContentsMargins(16, 16, 16, 16)
        layout_panel.setSpacing(12)

        fila_superior = QHBoxLayout()
        fila_superior.setSpacing(12)
        bloque_titulo = QVBoxLayout()
        etiqueta_usuario = QLabel(self._usuario.nombre_usuario)
        etiqueta_usuario.setObjectName("codigoDetalleUsuario")
        nombre = QLabel(self._usuario.nombre_completo)
        nombre.setObjectName("nombreDetalleUsuario")
        bloque_titulo.addWidget(etiqueta_usuario)
        bloque_titulo.addWidget(nombre)

        estado = QLabel(self._usuario.estado.title())
        estado.setObjectName("badgeEstadoUsuarioDetalle")
        estado.setProperty("activo", self._usuario.estado == "ACTIVO")
        estado.style().unpolish(estado)
        estado.style().polish(estado)
        fila_superior.addLayout(bloque_titulo, 1)
        fila_superior.addWidget(estado, alignment=Qt.AlignmentFlag.AlignTop)

        grid_identidad = QGridLayout()
        grid_identidad.setHorizontalSpacing(14)
        grid_identidad.setVerticalSpacing(14)
        grid_identidad.addWidget(self._crear_campo("Correo", self._usuario.correo), 0, 0)
        grid_identidad.addWidget(self._crear_campo("Rol visible", self._usuario.rol_principal), 0, 1)
        grid_identidad.addWidget(self._crear_campo("Estado", self._usuario.estado.title()), 1, 0)
        grid_identidad.addWidget(
            self._crear_campo(
                "Cambio obligatorio",
                "Pendiente" if self._usuario.requiere_cambio_contrasena else "No",
            ),
            1,
            1,
        )

        grid_actividad = QGridLayout()
        grid_actividad.setHorizontalSpacing(14)
        grid_actividad.setVerticalSpacing(14)
        grid_actividad.addWidget(
            self._crear_campo("Ultimo acceso", self._formateador_fecha(self._usuario.ultimo_acceso_en)),
            0,
            0,
        )
        grid_actividad.addWidget(
            self._crear_campo("Creado", self._formateador_fecha(self._usuario.creado_en)),
            0,
            1,
        )
        grid_actividad.addWidget(
            self._crear_campo("Creado por", self._usuario.creado_por_nombre or "Sin registro"),
            1,
            0,
        )
        grid_actividad.addWidget(
            self._crear_campo(
                "Ultima actualizacion",
                self._formateador_fecha(self._usuario.actualizado_en),
            ),
            1,
            1,
        )
        grid_actividad.addWidget(
            self._crear_campo(
                "Actualizado por",
                self._usuario.actualizado_por_nombre or "Sin registro",
            ),
            2,
            0,
        )
        grid_actividad.addWidget(
            self._crear_campo("Sesiones registradas", str(self._usuario.total_sesiones)),
            2,
            1,
        )
        grid_actividad.addWidget(
            self._crear_campo("Intentos fallidos", str(self._usuario.intentos_fallidos)),
            3,
            0,
            1,
            2,
        )

        observaciones = self._crear_campo(
            "Observaciones",
            self._usuario.observaciones or "Sin observaciones registradas.",
        )

        fila_acciones = QHBoxLayout()
        fila_acciones.setSpacing(10)
        boton_cerrar = BotonAccionContextual(
            "Cerrar",
            variante="neutro",
            centrado=True,
            mostrar_icono=False,
        )
        boton_editar = BotonAccionContextual(
            "Editar",
            variante="edicion",
            centrado=True,
            mostrar_icono=False,
        )
        boton_cerrar.setMinimumWidth(124)
        boton_editar.setMinimumWidth(124)
        boton_cerrar.clicked.connect(self.reject)
        boton_editar.clicked.connect(self._solicitar_edicion)
        fila_acciones.addWidget(boton_cerrar)
        fila_acciones.addStretch(1)
        fila_acciones.addWidget(boton_editar)

        layout_panel.addLayout(fila_superior)
        layout_panel.addWidget(
            self._crear_seccion(
                "Identidad y acceso",
                "Datos visibles del usuario y rol asignado.",
                grid_identidad,
            )
        )
        layout_panel.addWidget(
            self._crear_seccion(
                "Actividad reciente",
                "Indicadores operativos de acceso y seguridad.",
                grid_actividad,
            )
        )
        layout_panel.addWidget(
            self._crear_seccion(
                "Observaciones",
                "Notas administrativas internas de la cuenta.",
                [observaciones],
            )
        )
        layout_panel.addLayout(fila_acciones)
        layout_scroll.addWidget(panel)
        scroll.setWidget(contenedor)

        self.layout_cabecera.addWidget(titulo)
        self.layout_cabecera.addWidget(descripcion)
        self.layout_cuerpo.addWidget(scroll)
        self._pie.setVisible(False)
        self._aplicar_estilos()

    def _crear_seccion(
        self,
        titulo: str,
        descripcion: str,
        contenido: QGridLayout | list[QWidget],
    ) -> QFrame:
        bloque = QFrame()
        bloque.setObjectName("seccionDetalleUsuario")
        layout = QVBoxLayout(bloque)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        label_titulo = QLabel(titulo)
        label_titulo.setObjectName("tituloSeccionDetalleUsuario")
        label_descripcion = QLabel(descripcion)
        label_descripcion.setObjectName("descripcionSeccionDetalleUsuario")
        label_descripcion.setWordWrap(True)
        layout.addWidget(label_titulo)
        layout.addWidget(label_descripcion)
        if isinstance(contenido, list):
            for widget in contenido:
                layout.addWidget(widget)
        else:
            layout.addLayout(contenido)
        return bloque

    def _crear_campo(self, etiqueta: str, valor: str) -> QFrame:
        bloque = QFrame()
        bloque.setObjectName("campoDetalleUsuario")
        layout = QVBoxLayout(bloque)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(5)
        label_etiqueta = QLabel(etiqueta)
        label_etiqueta.setObjectName("etiquetaDetalleUsuario")
        label_valor = QLabel(valor)
        label_valor.setObjectName("valorDetalleUsuario")
        label_valor.setWordWrap(True)
        layout.addWidget(label_etiqueta)
        layout.addWidget(label_valor)
        return bloque

    def _solicitar_edicion(self) -> None:
        self._accion_resultado = "editar"
        self.accept()

    def _aplicar_estilos(self) -> None:
        self.setStyleSheet(
            self.styleSheet()
            + """
            QScrollArea#scrollDetalleUsuario {
                background: transparent;
                border: none;
            }
            QFrame#panelDetalleUsuario,
            QFrame#seccionDetalleUsuario,
            QFrame#campoDetalleUsuario {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 16px;
            }
            QLabel#codigoDetalleUsuario,
            QLabel#etiquetaDetalleUsuario,
            QLabel#descripcionSeccionDetalleUsuario {
                color: rgba(235, 242, 248, 0.72);
            }
            QLabel#nombreDetalleUsuario,
            QLabel#tituloSeccionDetalleUsuario,
            QLabel#valorDetalleUsuario {
                color: #f7fbff;
            }
            QLabel#codigoDetalleUsuario {
                font-size: 12px;
                font-weight: 800;
            }
            QLabel#nombreDetalleUsuario {
                font-size: 18px;
                font-weight: 900;
            }
            QLabel#tituloSeccionDetalleUsuario {
                font-size: 14px;
                font-weight: 800;
            }
            QLabel#valorDetalleUsuario {
                font-size: 13px;
                font-weight: 700;
            }
            QLabel#badgeEstadoUsuarioDetalle {
                border-radius: 11px;
                padding: 6px 10px;
                font-size: 11px;
                font-weight: 800;
                color: #f4f8fb;
                background: rgba(132, 146, 166, 0.22);
                border: 1px solid rgba(255, 255, 255, 0.12);
            }
            QLabel#badgeEstadoUsuarioDetalle[activo="true"] {
                color: #d9fff5;
                background: rgba(16, 120, 98, 0.22);
                border-color: rgba(158, 231, 214, 0.26);
            }
            """
        )


class DialogoGestionAccesoUsuario(DialogoBaseSicap):
    """Modal para restablecer contrasena o desbloquear una cuenta."""

    def __init__(self, usuario: UsuarioSistema, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._usuario = usuario
        self._resultado: tuple[str, str, str] | None = None
        self.setMinimumWidth(520)
        self.setMinimumHeight(390)
        self._construir_ui()

    def obtener_resultado(self) -> tuple[str, str, str] | None:
        return self._resultado

    def _construir_ui(self) -> None:
        titulo = QLabel("Gestion de acceso")
        titulo.setObjectName("tituloDialogoSicap")
        descripcion = QLabel(
            "Aplica un restablecimiento administrativo o desbloquea la cuenta si quedo bloqueada."
        )
        descripcion.setObjectName("descripcionDialogoSicap")
        descripcion.setWordWrap(True)

        panel = QFrame()
        panel.setObjectName("bloqueDialogoSicap")
        layout_panel = QVBoxLayout(panel)
        layout_panel.setContentsMargins(14, 14, 14, 14)
        layout_panel.setSpacing(10)

        etiqueta_usuario = QLabel(
            f"<b>{self._usuario.nombre_usuario}</b><br>{self._usuario.nombre_completo}<br>{self._usuario.rol_principal}"
        )
        etiqueta_usuario.setObjectName("descripcionDialogoSicap")
        etiqueta_usuario.setWordWrap(True)
        layout_panel.addWidget(etiqueta_usuario)

        self._campo_contrasena = QLineEdit()
        self._campo_contrasena.setEchoMode(QLineEdit.EchoMode.Password)
        self._campo_contrasena.setPlaceholderText("Contrasena temporal")
        self._campo_confirmacion = QLineEdit()
        self._campo_confirmacion.setEchoMode(QLineEdit.EchoMode.Password)
        self._campo_confirmacion.setPlaceholderText("Confirmar contrasena")

        layout_panel.addWidget(self._crear_bloque("Nueva contrasena temporal", self._campo_contrasena))
        layout_panel.addWidget(self._crear_bloque("Confirmacion", self._campo_confirmacion))

        contexto = []
        if self._usuario.requiere_cambio_contrasena:
            contexto.append("La cuenta ya tiene cambio obligatorio de contrasena pendiente.")
        if self._usuario.intentos_fallidos > 0 or self._usuario.estado == "BLOQUEADO":
            contexto.append(
                f"Intentos fallidos actuales: {self._usuario.intentos_fallidos}. Puedes desbloquear la cuenta."
            )
        else:
            contexto.append("La cuenta no esta bloqueada, pero puedes aplicar un nuevo acceso temporal.")

        nota = QLabel(" ".join(contexto))
        nota.setObjectName("descripcionDialogoSicap")
        nota.setWordWrap(True)
        layout_panel.addWidget(nota)

        self._mensaje = QLabel("")
        self._mensaje.setObjectName("mensajeErrorDialogoSicap")
        self._mensaje.setVisible(False)

        fila_acciones = QHBoxLayout()
        fila_acciones.setSpacing(10)
        boton_cancelar = BotonAccionContextual(
            "Cancelar",
            variante="neutro",
            centrado=True,
            mostrar_icono=False,
        )
        boton_restablecer = BotonAccionContextual(
            "Restablecer contrasena",
            variante="primario",
            centrado=True,
            mostrar_icono=False,
        )
        boton_cancelar.setMinimumWidth(132)
        boton_restablecer.setMinimumWidth(190)
        boton_cancelar.clicked.connect(self.reject)
        boton_restablecer.clicked.connect(self._confirmar_restablecimiento)
        fila_acciones.addWidget(boton_cancelar)
        fila_acciones.addStretch(1)
        if self._usuario.intentos_fallidos > 0 or self._usuario.estado == "BLOQUEADO":
            boton_desbloquear = BotonAccionContextual(
                "Desbloquear",
                variante="edicion",
                centrado=True,
                mostrar_icono=False,
            )
            boton_desbloquear.setMinimumWidth(148)
            boton_desbloquear.clicked.connect(self._confirmar_desbloqueo)
            fila_acciones.addWidget(boton_desbloquear)
        fila_acciones.addWidget(boton_restablecer)

        self.layout_cabecera.addWidget(titulo)
        self.layout_cabecera.addWidget(descripcion)
        self.layout_cuerpo.addWidget(panel)
        self.layout_cuerpo.addWidget(self._mensaje)
        self.layout_pie.addLayout(fila_acciones)

    def _crear_bloque(self, etiqueta: str, widget: QWidget) -> QWidget:
        bloque = QWidget()
        layout = QVBoxLayout(bloque)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        label = QLabel(etiqueta)
        label.setObjectName("etiquetaDatoDialogoSicap")
        layout.addWidget(label)
        layout.addWidget(widget)
        return bloque

    def _confirmar_restablecimiento(self) -> None:
        contrasena = self._campo_contrasena.text()
        confirmacion = self._campo_confirmacion.text()
        if not contrasena or not confirmacion:
            self._mostrar_error("Completa ambos campos para restablecer la contrasena.")
            return
        self._resultado = ("restablecer", contrasena, confirmacion)
        self.accept()

    def _confirmar_desbloqueo(self) -> None:
        self._resultado = ("desbloquear", "", "")
        self.accept()

    def _mostrar_error(self, mensaje: str) -> None:
        self._mensaje.setText(mensaje)
        self._mensaje.setVisible(True)


class DialogoFormularioRol(DialogoBaseSicap):
    """Modal para crear o editar roles visibles."""

    ORDEN_ACCIONES = ("VER", "GESTIONAR", "REGISTRAR", "GENERAR", "ANULAR")

    def __init__(
        self,
        permisos_disponibles: Iterable[PermisoSistema],
        rol: RolSistema | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._rol = rol
        self._permisos_disponibles = list(permisos_disponibles)
        self._permisos_seleccionados = {permiso.codigo for permiso in rol.permisos} if rol else set()
        self._botones_permisos: dict[str, QPushButton] = {}
        self._botones_modulo: dict[str, QPushButton] = {}
        self.setMinimumWidth(760)
        self.setMinimumHeight(620)
        self._construir_ui()

    def obtener_formulario(self) -> FormularioRol:
        return FormularioRol(
            identificador=None if self._rol is None else self._rol.identificador,
            nombre=self._campo_nombre.text().strip(),
            descripcion=self._campo_descripcion.toPlainText().strip(),
            permisos_codigos=tuple(sorted(self._permisos_seleccionados)),
        )

    def accept(self) -> None:
        formulario = self.obtener_formulario()
        if not formulario.nombre:
            self._mostrar_error("Indica el nombre del rol.")
            return
        if not formulario.descripcion:
            self._mostrar_error("Indica la descripcion del rol.")
            return
        if not formulario.permisos_codigos:
            self._mostrar_error("Selecciona al menos un permiso para el rol.")
            return
        self._mensaje.setVisible(False)
        super().accept()

    def _construir_ui(self) -> None:
        titulo = QLabel("Editar rol" if self._rol else "Crear nuevo rol")
        titulo.setObjectName("tituloDialogoSicap")
        descripcion = QLabel(
            "Define el nombre, la descripcion y los permisos operativos visibles del rol."
        )
        descripcion.setObjectName("descripcionDialogoSicap")
        descripcion.setWordWrap(True)

        panel_datos = self._crear_panel(
            "Datos del rol",
            "Configura el nombre visible y una descripcion corta del alcance operativo.",
        )
        self._campo_nombre = QLineEdit()
        self._campo_nombre.setPlaceholderText("Ej: Supervisor, Recepcion, Auditor")
        self._campo_descripcion = QPlainTextEdit()
        self._campo_descripcion.setPlaceholderText("Describe el alcance de este rol")
        self._campo_descripcion.setFixedHeight(72)
        panel_datos.layout().addWidget(self._crear_bloque("Nombre del rol", self._campo_nombre))
        panel_datos.layout().addWidget(self._crear_bloque("Descripcion", self._campo_descripcion))

        panel_permisos = self._crear_panel(
            "Permisos por modulo",
            "La matriz se adapta a los permisos reales del sistema. Usa \"Todos\" para marcar o quitar los de un modulo.",
        )
        self._tabla_permisos = QTableWidget()
        self._tabla_permisos.setObjectName("tablaFormularioRolUsuarios")
        self._tabla_permisos.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._tabla_permisos.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self._tabla_permisos.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._tabla_permisos.setFrameShape(QFrame.Shape.NoFrame)
        self._tabla_permisos.viewport().setObjectName("viewportTablaFormularioRolUsuarios")
        self._construir_tabla_permisos()
        panel_permisos.layout().addWidget(self._tabla_permisos)

        ayuda = QLabel(
            "Los usuarios vinculados a este rol heredaran automaticamente los permisos seleccionados."
        )
        ayuda.setObjectName("descripcionDialogoSicap")
        ayuda.setWordWrap(True)
        panel_permisos.layout().addWidget(ayuda)

        if self._rol is not None and self._rol.es_sistema:
            nota_sistema = QLabel(
                "Rol de sistema: evita quitar permisos que dejen sin flujo operativo a usuarios ya asignados."
            )
            nota_sistema.setObjectName("notaRolSistemaModal")
            nota_sistema.setWordWrap(True)
            panel_permisos.layout().addWidget(nota_sistema)

        self._mensaje = QLabel("")
        self._mensaje.setObjectName("mensajeErrorDialogoSicap")
        self._mensaje.setVisible(False)

        fila_acciones = QHBoxLayout()
        fila_acciones.setSpacing(10)
        boton_cancelar = BotonAccionContextual(
            "Cancelar",
            variante="neutro",
            centrado=True,
            mostrar_icono=False,
        )
        boton_guardar = BotonAccionContextual(
            "Guardar cambios" if self._rol else "Crear rol",
            variante="primario",
            centrado=True,
            mostrar_icono=False,
        )
        boton_cancelar.setMinimumWidth(126)
        boton_guardar.setMinimumWidth(152)
        boton_cancelar.clicked.connect(self.reject)
        boton_guardar.clicked.connect(self.accept)
        fila_acciones.addWidget(boton_cancelar)
        fila_acciones.addStretch(1)
        fila_acciones.addWidget(boton_guardar)

        if self._rol is not None:
            self._campo_nombre.setText(self._rol.nombre)
            self._campo_descripcion.setPlainText(self._rol.descripcion)

        self.layout_cabecera.addWidget(titulo)
        self.layout_cabecera.addWidget(descripcion)
        self.layout_cuerpo.addWidget(panel_datos)
        self.layout_cuerpo.addWidget(panel_permisos)
        self.layout_cuerpo.addWidget(self._mensaje)
        self.layout_pie.addLayout(fila_acciones)
        self._aplicar_estilos()

    def _construir_tabla_permisos(self) -> None:
        acciones_disponibles = self._acciones_disponibles()
        columnas = ["Modulo"] + [self._texto_accion(accion) for accion in acciones_disponibles] + ["Todos"]
        modulos = self._permisos_por_modulo()
        self._tabla_permisos.setColumnCount(len(columnas))
        self._tabla_permisos.setRowCount(len(modulos))
        configurar_tabla_operativa(self._tabla_permisos, columnas)
        self._tabla_permisos.horizontalHeader().setStretchLastSection(False)
        self._tabla_permisos.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for indice in range(1, len(columnas)):
            self._tabla_permisos.horizontalHeader().setSectionResizeMode(indice, QHeaderView.ResizeMode.ResizeToContents)
        self._tabla_permisos.verticalHeader().setDefaultSectionSize(48)

        for fila, (modulo, permisos) in enumerate(modulos):
            self._tabla_permisos.setItem(fila, 0, crear_item_tabla(modulo))
            for offset, accion in enumerate(acciones_disponibles, start=1):
                permiso = next((item for item in permisos if self._accion_permiso(item) == accion), None)
                if permiso is None:
                    vacio = QLabel("—")
                    vacio.setObjectName("celdaVaciaPermisoRol")
                    vacio.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    self._tabla_permisos.setCellWidget(fila, offset, vacio)
                    continue
                boton = self._crear_boton_permiso(permiso.codigo)
                self._tabla_permisos.setCellWidget(fila, offset, self._centrar_widget(boton))
            boton_todos = QPushButton("Todos")
            boton_todos.setObjectName("botonTodosPermisosRol")
            boton_todos.setCursor(Qt.CursorShape.PointingHandCursor)
            boton_todos.clicked.connect(lambda checked=False, nombre_modulo=modulo: self._alternar_modulo(nombre_modulo))
            self._botones_modulo[modulo] = boton_todos
            self._tabla_permisos.setCellWidget(
                fila,
                len(columnas) - 1,
                self._centrar_widget(boton_todos),
            )
            self._actualizar_boton_modulo(modulo)

    def _crear_panel(self, titulo: str, descripcion: str) -> QFrame:
        panel = QFrame()
        panel.setObjectName("bloqueDialogoSicap")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        label_titulo = QLabel(titulo)
        label_titulo.setObjectName("etiquetaDatoDialogoSicap")
        label_descripcion = QLabel(descripcion)
        label_descripcion.setObjectName("descripcionDialogoSicap")
        label_descripcion.setWordWrap(True)
        layout.addWidget(label_titulo)
        layout.addWidget(label_descripcion)
        return panel

    def _crear_bloque(self, etiqueta: str, widget: QWidget) -> QWidget:
        bloque = QWidget()
        layout = QVBoxLayout(bloque)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        label = QLabel(etiqueta)
        label.setObjectName("etiquetaDatoDialogoSicap")
        layout.addWidget(label)
        layout.addWidget(widget)
        return bloque

    def _crear_boton_permiso(self, codigo_permiso: str) -> QPushButton:
        boton = QPushButton("✓")
        boton.setObjectName("botonPermisoRol")
        boton.setCursor(Qt.CursorShape.PointingHandCursor)
        boton.setCheckable(True)
        boton.setChecked(codigo_permiso in self._permisos_seleccionados)
        boton.clicked.connect(
            lambda checked=False, codigo=codigo_permiso: self._alternar_permiso(codigo)
        )
        self._botones_permisos[codigo_permiso] = boton
        self._actualizar_boton_permiso(codigo_permiso)
        return boton

    @staticmethod
    def _centrar_widget(widget: QWidget) -> QWidget:
        contenedor = QWidget()
        layout = QHBoxLayout(contenedor)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(widget, alignment=Qt.AlignmentFlag.AlignCenter)
        return contenedor

    def _alternar_permiso(self, codigo_permiso: str) -> None:
        if codigo_permiso in self._permisos_seleccionados:
            self._permisos_seleccionados.remove(codigo_permiso)
        else:
            self._permisos_seleccionados.add(codigo_permiso)
        self._actualizar_boton_permiso(codigo_permiso)
        modulo = self._modulo_de_permiso(codigo_permiso)
        if modulo:
            self._actualizar_boton_modulo(modulo)

    def _alternar_modulo(self, modulo: str) -> None:
        permisos_modulo = [permiso.codigo for permiso in self._permisos_disponibles if permiso.modulo == modulo]
        todos_marcados = all(codigo in self._permisos_seleccionados for codigo in permisos_modulo)
        for codigo in permisos_modulo:
            if todos_marcados:
                self._permisos_seleccionados.discard(codigo)
            else:
                self._permisos_seleccionados.add(codigo)
            self._actualizar_boton_permiso(codigo)
        self._actualizar_boton_modulo(modulo)

    def _actualizar_boton_permiso(self, codigo_permiso: str) -> None:
        boton = self._botones_permisos.get(codigo_permiso)
        if boton is None:
            return
        activo = codigo_permiso in self._permisos_seleccionados
        boton.setChecked(activo)
        boton.setProperty("activo", activo)
        boton.style().unpolish(boton)
        boton.style().polish(boton)

    def _actualizar_boton_modulo(self, modulo: str) -> None:
        boton = self._botones_modulo.get(modulo)
        if boton is None:
            return
        permisos_modulo = [permiso.codigo for permiso in self._permisos_disponibles if permiso.modulo == modulo]
        todos_marcados = bool(permisos_modulo) and all(
            codigo in self._permisos_seleccionados for codigo in permisos_modulo
        )
        boton.setText("Quitar" if todos_marcados else "Todos")
        boton.setProperty("activo", todos_marcados)
        boton.style().unpolish(boton)
        boton.style().polish(boton)

    def _permisos_por_modulo(self) -> list[tuple[str, list[PermisoSistema]]]:
        agrupados: dict[str, list[PermisoSistema]] = {}
        for permiso in self._permisos_disponibles:
            agrupados.setdefault(permiso.modulo, []).append(permiso)
        return sorted(agrupados.items(), key=lambda item: item[0].casefold())

    def _acciones_disponibles(self) -> list[str]:
        acciones = {self._accion_permiso(permiso) for permiso in self._permisos_disponibles}
        ordenadas = [accion for accion in self.ORDEN_ACCIONES if accion in acciones]
        restantes = sorted(acciones.difference(self.ORDEN_ACCIONES))
        return ordenadas + restantes

    @staticmethod
    def _accion_permiso(permiso: PermisoSistema) -> str:
        return permiso.codigo.split(".")[-1].replace("_", " ").upper()

    @staticmethod
    def _texto_accion(accion: str) -> str:
        return accion.title()

    def _modulo_de_permiso(self, codigo_permiso: str) -> str:
        for permiso in self._permisos_disponibles:
            if permiso.codigo == codigo_permiso:
                return permiso.modulo
        return ""

    def _mostrar_error(self, mensaje: str) -> None:
        self._mensaje.setText(mensaje)
        self._mensaje.setVisible(True)

    def _aplicar_estilos(self) -> None:
        self.setStyleSheet(
            self.styleSheet()
            + """
            QTableWidget#tablaFormularioRolUsuarios {
                background: rgba(74, 79, 154, 0.88);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 14px;
            }
            QTableWidget#tablaFormularioRolUsuarios QTableCornerButton::section {
                background: rgba(108, 113, 190, 0.92);
                border: none;
            }
            QWidget#viewportTablaFormularioRolUsuarios {
                background: transparent;
                border: none;
            }
            QPushButton#botonPermisoRol {
                min-width: 28px;
                min-height: 28px;
                max-width: 28px;
                max-height: 28px;
                border-radius: 9px;
                border: 1px solid rgba(255, 255, 255, 0.12);
                background: rgba(255, 255, 255, 0.08);
                color: rgba(235, 242, 248, 0.42);
                font-size: 12px;
                font-weight: 900;
            }
            QPushButton#botonPermisoRol[activo="true"] {
                color: #d9fff5;
                background: rgba(16, 120, 98, 0.20);
                border: 1px solid rgba(158, 231, 214, 0.28);
            }
            QPushButton#botonTodosPermisosRol {
                min-height: 28px;
                border-radius: 9px;
                padding: 0 10px;
                border: 1px solid rgba(255, 255, 255, 0.12);
                background: rgba(255, 255, 255, 0.08);
                color: #ebf4ff;
                font-size: 11px;
                font-weight: 800;
            }
            QPushButton#botonTodosPermisosRol[activo="true"] {
                color: #f5e1ff;
                background: rgba(146, 101, 255, 0.16);
                border: 1px solid rgba(207, 181, 255, 0.24);
            }
            QLabel#celdaVaciaPermisoRol {
                color: rgba(235, 242, 248, 0.46);
                font-size: 12px;
                font-weight: 700;
            }
            QLabel#notaRolSistemaModal {
                color: #efe2ff;
                font-size: 11px;
                font-weight: 700;
                padding: 8px 10px;
                border-radius: 10px;
                background: rgba(146, 101, 255, 0.14);
                border: 1px solid rgba(207, 181, 255, 0.22);
            }
            """
        )


class DialogoMatrizPermisosUsuarios(DialogoBaseSicap):
    """Matriz visual de permisos reales por rol."""

    def __init__(self, roles: Iterable[RolSistema], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._roles = [rol for rol in roles if rol.estado == "ACTIVO"]
        self.setMinimumWidth(980)
        self.setMinimumHeight(720)
        self._construir_ui()

    def _construir_ui(self) -> None:
        titulo = QLabel("Matriz de permisos por rol")
        titulo.setObjectName("tituloDialogoSicap")
        descripcion = QLabel(
            "Los permisos mostrados corresponden al modelo real del sistema y no a una matriz CRUD generica."
        )
        descripcion.setObjectName("descripcionDialogoSicap")
        descripcion.setWordWrap(True)

        leyenda = QLabel(
            "Cada celda muestra acciones reales como VER, GESTIONAR, REGISTRAR o GENERAR, agrupadas por modulo."
        )
        leyenda.setObjectName("descripcionDialogoSicap")
        leyenda.setWordWrap(True)

        tabla = QTableWidget()
        tabla.setObjectName("tablaMatrizPermisosUsuarios")
        modulos = self._modulos_visibles()
        columnas = 1 + len(self._roles)
        tabla.setColumnCount(columnas)
        tabla.setRowCount(len(modulos))
        encabezados = ["Modulo"] + [rol.nombre for rol in self._roles]
        configurar_tabla_operativa(tabla, encabezados)
        tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        tabla.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        tabla.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        tabla.horizontalHeader().setStretchLastSection(False)
        tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        for indice in range(1, columnas):
            tabla.horizontalHeader().setSectionResizeMode(indice, QHeaderView.ResizeMode.Stretch)
        tabla.verticalHeader().setDefaultSectionSize(64)
        tabla.setFrameShape(QFrame.Shape.NoFrame)
        tabla.viewport().setObjectName("viewportTablaMatrizPermisosUsuarios")

        for fila, modulo in enumerate(modulos):
            tabla.setItem(fila, 0, crear_item_tabla(modulo))
            for columna, rol in enumerate(self._roles, start=1):
                tabla.setCellWidget(fila, columna, self._crear_celda_permisos(rol, modulo))

        fila_acciones = QHBoxLayout()
        fila_acciones.setSpacing(10)
        fila_acciones.addStretch(1)
        boton_cerrar = BotonAccionContextual(
            "Cerrar",
            variante="primario",
            centrado=True,
            mostrar_icono=False,
        )
        boton_cerrar.setMinimumWidth(140)
        boton_cerrar.clicked.connect(self.accept)
        fila_acciones.addWidget(boton_cerrar)

        self.layout_cabecera.addWidget(titulo)
        self.layout_cabecera.addWidget(descripcion)
        self.layout_cuerpo.addWidget(leyenda)
        self.layout_cuerpo.addWidget(tabla)
        self.layout_pie.addLayout(fila_acciones)
        self._aplicar_estilos()

    def _modulos_visibles(self) -> list[str]:
        modulos = {
            permiso.modulo.strip()
            for rol in self._roles
            for permiso in rol.permisos
            if permiso.modulo.strip()
        }
        return sorted(modulos, key=str.casefold)

    def _crear_celda_permisos(self, rol: RolSistema, modulo: str) -> QWidget:
        contenedor = QWidget()
        layout = QHBoxLayout(contenedor)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        etiquetas = self._resumir_acciones_modulo(rol, modulo)
        if not etiquetas:
            etiqueta_vacia = QLabel("Sin acceso")
            etiqueta_vacia.setObjectName("badgePermisoSinAcceso")
            layout.addWidget(etiqueta_vacia)
            layout.addStretch(1)
            return contenedor

        for texto, color in etiquetas:
            badge = QLabel(texto)
            badge.setObjectName("badgePermisoRol")
            badge.setProperty("color", color)
            badge.style().unpolish(badge)
            badge.style().polish(badge)
            layout.addWidget(badge)
        layout.addStretch(1)
        return contenedor

    @staticmethod
    def _resumir_acciones_modulo(rol: RolSistema, modulo: str) -> list[tuple[str, str]]:
        acciones: list[tuple[str, str]] = []
        colores = {
            "VER": "cyan",
            "GESTIONAR": "purple",
            "REGISTRAR": "green",
            "GENERAR": "blue",
            "RESPALDO": "orange",
            "LOGS": "red",
            "AUDITAR": "indigo",
        }
        vistos: set[str] = set()
        for permiso in rol.permisos:
            if permiso.modulo.strip().casefold() != modulo.casefold():
                continue
            accion = permiso.codigo.split(".")[-1].replace("_", " ").upper()
            if accion in vistos:
                continue
            vistos.add(accion)
            acciones.append((accion, colores.get(accion, "gris")))
        return acciones

    def _aplicar_estilos(self) -> None:
        self.setStyleSheet(
            self.styleSheet()
            + """
            QTableWidget#tablaMatrizPermisosUsuarios {
                background: rgba(74, 79, 154, 0.88);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 18px;
            }
            QTableWidget#tablaMatrizPermisosUsuarios QTableCornerButton::section {
                background: rgba(108, 113, 190, 0.92);
                border: none;
            }
            QWidget#viewportTablaMatrizPermisosUsuarios {
                background: transparent;
                border: none;
            }
            QLabel#badgePermisoRol,
            QLabel#badgePermisoSinAcceso {
                border-radius: 10px;
                padding: 4px 8px;
                font-size: 10px;
                font-weight: 800;
            }
            QLabel#badgePermisoSinAcceso {
                color: rgba(235, 242, 248, 0.7);
                background: rgba(132, 146, 166, 0.18);
                border: 1px solid rgba(255, 255, 255, 0.10);
            }
            QLabel#badgePermisoRol[color="cyan"] {
                color: #d5f7ff;
                background: rgba(44, 177, 212, 0.18);
                border: 1px solid rgba(122, 226, 255, 0.22);
            }
            QLabel#badgePermisoRol[color="purple"] {
                color: #efe2ff;
                background: rgba(146, 101, 255, 0.18);
                border: 1px solid rgba(195, 169, 255, 0.22);
            }
            QLabel#badgePermisoRol[color="green"] {
                color: #d9fff5;
                background: rgba(16, 120, 98, 0.18);
                border: 1px solid rgba(158, 231, 214, 0.26);
            }
            QLabel#badgePermisoRol[color="blue"] {
                color: #dce9ff;
                background: rgba(79, 163, 255, 0.18);
                border: 1px solid rgba(140, 194, 255, 0.26);
            }
            QLabel#badgePermisoRol[color="orange"] {
                color: #ffefd5;
                background: rgba(255, 170, 44, 0.18);
                border: 1px solid rgba(255, 210, 152, 0.24);
            }
            QLabel#badgePermisoRol[color="red"] {
                color: #ffd9d5;
                background: rgba(255, 98, 92, 0.18);
                border: 1px solid rgba(255, 175, 170, 0.24);
            }
            QLabel#badgePermisoRol[color="indigo"] {
                color: #e2e5ff;
                background: rgba(112, 127, 255, 0.18);
                border: 1px solid rgba(174, 183, 255, 0.24);
            }
            QLabel#badgePermisoRol[color="gris"] {
                color: #eef4ff;
                background: rgba(132, 146, 166, 0.18);
                border: 1px solid rgba(255, 255, 255, 0.10);
            }
            """
        )


class VistaUsuarios(QWidget):
    """Pantalla operativa para gestion administrativa de usuarios."""

    DURACION_MENSAJE_MS = 4200
    ANCHO_COLUMNA_ACCIONES = 190

    filtro_texto_cambiado = Signal(str)
    filtro_rapido_cambiado = Signal(str)
    filtro_rol_cambiado = Signal(str)
    exportar_solicitado = Signal()
    nuevo_usuario_solicitado = Signal()
    detalle_usuario_solicitado = Signal(int)
    editar_usuario_solicitado = Signal(int)
    cambio_estado_solicitado = Signal(int)
    gestion_acceso_solicitada = Signal(int)
    ver_matriz_permisos_solicitada = Signal()
    nuevo_rol_solicitado = Signal()
    editar_rol_solicitado = Signal(int)
    cambio_estado_rol_solicitado = Signal(int)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("vistaUsuarios")
        self._tema_actual = TEMA_SICAP_PREDETERMINADO
        self._paleta_tema = obtener_paleta_tema(self._tema_actual)
        self._roles_actuales: list[RolSistema] = []
        self._permisos_roles: list[PermisoSistema] = []
        self._filtro_rol_actual = FILTRO_USUARIOS_TODOS
        self._temporizador_mensaje = QTimer(self)
        self._temporizador_mensaje.setSingleShot(True)
        self._temporizador_mensaje.timeout.connect(self._ocultar_mensaje)
        self._construir_ui()
        self._aplicar_estilos()

    def aplicar_tema(self, nombre_tema: str) -> None:
        self._tema_actual = nombre_tema if nombre_tema in ("oscuro", "claro") else TEMA_SICAP_PREDETERMINADO
        self._paleta_tema = obtener_paleta_tema(self._tema_actual)
        self._aplicar_estilos()
        for boton in (self._boton_exportar, self._boton_nuevo):
            aplicar_estilo_boton_operativo(boton, principal=boton is self._boton_nuevo)

    def mostrar_resumen(self, resumen: ResumenUsuarios) -> None:
        self._tarjeta_total.actualizar(
            "Total de usuarios",
            str(resumen.total_usuarios),
            "Cuentas visibles en administracion.",
        )
        self._tarjeta_activos.actualizar(
            "Usuarios activos",
            str(resumen.usuarios_activos),
            "Cuentas habilitadas para operar.",
        )
        self._tarjeta_admins.actualizar(
            "Administradores",
            str(resumen.administradores),
            "Usuarios con gestion administrativa.",
        )
        self._tarjeta_accesos.actualizar(
            "Ultimos accesos hoy",
            str(resumen.accesos_hoy),
            "Inicios de sesion registrados hoy.",
        )

    def mostrar_roles(
        self,
        roles: list[RolSistema],
        permisos_disponibles: Iterable[PermisoSistema],
    ) -> None:
        self._roles_actuales = list(roles)
        self._permisos_roles = list(permisos_disponibles)
        self._actualizar_filtro_roles()
        self._renderizar_tarjetas_roles()

    def mostrar_usuarios(
        self,
        usuarios: list[UsuarioSistema],
        formateador_fecha: Callable[[str | None], str],
    ) -> None:
        self._tabla.setRowCount(len(usuarios))
        for fila, usuario in enumerate(usuarios):
            self._tabla.setItem(fila, 0, self._crear_item_usuario(usuario.nombre_usuario, usuario))
            self._tabla.setItem(fila, 1, crear_item_tabla(usuario.nombre_completo))
            self._tabla.setItem(fila, 2, crear_item_tabla(usuario.correo))
            self._tabla.setCellWidget(fila, 3, self._crear_badge_rol(usuario.rol_principal))
            self._tabla.setCellWidget(fila, 4, self._crear_badge_estado(usuario.estado))
            self._tabla.setItem(fila, 5, crear_item_tabla(formateador_fecha(usuario.ultimo_acceso_en)))
            self._tabla.setCellWidget(fila, 6, self._crear_acciones_fila(usuario))

        sin_datos = len(usuarios) == 0
        self._tabla.setVisible(not sin_datos)
        self._estado_vacio.setVisible(sin_datos)

    def mostrar_mensaje(self, mensaje: str, es_error: bool = False) -> None:
        self._mensaje.setText(mensaje)
        self._mensaje.setProperty("error", es_error)
        self._mensaje.style().unpolish(self._mensaje)
        self._mensaje.style().polish(self._mensaje)
        self._mensaje.setVisible(bool(mensaje))
        if mensaje:
            self._temporizador_mensaje.start(self.DURACION_MENSAJE_MS)

    def solicitar_datos_usuario(
        self,
        roles: Iterable[RolSistema],
        usuario: UsuarioSistema | None = None,
    ) -> FormularioUsuario | None:
        dialogo = DialogoFormularioUsuario(roles=roles, usuario=usuario, parent=self)
        return dialogo.obtener_formulario() if dialogo.exec() == QDialog.DialogCode.Accepted else None

    def solicitar_datos_rol(
        self,
        permisos_disponibles: Iterable[PermisoSistema],
        rol: RolSistema | None = None,
    ) -> FormularioRol | None:
        dialogo = DialogoFormularioRol(
            permisos_disponibles=permisos_disponibles,
            rol=rol,
            parent=self,
        )
        return dialogo.obtener_formulario() if dialogo.exec() == QDialog.DialogCode.Accepted else None

    def mostrar_detalle_usuario(
        self,
        usuario: UsuarioSistema,
        formateador_fecha: Callable[[str | None], str],
    ) -> str:
        dialogo = DialogoDetalleUsuario(usuario=usuario, formateador_fecha=formateador_fecha, parent=self)
        dialogo.exec()
        return dialogo.accion_resultado

    def solicitar_gestion_acceso(self, usuario: UsuarioSistema) -> tuple[str, str, str] | None:
        dialogo = DialogoGestionAccesoUsuario(usuario=usuario, parent=self)
        if dialogo.exec() != QDialog.DialogCode.Accepted:
            return None
        return dialogo.obtener_resultado()

    def mostrar_matriz_permisos(self, roles: Iterable[RolSistema]) -> None:
        DialogoMatrizPermisosUsuarios(roles=roles, parent=self).exec()

    def confirmar_cambio_estado_usuario(self, usuario: UsuarioSistema) -> bool:
        accion = "desactivar" if usuario.estado == "ACTIVO" else "activar"
        dialogo = DialogoConfirmacionSicap(
            titulo=f"Confirmar {accion} usuario",
            descripcion=(
                "Esta accion cambiara el estado operativo de la cuenta seleccionada."
            ),
            detalles=(
                ("Usuario", usuario.nombre_usuario),
                ("Nombre", usuario.nombre_completo),
                ("Estado actual", usuario.estado.title()),
            ),
            texto_confirmar=accion.title(),
            variante_confirmar="peligro" if accion == "desactivar" else "primario",
            parent=self,
        )
        return dialogo.exec() == QDialog.DialogCode.Accepted

    def confirmar_cambio_estado_rol(self, rol: RolSistema) -> bool:
        accion = "desactivar" if rol.estado == "ACTIVO" else "activar"
        dialogo = DialogoConfirmacionSicap(
            titulo=f"Confirmar {accion} rol",
            descripcion="Esta accion cambiara el estado operativo del rol seleccionado.",
            detalles=(
                ("Rol", rol.nombre),
                ("Estado actual", rol.estado.title()),
                ("Usuarios vinculados", str(rol.total_usuarios)),
            ),
            texto_confirmar=accion.title(),
            variante_confirmar="peligro" if accion == "desactivar" else "primario",
            parent=self,
        )
        return dialogo.exec() == QDialog.DialogCode.Accepted

    def solicitar_ruta_exportacion(self) -> str:
        ruta, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar usuarios",
            "usuarios.csv",
            "CSV (*.csv)",
        )
        return ruta

    def _construir_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        encabezado = QHBoxLayout()
        encabezado.setSpacing(12)
        bloque_titulo = QVBoxLayout()
        bloque_titulo.setSpacing(4)
        descripcion = QLabel("Gestion de usuarios, roles visibles y control de acceso operativo.")
        descripcion.setObjectName("descripcionModulo")
        descripcion.setWordWrap(True)
        bloque_titulo.addWidget(descripcion)

        fila_acciones = QHBoxLayout()
        fila_acciones.setSpacing(8)
        fila_acciones.addStretch(1)
        self._boton_exportar = crear_boton_operativo("Exportar")
        self._boton_nuevo = crear_boton_operativo("Nuevo usuario", principal=True)
        self._boton_exportar.clicked.connect(self.exportar_solicitado.emit)
        self._boton_nuevo.clicked.connect(self.nuevo_usuario_solicitado.emit)
        fila_acciones.addWidget(self._boton_exportar)
        fila_acciones.addWidget(self._boton_nuevo)

        encabezado.addLayout(bloque_titulo, 1)
        encabezado.addLayout(fila_acciones)

        self._mensaje = QLabel("")
        self._mensaje.setObjectName("mensajeUsuarios")
        self._mensaje.setVisible(False)
        self._mensaje.setWordWrap(True)

        self._tabs = QTabWidget()
        self._tabs.setObjectName("tabsUsuarios")
        self._tabs.addTab(self._crear_pestana_usuarios(), "Usuarios")
        self._tabs.addTab(self._crear_pestana_roles(), "Roles")

        layout.addLayout(encabezado)
        layout.addWidget(self._mensaje)
        layout.addWidget(self._tabs, 1)

    def _crear_pestana_usuarios(self) -> QWidget:
        pagina = QWidget()
        layout = QVBoxLayout(pagina)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        tarjetas = QGridLayout()
        tarjetas.setHorizontalSpacing(10)
        tarjetas.setVerticalSpacing(10)
        self._tarjeta_total = TarjetaResumenUsuario("user.svg", "#8ec9ff")
        self._tarjeta_activos = TarjetaResumenUsuario("circle-check.svg", "#8de8c7")
        self._tarjeta_admins = TarjetaResumenUsuario("key.svg", "#7ce5f4")
        self._tarjeta_accesos = TarjetaResumenUsuario("clock.svg", "#93b8ff")
        tarjetas.addWidget(self._tarjeta_total, 0, 0)
        tarjetas.addWidget(self._tarjeta_activos, 0, 1)
        tarjetas.addWidget(self._tarjeta_admins, 0, 2)
        tarjetas.addWidget(self._tarjeta_accesos, 0, 3)

        panel_filtros = QFrame()
        panel_filtros.setObjectName("panelOperativoUsuarios")
        layout_filtros = QVBoxLayout(panel_filtros)
        layout_filtros.setContentsMargins(14, 14, 14, 14)
        layout_filtros.setSpacing(10)

        fila_filtros = QHBoxLayout()
        fila_filtros.setSpacing(10)

        self._campo_busqueda = QLineEdit()
        self._campo_busqueda.setPlaceholderText("Buscar por nombre, usuario o correo")
        self._campo_busqueda.textChanged.connect(self.filtro_texto_cambiado.emit)
        fila_filtros.addWidget(self._campo_busqueda, 1)

        self._grupo_filtros = QButtonGroup(self)
        self._grupo_filtros.setExclusive(True)
        self._botones_filtro: dict[str, QPushButton] = {}
        for codigo, texto in (
            (FILTRO_USUARIOS_TODOS, "Todos"),
            (FILTRO_USUARIOS_ACTIVOS, "Activos"),
            (FILTRO_USUARIOS_INACTIVOS, "Inactivos"),
            (FILTRO_USUARIOS_ADMINISTRADORES, "Administradores"),
        ):
            boton = QPushButton(texto)
            boton.setObjectName("chipFiltroUsuario")
            boton.setCheckable(True)
            boton.setCursor(Qt.CursorShape.PointingHandCursor)
            boton.clicked.connect(
                lambda checked=False, valor=codigo: self.filtro_rapido_cambiado.emit(valor)
            )
            self._grupo_filtros.addButton(boton)
            self._botones_filtro[codigo] = boton
            fila_filtros.addWidget(boton)
        self._botones_filtro[FILTRO_USUARIOS_TODOS].setChecked(True)

        self._combo_roles = QComboBox()
        self._combo_roles.setObjectName("comboFiltroRolUsuarios")
        self._combo_roles.setMinimumWidth(210)
        self._combo_roles.currentIndexChanged.connect(self._emitir_filtro_rol)
        fila_filtros.addWidget(self._combo_roles)
        layout_filtros.addLayout(fila_filtros)

        panel_tabla = QFrame()
        panel_tabla.setObjectName("panelTablaUsuarios")
        layout_tabla = QVBoxLayout(panel_tabla)
        layout_tabla.setContentsMargins(14, 14, 14, 14)
        layout_tabla.setSpacing(10)

        self._tabla = QTableWidget(0, 7)
        self._tabla.setObjectName("tablaUsuarios")
        configurar_tabla_operativa(
            self._tabla,
            [
                "Usuario",
                "Nombre completo",
                "Correo",
                "Rol",
                "Estado",
                "Ultimo acceso",
                "Acciones",
            ],
        )
        self._tabla.horizontalHeader().setStretchLastSection(False)
        self._tabla.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self._tabla.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self._tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._tabla.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self._tabla.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self._tabla.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self._tabla.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self._tabla.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Interactive)
        self._tabla.setColumnWidth(6, self.ANCHO_COLUMNA_ACCIONES)
        self._tabla.verticalHeader().setDefaultSectionSize(60)
        self._tabla.setAlternatingRowColors(True)
        self._tabla.setFrameShape(QFrame.Shape.NoFrame)
        self._tabla.setViewportMargins(0, 0, 0, 18)
        self._tabla.viewport().setObjectName("viewportTablaUsuarios")
        self._tabla.viewport().setAutoFillBackground(False)

        self._estado_vacio = QLabel("No hay usuarios que coincidan con los filtros actuales.")
        self._estado_vacio.setObjectName("estadoVacioUsuarios")
        self._estado_vacio.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._estado_vacio.setVisible(False)

        layout_tabla.addWidget(self._tabla)
        layout_tabla.addWidget(self._estado_vacio)

        layout.addLayout(tarjetas)
        layout.addWidget(panel_filtros)
        layout.addWidget(panel_tabla, 1)
        return pagina

    def _crear_pestana_roles(self) -> QWidget:
        pagina = QWidget()
        layout = QVBoxLayout(pagina)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        encabezado = QHBoxLayout()
        encabezado.addStretch(1)

        fila_acciones = QHBoxLayout()
        fila_acciones.setSpacing(8)
        boton_crear = crear_boton_operativo("Crear rol", principal=True)
        boton_crear.clicked.connect(self.nuevo_rol_solicitado.emit)
        fila_acciones.addWidget(boton_crear)
        encabezado.addLayout(fila_acciones)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setObjectName("scrollRolesUsuarios")

        contenedor = QWidget()
        self._layout_tarjetas_roles = QGridLayout(contenedor)
        self._layout_tarjetas_roles.setContentsMargins(0, 0, 0, 0)
        self._layout_tarjetas_roles.setHorizontalSpacing(12)
        self._layout_tarjetas_roles.setVerticalSpacing(12)
        scroll.setWidget(contenedor)

        self._nota_roles = QLabel(
            "Los roles visibles se asignan desde el formulario de usuarios. El superadministrador tecnico permanece fuera del flujo operativo y no se edita aqui."
        )
        self._nota_roles.setObjectName("notaRolesUsuarios")
        self._nota_roles.setWordWrap(True)

        layout.addLayout(encabezado)
        layout.addWidget(scroll, 1)
        layout.addWidget(self._nota_roles)
        return pagina

    def _crear_item_usuario(self, texto: str, usuario: UsuarioSistema) -> QTableWidgetItem:
        item = crear_item_tabla(texto)
        item.setData(Qt.ItemDataRole.UserRole, usuario)
        return item

    def _crear_badge_rol(self, rol: str) -> QWidget:
        contenedor = QWidget()
        layout = QHBoxLayout(contenedor)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        badge = QLabel(rol.title())
        badge.setObjectName("badgeRolUsuario")
        badge.setProperty("administrador", "ADMINISTRADOR" in rol.upper())
        badge.style().unpolish(badge)
        badge.style().polish(badge)
        layout.addWidget(badge, alignment=Qt.AlignmentFlag.AlignCenter)
        return contenedor

    def _crear_badge_estado(self, estado: str) -> QWidget:
        contenedor = QWidget()
        layout = QHBoxLayout(contenedor)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        badge = QLabel(estado.title())
        badge.setObjectName("badgeEstadoUsuario")
        badge.setProperty("activo", estado == "ACTIVO")
        badge.style().unpolish(badge)
        badge.style().polish(badge)
        layout.addWidget(badge, alignment=Qt.AlignmentFlag.AlignCenter)
        return contenedor

    def _crear_acciones_fila(self, usuario: UsuarioSistema) -> QWidget:
        contenedor = QWidget()
        contenedor.setObjectName("contenedorAccionesUsuario")
        contenedor.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        contenedor.setMinimumWidth(self.ANCHO_COLUMNA_ACCIONES)
        contenedor.setMinimumHeight(58)
        layout = QHBoxLayout(contenedor)
        layout.setContentsMargins(0, 0, 0, 14)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        boton_detalle = BotonIconoFilaUsuario("eye.svg", "#4fa3ff", "Ver informacion")
        boton_editar = BotonIconoFilaUsuario("user.svg", "#4fa3ff", "Editar usuario")
        boton_estado = BotonIconoFilaUsuario(
            "lock.svg" if usuario.estado == "ACTIVO" else "circle-check.svg",
            "#ff625c" if usuario.estado == "ACTIVO" else "#4fa3ff",
            "Desactivar" if usuario.estado == "ACTIVO" else "Activar",
        )
        boton_seguridad = BotonIconoFilaUsuario("key.svg", "#93b8ff", "Gestionar acceso")

        boton_detalle.clicked.connect(
            lambda checked=False, identificador=usuario.identificador: self.detalle_usuario_solicitado.emit(
                int(identificador)
            )
        )
        boton_editar.clicked.connect(
            lambda checked=False, identificador=usuario.identificador: self.editar_usuario_solicitado.emit(
                int(identificador)
            )
        )
        boton_estado.clicked.connect(
            lambda checked=False, identificador=usuario.identificador: self.cambio_estado_solicitado.emit(
                int(identificador)
            )
        )
        boton_seguridad.clicked.connect(
            lambda checked=False, identificador=usuario.identificador: self.gestion_acceso_solicitada.emit(
                int(identificador)
            )
        )

        if usuario.es_tecnico or usuario.es_oculto or usuario.es_superadministrador():
            boton_editar.setDisabled(True)
            boton_estado.setDisabled(True)
            boton_seguridad.setDisabled(True)

        layout.addWidget(boton_detalle)
        layout.addWidget(boton_editar)
        layout.addWidget(boton_estado)
        layout.addWidget(boton_seguridad)
        return contenedor

    def _actualizar_filtro_roles(self) -> None:
        self._combo_roles.blockSignals(True)
        self._combo_roles.clear()
        self._combo_roles.addItem("Todos los roles", FILTRO_USUARIOS_TODOS)
        for rol in self._roles_actuales:
            self._combo_roles.addItem(rol.nombre, rol.nombre)
        indice = self._combo_roles.findData(self._filtro_rol_actual)
        self._combo_roles.setCurrentIndex(indice if indice >= 0 else 0)
        self._combo_roles.blockSignals(False)

    def _renderizar_tarjetas_roles(self) -> None:
        while self._layout_tarjetas_roles.count():
            item = self._layout_tarjetas_roles.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        for indice, rol in enumerate(self._roles_actuales):
            fila = indice // 2
            columna = indice % 2
            self._layout_tarjetas_roles.addWidget(self._crear_tarjeta_rol(rol), fila, columna)
        if not self._roles_actuales:
            vacio = QLabel("No hay roles visibles para este perfil.")
            vacio.setObjectName("estadoVacioUsuarios")
            vacio.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._layout_tarjetas_roles.addWidget(vacio, 0, 0)

    def _crear_tarjeta_rol(self, rol: RolSistema) -> QFrame:
        tarjeta = QFrame()
        tarjeta.setObjectName("tarjetaRolUsuario")
        layout = QVBoxLayout(tarjeta)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        fila = QHBoxLayout()
        fila.setSpacing(8)
        bloque_titulo = QVBoxLayout()
        bloque_titulo.setSpacing(4)
        fila_titulo = QHBoxLayout()
        fila_titulo.setSpacing(8)
        titulo = QLabel(rol.nombre)
        titulo.setObjectName("tituloRolUsuario")
        badge = QLabel("Sistema" if rol.es_sistema else rol.estado.title())
        badge.setObjectName("badgeRolSistemaUsuario")
        badge.setProperty("sistema", rol.es_sistema)
        badge.style().unpolish(badge)
        badge.style().polish(badge)
        fila_titulo.addWidget(titulo)
        fila_titulo.addWidget(badge, alignment=Qt.AlignmentFlag.AlignLeft)
        fila_titulo.addStretch(1)
        descripcion = QLabel(rol.descripcion or "Rol sin descripcion.")
        descripcion.setObjectName("descripcionRolUsuario")
        descripcion.setWordWrap(True)
        bloque_titulo.addLayout(fila_titulo)
        bloque_titulo.addWidget(descripcion)

        boton_estado = BotonIconoFilaUsuario(
            "lock.svg" if rol.estado == "ACTIVO" else "circle-check.svg",
            "#ff625c" if rol.estado == "ACTIVO" else "#4fa3ff",
            "Desactivar rol" if rol.estado == "ACTIVO" else "Activar rol",
        )
        boton_estado.clicked.connect(
            lambda checked=False, identificador=rol.identificador: self.cambio_estado_rol_solicitado.emit(
                int(identificador)
            )
        )

        fila.addLayout(bloque_titulo, 1)
        fila.addWidget(boton_estado, alignment=Qt.AlignmentFlag.AlignTop)

        metricas = QHBoxLayout()
        metricas.setSpacing(12)
        metricas.addWidget(self._crear_minitarjeta_rol("Usuarios", str(rol.total_usuarios)))
        metricas.addWidget(self._crear_minitarjeta_rol("Permisos", str(len(rol.permisos))))

        titulo_modulos = QLabel("Permisos por modulo")
        titulo_modulos.setObjectName("tituloMiniTarjetaRolUsuario")
        chips_modulos = self._crear_lista_permisos_modulo(rol)

        separador = QFrame()
        separador.setObjectName("separadorRolUsuario")
        separador.setFixedHeight(1)

        fila_acciones = QHBoxLayout()
        fila_acciones.setSpacing(8)
        boton_editar = BotonAccionContextual(
            "Editar",
            variante="edicion",
            centrado=True,
            mostrar_icono=False,
        )
        boton_editar.clicked.connect(
            lambda checked=False, identificador=rol.identificador: self.editar_rol_solicitado.emit(
                int(identificador)
            )
        )
        fila_acciones.addWidget(boton_editar)
        fila_acciones.addStretch(1)

        layout.addLayout(fila)
        layout.addLayout(metricas)
        layout.addWidget(titulo_modulos)
        layout.addWidget(chips_modulos)
        layout.addWidget(separador)
        layout.addLayout(fila_acciones)
        return tarjeta

    def _crear_minitarjeta_rol(self, titulo: str, valor: str) -> QFrame:
        tarjeta = QFrame()
        tarjeta.setObjectName("miniTarjetaRolUsuario")
        layout = QVBoxLayout(tarjeta)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(3)
        label_titulo = QLabel(titulo)
        label_titulo.setObjectName("tituloMiniTarjetaRolUsuario")
        label_valor = QLabel(valor)
        label_valor.setObjectName("valorMiniTarjetaRolUsuario")
        layout.addWidget(label_titulo)
        layout.addWidget(label_valor)
        return tarjeta

    def _crear_chips_modulos(self, modulos: list[str]) -> QWidget:
        contenedor = QWidget()
        layout = QGridLayout(contenedor)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setHorizontalSpacing(6)
        layout.setVerticalSpacing(6)
        modulos_visibles = modulos[:6]
        for indice, modulo in enumerate(modulos_visibles):
            chip = QLabel(modulo)
            chip.setObjectName("chipModuloRolUsuario")
            layout.addWidget(chip, indice // 3, indice % 3)
        if len(modulos) > 6:
            adicional = QLabel(f"+{len(modulos) - 6}")
            adicional.setObjectName("chipModuloRolUsuarioSecundario")
            layout.addWidget(adicional, len(modulos_visibles) // 3, len(modulos_visibles) % 3)
        return contenedor

    def _crear_lista_permisos_modulo(self, rol: RolSistema) -> QWidget:
        contenedor = QWidget()
        layout = QVBoxLayout(contenedor)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        for modulo, acciones in self._acciones_por_modulo_rol(rol):
            fila = QWidget()
            fila_layout = QHBoxLayout(fila)
            fila_layout.setContentsMargins(0, 0, 0, 0)
            fila_layout.setSpacing(8)
            etiqueta_modulo = QLabel(modulo)
            etiqueta_modulo.setObjectName("tituloModuloPermisoRolUsuario")
            fila_layout.addWidget(etiqueta_modulo)
            fila_layout.addWidget(self._crear_badges_acciones_rol(acciones), 1)
            layout.addWidget(fila)
        if layout.count() == 0:
            vacio = QLabel("Sin permisos asignados.")
            vacio.setObjectName("detallePermisoRolUsuario")
            layout.addWidget(vacio)
        return contenedor

    def _crear_badges_acciones_rol(self, acciones: list[str]) -> QWidget:
        contenedor = QWidget()
        layout = QHBoxLayout(contenedor)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        for accion in acciones:
            badge = QLabel(accion)
            badge.setObjectName("badgeAccionPermisoRolUsuario")
            layout.addWidget(badge)
        layout.addStretch(1)
        return contenedor

    @staticmethod
    def _acciones_por_modulo_rol(rol: RolSistema) -> list[tuple[str, list[str]]]:
        agrupados: dict[str, list[str]] = {}
        for permiso in rol.permisos:
            modulo = permiso.modulo.strip()
            if not modulo:
                continue
            accion = permiso.codigo.split(".")[-1].replace("_", " ").title()
            agrupados.setdefault(modulo, [])
            if accion not in agrupados[modulo]:
                agrupados[modulo].append(accion)
        return sorted(agrupados.items(), key=lambda item: item[0].casefold())

    @staticmethod
    def _modulos_resumidos_rol(rol: RolSistema) -> list[str]:
        modulos: list[str] = []
        vistos: set[str] = set()
        for permiso in rol.permisos:
            nombre = permiso.modulo.strip()
            if not nombre or nombre in vistos:
                continue
            vistos.add(nombre)
            modulos.append(nombre)
        return modulos

    def _emitir_filtro_rol(self) -> None:
        self._filtro_rol_actual = str(self._combo_roles.currentData() or FILTRO_USUARIOS_TODOS)
        self.filtro_rol_cambiado.emit(self._filtro_rol_actual)

    def _ocultar_mensaje(self) -> None:
        self._mensaje.clear()
        self._mensaje.setVisible(False)

    def _aplicar_estilos(self) -> None:
        paleta = self._paleta_tema
        fondo_header_destacado = obtener_fondo_header_destacado(self._tema_actual)
        self.setStyleSheet(
            f"""
            QWidget#vistaUsuarios {{
                background: transparent;
                font-family: "{paleta["familia_tipografica"]}";
            }}
            QLabel#tituloModulo {{
                color: #ffffff;
                font-size: 19px;
                font-weight: 900;
            }}
            QLabel#subtituloModuloUsuarios,
            QLabel#tituloPanelPermisosUsuarios,
            QLabel#tituloRolUsuario,
            QLabel#valorMiniTarjetaRolUsuario {{
                color: #ffffff;
                font-weight: 800;
            }}
            QLabel#subtituloModuloUsuarios {{
                font-size: 18px;
            }}
            QLabel#descripcionModulo,
            QLabel#detalleTarjetaResumenUsuario,
            QLabel#textoPanelPermisosUsuarios,
            QLabel#detalleRolesUsuarios,
            QLabel#notaRolesUsuarios,
            QLabel#descripcionRolUsuario,
            QLabel#tituloMiniTarjetaRolUsuario {{
                color: rgba(235, 242, 248, 0.76);
                font-size: 11px;
            }}
            QLabel#mensajeUsuarios {{
                color: #d9fff5;
                font-size: 12px;
                font-weight: 700;
                padding: 8px 10px;
                border-radius: 12px;
                background-color: rgba(16, 120, 98, 0.16);
                border: 1px solid rgba(158, 231, 214, 0.26);
            }}
            QLabel#mensajeUsuarios[error="true"] {{
                color: #ffd4cf;
                background-color: rgba(180, 35, 24, 0.15);
                border: 1px solid rgba(255, 205, 199, 0.28);
            }}
            QFrame#panelOperativoUsuarios,
            QFrame#tarjetaResumenUsuarios,
            QFrame#panelPermisosUsuarios,
            QFrame#tarjetaRolUsuario,
            QFrame#miniTarjetaRolUsuario {{
                background: rgba(255, 255, 255, 0.10);
                border: 1px solid rgba(255, 255, 255, 0.16);
                border-radius: 18px;
            }}
            QFrame#panelPermisosUsuarios {{
                background: rgba(79, 163, 255, 0.12);
                border: 1px solid rgba(138, 194, 255, 0.22);
            }}
            QFrame#tarjetaRolUsuario {{
                background: rgba(255, 255, 255, 0.12);
                border-color: rgba(255, 255, 255, 0.18);
            }}
            QFrame#panelOperativoUsuarios,
            QFrame#tarjetaResumenUsuarios,
            QFrame#miniTarjetaRolUsuario {{
                background: {fondo_header_destacado};
                border: 1px solid rgba(255, 255, 255, 0.16);
            }}
            QFrame#panelTablaUsuarios {{
                background: {fondo_header_destacado};
                border: 1px solid rgba(255, 255, 255, 0.16);
                border-radius: 18px;
            }}
            QTableWidget#tablaUsuarios {{
                background: rgba(74, 79, 154, 0.88);
                background-clip: padding;
                border: none;
                border-radius: 18px;
                padding: 0 0 18px 0;
            }}
            QWidget#viewportTablaUsuarios {{
                background: transparent;
                border: none;
                border-bottom-left-radius: 18px;
                border-bottom-right-radius: 18px;
            }}
            QTableWidget#tablaUsuarios QHeaderView::section:first {{
                border-top-left-radius: 18px;
            }}
            QTableWidget#tablaUsuarios QHeaderView::section {{
                background: rgba(108, 113, 190, 0.92);
                color: #f7fbff;
                border: none;
                border-right: 1px solid rgba(255, 255, 255, 0.08);
                border-bottom: 1px solid rgba(255, 255, 255, 0.08);
                padding: 10px 12px;
                font-size: 12px;
                font-weight: 800;
            }}
            QTableWidget#tablaUsuarios QHeaderView::section:last {{
                border-top-right-radius: 18px;
            }}
            QTableWidget#tablaUsuarios::item {{
                padding: 9px 12px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.08);
                background: rgba(255, 255, 255, 0.03);
            }}
            QTableWidget#tablaUsuarios::item:alternate {{
                background: rgba(255, 255, 255, 0.07);
            }}
            QTableWidget#tablaUsuarios::item:selected {{
                background: rgba(142, 201, 255, 0.10);
            }}
            QLabel#iconoTarjetaResumenUsuario,
            QLabel#iconoPanelPermisosUsuarios {{
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.10);
                border-radius: 12px;
            }}
            QLabel#tituloTarjetaResumenUsuario {{
                color: rgba(235, 242, 248, 0.72);
                font-size: 11px;
                font-weight: 700;
            }}
            QLabel#valorTarjetaResumenUsuario {{
                color: #ffffff;
                font-size: 20px;
                font-weight: 900;
            }}
            QLineEdit,
            QComboBox,
            QPlainTextEdit {{
                min-height: 36px;
                border: 1px solid rgba(255, 255, 255, 0.18);
                border-radius: 12px;
                background: rgba(255, 255, 255, 0.11);
                color: #f5fbff;
                padding: 0 10px;
                font-size: 12px;
            }}
            QPlainTextEdit {{
                min-height: 88px;
                padding: 10px;
            }}
            QLineEdit:focus,
            QComboBox:focus,
            QPlainTextEdit:focus {{
                border-color: rgba(109, 241, 220, 0.42);
                background: rgba(255, 255, 255, 0.16);
            }}
            QComboBox::drop-down {{
                border: none;
                width: 24px;
                background: rgba(255, 255, 255, 0.06);
                border-top-right-radius: 12px;
                border-bottom-right-radius: 12px;
            }}
            QComboBox QAbstractItemView {{
                background: rgba(29, 33, 68, 0.98);
                color: #f5fbff;
                border: 1px solid rgba(255, 255, 255, 0.14);
                selection-background-color: rgba(109, 241, 220, 0.22);
                selection-color: #ffffff;
                padding: 6px;
            }}
            QPushButton#chipFiltroUsuario {{
                min-height: 30px;
                border-radius: 11px;
                padding: 0 12px;
                background: rgba(255, 255, 255, 0.06);
                border: 1px solid rgba(255, 255, 255, 0.14);
                color: #ecf5ff;
                font-size: 11px;
                font-weight: 700;
            }}
            QPushButton#chipFiltroUsuario:hover {{
                background: rgba(255, 255, 255, 0.12);
            }}
            QPushButton#chipFiltroUsuario:checked {{
                color: #0f2d43;
                background: #d2f4f2;
                border-color: rgba(255, 255, 255, 0.18);
            }}
            QLabel#badgeRolUsuario,
            QLabel#badgeEstadoUsuario,
            QLabel#badgeRolSistemaUsuario {{
                border-radius: 11px;
                padding: 6px 10px;
                font-size: 11px;
                font-weight: 800;
            }}
            QLabel#badgeRolUsuario {{
                color: #d7e4ff;
                background: rgba(86, 124, 255, 0.16);
                border: 1px solid rgba(157, 178, 255, 0.24);
            }}
            QLabel#badgeRolUsuario[administrador="true"],
            QLabel#badgeRolSistemaUsuario[sistema="true"] {{
                color: #f5e1ff;
                background: rgba(146, 101, 255, 0.16);
                border: 1px solid rgba(207, 181, 255, 0.24);
            }}
            QLabel#badgeEstadoUsuario {{
                color: #f4f8fb;
                background: rgba(132, 146, 166, 0.22);
                border: 1px solid rgba(255, 255, 255, 0.12);
            }}
            QLabel#badgeEstadoUsuario[activo="true"] {{
                color: #d9fff5;
                background: rgba(16, 120, 98, 0.22);
                border-color: rgba(158, 231, 214, 0.26);
            }}
            QLabel#badgeRolSistemaUsuario {{
                color: #d9fff5;
                background: rgba(16, 120, 98, 0.18);
                border: 1px solid rgba(158, 231, 214, 0.22);
            }}
            QLabel#chipModuloRolUsuario,
            QLabel#chipModuloRolUsuarioSecundario {{
                border-radius: 9px;
                padding: 5px 9px;
                font-size: 11px;
                font-weight: 700;
            }}
            QLabel#chipModuloRolUsuario {{
                color: #d7f5ff;
                background: rgba(44, 177, 212, 0.14);
                border: 1px solid rgba(122, 226, 255, 0.18);
            }}
            QLabel#chipModuloRolUsuarioSecundario {{
                color: rgba(235, 242, 248, 0.82);
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.12);
            }}
            QLabel#tituloModuloPermisoRolUsuario {{
                color: rgba(235, 242, 248, 0.82);
                font-size: 11px;
                font-weight: 800;
                min-width: 140px;
            }}
            QLabel#detallePermisoRolUsuario {{
                color: rgba(235, 242, 248, 0.72);
                font-size: 11px;
                font-weight: 700;
            }}
            QLabel#badgeAccionPermisoRolUsuario {{
                border-radius: 9px;
                padding: 4px 8px;
                font-size: 10px;
                font-weight: 800;
                color: #d7f5ff;
                background: rgba(44, 177, 212, 0.14);
                border: 1px solid rgba(122, 226, 255, 0.18);
            }}
            QFrame#separadorRolUsuario {{
                background: rgba(255, 255, 255, 0.10);
                border: none;
            }}
            QWidget#contenedorAccionesUsuario {{
                background: transparent;
            }}
            QToolButton#botonIconoFilaUsuario {{
                background: transparent;
                border: none;
                border-radius: 8px;
                padding: 0px;
                margin: 0px;
            }}
            QToolButton#botonIconoFilaUsuario:hover {{
                background: transparent;
                border: none;
            }}
            QLabel#estadoVacioUsuarios {{
                color: rgba(235, 242, 248, 0.76);
                font-size: 12px;
                font-weight: 700;
                padding: 20px 14px;
            }}
            QLabel#bloqueInfoRolUsuario {{
                color: #dce9ff;
                font-size: 12px;
                font-weight: 600;
                padding: 12px 14px;
                border-radius: 12px;
                background: rgba(79, 163, 255, 0.12);
                border: 1px solid rgba(138, 194, 255, 0.20);
            }}
            QTabWidget#tabsUsuarios {{
                background: transparent;
            }}
            QTabWidget#tabsUsuarios QWidget {{
                background: transparent;
            }}
            QTabWidget#tabsUsuarios::pane {{
                border: 1px solid rgba(255, 255, 255, 0.10);
                border-radius: 18px;
                background: rgba(255, 255, 255, 0.05);
                margin-top: 12px;
                padding: 10px 10px 12px 10px;
            }}
            QScrollArea#scrollRolesUsuarios {{
                background: transparent;
                border: none;
            }}
            QScrollArea#scrollRolesUsuarios > QWidget > QWidget {{
                background: transparent;
            }}
            QTabWidget#tabsUsuarios QTabBar {{
                background: rgba(255, 255, 255, 0.04);
                border: 1px solid rgba(255, 255, 255, 0.10);
                border-radius: 16px;
                padding: 6px;
            }}
            QTabWidget#tabsUsuarios QTabBar::tab {{
                color: rgba(235, 242, 248, 0.74);
                padding: 10px 18px;
                margin-right: 6px;
                border: 1px solid transparent;
                border-radius: 12px;
                font-size: 13px;
                font-weight: 800;
                background: rgba(255, 255, 255, 0.05);
            }}
            QTabWidget#tabsUsuarios QTabBar::tab:hover {{
                background: rgba(255, 255, 255, 0.10);
                color: #ffffff;
            }}
            QTabWidget#tabsUsuarios QTabBar::tab:selected {{
                color: #0f2d43;
                background: #d2f4f2;
                border-color: rgba(109, 241, 220, 0.26);
            }}
            QLabel {{
                color: #f4fbff;
            }}
            """
        )
        if self._tema_actual == "claro":
            self.setStyleSheet(
                self.styleSheet()
                + f"""
                QLabel#tituloModulo,
                QLabel#subtituloModuloUsuarios,
                QLabel#tituloPanelPermisosUsuarios,
                QLabel#tituloRolUsuario,
                QLabel#valorMiniTarjetaRolUsuario,
                QLabel#valorTarjetaResumenUsuario,
                QLabel#tituloMiniTarjetaRolUsuario,
                QLabel#nombreUsuarioDetalle,
                QLabel#tituloTabRolesUsuarios,
                QLabel#estadoResumenRolesUsuarios {{
                    color: {paleta["texto_principal"]};
                }}
                QLabel#descripcionModulo,
                QLabel#detalleTarjetaResumenUsuario,
                QLabel#textoPanelPermisosUsuarios,
                QLabel#detalleRolesUsuarios,
                QLabel#notaRolesUsuarios,
                QLabel#descripcionRolUsuario,
                QLabel#tituloTarjetaResumenUsuario,
                QLabel#chipModuloRolUsuarioSecundario,
                QLabel#estadoVacioUsuarios {{
                    color: {paleta["texto_secundario"]};
                }}
                QLabel#mensajeUsuarios {{
                    color: {paleta["texto_exito"]};
                    background-color: {paleta["fondo_exito"]};
                    border-color: {paleta["borde_exito"]};
                }}
                QLabel#mensajeUsuarios[error="true"] {{
                    color: {paleta["texto_error"]};
                    background-color: {paleta["fondo_error"]};
                    border-color: {paleta["borde_error"]};
                }}
                QFrame#panelOperativoUsuarios,
                QFrame#tarjetaResumenUsuarios,
                QFrame#panelTablaUsuarios,
                QFrame#tarjetaRolUsuario,
                QFrame#miniTarjetaRolUsuario,
                QTabWidget#tabsUsuarios::pane {{
                    background: {paleta["fondo_superficie_suave"]};
                    border-color: {paleta["borde_suave"]};
                }}
                QFrame#panelPermisosUsuarios {{
                    background: {paleta["fondo_superficie"]};
                    border-color: {paleta["borde_principal"]};
                }}
                QTableWidget#tablaUsuarios {{
                    background: {paleta["fondo_tabla_cuerpo"]};
                    color: {paleta["texto_input"]};
                }}
                QTableWidget#tablaUsuarios QHeaderView::section {{
                    background: {paleta["fondo_tabla_header_destacado"]};
                    color: {paleta["texto_input"]};
                    border-right: 1px solid {paleta["borde_tabla"]};
                    border-bottom: 1px solid {paleta["borde_tabla"]};
                }}
                QTableWidget#tablaUsuarios::item {{
                    border-bottom: 1px solid {paleta["borde_tabla"]};
                    background: {paleta["fondo_tabla_fila"]};
                }}
                QLabel#iconoTarjetaResumenUsuario,
                QLabel#iconoPanelPermisosUsuarios,
                QLabel#iconoDatoRolUsuario {{
                    background: {paleta["fondo_superficie_muy_suave"]};
                    border: 1px solid {paleta["borde_suave"]};
                }}
                QLineEdit,
                QComboBox,
                QPlainTextEdit {{
                    border-color: {paleta["borde_medio"]};
                    background: {paleta["fondo_input"]};
                    color: {paleta["texto_input"]};
                }}
                QLineEdit:focus,
                QComboBox:focus,
                QPlainTextEdit:focus {{
                    border-color: {paleta["borde_foco_input"]};
                    background: {paleta["fondo_input_focus"]};
                }}
                QComboBox::drop-down {{
                    background: {paleta["fondo_superficie_muy_suave"]};
                }}
                QComboBox QAbstractItemView {{
                    background: {paleta["fondo_dialogo"]};
                    color: {paleta["texto_input"]};
                    border: 1px solid {paleta["borde_suave"]};
                    selection-background-color: {paleta["acento_seleccion"]};
                    selection-color: {paleta["texto_principal"]};
                }}
                QPushButton#chipFiltroUsuario {{
                    background: {paleta["fondo_chip"]};
                    border-color: {paleta["borde_suave"]};
                    color: {paleta["texto_chip"]};
                }}
                QPushButton#chipFiltroUsuario:hover {{
                    background: {paleta["fondo_chip_hover"]};
                }}
                QPushButton#chipFiltroUsuario:checked,
                QTabWidget#tabsUsuarios QTabBar::tab:selected {{
                    color: {paleta["texto_chip_activo"]};
                    background: {paleta["fondo_chip_activo"]};
                    border-color: {paleta["borde_chip_activo"]};
                }}
                QTabWidget#tabsUsuarios QTabBar {{
                    background: {paleta["fondo_superficie_muy_suave"]};
                    border-color: {paleta["borde_suave"]};
                }}
                QTabWidget#tabsUsuarios QTabBar::tab {{
                    color: {paleta["texto_secundario"]};
                    background: {paleta["fondo_panel_accion"]};
                }}
                QTabWidget#tabsUsuarios QTabBar::tab:hover {{
                    background: {paleta["fondo_superficie"]};
                    color: {paleta["texto_principal"]};
                }}
                QLabel#badgeEstadoUsuario {{
                    color: {paleta["texto_badge"]};
                    background: {paleta["fondo_badge"]};
                    border-color: {paleta["borde_suave"]};
                }}
                QLabel#badgeEstadoUsuario[activo="true"],
                QLabel#badgeRolSistemaUsuario {{
                    color: {paleta["texto_exito"]};
                    background: {paleta["fondo_exito"]};
                    border-color: {paleta["borde_exito"]};
                }}
                QLabel#badgeRolUsuario {{
                    color: {paleta["texto_badge_activo"]};
                    background: {paleta["fondo_badge_activo"]};
                    border-color: {paleta["borde_badge_activo"]};
                }}
                QLabel#badgeRolUsuario[administrador="true"],
                QLabel#badgeRolSistemaUsuario[sistema="true"] {{
                    color: {paleta["texto_chip_activo"]};
                    background: {paleta["fondo_chip_activo"]};
                    border-color: {paleta["borde_chip_activo"]};
                }}
                QLabel#chipModuloRolUsuario {{
                    color: {paleta["texto_badge_activo"]};
                    background: {paleta["fondo_badge_activo"]};
                    border-color: {paleta["borde_badge_activo"]};
                }}
                QLabel#bloqueInfoRolUsuario {{
                    color: {paleta["texto_principal"]};
                    background: {paleta["fondo_superficie_muy_suave"]};
                    border-color: {paleta["borde_principal"]};
                }}
                QLabel {{
                    color: {paleta["texto_principal"]};
                }}
                """
            )
