"""Servicios del modulo principal."""

from __future__ import annotations

from modulos.autenticacion.entidades import UsuarioAutenticado
from modulos.principal.entidades import EstadoModuloPrincipal, ModuloNavegacion
from modulos.principal.repositorio import RepositorioModuloPrincipal


MODULOS_OPERATIVOS = (
    ModuloNavegacion("dashboard", "Inicio", "Resumen operativo del sistema y tablero principal.", "home.svg", "modulo.dashboard"),
    ModuloNavegacion("barrios", "Barrios", "Gestión de barrios y organización territorial.", "map-2.svg", "modulo.barrios"),
    ModuloNavegacion("usuarios", "Usuarios", "Gestión de usuarios, acceso y roles operativos.", "users.svg", "modulo.usuarios"),
    ModuloNavegacion("abonados", "Abonados", "Registro de abonados y seguimiento administrativo.", "id.svg", "modulo.abonados"),
    ModuloNavegacion("casas", "Casas", "Control de viviendas, servicio y relación con abonados.", "home-2.svg", "modulo.casas"),
    ModuloNavegacion("pagos", "Pagos", "Cobro mensual, conceptos operativos y comprobantes.", "receipt-2.svg", "modulo.pagos"),
    ModuloNavegacion("historial_pagos", "Historial de pagos", "Consulta comprobantes emitidos y reimpresión operativa.", "clock.svg", "modulo.historial_pagos"),
    ModuloNavegacion("morosidad", "Morosidad", "Seguimiento de deuda vencida y riesgo de cobro.", "urgent.svg", "modulo.morosidad"),
    ModuloNavegacion("planes_pago", "Planes de pago", "Acuerdos, cuotas y saldos financiados.", "calendar-stats.svg", "modulo.planes_pago"),
    ModuloNavegacion("reportes", "Reportes", "Consultas administrativas, indicadores y exportaciones.", "chart-bar.svg", "modulo.reportes"),
    ModuloNavegacion("configuracion", "Configuración", "Parámetros operativos, comprobantes y control local.", "settings-2.svg", "modulo.configuracion"),
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
            analitica=self.repositorio_modulo_principal.obtener_analitica_dashboard(),
            modulos=modulos_visibles,
        )

    @staticmethod
    def _resolver_perfil(usuario: UsuarioAutenticado) -> str:
        if "ADMINISTRADOR" in usuario.roles:
            return "ADMINISTRADOR"
        if "CAJERO" in usuario.roles:
            return "CAJERO"
        return "CONSULTA"

    @staticmethod
    def _puede_ver_modulo(usuario: UsuarioAutenticado, modulo: ModuloNavegacion) -> bool:
        if modulo.permiso_requerido is None:
            return True
        return usuario.tiene_permiso(modulo.permiso_requerido)
