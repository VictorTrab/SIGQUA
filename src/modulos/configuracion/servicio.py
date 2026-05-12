"""Servicios del modulo de configuracion."""

from __future__ import annotations

from comun.configuracion.gestor_rutas import GestorRutas
from modulos.autenticacion.servicio import MAXIMO_INTENTOS_FALLIDOS
from modulos.configuracion.entidades import (
    DatosJunta,
    EstadoConfiguracion,
    InformacionConfiguracion,
    ParametrosCobro,
    ResultadoGestionConfiguracion,
    SeguridadConfiguracion,
)
from modulos.configuracion.repositorio import RepositorioConfiguracion


CLAVES_DATOS_JUNTA = (
    "junta.nombre",
    "junta.telefono",
    "junta.correo",
    "junta.direccion",
)
CLAVES_COBRO = (
    "cobro.precio_mensual_centavos",
    "cobro.mora_activa",
    "cobro.multa_mora_automatica_activa",
    "cobro.multa_mora_automatica_centavos",
    "cobro.corte_automatico_activo",
    "sistema.nombre",
    "sistema.version",
)


class ServicioConfiguracion:
    """Orquesta lectura y actualizacion de configuracion operativa real."""

    DURACION_SESION_HORAS = 8

    def __init__(
        self,
        repositorio_configuracion: RepositorioConfiguracion,
        gestor_rutas: GestorRutas,
    ) -> None:
        self._repositorio_configuracion = repositorio_configuracion
        self._gestor_rutas = gestor_rutas

    def obtener_estado(self) -> EstadoConfiguracion:
        claves = CLAVES_DATOS_JUNTA + CLAVES_COBRO
        parametros = self._repositorio_configuracion.listar_por_claves(claves)

        datos_junta = DatosJunta(
            nombre=parametros.get("junta.nombre").valor if "junta.nombre" in parametros else "",
            telefono=parametros.get("junta.telefono").valor if "junta.telefono" in parametros else "",
            correo=parametros.get("junta.correo").valor if "junta.correo" in parametros else "",
            direccion=parametros.get("junta.direccion").valor if "junta.direccion" in parametros else "",
        )
        parametros_cobro = ParametrosCobro(
            precio_mensual_centavos=self._a_entero(
                parametros.get("cobro.precio_mensual_centavos").valor
                if "cobro.precio_mensual_centavos" in parametros
                else "0"
            ),
            mora_visible=self._a_booleano(
                parametros.get("cobro.mora_activa").valor
                if "cobro.mora_activa" in parametros
                else "1"
            ),
            multa_mora_automatica_activa=self._a_booleano(
                parametros.get("cobro.multa_mora_automatica_activa").valor
                if "cobro.multa_mora_automatica_activa" in parametros
                else "0"
            ),
            multa_mora_automatica_centavos=self._a_entero(
                parametros.get("cobro.multa_mora_automatica_centavos").valor
                if "cobro.multa_mora_automatica_centavos" in parametros
                else "0"
            ),
            corte_automatico_activo=self._a_booleano(
                parametros.get("cobro.corte_automatico_activo").valor
                if "cobro.corte_automatico_activo" in parametros
                else "0"
            ),
        )
        informacion = InformacionConfiguracion(
            nombre_sistema=parametros.get("sistema.nombre").valor if "sistema.nombre" in parametros else "SICAP",
            version_sistema=parametros.get("sistema.version").valor if "sistema.version" in parametros else "",
            ruta_base_datos=str(self._gestor_rutas.obtener_ruta_base_datos()),
            modo_operacion="Autenticacion local sin correo y sin Resend",
            ultima_actualizacion=max(
                (
                    parametro.actualizado_en
                    for parametro in parametros.values()
                    if parametro.actualizado_en
                ),
                default="",
            ),
        )
        seguridad = SeguridadConfiguracion(
            autenticacion_local=True,
            maximo_intentos_fallidos=MAXIMO_INTENTOS_FALLIDOS,
            duracion_sesion_horas=self.DURACION_SESION_HORAS,
            restablecimiento_administrativo=True,
            cambio_contrasena_obligatorio=True,
        )
        return EstadoConfiguracion(
            datos_junta=datos_junta,
            parametros_cobro=parametros_cobro,
            seguridad=seguridad,
            informacion=informacion,
        )

    def guardar_datos_junta(
        self,
        nombre: str,
        telefono: str,
        correo: str,
        direccion: str,
        actor_id: int | None = None,
    ) -> ResultadoGestionConfiguracion:
        nombre = nombre.strip()
        telefono = telefono.strip()
        correo = correo.strip()
        direccion = direccion.strip()

        if not nombre:
            return ResultadoGestionConfiguracion(
                False,
                "Indica el nombre de la junta para continuar.",
                "VALIDACION",
            )
        if not direccion:
            return ResultadoGestionConfiguracion(
                False,
                "Indica la direccion operativa de la junta.",
                "VALIDACION",
            )
        try:
            self._repositorio_configuracion.actualizar_valores(
                {
                    "junta.nombre": nombre,
                    "junta.telefono": telefono,
                    "junta.correo": correo,
                    "junta.direccion": direccion,
                },
                actor_id=actor_id,
            )
        except Exception:
            return ResultadoGestionConfiguracion(
                False,
                "No fue posible guardar los datos de la junta.",
                "ERROR_SQLITE",
            )
        return ResultadoGestionConfiguracion(True, "Datos de la junta actualizados.", "OK")

    def guardar_parametros_cobro(
        self,
        precio_mensual_centavos: int,
        multa_mora_automatica_activa: bool,
        multa_mora_automatica_centavos: int,
        corte_automatico_activo: bool,
        actor_id: int | None = None,
    ) -> ResultadoGestionConfiguracion:
        if precio_mensual_centavos < 0:
            return ResultadoGestionConfiguracion(
                False,
                "El precio mensual no puede ser negativo.",
                "VALIDACION",
            )
        if multa_mora_automatica_centavos < 0:
            return ResultadoGestionConfiguracion(
                False,
                "La multa automatica por mora no puede ser negativa.",
                "VALIDACION",
            )
        if not multa_mora_automatica_activa:
            multa_mora_automatica_centavos = 0
        try:
            self._repositorio_configuracion.actualizar_valores(
                {
                    "cobro.precio_mensual_centavos": str(precio_mensual_centavos),
                    "cobro.multa_mora_automatica_activa": "1" if multa_mora_automatica_activa else "0",
                    "cobro.multa_mora_automatica_centavos": str(multa_mora_automatica_centavos),
                    "cobro.corte_automatico_activo": "1" if corte_automatico_activo else "0",
                },
                actor_id=actor_id,
            )
        except Exception:
            return ResultadoGestionConfiguracion(
                False,
                "No fue posible actualizar los parametros de cobro.",
                "ERROR_SQLITE",
            )
        return ResultadoGestionConfiguracion(True, "Parametros de cobro actualizados.", "OK")

    @staticmethod
    def formatear_moneda(valor_centavos: int) -> str:
        return f"L {valor_centavos / 100:,.2f}"

    @staticmethod
    def _a_booleano(valor: str) -> bool:
        return str(valor).strip() in {"1", "true", "TRUE", "si", "SI"}

    @staticmethod
    def _a_entero(valor: str) -> int:
        try:
            return int(str(valor).strip() or "0")
        except ValueError:
            return 0
