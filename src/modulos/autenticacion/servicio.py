"""Servicios del modulo de autenticacion."""

from __future__ import annotations

from datetime import datetime, timedelta
import hashlib
import math
from logging import Logger
from secrets import token_urlsafe

from comun.logs import obtener_logger_sigqua
from comun.seguridad import (
    generar_hash_contrasena,
    validar_politica_contrasena,
    verificar_contrasena,
)
from modulos.configuracion.repositorio import RepositorioConfiguracionSQLite
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
ESPERAS_PROGRESIVAS_MINUTOS = (5, 10, 15, 30, 60)
INTENTOS_ANTES_DE_ESPERA = 5


class ServicioAutenticacion:
    """Orquesta la logica de negocio del modulo."""

    def __init__(
        self,
        repositorio_autenticacion: RepositorioAutenticacion,
        duracion_sesion_horas: int = 8,
        repositorio_configuracion: RepositorioConfiguracionSQLite | None = None,
    ) -> None:
        self.repositorio_autenticacion = repositorio_autenticacion
        self.duracion_sesion_horas = duracion_sesion_horas
        self._repositorio_configuracion = repositorio_configuracion
        self._logger: Logger = obtener_logger_sigqua("autenticacion.servicio")

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

        momento_actual = self._ahora()
        bloqueado_hasta = self._parsear_fecha(usuario.bloqueado_hasta)
        if bloqueado_hasta is not None and momento_actual < bloqueado_hasta:
            minutos_restantes = max(
                1,
                math.ceil((bloqueado_hasta - momento_actual).total_seconds() / 60),
            )
            self.repositorio_autenticacion.registrar_intento_login(
                identificador=nombre_usuario,
                resultado="FALLIDO",
                usuario_id=usuario.identificador,
                motivo="ESPERA_SEGURIDAD_ACTIVA",
                equipo=ip_origen,
            )
            return ResultadoLogin(
                exito=False,
                mensaje=(
                    f"Espera {minutos_restantes} "
                    f"{'minuto' if minutos_restantes == 1 else 'minutos'} antes de intentar de nuevo."
                ),
                codigo="ESPERA_SEGURIDAD",
            )

        if not verificar_contrasena(contrasena_plana, usuario.contrasena_hash):
            intentos_fallidos = self.repositorio_autenticacion.incrementar_intentos_fallidos(
                usuario.identificador,
                self._formatear_fecha(momento_actual),
            )
            if intentos_fallidos < INTENTOS_ANTES_DE_ESPERA:
                intentos_restantes = INTENTOS_ANTES_DE_ESPERA - intentos_fallidos
                self.repositorio_autenticacion.registrar_intento_login(
                    identificador=nombre_usuario,
                    resultado="FALLIDO",
                    usuario_id=usuario.identificador,
                    motivo="CONTRASENA_INVALIDA",
                    equipo=ip_origen,
                )
                self._logger.warning(
                    "Intento de login con contrasena incorrecta para '%s'.",
                    nombre_usuario,
                )
                return ResultadoLogin(
                    exito=False,
                    mensaje=(
                        f"Usuario o contraseña incorrectos. Quedan {intentos_restantes} "
                        f"{'intento' if intentos_restantes == 1 else 'intentos'} "
                        "antes de la espera de seguridad."
                    ),
                    codigo="LOGIN_INVALIDO",
                )

            indice_espera = min(
                intentos_fallidos - INTENTOS_ANTES_DE_ESPERA + 1,
                len(ESPERAS_PROGRESIVAS_MINUTOS),
            ) - 1
            minutos_espera = ESPERAS_PROGRESIVAS_MINUTOS[indice_espera]
            fin_espera = momento_actual + timedelta(minutes=minutos_espera)
            self.repositorio_autenticacion.programar_espera_login(
                usuario_id=usuario.identificador,
                momento=self._formatear_fecha(momento_actual),
                bloqueado_hasta=self._formatear_fecha(fin_espera),
            )
            self.repositorio_autenticacion.registrar_intento_login(
                identificador=nombre_usuario,
                resultado="FALLIDO",
                usuario_id=usuario.identificador,
                motivo=f"CONTRASENA_INVALIDA_ESPERA_{minutos_espera}_MIN",
                equipo=ip_origen,
            )
            self._logger.warning(
                "Intento de login con contrasena incorrecta para '%s'.",
                nombre_usuario,
            )
            return ResultadoLogin(
                exito=False,
                mensaje=(
                    "Contraseña incorrecta. "
                    f"Espera {minutos_espera} minutos antes de intentar de nuevo."
                ),
                codigo="ESPERA_SEGURIDAD",
            )

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

        expira_en = momento_actual + timedelta(hours=self._resolver_duracion_sesion_horas())
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

        mensaje_validacion = validar_politica_contrasena(
            nueva_contrasena,
            confirmacion_contrasena,
            nombre_usuario=usuario.nombre_usuario,
            correo=usuario.correo,
        )
        if mensaje_validacion is not None:
            return ResultadoOperacion(
                exito=False,
                mensaje=mensaje_validacion,
                codigo=CODIGO_VALIDACION,
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
    def _parsear_fecha(fecha_texto: str | None) -> datetime | None:
        if not fecha_texto:
            return None
        try:
            return datetime.strptime(fecha_texto, FORMATO_FECHA_BD)
        except ValueError:
            return None

    @staticmethod
    def _generar_hash_token(token_sesion: str) -> str:
        return hashlib.sha256(token_sesion.encode("utf-8")).hexdigest()

    def _resolver_duracion_sesion_horas(self) -> float:
        if self._repositorio_configuracion is None:
            return float(self.duracion_sesion_horas)
        try:
            parametros = self._repositorio_configuracion.listar_por_claves(
                ("seguridad.duracion_sesion_horas",)
            )
            parametro = parametros.get("seguridad.duracion_sesion_horas")
            if parametro is None:
                return float(self.duracion_sesion_horas)
            valor = float(str(parametro.valor or self.duracion_sesion_horas))
            return valor if valor > 0 else float(self.duracion_sesion_horas)
        except Exception:
            return float(self.duracion_sesion_horas)
