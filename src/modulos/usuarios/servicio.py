"""Servicios del modulo de usuarios."""

from __future__ import annotations

import csv
import sqlite3
from datetime import datetime

from comun.seguridad import generar_hash_contrasena
from modulos.autenticacion.entidades import UsuarioAutenticado
from modulos.usuarios.entidades import FormularioUsuario, ResumenUsuarios, ResultadoGestionUsuarios, RolSistema, UsuarioSistema
from modulos.usuarios.repositorio import RepositorioUsuarios


FORMATO_FECHA_BD = "%Y-%m-%d %H:%M:%S"
ESTADOS_OPERATIVOS_EDITABLES = {"ACTIVO", "INACTIVO"}
FILTRO_USUARIOS_TODOS = "todos"
FILTRO_USUARIOS_ACTIVOS = "activos"
FILTRO_USUARIOS_INACTIVOS = "inactivos"
FILTRO_USUARIOS_ADMINISTRADORES = "administradores"
PERMISO_MODULO_USUARIOS = "modulo.usuarios"
ROLES_VISIBLES = ("ADMINISTRADOR", "CAJERO", "CONSULTA")


class ServicioUsuarios:
    """Orquesta la logica de negocio del modulo."""

    def __init__(self, repositorio_usuarios: RepositorioUsuarios):
        self.repositorio_usuarios = repositorio_usuarios

    def listar_usuarios_para_administracion(
        self,
        actor: UsuarioAutenticado,
    ) -> list[UsuarioSistema]:
        return self.repositorio_usuarios.listar_operativos_visibles()

    def listar_roles_asignables(
        self,
        actor: UsuarioAutenticado,
    ) -> list[RolSistema]:
        return [
            rol
            for rol in self.repositorio_usuarios.listar_roles_operativos()
            if rol.estado == "ACTIVO" and rol.nombre in ROLES_VISIBLES
        ]

    def obtener_resumen(self, usuarios: list[UsuarioSistema]) -> ResumenUsuarios:
        hoy = datetime.now().date()
        accesos_hoy = 0
        for usuario in usuarios:
            fecha_acceso = self._parsear_fecha(usuario.ultimo_acceso_en)
            if fecha_acceso is not None and fecha_acceso.date() == hoy:
                accesos_hoy += 1
        return ResumenUsuarios(
            total_usuarios=len(usuarios),
            usuarios_activos=sum(1 for usuario in usuarios if usuario.estado == "ACTIVO"),
            administradores=sum(1 for usuario in usuarios if "ADMINISTRADOR" in usuario.roles),
            accesos_hoy=accesos_hoy,
        )

    def filtrar_usuarios(
        self,
        usuarios: list[UsuarioSistema],
        texto: str = "",
        filtro_rapido: str = FILTRO_USUARIOS_TODOS,
        rol: str = FILTRO_USUARIOS_TODOS,
    ) -> list[UsuarioSistema]:
        texto_normalizado = texto.strip().casefold()
        rol_normalizado = rol.strip().casefold()

        def coincide_busqueda(usuario: UsuarioSistema) -> bool:
            if not texto_normalizado:
                return True
            universo = (
                usuario.nombre_usuario,
                usuario.nombre_completo,
                usuario.correo,
            )
            return any(texto_normalizado in valor.casefold() for valor in universo if valor)

        def coincide_filtro(usuario: UsuarioSistema) -> bool:
            if filtro_rapido == FILTRO_USUARIOS_ACTIVOS:
                return usuario.estado == "ACTIVO"
            if filtro_rapido == FILTRO_USUARIOS_INACTIVOS:
                return usuario.estado != "ACTIVO"
            if filtro_rapido == FILTRO_USUARIOS_ADMINISTRADORES:
                return "ADMINISTRADOR" in usuario.roles
            return True

        def coincide_rol(usuario: UsuarioSistema) -> bool:
            if rol_normalizado in {"", FILTRO_USUARIOS_TODOS}:
                return True
            return any(rol_normalizado == nombre.casefold() for nombre in usuario.roles)

        return [
            usuario
            for usuario in usuarios
            if coincide_busqueda(usuario) and coincide_filtro(usuario) and coincide_rol(usuario)
        ]

    def crear_usuario_operativo(
        self,
        actor: UsuarioAutenticado,
        formulario: FormularioUsuario,
    ) -> ResultadoGestionUsuarios:
        if not self._puede_gestionar_usuarios(actor):
            return ResultadoGestionUsuarios(False, "No tienes permisos para crear usuarios.", "PERMISO_DENEGADO")

        validacion = self._validar_formulario(formulario)
        if validacion is not None:
            return validacion
        validacion = self._validar_contrasena(
            formulario.contrasena,
            formulario.confirmacion_contrasena,
        )
        if validacion is not None:
            return validacion

        rol = self._resolver_rol_asignable(formulario.rol_id, actor)
        if rol is None:
            return ResultadoGestionUsuarios(False, "Selecciona un rol visible valido.", "VALIDACION")

        momento = self._formatear_fecha(datetime.now())
        try:
            self.repositorio_usuarios.crear_usuario_operativo(
                actor_id=actor.identificador,
                formulario=formulario,
                nuevo_hash=generar_hash_contrasena(formulario.contrasena),
                momento=momento,
            )
        except sqlite3.IntegrityError:
            return ResultadoGestionUsuarios(
                False,
                "El nombre de usuario o el correo ya existen en el sistema.",
                "DUPLICADO",
            )
        return ResultadoGestionUsuarios(
            True,
            "Usuario creado correctamente.",
            "OK",
        )

    def actualizar_usuario_operativo(
        self,
        actor: UsuarioAutenticado,
        formulario: FormularioUsuario,
    ) -> ResultadoGestionUsuarios:
        if formulario.identificador is None:
            return ResultadoGestionUsuarios(False, "No se identifico el usuario a editar.", "VALIDACION")
        if not self._puede_gestionar_usuarios(actor):
            return ResultadoGestionUsuarios(False, "No tienes permisos para editar usuarios.", "PERMISO_DENEGADO")

        objetivo = self.repositorio_usuarios.obtener_por_identificador(formulario.identificador)
        if objetivo is None:
            return ResultadoGestionUsuarios(False, "El usuario indicado no existe.", "USUARIO_NO_ENCONTRADO")
        if not self._puede_gestionar_usuario(actor, objetivo):
            return ResultadoGestionUsuarios(
                False,
                "No puedes editar usuarios tecnicos u ocultos.",
                "PERMISO_DENEGADO",
            )

        validacion = self._validar_formulario(formulario)
        if validacion is not None:
            return validacion

        rol = self._resolver_rol_asignable(formulario.rol_id, actor)
        if rol is None:
            return ResultadoGestionUsuarios(False, "Selecciona un rol visible valido.", "VALIDACION")

        momento = self._formatear_fecha(datetime.now())
        try:
            self.repositorio_usuarios.actualizar_usuario_operativo(
                actor_id=actor.identificador,
                formulario=formulario,
                momento=momento,
            )
        except sqlite3.IntegrityError:
            return ResultadoGestionUsuarios(
                False,
                "El nombre de usuario o el correo ya existen en el sistema.",
                "DUPLICADO",
            )
        return ResultadoGestionUsuarios(True, "Usuario actualizado correctamente.", "OK")

    def cambiar_estado_usuario_operativo(
        self,
        actor: UsuarioAutenticado,
        nombre_usuario_objetivo: str,
    ) -> ResultadoGestionUsuarios:
        if not self._puede_gestionar_usuarios(actor):
            return ResultadoGestionUsuarios(False, "No tienes permisos para cambiar estados.", "PERMISO_DENEGADO")

        usuario_objetivo = self.repositorio_usuarios.obtener_por_nombre_usuario(nombre_usuario_objetivo.strip())
        if usuario_objetivo is None:
            return ResultadoGestionUsuarios(False, "El usuario indicado no existe.", "USUARIO_NO_ENCONTRADO")
        if not self._puede_gestionar_usuario(actor, usuario_objetivo):
            return ResultadoGestionUsuarios(
                False,
                "No puedes modificar usuarios tecnicos u ocultos.",
                "PERMISO_DENEGADO",
            )

        nuevo_estado = "INACTIVO" if usuario_objetivo.estado == "ACTIVO" else "ACTIVO"
        momento = self._formatear_fecha(datetime.now())
        self.repositorio_usuarios.cambiar_estado_usuario(
            actor_id=actor.identificador,
            objetivo_id=usuario_objetivo.identificador,
            nuevo_estado=nuevo_estado,
            momento=momento,
        )
        return ResultadoGestionUsuarios(
            True,
            f"Usuario {nuevo_estado.lower()} correctamente.",
            "OK",
        )

    def restablecer_contrasena_administrativa(
        self,
        actor: UsuarioAutenticado,
        nombre_usuario_objetivo: str,
        nueva_contrasena: str,
        confirmacion_contrasena: str,
    ) -> ResultadoGestionUsuarios:
        if not self._puede_gestionar_usuarios(actor):
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
                mensaje="No puedes gestionar usuarios tecnicos u ocultos.",
                codigo="PERMISO_DENEGADO",
            )

        validacion = self._validar_contrasena(nueva_contrasena, confirmacion_contrasena)
        if validacion is not None:
            return validacion
        momento = self._formatear_fecha(datetime.now())
        self.repositorio_usuarios.restablecer_contrasena_administrativa(
            actor_id=actor.identificador,
            objetivo_id=usuario_objetivo.identificador,
            nuevo_hash=generar_hash_contrasena(nueva_contrasena),
            momento=momento,
        )
        return ResultadoGestionUsuarios(
            exito=True,
            mensaje="Contrasena restablecida correctamente.",
            codigo="OK",
        )

    def desbloquear_usuario_operativo(
        self,
        actor: UsuarioAutenticado,
        nombre_usuario_objetivo: str,
    ) -> ResultadoGestionUsuarios:
        if not self._puede_gestionar_usuarios(actor):
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
                mensaje="No puedes desbloquear usuarios tecnicos u ocultos.",
                codigo="PERMISO_DENEGADO",
            )

        momento = self._formatear_fecha(datetime.now())
        self.repositorio_usuarios.desbloquear_usuario(
            actor_id=actor.identificador,
            objetivo_id=usuario_objetivo.identificador,
            momento=momento,
        )
        return ResultadoGestionUsuarios(
            exito=True,
            mensaje="Usuario desbloqueado correctamente.",
            codigo="OK",
        )

    def exportar_csv(
        self,
        ruta_destino: str,
        usuarios: list[UsuarioSistema],
    ) -> ResultadoGestionUsuarios:
        try:
            with open(ruta_destino, "w", newline="", encoding="utf-8") as archivo:
                escritor = csv.writer(archivo)
                escritor.writerow(
                    [
                        "usuario",
                        "nombre_completo",
                        "correo",
                        "rol_principal",
                        "estado",
                        "ultimo_acceso",
                        "creado_en",
                    ]
                )
                for usuario in usuarios:
                    escritor.writerow(
                        [
                            usuario.nombre_usuario,
                            usuario.nombre_completo,
                            usuario.correo,
                            usuario.rol_principal,
                            usuario.estado,
                            self.formatear_fecha_hora(usuario.ultimo_acceso_en),
                            self.formatear_fecha_hora(usuario.creado_en),
                        ]
                    )
        except OSError:
            return ResultadoGestionUsuarios(False, "No fue posible exportar el archivo CSV.", "ERROR_IO")
        return ResultadoGestionUsuarios(True, "Usuarios exportados correctamente.", "OK")

    @staticmethod
    def formatear_fecha_hora(fecha_texto: str | None) -> str:
        fecha = ServicioUsuarios._parsear_fecha(fecha_texto)
        if fecha is None:
            return "Sin registro"
        return fecha.strftime("%d/%m/%Y %I:%M %p")

    @staticmethod
    def _puede_gestionar_usuario(actor: UsuarioAutenticado, objetivo: UsuarioSistema) -> bool:
        return not objetivo.es_tecnico and not objetivo.es_oculto

    def _resolver_rol_asignable(self, rol_id: int, actor: UsuarioAutenticado) -> RolSistema | None:
        for rol in self.listar_roles_asignables(actor):
            if rol.identificador == rol_id:
                return rol
        return None

    @staticmethod
    def _formatear_fecha(fecha: datetime) -> str:
        return fecha.strftime(FORMATO_FECHA_BD)

    @staticmethod
    def _parsear_fecha(fecha_texto: str | None) -> datetime | None:
        if not fecha_texto:
            return None
        try:
            return datetime.strptime(fecha_texto, FORMATO_FECHA_BD)
        except ValueError:
            return None

    @staticmethod
    def _validar_contrasena(
        contrasena: str,
        confirmacion: str,
    ) -> ResultadoGestionUsuarios | None:
        if not contrasena or not confirmacion:
            return ResultadoGestionUsuarios(False, "Escribe y confirma la contrasena.", "VALIDACION")
        if len(contrasena) < 8:
            return ResultadoGestionUsuarios(
                False,
                "La contrasena debe tener al menos 8 caracteres.",
                "VALIDACION",
            )
        if contrasena != confirmacion:
            return ResultadoGestionUsuarios(False, "Las contrasenas no coinciden.", "VALIDACION")
        return None

    @staticmethod
    def _validar_formulario(
        formulario: FormularioUsuario,
    ) -> ResultadoGestionUsuarios | None:
        if not formulario.nombre_completo.strip():
            return ResultadoGestionUsuarios(False, "Indica el nombre completo del usuario.", "VALIDACION")
        if not formulario.nombre_usuario.strip():
            return ResultadoGestionUsuarios(False, "Indica el nombre de usuario.", "VALIDACION")
        if not formulario.correo.strip():
            return ResultadoGestionUsuarios(False, "Indica el correo del usuario.", "VALIDACION")
        if "@" not in formulario.correo:
            return ResultadoGestionUsuarios(False, "Indica un correo valido.", "VALIDACION")
        if formulario.estado not in ESTADOS_OPERATIVOS_EDITABLES:
            return ResultadoGestionUsuarios(False, "Selecciona un estado operativo valido.", "VALIDACION")
        if formulario.rol_id <= 0:
            return ResultadoGestionUsuarios(False, "Selecciona un rol valido.", "VALIDACION")
        return None

    @staticmethod
    def _puede_gestionar_usuarios(actor: UsuarioAutenticado) -> bool:
        return actor.tiene_permiso(PERMISO_MODULO_USUARIOS)
