"""Servicios del modulo de autenticacion."""

from __future__ import annotations

from datetime import datetime, timedelta
from secrets import token_urlsafe

from apis.contratos.proveedor_correo import ProveedorCorreo
from comun.seguridad import es_hash_scrypt_valido, generar_hash_contrasena, verificar_contrasena
from modulos.autenticacion.entidades import (
    CredencialesUsuario,
    ResultadoLogin,
    ResultadoOperacion,
    ResultadoRecuperacion,
    ResultadoValidacionToken,
    TokenRecuperacion,
    UsuarioAutenticado,
)
from modulos.autenticacion.repositorio import RepositorioAutenticacion


FORMATO_FECHA_BD = "%Y-%m-%d %H:%M:%S"
MENSAJE_LOGIN_INVALIDO = "Usuario o contraseña incorrectos."
MENSAJE_TOKEN_INVALIDO = "El enlace no es valido o ya expiro."
MENSAJE_RECUPERACION_GENERICO = (
    "Si el correo pertenece a una cuenta activa, el enlace de recuperacion ya esta listo."
)
CODIGO_VALIDACION = "VALIDACION"
CODIGO_TOKEN_INVALIDO = "TOKEN_INVALIDO"


class ServicioAutenticacion:
    """Orquesta la logica de negocio del modulo."""

    def __init__(
        self,
        repositorio_autenticacion: RepositorioAutenticacion,
        proveedor_correo: ProveedorCorreo | None = None,
        entorno: str = "desarrollo",
        duracion_sesion_horas: int = 8,
        duracion_token_minutos: int = 30,
    ) -> None:
        self.repositorio_autenticacion = repositorio_autenticacion
        self.proveedor_correo = proveedor_correo
        self.entorno = entorno
        self.duracion_sesion_horas = duracion_sesion_horas
        self.duracion_token_minutos = duracion_token_minutos

    def asegurar_usuario_admin_desarrollo(self) -> None:
        """Repara instalaciones locales que aun conservan el hash placeholder."""
        usuario_admin = self.repositorio_autenticacion.obtener_usuario_por_nombre_usuario("admin")
        if usuario_admin is None:
            return

        if es_hash_scrypt_valido(usuario_admin.contrasena_hash):
            return

        if usuario_admin.contrasena_hash != "CAMBIAR_HASH_EN_DESARROLLO":
            return

        marca_tiempo = self._formatear_fecha(self._ahora())
        nuevo_hash = generar_hash_contrasena("Admin123!")
        self.repositorio_autenticacion.actualizar_hash_usuario(
            usuario_admin.identificador,
            nuevo_hash,
            marca_tiempo,
        )

    def iniciar_sesion(
        self,
        credenciales: CredencialesUsuario,
        ip_origen: str | None = None,
    ) -> ResultadoLogin:
        nombre_usuario = credenciales.nombre_usuario.strip()
        contrasena_plana = credenciales.contrasena_plana

        if not nombre_usuario or not contrasena_plana:
            return ResultadoLogin(
                exito=False,
                mensaje="Ingresa tu usuario y contrasena.",
                codigo=CODIGO_VALIDACION,
            )

        usuario = self.repositorio_autenticacion.obtener_usuario_por_nombre_usuario(nombre_usuario)
        if usuario is None:
            self.repositorio_autenticacion.registrar_intento_login(
                nombre_usuario=nombre_usuario,
                exito=False,
                usuario_id=None,
                ip_origen=ip_origen,
            )
            return ResultadoLogin(exito=False, mensaje=MENSAJE_LOGIN_INVALIDO, codigo="LOGIN_INVALIDO")

        if usuario.estado == "INACTIVO":
            self.repositorio_autenticacion.registrar_intento_login(
                nombre_usuario=nombre_usuario,
                exito=False,
                usuario_id=usuario.identificador,
                ip_origen=ip_origen,
            )
            return ResultadoLogin(
                exito=False,
                mensaje="Tu usuario esta inactivo. Contacta al administrador.",
                codigo="USUARIO_INACTIVO",
            )

        if usuario.estado == "BLOQUEADO":
            self.repositorio_autenticacion.registrar_intento_login(
                nombre_usuario=nombre_usuario,
                exito=False,
                usuario_id=usuario.identificador,
                ip_origen=ip_origen,
            )
            return ResultadoLogin(
                exito=False,
                mensaje="Tu usuario esta bloqueado. Contacta al administrador.",
                codigo="USUARIO_BLOQUEADO",
            )

        if not verificar_contrasena(contrasena_plana, usuario.contrasena_hash):
            self.repositorio_autenticacion.registrar_intento_login(
                nombre_usuario=nombre_usuario,
                exito=False,
                usuario_id=usuario.identificador,
                ip_origen=ip_origen,
            )
            return ResultadoLogin(exito=False, mensaje=MENSAJE_LOGIN_INVALIDO, codigo="LOGIN_INVALIDO")

        momento_actual = self._ahora()
        expira_en = momento_actual + timedelta(hours=self.duracion_sesion_horas)
        token_sesion = token_urlsafe(32)

        self.repositorio_autenticacion.actualizar_ultimo_acceso(
            usuario.identificador,
            self._formatear_fecha(momento_actual),
        )
        self.repositorio_autenticacion.crear_sesion(
            usuario_id=usuario.identificador,
            token_sesion=token_sesion,
            expira_en=self._formatear_fecha(expira_en),
            ip_origen=ip_origen,
        )
        self.repositorio_autenticacion.registrar_intento_login(
            nombre_usuario=nombre_usuario,
            exito=True,
            usuario_id=usuario.identificador,
            ip_origen=ip_origen,
        )

        return ResultadoLogin(
            exito=True,
            mensaje="Autenticacion correcta.",
            codigo="OK",
            usuario=UsuarioAutenticado.desde_registro(usuario),
            token_sesion=token_sesion,
        )

    def solicitar_recuperacion(self, correo: str) -> ResultadoRecuperacion:
        correo_normalizado = correo.strip().lower()
        if not correo_normalizado:
            return ResultadoRecuperacion(
                exito=False,
                mensaje="Ingresa el correo de tu cuenta.",
                codigo=CODIGO_VALIDACION,
            )

        usuario = self.repositorio_autenticacion.obtener_usuario_por_correo(correo_normalizado)
        if usuario is None or usuario.estado != "ACTIVO":
            return ResultadoRecuperacion(
                exito=True,
                mensaje=MENSAJE_RECUPERACION_GENERICO,
                codigo="RECUPERACION_GENERICA",
            )

        expira_en = self._ahora() + timedelta(minutes=self.duracion_token_minutos)
        token_generado = token_urlsafe(24)
        token_persistido = self.repositorio_autenticacion.crear_token_recuperacion(
            usuario_id=usuario.identificador,
            token=token_generado,
            expira_en=self._formatear_fecha(expira_en),
        )

        if self.proveedor_correo is not None:
            self.proveedor_correo.enviar_correo(
                destinatario=usuario.correo,
                asunto="Recuperacion de acceso a SICAP",
                contenido=self._construir_contenido_recuperacion(token_persistido),
            )

        token_prueba = token_generado if self._es_entorno_desarrollo() else None
        return ResultadoRecuperacion(
            exito=True,
            mensaje=MENSAJE_RECUPERACION_GENERICO,
            codigo="RECUPERACION_GENERICA",
            token_prueba=token_prueba,
        )

    def validar_token_recuperacion(self, token: str) -> ResultadoValidacionToken:
        token_normalizado = token.strip()
        if not token_normalizado:
            return ResultadoValidacionToken(
                exito=False,
                mensaje=MENSAJE_TOKEN_INVALIDO,
                codigo=CODIGO_TOKEN_INVALIDO,
            )

        token_persistido = self.repositorio_autenticacion.obtener_token_recuperacion(token_normalizado)
        if token_persistido is None:
            return ResultadoValidacionToken(
                exito=False,
                mensaje=MENSAJE_TOKEN_INVALIDO,
                codigo=CODIGO_TOKEN_INVALIDO,
            )

        if token_persistido.usado_en is not None:
            return ResultadoValidacionToken(
                exito=False,
                mensaje=MENSAJE_TOKEN_INVALIDO,
                codigo=CODIGO_TOKEN_INVALIDO,
            )

        if self._parsear_fecha(token_persistido.expira_en) < self._ahora():
            return ResultadoValidacionToken(
                exito=False,
                mensaje=MENSAJE_TOKEN_INVALIDO,
                codigo=CODIGO_TOKEN_INVALIDO,
            )

        return ResultadoValidacionToken(
            exito=True,
            mensaje="Define una nueva contrasena para continuar.",
            codigo="OK",
            token_recuperacion=token_persistido,
        )

    def restablecer_contrasena(
        self,
        token: str,
        nueva_contrasena: str,
        confirmacion_contrasena: str,
    ) -> ResultadoOperacion:
        if not nueva_contrasena or not confirmacion_contrasena:
            return ResultadoOperacion(
                exito=False,
                mensaje="Completa ambos campos de contrasena.",
                codigo=CODIGO_VALIDACION,
            )

        if len(nueva_contrasena) < 8:
            return ResultadoOperacion(
                exito=False,
                mensaje="La nueva contrasena debe tener al menos 8 caracteres.",
                codigo=CODIGO_VALIDACION,
            )

        if nueva_contrasena != confirmacion_contrasena:
            return ResultadoOperacion(
                exito=False,
                mensaje="Las contrasenas no coinciden.",
                codigo=CODIGO_VALIDACION,
            )

        resultado_token = self.validar_token_recuperacion(token)
        if not resultado_token.exito or resultado_token.token_recuperacion is None:
            return ResultadoOperacion(
                exito=False,
                mensaje=MENSAJE_TOKEN_INVALIDO,
                codigo=CODIGO_TOKEN_INVALIDO,
            )

        marca_tiempo = self._formatear_fecha(self._ahora())
        nuevo_hash = generar_hash_contrasena(nueva_contrasena)
        self.repositorio_autenticacion.restablecer_contrasena(
            usuario_id=resultado_token.token_recuperacion.usuario_id,
            token_id=resultado_token.token_recuperacion.identificador,
            nuevo_hash=nuevo_hash,
            momento=marca_tiempo,
        )
        return ResultadoOperacion(
            exito=True,
            mensaje="Tu contrasena se actualizo correctamente.",
            codigo="OK",
        )

    def _construir_contenido_recuperacion(self, token_recuperacion: TokenRecuperacion) -> str:
        return (
            "<h2>Recuperacion de acceso a SICAP</h2>"
            "<p>Tu enlace de recuperacion ya esta listo.</p>"
            f"<p>Token temporal: <strong>{token_recuperacion.token}</strong></p>"
            f"<p>Vigencia hasta: <strong>{token_recuperacion.expira_en}</strong></p>"
        )

    def _es_entorno_desarrollo(self) -> bool:
        return self.entorno.strip().lower() in {"desarrollo", "dev", "development"}

    @staticmethod
    def _ahora() -> datetime:
        return datetime.now()

    @staticmethod
    def _formatear_fecha(fecha: datetime) -> str:
        return fecha.strftime(FORMATO_FECHA_BD)

    @staticmethod
    def _parsear_fecha(valor: str) -> datetime:
        return datetime.strptime(valor, FORMATO_FECHA_BD)
