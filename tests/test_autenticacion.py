from __future__ import annotations

import os
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


class ProveedorCorreoFalso:
    def __init__(self) -> None:
        self.correos_enviados: list[dict[str, str]] = []

    def enviar_correo(self, destinatario: str, asunto: str, contenido: str) -> None:
        self.correos_enviados.append(
            {
                "destinatario": destinatario,
                "asunto": asunto,
                "contenido": contenido,
            }
        )


class TestAutenticacion(unittest.TestCase):
    def setUp(self) -> None:
        self.directorio_temporal = tempfile.TemporaryDirectory()
        self.raiz_temporal = Path(self.directorio_temporal.name)
        (self.raiz_temporal / "database" / "migrations").mkdir(parents=True, exist_ok=True)

        ruta_esquema_real = (
            RAIZ_PROYECTO / "database" / "migrations" / "002_esquema_inicial.sql"
        )
        contenido_sql = ruta_esquema_real.read_text(encoding="utf-8")
        (self.raiz_temporal / "database" / "migrations" / "002_esquema_inicial.sql").write_text(
            contenido_sql,
            encoding="utf-8",
        )

        self.gestor_rutas = GestorRutas(raiz_proyecto=self.raiz_temporal)
        self.gestor_base_datos = GestorBaseDatos(self.gestor_rutas)
        self.gestor_base_datos.inicializar_base_datos()
        self.proveedor_correo = ProveedorCorreoFalso()
        self.repositorio = RepositorioAutenticacionSQLite(self.gestor_base_datos)
        self.servicio = ServicioAutenticacion(
            repositorio_autenticacion=self.repositorio,
            proveedor_correo=self.proveedor_correo,
            entorno="desarrollo",
        )

    def tearDown(self) -> None:
        self.directorio_temporal.cleanup()

    def test_login_valido_crea_sesion_y_registra_intento(self) -> None:
        resultado = self.servicio.iniciar_sesion(
            CredencialesUsuario(nombre_usuario="admin", contrasena_plana="Admin123!")
        )

        self.assertTrue(resultado.exito)
        self.assertIsNotNone(resultado.usuario)
        self.assertIsNotNone(resultado.token_sesion)

        conexion = sqlite3.connect(self.gestor_rutas.obtener_ruta_base_datos())
        try:
            total_sesiones = conexion.execute("SELECT COUNT(*) FROM sesiones;").fetchone()[0]
            total_intentos = conexion.execute(
                "SELECT COUNT(*) FROM intentos_login WHERE exito = 1;"
            ).fetchone()[0]
            ultimo_acceso = conexion.execute(
                "SELECT ultimo_acceso_en FROM usuarios WHERE nombre_usuario = 'admin';"
            ).fetchone()[0]
        finally:
            conexion.close()

        self.assertEqual(total_sesiones, 1)
        self.assertEqual(total_intentos, 1)
        self.assertIsNotNone(ultimo_acceso)

    def test_login_invalido_registra_intento_fallido(self) -> None:
        resultado = self.servicio.iniciar_sesion(
            CredencialesUsuario(nombre_usuario="admin", contrasena_plana="mal-clave")
        )

        self.assertFalse(resultado.exito)

        conexion = sqlite3.connect(self.gestor_rutas.obtener_ruta_base_datos())
        try:
            total_fallidos = conexion.execute(
                "SELECT COUNT(*) FROM intentos_login WHERE exito = 0;"
            ).fetchone()[0]
            total_sesiones = conexion.execute("SELECT COUNT(*) FROM sesiones;").fetchone()[0]
        finally:
            conexion.close()

        self.assertEqual(total_fallidos, 1)
        self.assertEqual(total_sesiones, 0)

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
            CredencialesUsuario(nombre_usuario="admin", contrasena_plana="Admin123!")
        )

        self.assertFalse(resultado.exito)
        self.assertIn("bloqueado", resultado.mensaje.lower())

    def test_recuperacion_existente_persiste_token_y_entrega_token_prueba(self) -> None:
        resultado = self.servicio.solicitar_recuperacion("admin@sicap.local")

        self.assertTrue(resultado.exito)
        self.assertTrue(resultado.token_prueba)
        self.assertEqual(len(self.proveedor_correo.correos_enviados), 1)

        conexion = sqlite3.connect(self.gestor_rutas.obtener_ruta_base_datos())
        try:
            total_tokens = conexion.execute(
                "SELECT COUNT(*) FROM tokens_recuperacion_contrasena;"
            ).fetchone()[0]
        finally:
            conexion.close()

        self.assertEqual(total_tokens, 1)

    def test_recuperacion_inexistente_no_enumera_cuentas(self) -> None:
        resultado = self.servicio.solicitar_recuperacion("no-existe@sicap.local")

        self.assertTrue(resultado.exito)
        self.assertIsNone(resultado.token_prueba)
        self.assertEqual(len(self.proveedor_correo.correos_enviados), 0)

        conexion = sqlite3.connect(self.gestor_rutas.obtener_ruta_base_datos())
        try:
            total_tokens = conexion.execute(
                "SELECT COUNT(*) FROM tokens_recuperacion_contrasena;"
            ).fetchone()[0]
        finally:
            conexion.close()

        self.assertEqual(total_tokens, 0)

    def test_restablecimiento_exitoso_invalida_reutilizacion_del_token(self) -> None:
        recuperacion = self.servicio.solicitar_recuperacion("admin@sicap.local")
        self.assertTrue(recuperacion.token_prueba)

        resultado = self.servicio.restablecer_contrasena(
            token=recuperacion.token_prueba or "",
            nueva_contrasena="NuevaClave123!",
            confirmacion_contrasena="NuevaClave123!",
        )

        self.assertTrue(resultado.exito)

        login_nuevo = self.servicio.iniciar_sesion(
            CredencialesUsuario(nombre_usuario="admin", contrasena_plana="NuevaClave123!")
        )
        self.assertTrue(login_nuevo.exito)

        reutilizacion = self.servicio.restablecer_contrasena(
            token=recuperacion.token_prueba or "",
            nueva_contrasena="OtraClave123!",
            confirmacion_contrasena="OtraClave123!",
        )
        self.assertFalse(reutilizacion.exito)

    def test_asegurar_usuario_admin_desarrollo_repara_placeholder(self) -> None:
        conexion = self.gestor_base_datos.obtener_conexion()
        try:
            with conexion:
                conexion.execute(
                    """
                    UPDATE usuarios
                    SET contrasena_hash = 'CAMBIAR_HASH_EN_DESARROLLO'
                    WHERE nombre_usuario = 'admin';
                    """
                )
        finally:
            conexion.close()

        self.servicio.asegurar_usuario_admin_desarrollo()
        resultado = self.servicio.iniciar_sesion(
            CredencialesUsuario(nombre_usuario="admin", contrasena_plana="Admin123!")
        )
        self.assertTrue(resultado.exito)


if __name__ == "__main__":
    unittest.main()
