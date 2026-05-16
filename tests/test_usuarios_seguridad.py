from __future__ import annotations

import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path


RAIZ_PROYECTO = Path(__file__).resolve().parents[1]
RUTA_SRC = RAIZ_PROYECTO / "src"

if str(RUTA_SRC) not in sys.path:
    sys.path.insert(0, str(RUTA_SRC))

from comun.base_datos import GestorBaseDatos  # noqa: E402
from comun.configuracion.gestor_rutas import GestorRutas  # noqa: E402
from modulos.autenticacion.entidades import UsuarioAutenticado  # noqa: E402
from modulos.usuarios.entidades import FormularioRol, FormularioUsuario  # noqa: E402
from modulos.usuarios.repositorio import RepositorioUsuariosSQLite  # noqa: E402
from modulos.usuarios.servicio import ServicioUsuarios  # noqa: E402


class TestUsuariosSeguridad(unittest.TestCase):
    def setUp(self) -> None:
        self.directorio_temporal = tempfile.TemporaryDirectory()
        self.raiz_temporal = Path(self.directorio_temporal.name)
        (self.raiz_temporal / "database" / "migrations").mkdir(parents=True, exist_ok=True)

        for ruta_migracion in (RAIZ_PROYECTO / "database" / "migrations").glob("*.sql"):
            contenido_sql = ruta_migracion.read_text(encoding="utf-8")
            (self.raiz_temporal / "database" / "migrations" / ruta_migracion.name).write_text(
                contenido_sql,
                encoding="utf-8",
            )

        self.gestor_rutas = GestorRutas(raiz_proyecto=self.raiz_temporal)
        self.gestor_base_datos = GestorBaseDatos(self.gestor_rutas)
        self.gestor_base_datos.inicializar_base_datos()
        self.repositorio = RepositorioUsuariosSQLite(self.gestor_base_datos)
        self.servicio = ServicioUsuarios(self.repositorio)

        self._crear_usuario_operativo(
            nombre_usuario="cajero1",
            nombre_completo="Cajero Uno",
            correo="cajero1@sicap.local",
            rol_id=3,
        )

        self.admin = UsuarioAutenticado(
            identificador=self._obtener_id_usuario("admin"),
            nombre_usuario="admin",
            nombre_completo="Administrador del Sistema",
            correo="admin@sicap.local",
            estado="ACTIVO",
            roles=("ADMINISTRADOR",),
            permisos=frozenset(
                {
                    "usuarios.gestionar",
                    "usuarios.restablecer_contrasena",
                    "usuarios.desbloquear",
                }
            ),
        )
        self.superadmin = UsuarioAutenticado(
            identificador=self._obtener_id_usuario("superadmin"),
            nombre_usuario="superadmin",
            nombre_completo="Superadministrador Tecnico",
            correo="superadmin@sicap.local",
            estado="ACTIVO",
            es_tecnico=True,
            es_oculto=True,
            roles=("SUPERADMINISTRADOR",),
            permisos=frozenset(
                {
                    "usuarios.restablecer_contrasena",
                    "usuarios.desbloquear",
                    "mantenimiento.ver",
                    "seguridad.ver_logs",
                }
            ),
        )

    def tearDown(self) -> None:
        self.directorio_temporal.cleanup()

    def test_admin_lista_solo_usuarios_operativos(self) -> None:
        usuarios = self.servicio.listar_usuarios_para_administracion(self.admin)
        nombres = {usuario.nombre_usuario for usuario in usuarios}

        self.assertIn("admin", nombres)
        self.assertIn("cajero1", nombres)
        self.assertNotIn("superadmin", nombres)

    def test_superadmin_puede_ver_usuarios_tecnicos(self) -> None:
        usuarios = self.servicio.listar_usuarios_para_administracion(self.superadmin)
        nombres = {usuario.nombre_usuario for usuario in usuarios}

        self.assertIn("superadmin", nombres)
        self.assertIn("admin", nombres)
        self.assertIn("cajero1", nombres)

    def test_admin_restablece_usuario_operativo_y_se_registra_auditoria(self) -> None:
        resultado = self.servicio.restablecer_contrasena_administrativa(
            actor=self.admin,
            nombre_usuario_objetivo="cajero1",
            nueva_contrasena_temporal="Temporal123!",
            confirmacion_contrasena="Temporal123!",
        )
        self.assertTrue(resultado.exito)

        conexion = sqlite3.connect(self.gestor_rutas.obtener_ruta_base_datos())
        try:
            requiere_cambio, restablecida_por = conexion.execute(
                """
                SELECT requiere_cambio_contrasena, restablecida_por_usuario_id
                FROM usuarios
                WHERE nombre_usuario = 'cajero1';
                """
            ).fetchone()
            total_auditoria = conexion.execute(
                """
                SELECT COUNT(*)
                FROM auditoria
                WHERE accion = 'RESTABLECER_CONTRASENA'
                  AND entidad = 'usuarios';
                """
            ).fetchone()[0]
        finally:
            conexion.close()

        self.assertEqual(requiere_cambio, 1)
        self.assertEqual(restablecida_por, self.admin.identificador)
        self.assertEqual(total_auditoria, 1)

    def test_admin_no_puede_restablecer_superadministrador(self) -> None:
        resultado = self.servicio.restablecer_contrasena_administrativa(
            actor=self.admin,
            nombre_usuario_objetivo="superadmin",
            nueva_contrasena_temporal="Temporal123!",
            confirmacion_contrasena="Temporal123!",
        )
        self.assertFalse(resultado.exito)
        self.assertEqual(resultado.codigo, "PERMISO_DENEGADO")

    def test_admin_puede_desbloquear_usuario_operativo(self) -> None:
        conexion = self.gestor_base_datos.obtener_conexion()
        try:
            with conexion:
                conexion.execute(
                    """
                    UPDATE usuarios
                    SET estado = 'BLOQUEADO', intentos_fallidos = 5
                    WHERE nombre_usuario = 'cajero1';
                    """
                )
        finally:
            conexion.close()

        resultado = self.servicio.desbloquear_usuario_operativo(
            actor=self.admin,
            nombre_usuario_objetivo="cajero1",
        )
        self.assertTrue(resultado.exito)

        conexion = sqlite3.connect(self.gestor_rutas.obtener_ruta_base_datos())
        try:
            estado, intentos = conexion.execute(
                """
                SELECT estado, intentos_fallidos
                FROM usuarios
                WHERE nombre_usuario = 'cajero1';
                """
            ).fetchone()
        finally:
            conexion.close()

        self.assertEqual(estado, "ACTIVO")
        self.assertEqual(intentos, 0)

    def test_admin_puede_crear_usuario_operativo_y_asignar_rol_visible(self) -> None:
        formulario = FormularioUsuario(
            identificador=None,
            nombre_usuario="recepcion1",
            nombre_completo="Recepcion Uno",
            correo="recepcion1@sicap.local",
            estado="ACTIVO",
            rol_id=self._obtener_id_rol("CAJERO"),
            observaciones="Usuario creado en prueba",
            contrasena_temporal="Temporal123!",
            confirmacion_contrasena="Temporal123!",
        )

        resultado = self.servicio.crear_usuario_operativo(self.admin, formulario)

        self.assertTrue(resultado.exito)
        usuario = self.repositorio.obtener_por_nombre_usuario("recepcion1")
        self.assertIsNotNone(usuario)
        self.assertEqual(usuario.rol_principal, "CAJERO")
        self.assertTrue(usuario.requiere_cambio_contrasena)

    def test_admin_puede_actualizar_usuario_operativo(self) -> None:
        usuario = self.repositorio.obtener_por_nombre_usuario("cajero1")
        self.assertIsNotNone(usuario)
        formulario = FormularioUsuario(
            identificador=usuario.identificador,
            nombre_usuario="cajero1",
            nombre_completo="Cajero Uno Actualizado",
            correo="cajero1.actualizado@sicap.local",
            estado="INACTIVO",
            rol_id=self._obtener_id_rol("ADMINISTRADOR"),
            observaciones="Cambio administrativo",
        )

        resultado = self.servicio.actualizar_usuario_operativo(self.admin, formulario)

        self.assertTrue(resultado.exito)
        actualizado = self.repositorio.obtener_por_nombre_usuario("cajero1")
        self.assertIsNotNone(actualizado)
        self.assertEqual(actualizado.nombre_completo, "Cajero Uno Actualizado")
        self.assertEqual(actualizado.correo, "cajero1.actualizado@sicap.local")
        self.assertEqual(actualizado.estado, "INACTIVO")
        self.assertEqual(actualizado.rol_principal, "ADMINISTRADOR")

    def test_admin_puede_exportar_usuarios_filtrados_a_csv(self) -> None:
        ruta_csv = self.raiz_temporal / "usuarios_exportados.csv"

        resultado = self.servicio.exportar_csv(
            str(ruta_csv),
            self.servicio.listar_usuarios_para_administracion(self.admin),
        )

        self.assertTrue(resultado.exito)
        contenido = ruta_csv.read_text(encoding="utf-8")
        self.assertIn("usuario,nombre_completo,correo,rol_principal,estado,ultimo_acceso,creado_en", contenido)
        self.assertIn("admin", contenido)
        self.assertIn("cajero1", contenido)

    def test_servicio_filtra_usuarios_por_busqueda_filtro_rapido_y_rol(self) -> None:
        usuarios = self.servicio.listar_usuarios_para_administracion(self.admin)

        filtrados = self.servicio.filtrar_usuarios(
            usuarios,
            texto="cajero1",
            filtro_rapido="activos",
            rol="cajero",
        )

        self.assertEqual(len(filtrados), 1)
        self.assertEqual(filtrados[0].nombre_usuario, "cajero1")

    def test_admin_puede_crear_rol_operativo_con_permisos_visibles(self) -> None:
        formulario = FormularioRol(
            identificador=None,
            nombre="Supervisor",
            descripcion="Supervisa operaciones generales",
            permisos_codigos=("dashboard.ver", "reportes.generar"),
        )

        resultado = self.servicio.crear_rol_operativo(self.admin, formulario)

        self.assertTrue(resultado.exito)
        roles = self.servicio.listar_roles_para_administracion(self.admin)
        supervisor = next((rol for rol in roles if rol.nombre == "Supervisor"), None)
        self.assertIsNotNone(supervisor)
        self.assertEqual({permiso.codigo for permiso in supervisor.permisos}, {"dashboard.ver", "reportes.generar"})

    def test_admin_puede_actualizar_rol_operativo(self) -> None:
        crear = self.servicio.crear_rol_operativo(
            self.admin,
            FormularioRol(
                identificador=None,
                nombre="Recepcion",
                descripcion="Recepcion inicial",
                permisos_codigos=("dashboard.ver",),
            ),
        )
        self.assertTrue(crear.exito)
        rol = next(
            rol
            for rol in self.servicio.listar_roles_para_administracion(self.admin)
            if rol.nombre == "Recepcion"
        )

        resultado = self.servicio.actualizar_rol_operativo(
            self.admin,
            FormularioRol(
                identificador=rol.identificador,
                nombre="Recepcion",
                descripcion="Recepcion y seguimiento",
                permisos_codigos=("dashboard.ver", "morosidad.ver"),
            ),
        )

        self.assertTrue(resultado.exito)
        actualizado = next(
            item
            for item in self.servicio.listar_roles_para_administracion(self.admin)
            if item.identificador == rol.identificador
        )
        self.assertEqual(actualizado.descripcion, "Recepcion y seguimiento")
        self.assertEqual(
            {permiso.codigo for permiso in actualizado.permisos},
            {"dashboard.ver", "morosidad.ver"},
        )

    def test_no_se_puede_desactivar_rol_con_usuarios_vinculados(self) -> None:
        rol_cajero = next(
            rol
            for rol in self.servicio.listar_roles_para_administracion(self.admin)
            if rol.nombre == "CAJERO"
        )

        resultado = self.servicio.cambiar_estado_rol_operativo(self.admin, rol_cajero.identificador)

        self.assertFalse(resultado.exito)
        self.assertEqual(resultado.codigo, "ROL_CON_USUARIOS")

    def test_se_puede_desactivar_y_reactivar_rol_sin_usuarios_vinculados(self) -> None:
        crear = self.servicio.crear_rol_operativo(
            self.admin,
            FormularioRol(
                identificador=None,
                nombre="Temporal",
                descripcion="Rol temporal",
                permisos_codigos=("dashboard.ver",),
            ),
        )
        self.assertTrue(crear.exito)
        rol = next(
            rol
            for rol in self.servicio.listar_roles_para_administracion(self.admin)
            if rol.nombre == "Temporal"
        )

        desactivar = self.servicio.cambiar_estado_rol_operativo(self.admin, rol.identificador)
        self.assertTrue(desactivar.exito)
        rol_inactivo = next(
            item
            for item in self.servicio.listar_roles_para_administracion(self.admin)
            if item.identificador == rol.identificador
        )
        self.assertEqual(rol_inactivo.estado, "INACTIVO")

        activar = self.servicio.cambiar_estado_rol_operativo(self.admin, rol.identificador)
        self.assertTrue(activar.exito)
        rol_activo = next(
            item
            for item in self.servicio.listar_roles_para_administracion(self.admin)
            if item.identificador == rol.identificador
        )
        self.assertEqual(rol_activo.estado, "ACTIVO")

    def _crear_usuario_operativo(
        self,
        nombre_usuario: str,
        nombre_completo: str,
        correo: str,
        rol_id: int,
    ) -> None:
        conexion = self.gestor_base_datos.obtener_conexion()
        try:
            with conexion:
                conexion.execute(
                    """
                    INSERT INTO usuarios(
                        nombre_usuario,
                        nombre_completo,
                        correo,
                        contrasena_hash,
                        estado,
                        es_tecnico,
                        es_oculto,
                        requiere_cambio_contrasena
                    )
                    VALUES (?, ?, ?, 'CAMBIAR_HASH_EN_DESARROLLO', 'ACTIVO', 0, 0, 0);
                    """,
                    (nombre_usuario, nombre_completo, correo),
                )
                usuario_id = conexion.execute(
                    "SELECT id FROM usuarios WHERE nombre_usuario = ?;",
                    (nombre_usuario,),
                ).fetchone()[0]
                conexion.execute(
                    "INSERT INTO usuarios_roles(usuario_id, rol_id) VALUES (?, ?);",
                    (usuario_id, rol_id),
                )
        finally:
            conexion.close()

    def _obtener_id_usuario(self, nombre_usuario: str) -> int:
        conexion = sqlite3.connect(self.gestor_rutas.obtener_ruta_base_datos())
        try:
            return int(
                conexion.execute(
                    "SELECT id FROM usuarios WHERE nombre_usuario = ?;",
                    (nombre_usuario,),
                ).fetchone()[0]
            )
        finally:
            conexion.close()

    def _obtener_id_rol(self, nombre_rol: str) -> int:
        conexion = sqlite3.connect(self.gestor_rutas.obtener_ruta_base_datos())
        try:
            return int(
                conexion.execute(
                    "SELECT id FROM roles WHERE nombre = ?;",
                    (nombre_rol,),
                ).fetchone()[0]
            )
        finally:
            conexion.close()


if __name__ == "__main__":
    unittest.main()
