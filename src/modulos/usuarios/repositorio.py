"""Contratos e implementacion SQLite del modulo de usuarios."""

from __future__ import annotations

from contextlib import closing
from typing import Protocol

from comun.base_datos import GestorBaseDatos
from modulos.usuarios.entidades import (
    FormularioRol,
    FormularioUsuario,
    PermisoSistema,
    RolSistema,
    UsuarioSistema,
)


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

    def listar_roles_operativos(self) -> list[RolSistema]:
        """Lista roles visibles en el modulo de usuarios."""

    def listar_permisos_operativos(self) -> list[PermisoSistema]:
        """Lista permisos visibles para construir roles operativos."""

    def obtener_rol_operativo_por_identificador(self, identificador: int) -> RolSistema | None:
        """Obtiene un rol visible por identificador."""

    def crear_rol_operativo(
        self,
        actor_id: int,
        formulario: FormularioRol,
        momento: str,
    ) -> None:
        """Crea un rol operativo y sincroniza sus permisos."""

    def actualizar_rol_operativo(
        self,
        actor_id: int,
        formulario: FormularioRol,
        momento: str,
    ) -> None:
        """Actualiza un rol operativo y sincroniza sus permisos."""

    def cambiar_estado_rol_operativo(
        self,
        actor_id: int,
        rol_id: int,
        nuevo_estado: str,
        momento: str,
    ) -> None:
        """Actualiza el estado visible de un rol operativo."""

    def crear_usuario_operativo(
        self,
        actor_id: int,
        formulario: FormularioUsuario,
        nuevo_hash: str,
        momento: str,
    ) -> None:
        """Crea un usuario operativo y asigna su rol principal."""

    def actualizar_usuario_operativo(
        self,
        actor_id: int,
        formulario: FormularioUsuario,
        momento: str,
    ) -> None:
        """Actualiza un usuario operativo y sincroniza su rol principal."""

    def cambiar_estado_usuario(
        self,
        actor_id: int,
        objetivo_id: int,
        nuevo_estado: str,
        momento: str,
    ) -> None:
        """Actualiza el estado operativo del usuario."""

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
                u.ultimo_acceso_en,
                u.creado_en,
                u.actualizado_en,
                COALESCE(uc.nombre_completo, uc.nombre_usuario, '') AS creado_por_nombre,
                COALESCE(uu.nombre_completo, uu.nombre_usuario, '') AS actualizado_por_nombre,
                COALESCE(u.observaciones, '') AS observaciones,
                GROUP_CONCAT(DISTINCT r.nombre) AS roles_csv,
                GROUP_CONCAT(DISTINCT p.codigo) AS permisos_csv,
                COUNT(DISTINCT s.id) AS total_sesiones
            FROM usuarios u
            LEFT JOIN usuarios uc ON uc.id = u.creado_por
            LEFT JOIN usuarios uu ON uu.id = u.actualizado_por
            LEFT JOIN usuarios_roles ur ON ur.usuario_id = u.id
            LEFT JOIN roles r ON r.id = ur.rol_id
            LEFT JOIN roles_permisos rp ON rp.rol_id = r.id
            LEFT JOIN permisos p ON p.id = rp.permiso_id
            LEFT JOIN sesiones s ON s.usuario_id = u.id
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
                u.bloqueado_hasta,
                u.ultimo_acceso_en,
                u.creado_en,
                u.actualizado_en,
                creado_por_nombre,
                actualizado_por_nombre,
                u.observaciones
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
                u.ultimo_acceso_en,
                u.creado_en,
                u.actualizado_en,
                COALESCE(uc.nombre_completo, uc.nombre_usuario, '') AS creado_por_nombre,
                COALESCE(uu.nombre_completo, uu.nombre_usuario, '') AS actualizado_por_nombre,
                COALESCE(u.observaciones, '') AS observaciones,
                GROUP_CONCAT(DISTINCT r.nombre) AS roles_csv,
                GROUP_CONCAT(DISTINCT p.codigo) AS permisos_csv,
                COUNT(DISTINCT s.id) AS total_sesiones
            FROM usuarios u
            LEFT JOIN usuarios uc ON uc.id = u.creado_por
            LEFT JOIN usuarios uu ON uu.id = u.actualizado_por
            LEFT JOIN usuarios_roles ur ON ur.usuario_id = u.id
            LEFT JOIN roles r ON r.id = ur.rol_id
            LEFT JOIN roles_permisos rp ON rp.rol_id = r.id
            LEFT JOIN permisos p ON p.id = rp.permiso_id
            LEFT JOIN sesiones s ON s.usuario_id = u.id
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
                u.bloqueado_hasta,
                u.ultimo_acceso_en,
                u.creado_en,
                u.actualizado_en,
                creado_por_nombre,
                actualizado_por_nombre,
                u.observaciones
            ORDER BY lower(u.nombre_usuario);
        """
        return self._ejecutar_consulta_usuarios(consulta)

    def listar_roles_operativos(self) -> list[RolSistema]:
        consulta_roles = """
            SELECT
                r.id,
                r.nombre,
                COALESCE(r.descripcion, '') AS descripcion,
                r.estado,
                r.es_sistema,
                COUNT(DISTINCT ur.usuario_id) AS total_usuarios
            FROM roles r
            LEFT JOIN usuarios_roles ur ON ur.rol_id = r.id
            LEFT JOIN usuarios u ON u.id = ur.usuario_id AND u.eliminado_en IS NULL
            WHERE lower(r.nombre) <> 'superadministrador'
            GROUP BY r.id, r.nombre, r.descripcion, r.estado, r.es_sistema
            ORDER BY r.es_sistema DESC, lower(r.nombre);
        """
        consulta_permisos = """
            SELECT
                rp.rol_id,
                p.codigo,
                p.nombre,
                COALESCE(p.descripcion, '') AS descripcion,
                p.modulo
            FROM roles_permisos rp
            INNER JOIN permisos p ON p.id = rp.permiso_id
            INNER JOIN roles r ON r.id = rp.rol_id
            WHERE lower(r.nombre) <> 'superadministrador'
            ORDER BY rp.rol_id, lower(p.modulo), lower(p.codigo);
        """
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            filas_roles = conexion.execute(consulta_roles).fetchall()
            filas_permisos = conexion.execute(consulta_permisos).fetchall()

        permisos_por_rol: dict[int, list[PermisoSistema]] = {}
        for fila in filas_permisos:
            rol_id = int(fila["rol_id"])
            permisos_por_rol.setdefault(rol_id, []).append(
                PermisoSistema(
                    codigo=str(fila["codigo"]),
                    nombre=str(fila["nombre"]),
                    descripcion=str(fila["descripcion"]),
                    modulo=str(fila["modulo"]),
                )
            )

        return [
            RolSistema(
                identificador=int(fila["id"]),
                nombre=str(fila["nombre"]),
                descripcion=str(fila["descripcion"]),
                estado=str(fila["estado"]),
                es_sistema=bool(fila["es_sistema"]),
                total_usuarios=int(fila["total_usuarios"] or 0),
                permisos=tuple(permisos_por_rol.get(int(fila["id"]), [])),
            )
            for fila in filas_roles
        ]

    def listar_permisos_operativos(self) -> list[PermisoSistema]:
        consulta = """
            SELECT
                p.codigo,
                p.nombre,
                COALESCE(p.descripcion, '') AS descripcion,
                p.modulo
            FROM permisos p
            WHERE lower(p.modulo) NOT IN ('mantenimiento', 'seguridad')
            ORDER BY lower(p.modulo), lower(p.codigo);
        """
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            filas = conexion.execute(consulta).fetchall()
        return [
            PermisoSistema(
                codigo=str(fila["codigo"]),
                nombre=str(fila["nombre"]),
                descripcion=str(fila["descripcion"]),
                modulo=str(fila["modulo"]),
            )
            for fila in filas
        ]

    def obtener_rol_operativo_por_identificador(self, identificador: int) -> RolSistema | None:
        roles = self.listar_roles_operativos()
        return next((rol for rol in roles if rol.identificador == identificador), None)

    def crear_rol_operativo(
        self,
        actor_id: int,
        formulario: FormularioRol,
        momento: str,
    ) -> None:
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            with conexion:
                cursor = conexion.execute(
                    """
                    INSERT INTO roles(
                        nombre,
                        descripcion,
                        es_sistema,
                        estado,
                        creado_en,
                        actualizado_en
                    )
                    VALUES (?, ?, 0, 'ACTIVO', ?, ?);
                    """,
                    (
                        formulario.nombre,
                        formulario.descripcion,
                        momento,
                        momento,
                    ),
                )
                rol_id = int(cursor.lastrowid)
                self._sincronizar_permisos_rol(conexion, rol_id, formulario.permisos_codigos)

    def actualizar_rol_operativo(
        self,
        actor_id: int,
        formulario: FormularioRol,
        momento: str,
    ) -> None:
        if formulario.identificador is None:
            raise ValueError("Se requiere el identificador del rol.")
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            with conexion:
                conexion.execute(
                    """
                    UPDATE roles
                    SET nombre = ?,
                        descripcion = ?,
                        actualizado_en = ?
                    WHERE id = ?;
                    """,
                    (
                        formulario.nombre,
                        formulario.descripcion,
                        momento,
                        formulario.identificador,
                    ),
                )
                self._sincronizar_permisos_rol(
                    conexion,
                    formulario.identificador,
                    formulario.permisos_codigos,
                )

    def cambiar_estado_rol_operativo(
        self,
        actor_id: int,
        rol_id: int,
        nuevo_estado: str,
        momento: str,
    ) -> None:
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            with conexion:
                conexion.execute(
                    """
                    UPDATE roles
                    SET estado = ?,
                        actualizado_en = ?
                    WHERE id = ?;
                    """,
                    (nuevo_estado, momento, rol_id),
                )

    def crear_usuario_operativo(
        self,
        actor_id: int,
        formulario: FormularioUsuario,
        nuevo_hash: str,
        momento: str,
    ) -> None:
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            with conexion:
                cursor = conexion.execute(
                    """
                    INSERT INTO usuarios(
                        nombre_usuario,
                        nombre_completo,
                        correo,
                        contrasena_hash,
                        estado,
                        observaciones,
                        requiere_cambio_contrasena,
                        creado_en,
                        actualizado_en,
                        creado_por,
                        actualizado_por
                    )
                    VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?);
                    """,
                    (
                        formulario.nombre_usuario,
                        formulario.nombre_completo,
                        formulario.correo,
                        nuevo_hash,
                        formulario.estado,
                        formulario.observaciones,
                        momento,
                        momento,
                        actor_id,
                        actor_id,
                    ),
                )
                usuario_id = int(cursor.lastrowid)
                conexion.execute(
                    "INSERT INTO usuarios_roles(usuario_id, rol_id) VALUES (?, ?);",
                    (usuario_id, formulario.rol_id),
                )

    def actualizar_usuario_operativo(
        self,
        actor_id: int,
        formulario: FormularioUsuario,
        momento: str,
    ) -> None:
        if formulario.identificador is None:
            raise ValueError("Se requiere el identificador del usuario.")
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            with conexion:
                conexion.execute(
                    """
                    UPDATE usuarios
                    SET nombre_usuario = ?,
                        nombre_completo = ?,
                        correo = ?,
                        estado = ?,
                        observaciones = ?,
                        actualizado_en = ?,
                        actualizado_por = ?
                    WHERE id = ?;
                    """,
                    (
                        formulario.nombre_usuario,
                        formulario.nombre_completo,
                        formulario.correo,
                        formulario.estado,
                        formulario.observaciones,
                        momento,
                        actor_id,
                        formulario.identificador,
                    ),
                )
                conexion.execute(
                    "DELETE FROM usuarios_roles WHERE usuario_id = ?;",
                    (formulario.identificador,),
                )
                conexion.execute(
                    "INSERT INTO usuarios_roles(usuario_id, rol_id) VALUES (?, ?);",
                    (formulario.identificador, formulario.rol_id),
                )

    def cambiar_estado_usuario(
        self,
        actor_id: int,
        objetivo_id: int,
        nuevo_estado: str,
        momento: str,
    ) -> None:
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            with conexion:
                conexion.execute(
                    """
                    UPDATE usuarios
                    SET estado = ?,
                        actualizado_en = ?,
                        actualizado_por = ?
                    WHERE id = ?;
                    """,
                    (nuevo_estado, momento, actor_id, objetivo_id),
                )

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
            VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now', 'localtime'));
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
    def _sincronizar_permisos_rol(
        conexion: object,
        rol_id: int,
        permisos_codigos: tuple[str, ...],
    ) -> None:
        conexion.execute("DELETE FROM roles_permisos WHERE rol_id = ?;", (rol_id,))
        for codigo in permisos_codigos:
            conexion.execute(
                """
                INSERT INTO roles_permisos(rol_id, permiso_id)
                SELECT ?, id
                FROM permisos
                WHERE codigo = ?;
                """,
                (rol_id, codigo),
            )

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
                u.ultimo_acceso_en,
                u.creado_en,
                u.actualizado_en,
                COALESCE(uc.nombre_completo, uc.nombre_usuario, '') AS creado_por_nombre,
                COALESCE(uu.nombre_completo, uu.nombre_usuario, '') AS actualizado_por_nombre,
                COALESCE(u.observaciones, '') AS observaciones,
                GROUP_CONCAT(DISTINCT r.nombre) AS roles_csv,
                GROUP_CONCAT(DISTINCT p.codigo) AS permisos_csv,
                COUNT(DISTINCT s.id) AS total_sesiones
            FROM usuarios u
            LEFT JOIN usuarios uc ON uc.id = u.creado_por
            LEFT JOIN usuarios uu ON uu.id = u.actualizado_por
            LEFT JOIN usuarios_roles ur ON ur.usuario_id = u.id
            LEFT JOIN roles r ON r.id = ur.rol_id
            LEFT JOIN roles_permisos rp ON rp.rol_id = r.id
            LEFT JOIN permisos p ON p.id = rp.permiso_id
            LEFT JOIN sesiones s ON s.usuario_id = u.id
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
                u.bloqueado_hasta,
                u.ultimo_acceso_en,
                u.creado_en,
                u.actualizado_en,
                creado_por_nombre,
                actualizado_por_nombre,
                u.observaciones
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
            ultimo_acceso_en=str(fila["ultimo_acceso_en"]) if fila["ultimo_acceso_en"] else None,
            creado_en=str(fila["creado_en"]) if fila["creado_en"] else None,
            actualizado_en=str(fila["actualizado_en"]) if fila["actualizado_en"] else None,
            creado_por_nombre=str(fila["creado_por_nombre"] or ""),
            actualizado_por_nombre=str(fila["actualizado_por_nombre"] or ""),
            observaciones=str(fila["observaciones"] or ""),
            total_sesiones=int(fila["total_sesiones"] or 0),
        )

