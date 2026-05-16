"""Servicios del modulo principal."""

from __future__ import annotations

from modulos.autenticacion.entidades import UsuarioAutenticado
from modulos.principal.entidades import (
    EstadoModuloPrincipal,
    MensajeCabeceraPrincipal,
    ModuloNavegacion,
    ResumenOperativoCabecera,
)
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
        resumen_cabecera = self.repositorio_modulo_principal.obtener_resumen_operativo_cabecera()
        notificaciones_criticas = self._construir_notificaciones_criticas(resumen_cabecera)
        return EstadoModuloPrincipal(
            nombre_usuario=usuario.nombre_usuario,
            nombre_completo=usuario.nombre_completo,
            perfil=self._resolver_perfil(usuario),
            metricas=self.repositorio_modulo_principal.obtener_metricas_dashboard(),
            analitica=self.repositorio_modulo_principal.obtener_analitica_dashboard(),
            mensajes_cabecera=self._construir_mensajes_cabecera(notificaciones_criticas),
            evento_reciente=None,
            modulos=modulos_visibles,
            puede_abrir_mantenimiento=usuario.tiene_permiso("mantenimiento.ver"),
            notificaciones_criticas=notificaciones_criticas,
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

    def _construir_mensajes_cabecera(
        self,
        notificaciones_criticas: tuple[MensajeCabeceraPrincipal, ...],
    ) -> tuple[MensajeCabeceraPrincipal, ...]:
        if notificaciones_criticas:
            if any(mensaje.tipo == "ERROR" for mensaje in notificaciones_criticas):
                return (
                    MensajeCabeceraPrincipal(
                        "ERROR",
                        "Hay alertas criticas del sistema que requieren atencion.",
                        "alert-triangle.svg",
                    ),
                )
            return (
                MensajeCabeceraPrincipal(
                    "ADVERTENCIA",
                    "Existen advertencias tecnicas pendientes por revisar.",
                    "alert-triangle.svg",
                ),
            )
        return (
            MensajeCabeceraPrincipal(
                "CORRECTO",
                "Sistema funcionando correctamente.",
                "circle-check.svg",
            ),
        )

    def _construir_notificaciones_criticas(
        self,
        resumen: ResumenOperativoCabecera,
    ) -> tuple[MensajeCabeceraPrincipal, ...]:
        notificaciones: list[MensajeCabeceraPrincipal] = []

        estado_respaldo = (resumen.ultimo_respaldo_estado or "").upper()
        if resumen.respaldo_automatico and estado_respaldo == "FALLIDO":
            notificaciones.append(
                MensajeCabeceraPrincipal(
                    "ERROR",
                    "No se pudo generar el respaldo automatico.",
                    "alert-triangle.svg",
                )
            )
        elif resumen.respaldo_automatico and not resumen.ultimo_respaldo_en:
            notificaciones.append(
                MensajeCabeceraPrincipal(
                    "ADVERTENCIA",
                    "El respaldo automatico sigue activo pero aun no registra ejecuciones.",
                    "alert-triangle.svg",
                )
            )

        for severidad, mensaje in self.repositorio_modulo_principal.listar_eventos_criticos_sistema(
            limite=12
        ):
            tipo = self._mapear_tipo_evento(severidad)
            notificaciones.append(
                MensajeCabeceraPrincipal(
                    tipo,
                    mensaje,
                    self._resolver_icono_por_tipo(tipo),
                )
            )

        notificaciones_filtradas: list[MensajeCabeceraPrincipal] = []
        mensajes_vistos: set[tuple[str, str]] = set()
        for notificacion in notificaciones:
            clave = (notificacion.tipo, notificacion.mensaje)
            if clave in mensajes_vistos:
                continue
            mensajes_vistos.add(clave)
            notificaciones_filtradas.append(notificacion)
        return tuple(notificaciones_filtradas)

    @staticmethod
    def _mapear_tipo_evento(severidad: str) -> str:
        severidad_normalizada = (severidad or "INFO").upper()
        if severidad_normalizada in {"ERROR", "CRITICO"}:
            return "ERROR"
        if severidad_normalizada == "ADVERTENCIA":
            return "ADVERTENCIA"
        return "INFORMACION"

    @staticmethod
    def _resolver_icono_por_tipo(tipo: str) -> str:
        return {
            "CORRECTO": "circle-check.svg",
            "ADVERTENCIA": "alert-triangle.svg",
            "ERROR": "alert-triangle.svg",
            "INFORMACION": "info-circle.svg",
        }.get(tipo, "info-circle.svg")
