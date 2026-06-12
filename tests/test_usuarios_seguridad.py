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
from comun.seguridad import validar_politica_contrasena, verificar_contrasena  # noqa: E402
from tests.utilidades_base_datos import inicializar_base_datos_prueba  # noqa: E402
from modulos.autenticacion.entidades import CredencialesUsuario, UsuarioAutenticado  # noqa: E402
from modulos.autenticacion.repositorio import RepositorioAutenticacionSQLite  # noqa: E402
from modulos.autenticacion.servicio import ServicioAutenticacion  # noqa: E402
from modulos.configuracion.repositorio import RepositorioConfiguracionSQLite  # noqa: E402
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
        inicializar_base_datos_prueba(self.gestor_base_datos)
        self.repositorio = RepositorioUsuariosSQLite(self.gestor_base_datos)
        self.servicio = ServicioUsuarios(self.repositorio)

        self._crear_usuario_operativo(
            nombre_usuario="cajero1",
            nombre_completo="Cajero Uno",
            correo="cajero1@sigqua.local",
            rol_id=3,
        )

        self.admin = UsuarioAutenticado(
            identificador=self._obtener_id_usuario("admin"),
            nombre_usuario="admin",
            nombre_completo="Administrador del Sistema",
            correo="admin@sigqua.local",
            estado="ACTIVO",
            roles=("ADMINISTRADOR",),
            permisos=frozenset({"modulo.usuarios"}),
        )
    def tearDown(self) -> None:
        self.directorio_temporal.cleanup()

    def test_admin_lista_solo_usuarios_operativos(self) -> None:
        usuarios = self.servicio.listar_usuarios_para_administracion(self.admin)
        nombres = {usuario.nombre_usuario for usuario in usuarios}

        self.assertIn("admin", nombres)
        self.assertIn("cajero1", nombres)
        self.assertNotIn("superadmin", nombres)

    def test_roles_asignables_solo_muestran_roles_fijos_visibles(self) -> None:
        roles = self.servicio.listar_roles_asignables(self.admin)
        self.assertEqual([rol.nombre for rol in roles], ["ADMINISTRADOR", "CAJERO", "CONSULTA"])

    def test_admin_restablece_usuario_con_contrasena_definida(self) -> None:
        resultado = self.servicio.restablecer_contrasena_administrativa(
            actor=self.admin,
            nombre_usuario_objetivo="cajero1",
            nueva_contrasena="NuevaClaveCajero1!",
            confirmacion_contrasena="NuevaClaveCajero1!",
        )
        self.assertTrue(resultado.exito)

        conexion = sqlite3.connect(self.gestor_rutas.obtener_ruta_base_datos())
        try:
            requiere_cambio, restablecida_por, contrasena_hash = conexion.execute(
                """
                SELECT requiere_cambio_contrasena, restablecida_por_usuario_id, contrasena_hash
                FROM usuarios
                WHERE nombre_usuario = 'cajero1';
                """
            ).fetchone()
        finally:
            conexion.close()

        self.assertEqual(requiere_cambio, 0)
        self.assertEqual(restablecida_por, self.admin.identificador)
        self.assertNotEqual(contrasena_hash, "NuevaClaveCajero1!")
        self.assertTrue(verificar_contrasena("NuevaClaveCajero1!", contrasena_hash))

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

    def test_admin_puede_crear_usuario_con_contrasena_definida(self) -> None:
        formulario = FormularioUsuario(
            identificador=None,
            nombre_usuario="recepcion1",
            nombre_completo="Recepcion Uno",
            correo="recepcion1@sigqua.local",
            estado="ACTIVO",
            rol_id=self._obtener_id_rol("CAJERO"),
            observaciones="Usuario creado en prueba",
            contrasena="ClaveRecepcion1!",
            confirmacion_contrasena="ClaveRecepcion1!",
        )

        resultado = self.servicio.crear_usuario_operativo(self.admin, formulario)

        self.assertTrue(resultado.exito)

        usuario = self.repositorio.obtener_por_nombre_usuario("recepcion1")
        self.assertIsNotNone(usuario)
        self.assertEqual(usuario.rol_principal, "CAJERO")
        self.assertFalse(usuario.requiere_cambio_contrasena)
        self.assertEqual(usuario.creado_por_nombre, "Administrador del Sistema")
        self.assertEqual(usuario.actualizado_por_nombre, "Administrador del Sistema")

        conexion = sqlite3.connect(self.gestor_rutas.obtener_ruta_base_datos())
        try:
            hash_persistido, intentos, bloqueado_hasta = conexion.execute(
                """
                SELECT contrasena_hash, intentos_fallidos, bloqueado_hasta
                FROM usuarios
                WHERE nombre_usuario = 'recepcion1';
                """
            ).fetchone()
        finally:
            conexion.close()

        self.assertTrue(hash_persistido.startswith("scrypt$"))
        self.assertNotEqual(hash_persistido, formulario.contrasena)
        self.assertTrue(verificar_contrasena(formulario.contrasena, hash_persistido))
        self.assertEqual(intentos, 0)
        self.assertIsNone(bloqueado_hasta)

        servicio_autenticacion = ServicioAutenticacion(
            RepositorioAutenticacionSQLite(self.gestor_base_datos),
            repositorio_configuracion=RepositorioConfiguracionSQLite(
                self.gestor_base_datos
            ),
        )
        login = servicio_autenticacion.iniciar_sesion(
            CredencialesUsuario("recepcion1", formulario.contrasena)
        )
        self.assertTrue(login.exito)
        self.assertFalse(login.requiere_cambio_contrasena)

    def test_politica_compartida_rechaza_cada_requisito_por_separado(self) -> None:
        casos = (
            ("       ", "       ", "solo espacios"),
            ("Ab1!", "Ab1!", "al menos 8"),
            ("clave123!", "clave123!", "mayuscula"),
            ("CLAVE123!", "CLAVE123!", "minuscula"),
            ("ClaveSegura!", "ClaveSegura!", "numero"),
            ("Clave123 ", "Clave123 ", "simbolo"),
            ("Clave123\u200b", "Clave123\u200b", "simbolo"),
            ("Clave123!", "Otra123!", "no coinciden"),
        )

        for contrasena, confirmacion, fragmento in casos:
            with self.subTest(fragmento=fragmento):
                mensaje = validar_politica_contrasena(contrasena, confirmacion)
                self.assertIsNotNone(mensaje)
                self.assertIn(fragmento, mensaje.lower())

    def test_politica_compara_usuario_y_correo_sin_mayusculas_ni_espacios_externos(self) -> None:
        mensaje_usuario = validar_politica_contrasena(
            "  Usuario1!  ",
            "  Usuario1!  ",
            nombre_usuario="usuario1!",
        )
        mensaje_correo = validar_politica_contrasena(
            "  Persona1@Ejemplo.com  ",
            "  Persona1@Ejemplo.com  ",
            correo="persona1@ejemplo.COM",
        )

        self.assertIn("nombre de usuario", mensaje_usuario or "")
        self.assertIn("correo", mensaje_correo or "")

    def test_creacion_y_restablecimiento_rechazan_contrasenas_debiles(self) -> None:
        formulario = FormularioUsuario(
            identificador=None,
            nombre_usuario="consulta1",
            nombre_completo="Consulta Uno",
            correo="consulta1@sigqua.local",
            estado="ACTIVO",
            rol_id=self._obtener_id_rol("CONSULTA"),
            observaciones="",
            contrasena="sinmayuscula1!",
            confirmacion_contrasena="sinmayuscula1!",
        )

        creacion = self.servicio.crear_usuario_operativo(self.admin, formulario)
        restablecimiento = self.servicio.restablecer_contrasena_administrativa(
            actor=self.admin,
            nombre_usuario_objetivo="cajero1",
            nueva_contrasena="SINMINUSCULA1!",
            confirmacion_contrasena="SINMINUSCULA1!",
        )

        self.assertFalse(creacion.exito)
        self.assertIn("mayuscula", creacion.mensaje.lower())
        self.assertFalse(restablecimiento.exito)
        self.assertIn("minuscula", restablecimiento.mensaje.lower())

    def test_admin_puede_actualizar_usuario_operativo(self) -> None:
        usuario = self.repositorio.obtener_por_nombre_usuario("cajero1")
        self.assertIsNotNone(usuario)
        formulario = FormularioUsuario(
            identificador=usuario.identificador,
            nombre_usuario="cajero1",
            nombre_completo="Cajero Uno Actualizado",
            correo="cajero1.actualizado@sigqua.local",
            estado="INACTIVO",
            rol_id=self._obtener_id_rol("ADMINISTRADOR"),
            observaciones="Cambio administrativo",
        )

        resultado = self.servicio.actualizar_usuario_operativo(self.admin, formulario)

        self.assertTrue(resultado.exito)
        actualizado = self.repositorio.obtener_por_nombre_usuario("cajero1")
        self.assertIsNotNone(actualizado)
        self.assertEqual(actualizado.nombre_completo, "Cajero Uno Actualizado")
        self.assertEqual(actualizado.correo, "cajero1.actualizado@sigqua.local")
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

    @staticmethod
    def _copiar_migraciones(raiz_temporal: Path) -> None:
        (raiz_temporal / "database" / "migrations").mkdir(parents=True, exist_ok=True)
        for ruta_migracion in (RAIZ_PROYECTO / "database" / "migrations").glob("*.sql"):
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
