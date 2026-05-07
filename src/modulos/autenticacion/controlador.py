"""Controladores del modulo de autenticacion."""

from __future__ import annotations

from modulos.autenticacion.entidades import CredencialesUsuario
from modulos.autenticacion.servicio import ServicioAutenticacion
from modulos.autenticacion.vista import VistaAutenticacion


class ControladorAutenticacion:
    """Conecta la vista con los servicios del modulo."""

    def __init__(
        self,
        servicio_autenticacion: ServicioAutenticacion,
        vista_autenticacion: VistaAutenticacion,
    ) -> None:
        self.servicio_autenticacion = servicio_autenticacion
        self.vista_autenticacion = vista_autenticacion
        self._conectar_eventos()
        self.vista_autenticacion.mostrar_login()

    def abrir_restablecimiento_administrativo(
        self,
        nombre_usuario: str,
        mensaje: str | None = None,
    ) -> None:
        self.vista_autenticacion.mostrar_restablecer(nombre_usuario, mensaje)

    def _conectar_eventos(self) -> None:
        self.vista_autenticacion.iniciar_sesion_solicitada.connect(self._procesar_login)
        self.vista_autenticacion.ir_a_olvido_solicitado.connect(self._mostrar_olvido_contrasena)
        self.vista_autenticacion.restablecimiento_solicitado.connect(
            self._procesar_restablecimiento
        )
        self.vista_autenticacion.volver_a_login_solicitado.connect(self._mostrar_login)

    def _procesar_login(self, nombre_usuario: str, contrasena: str) -> None:
        resultado = self.servicio_autenticacion.iniciar_sesion(
            CredencialesUsuario(
                nombre_usuario=nombre_usuario,
                contrasena_plana=contrasena,
            )
        )
        if resultado.exito and resultado.usuario is not None:
            if resultado.requiere_cambio_contrasena:
                self.vista_autenticacion.limpiar_campos_sensibles()
                self.vista_autenticacion.mostrar_restablecer(
                    resultado.usuario.nombre_usuario,
                    resultado.mensaje,
                )
                return
            self.vista_autenticacion.limpiar_campos_sensibles()
            self.vista_autenticacion.notificar_autenticacion_exitosa(
                resultado.usuario,
                resultado.token_sesion or "",
            )
            return
        self.vista_autenticacion.mostrar_error_login(resultado.mensaje)

    def _mostrar_olvido_contrasena(self) -> None:
        self.vista_autenticacion.mostrar_olvido_contrasena()

    def _procesar_restablecimiento(
        self,
        nombre_usuario: str,
        nueva_contrasena: str,
        confirmacion_contrasena: str,
    ) -> None:
        resultado = self.servicio_autenticacion.restablecer_contrasena(
            nombre_usuario=nombre_usuario,
            nueva_contrasena=nueva_contrasena,
            confirmacion_contrasena=confirmacion_contrasena,
        )
        if resultado.exito:
            self.vista_autenticacion.mostrar_exito(resultado.mensaje)
            return

        self.vista_autenticacion.mostrar_error_restablecer(resultado.mensaje)

    def _mostrar_login(self) -> None:
        self.vista_autenticacion.mostrar_login()
