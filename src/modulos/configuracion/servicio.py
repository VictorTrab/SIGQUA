"""Servicios del modulo de configuracion."""

from __future__ import annotations

from comun.configuracion.gestor_rutas import GestorRutas
from modulos.autenticacion.servicio import MAXIMO_INTENTOS_FALLIDOS
from modulos.configuracion.entidades import (
    DatosJunta,
    EstadoConfiguracion,
    FacturaConfiguracion,
    InformacionConfiguracion,
    OperacionConfiguracion,
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
    "cobro.meses_para_corte",
    "cobro.permitir_pago_adelantado",
    "cobro.meses_adelanto_maximo",
)
CLAVES_FACTURA = (
    "factura.texto_pie",
    "factura.formato_salida",
)
CLAVES_SISTEMA = (
    "sistema.nombre",
    "sistema.version",
    "sistema.respaldo_automatico",
)
FORMATOS_SALIDA_FACTURA_VALIDOS = ("PDF", "HTML", "TEXTO")


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
        claves = CLAVES_DATOS_JUNTA + CLAVES_COBRO + CLAVES_FACTURA + CLAVES_SISTEMA
        parametros = self._repositorio_configuracion.listar_por_claves(claves)
        correlativo_actual, ultimo_comprobante, total_comprobantes = (
            self._repositorio_configuracion.obtener_resumen_comprobantes()
        )
        ultimo_respaldo_en, ultimo_respaldo_estado, total_respaldos = (
            self._repositorio_configuracion.obtener_resumen_respaldos()
        )

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
            meses_para_corte=self._a_entero(
                parametros.get("cobro.meses_para_corte").valor
                if "cobro.meses_para_corte" in parametros
                else "0"
            ),
            permitir_pago_adelantado=self._a_booleano(
                parametros.get("cobro.permitir_pago_adelantado").valor
                if "cobro.permitir_pago_adelantado" in parametros
                else "0"
            ),
            meses_adelanto_maximo=self._a_entero(
                parametros.get("cobro.meses_adelanto_maximo").valor
                if "cobro.meses_adelanto_maximo" in parametros
                else "0"
            ),
        )
        factura = FacturaConfiguracion(
            texto_pie=parametros.get("factura.texto_pie").valor if "factura.texto_pie" in parametros else "",
            formato_salida=(
                parametros.get("factura.formato_salida").valor.upper()
                if "factura.formato_salida" in parametros
                else "PDF"
            ),
            correlativo_actual=self._formatear_correlativo(correlativo_actual),
            proximo_correlativo=self._formatear_correlativo(correlativo_actual + 1),
            ultimo_comprobante_emitido=(
                ultimo_comprobante if ultimo_comprobante else "Sin comprobantes emitidos"
            ),
            total_comprobantes_emitidos=total_comprobantes,
        )
        operacion = OperacionConfiguracion(
            respaldo_automatico=self._a_booleano(
                parametros.get("sistema.respaldo_automatico").valor
                if "sistema.respaldo_automatico" in parametros
                else "0"
            ),
            ultimo_respaldo_en=ultimo_respaldo_en,
            ultimo_respaldo_estado=ultimo_respaldo_estado or "SIN_REGISTRO",
            total_respaldos=total_respaldos,
            ruta_exportaciones_comprobantes=str(
                self._gestor_rutas.obtener_ruta_exportaciones_comprobantes()
            ),
            ruta_exportaciones_reportes=str(
                self._gestor_rutas.obtener_ruta_exportaciones_reportes()
            ),
        )
        informacion = InformacionConfiguracion(
            nombre_sistema=parametros.get("sistema.nombre").valor if "sistema.nombre" in parametros else "SICAP",
            version_sistema=parametros.get("sistema.version").valor if "sistema.version" in parametros else "",
            ruta_base_datos=str(self._gestor_rutas.obtener_ruta_base_datos()),
            modo_operacion="Autenticacion local sin correo y con soporte administrativo",
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
            factura=factura,
            operacion=operacion,
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

    def guardar_parametros_factura(
        self,
        texto_pie: str,
        formato_salida: str,
        actor_id: int | None = None,
    ) -> ResultadoGestionConfiguracion:
        texto_pie = texto_pie.strip()
        formato_salida = formato_salida.strip().upper()

        if not texto_pie:
            return ResultadoGestionConfiguracion(
                False,
                "Indica el texto inferior del comprobante.",
                "VALIDACION",
            )
        if formato_salida not in FORMATOS_SALIDA_FACTURA_VALIDOS:
            return ResultadoGestionConfiguracion(
                False,
                "Selecciona un formato de salida valido.",
                "VALIDACION",
            )
        try:
            self._repositorio_configuracion.actualizar_valores(
                {
                    "factura.texto_pie": texto_pie,
                    "factura.formato_salida": formato_salida,
                },
                actor_id=actor_id,
            )
        except Exception:
            return ResultadoGestionConfiguracion(
                False,
                "No fue posible actualizar la configuracion de comprobantes.",
                "ERROR_SQLITE",
            )
        return ResultadoGestionConfiguracion(
            True,
            "Configuracion de factura y comprobantes actualizada.",
            "OK",
        )

    def guardar_parametros_cobro(
        self,
        precio_mensual_centavos: int,
        multa_mora_automatica_activa: bool,
        multa_mora_automatica_centavos: int,
        corte_automatico_activo: bool,
        meses_para_corte: int,
        permitir_pago_adelantado: bool,
        meses_adelanto_maximo: int,
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
        if meses_para_corte < 1:
            return ResultadoGestionConfiguracion(
                False,
                "Define al menos un mes para el umbral de corte o alerta.",
                "VALIDACION",
            )
        if permitir_pago_adelantado and meses_adelanto_maximo < 1:
            return ResultadoGestionConfiguracion(
                False,
                "Indica el maximo de meses adelantados permitidos.",
                "VALIDACION",
            )
        if not multa_mora_automatica_activa:
            multa_mora_automatica_centavos = 0
        if not permitir_pago_adelantado:
            meses_adelanto_maximo = 0
        try:
            self._repositorio_configuracion.actualizar_valores(
                {
                    "cobro.precio_mensual_centavos": str(precio_mensual_centavos),
                    "cobro.multa_mora_automatica_activa": "1" if multa_mora_automatica_activa else "0",
                    "cobro.multa_mora_automatica_centavos": str(multa_mora_automatica_centavos),
                    "cobro.corte_automatico_activo": "1" if corte_automatico_activo else "0",
                    "cobro.meses_para_corte": str(meses_para_corte),
                    "cobro.permitir_pago_adelantado": "1" if permitir_pago_adelantado else "0",
                    "cobro.meses_adelanto_maximo": str(meses_adelanto_maximo),
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

    def guardar_operacion_respaldo(
        self,
        respaldo_automatico: bool,
        actor_id: int | None = None,
    ) -> ResultadoGestionConfiguracion:
        try:
            self._repositorio_configuracion.actualizar_valores(
                {"sistema.respaldo_automatico": "1" if respaldo_automatico else "0"},
                actor_id=actor_id,
            )
        except Exception:
            return ResultadoGestionConfiguracion(
                False,
                "No fue posible actualizar el control de respaldos.",
                "ERROR_SQLITE",
            )
        return ResultadoGestionConfiguracion(True, "Control de respaldo actualizado.", "OK")

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

    @staticmethod
    def _formatear_correlativo(numero: int) -> str:
        return f"REC-{max(numero, 0):05d}"
