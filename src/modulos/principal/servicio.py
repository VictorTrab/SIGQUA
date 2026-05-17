"""Servicios del modulo principal."""

from __future__ import annotations

from modulos.autenticacion.entidades import UsuarioAutenticado
from modulos.principal.entidades import EstadoModuloPrincipal, ModuloNavegacion
from modulos.principal.repositorio import RepositorioModuloPrincipal


MODULOS_OPERATIVOS = (
    ModuloNavegacion("dashboard", "Inicio", "Resumen operativo del sistema y tablero principal.", "home.svg"),
    ModuloNavegacion("barrios", "Barrios", "Gestion de barrios y organizacion territorial.", "map-2.svg"),
    ModuloNavegacion("usuarios", "Usuarios", "Gestion de usuarios, acceso y roles operativos.", "users.svg", "usuarios.gestionar"),
    ModuloNavegacion("abonados", "Abonados", "Registro de abonados y seguimiento administrativo.", "id.svg"),
    ModuloNavegacion("casas", "Casas", "Control de viviendas, servicio y relacion con abonados.", "home-2.svg"),
    ModuloNavegacion("pagos", "Pagos", "Cobro mensual, conceptos operativos y comprobantes.", "receipt-2.svg"),
    ModuloNavegacion("historial_pagos", "Historial de pagos", "Consulta comprobantes emitidos y reimpresion operativa.", "clock.svg"),
    ModuloNavegacion("morosidad", "Morosidad", "Seguimiento de deuda vencida y riesgo de cobro.", "urgent.svg"),
    ModuloNavegacion("planes_pago", "Planes de pago", "Acuerdos, cuotas y saldos financiados.", "calendar-stats.svg"),
    ModuloNavegacion("reportes", "Reportes", "Consultas administrativas, indicadores y exportaciones.", "chart-bar.svg"),
    ModuloNavegacion("configuracion", "Configuracion", "Parametros operativos, comprobantes y control local.", "settings-2.svg"),
    ModuloNavegacion("mantenimiento", "Mantenimiento", "Herramientas tecnicas sensibles y soporte avanzado.", "tool.svg", "mantenimiento.ver", True),
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
