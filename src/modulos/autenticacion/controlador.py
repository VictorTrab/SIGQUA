"""Controladores del modulo de autenticacion."""

from __future__ import annotations

from modulos.autenticacion.entidades import CredencialesUsuario
from modulos.autenticacion.servicio import CODIGO_TOKEN_INVALIDO, ServicioAutenticacion
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

    def abrir_restablecimiento_desde_token(self, token: str) -> None:
        resultado = self.servicio_autenticacion.validar_token_recuperacion(token)
        if resultado.exito and resultado.token_recuperacion is not None:
            self.vista_autenticacion.mostrar_restablecer(token, resultado.mensaje)
            return
        self.vista_autenticacion.mostrar_enlace_invalido(resultado.mensaje)

    def _conectar_eventos(self) -> None:
        self.vista_autenticacion.iniciar_sesion_solicitada.connect(self._procesar_login)
        self.vista_autenticacion.ir_a_olvido_solicitado.connect(self._mostrar_olvido_contrasena)
        self.vista_autenticacion.recuperacion_solicitada.connect(self._procesar_recuperacion)
        self.vista_autenticacion.token_prueba_solicitado.connect(
            self.abrir_restablecimiento_desde_token
        )
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
            self.vista_autenticacion.limpiar_campos_sensibles()
            self.vista_autenticacion.notificar_autenticacion_exitosa(resultado.usuario)
            return
        self.vista_autenticacion.mostrar_error_login(resultado.mensaje)

    def _mostrar_olvido_contrasena(self) -> None:
        self.vista_autenticacion.mostrar_olvido_contrasena()

    def _procesar_recuperacion(self, correo: str) -> None:
        resultado = self.servicio_autenticacion.solicitar_recuperacion(correo)
        if not resultado.exito:
            self.vista_autenticacion.mostrar_error_olvido(resultado.mensaje)
            return
        self.vista_autenticacion.mostrar_correo_enviado(
            mensaje=resultado.mensaje,
            token_prueba=resultado.token_prueba,
        )

    def _procesar_restablecimiento(
        self,
        token: str,
        nueva_contrasena: str,
        confirmacion_contrasena: str,
    ) -> None:
        resultado = self.servicio_autenticacion.restablecer_contrasena(
            token=token,
            nueva_contrasena=nueva_contrasena,
            confirmacion_contrasena=confirmacion_contrasena,
        )
        if resultado.exito:
            self.vista_autenticacion.mostrar_exito(resultado.mensaje)
            return

        if resultado.codigo == CODIGO_TOKEN_INVALIDO:
            self.vista_autenticacion.mostrar_enlace_invalido(resultado.mensaje)
            return

        self.vista_autenticacion.mostrar_error_restablecer(resultado.mensaje)

    def _mostrar_login(self) -> None:
        self.vista_autenticacion.mostrar_login()
