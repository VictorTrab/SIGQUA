"""Persistencia SQLite para el modulo de autenticacion."""

from __future__ import annotations

from contextlib import closing
from typing import Protocol

from comun.base_datos import GestorBaseDatos
from modulos.autenticacion.entidades import UsuarioRegistroAutenticacion


class RepositorioAutenticacion(Protocol):
    """Define el acceso persistente requerido por autenticacion."""

    def obtener_usuario_por_nombre_usuario(
        self,
        nombre_usuario: str,
    ) -> UsuarioRegistroAutenticacion | None:
        """Obtiene un usuario por nombre de usuario."""

    def obtener_usuario_por_id(
        self,
        identificador: int,
    ) -> UsuarioRegistroAutenticacion | None:
        """Obtiene un usuario por identificador."""

    def registrar_intento_login(
        self,
        identificador: str,
        resultado: str,
        usuario_id: int | None = None,
        motivo: str | None = None,
        equipo: str | None = None,
    ) -> None:
        """Registra un intento de login."""

    def crear_sesion(
        self,
        usuario_id: int,
        token_sesion_hash: str,
        expira_en: str | None,
        equipo: str | None = None,
    ) -> None:
        """Crea una sesion persistida."""

    def actualizar_ultimo_acceso(self, usuario_id: int, momento: str) -> None:
        """Actualiza el ultimo acceso del usuario."""

    def reiniciar_intentos_fallidos(self, usuario_id: int, momento: str) -> None:
        """Limpia el contador de intentos fallidos tras un login correcto."""

    def incrementar_intentos_fallidos(self, usuario_id: int, momento: str) -> int:
        """Incrementa y devuelve el total de intentos fallidos."""

    def bloquear_usuario(
        self,
        usuario_id: int,
        momento: str,
        bloqueado_hasta: str | None = None,
    ) -> None:
        """Bloquea un usuario por politicas de seguridad."""

    def finalizar_sesion(self, token_sesion_hash: str, momento: str) -> None:
        """Marca una sesion como finalizada."""

    def actualizar_contrasena_usuario(
        self,
        usuario_id: int,
        nuevo_hash: str,
        momento: str,
        requiere_cambio_contrasena: bool = False,
        contrasena_temporal_expira_en: str | None = None,
        restablecida_por_usuario_id: int | None = None,
        fecha_restablecimiento: str | None = None,
    ) -> None:
        """Actualiza el hash de contrasena y sus banderas asociadas."""


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
                u.id,
                u.nombre_usuario,
                u.nombre_completo,
                u.correo,
                u.estado,
                u.contrasena_hash,
                u.es_tecnico,
                u.es_oculto,
                u.requiere_cambio_contrasena,
                u.contrasena_temporal_expira_en,
                u.intentos_fallidos,
                u.bloqueado_hasta,
                GROUP_CONCAT(DISTINCT r.nombre) AS roles_csv,
                GROUP_CONCAT(DISTINCT p.codigo) AS permisos_csv
            FROM usuarios u
            LEFT JOIN usuarios_roles ur ON ur.usuario_id = u.id
            LEFT JOIN roles r ON r.id = ur.rol_id
            LEFT JOIN roles_permisos rp ON rp.rol_id = r.id
            LEFT JOIN permisos p ON p.id = rp.permiso_id
            WHERE lower(u.nombre_usuario) = lower(?)
              AND u.eliminado_en IS NULL
            GROUP BY
                u.id,
                u.nombre_usuario,
                u.nombre_completo,
                u.correo,
                u.estado,
                u.contrasena_hash,
                u.es_tecnico,
                u.es_oculto,
                u.requiere_cambio_contrasena,
                u.contrasena_temporal_expira_en,
                u.intentos_fallidos,
                u.bloqueado_hasta
            LIMIT 1;
        """
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            fila = conexion.execute(consulta, (nombre_usuario,)).fetchone()
        return self._fila_a_usuario(fila)

    def obtener_usuario_por_id(
        self,
        identificador: int,
    ) -> UsuarioRegistroAutenticacion | None:
        consulta = """
            SELECT
                u.id,
                u.nombre_usuario,
                u.nombre_completo,
                u.correo,
                u.estado,
                u.contrasena_hash,
                u.es_tecnico,
                u.es_oculto,
                u.requiere_cambio_contrasena,
                u.contrasena_temporal_expira_en,
                u.intentos_fallidos,
                u.bloqueado_hasta,
                GROUP_CONCAT(DISTINCT r.nombre) AS roles_csv,
                GROUP_CONCAT(DISTINCT p.codigo) AS permisos_csv
            FROM usuarios u
            LEFT JOIN usuarios_roles ur ON ur.usuario_id = u.id
            LEFT JOIN roles r ON r.id = ur.rol_id
            LEFT JOIN roles_permisos rp ON rp.rol_id = r.id
            LEFT JOIN permisos p ON p.id = rp.permiso_id
            WHERE u.id = ?
              AND u.eliminado_en IS NULL
            GROUP BY
                u.id,
                u.nombre_usuario,
                u.nombre_completo,
                u.correo,
                u.estado,
                u.contrasena_hash,
                u.es_tecnico,
                u.es_oculto,
                u.requiere_cambio_contrasena,
                u.contrasena_temporal_expira_en,
                u.intentos_fallidos,
                u.bloqueado_hasta
            LIMIT 1;
        """
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            fila = conexion.execute(consulta, (identificador,)).fetchone()
        return self._fila_a_usuario(fila)

    def registrar_intento_login(
        self,
        identificador: str,
        resultado: str,
        usuario_id: int | None = None,
        motivo: str | None = None,
        equipo: str | None = None,
    ) -> None:
        consulta = """
            INSERT INTO intentos_login(usuario_o_correo, usuario_id, resultado, motivo, equipo)
            VALUES (?, ?, ?, ?, ?);
        """
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            with conexion:
                conexion.execute(
                    consulta,
                    (identificador, usuario_id, resultado, motivo, equipo),
                )

    def crear_sesion(
        self,
        usuario_id: int,
        token_sesion_hash: str,
        expira_en: str | None,
        equipo: str | None = None,
    ) -> None:
        consulta = """
            INSERT INTO sesiones(usuario_id, token_sesion_hash, expira_en, equipo, estado)
            VALUES (?, ?, ?, ?, 'ACTIVA');
        """
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            with conexion:
                conexion.execute(
                    consulta,
                    (usuario_id, token_sesion_hash, expira_en, equipo),
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

    def reiniciar_intentos_fallidos(self, usuario_id: int, momento: str) -> None:
        consulta = """
            UPDATE usuarios
            SET intentos_fallidos = 0,
                bloqueado_hasta = NULL,
                actualizado_en = ?
            WHERE id = ?;
        """
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            with conexion:
                conexion.execute(consulta, (momento, usuario_id))

    def incrementar_intentos_fallidos(self, usuario_id: int, momento: str) -> int:
        consulta_actualizacion = """
            UPDATE usuarios
            SET intentos_fallidos = intentos_fallidos + 1,
                actualizado_en = ?
            WHERE id = ?;
        """
        consulta_total = """
            SELECT intentos_fallidos
            FROM usuarios
            WHERE id = ?;
        """
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            with conexion:
                conexion.execute(consulta_actualizacion, (momento, usuario_id))
                fila = conexion.execute(consulta_total, (usuario_id,)).fetchone()
        return int(fila["intentos_fallidos"]) if fila is not None else 0

    def bloquear_usuario(
        self,
        usuario_id: int,
        momento: str,
        bloqueado_hasta: str | None = None,
    ) -> None:
        consulta = """
            UPDATE usuarios
            SET estado = 'BLOQUEADO',
                bloqueado_hasta = ?,
                actualizado_en = ?
            WHERE id = ?;
        """
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            with conexion:
                conexion.execute(consulta, (bloqueado_hasta, momento, usuario_id))

    def finalizar_sesion(self, token_sesion_hash: str, momento: str) -> None:
        consulta = """
            UPDATE sesiones
            SET cerrado_en = ?, estado = 'CERRADA'
            WHERE token_sesion_hash = ?
              AND estado = 'ACTIVA';
        """
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            with conexion:
                conexion.execute(consulta, (momento, token_sesion_hash))

    def actualizar_contrasena_usuario(
        self,
        usuario_id: int,
        nuevo_hash: str,
        momento: str,
        requiere_cambio_contrasena: bool = False,
        contrasena_temporal_expira_en: str | None = None,
        restablecida_por_usuario_id: int | None = None,
        fecha_restablecimiento: str | None = None,
    ) -> None:
        consulta = """
            UPDATE usuarios
            SET contrasena_hash = ?,
                ultimo_cambio_contrasena_en = ?,
                requiere_cambio_contrasena = ?,
                contrasena_temporal_expira_en = ?,
                restablecida_por_usuario_id = ?,
                fecha_restablecimiento_contrasena = ?,
                intentos_fallidos = 0,
                bloqueado_hasta = NULL,
                actualizado_en = ?
            WHERE id = ?;
        """
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            with conexion:
                conexion.execute(
                    consulta,
                    (
                        nuevo_hash,
                        momento,
                        int(requiere_cambio_contrasena),
                        contrasena_temporal_expira_en,
                        restablecida_por_usuario_id,
                        fecha_restablecimiento,
                        momento,
                        usuario_id,
                    ),
                )

    @staticmethod
    def _fila_a_usuario(fila: object) -> UsuarioRegistroAutenticacion | None:
        if fila is None:
            return None
        roles = tuple(
            rol.strip()
            for rol in str(fila["roles_csv"] or "").split(",")
            if rol and rol.strip()
        )
        permisos = frozenset(
            permiso.strip()
            for permiso in str(fila["permisos_csv"] or "").split(",")
            if permiso and permiso.strip()
        )
        return UsuarioRegistroAutenticacion(
            identificador=int(fila["id"]),
            nombre_usuario=str(fila["nombre_usuario"]),
            nombre_completo=str(fila["nombre_completo"]),
            correo=str(fila["correo"]),
            estado=str(fila["estado"]),
            contrasena_hash=str(fila["contrasena_hash"]),
            es_tecnico=bool(fila["es_tecnico"]),
            es_oculto=bool(fila["es_oculto"]),
            requiere_cambio_contrasena=bool(fila["requiere_cambio_contrasena"]),
            contrasena_temporal_expira_en=(
                str(fila["contrasena_temporal_expira_en"])
                if fila["contrasena_temporal_expira_en"]
                else None
            ),
            intentos_fallidos=int(fila["intentos_fallidos"] or 0),
            bloqueado_hasta=fila["bloqueado_hasta"],
            roles=roles,
            permisos=permisos,
        )
