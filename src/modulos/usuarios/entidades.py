"""Entidades del modulo de usuarios."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class PermisoSistema:
    """Representa un permiso real del sistema."""

    codigo: str
    nombre: str
    descripcion: str
    modulo: str


@dataclass(slots=True)
class RolSistema:
    """Representa un rol visible dentro del modulo."""

    identificador: int
    nombre: str
    descripcion: str
    estado: str
    es_sistema: bool
    total_usuarios: int = 0
    permisos: tuple[PermisoSistema, ...] = ()


@dataclass(slots=True)
class UsuarioSistema:
    """Representa un usuario recuperado desde la persistencia."""

    identificador: int
    nombre_usuario: str
    nombre_completo: str
    correo: str
    estado: str
    es_tecnico: bool = False
    es_oculto: bool = False
    requiere_cambio_contrasena: bool = False
    intentos_fallidos: int = 0
    bloqueado_hasta: str | None = None
    roles: tuple[str, ...] = ()
    permisos: frozenset[str] = frozenset()
    ultimo_acceso_en: str | None = None
    creado_en: str | None = None
    actualizado_en: str | None = None
    creado_por_nombre: str = ""
    actualizado_por_nombre: str = ""
    observaciones: str = ""
    total_sesiones: int = 0

    def tiene_permiso(self, codigo_permiso: str) -> bool:
        return codigo_permiso in self.permisos

    @property
    def rol_principal(self) -> str:
        return self.roles[0] if self.roles else "Sin rol"


@dataclass(slots=True)
class ResumenUsuarios:
    """Metricas visibles en las tarjetas resumen del modulo."""

    total_usuarios: int
    usuarios_activos: int
    administradores: int
    accesos_hoy: int


@dataclass(slots=True)
class FormularioUsuario:
    """Datos solicitados desde el formulario de creacion o edicion."""

    identificador: int | None
    nombre_usuario: str
    nombre_completo: str
    correo: str
    estado: str
    rol_id: int
    observaciones: str
    contrasena: str = ""
    confirmacion_contrasena: str = ""


@dataclass(slots=True)
class ResultadoGestionUsuarios:
    """Resultado generico de operaciones del modulo."""

    exito: bool
    mensaje: str
    codigo: str = ""
