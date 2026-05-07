"""Controlador del modulo de usuarios."""

from __future__ import annotations

from modulos.autenticacion.entidades import UsuarioAutenticado
from modulos.usuarios.servicio import ServicioUsuarios
from modulos.usuarios.vista import VistaUsuarios


class ControladorUsuarios:
    """Conecta la vista con los servicios del modulo."""

    def __init__(self, servicio_usuarios: ServicioUsuarios, vista_usuarios: VistaUsuarios):
        self._servicio_usuarios = servicio_usuarios
        self._vista_usuarios = vista_usuarios
        self._actor: UsuarioAutenticado | None = None
        self._conectar_senales()

    def mostrar_para_actor(self, actor: UsuarioAutenticado) -> None:
        """Carga usuarios visibles para el usuario autenticado."""
        self._actor = actor
        self._refrescar()

    def _conectar_senales(self) -> None:
        self._vista_usuarios.recargar_solicitado.connect(self._refrescar)
        self._vista_usuarios.restablecer_solicitado.connect(self._restablecer_contrasena)
        self._vista_usuarios.desbloquear_solicitado.connect(self._desbloquear_usuario)

    def _refrescar(self) -> None:
        if self._actor is None:
            self._vista_usuarios.mostrar_usuarios([])
            return
        self._vista_usuarios.mostrar_usuarios(
            self._servicio_usuarios.listar_usuarios_para_administracion(self._actor)
        )

    def _restablecer_contrasena(
        self,
        nombre_usuario: str,
        nueva_contrasena: str,
        confirmacion: str,
    ) -> None:
        if self._actor is None:
            self._vista_usuarios.mostrar_mensaje("No hay una sesion activa.", es_exito=False)
            return
        resultado = self._servicio_usuarios.restablecer_contrasena_administrativa(
            actor=self._actor,
            nombre_usuario_objetivo=nombre_usuario,
            nueva_contrasena_temporal=nueva_contrasena,
            confirmacion_contrasena=confirmacion,
        )
        self._vista_usuarios.mostrar_mensaje(resultado.mensaje, resultado.exito)
        if resultado.exito:
            self._refrescar()

    def _desbloquear_usuario(self, nombre_usuario: str) -> None:
        if self._actor is None:
            self._vista_usuarios.mostrar_mensaje("No hay una sesion activa.", es_exito=False)
            return
        resultado = self._servicio_usuarios.desbloquear_usuario_operativo(
            actor=self._actor,
            nombre_usuario_objetivo=nombre_usuario,
        )
        self._vista_usuarios.mostrar_mensaje(resultado.mensaje, resultado.exito)
        if resultado.exito:
            self._refrescar()
