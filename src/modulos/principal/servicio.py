"""Servicios del modulo principal."""

from __future__ import annotations

from modulos.autenticacion.entidades import UsuarioAutenticado
from modulos.principal.entidades import EstadoModuloPrincipal, ModuloNavegacion
from modulos.principal.repositorio import RepositorioModuloPrincipal


MODULOS_OPERATIVOS = (
    ModuloNavegacion("dashboard", "Inicio", "Resumen operativo del sistema.", "circle-check.svg"),
    ModuloNavegacion("barrios", "Barrios", "Catalogo base de barrios.", "circle-check.svg"),
    ModuloNavegacion("usuarios", "Usuarios", "Gestion de usuarios operativos.", "user.svg", "usuarios.gestionar"),
    ModuloNavegacion("abonados", "Abonados", "Registro y consulta de abonados.", "user.svg"),
    ModuloNavegacion("casas", "Casas", "Unidades de servicio por abonado.", "circle-check.svg"),
    ModuloNavegacion("pagos", "Pagos", "Registro e historial de pagos.", "circle-check.svg"),
    ModuloNavegacion("morosidad", "Morosidad", "Seguimiento de deuda y mora.", "alert-triangle.svg"),
    ModuloNavegacion("planes_pago", "Planes de pago", "Acuerdos, cuotas y saldos.", "key.svg"),
    ModuloNavegacion("reportes", "Reportes", "Consultas e informes administrativos.", "circle-check.svg"),
    ModuloNavegacion("configuracion", "Configuracion", "Parametros operativos.", "key.svg"),
    ModuloNavegacion("mantenimiento", "Mantenimiento", "Herramientas tecnicas sensibles.", "lock.svg", "mantenimiento.ver", True),
)


class ServicioModuloPrincipal:
    """Orquesta el estado inicial del shell principal."""

    def __init__(self, repositorio_modulo_principal: RepositorioModuloPrincipal) -> None:
        self.repositorio_modulo_principal = repositorio_modulo_principal

    def obtener_estado_para_usuario(
        self,
        usuario: UsuarioAutenticado,
    ) -> EstadoModuloPrincipal:
        modulos_visibles = tuple(
            modulo for modulo in MODULOS_OPERATIVOS if self._puede_ver_modulo(usuario, modulo)
        )
        return EstadoModuloPrincipal(
            nombre_usuario=usuario.nombre_usuario,
            nombre_completo=usuario.nombre_completo,
            perfil=self._resolver_perfil(usuario),
            metricas=self.repositorio_modulo_principal.obtener_metricas_dashboard(),
            modulos=modulos_visibles,
            puede_abrir_mantenimiento=usuario.tiene_permiso("mantenimiento.ver"),
        )

    @staticmethod
    def _resolver_perfil(usuario: UsuarioAutenticado) -> str:
        if usuario.es_superadministrador():
            return "SUPERADMINISTRADOR"
        if usuario.tiene_permiso("usuarios.gestionar"):
            return "ADMINISTRADOR"
        return "OPERATIVO"

    @staticmethod
    def _puede_ver_modulo(usuario: UsuarioAutenticado, modulo: ModuloNavegacion) -> bool:
        if modulo.es_tecnico:
            return usuario.tiene_permiso(modulo.permiso_requerido or "")
        if modulo.permiso_requerido is None:
            return True
        return usuario.tiene_permiso(modulo.permiso_requerido) or usuario.es_superadministrador()

