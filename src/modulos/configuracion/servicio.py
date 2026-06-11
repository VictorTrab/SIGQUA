"""Servicios del modulo de configuracion."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import os
import sys
import tempfile

from comun.configuracion.gestor_rutas import GestorRutas
from comun.configuracion.identidad_empresa import (
    CLAVES_IDENTIDAD_EMPRESA,
    CLAVES_IDENTIDAD_LEGADAS_JUNTA,
    construir_identidad_empresa,
)
from comun.respaldo import (
    ConfiguracionRespaldoLocal,
    ServicioRespaldoLocal,
)
from comun.logs import obtener_logger_sigqua
from comun.impresion_termica import TransporteWindowsRawEscpos
from modulos.configuracion.entidades import (
    EstadoConfiguracion,
    FacturaConfiguracion,
    IdentidadEmpresa,
    InformacionConfiguracion,
    OperacionConfiguracion,
    ParametrosCobro,
    ReportesPdfConfiguracion,
    ResultadoGestionConfiguracion,
    SeguridadConfiguracion,
)
from modulos.configuracion.repositorio import RepositorioConfiguracion
from modulos.comprobantes import ServicioComprobantes
from reportlab.pdfgen import canvas


CLAVES_DATOS_EMPRESA = CLAVES_IDENTIDAD_EMPRESA + CLAVES_IDENTIDAD_LEGADAS_JUNTA
CLAVES_COBRO = (
    "cobro.precio_mensual_centavos",
    "cobro.mora_activa",
    "cobro.multa_mora_automatica_activa",
    "cobro.multa_mora_automatica_centavos",
    "cobro.corte_automatico_activo",
    "cobro.meses_para_corte",
    "cobro.cobrar_mensualidad_prorrateada_activacion",
    "cobro.permitir_pago_adelantado",
    "cobro.meses_adelanto_maximo",
    "cobro.mora_leve_hasta_meses",
    "cobro.mora_media_hasta_meses",
)
CLAVES_FACTURA = (
    "factura.titulo_documento",
    "factura.subtitulo_documento",
    "factura.texto_legal_superior",
    "factura.texto_pie",
    "factura.texto_legal_inferior",
    "factura.etiqueta_copia",
    "factura.mostrar_correo",
    "factura.mostrar_telefono",
    "factura.mostrar_direccion",
    "factura.mostrar_identificador_fiscal",
    "documentos.firma_habilitada",
    "documentos.firma_texto_linea",
    "impresion_termica.nombre_impresora",
    "impresion_termica.ancho_papel_mm",
    "impresion_termica.corte_automatico",
    "impresion_termica.codigo_pagina",
    "impresion_reportes.nombre_impresora",
)
CLAVES_SISTEMA = (
    "sistema.nombre",
    "sistema.version",
    "sistema.respaldo_automatico",
    "seguridad.duracion_sesion_horas",
    "respaldo.ruta_principal",
)
CLAVES_REPORTES_PDF = (
    "reportes.ruta_salida",
    "reportes.abrir_automaticamente",
    "reportes.firma_habilitada",
    "reportes.firma_texto_linea",
)
TEXTO_FIRMA_PREDETERMINADO = "Firma autorizada"
DURACIONES_SESION_HORAS_VALIDAS = (0.5, 1.0, 2.0, 4.0, 8.0, 12.0)
MAXIMO_INTENTOS_FALLIDOS_OPERATIVO = 5
RETENCION_MAXIMA_RESPALDOS = 5
logger = obtener_logger_sigqua("configuracion.servicio")


class ServicioConfiguracion:
    """Orquesta lectura y actualizacion de configuracion operativa real."""

    DURACION_SESION_PREDETERMINADA = 8.0

    def __init__(
        self,
        repositorio_configuracion: RepositorioConfiguracion,
        gestor_rutas: GestorRutas,
        servicio_respaldo: ServicioRespaldoLocal | None = None,
        servicio_comprobantes: ServicioComprobantes | None = None,
    ) -> None:
        self._repositorio_configuracion = repositorio_configuracion
        self._gestor_rutas = gestor_rutas
        self._servicio_respaldo = servicio_respaldo
        self._servicio_comprobantes = servicio_comprobantes

    def obtener_estado(self) -> EstadoConfiguracion:
        claves = (
            CLAVES_DATOS_EMPRESA
            + CLAVES_COBRO
            + CLAVES_FACTURA
            + CLAVES_SISTEMA
            + CLAVES_REPORTES_PDF
        )
        parametros = self._repositorio_configuracion.listar_por_claves(claves)
        correlativo_actual, ultimo_comprobante, total_comprobantes = (
            self._repositorio_configuracion.obtener_resumen_comprobantes()
        )
        detalle_respaldo = self._obtener_resumen_respaldos_archivo()
        identidad = construir_identidad_empresa(parametros, nombre_predeterminado="SIGQUA")
        ultimo_parametro_actualizado = max(
            (
                parametro
                for parametro in parametros.values()
                if hasattr(parametro, "actualizado_en") and parametro.actualizado_en
            ),
            key=lambda parametro: parametro.actualizado_en,
            default=None,
        )

        parametros_cobro = ParametrosCobro(
            precio_mensual_centavos=self._a_entero(self._valor_parametro(parametros, "cobro.precio_mensual_centavos", "0")),
            mora_visible=self._a_booleano(self._valor_parametro(parametros, "cobro.mora_activa", "1")),
            multa_mora_automatica_activa=self._a_booleano(
                self._valor_parametro(parametros, "cobro.multa_mora_automatica_activa", "0")
            ),
            multa_mora_automatica_centavos=self._a_entero(
                self._valor_parametro(parametros, "cobro.multa_mora_automatica_centavos", "0")
            ),
            corte_automatico_activo=self._a_booleano(
                self._valor_parametro(parametros, "cobro.corte_automatico_activo", "0")
            ),
            meses_para_corte=self._a_entero(self._valor_parametro(parametros, "cobro.meses_para_corte", "0")),
            cobrar_mensualidad_prorrateada_activacion=self._a_booleano(
                self._valor_parametro(
                    parametros,
                    "cobro.cobrar_mensualidad_prorrateada_activacion",
                    "0",
                )
            ),
            permitir_pago_adelantado=self._a_booleano(
                self._valor_parametro(parametros, "cobro.permitir_pago_adelantado", "0")
            ),
            meses_adelanto_maximo=self._a_entero(
                self._valor_parametro(parametros, "cobro.meses_adelanto_maximo", "0")
            ),
            mora_leve_hasta_meses=self._a_entero(
                self._valor_parametro(parametros, "cobro.mora_leve_hasta_meses", "2")
            ),
            mora_media_hasta_meses=self._a_entero(
                self._valor_parametro(parametros, "cobro.mora_media_hasta_meses", "5")
            ),
        )
        firma_texto_linea = self._resolver_texto_firma_linea(parametros)
        factura = FacturaConfiguracion(
            titulo_documento=self._valor_parametro(parametros, "factura.titulo_documento", "RECIBO DE PAGO"),
            subtitulo_documento=self._valor_parametro(parametros, "factura.subtitulo_documento", ""),
            texto_legal_superior=self._valor_parametro(parametros, "factura.texto_legal_superior", ""),
            texto_pie=self._valor_parametro(parametros, "factura.texto_pie", ""),
            texto_legal_inferior=self._valor_parametro(parametros, "factura.texto_legal_inferior", ""),
            etiqueta_copia=self._valor_parametro(parametros, "factura.etiqueta_copia", "ORIGINAL"),
            mostrar_correo=self._a_booleano(self._valor_parametro(parametros, "factura.mostrar_correo", "1")),
            mostrar_telefono=self._a_booleano(
                self._valor_parametro(parametros, "factura.mostrar_telefono", "1")
            ),
            mostrar_direccion=self._a_booleano(
                self._valor_parametro(parametros, "factura.mostrar_direccion", "1")
            ),
            mostrar_identificador_fiscal=self._a_booleano(
                self._valor_parametro(parametros, "factura.mostrar_identificador_fiscal", "0")
            ),
            firma_habilitada=self._a_booleano(
                self._valor_parametro(parametros, "documentos.firma_habilitada", "0")
            ),
            firma_texto_linea=firma_texto_linea,
            impresora_termica_nombre=self._valor_parametro(
                parametros, "impresion_termica.nombre_impresora", ""
            ),
            impresora_termica_ancho_mm=self._a_entero(
                self._valor_parametro(parametros, "impresion_termica.ancho_papel_mm", "80")
            ),
            impresora_termica_corte_automatico=self._a_booleano(
                self._valor_parametro(parametros, "impresion_termica.corte_automatico", "1")
            ),
            impresora_termica_codigo_pagina="cp850",
            impresora_reportes_nombre=self._valor_parametro(
                parametros, "impresion_reportes.nombre_impresora", ""
            ),
            comprobantes_pendientes_impresion=self._contar_pendientes_impresion(),
            correlativo_actual=self._formatear_correlativo(correlativo_actual),
            proximo_correlativo=self._formatear_correlativo(correlativo_actual + 1),
            ultimo_comprobante_emitido=ultimo_comprobante if ultimo_comprobante else "Sin comprobantes emitidos",
            total_comprobantes_emitidos=total_comprobantes,
        )
        duracion_sesion_horas = self._resolver_duracion_sesion_horas(parametros)
        ruta_reportes_predeterminada = self._gestor_rutas.obtener_ruta_reportes_predeterminada()
        ruta_reportes_configurada = self._valor_parametro(
            parametros,
            "reportes.ruta_salida",
            "",
        ).strip()
        ruta_reportes_efectiva = (
            Path(ruta_reportes_configurada).expanduser()
            if ruta_reportes_configurada
            else ruta_reportes_predeterminada
        )
        reportes_pdf = ReportesPdfConfiguracion(
            ruta_salida=str(ruta_reportes_efectiva),
            ruta_predeterminada=str(ruta_reportes_predeterminada),
            abrir_automaticamente=self._a_booleano(
                self._valor_parametro(parametros, "reportes.abrir_automaticamente", "1")
            ),
            firma_habilitada=self._a_booleano(
                self._valor_parametro(parametros, "reportes.firma_habilitada", "0")
            ),
            firma_texto_linea=(
                self._valor_parametro(
                    parametros,
                    "reportes.firma_texto_linea",
                    TEXTO_FIRMA_PREDETERMINADO,
                ).strip()
                or TEXTO_FIRMA_PREDETERMINADO
            ),
        )
        configuracion_respaldo = self._construir_configuracion_respaldo(parametros)
        operacion = OperacionConfiguracion(
            respaldo_automatico=True,
            ultimo_respaldo_en=str(detalle_respaldo.get("generado_en", "")),
            ultimo_respaldo_estado=(
                "DISPONIBLE" if detalle_respaldo else "SIN_REGISTRO"
            ),
            total_respaldos=int(detalle_respaldo.get("total", 0) or 0),
            ultimo_respaldo_archivo=str(detalle_respaldo.get("nombre_archivo", "")),
            ultimo_respaldo_tamano_bytes=int(detalle_respaldo.get("tamano_bytes", 0) or 0),
            ultimo_respaldo_generado_por="Sistema local" if detalle_respaldo else "Sin registro",
            ruta_respaldos_principal=configuracion_respaldo.ruta_principal,
            retencion_maxima=configuracion_respaldo.retencion_maxima,
        )
        informacion = InformacionConfiguracion(
            nombre_sistema=self._valor_parametro(parametros, "sistema.nombre", "SIGQUA"),
            version_sistema=self._valor_parametro(parametros, "sistema.version", ""),
            ruta_base_datos=str(self._gestor_rutas.obtener_ruta_base_datos()),
            modo_operacion="Acceso local",
            ultima_actualizacion=ultimo_parametro_actualizado.actualizado_en if ultimo_parametro_actualizado else "",
            actualizado_por=self._resolver_autoria(
                ultimo_parametro_actualizado.actualizado_por_nombre if ultimo_parametro_actualizado else "",
                bool(ultimo_parametro_actualizado),
            ),
        )
        seguridad = SeguridadConfiguracion(
            autenticacion_local=True,
            maximo_intentos_fallidos=MAXIMO_INTENTOS_FALLIDOS_OPERATIVO,
            duracion_sesion_horas=self._duracion_para_visualizacion(duracion_sesion_horas),
            restablecimiento_administrativo=True,
            cambio_contrasena_obligatorio=True,
        )
        return EstadoConfiguracion(
            identidad_empresa=IdentidadEmpresa(
                nombre=identidad.nombre,
                telefono=identidad.telefono,
                correo=identidad.correo,
                direccion=identidad.direccion,
                identificador_fiscal=identidad.identificador_fiscal,
                sitio_web=identidad.sitio_web,
                mensaje_contacto=identidad.mensaje_contacto,
            ),
            parametros_cobro=parametros_cobro,
            factura=factura,
            reportes_pdf=reportes_pdf,
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
        identificador_fiscal: str,
        sitio_web: str,
        mensaje_contacto: str,
        actor_id: int | None = None,
    ) -> ResultadoGestionConfiguracion:
        nombre = nombre.strip()
        telefono = telefono.strip()
        correo = correo.strip()
        direccion = direccion.strip()
        identificador_fiscal = identificador_fiscal.strip()
        sitio_web = sitio_web.strip()
        mensaje_contacto = mensaje_contacto.strip()

        if not nombre:
            return ResultadoGestionConfiguracion(False, "Indica el nombre legal o comercial de la empresa.", "VALIDACION")
        if not direccion:
            return ResultadoGestionConfiguracion(False, "Indica la direccion fiscal u operativa de la empresa.", "VALIDACION")
        try:
            self._repositorio_configuracion.actualizar_valores(
                {
                    "empresa.nombre": nombre,
                    "empresa.telefono": telefono,
                    "empresa.correo": correo,
                    "empresa.direccion": direccion,
                    "empresa.identificador_fiscal": identificador_fiscal,
                    "empresa.sitio_web": sitio_web,
                    "empresa.mensaje_contacto": mensaje_contacto,
                },
                actor_id=actor_id,
            )
        except Exception:
            return ResultadoGestionConfiguracion(False, "No fue posible guardar la identidad de la empresa.", "ERROR_SQLITE")
        return ResultadoGestionConfiguracion(True, "Identidad de la empresa actualizada.", "OK")

    def guardar_parametros_factura(
        self,
        titulo_documento: str,
        texto_pie: str,
        etiqueta_copia: str,
        mostrar_correo: bool,
        mostrar_telefono: bool,
        mostrar_direccion: bool,
        mostrar_identificador_fiscal: bool,
        firma_habilitada: bool,
        firma_texto_linea: str,
        impresora_termica_nombre: str = "",
        impresora_termica_ancho_mm: int = 80,
        impresora_termica_corte_automatico: bool = True,
        impresora_reportes_nombre: str = "",
        actor_id: int | None = None,
    ) -> ResultadoGestionConfiguracion:
        titulo_documento = titulo_documento.strip()
        texto_pie = texto_pie.strip()
        etiqueta_copia = etiqueta_copia.strip()
        firma_texto_linea = firma_texto_linea.strip() or TEXTO_FIRMA_PREDETERMINADO
        impresora_termica_nombre = impresora_termica_nombre.strip()
        impresora_reportes_nombre = impresora_reportes_nombre.strip()

        if not titulo_documento:
            return ResultadoGestionConfiguracion(False, "Indica el titulo principal del recibo.", "VALIDACION")
        if not texto_pie:
            return ResultadoGestionConfiguracion(False, "Indica el texto inferior del comprobante.", "VALIDACION")
        if not etiqueta_copia:
            return ResultadoGestionConfiguracion(False, "Indica la etiqueta visible del recibo.", "VALIDACION")
        if impresora_termica_ancho_mm not in {58, 80}:
            return ResultadoGestionConfiguracion(False, "El ancho termico debe ser 58 mm u 80 mm.", "VALIDACION")
        try:
            self._repositorio_configuracion.actualizar_valores(
                {
                    "factura.titulo_documento": titulo_documento,
                    "factura.texto_pie": texto_pie,
                    "factura.etiqueta_copia": etiqueta_copia,
                    "factura.mostrar_correo": "1" if mostrar_correo else "0",
                    "factura.mostrar_telefono": "1" if mostrar_telefono else "0",
                    "factura.mostrar_direccion": "1" if mostrar_direccion else "0",
                    "factura.mostrar_identificador_fiscal": "1" if mostrar_identificador_fiscal else "0",
                    "documentos.firma_habilitada": "1" if firma_habilitada else "0",
                    "documentos.firma_texto_linea": firma_texto_linea,
                    "impresion_termica.nombre_impresora": impresora_termica_nombre,
                    "impresion_termica.ancho_papel_mm": str(impresora_termica_ancho_mm),
                    "impresion_termica.corte_automatico": "1" if impresora_termica_corte_automatico else "0",
                    "impresion_termica.codigo_pagina": "cp850",
                    "impresion_reportes.nombre_impresora": impresora_reportes_nombre,
                },
                actor_id=actor_id,
            )
        except Exception:
            return ResultadoGestionConfiguracion(False, "No fue posible actualizar la configuracion de comprobantes.", "ERROR_SQLITE")
        return ResultadoGestionConfiguracion(True, "Documentos y comprobantes actualizados.", "OK")

    def guardar_reportes_pdf(
        self,
        ruta_salida: str,
        abrir_automaticamente: bool,
        firma_habilitada: bool,
        firma_texto_linea: str,
        actor_id: int | None = None,
    ) -> ResultadoGestionConfiguracion:
        ruta_salida = ruta_salida.strip()
        ruta_predeterminada = self._gestor_rutas.obtener_ruta_reportes_predeterminada()
        ruta_efectiva = Path(ruta_salida).expanduser() if ruta_salida else ruta_predeterminada
        try:
            ruta_efectiva.mkdir(parents=True, exist_ok=True)
        except OSError:
            return ResultadoGestionConfiguracion(
                False,
                "No fue posible crear o acceder a la carpeta de reportes.",
                "RUTA_INVALIDA",
            )
        texto_firma = firma_texto_linea.strip() or TEXTO_FIRMA_PREDETERMINADO
        valor_ruta = "" if ruta_efectiva == ruta_predeterminada else str(ruta_efectiva)
        try:
            self._repositorio_configuracion.actualizar_valores(
                {
                    "reportes.ruta_salida": valor_ruta,
                    "reportes.abrir_automaticamente": "1" if abrir_automaticamente else "0",
                    "reportes.firma_habilitada": "1" if firma_habilitada else "0",
                    "reportes.firma_texto_linea": texto_firma,
                },
                actor_id=actor_id,
            )
        except Exception:
            return ResultadoGestionConfiguracion(
                False,
                "No fue posible guardar la configuracion de reportes PDF.",
                "ERROR_SQLITE",
            )
        return ResultadoGestionConfiguracion(True, "Configuracion de reportes PDF actualizada.", "OK")

    def guardar_parametros_cobro(
        self,
        precio_mensual_centavos: int,
        multa_mora_automatica_activa: bool,
        multa_mora_automatica_centavos: int,
        corte_automatico_activo: bool,
        meses_para_corte: int,
        cobrar_mensualidad_prorrateada_activacion: bool,
        permitir_pago_adelantado: bool,
        meses_adelanto_maximo: int,
        mora_leve_hasta_meses: int,
        mora_media_hasta_meses: int,
        actor_id: int | None = None,
    ) -> ResultadoGestionConfiguracion:
        if precio_mensual_centavos <= 0:
            return ResultadoGestionConfiguracion(False, "El precio mensual debe ser mayor que cero.", "VALIDACION")
        if multa_mora_automatica_centavos < 0:
            return ResultadoGestionConfiguracion(False, "La multa automatica por mora no puede ser negativa.", "VALIDACION")
        if meses_para_corte < 1:
            return ResultadoGestionConfiguracion(False, "Define al menos un mes para el umbral de corte o alerta.", "VALIDACION")
        if permitir_pago_adelantado and meses_adelanto_maximo < 1:
            return ResultadoGestionConfiguracion(False, "Indica el maximo de meses adelantados permitidos.", "VALIDACION")
        if permitir_pago_adelantado and meses_adelanto_maximo > 12:
            return ResultadoGestionConfiguracion(False, "El maximo recomendado de adelantos es de 12 meses.", "VALIDACION")
        if mora_leve_hasta_meses < 1:
            return ResultadoGestionConfiguracion(False, "La prioridad baja debe cubrir al menos 1 mes vencido.", "VALIDACION")
        if mora_media_hasta_meses <= mora_leve_hasta_meses:
            return ResultadoGestionConfiguracion(False, "La prioridad media debe terminar despues de la prioridad baja.", "VALIDACION")
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
                    "cobro.cobrar_mensualidad_prorrateada_activacion": (
                        "1" if cobrar_mensualidad_prorrateada_activacion else "0"
                    ),
                    "cobro.permitir_pago_adelantado": "1" if permitir_pago_adelantado else "0",
                    "cobro.meses_adelanto_maximo": str(meses_adelanto_maximo),
                    "cobro.mora_leve_hasta_meses": str(mora_leve_hasta_meses),
                    "cobro.mora_media_hasta_meses": str(mora_media_hasta_meses),
                },
                actor_id=actor_id,
            )
        except Exception:
            return ResultadoGestionConfiguracion(False, "No fue posible actualizar los parametros de cobro.", "ERROR_SQLITE")
        return ResultadoGestionConfiguracion(True, "Parametros de cobro actualizados.", "OK")

    def guardar_duracion_sesion(
        self,
        duracion_sesion_horas: float,
        actor_id: int | None = None,
    ) -> ResultadoGestionConfiguracion:
        if duracion_sesion_horas not in DURACIONES_SESION_HORAS_VALIDAS:
            return ResultadoGestionConfiguracion(False, "Selecciona un tiempo de sesion valido.", "VALIDACION")

        try:
            self._repositorio_configuracion.actualizar_valores(
                {"seguridad.duracion_sesion_horas": self._duracion_a_texto(duracion_sesion_horas)},
                actor_id=actor_id,
            )
        except Exception:
            return ResultadoGestionConfiguracion(False, "No fue posible actualizar la duracion de sesion.", "ERROR_SQLITE")
        return ResultadoGestionConfiguracion(True, "Duracion de sesion actualizada.", "OK")

    def crear_respaldo_automatico(self, actor_id: int | None = None) -> ResultadoGestionConfiguracion:
        return self._crear_respaldo("AUTOMATICO", actor_id=actor_id)

    def restaurar_respaldo_externo(
        self,
        ruta_archivo: str,
        actor_id: int | None = None,
    ) -> ResultadoGestionConfiguracion:
        if self._servicio_respaldo is None:
            return ResultadoGestionConfiguracion(False, "El servicio de respaldo no esta disponible.", "ERROR_CONFIG")
        ruta_respaldo = Path(ruta_archivo).expanduser()
        if not ruta_respaldo.exists() or not ruta_respaldo.is_file():
            return ResultadoGestionConfiguracion(False, "El archivo de respaldo seleccionado no existe.", "VALIDACION")
        if ruta_respaldo.suffix.lower() != ".zip":
            return ResultadoGestionConfiguracion(False, "Selecciona un respaldo SIGQUA con extension .zip.", "VALIDACION")
        return self._restaurar_ruta_respaldo(
            ruta_respaldo=ruta_respaldo,
            actor_id=actor_id,
        )

    def probar_impresora_comprobantes(self, nombre_impresora: str) -> ResultadoGestionConfiguracion:
        nombre_impresora = nombre_impresora.strip()
        if not nombre_impresora:
            return ResultadoGestionConfiguracion(False, "Configura primero la impresora de comprobantes.", "VALIDACION")
        datos = (
            b"\x1b@"
            + "SIGQUA\nPrueba de impresora de comprobantes\nESC/POS Windows RAW\n\n".encode("cp850", errors="replace")
            + b"\x1dV\x00"
        )
        resultado = TransporteWindowsRawEscpos().enviar(nombre_impresora, datos, "SIGQUA prueba comprobantes")
        return ResultadoGestionConfiguracion(resultado.exito, resultado.mensaje, resultado.codigo)

    def probar_impresora_reportes(self, nombre_impresora: str) -> ResultadoGestionConfiguracion:
        nombre_impresora = nombre_impresora.strip()
        if not nombre_impresora:
            return ResultadoGestionConfiguracion(False, "Configura primero la impresora de reportes.", "VALIDACION")
        if sys.platform != "win32" or not hasattr(os, "startfile"):
            return ResultadoGestionConfiguracion(False, "La prueba de impresion de reportes solo esta disponible en Windows.", "ERROR_CONFIG")
        ruta_temporal = Path(tempfile.gettempdir()) / "sigqua_prueba_impresora_reportes.pdf"
        documento = canvas.Canvas(str(ruta_temporal))
        documento.drawString(72, 740, "SIGQUA")
        documento.drawString(72, 720, "Prueba de impresora de reportes PDF")
        documento.drawString(72, 700, f"Impresora: {nombre_impresora}")
        documento.save()
        try:
            os.startfile(str(ruta_temporal), "printto", f'"{nombre_impresora}"')  # type: ignore[attr-defined]
        except OSError as error:
            return ResultadoGestionConfiguracion(False, f"No fue posible enviar la prueba PDF. {error}", "ERROR_IMPRESION")
        return ResultadoGestionConfiguracion(True, "Prueba enviada a la impresora de reportes.", "OK")

    def _crear_respaldo(
        self,
        tipo_respaldo: str,
        actor_id: int | None = None,
    ) -> ResultadoGestionConfiguracion:
        if self._servicio_respaldo is None:
            return ResultadoGestionConfiguracion(False, "El servicio de respaldo no esta disponible.", "ERROR_CONFIG")
        estado = self.obtener_estado()
        try:
            configuracion = self._construir_configuracion_respaldo({})
            configuracion.version_sistema = estado.informacion.version_sistema or "Sin version"
            detalle = self._servicio_respaldo.crear_respaldo(
                configuracion=configuracion,
                generado_por=actor_id,
                tipo_respaldo=tipo_respaldo,
            )
        except Exception as error:
            logger.exception("No fue posible generar el respaldo automatico.")
            return ResultadoGestionConfiguracion(False, f"No fue posible generar el respaldo: {error}", "ERROR_RESPALDO")
        return ResultadoGestionConfiguracion(True, f"Respaldo generado: {detalle.nombre_archivo}", "OK")

    def _restaurar_ruta_respaldo(
        self,
        *,
        ruta_respaldo: Path,
        actor_id: int | None,
    ) -> ResultadoGestionConfiguracion:
        if self._servicio_respaldo is None:
            return ResultadoGestionConfiguracion(
                False,
                "El servicio de respaldo no esta disponible.",
                "ERROR_CONFIG",
            )
        estado = self.obtener_estado()
        configuracion = self._construir_configuracion_respaldo({})
        configuracion.version_sistema = estado.informacion.version_sistema or "Sin version"
        try:
            resultado = self._servicio_respaldo.restaurar_respaldo(
                ruta_respaldo=str(ruta_respaldo),
                configuracion=configuracion,
                generado_por=actor_id,
            )
        except Exception as error:
            logger.exception("Fallo la restauracion del respaldo %s.", ruta_respaldo.name)
            return ResultadoGestionConfiguracion(
                False,
                f"No fue posible restaurar el respaldo: {error}",
                "ERROR_RESTAURACION",
            )
        return ResultadoGestionConfiguracion(
            True,
            "Respaldo restaurado correctamente. SIGQUA se reiniciara para aplicar los cambios.",
            "OK",
        )

    def _obtener_resumen_respaldos_archivo(self) -> dict[str, object]:
        ruta_respaldos = self._gestor_rutas.obtener_ruta_respaldos()
        ruta_respaldos.mkdir(parents=True, exist_ok=True)
        archivos = sorted(
            (
                ruta
                for ruta in ruta_respaldos.glob("SIGQUA_RESPALDO_*.zip")
                if ruta.is_file()
            ),
            key=lambda ruta: ruta.stat().st_mtime,
            reverse=True,
        )
        if not archivos:
            return {}
        ultimo = archivos[0]
        fecha = datetime.fromtimestamp(ultimo.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        return {
            "nombre_archivo": ultimo.name,
            "tamano_bytes": ultimo.stat().st_size,
            "generado_en": fecha,
            "total": len(archivos),
        }

    def opciones_duracion_sesion(self) -> tuple[tuple[str, float], ...]:
        return (
            ("30 minutos", 0.5),
            ("1 hora", 1.0),
            ("2 horas", 2.0),
            ("4 horas", 4.0),
            ("8 horas", 8.0),
            ("12 horas", 12.0),
        )

    @staticmethod
    def formatear_moneda(valor_centavos: int) -> str:
        return f"L {valor_centavos / 100:,.2f}"

    @staticmethod
    def formatear_tamano_bytes(valor: int) -> str:
        if valor <= 0:
            return "0 B"
        unidades = ("B", "KB", "MB", "GB")
        tamano = float(valor)
        indice = 0
        while tamano >= 1024 and indice < len(unidades) - 1:
            tamano /= 1024.0
            indice += 1
        return f"{tamano:,.1f} {unidades[indice]}"

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
    def _a_decimal(valor: str, predeterminado: float = 0.0) -> float:
        try:
            return float(str(valor).strip() or str(predeterminado))
        except ValueError:
            return predeterminado

    @staticmethod
    def _duracion_a_texto(valor: float) -> str:
        if float(valor).is_integer():
            return str(int(valor))
        return str(valor)

    @staticmethod
    def _duracion_para_visualizacion(valor: float) -> float:
        return float(valor)

    @staticmethod
    def _resolver_autoria(nombre_usuario: str, existe_evento: bool) -> str:
        nombre_limpio = (nombre_usuario or "").strip()
        if nombre_limpio:
            return nombre_limpio
        return "Sistema" if existe_evento else "Sin registro"

    @staticmethod
    def _formatear_correlativo(numero: int) -> str:
        return f"REC-{max(numero, 0):05d}"

    @staticmethod
    def _valor_parametro(parametros: dict[str, object], clave: str, predeterminado: str = "") -> str:
        parametro = parametros.get(clave)
        if parametro is None:
            return predeterminado
        if hasattr(parametro, "valor"):
            return str(getattr(parametro, "valor") or predeterminado)
        return str(parametro or predeterminado)

    def _resolver_duracion_sesion_horas(self, parametros: dict[str, object]) -> float:
        valor = self._a_decimal(
            self._valor_parametro(
                parametros,
                "seguridad.duracion_sesion_horas",
                str(self.DURACION_SESION_PREDETERMINADA),
            ),
            self.DURACION_SESION_PREDETERMINADA,
        )
        if valor not in DURACIONES_SESION_HORAS_VALIDAS:
            return self.DURACION_SESION_PREDETERMINADA
        return valor

    def _construir_configuracion_respaldo(
        self,
        parametros: dict[str, object],
    ) -> ConfiguracionRespaldoLocal:
        return ConfiguracionRespaldoLocal(
            ruta_principal=str(self._gestor_rutas.obtener_ruta_respaldos()),
            retencion_maxima=RETENCION_MAXIMA_RESPALDOS,
            version_sistema=self._valor_parametro(parametros, "sistema.version", ""),
        )

    def _resolver_texto_firma_linea(self, parametros: dict[str, object]) -> str:
        return (
            self._valor_parametro(parametros, "documentos.firma_texto_linea", "").strip()
            or TEXTO_FIRMA_PREDETERMINADO
        )

    def _contar_pendientes_impresion(self) -> int:
        if self._servicio_comprobantes is None:
            return 0
        try:
            return self._servicio_comprobantes.contar_pendientes_impresion()
        except Exception:
            return 0

    def _normalizar_ruta_configurada(self, ruta: str) -> str:
        ruta_limpia = ruta.strip()
        if not ruta_limpia:
            return ""
        ruta_path = Path(ruta_limpia).expanduser()
        if not ruta_path.is_absolute():
            ruta_path = self._gestor_rutas.raiz_proyecto / ruta_path
        return str(ruta_path)
