"""Contratos e implementacion SQLite del modulo de usuarios."""

from __future__ import annotations

from contextlib import closing
from typing import Protocol

from comun.base_datos import GestorBaseDatos
from modulos.usuarios.entidades import UsuarioSistema


class RepositorioUsuarios(Protocol):
    """Define el acceso persistente requerido por usuarios."""

    def obtener_por_identificador(self, identificador: int) -> UsuarioSistema | None:
        """Obtiene un usuario por su identificador."""

    def obtener_por_nombre_usuario(self, nombre_usuario: str) -> UsuarioSistema | None:
        """Obtiene un usuario por nombre de usuario."""

    def listar_operativos_visibles(self) -> list[UsuarioSistema]:
        """Lista usuarios operativos visibles para administracion normal."""

    def listar_tecnicos(self) -> list[UsuarioSistema]:
        """Lista usuarios tecnicos ocultos."""

    def restablecer_contrasena_administrativa(
        self,
        actor_id: int,
        objetivo_id: int,
        nuevo_hash: str,
        momento: str,
    ) -> None:
        """Aplica un restablecimiento administrativo de contrasena."""

    def desbloquear_usuario(
        self,
        actor_id: int,
        objetivo_id: int,
        momento: str,
    ) -> None:
        """Desbloquea un usuario operativo."""

    def registrar_auditoria(
        self,
        usuario_id: int | None,
        accion: str,
        entidad: str,
        entidad_id: int | None,
        resumen: str,
        datos_antes_json: str | None = None,
        datos_despues_json: str | None = None,
    ) -> None:
        """Registra un evento de auditoria sensible."""


class RepositorioUsuariosSQLite:
    """Implementacion SQLite del modulo de usuarios."""

    def __init__(self, gestor_base_datos: GestorBaseDatos) -> None:
        self._gestor_base_datos = gestor_base_datos

    def obtener_por_identificador(self, identificador: int) -> UsuarioSistema | None:
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            fila = conexion.execute(self._consulta_usuario_detallado(), (identificador,)).fetchone()
        return self._fila_a_usuario(fila)

    def obtener_por_nombre_usuario(self, nombre_usuario: str) -> UsuarioSistema | None:
        consulta = self._consulta_usuario_detallado().replace("u.id = ?", "lower(u.nombre_usuario) = lower(?)")
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            fila = conexion.execute(consulta, (nombre_usuario,)).fetchone()
        return self._fila_a_usuario(fila)

    def listar_operativos_visibles(self) -> list[UsuarioSistema]:
        consulta = """
            SELECT
                u.id,
                u.nombre_usuario,
                u.nombre_completo,
                u.correo,
                u.estado,
                u.es_tecnico,
                u.es_oculto,
                u.requiere_cambio_contrasena,
                u.intentos_fallidos,
                u.bloqueado_hasta,
                GROUP_CONCAT(DISTINCT r.nombre) AS roles_csv,
                GROUP_CONCAT(DISTINCT p.codigo) AS permisos_csv
            FROM usuarios u
            LEFT JOIN usuarios_roles ur ON ur.usuario_id = u.id
            LEFT JOIN roles r ON r.id = ur.rol_id
            LEFT JOIN roles_permisos rp ON rp.rol_id = r.id
            LEFT JOIN permisos p ON p.id = rp.permiso_id
            WHERE u.eliminado_en IS NULL
              AND u.es_oculto = 0
              AND u.es_tecnico = 0
            GROUP BY
                u.id,
                u.nombre_usuario,
                u.nombre_completo,
                u.correo,
                u.estado,
                u.es_tecnico,
                u.es_oculto,
                u.requiere_cambio_contrasena,
                u.intentos_fallidos,
                u.bloqueado_hasta
            ORDER BY lower(u.nombre_usuario);
        """
        return self._ejecutar_consulta_usuarios(consulta)

    def listar_tecnicos(self) -> list[UsuarioSistema]:
        consulta = """
            SELECT
                u.id,
                u.nombre_usuario,
                u.nombre_completo,
                u.correo,
                u.estado,
                u.es_tecnico,
                u.es_oculto,
                u.requiere_cambio_contrasena,
                u.intentos_fallidos,
                u.bloqueado_hasta,
                GROUP_CONCAT(DISTINCT r.nombre) AS roles_csv,
                GROUP_CONCAT(DISTINCT p.codigo) AS permisos_csv
            FROM usuarios u
            LEFT JOIN usuarios_roles ur ON ur.usuario_id = u.id
            LEFT JOIN roles r ON r.id = ur.rol_id
            LEFT JOIN roles_permisos rp ON rp.rol_id = r.id
            LEFT JOIN permisos p ON p.id = rp.permiso_id
            WHERE u.eliminado_en IS NULL
              AND (u.es_oculto = 1 OR u.es_tecnico = 1)
            GROUP BY
                u.id,
                u.nombre_usuario,
                u.nombre_completo,
                u.correo,
                u.estado,
                u.es_tecnico,
                u.es_oculto,
                u.requiere_cambio_contrasena,
                u.intentos_fallidos,
                u.bloqueado_hasta
            ORDER BY lower(u.nombre_usuario);
        """
        return self._ejecutar_consulta_usuarios(consulta)

    def restablecer_contrasena_administrativa(
        self,
        actor_id: int,
        objetivo_id: int,
        nuevo_hash: str,
        momento: str,
    ) -> None:
        consulta = """
            UPDATE usuarios
            SET contrasena_hash = ?,
                ultimo_cambio_contrasena_en = ?,
                requiere_cambio_contrasena = 1,
                intentos_fallidos = 0,
                bloqueado_hasta = NULL,
                estado = 'ACTIVO',
                fecha_restablecimiento_contrasena = ?,
                restablecida_por_usuario_id = ?,
                actualizado_en = ?,
                actualizado_por = ?
            WHERE id = ?;
        """
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            with conexion:
                conexion.execute(
                    consulta,
                    (
                        nuevo_hash,
                        momento,
                        momento,
                        actor_id,
                        momento,
                        actor_id,
                        objetivo_id,
                    ),
                )

    def desbloquear_usuario(
        self,
        actor_id: int,
        objetivo_id: int,
        momento: str,
    ) -> None:
        consulta = """
            UPDATE usuarios
            SET estado = 'ACTIVO',
                intentos_fallidos = 0,
                bloqueado_hasta = NULL,
                actualizado_en = ?,
                actualizado_por = ?
            WHERE id = ?;
        """
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            with conexion:
                conexion.execute(consulta, (momento, actor_id, objetivo_id))

    def registrar_auditoria(
        self,
        usuario_id: int | None,
        accion: str,
        entidad: str,
        entidad_id: int | None,
        resumen: str,
        datos_antes_json: str | None = None,
        datos_despues_json: str | None = None,
    ) -> None:
        consulta = """
            INSERT INTO auditoria(
                usuario_id,
                accion,
                entidad,
                entidad_id,
                resumen,
                datos_antes_json,
                datos_despues_json,
                fecha_evento
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'));
        """
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            with conexion:
                conexion.execute(
                    consulta,
                    (
                        usuario_id,
                        accion,
                        entidad,
                        entidad_id,
                        resumen,
                        datos_antes_json,
                        datos_despues_json,
                    ),
                )

    def _ejecutar_consulta_usuarios(self, consulta: str) -> list[UsuarioSistema]:
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            filas = conexion.execute(consulta).fetchall()
        return [usuario for fila in filas if (usuario := self._fila_a_usuario(fila)) is not None]

    @staticmethod
    def _consulta_usuario_detallado() -> str:
        return """
            SELECT
                u.id,
                u.nombre_usuario,
                u.nombre_completo,
                u.correo,
                u.estado,
                u.es_tecnico,
                u.es_oculto,
                u.requiere_cambio_contrasena,
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
                u.es_tecnico,
                u.es_oculto,
                u.requiere_cambio_contrasena,
                u.intentos_fallidos,
                u.bloqueado_hasta
            LIMIT 1;
        """

    @staticmethod
    def _fila_a_usuario(fila: object) -> UsuarioSistema | None:
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
        return UsuarioSistema(
            identificador=int(fila["id"]),
            nombre_usuario=str(fila["nombre_usuario"]),
            nombre_completo=str(fila["nombre_completo"]),
            correo=str(fila["correo"]),
            estado=str(fila["estado"]),
            es_tecnico=bool(fila["es_tecnico"]),
            es_oculto=bool(fila["es_oculto"]),
            requiere_cambio_contrasena=bool(fila["requiere_cambio_contrasena"]),
            intentos_fallidos=int(fila["intentos_fallidos"] or 0),
            bloqueado_hasta=fila["bloqueado_hasta"],
            roles=roles,
            permisos=permisos,
        )

