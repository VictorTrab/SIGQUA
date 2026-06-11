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
from modulos.autenticacion.entidades import CredencialesUsuario  # noqa: E402
from modulos.autenticacion.repositorio import RepositorioAutenticacionSQLite  # noqa: E402
from modulos.autenticacion.servicio import ServicioAutenticacion  # noqa: E402
from modulos.configuracion.repositorio import RepositorioConfiguracionSQLite  # noqa: E402
from tests.utilidades_base_datos import inicializar_base_datos_prueba  # noqa: E402


class TestAutenticacion(unittest.TestCase):
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
        inicializar_base_datos_prueba(self.gestor_base_datos)
        self.repositorio = RepositorioAutenticacionSQLite(self.gestor_base_datos)
        self.repositorio_configuracion = RepositorioConfiguracionSQLite(self.gestor_base_datos)
        self.servicio = ServicioAutenticacion(
            repositorio_autenticacion=self.repositorio,
            repositorio_configuracion=self.repositorio_configuracion,
        )

    def tearDown(self) -> None:
        self.directorio_temporal.cleanup()

    def test_login_valido_crea_sesion_y_registra_intento(self) -> None:
        resultado = self.servicio.iniciar_sesion(
            CredencialesUsuario(nombre_usuario="admin", contrasena_plana="SIGQUA2026!")
        )

        self.assertTrue(resultado.exito)
        self.assertIsNotNone(resultado.usuario)
        self.assertTrue(resultado.requiere_cambio_contrasena)
        self.assertIsNone(resultado.token_sesion)

        conexion = sqlite3.connect(self.gestor_rutas.obtener_ruta_base_datos())
        try:
            total_sesiones = conexion.execute("SELECT COUNT(*) FROM sesiones;").fetchone()[0]
            total_intentos = conexion.execute(
                "SELECT COUNT(*) FROM intentos_login WHERE resultado = 'EXITOSO';"
            ).fetchone()[0]
            ultimo_acceso = conexion.execute(
                "SELECT ultimo_acceso_en FROM usuarios WHERE nombre_usuario = 'admin';"
            ).fetchone()[0]
        finally:
            conexion.close()

        self.assertEqual(total_sesiones, 0)
        self.assertEqual(total_intentos, 1)
        self.assertIsNotNone(ultimo_acceso)

    def test_credencial_inicial_no_tiene_caducidad_temporal(self) -> None:
        resultado = self.servicio.iniciar_sesion(
            CredencialesUsuario(nombre_usuario="admin", contrasena_plana="SIGQUA2026!")
        )

        self.assertTrue(resultado.exito)
        self.assertTrue(resultado.requiere_cambio_contrasena)
        self.assertIsNone(resultado.token_sesion)

    def test_login_usa_duracion_sesion_configurada(self) -> None:
        self.repositorio_configuracion.actualizar_valores(
            {"seguridad.duracion_sesion_horas": "0.5"},
            actor_id=1,
        )

        self.servicio.restablecer_contrasena(
            nombre_usuario="admin",
            nueva_contrasena="NuevaClave123!",
            confirmacion_contrasena="NuevaClave123!",
        )
        resultado = self.servicio.iniciar_sesion(
            CredencialesUsuario(nombre_usuario="admin", contrasena_plana="NuevaClave123!")
        )

        self.assertTrue(resultado.exito)
        self.assertIsNotNone(resultado.usuario)
        conexion = sqlite3.connect(self.gestor_rutas.obtener_ruta_base_datos())
        try:
            expira_en = conexion.execute(
                """
                SELECT expira_en
                FROM sesiones
                WHERE usuario_id = (
                    SELECT id FROM usuarios WHERE nombre_usuario = 'admin'
                )
                ORDER BY id DESC
                LIMIT 1;
                """
            ).fetchone()[0]
        finally:
            conexion.close()
        self.assertIsNotNone(expira_en)

    def test_login_invalido_registra_intento_fallido(self) -> None:
        resultado = self.servicio.iniciar_sesion(
            CredencialesUsuario(nombre_usuario="admin", contrasena_plana="mal-clave")
        )

        self.assertFalse(resultado.exito)

        conexion = sqlite3.connect(self.gestor_rutas.obtener_ruta_base_datos())
        try:
            total_fallidos = conexion.execute(
                "SELECT COUNT(*) FROM intentos_login WHERE resultado = 'FALLIDO';"
            ).fetchone()[0]
            total_sesiones = conexion.execute("SELECT COUNT(*) FROM sesiones;").fetchone()[0]
        finally:
            conexion.close()

        self.assertEqual(total_fallidos, 1)
        self.assertEqual(total_sesiones, 0)

    def test_login_fallido_repetido_bloquea_usuario(self) -> None:
        for _ in range(5):
            resultado = self.servicio.iniciar_sesion(
                CredencialesUsuario(nombre_usuario="admin", contrasena_plana="mal-clave")
            )

        self.assertFalse(resultado.exito)
        self.assertEqual(resultado.codigo, "USUARIO_BLOQUEADO")

        conexion = sqlite3.connect(self.gestor_rutas.obtener_ruta_base_datos())
        try:
            estado, intentos = conexion.execute(
                """
                SELECT estado, intentos_fallidos
                FROM usuarios
                WHERE nombre_usuario = 'admin';
                """
            ).fetchone()
        finally:
            conexion.close()

        self.assertEqual(estado, "BLOQUEADO")
        self.assertEqual(intentos, 5)

    def test_login_bloqueado_falla_con_mensaje_especifico(self) -> None:
        conexion = self.gestor_base_datos.obtener_conexion()
        try:
            with conexion:
                conexion.execute(
                    "UPDATE usuarios SET estado = 'BLOQUEADO' WHERE nombre_usuario = 'admin';"
                )
        finally:
            conexion.close()

        resultado = self.servicio.iniciar_sesion(
            CredencialesUsuario(nombre_usuario="admin", contrasena_plana="SIGQUA2026!")
        )

        self.assertFalse(resultado.exito)
        self.assertIn("bloqueado", resultado.mensaje.lower())

    def test_restablecimiento_local_actualiza_hash_y_permita_login_nuevo(self) -> None:
        resultado = self.servicio.restablecer_contrasena(
            nombre_usuario="admin",
            nueva_contrasena="NuevaClave123!",
            confirmacion_contrasena="NuevaClave123!",
        )
        self.assertTrue(resultado.exito)

        login_anterior = self.servicio.iniciar_sesion(
            CredencialesUsuario(nombre_usuario="admin", contrasena_plana="SIGQUA2026!")
        )
        self.assertFalse(login_anterior.exito)

        login_nuevo = self.servicio.iniciar_sesion(
            CredencialesUsuario(nombre_usuario="admin", contrasena_plana="NuevaClave123!")
        )
        self.assertTrue(login_nuevo.exito)
        self.assertFalse(login_nuevo.requiere_cambio_contrasena)
        self.assertIsNotNone(login_nuevo.token_sesion)

        conexion = sqlite3.connect(self.gestor_rutas.obtener_ruta_base_datos())
        try:
            ultimo_cambio, requiere = conexion.execute(
                """
                SELECT ultimo_cambio_contrasena_en, requiere_cambio_contrasena
                FROM usuarios
                WHERE nombre_usuario = 'admin';
                """
            ).fetchone()
        finally:
            conexion.close()

        self.assertIsNotNone(ultimo_cambio)
        self.assertEqual(requiere, 0)

    def test_restablecimiento_local_falla_para_usuario_desconocido(self) -> None:
        resultado = self.servicio.restablecer_contrasena(
            nombre_usuario="fantasma",
            nueva_contrasena="NuevaClave123!",
            confirmacion_contrasena="NuevaClave123!",
        )

        self.assertFalse(resultado.exito)
        self.assertEqual(resultado.codigo, "USUARIO_NO_ENCONTRADO")

    def test_cerrar_sesion_actualiza_finalizado_en(self) -> None:
        restablecimiento = self.servicio.restablecer_contrasena(
            nombre_usuario="admin",
            nueva_contrasena="NuevaClave123!",
            confirmacion_contrasena="NuevaClave123!",
        )
        self.assertTrue(restablecimiento.exito)

        login = self.servicio.iniciar_sesion(
            CredencialesUsuario(nombre_usuario="admin", contrasena_plana="NuevaClave123!")
        )
        self.assertTrue(login.exito)
        self.assertTrue(login.token_sesion)

        cierre = self.servicio.cerrar_sesion(login.token_sesion or "")
        self.assertTrue(cierre.exito)

        conexion = sqlite3.connect(self.gestor_rutas.obtener_ruta_base_datos())
        try:
            finalizado_en, estado = conexion.execute(
                "SELECT cerrado_en, estado FROM sesiones WHERE estado = 'CERRADA' LIMIT 1;"
            ).fetchone()
        finally:
            conexion.close()

        self.assertIsNotNone(finalizado_en)
        self.assertEqual(estado, "CERRADA")

    def test_esquema_nuevo_no_crea_tabla_tokens_recuperacion(self) -> None:
        conexion = sqlite3.connect(self.gestor_rutas.obtener_ruta_base_datos())
        try:
            tabla_tokens = conexion.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table' AND name = 'tokens_recuperacion_contrasena';
                """
            ).fetchone()
        finally:
            conexion.close()

        self.assertIsNone(tabla_tokens)

    def test_plantilla_excluye_tablas_tecnicas_y_conserva_vistas_operativas(self) -> None:
        conexion = sqlite3.connect(self.gestor_rutas.obtener_ruta_base_datos())
        try:
            nombres = {
                fila[0]
                for fila in conexion.execute(
                    """
                    SELECT name
                    FROM sqlite_master
                    WHERE type IN ('table', 'view')
                      AND name IN (
                          'historial_respaldos',
                          'eventos_tecnicos',
                          'auditoria',
                          'esquema_migraciones',
                          'reportes_generados',
                          'vw_usuarios_operativos',
                          'vw_usuarios_tecnicos',
                          'vw_usuarios_restablecibles_por_admin'
                      );
                    """
                ).fetchall()
            }
        finally:
            conexion.close()

        self.assertEqual(
            nombres,
            {
                "vw_usuarios_operativos",
                "vw_usuarios_restablecibles_por_admin",
            },
        )


if __name__ == "__main__":
    unittest.main()

