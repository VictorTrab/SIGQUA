from __future__ import annotations

import os
import shutil
import sys
import unittest
import uuid
from pathlib import Path


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

RAIZ_PROYECTO = Path(__file__).resolve().parents[1]
RUTA_SRC = RAIZ_PROYECTO / "src"

if str(RUTA_SRC) not in sys.path:
    sys.path.insert(0, str(RUTA_SRC))

from PySide6.QtCore import Qt  # noqa: E402
from PySide6.QtWidgets import QApplication, QToolButton, QWidget  # noqa: E402

from app import (  # noqa: E402
    ALTO_VENTANA_AUTENTICACION,
    ANCHO_VENTANA_AUTENTICACION,
    crear_ventana_principal,
)
from comun.configuracion.gestor_rutas import GestorRutas  # noqa: E402
from modulos.autenticacion.controlador import ControladorAutenticacion  # noqa: E402
from modulos.autenticacion.entidades import SesionIniciada, UsuarioAutenticado  # noqa: E402
from modulos.autenticacion.vista import (  # noqa: E402
    ANCHO_MAXIMO_TARJETA,
    COLOR_GRADIENTE_FINAL,
    COLOR_GRADIENTE_INICIAL,
    VistaAutenticacion,
)
from modulos.mantenimiento.vista import VistaMantenimiento  # noqa: E402
from modulos.barrios.vista import VistaBarrios  # noqa: E402
from modulos.barrios.entidades import Barrio  # noqa: E402
from modulos.principal.vista import VistaModuloPrincipal  # noqa: E402


class TestVistaYAppAutenticacion(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.aplicacion = QApplication.instance() or QApplication([])

    @staticmethod
    def _copiar_migraciones(raiz_temporal: Path) -> None:
        for ruta_migracion in (RAIZ_PROYECTO / "database" / "migrations").glob("*.sql"):
            contenido_sql = ruta_migracion.read_text(encoding="utf-8")
            (raiz_temporal / "database" / "migrations" / ruta_migracion.name).write_text(
                contenido_sql,
                encoding="utf-8",
            )

    @staticmethod
    def _crear_raiz_temporal_prueba(prefijo: str) -> Path:
        raiz_temporal = RAIZ_PROYECTO / ".codex-temp" / f"{prefijo}_{uuid.uuid4().hex}"
        (raiz_temporal / "database" / "migrations").mkdir(parents=True, exist_ok=True)
        return raiz_temporal

    def test_vista_usa_tres_paginas_reutilizables_y_navegacion_local(self) -> None:
        vista = VistaAutenticacion()
        fondo_blur = vista._pagina_login.findChild(type(vista._boton_login.parentWidget()), "fondoBlurTarjeta")

        self.assertEqual(vista._stack.count(), 3)
        self.assertEqual(vista._boton_login.parentWidget().maximumWidth(), ANCHO_MAXIMO_TARJETA)
        self.assertGreater(vista.maximumWidth(), ANCHO_MAXIMO_TARJETA)
        self.assertEqual(COLOR_GRADIENTE_INICIAL, "#1abc9c")
        self.assertEqual(COLOR_GRADIENTE_FINAL, "#1f2c51")
        self.assertIsNotNone(fondo_blur)
        self.assertIsNone(fondo_blur.graphicsEffect())
        self.assertEqual(len(vista._campo_contrasena.actions()), 2)
        self.assertEqual(vista._campo_contrasena.echoMode(), vista._campo_contrasena.EchoMode.Password)

        vista._campo_contrasena.actions()[-1].trigger()
        self.assertEqual(vista._campo_contrasena.echoMode(), vista._campo_contrasena.EchoMode.Normal)

        vista._campo_contrasena.actions()[-1].trigger()
        self.assertEqual(vista._campo_contrasena.echoMode(), vista._campo_contrasena.EchoMode.Password)
        self.assertFalse(vista._boton_login.icon().isNull())

        vista.mostrar_olvido_contrasena()
        self.assertIs(vista._stack.currentWidget(), vista._pagina_olvido)
        textos_olvido = [
            label.text().lower()
            for label in vista._pagina_olvido.findChildren(type(vista._label_pie_login))
        ]
        self.assertTrue(any("soporte o administracion" in texto for texto in textos_olvido))
        self.assertFalse(any("primera version" in texto for texto in textos_olvido))

    def test_vista_olvido_muestra_mensaje_informativo_y_restablecer_retorna_a_login(self) -> None:
        vista = VistaAutenticacion()

        vista.mostrar_olvido_contrasena()
        textos = [
            label.text().lower()
            for label in vista._pagina_olvido.findChildren(type(vista._label_pie_login))
        ]
        self.assertTrue(any("soporte o administracion" in texto for texto in textos))
        self.assertFalse(any("primera version" in texto for texto in textos))

        vista.mostrar_restablecer("admin", "Cambio obligatorio pendiente.")
        self.assertIs(vista._stack.currentWidget(), vista._pagina_restablecer)
        self.assertIn("admin", vista._label_usuario_restablecer.text().lower())

        vista.mostrar_exito("Tu contrasena se actualizo correctamente.")
        self.assertIs(vista._stack.currentWidget(), vista._pagina_login)
        self.assertIn("actualizo correctamente", vista._mensaje_login.text().lower())

    def test_capa_blur_no_bloquea_acciones_del_login(self) -> None:
        vista = VistaAutenticacion()
        eventos_login = []
        eventos_olvido = []
        vista.iniciar_sesion_solicitada.connect(
            lambda usuario, contrasena: eventos_login.append((usuario, contrasena))
        )
        vista.ir_a_olvido_solicitado.connect(lambda: eventos_olvido.append(True))

        vista._campo_usuario.setText("admin")
        vista._campo_contrasena.setText("Admin123!")
        vista._boton_login.click()
        vista._pagina_login.findChild(type(vista._boton_login), "botonSecundario").click()

        self.assertEqual(eventos_login, [("admin", "Admin123!")])
        self.assertEqual(eventos_olvido, [True])

    def test_app_compone_ventana_y_deja_login_con_tamano_fijo(self) -> None:
        raiz_temporal = self._crear_raiz_temporal_prueba("test_login_fijo")
        try:
            self._copiar_migraciones(raiz_temporal)

            gestor_rutas = GestorRutas(raiz_proyecto=raiz_temporal)
            _, ventana_principal, vista_autenticacion = crear_ventana_principal(gestor_rutas)

            self.assertIs(ventana_principal.centralWidget(), ventana_principal.contenedor_central)
            self.assertIs(ventana_principal.contenedor_central.currentWidget(), vista_autenticacion)
            self.assertEqual(ventana_principal.minimumWidth(), ANCHO_VENTANA_AUTENTICACION)
            self.assertEqual(ventana_principal.maximumWidth(), ANCHO_VENTANA_AUTENTICACION)
            self.assertEqual(ventana_principal.minimumHeight(), ALTO_VENTANA_AUTENTICACION)
            self.assertEqual(ventana_principal.maximumHeight(), ALTO_VENTANA_AUTENTICACION)
            self.assertFalse(
                bool(ventana_principal.windowFlags() & Qt.WindowType.WindowMaximizeButtonHint)
            )
            self.assertTrue(
                bool(ventana_principal.windowFlags() & Qt.WindowType.WindowMinimizeButtonHint)
            )
            self.assertTrue(
                bool(ventana_principal.windowFlags() & Qt.WindowType.WindowCloseButtonHint)
            )
            ventana_principal.close()
        finally:
            shutil.rmtree(raiz_temporal, ignore_errors=True)

    def test_post_login_abre_modulo_principal_provisional(self) -> None:
        raiz_temporal = self._crear_raiz_temporal_prueba("test_post_login")
        try:
            self._copiar_migraciones(raiz_temporal)

            gestor_rutas = GestorRutas(raiz_proyecto=raiz_temporal)
            _, ventana_principal, vista_autenticacion = crear_ventana_principal(gestor_rutas)

            vista_autenticacion.autenticacion_exitosa.emit(
                SesionIniciada(
                    usuario=UsuarioAutenticado(
                        identificador=1,
                        nombre_usuario="admin",
                        nombre_completo="Administrador del Sistema",
                        correo="admin@sicap.local",
                        estado="ACTIVO",
                    ),
                    token_sesion="token-prueba-123",
                )
            )
            self.aplicacion.processEvents()

            self.assertIs(ventana_principal.centralWidget(), ventana_principal.contenedor_central)
            self.assertIsInstance(
                ventana_principal.contenedor_central.currentWidget(),
                VistaModuloPrincipal,
            )
            self.assertEqual(ventana_principal.windowTitle(), "SICAP | Modulo principal")
            self.assertIsNotNone(ventana_principal.sesion_activa)
            self.assertEqual(ventana_principal.sesion_activa.token_sesion, "token-prueba-123")
            self.assertEqual(ventana_principal.contenedor_central.count(), 2)
            self.assertFalse(ventana_principal.vista_modulo_principal._boton_mantenimiento.isVisible())
            self.assertTrue(
                bool(ventana_principal.windowFlags() & Qt.WindowType.WindowMaximizeButtonHint)
            )
            self.assertTrue(
                bool(ventana_principal.windowState() & Qt.WindowState.WindowMaximized)
            )
            ventana_principal.close()
        finally:
            shutil.rmtree(raiz_temporal, ignore_errors=True)

    def test_logout_regresa_a_login_y_limpia_sesion(self) -> None:
        raiz_temporal = self._crear_raiz_temporal_prueba("test_logout")
        try:
            self._copiar_migraciones(raiz_temporal)

            gestor_rutas = GestorRutas(raiz_proyecto=raiz_temporal)
            _, ventana_principal, vista_autenticacion = crear_ventana_principal(gestor_rutas)

            vista_autenticacion.autenticacion_exitosa.emit(
                SesionIniciada(
                    usuario=UsuarioAutenticado(
                        identificador=1,
                        nombre_usuario="admin",
                        nombre_completo="Administrador del Sistema",
                        correo="admin@sicap.local",
                        estado="ACTIVO",
                    ),
                    token_sesion="token-prueba-456",
                )
            )

            alto_minimo_principal = ventana_principal.minimumSizeHint().height()
            ventana_principal.vista_modulo_principal.cerrar_sesion_solicitada.emit()

            self.assertIs(ventana_principal.centralWidget(), ventana_principal.contenedor_central)
            self.assertIs(ventana_principal.contenedor_central.currentWidget(), vista_autenticacion)
            self.assertIsNone(ventana_principal.sesion_activa)
            self.assertEqual(ventana_principal.windowTitle(), "SICAP | Autenticacion")
            self.assertEqual(ventana_principal.contenedor_central.count(), 2)
            self.assertGreaterEqual(alto_minimo_principal, 0)
            self.assertEqual(ventana_principal.minimumWidth(), ANCHO_VENTANA_AUTENTICACION)
            self.assertEqual(ventana_principal.maximumWidth(), ANCHO_VENTANA_AUTENTICACION)
            self.assertEqual(ventana_principal.minimumHeight(), ALTO_VENTANA_AUTENTICACION)
            self.assertEqual(ventana_principal.maximumHeight(), ALTO_VENTANA_AUTENTICACION)
            self.assertFalse(
                bool(ventana_principal.windowFlags() & Qt.WindowType.WindowMaximizeButtonHint)
            )
            self.assertTrue(
                bool(ventana_principal.windowFlags() & Qt.WindowType.WindowMinimizeButtonHint)
            )
            self.assertTrue(
                bool(ventana_principal.windowFlags() & Qt.WindowType.WindowCloseButtonHint)
            )
            self.assertIn(
                "Sesion cerrada correctamente.",
                vista_autenticacion._mensaje_login.text(),
            )
            ventana_principal.close()
        finally:
            shutil.rmtree(raiz_temporal, ignore_errors=True)

    def test_dashboard_principal_refluye_y_tiene_scroll_responsivo(self) -> None:
        raiz_temporal = RAIZ_PROYECTO / ".codex-temp" / f"test_dashboard_{uuid.uuid4().hex}"
        try:
            (raiz_temporal / "database" / "migrations").mkdir(parents=True, exist_ok=True)
            self._copiar_migraciones(raiz_temporal)

            gestor_rutas = GestorRutas(raiz_proyecto=raiz_temporal)
            _, ventana_principal, vista_autenticacion = crear_ventana_principal(gestor_rutas)

            vista_autenticacion.autenticacion_exitosa.emit(
                SesionIniciada(
                    usuario=UsuarioAutenticado(
                        identificador=1,
                        nombre_usuario="admin",
                        nombre_completo="Administrador del Sistema",
                        correo="admin@sicap.local",
                        estado="ACTIVO",
                    ),
                    token_sesion="token-dashboard",
                )
            )

            vista_principal = ventana_principal.vista_modulo_principal
            ventana_principal.show()
            self.aplicacion.processEvents()
            self.assertTrue(vista_principal._scroll_dashboard.widgetResizable())

            ventana_principal.resize(1200, 760)
            self.aplicacion.processEvents()
            self.assertEqual(vista_principal._modo_dashboard_actual, "compacto")
            self.assertGreater(vista_principal._scroll_dashboard.verticalScrollBar().maximum(), 0)

            ventana_principal.resize(1600, 960)
            self.aplicacion.processEvents()
            self.assertEqual(vista_principal._modo_dashboard_actual, "medio")
            self.assertGreater(vista_principal._scroll_dashboard.verticalScrollBar().maximum(), 0)

            ventana_principal.resize(1900, 1080)
            self.aplicacion.processEvents()
            self.assertEqual(vista_principal._modo_dashboard_actual, "amplio")
            self.assertIs(
                vista_principal._stack_contenido.currentWidget(),
                vista_principal._pagina_dashboard,
            )
            self.assertEqual(vista_principal._scroll_dashboard.verticalScrollBar().maximum(), 0)
            ventana_principal.close()
        finally:
            shutil.rmtree(raiz_temporal, ignore_errors=True)

    def test_controlador_permite_abrir_restablecimiento_administrativo(self) -> None:
        raiz_temporal = self._crear_raiz_temporal_prueba("test_restablecimiento")
        try:
            self._copiar_migraciones(raiz_temporal)

            gestor_rutas = GestorRutas(raiz_proyecto=raiz_temporal)
            _, ventana_principal, vista_autenticacion = crear_ventana_principal(gestor_rutas)

            controlador: ControladorAutenticacion = ventana_principal.controlador_autenticacion
            controlador.abrir_restablecimiento_administrativo(
                "admin",
                "Cambio obligatorio pendiente.",
            )

            self.assertIs(vista_autenticacion._stack.currentWidget(), vista_autenticacion._pagina_restablecer)
            self.assertIn("admin", vista_autenticacion._label_usuario_restablecer.text().lower())
            ventana_principal.close()
        finally:
            shutil.rmtree(raiz_temporal, ignore_errors=True)

    def test_superadmin_ve_y_abre_mantenimiento_tecnico(self) -> None:
        raiz_temporal = self._crear_raiz_temporal_prueba("test_superadmin")
        try:
            self._copiar_migraciones(raiz_temporal)

            gestor_rutas = GestorRutas(raiz_proyecto=raiz_temporal)
            _, ventana_principal, vista_autenticacion = crear_ventana_principal(gestor_rutas)

            vista_autenticacion.autenticacion_exitosa.emit(
                SesionIniciada(
                    usuario=UsuarioAutenticado(
                        identificador=99,
                        nombre_usuario="superadmin",
                        nombre_completo="Superadministrador Tecnico",
                        correo="superadmin@sicap.local",
                        estado="ACTIVO",
                        es_tecnico=True,
                        es_oculto=True,
                        roles=("SUPERADMINISTRADOR",),
                        permisos=frozenset({"mantenimiento.ver", "seguridad.ver_logs"}),
                    ),
                    token_sesion="token-superadmin-1",
                )
            )

            self.assertFalse(ventana_principal.vista_modulo_principal._boton_mantenimiento.isHidden())
            ventana_principal.vista_modulo_principal._boton_mantenimiento.click()
            self.assertIsInstance(
                ventana_principal.contenedor_central.currentWidget(),
                VistaMantenimiento,
            )
            ventana_principal.vista_mantenimiento.volver_solicitado.emit()
            self.assertIsInstance(
                ventana_principal.contenedor_central.currentWidget(),
                VistaModuloPrincipal,
            )
            ventana_principal.close()
        finally:
            shutil.rmtree(raiz_temporal, ignore_errors=True)

    def test_vista_barrios_usa_radio_minimo_en_panel_interno_de_tabla(self) -> None:
        vista = VistaBarrios()
        vista.show()
        self.aplicacion.processEvents()

        panel_tabla = vista.findChild(QWidget, "panelTablaBarrios")
        tabla = vista.findChild(type(vista._tabla), "tablaBarrios")
        viewport = vista._tabla.viewport()

        self.assertIsNotNone(panel_tabla)
        self.assertIs(tabla, vista._tabla)
        self.assertEqual(viewport.objectName(), "viewportTablaBarrios")
        self.assertIn("QFrame#panelTablaBarrios", vista.styleSheet())
        self.assertIn("QTableWidget#tablaBarrios", vista.styleSheet())
        self.assertIn(f"border-radius: {vista.RADIO_PANEL_TABLA}px;", vista.styleSheet())
        self.assertIn(f"padding: 0 0 {vista.RADIO_PANEL_TABLA}px 0;", vista.styleSheet())
        self.assertIn("QTableWidget#tablaBarrios QHeaderView::section", vista.styleSheet())
        self.assertEqual(vista._tabla.frameShape(), vista._tabla.Shape.NoFrame)
        self.assertFalse(vista._tabla.horizontalHeader().stretchLastSection())

        fila_acciones = vista._crear_acciones_fila(
            Barrio(identificador=1, nombre="Centro", estado="ACTIVO")
        )
        botones_accion = fila_acciones.findChildren(QToolButton, "botonIconoFilaBarrio")
        self.assertEqual(len(botones_accion), 3)
        self.assertTrue(all(not boton.text() for boton in botones_accion))
        self.assertTrue(all(not boton.icon().isNull() for boton in botones_accion))
        self.assertTrue(all(boton.iconSize().width() == 18 for boton in botones_accion))
        self.assertEqual(fila_acciones.minimumHeight(), 58)
        vista.close()

    def test_notificacion_barrios_desaparece_tras_temporizador(self) -> None:
        vista = VistaBarrios()

        vista.mostrar_mensaje("Barrio actualizado correctamente.")

        self.assertFalse(vista._mensaje.isHidden())
        self.assertTrue(vista._temporizador_mensaje.isActive())
        self.assertEqual(
            vista._temporizador_mensaje.interval(),
            vista.DURACION_MENSAJE_MS,
        )

        vista._temporizador_mensaje.timeout.emit()

        self.assertTrue(vista._mensaje.isHidden())
        self.assertEqual(vista._mensaje.text(), "")
        vista.close()


if __name__ == "__main__":
    unittest.main()
