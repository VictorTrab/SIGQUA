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
from modulos.usuarios.entidades import FormularioUsuario  # noqa: E402
from modulos.usuarios.repositorio import RepositorioUsuariosSQLite  # noqa: E402
from modulos.usuarios.servicio import ServicioUsuarios  # noqa: E402


class TestUsuariosSeguridad(unittest.TestCase):
    def setUp(self) -> None:
        self.directorio_temporal = tempfile.TemporaryDirectory()
        self.raiz_temporal = Path(self.directorio_temporal.name)
        self._copiar_migraciones(self.raiz_temporal)

        self.gestor_rutas = GestorRutas(raiz_proyecto=self.raiz_temporal)
        self.gestor_base_datos = GestorBaseDatos(self.gestor_rutas)
        self.gestor_base_datos.inicializar_base_datos(incluir_datos_prueba=True)
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
            permisos=frozenset({"modulo.usuarios"}),
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
            permisos=frozenset({"mantenimiento.ver"}),
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

    def test_roles_asignables_solo_muestran_roles_fijos_visibles(self) -> None:
        roles = self.servicio.listar_roles_asignables(self.admin)
        self.assertEqual([rol.nombre for rol in roles], ["ADMINISTRADOR", "CAJERO", "CONSULTA"])

    def test_admin_restablece_usuario_operativo_y_se_registra_auditoria(self) -> None:
        resultado = self.servicio.restablecer_contrasena_administrativa(
            actor=self.admin,
            nombre_usuario_objetivo="cajero1",
        )
        self.assertTrue(resultado.exito)
        self.assertTrue(resultado.contrasena_temporal_generada)
        self.assertIsNotNone(resultado.contrasena_temporal_expira_en)

        conexion = sqlite3.connect(self.gestor_rutas.obtener_ruta_base_datos())
        try:
            requiere_cambio, restablecida_por, expira_en = conexion.execute(
                """
                SELECT requiere_cambio_contrasena, restablecida_por_usuario_id, contrasena_temporal_expira_en
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
        self.assertIsNotNone(expira_en)
        self.assertGreaterEqual(total_auditoria, 1)

    def test_admin_no_puede_restablecer_superadministrador(self) -> None:
        resultado = self.servicio.restablecer_contrasena_administrativa(
            actor=self.admin,
            nombre_usuario_objetivo="superadmin",
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

    def test_admin_puede_crear_usuario_operativo_y_generar_credencial_temporal(self) -> None:
        formulario = FormularioUsuario(
            identificador=None,
            nombre_usuario="recepcion1",
            nombre_completo="Recepcion Uno",
            correo="recepcion1@sicap.local",
            estado="ACTIVO",
            rol_id=self._obtener_id_rol("CAJERO"),
            observaciones="Usuario creado en prueba",
        )

        resultado = self.servicio.crear_usuario_operativo(self.admin, formulario)

        self.assertTrue(resultado.exito)
        self.assertTrue(resultado.requiere_mostrar_credencial_temporal)
        self.assertTrue(resultado.contrasena_temporal_generada)
        self.assertIsNotNone(resultado.contrasena_temporal_expira_en)

        usuario = self.repositorio.obtener_por_nombre_usuario("recepcion1")
        self.assertIsNotNone(usuario)
        self.assertEqual(usuario.rol_principal, "CAJERO")
        self.assertTrue(usuario.requiere_cambio_contrasena)
        self.assertIsNotNone(usuario.contrasena_temporal_expira_en)
        self.assertEqual(usuario.creado_por_nombre, "Administrador del Sistema")
        self.assertEqual(usuario.actualizado_por_nombre, "Administrador del Sistema")

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
        self.assertEqual(actualizado.actualizado_por_nombre, "Administrador del Sistema")

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

    def test_migracion_normaliza_roles_personalizados_y_multiples_roles(self) -> None:
        directorio = tempfile.TemporaryDirectory()
        try:
            raiz = Path(directorio.name)
            self._copiar_migraciones(raiz, incluir_016=False)
            gestor_rutas = GestorRutas(raiz_proyecto=raiz)
            gestor_bd = GestorBaseDatos(gestor_rutas)
            gestor_bd.inicializar_base_datos(incluir_datos_prueba=True)
            conexion = gestor_bd.obtener_conexion()
            try:
                with conexion:
                    conexion.execute(
                        """
                        INSERT INTO roles(nombre, descripcion, es_sistema, estado, creado_en, actualizado_en)
                        VALUES ('Supervisor', 'Rol heredado', 0, 'ACTIVO', datetime('now', 'localtime'), datetime('now', 'localtime'));
                        """
                    )
                    rol_supervisor = int(
                        conexion.execute("SELECT id FROM roles WHERE nombre = 'Supervisor';").fetchone()[0]
                    )
                    permiso_pagos = int(
                        conexion.execute("SELECT id FROM permisos WHERE codigo = 'pagos.registrar';").fetchone()[0]
                    )
                    conexion.execute(
                        "INSERT INTO roles_permisos(rol_id, permiso_id) VALUES (?, ?);",
                        (rol_supervisor, permiso_pagos),
                    )
                    conexion.execute(
                        """
                        INSERT INTO usuarios(
                            nombre_usuario,
                            nombre_completo,
                            correo,
                            contrasena_hash,
                            estado,
                            requiere_cambio_contrasena
                        )
                        VALUES ('legacy1', 'Legacy Uno', 'legacy1@sicap.local', 'CAMBIAR_HASH_EN_DESARROLLO', 'ACTIVO', 0);
                        """
                    )
                    usuario_legacy = int(
                        conexion.execute("SELECT id FROM usuarios WHERE nombre_usuario = 'legacy1';").fetchone()[0]
                    )
                    conexion.execute(
                        "INSERT INTO usuarios_roles(usuario_id, rol_id) VALUES (?, ?);",
                        (usuario_legacy, rol_supervisor),
                    )
                    usuario_admin = int(
                        conexion.execute("SELECT id FROM usuarios WHERE nombre_usuario = 'admin';").fetchone()[0]
                    )
                    rol_consulta = int(
                        conexion.execute("SELECT id FROM roles WHERE nombre = 'CONSULTA';").fetchone()[0]
                    )
                    conexion.execute(
                        "INSERT INTO usuarios_roles(usuario_id, rol_id) VALUES (?, ?);",
                        (usuario_admin, rol_consulta),
                    )
            finally:
                conexion.close()

            contenido = (RAIZ_PROYECTO / "database" / "migrations" / "016_usuarios_roles_fijos_y_contrasena_temporal.sql").read_text(encoding="utf-8")
            conexion = gestor_bd.obtener_conexion()
            try:
                with conexion:
                    conexion.executescript(contenido)
            finally:
                conexion.close()

            conexion = sqlite3.connect(gestor_rutas.obtener_ruta_base_datos())
            try:
                rol_legacy = conexion.execute(
                    "SELECT COUNT(*) FROM roles WHERE nombre = 'Supervisor';"
                ).fetchone()[0]
                rol_usuario_legacy = conexion.execute(
                    """
                    SELECT r.nombre
                    FROM usuarios_roles ur
                    INNER JOIN roles r ON r.id = ur.rol_id
                    WHERE ur.usuario_id = (SELECT id FROM usuarios WHERE nombre_usuario = 'legacy1');
                    """
                ).fetchall()
                roles_admin = conexion.execute(
                    """
                    SELECT r.nombre
                    FROM usuarios_roles ur
                    INNER JOIN roles r ON r.id = ur.rol_id
                    WHERE ur.usuario_id = (SELECT id FROM usuarios WHERE nombre_usuario = 'admin')
                      AND r.nombre IN ('ADMINISTRADOR', 'CAJERO', 'CONSULTA');
                    """
                ).fetchall()
            finally:
                conexion.close()

            self.assertEqual(rol_legacy, 0)
            self.assertEqual([fila[0] for fila in rol_usuario_legacy], ["CAJERO"])
            self.assertEqual([fila[0] for fila in roles_admin], ["ADMINISTRADOR"])
        finally:
            directorio.cleanup()

    @staticmethod
    def _copiar_migraciones(raiz_temporal: Path, incluir_016: bool = True) -> None:
        (raiz_temporal / "database" / "migrations").mkdir(parents=True, exist_ok=True)
        for ruta_migracion in (RAIZ_PROYECTO / "database" / "migrations").glob("*.sql"):
            if not incluir_016 and ruta_migracion.name == "016_usuarios_roles_fijos_y_contrasena_temporal.sql":
                continue
            contenido_sql = ruta_migracion.read_text(encoding="utf-8")
            (raiz_temporal / "database" / "migrations" / ruta_migracion.name).write_text(
                contenido_sql,
                encoding="utf-8",
            )

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
