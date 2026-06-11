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
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from comun.ui import (
    BotonAccionContextual,
    CampoDetalleSigqua,
    ContenedorTarjetasResumenOperativo,
    DialogoBaseSigqua,
    DialogoConfirmacionSigqua,
    EncabezadoDetalleSigqua,
    SeccionDetalleSigqua,
    TarjetaResumenOperativa,
    aplicar_estilo_boton_operativo,
    configurar_tabla_operativa,
    crear_badge_estado_detalle_sigqua,
    crear_boton_operativo,
    crear_item_tabla,
    obtener_estilo_detalle_sigqua,
    obtener_icono_tabler_coloreado,
)
from comun.ui.temas import (
    TEMA_SIGQUA_PREDETERMINADO,
    obtener_fondo_header_destacado,
    obtener_paleta_tema,
    resolver_nombre_tema,
)
from modulos.usuarios.entidades import (
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


class TarjetaResumenUsuario(TarjetaResumenOperativa):
    """Adaptador del resumen comun para mantener nombres del modulo."""


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


class DialogoFormularioUsuario(DialogoBaseSigqua):
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
        self.setMinimumWidth(700)
        self._construir_ui()
        self.resize(700, 520)

    def obtener_formulario(self) -> FormularioUsuario:
        return FormularioUsuario(
            identificador=None if self._usuario is None else self._usuario.identificador,
            nombre_usuario=self._campo_usuario.text().strip(),
            nombre_completo=self._campo_nombre.text().strip(),
            correo=self._campo_correo.text().strip(),
            estado=self._combo_estado.currentData() or self._combo_estado.currentText(),
            rol_id=int(self._combo_rol.currentData() or 0),
            observaciones=self._campo_observaciones.toPlainText().strip(),
            contrasena=self._campo_contrasena.text(),
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
        if self._usuario is None and not formulario.contrasena:
            self._mostrar_error("Define la contrasena inicial del usuario.")
            return
        if self._usuario is None and formulario.contrasena != formulario.confirmacion_contrasena:
            self._mostrar_error("Las contrasenas no coinciden.")
            return
        self._mensaje.setVisible(False)
        super().accept()

    def _construir_ui(self) -> None:
        titulo = QLabel("Editar usuario" if self._usuario else "Nuevo usuario")
        titulo.setObjectName("tituloDialogoSigqua")
        descripcion = QLabel(
            "Configura la identidad del usuario, su rol visible y el estado operativo."
        )
        descripcion.setObjectName("descripcionDialogoSigqua")
        descripcion.setWordWrap(True)

        panel_datos = self._crear_panel("Datos principales", "Información base de la cuenta operativa.")
        grid_datos = QGridLayout()
        grid_datos.setHorizontalSpacing(12)
        grid_datos.setVerticalSpacing(12)

        self._campo_nombre = QLineEdit()
        self._campo_nombre.setPlaceholderText("Nombre completo")
        self._campo_usuario = QLineEdit()
        self._campo_usuario.setPlaceholderText("Nombre de usuario")
        self._campo_correo = QLineEdit()
        self._campo_correo.setPlaceholderText("usuario@sigqua.hn")
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
            "Asigna un unico rol visible y define la contrasena inicial.",
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

        grid_seguridad.addWidget(self._crear_bloque("Rol", self._combo_rol), 0, 0, 1, 2)
        self._campo_contrasena = QLineEdit()
        self._campo_contrasena.setEchoMode(QLineEdit.EchoMode.Password)
        self._campo_contrasena.setPlaceholderText("Minimo 8 caracteres")
        self._campo_confirmacion = QLineEdit()
        self._campo_confirmacion.setEchoMode(QLineEdit.EchoMode.Password)
        self._campo_confirmacion.setPlaceholderText("Repite la contrasena")
        if self._usuario is None:
            grid_seguridad.addWidget(
                self._crear_bloque("Contrasena inicial", self._campo_contrasena),
                1,
                0,
            )
            grid_seguridad.addWidget(
                self._crear_bloque("Confirmar contrasena", self._campo_confirmacion),
                1,
                1,
            )
        panel_seguridad.layout().addLayout(grid_seguridad)
        ayuda = QLabel(
            "La contrasena se almacena protegida mediante scrypt."
            if self._usuario is None
            else "Para cambiar la contrasena usa la accion de gestion de acceso."
        )
        ayuda.setObjectName("descripcionDialogoSigqua")
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
        self._campo_observaciones.setFixedHeight(72)
        panel_observaciones.layout().addWidget(self._campo_observaciones)

        self._mensaje = QLabel("")
        self._mensaje.setObjectName("mensajeErrorDialogoSigqua")
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
        fila_paneles = QHBoxLayout()
        fila_paneles.setSpacing(10)
        fila_paneles.addWidget(panel_datos, 1)
        fila_paneles.addWidget(panel_seguridad, 1)

        self.layout_cuerpo.addLayout(fila_paneles)
        self.layout_cuerpo.addWidget(panel_observaciones)
        self.layout_cuerpo.addWidget(self._mensaje)
        self.layout_pie.addLayout(fila_acciones)
        self._actualizar_resumen_rol()

    def _crear_panel(self, titulo: str, descripcion: str) -> QFrame:
        panel = QFrame()
        panel.setObjectName("bloqueDialogoSigqua")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)
        label_titulo = QLabel(titulo)
        label_titulo.setObjectName("etiquetaDatoDialogoSigqua")
        label_descripcion = QLabel(descripcion)
        label_descripcion.setObjectName("descripcionDialogoSigqua")
        label_descripcion.setWordWrap(True)
        layout.addWidget(label_titulo)
        layout.addWidget(label_descripcion)
        return panel

    def _crear_bloque(self, etiqueta: str, widget: QWidget) -> QWidget:
        bloque = QWidget()
        layout = QVBoxLayout(bloque)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)
        label = QLabel(etiqueta)
        label.setObjectName("etiquetaDatoDialogoSigqua")
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


class DialogoDetalleUsuario(DialogoBaseSigqua):
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
        self.setMinimumWidth(660)
        self._construir_ui()
        self.resize(660, 500)

    @property
    def accion_resultado(self) -> str:
        return self._accion_resultado

    def _construir_ui(self) -> None:
        titulo = QLabel("Detalle de usuario")
        titulo.setObjectName("tituloDialogoSigqua")
        descripcion = QLabel(
            "Consulta identidad, rol operativo, actividad reciente y estado de seguridad."
        )
        descripcion.setObjectName("descripcionDialogoSigqua")
        descripcion.setWordWrap(True)

        contenedor = QWidget()
        layout_scroll = QVBoxLayout(contenedor)
        layout_scroll.setContentsMargins(0, 0, 0, 0)
        layout_scroll.setSpacing(12)

        panel = QFrame()
        panel.setObjectName("panelDetalleSigqua")
        layout_panel = QVBoxLayout(panel)
        layout_panel.setContentsMargins(16, 16, 16, 16)
        layout_panel.setSpacing(12)

        encabezado = EncabezadoDetalleSigqua(
            self._usuario.nombre_usuario,
            self._usuario.nombre_completo,
            badges=(
                crear_badge_estado_detalle_sigqua(
                    self._usuario.estado.title(),
                    "activo" if self._usuario.estado == "ACTIVO" else "info",
                ),
            ),
        )

        grid_identidad = QGridLayout()
        grid_identidad.setHorizontalSpacing(14)
        grid_identidad.setVerticalSpacing(14)
        grid_identidad.addWidget(CampoDetalleSigqua("Correo", self._usuario.correo), 0, 0)
        grid_identidad.addWidget(CampoDetalleSigqua("Rol visible", self._usuario.rol_principal), 0, 1)
        grid_identidad.addWidget(CampoDetalleSigqua("Estado", self._usuario.estado.title()), 1, 0)
        grid_identidad.addWidget(
            CampoDetalleSigqua(
                "Cambio obligatorio",
                "Pendiente" if self._usuario.requiere_cambio_contrasena else "No",
            ),
            1,
            1,
        )

        grid_actividad = QGridLayout()
        grid_actividad.setHorizontalSpacing(14)
        grid_actividad.setVerticalSpacing(14)
        grid_actividad.addWidget(CampoDetalleSigqua("Ultimo acceso", self._formateador_fecha(self._usuario.ultimo_acceso_en)), 0, 0)
        grid_actividad.addWidget(CampoDetalleSigqua("Creado", self._formateador_fecha(self._usuario.creado_en)), 0, 1)
        grid_actividad.addWidget(CampoDetalleSigqua("Creado por", self._usuario.creado_por_nombre or "Sin registro"), 1, 0)
        grid_actividad.addWidget(CampoDetalleSigqua("Ultima actualizacion", self._formateador_fecha(self._usuario.actualizado_en)), 1, 1)
        grid_actividad.addWidget(CampoDetalleSigqua("Actualizado por", self._usuario.actualizado_por_nombre or "Sin registro"), 2, 0)
        grid_actividad.addWidget(CampoDetalleSigqua("Sesiones registradas", str(self._usuario.total_sesiones)), 2, 1)
        grid_actividad.addWidget(CampoDetalleSigqua("Intentos fallidos", str(self._usuario.intentos_fallidos)), 3, 0, 1, 2)

        observaciones = CampoDetalleSigqua(
            "Observaciones",
            self._usuario.observaciones or "Sin observaciones registradas.",
        )

        fila_acciones = QHBoxLayout()
        fila_acciones.setSpacing(10)
        boton_cerrar = BotonAccionContextual("Cerrar", icono="x.svg", variante="neutro", centrado=True, mostrar_icono=True)
        boton_editar = BotonAccionContextual("Editar", icono="edit.svg", variante="edicion", centrado=True, mostrar_icono=True)
        boton_cerrar.setMinimumWidth(124)
        boton_editar.setMinimumWidth(124)
        boton_cerrar.clicked.connect(self.reject)
        boton_editar.clicked.connect(self._solicitar_edicion)
        fila_acciones.addWidget(boton_cerrar)
        fila_acciones.addStretch(1)
        fila_acciones.addWidget(boton_editar)

        layout_panel.addWidget(encabezado)
        layout_panel.addWidget(SeccionDetalleSigqua("Identidad y acceso", "Datos visibles del usuario y rol asignado.", grid_identidad))
        layout_panel.addWidget(SeccionDetalleSigqua("Actividad reciente", "Indicadores operativos de acceso y seguridad.", grid_actividad))
        layout_panel.addWidget(SeccionDetalleSigqua("Observaciones", "Notas administrativas internas de la cuenta.", [observaciones]))
        layout_scroll.addWidget(panel)

        self.layout_cabecera.addWidget(titulo)
        self.layout_cabecera.addWidget(descripcion)
        self.layout_cuerpo.addWidget(self.crear_area_scroll_cuerpo(contenedor, "scrollDetalleUsuario"))
        self.layout_pie.addLayout(fila_acciones)
        self._aplicar_estilos()
        return

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
                "Última actualización",
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
            icono="x.svg",
            variante="neutro",
            centrado=True,
            mostrar_icono=True,
        )
        boton_editar = BotonAccionContextual(
            "Editar",
            icono="edit.svg",
            variante="edicion",
            centrado=True,
            mostrar_icono=True,
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
        layout_scroll.addWidget(panel)
        scroll.setWidget(contenedor)

        self.layout_cabecera.addWidget(titulo)
        self.layout_cabecera.addWidget(descripcion)
        self.layout_cuerpo.addWidget(scroll)
        self.layout_pie.addLayout(fila_acciones)
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
            """
            + obtener_estilo_detalle_sigqua(self._nombre_tema)
        )
        return

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
                background: rgba(13, 42, 69, 0.78);
                border: 1px solid rgba(126, 167, 196, 0.30);
                border-radius: 16px;
            }
            QLabel#codigoDetalleUsuario,
            QLabel#etiquetaDetalleUsuario,
            QLabel#descripcionSeccionDetalleUsuario {
                color: #C5DDEE;
            }
            QLabel#nombreDetalleUsuario,
            QLabel#tituloSeccionDetalleUsuario,
            QLabel#valorDetalleUsuario {
                color: #75C7F0;
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
                color: #C5DDEE;
                background: rgba(142, 168, 188, 0.22);
                border: 1px solid rgba(126, 167, 196, 0.30);
            }
            QLabel#badgeEstadoUsuarioDetalle[activo="true"] {
                color: #75C7F0;
                background: rgba(31, 79, 94, 0.96);
                border-color: rgba(117, 199, 240, 0.26);
            }
            """
        )


class DialogoGestionAccesoUsuario(DialogoBaseSigqua):
    """Modal para restablecer la contrasena o desbloquear una cuenta."""

    def __init__(self, usuario: UsuarioSistema, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._usuario = usuario
        self._resultado: str | None = None
        self.setMinimumWidth(500)
        self._construir_ui()
        self.resize(500, 280)

    def obtener_resultado(self) -> tuple[str, str, str] | None:
        if self._resultado is None:
            return None
        return (
            self._resultado,
            self._campo_contrasena.text(),
            self._campo_confirmacion.text(),
        )

    def _construir_ui(self) -> None:
        titulo = QLabel("Gestión de acceso")
        titulo.setObjectName("tituloDialogoSigqua")
        descripcion = QLabel(
            "Define una nueva contrasena o desbloquea la cuenta si quedo bloqueada."
        )
        descripcion.setObjectName("descripcionDialogoSigqua")
        descripcion.setWordWrap(True)

        panel = QFrame()
        panel.setObjectName("bloqueDialogoSigqua")
        layout_panel = QVBoxLayout(panel)
        layout_panel.setContentsMargins(14, 14, 14, 14)
        layout_panel.setSpacing(10)

        etiqueta_usuario = QLabel(
            f"<b>{self._usuario.nombre_usuario}</b><br>{self._usuario.nombre_completo}<br>{self._usuario.rol_principal}"
        )
        etiqueta_usuario.setObjectName("descripcionDialogoSigqua")
        etiqueta_usuario.setWordWrap(True)
        layout_panel.addWidget(etiqueta_usuario)

        contexto = []
        if self._usuario.requiere_cambio_contrasena:
            contexto.append("La cuenta ya tiene cambio obligatorio de contrasena pendiente.")
        if self._usuario.intentos_fallidos > 0 or self._usuario.estado == "BLOQUEADO":
            contexto.append(
                f"Intentos fallidos actuales: {self._usuario.intentos_fallidos}. Puedes desbloquear la cuenta."
            )
        else:
            contexto.append("La cuenta no esta bloqueada. Puedes restablecer su contrasena.")

        nota = QLabel(" ".join(contexto))
        nota.setObjectName("descripcionDialogoSigqua")
        nota.setWordWrap(True)
        layout_panel.addWidget(nota)
        self._campo_contrasena = QLineEdit()
        self._campo_contrasena.setEchoMode(QLineEdit.EchoMode.Password)
        self._campo_contrasena.setPlaceholderText("Minimo 8 caracteres")
        self._campo_confirmacion = QLineEdit()
        self._campo_confirmacion.setEchoMode(QLineEdit.EchoMode.Password)
        self._campo_confirmacion.setPlaceholderText("Repite la contrasena")
        layout_panel.addWidget(self._crear_bloque("Nueva contrasena", self._campo_contrasena))
        layout_panel.addWidget(
            self._crear_bloque("Confirmar contrasena", self._campo_confirmacion)
        )

        self._mensaje = QLabel("")
        self._mensaje.setObjectName("mensajeErrorDialogoSigqua")
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
        label.setObjectName("etiquetaDatoDialogoSigqua")
        layout.addWidget(label)
        layout.addWidget(widget)
        return bloque

    def _confirmar_restablecimiento(self) -> None:
        if len(self._campo_contrasena.text()) < 8:
            self._mostrar_error("La contrasena debe tener al menos 8 caracteres.")
            return
        if self._campo_contrasena.text() != self._campo_confirmacion.text():
            self._mostrar_error("Las contrasenas no coinciden.")
            return
        self._resultado = "restablecer"
        self.accept()

    def _confirmar_desbloqueo(self) -> None:
        self._resultado = "desbloquear"
        self.accept()

    def _mostrar_error(self, mensaje: str) -> None:
        self._mensaje.setText(mensaje)
        self._mensaje.setVisible(True)


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

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("vistaUsuarios")
        self._tema_actual = TEMA_SIGQUA_PREDETERMINADO
        self._paleta_tema = obtener_paleta_tema(self._tema_actual)
        self._roles_actuales: list[RolSistema] = []
        self._filtro_rol_actual = FILTRO_USUARIOS_TODOS
        self._temporizador_mensaje = QTimer(self)
        self._temporizador_mensaje.setSingleShot(True)
        self._temporizador_mensaje.timeout.connect(self._ocultar_mensaje)
        self._construir_ui()
        self._aplicar_estilos()

    def aplicar_tema(self, nombre_tema: str) -> None:
        self._tema_actual = resolver_nombre_tema(nombre_tema)
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
        _ = tuple(permisos_disponibles)
        self._actualizar_filtro_roles()

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

    def mostrar_detalle_usuario(
        self,
        usuario: UsuarioSistema,
        formateador_fecha: Callable[[str | None], str],
    ) -> str:
        dialogo = DialogoDetalleUsuario(usuario=usuario, formateador_fecha=formateador_fecha, parent=self)
        dialogo.exec()
        return dialogo.accion_resultado

    def solicitar_gestion_acceso(
        self,
        usuario: UsuarioSistema,
    ) -> tuple[str, str, str] | None:
        dialogo = DialogoGestionAccesoUsuario(usuario=usuario, parent=self)
        if dialogo.exec() != QDialog.DialogCode.Accepted:
            return None
        return dialogo.obtener_resultado()

    def confirmar_cambio_estado_usuario(self, usuario: UsuarioSistema) -> bool:
        accion = "desactivar" if usuario.estado == "ACTIVO" else "activar"
        dialogo = DialogoConfirmacionSigqua(
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
        layout.setContentsMargins(6, 4, 6, 6)
        layout.setSpacing(12)

        encabezado = QHBoxLayout()
        encabezado.setSpacing(12)

        fila_acciones = QHBoxLayout()
        fila_acciones.setSpacing(8)
        fila_acciones.addStretch(1)
        self._boton_exportar = crear_boton_operativo("Exportar")
        self._boton_nuevo = crear_boton_operativo("Nuevo usuario", principal=True)
        self._boton_exportar.clicked.connect(self.exportar_solicitado.emit)
        self._boton_nuevo.clicked.connect(self.nuevo_usuario_solicitado.emit)
        fila_acciones.addWidget(self._boton_exportar)
        fila_acciones.addWidget(self._boton_nuevo)

        encabezado.addStretch(1)
        encabezado.addLayout(fila_acciones)

        self._mensaje = QLabel("")
        self._mensaje.setObjectName("mensajeUsuarios")
        self._mensaje.setVisible(False)
        self._mensaje.setWordWrap(True)

        layout.addLayout(encabezado)
        layout.addWidget(self._mensaje)
        layout.addWidget(self._crear_pestana_usuarios(), 1)

    def _crear_pestana_usuarios(self) -> QWidget:
        pagina = QWidget()
        layout = QVBoxLayout(pagina)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        contenedor_tarjetas = ContenedorTarjetasResumenOperativo()
        self._tarjeta_total = TarjetaResumenUsuario("user.svg", "#75C7F0")
        self._tarjeta_activos = TarjetaResumenUsuario("circle-check.svg", "#37D399")
        self._tarjeta_admins = TarjetaResumenUsuario("key.svg", "#F5B84B")
        self._tarjeta_accesos = TarjetaResumenUsuario("clock.svg", "#92B6CC")
        contenedor_tarjetas.establecer_tarjetas(
            (self._tarjeta_total, self._tarjeta_activos, self._tarjeta_admins, self._tarjeta_accesos)
        )

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

        layout.addWidget(contenedor_tarjetas)
        layout.addWidget(panel_filtros)
        layout.addWidget(panel_tabla, 1)
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

        boton_detalle = BotonIconoFilaUsuario("eye.svg", "#75C7F0", "Ver informacion")
        boton_editar = BotonIconoFilaUsuario("user.svg", "#F5B84B", "Editar usuario")
        boton_estado = BotonIconoFilaUsuario(
            "lock.svg" if usuario.estado == "ACTIVO" else "circle-check.svg",
            "#37D399" if usuario.estado == "ACTIVO" else "#92B6CC",
            "Desactivar" if usuario.estado == "ACTIVO" else "Activar",
        )
        boton_seguridad = BotonIconoFilaUsuario("key.svg", "#A7B8FF", "Gestionar acceso")

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

        if usuario.es_tecnico or usuario.es_oculto:
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
                color: {paleta["texto_principal"]};
                font-size: 19px;
                font-weight: 900;
            }}
            QLabel#descripcionModulo,
            QLabel#detalleTarjetaResumenUsuario {{
                color: {paleta["texto_secundario"]};
                font-size: 11px;
            }}
            QLabel#mensajeUsuarios {{
                color: {paleta["texto_exito"]};
                font-size: 12px;
                font-weight: 700;
                padding: 8px 10px;
                border-radius: 12px;
                background-color: {paleta["fondo_exito"]};
                border: 1px solid {paleta["borde_exito"]};
            }}
            QLabel#mensajeUsuarios[error="true"] {{
                color: {paleta["texto_error"]};
                background-color: {paleta["fondo_error"]};
                border: 1px solid {paleta["borde_error"]};
            }}
            QFrame#panelOperativoUsuarios,
            QFrame#tarjetaResumenUsuarios {{
                background: {fondo_header_destacado};
                border: 1px solid {paleta["borde_principal"]};
                border-radius: 18px;
            }}
            QFrame#panelTablaUsuarios {{
                background: {fondo_header_destacado};
                border: 1px solid {paleta["borde_principal"]};
                border-radius: 18px;
            }}
            QTableWidget#tablaUsuarios {{
                background: {paleta["fondo_tabla_cuerpo"]};
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
                background: {paleta["fondo_tabla_header_destacado"]};
                color: {paleta["texto_principal"]};
                border: none;
                border-right: 1px solid {paleta["borde_suave"]};
                border-bottom: 1px solid {paleta["borde_suave"]};
                padding: 10px 12px;
                font-size: 12px;
                font-weight: 800;
            }}
            QTableWidget#tablaUsuarios QHeaderView::section:last {{
                border-top-right-radius: 18px;
            }}
            QTableWidget#tablaUsuarios::item {{
                padding: 9px 12px;
                border-bottom: 1px solid {paleta["borde_suave"]};
                background: {paleta["fondo_tabla_fila"]};
            }}
            QTableWidget#tablaUsuarios::item:alternate {{
                background: {paleta["fondo_tabla_fila_alterna"]};
            }}
            QTableWidget#tablaUsuarios::item:selected {{
                background: {paleta["fondo_tabla_seleccion"]};
            }}
            QLabel#iconoTarjetaResumenUsuario {{
                background: {paleta["fondo_superficie_suave"]};
                border: 1px solid {paleta["borde_suave"]};
                border-radius: 12px;
            }}
            QLabel#tituloTarjetaResumenUsuario {{
                color: {paleta["texto_secundario"]};
                font-size: 11px;
                font-weight: 700;
            }}
            QLabel#valorTarjetaResumenUsuario {{
                color: {paleta["texto_principal"]};
                font-size: 20px;
                font-weight: 900;
            }}
            QLineEdit,
            QComboBox,
            QPlainTextEdit {{
                min-height: 36px;
                border: 1px solid {paleta["borde_medio"]};
                border-radius: 12px;
                background: {paleta["fondo_input"]};
                color: {paleta["texto_input"]};
                padding: 0 10px;
                font-size: 12px;
            }}
            QPlainTextEdit {{
                min-height: 72px;
                padding: 10px;
            }}
            QLineEdit:focus,
            QComboBox:focus,
            QPlainTextEdit:focus {{
                border-color: {paleta["borde_foco_input"]};
                background: {paleta["fondo_input_focus"]};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 24px;
                background: {paleta["fondo_chip"]};
                border-top-right-radius: 12px;
                border-bottom-right-radius: 12px;
            }}
            QComboBox QAbstractItemView {{
                background: {paleta["fondo_input"]};
                color: {paleta["texto_input"]};
                border: 1px solid {paleta["borde_suave"]};
                selection-background-color: {paleta["acento_seleccion"]};
                selection-color: {paleta["texto_principal"]};
                padding: 6px;
            }}
            QPushButton#chipFiltroUsuario {{
                min-height: 30px;
                border-radius: 11px;
                padding: 0 12px;
                background: {paleta["fondo_chip"]};
                border: 1px solid {paleta["borde_suave"]};
                color: {paleta["texto_chip"]};
                font-size: 11px;
                font-weight: 700;
            }}
            QPushButton#chipFiltroUsuario:hover {{
                background: {paleta["fondo_chip_hover"]};
            }}
            QPushButton#chipFiltroUsuario:checked {{
                color: {paleta["texto_chip_activo"]};
                background: {paleta["fondo_chip_activo"]};
                border-color: {paleta["borde_chip_activo"]};
            }}
            QLabel#badgeRolUsuario,
            QLabel#badgeEstadoUsuario {{
                border-radius: 11px;
                padding: 6px 10px;
                font-size: 11px;
                font-weight: 800;
            }}
            QLabel#badgeRolUsuario {{
                color: {paleta["texto_badge"]};
                background: {paleta["fondo_badge"]};
                border: 1px solid {paleta["borde_suave"]};
            }}
            QLabel#badgeRolUsuario[administrador="true"] {{
                color: {paleta["texto_principal"]};
                background: {paleta["fondo_chip_activo"]};
                border: 1px solid {paleta["borde_chip_activo"]};
            }}
            QLabel#badgeEstadoUsuario {{
                color: {paleta["texto_badge"]};
                background: {paleta["fondo_badge"]};
                border: 1px solid {paleta["borde_suave"]};
            }}
            QLabel#badgeEstadoUsuario[activo="true"] {{
                color: {paleta["texto_principal"]};
                background: {paleta["fondo_badge_activo"]};
                border-color: {paleta["borde_badge_activo"]};
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
                color: {paleta["texto_secundario"]};
                font-size: 12px;
                font-weight: 700;
                padding: 20px 14px;
            }}
            QLabel#bloqueInfoRolUsuario {{
                color: {paleta["texto_secundario"]};
                font-size: 12px;
                font-weight: 600;
                padding: 12px 14px;
                border-radius: 12px;
                background: {paleta["fondo_panel_accion"]};
                border: 1px solid {paleta["borde_principal"]};
            }}
            QLabel {{
                color: {paleta["texto_principal"]};
            }}
            """
        )

