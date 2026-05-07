"""Servicios del modulo de usuarios."""

from __future__ import annotations

import json
from datetime import datetime

from comun.seguridad import generar_hash_contrasena
from modulos.autenticacion.entidades import UsuarioAutenticado
from modulos.usuarios.entidades import ResultadoGestionUsuarios, UsuarioSistema
from modulos.usuarios.repositorio import RepositorioUsuarios


FORMATO_FECHA_BD = "%Y-%m-%d %H:%M:%S"


class ServicioUsuarios:
    """Orquesta la logica de negocio del modulo."""

    def __init__(self, repositorio_usuarios: RepositorioUsuarios):
        self.repositorio_usuarios = repositorio_usuarios

    def listar_usuarios_para_administracion(
        self,
        actor: UsuarioAutenticado,
    ) -> list[UsuarioSistema]:
        if actor.es_superadministrador():
            operativos = self.repositorio_usuarios.listar_operativos_visibles()
            tecnicos = self.repositorio_usuarios.listar_tecnicos()
            return operativos + tecnicos
        return self.repositorio_usuarios.listar_operativos_visibles()

    def restablecer_contrasena_administrativa(
        self,
        actor: UsuarioAutenticado,
        nombre_usuario_objetivo: str,
        nueva_contrasena_temporal: str,
        confirmacion_contrasena: str,
    ) -> ResultadoGestionUsuarios:
        if not actor.tiene_permiso("usuarios.restablecer_contrasena") and not actor.es_superadministrador():
            return ResultadoGestionUsuarios(
                exito=False,
                mensaje="No tienes permisos para restablecer contrasenas.",
                codigo="PERMISO_DENEGADO",
            )

        nombre_usuario_objetivo = nombre_usuario_objetivo.strip()
        if not nombre_usuario_objetivo:
            return ResultadoGestionUsuarios(
                exito=False,
                mensaje="Indica el usuario objetivo.",
                codigo="VALIDACION",
            )

        if not nueva_contrasena_temporal or not confirmacion_contrasena:
            return ResultadoGestionUsuarios(
                exito=False,
                mensaje="Completa ambos campos de contrasena temporal.",
                codigo="VALIDACION",
            )

        if len(nueva_contrasena_temporal) < 8:
            return ResultadoGestionUsuarios(
                exito=False,
                mensaje="La contrasena temporal debe tener al menos 8 caracteres.",
                codigo="VALIDACION",
            )

        if nueva_contrasena_temporal != confirmacion_contrasena:
            return ResultadoGestionUsuarios(
                exito=False,
                mensaje="Las contrasenas no coinciden.",
                codigo="VALIDACION",
            )

        usuario_objetivo = self.repositorio_usuarios.obtener_por_nombre_usuario(nombre_usuario_objetivo)
        if usuario_objetivo is None:
            return ResultadoGestionUsuarios(
                exito=False,
                mensaje="El usuario indicado no existe.",
                codigo="USUARIO_NO_ENCONTRADO",
            )

        if not self._puede_gestionar_usuario(actor, usuario_objetivo):
            return ResultadoGestionUsuarios(
                exito=False,
                mensaje="No puedes gestionar usuarios tecnicos o superadministradores.",
                codigo="PERMISO_DENEGADO",
            )

        momento = self._formatear_fecha(datetime.now())
        self.repositorio_usuarios.restablecer_contrasena_administrativa(
            actor_id=actor.identificador,
            objetivo_id=usuario_objetivo.identificador,
            nuevo_hash=generar_hash_contrasena(nueva_contrasena_temporal),
            momento=momento,
        )
        return ResultadoGestionUsuarios(
            exito=True,
            mensaje=(
                "Contrasena temporal aplicada. El usuario debera cambiarla en su proximo acceso."
            ),
            codigo="OK",
        )

    def desbloquear_usuario_operativo(
        self,
        actor: UsuarioAutenticado,
        nombre_usuario_objetivo: str,
    ) -> ResultadoGestionUsuarios:
        if not actor.tiene_permiso("usuarios.desbloquear") and not actor.es_superadministrador():
            return ResultadoGestionUsuarios(
                exito=False,
                mensaje="No tienes permisos para desbloquear usuarios.",
                codigo="PERMISO_DENEGADO",
            )

        usuario_objetivo = self.repositorio_usuarios.obtener_por_nombre_usuario(
            nombre_usuario_objetivo.strip()
        )
        if usuario_objetivo is None:
            return ResultadoGestionUsuarios(
                exito=False,
                mensaje="El usuario indicado no existe.",
                codigo="USUARIO_NO_ENCONTRADO",
            )

        if not self._puede_gestionar_usuario(actor, usuario_objetivo):
            return ResultadoGestionUsuarios(
                exito=False,
                mensaje="No puedes desbloquear usuarios tecnicos o superadministradores.",
                codigo="PERMISO_DENEGADO",
            )

        momento = self._formatear_fecha(datetime.now())
        self.repositorio_usuarios.desbloquear_usuario(
            actor_id=actor.identificador,
            objetivo_id=usuario_objetivo.identificador,
            momento=momento,
        )
        self.repositorio_usuarios.registrar_auditoria(
            usuario_id=actor.identificador,
            accion="DESBLOQUEAR_USUARIO",
            entidad="usuarios",
            entidad_id=usuario_objetivo.identificador,
            resumen=f"Desbloqueo administrativo del usuario {usuario_objetivo.nombre_usuario}",
            datos_antes_json=json.dumps({"estado": usuario_objetivo.estado}, ensure_ascii=True),
            datos_despues_json=json.dumps({"estado": "ACTIVO"}, ensure_ascii=True),
        )
        return ResultadoGestionUsuarios(
            exito=True,
            mensaje="Usuario desbloqueado correctamente.",
            codigo="OK",
        )

    @staticmethod
    def _puede_gestionar_usuario(actor: UsuarioAutenticado, objetivo: UsuarioSistema) -> bool:
        if actor.es_superadministrador():
            return True
        return not objetivo.es_tecnico and not objetivo.es_oculto and not objetivo.es_superadministrador()

    @staticmethod
    def _formatear_fecha(fecha: datetime) -> str:
        return fecha.strftime(FORMATO_FECHA_BD)

