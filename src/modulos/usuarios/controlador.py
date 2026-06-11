"""Controlador del modulo de usuarios."""

from __future__ import annotations

from modulos.autenticacion.entidades import UsuarioAutenticado
from modulos.usuarios.entidades import RolSistema, UsuarioSistema
from modulos.usuarios.servicio import FILTRO_USUARIOS_TODOS, ServicioUsuarios
from modulos.usuarios.vista import VistaUsuarios


class ControladorUsuarios:
    """Conecta la vista con los servicios del modulo."""

    def __init__(self, servicio_usuarios: ServicioUsuarios, vista_usuarios: VistaUsuarios):
        self._servicio_usuarios = servicio_usuarios
        self._vista_usuarios = vista_usuarios
        self._actor: UsuarioAutenticado | None = None
        self._usuarios_actuales: list[UsuarioSistema] = []
        self._usuarios_filtrados: list[UsuarioSistema] = []
        self._roles_actuales: list[RolSistema] = []
        self._filtro_texto = ""
        self._filtro_rapido = FILTRO_USUARIOS_TODOS
        self._filtro_rol = FILTRO_USUARIOS_TODOS
        self._conectar_senales()

    def mostrar_para_actor(self, actor: UsuarioAutenticado) -> None:
        """Carga usuarios visibles para el usuario autenticado."""
        self._actor = actor
        self._filtro_texto = ""
        self._filtro_rapido = FILTRO_USUARIOS_TODOS
        self._filtro_rol = FILTRO_USUARIOS_TODOS
        self._refrescar()

    def _conectar_senales(self) -> None:
        self._vista_usuarios.filtro_texto_cambiado.connect(self._manejar_filtro_texto)
        self._vista_usuarios.filtro_rapido_cambiado.connect(self._manejar_filtro_rapido)
        self._vista_usuarios.filtro_rol_cambiado.connect(self._manejar_filtro_rol)
        self._vista_usuarios.exportar_solicitado.connect(self._exportar)
        self._vista_usuarios.nuevo_usuario_solicitado.connect(self._crear_usuario)
        self._vista_usuarios.detalle_usuario_solicitado.connect(self._mostrar_detalle)
        self._vista_usuarios.editar_usuario_solicitado.connect(self._editar_usuario)
        self._vista_usuarios.cambio_estado_solicitado.connect(self._cambiar_estado_usuario)
        self._vista_usuarios.gestion_acceso_solicitada.connect(self._gestionar_acceso_usuario)

    def _manejar_filtro_texto(self, texto: str) -> None:
        self._filtro_texto = texto.strip()
        self._renderizar_usuarios_filtrados()

    def _manejar_filtro_rapido(self, filtro_rapido: str) -> None:
        self._filtro_rapido = filtro_rapido
        self._renderizar_usuarios_filtrados()

    def _manejar_filtro_rol(self, rol: str) -> None:
        self._filtro_rol = rol
        self._renderizar_usuarios_filtrados()

    def _crear_usuario(self) -> None:
        if self._actor is None:
            self._mostrar_sin_sesion()
            return
        formulario = self._vista_usuarios.solicitar_datos_usuario(
            self._servicio_usuarios.listar_roles_asignables(self._actor)
        )
        if formulario is None:
            return
        resultado = self._servicio_usuarios.crear_usuario_operativo(self._actor, formulario)
        self._vista_usuarios.mostrar_mensaje(resultado.mensaje, es_error=not resultado.exito)
        if resultado.exito:
            self._refrescar()

    def _mostrar_detalle(self, identificador: int) -> None:
        usuario = self._buscar_usuario(identificador)
        if usuario is None:
            self._vista_usuarios.mostrar_mensaje(
                "No fue posible encontrar el usuario seleccionado.",
                es_error=True,
            )
            self._refrescar()
            return

        accion = self._vista_usuarios.mostrar_detalle_usuario(
            usuario=usuario,
            formateador_fecha=self._servicio_usuarios.formatear_fecha_hora,
        )
        if accion == "editar":
            self._editar_usuario(identificador)

    def _editar_usuario(self, identificador: int) -> None:
        if self._actor is None:
            self._mostrar_sin_sesion()
            return
        usuario = self._buscar_usuario(identificador)
        if usuario is None:
            self._vista_usuarios.mostrar_mensaje(
                "No fue posible encontrar el usuario seleccionado.",
                es_error=True,
            )
            self._refrescar()
            return
        if not self._es_usuario_operable(usuario):
            self._vista_usuarios.mostrar_mensaje(
                "Los usuarios tecnicos u ocultos solo se consultan desde esta vista.",
                es_error=True,
            )
            return

        formulario = self._vista_usuarios.solicitar_datos_usuario(
            self._servicio_usuarios.listar_roles_asignables(self._actor),
            usuario=usuario,
        )
        if formulario is None:
            return
        resultado = self._servicio_usuarios.actualizar_usuario_operativo(self._actor, formulario)
        self._vista_usuarios.mostrar_mensaje(resultado.mensaje, es_error=not resultado.exito)
        if resultado.exito:
            self._refrescar()

    def _cambiar_estado_usuario(self, identificador: int) -> None:
        if self._actor is None:
            self._mostrar_sin_sesion()
            return
        usuario = self._buscar_usuario(identificador)
        if usuario is None:
            self._vista_usuarios.mostrar_mensaje(
                "No fue posible encontrar el usuario seleccionado.",
                es_error=True,
            )
            self._refrescar()
            return
        if not self._es_usuario_operable(usuario):
            self._vista_usuarios.mostrar_mensaje(
                "Los usuarios tecnicos u ocultos no cambian de estado desde este modulo.",
                es_error=True,
            )
            return
        if not self._vista_usuarios.confirmar_cambio_estado_usuario(usuario):
            return

        resultado = self._servicio_usuarios.cambiar_estado_usuario_operativo(
            actor=self._actor,
            nombre_usuario_objetivo=usuario.nombre_usuario,
        )
        self._vista_usuarios.mostrar_mensaje(resultado.mensaje, es_error=not resultado.exito)
        if resultado.exito:
            self._refrescar()

    def _gestionar_acceso_usuario(self, identificador: int) -> None:
        if self._actor is None:
            self._mostrar_sin_sesion()
            return
        usuario = self._buscar_usuario(identificador)
        if usuario is None:
            self._vista_usuarios.mostrar_mensaje(
                "No fue posible encontrar el usuario seleccionado.",
                es_error=True,
            )
            self._refrescar()
            return
        if not self._es_usuario_operable(usuario):
            self._vista_usuarios.mostrar_mensaje(
                "Los usuarios tecnicos u ocultos no se administran desde este flujo.",
                es_error=True,
            )
            return

        gestion = self._vista_usuarios.solicitar_gestion_acceso(usuario)
        if gestion is None:
            return
        accion, nueva_contrasena, confirmacion_contrasena = gestion

        if accion == "desbloquear":
            resultado = self._servicio_usuarios.desbloquear_usuario_operativo(
                actor=self._actor,
                nombre_usuario_objetivo=usuario.nombre_usuario,
            )
            self._vista_usuarios.mostrar_mensaje(resultado.mensaje, es_error=not resultado.exito)
            if resultado.exito:
                self._refrescar()
            return

        resultado = self._servicio_usuarios.restablecer_contrasena_administrativa(
            actor=self._actor,
            nombre_usuario_objetivo=usuario.nombre_usuario,
            nueva_contrasena=nueva_contrasena,
            confirmacion_contrasena=confirmacion_contrasena,
        )
        self._vista_usuarios.mostrar_mensaje(resultado.mensaje, es_error=not resultado.exito)
        if resultado.exito:
            self._refrescar()

    def _exportar(self) -> None:
        ruta_destino = self._vista_usuarios.solicitar_ruta_exportacion()
        if not ruta_destino:
            return
        resultado = self._servicio_usuarios.exportar_csv(ruta_destino, self._usuarios_filtrados)
        self._vista_usuarios.mostrar_mensaje(resultado.mensaje, es_error=not resultado.exito)

    def _refrescar(self) -> None:
        if self._actor is None:
            self._usuarios_actuales = []
            self._usuarios_filtrados = []
            self._roles_actuales = []
            self._vista_usuarios.mostrar_roles([], [])
            self._vista_usuarios.mostrar_resumen(self._servicio_usuarios.obtener_resumen([]))
            self._vista_usuarios.mostrar_usuarios([], self._servicio_usuarios.formatear_fecha_hora)
            return

        self._usuarios_actuales = self._servicio_usuarios.listar_usuarios_para_administracion(self._actor)
        self._roles_actuales = self._servicio_usuarios.listar_roles_asignables(self._actor)
        self._vista_usuarios.mostrar_roles(self._roles_actuales, [])
        self._vista_usuarios.mostrar_resumen(self._servicio_usuarios.obtener_resumen(self._usuarios_actuales))
        self._renderizar_usuarios_filtrados()

    def _renderizar_usuarios_filtrados(self) -> None:
        self._usuarios_filtrados = self._servicio_usuarios.filtrar_usuarios(
            self._usuarios_actuales,
            texto=self._filtro_texto,
            filtro_rapido=self._filtro_rapido,
            rol=self._filtro_rol,
        )
        self._vista_usuarios.mostrar_usuarios(
            self._usuarios_filtrados,
            self._servicio_usuarios.formatear_fecha_hora,
        )

    def _buscar_usuario(self, identificador: int) -> UsuarioSistema | None:
        return next((usuario for usuario in self._usuarios_actuales if usuario.identificador == identificador), None)

    @staticmethod
    def _es_usuario_operable(usuario: UsuarioSistema) -> bool:
        return not usuario.es_tecnico and not usuario.es_oculto

    def _mostrar_sin_sesion(self) -> None:
        self._vista_usuarios.mostrar_mensaje("No hay una sesion activa.", es_error=True)
