"""Persistencia SQLite para el modulo de autenticacion."""

from __future__ import annotations

from contextlib import closing
from typing import Protocol

from comun.base_datos import GestorBaseDatos
from modulos.autenticacion.entidades import TokenRecuperacion, UsuarioRegistroAutenticacion


class RepositorioAutenticacion(Protocol):
    """Define el acceso persistente requerido por autenticacion."""

    def obtener_usuario_por_nombre_usuario(
        self,
        nombre_usuario: str,
    ) -> UsuarioRegistroAutenticacion | None:
        """Obtiene un usuario por nombre de usuario."""

    def obtener_usuario_por_correo(self, correo: str) -> UsuarioRegistroAutenticacion | None:
        """Obtiene un usuario por correo."""

    def registrar_intento_login(
        self,
        nombre_usuario: str,
        exito: bool,
        usuario_id: int | None = None,
        ip_origen: str | None = None,
    ) -> None:
        """Registra un intento de login."""

    def crear_sesion(
        self,
        usuario_id: int,
        token_sesion: str,
        expira_en: str,
        ip_origen: str | None = None,
    ) -> None:
        """Crea una sesion persistida."""

    def actualizar_ultimo_acceso(self, usuario_id: int, momento: str) -> None:
        """Actualiza el ultimo acceso del usuario."""

    def crear_token_recuperacion(
        self,
        usuario_id: int,
        token: str,
        expira_en: str,
    ) -> TokenRecuperacion:
        """Crea un token de recuperacion persistido."""

    def obtener_token_recuperacion(self, token: str) -> TokenRecuperacion | None:
        """Obtiene un token de recuperacion por su valor."""

    def restablecer_contrasena(
        self,
        usuario_id: int,
        token_id: int,
        nuevo_hash: str,
        momento: str,
    ) -> None:
        """Actualiza la contrasena y consume el token en una sola transaccion."""

    def actualizar_hash_usuario(
        self,
        usuario_id: int,
        nuevo_hash: str,
        momento: str,
    ) -> None:
        """Actualiza el hash de contrasena de un usuario."""


class RepositorioAutenticacionSQLite:
    """Implementacion SQLite para el modulo de autenticacion."""

    def __init__(self, gestor_base_datos: GestorBaseDatos) -> None:
        self._gestor_base_datos = gestor_base_datos

    def obtener_usuario_por_nombre_usuario(
        self,
        nombre_usuario: str,
    ) -> UsuarioRegistroAutenticacion | None:
        consulta = """
            SELECT
                id,
                nombre_usuario,
                nombre_completo,
                correo,
                estado,
                contrasena_hash
            FROM usuarios
            WHERE lower(nombre_usuario) = lower(?)
              AND eliminado_en IS NULL
            LIMIT 1;
        """
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            fila = conexion.execute(consulta, (nombre_usuario,)).fetchone()
        return self._fila_a_usuario(fila)

    def obtener_usuario_por_correo(self, correo: str) -> UsuarioRegistroAutenticacion | None:
        consulta = """
            SELECT
                id,
                nombre_usuario,
                nombre_completo,
                correo,
                estado,
                contrasena_hash
            FROM usuarios
            WHERE lower(correo) = lower(?)
              AND eliminado_en IS NULL
            LIMIT 1;
        """
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            fila = conexion.execute(consulta, (correo,)).fetchone()
        return self._fila_a_usuario(fila)

    def registrar_intento_login(
        self,
        nombre_usuario: str,
        exito: bool,
        usuario_id: int | None = None,
        ip_origen: str | None = None,
    ) -> None:
        consulta = """
            INSERT INTO intentos_login(usuario_id, nombre_usuario, exito, ip_origen)
            VALUES (?, ?, ?, ?);
        """
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            with conexion:
                conexion.execute(
                    consulta,
                    (usuario_id, nombre_usuario, int(exito), ip_origen),
                )

    def crear_sesion(
        self,
        usuario_id: int,
        token_sesion: str,
        expira_en: str,
        ip_origen: str | None = None,
    ) -> None:
        consulta = """
            INSERT INTO sesiones(usuario_id, token_sesion, expira_en, ip_origen)
            VALUES (?, ?, ?, ?);
        """
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            with conexion:
                conexion.execute(
                    consulta,
                    (usuario_id, token_sesion, expira_en, ip_origen),
                )

    def actualizar_ultimo_acceso(self, usuario_id: int, momento: str) -> None:
        consulta = """
            UPDATE usuarios
            SET ultimo_acceso_en = ?, actualizado_en = ?
            WHERE id = ?;
        """
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            with conexion:
                conexion.execute(consulta, (momento, momento, usuario_id))

    def crear_token_recuperacion(
        self,
        usuario_id: int,
        token: str,
        expira_en: str,
    ) -> TokenRecuperacion:
        consulta = """
            INSERT INTO tokens_recuperacion_contrasena(usuario_id, token, expira_en)
            VALUES (?, ?, ?);
        """
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            with conexion:
                cursor = conexion.execute(consulta, (usuario_id, token, expira_en))
                identificador = int(cursor.lastrowid)
        return TokenRecuperacion(
            identificador=identificador,
            usuario_id=usuario_id,
            token=token,
            expira_en=expira_en,
            usado_en=None,
        )

    def obtener_token_recuperacion(self, token: str) -> TokenRecuperacion | None:
        consulta = """
            SELECT id, usuario_id, token, expira_en, usado_en
            FROM tokens_recuperacion_contrasena
            WHERE token = ?
            LIMIT 1;
        """
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            fila = conexion.execute(consulta, (token,)).fetchone()
        return self._fila_a_token(fila)

    def restablecer_contrasena(
        self,
        usuario_id: int,
        token_id: int,
        nuevo_hash: str,
        momento: str,
    ) -> None:
        consulta_actualizar_usuario = """
            UPDATE usuarios
            SET contrasena_hash = ?, ultimo_cambio_contrasena_en = ?, actualizado_en = ?
            WHERE id = ?;
        """
        consulta_consumir_token = """
            UPDATE tokens_recuperacion_contrasena
            SET usado_en = ?
            WHERE id = ?;
        """
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            with conexion:
                conexion.execute(
                    consulta_actualizar_usuario,
                    (nuevo_hash, momento, momento, usuario_id),
                )
                conexion.execute(consulta_consumir_token, (momento, token_id))

    def actualizar_hash_usuario(
        self,
        usuario_id: int,
        nuevo_hash: str,
        momento: str,
    ) -> None:
        consulta = """
            UPDATE usuarios
            SET contrasena_hash = ?, ultimo_cambio_contrasena_en = ?, actualizado_en = ?
            WHERE id = ?;
        """
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            with conexion:
                conexion.execute(consulta, (nuevo_hash, momento, momento, usuario_id))

    @staticmethod
    def _fila_a_usuario(fila: object) -> UsuarioRegistroAutenticacion | None:
        if fila is None:
            return None
        return UsuarioRegistroAutenticacion(
            identificador=int(fila["id"]),
            nombre_usuario=str(fila["nombre_usuario"]),
            nombre_completo=str(fila["nombre_completo"]),
            correo=str(fila["correo"]),
            estado=str(fila["estado"]),
            contrasena_hash=str(fila["contrasena_hash"]),
        )

    @staticmethod
    def _fila_a_token(fila: object) -> TokenRecuperacion | None:
        if fila is None:
            return None
        return TokenRecuperacion(
            identificador=int(fila["id"]),
            usuario_id=int(fila["usuario_id"]),
            token=str(fila["token"]),
            expira_en=str(fila["expira_en"]),
            usado_en=None if fila["usado_en"] is None else str(fila["usado_en"]),
        )
