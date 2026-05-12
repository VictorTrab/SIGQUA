"""Vista PySide6 del modulo de usuarios."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QSizePolicy,
    QTableWidget,
    QVBoxLayout,
    QWidget,
)

from comun.ui import (
    aplicar_estilo_boton_operativo,
    configurar_tabla_operativa,
    crear_boton_operativo,
    crear_item_tabla,
)
from comun.ui.temas import TEMA_SICAP_PREDETERMINADO, obtener_paleta_tema
from modulos.usuarios.entidades import UsuarioSistema


class VistaUsuarios(QWidget):
    """Pantalla operativa para gestion administrativa de usuarios."""

    recargar_solicitado = Signal()
    restablecer_solicitado = Signal(str, str, str)
    desbloquear_solicitado = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._tema_actual = TEMA_SICAP_PREDETERMINADO
        self._paleta_tema = obtener_paleta_tema(self._tema_actual)
        self._usuario_seleccionado: UsuarioSistema | None = None
        self._construir_ui()
        self._aplicar_estilos()

    def aplicar_tema(self, nombre_tema: str) -> None:
        self._tema_actual = nombre_tema if nombre_tema in ("oscuro", "claro") else TEMA_SICAP_PREDETERMINADO
        self._paleta_tema = obtener_paleta_tema(self._tema_actual)
        self._aplicar_estilos()
        aplicar_estilo_boton_operativo(self._boton_recargar, principal=False)
        aplicar_estilo_boton_operativo(self._boton_restablecer, principal=True)
        aplicar_estilo_boton_operativo(self._boton_desbloquear, principal=False)

    def mostrar_usuarios(self, usuarios: list[UsuarioSistema]) -> None:
        """Renderiza el listado visible para el actor autenticado."""
        self._tabla.setRowCount(0)
        for usuario in usuarios:
            fila = self._tabla.rowCount()
            self._tabla.insertRow(fila)
            self._tabla.setItem(fila, 0, crear_item_tabla(usuario.nombre_usuario))
            self._tabla.setItem(fila, 1, crear_item_tabla(usuario.nombre_completo))
            self._tabla.setItem(fila, 2, crear_item_tabla(", ".join(usuario.roles) or "Sin rol"))
            self._tabla.setItem(fila, 3, crear_item_tabla(usuario.estado))
            self._tabla.setItem(
                fila,
                4,
                crear_item_tabla("Si" if usuario.requiere_cambio_contrasena else "No"),
            )
            self._tabla.item(fila, 0).setData(Qt.ItemDataRole.UserRole, usuario)

        self._tabla.resizeRowsToContents()
        if usuarios:
            self._tabla.selectRow(0)
            self._seleccionar_fila(0)
        else:
            self._limpiar_seleccion()
            self.mostrar_mensaje("No hay usuarios visibles para este perfil.", es_exito=True)

    def mostrar_mensaje(self, mensaje: str, es_exito: bool) -> None:
        self._mensaje.setText(mensaje)
        self._mensaje.setProperty("estado", "exito" if es_exito else "error")
        self._mensaje.style().unpolish(self._mensaje)
        self._mensaje.style().polish(self._mensaje)

    def _construir_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 10)
        layout.setSpacing(16)

        encabezado = QHBoxLayout()
        encabezado.setSpacing(12)
        bloque_titulo = QVBoxLayout()
        bloque_titulo.setSpacing(4)
        titulo = QLabel("Usuarios")
        titulo.setObjectName("tituloModulo")
        descripcion = QLabel(
            "Gestiona usuarios operativos, desbloqueos y restablecimientos administrativos."
        )
        descripcion.setObjectName("descripcionModulo")
        descripcion.setWordWrap(True)
        bloque_titulo.addWidget(titulo)
        bloque_titulo.addWidget(descripcion)

        self._boton_recargar = crear_boton_operativo("Actualizar")
        self._boton_recargar.clicked.connect(self.recargar_solicitado.emit)
        encabezado.addLayout(bloque_titulo, stretch=1)
        encabezado.addWidget(self._boton_recargar, alignment=Qt.AlignmentFlag.AlignTop)
        layout.addLayout(encabezado)

        contenido = QHBoxLayout()
        contenido.setSpacing(16)

        panel_tabla = QFrame()
        panel_tabla.setObjectName("panelOperativo")
        panel_tabla_layout = QVBoxLayout(panel_tabla)
        panel_tabla_layout.setContentsMargins(18, 18, 18, 18)
        panel_tabla_layout.setSpacing(10)

        self._tabla = QTableWidget(0, 5)
        configurar_tabla_operativa(
            self._tabla,
            ("Usuario", "Nombre", "Roles", "Estado", "Cambio obligatorio"),
        )
        self._tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self._tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._tabla.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self._tabla.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self._tabla.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self._tabla.cellClicked.connect(lambda fila, _columna: self._seleccionar_fila(fila))
        panel_tabla_layout.addWidget(self._tabla)

        panel_acciones = QFrame()
        panel_acciones.setObjectName("panelOperativo")
        panel_acciones.setMinimumWidth(284)
        panel_acciones.setMaximumWidth(332)
        panel_acciones.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        acciones_layout = QVBoxLayout(panel_acciones)
        acciones_layout.setContentsMargins(20, 20, 20, 20)
        acciones_layout.setSpacing(10)

        self._usuario_actual = QLabel("Selecciona un usuario")
        self._usuario_actual.setObjectName("subtituloPanel")
        self._detalle_usuario = QLabel("Las acciones disponibles respetan la visibilidad por perfil.")
        self._detalle_usuario.setWordWrap(True)
        self._detalle_usuario.setObjectName("textoSecundario")

        self._campo_contrasena = QLineEdit()
        self._campo_contrasena.setEchoMode(QLineEdit.EchoMode.Password)
        self._campo_contrasena.setPlaceholderText("Contrasena temporal")
        self._campo_confirmacion = QLineEdit()
        self._campo_confirmacion.setEchoMode(QLineEdit.EchoMode.Password)
        self._campo_confirmacion.setPlaceholderText("Confirmar contrasena")

        self._boton_restablecer = crear_boton_operativo("Restablecer contrasena", principal=True)
        self._boton_desbloquear = crear_boton_operativo("Desbloquear usuario")
        self._boton_restablecer.clicked.connect(self._emitir_restablecimiento)
        self._boton_desbloquear.clicked.connect(self._emitir_desbloqueo)

        self._mensaje = QLabel("")
        self._mensaje.setObjectName("mensajeModulo")
        self._mensaje.setWordWrap(True)

        acciones_layout.addWidget(self._usuario_actual)
        acciones_layout.addWidget(self._detalle_usuario)
        acciones_layout.addSpacing(4)
        acciones_layout.addWidget(QLabel("Nueva contrasena temporal"))
        acciones_layout.addWidget(self._campo_contrasena)
        acciones_layout.addWidget(QLabel("Confirmar contrasena"))
        acciones_layout.addWidget(self._campo_confirmacion)
        acciones_layout.addWidget(self._boton_restablecer)
        acciones_layout.addWidget(self._boton_desbloquear)
        acciones_layout.addWidget(self._mensaje)
        acciones_layout.addStretch(1)

        contenido.addWidget(panel_tabla, stretch=1)
        contenido.addWidget(panel_acciones)
        layout.addLayout(contenido, stretch=1)

    def _seleccionar_fila(self, fila: int) -> None:
        item = self._tabla.item(fila, 0)
        if item is None:
            self._limpiar_seleccion()
            return

        usuario = item.data(Qt.ItemDataRole.UserRole)
        if not isinstance(usuario, UsuarioSistema):
            self._limpiar_seleccion()
            return

        self._usuario_seleccionado = usuario
        self._usuario_actual.setText(usuario.nombre_usuario)
        perfil = ", ".join(usuario.roles) or "Sin rol asignado"
        detalle = f"{usuario.nombre_completo}\nPerfil: {perfil}\nEstado: {usuario.estado}"
        if usuario.requiere_cambio_contrasena:
            detalle += "\nCambio obligatorio pendiente."
        self._detalle_usuario.setText(detalle)
        self._campo_contrasena.clear()
        self._campo_confirmacion.clear()
        self._mensaje.clear()

    def _limpiar_seleccion(self) -> None:
        self._usuario_seleccionado = None
        self._usuario_actual.setText("Selecciona un usuario")
        self._detalle_usuario.setText("No hay un usuario seleccionado.")

    def _emitir_restablecimiento(self) -> None:
        if self._usuario_seleccionado is None:
            self.mostrar_mensaje("Selecciona un usuario para continuar.", es_exito=False)
            return
        self.restablecer_solicitado.emit(
            self._usuario_seleccionado.nombre_usuario,
            self._campo_contrasena.text(),
            self._campo_confirmacion.text(),
        )

    def _emitir_desbloqueo(self) -> None:
        if self._usuario_seleccionado is None:
            self.mostrar_mensaje("Selecciona un usuario para continuar.", es_exito=False)
            return
        self.desbloquear_solicitado.emit(self._usuario_seleccionado.nombre_usuario)

    def _aplicar_estilos(self) -> None:
        self.setStyleSheet(
            """
            #tituloModulo {
                color: #ffffff;
                font-size: 23px;
                font-weight: 800;
            }
            #descripcionModulo,
            #textoSecundario {
                color: rgba(235, 242, 248, 0.74);
                font-size: 13px;
            }
            #panelOperativo {
                background: rgba(255, 255, 255, 0.10);
                border: 1px solid rgba(255, 255, 255, 0.16);
                border-radius: 22px;
            }
            #subtituloPanel {
                color: #ffffff;
                font-size: 17px;
                font-weight: 800;
            }
            QLineEdit {
                min-height: 40px;
                border-radius: 14px;
                border: 1px solid rgba(255, 255, 255, 0.18);
                padding: 0 12px;
                background: rgba(255, 255, 255, 0.11);
                color: #f7fbff;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid rgba(109, 241, 220, 0.42);
                background: rgba(255, 255, 255, 0.16);
            }
            QLabel {
                color: #f4fbff;
                font-size: 13px;
            }
            #mensajeModulo {
                padding: 10px 12px;
                border-radius: 14px;
                background: transparent;
            }
            #mensajeModulo[estado="exito"] {
                color: #d9fff5;
                background: rgba(16, 120, 98, 0.16);
                border: 1px solid rgba(158, 231, 214, 0.26);
            }
            #mensajeModulo[estado="error"] {
                color: #ffd4cf;
                background: rgba(180, 35, 24, 0.15);
                border: 1px solid rgba(255, 205, 199, 0.28);
            }
            """
        )
        if self._tema_actual == "claro":
            paleta = self._paleta_tema
            self.setStyleSheet(
                self.styleSheet()
                + f"""
                #tituloModulo,
                #subtituloPanel {{
                    color: {paleta["texto_principal"]};
                }}
                #descripcionModulo,
                #textoSecundario,
                QLabel {{
                    color: {paleta["texto_secundario"]};
                }}
                #panelOperativo {{
                    background: {paleta["fondo_superficie"]};
                    border: 1px solid {paleta["borde_principal"]};
                }}
                QLineEdit {{
                    border: 1px solid {paleta["borde_medio"]};
                    background: {paleta["fondo_input"]};
                    color: {paleta["texto_input"]};
                }}
                QLineEdit:focus {{
                    border: 1px solid {paleta["borde_foco_input"]};
                    background: {paleta["fondo_input_focus"]};
                }}
                #mensajeModulo[estado="exito"] {{
                    color: {paleta["texto_exito"]};
                    background: {paleta["fondo_exito"]};
                    border: 1px solid {paleta["borde_exito"]};
                }}
                #mensajeModulo[estado="error"] {{
                    color: {paleta["texto_error"]};
                    background: {paleta["fondo_error"]};
                    border: 1px solid {paleta["borde_error"]};
                }}
                """
            )
