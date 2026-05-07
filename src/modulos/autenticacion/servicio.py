"""Servicios del modulo de autenticacion."""

from __future__ import annotations

from datetime import datetime, timedelta
import hashlib
from logging import Logger
from secrets import token_urlsafe

from comun.logs import obtener_logger_sicap
from comun.seguridad import es_hash_scrypt_valido, generar_hash_contrasena, verificar_contrasena
from modulos.autenticacion.entidades import (
    CredencialesUsuario,
    ResultadoLogin,
    ResultadoOperacion,
    UsuarioAutenticado,
)
from modulos.autenticacion.repositorio import RepositorioAutenticacion


FORMATO_FECHA_BD = "%Y-%m-%d %H:%M:%S"
MENSAJE_LOGIN_INVALIDO = "Usuario o contraseña incorrectos."
CODIGO_VALIDACION = "VALIDACION"
MAXIMO_INTENTOS_FALLIDOS = 5


class ServicioAutenticacion:
    """Orquesta la logica de negocio del modulo."""

    def __init__(
        self,
        repositorio_autenticacion: RepositorioAutenticacion,
        duracion_sesion_horas: int = 8,
    ) -> None:
        self.repositorio_autenticacion = repositorio_autenticacion
        self.duracion_sesion_horas = duracion_sesion_horas
        self._logger: Logger = obtener_logger_sicap("autenticacion.servicio")

    def asegurar_usuario_admin_desarrollo(self) -> None:
        """Repara instalaciones locales que aun conservan hashes placeholder."""
        usuarios_desarrollo = (
            ("admin", "Admin123!"),
            ("superadmin", "SuperAdmin123!"),
        )
        for nombre_usuario, contrasena_defecto in usuarios_desarrollo:
            usuario = self.repositorio_autenticacion.obtener_usuario_por_nombre_usuario(
                nombre_usuario
            )
            if usuario is None:
                continue

            if es_hash_scrypt_valido(usuario.contrasena_hash):
                continue

            if usuario.contrasena_hash != "CAMBIAR_HASH_EN_DESARROLLO":
                continue

            marca_tiempo = self._formatear_fecha(self._ahora())
            nuevo_hash = generar_hash_contrasena(contrasena_defecto)
            self.repositorio_autenticacion.actualizar_contrasena_usuario(
                usuario_id=usuario.identificador,
                nuevo_hash=nuevo_hash,
                momento=marca_tiempo,
                requiere_cambio_contrasena=usuario.requiere_cambio_contrasena,
            )
            self._logger.warning(
                "Se reemplazo el hash placeholder del usuario %s en entorno local.",
                nombre_usuario,
            )

    def iniciar_sesion(
        self,
        credenciales: CredencialesUsuario,
        ip_origen: str | None = None,
    ) -> ResultadoLogin:
        nombre_usuario = credenciales.nombre_usuario.strip()
        contrasena_plana = credenciales.contrasena_plana

        if not nombre_usuario or not contrasena_plana:
            self._logger.warning("Intento de login rechazado por credenciales incompletas.")
            return ResultadoLogin(
                exito=False,
                mensaje="Ingresa tu usuario y contraseña.",
                codigo=CODIGO_VALIDACION,
            )

        usuario = self.repositorio_autenticacion.obtener_usuario_por_nombre_usuario(nombre_usuario)
        if usuario is None:
            self.repositorio_autenticacion.registrar_intento_login(
                identificador=nombre_usuario,
                resultado="FALLIDO",
                usuario_id=None,
                motivo="USUARIO_NO_EXISTE",
                equipo=ip_origen,
            )
            self._logger.warning(
                "Intento de login fallido para usuario inexistente '%s'.",
                nombre_usuario,
            )
            return ResultadoLogin(
                exito=False,
                mensaje=MENSAJE_LOGIN_INVALIDO,
                codigo="LOGIN_INVALIDO",
            )

        if usuario.estado == "INACTIVO":
            self.repositorio_autenticacion.registrar_intento_login(
                identificador=nombre_usuario,
                resultado="FALLIDO",
                usuario_id=usuario.identificador,
                motivo="USUARIO_INACTIVO",
                equipo=ip_origen,
            )
            self._logger.warning(
                "Intento de login rechazado para usuario inactivo '%s'.",
                nombre_usuario,
            )
            return ResultadoLogin(
                exito=False,
                mensaje="Tu usuario esta inactivo. Contacta al administrador.",
                codigo="USUARIO_INACTIVO",
            )

        if usuario.estado == "BLOQUEADO":
            self.repositorio_autenticacion.registrar_intento_login(
                identificador=nombre_usuario,
                resultado="FALLIDO",
                usuario_id=usuario.identificador,
                motivo="USUARIO_BLOQUEADO",
                equipo=ip_origen,
            )
            self._logger.warning(
                "Intento de login rechazado para usuario bloqueado '%s'.",
                nombre_usuario,
            )
            return ResultadoLogin(
                exito=False,
                mensaje="Tu usuario esta bloqueado. Contacta al administrador.",
                codigo="USUARIO_BLOQUEADO",
            )

        if not verificar_contrasena(contrasena_plana, usuario.contrasena_hash):
            intentos_fallidos = self.repositorio_autenticacion.incrementar_intentos_fallidos(
                usuario.identificador,
                self._formatear_fecha(self._ahora()),
            )
            motivo = "CONTRASENA_INVALIDA"
            if intentos_fallidos >= MAXIMO_INTENTOS_FALLIDOS:
                self.repositorio_autenticacion.bloquear_usuario(
                    usuario_id=usuario.identificador,
                    momento=self._formatear_fecha(self._ahora()),
                )
                motivo = "USUARIO_BLOQUEADO_POR_INTENTOS"
            self.repositorio_autenticacion.registrar_intento_login(
                identificador=nombre_usuario,
                resultado="FALLIDO",
                usuario_id=usuario.identificador,
                motivo=motivo,
                equipo=ip_origen,
            )
            self._logger.warning(
                "Intento de login con contrasena incorrecta para '%s'.",
                nombre_usuario,
            )
            mensaje = MENSAJE_LOGIN_INVALIDO
            codigo = "LOGIN_INVALIDO"
            if intentos_fallidos >= MAXIMO_INTENTOS_FALLIDOS:
                mensaje = "Tu usuario fue bloqueado por seguridad. Contacta al administrador."
                codigo = "USUARIO_BLOQUEADO"
            return ResultadoLogin(
                exito=False,
                mensaje=mensaje,
                codigo=codigo,
            )

        momento_actual = self._ahora()
        self.repositorio_autenticacion.reiniciar_intentos_fallidos(
            usuario.identificador,
            self._formatear_fecha(momento_actual),
        )
        self.repositorio_autenticacion.registrar_intento_login(
            identificador=nombre_usuario,
            resultado="EXITOSO",
            usuario_id=usuario.identificador,
            motivo=(
                "CAMBIO_CONTRASENA_OBLIGATORIO"
                if usuario.requiere_cambio_contrasena
                else "LOGIN_OK"
            ),
            equipo=ip_origen,
        )
        self.repositorio_autenticacion.actualizar_ultimo_acceso(
            usuario.identificador,
            self._formatear_fecha(momento_actual),
        )

        usuario_autenticado = UsuarioAutenticado.desde_registro(usuario)
        if usuario.requiere_cambio_contrasena:
            self._logger.info(
                "Usuario '%s' autenticado con cambio obligatorio pendiente.",
                nombre_usuario,
            )
            return ResultadoLogin(
                exito=True,
                mensaje="Debes cambiar tu contraseña antes de continuar.",
                codigo="CAMBIO_CONTRASENA_OBLIGATORIO",
                usuario=usuario_autenticado,
                token_sesion=None,
                requiere_cambio_contrasena=True,
            )

        expira_en = momento_actual + timedelta(hours=self.duracion_sesion_horas)
        token_sesion = token_urlsafe(32)
        self.repositorio_autenticacion.crear_sesion(
            usuario_id=usuario.identificador,
            token_sesion_hash=self._generar_hash_token(token_sesion),
            expira_en=self._formatear_fecha(expira_en),
            equipo=ip_origen,
        )
        self._logger.info(
            "Sesion iniciada por '%s' con usuario_id=%s.",
            nombre_usuario,
            usuario.identificador,
        )

        return ResultadoLogin(
            exito=True,
            mensaje="Autenticacion correcta.",
            codigo="OK",
            usuario=usuario_autenticado,
            token_sesion=token_sesion,
        )

    def restablecer_contrasena(
        self,
        nombre_usuario: str,
        nueva_contrasena: str,
        confirmacion_contrasena: str,
    ) -> ResultadoOperacion:
        nombre_usuario_normalizado = nombre_usuario.strip()
        if not nombre_usuario_normalizado:
            return ResultadoOperacion(
                exito=False,
                mensaje="No se identifico el usuario a restablecer.",
                codigo=CODIGO_VALIDACION,
            )

        if not nueva_contrasena or not confirmacion_contrasena:
            return ResultadoOperacion(
                exito=False,
                mensaje="Completa ambos campos de contraseña.",
                codigo=CODIGO_VALIDACION,
            )

        if len(nueva_contrasena) < 8:
            return ResultadoOperacion(
                exito=False,
                mensaje="La nueva contraseña debe tener al menos 8 caracteres.",
                codigo=CODIGO_VALIDACION,
            )

        if nueva_contrasena != confirmacion_contrasena:
            return ResultadoOperacion(
                exito=False,
                mensaje="Las contraseñas no coinciden.",
                codigo=CODIGO_VALIDACION,
            )

        usuario = self.repositorio_autenticacion.obtener_usuario_por_nombre_usuario(
            nombre_usuario_normalizado
        )
        if usuario is None:
            return ResultadoOperacion(
                exito=False,
                mensaje="El usuario indicado no existe.",
                codigo="USUARIO_NO_ENCONTRADO",
            )

        if usuario.estado != "ACTIVO":
            return ResultadoOperacion(
                exito=False,
                mensaje="Solo se permite restablecer contraseña para usuarios activos.",
                codigo="USUARIO_NO_ACTIVO",
            )

        marca_tiempo = self._formatear_fecha(self._ahora())
        nuevo_hash = generar_hash_contrasena(nueva_contrasena)
        self.repositorio_autenticacion.actualizar_contrasena_usuario(
            usuario_id=usuario.identificador,
            nuevo_hash=nuevo_hash,
            momento=marca_tiempo,
            requiere_cambio_contrasena=False,
            restablecida_por_usuario_id=None,
            fecha_restablecimiento=None,
        )
        self._logger.info(
            "Contraseña restablecida para usuario_id=%s.",
            usuario.identificador,
        )
        return ResultadoOperacion(
            exito=True,
            mensaje="Tu contraseña se actualizo correctamente.",
            codigo="OK",
        )

    def cerrar_sesion(self, token_sesion: str) -> ResultadoOperacion:
        if not token_sesion.strip():
            return ResultadoOperacion(
                exito=False,
                mensaje="No existe una sesion activa para cerrar.",
                codigo=CODIGO_VALIDACION,
            )

        self.repositorio_autenticacion.finalizar_sesion(
            token_sesion_hash=self._generar_hash_token(token_sesion.strip()),
            momento=self._formatear_fecha(self._ahora()),
        )
        self._logger.info("Se finalizo una sesion activa.")
        return ResultadoOperacion(
            exito=True,
            mensaje="Sesion cerrada correctamente.",
            codigo="OK",
        )

    @staticmethod
    def _ahora() -> datetime:
        return datetime.now()

    @staticmethod
    def _formatear_fecha(fecha: datetime) -> str:
        return fecha.strftime(FORMATO_FECHA_BD)

    @staticmethod
    def _generar_hash_token(token_sesion: str) -> str:
        return hashlib.sha256(token_sesion.encode("utf-8")).hexdigest()
