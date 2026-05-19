"""Servicios del modulo de configuracion."""

from __future__ import annotations

from pathlib import Path

from comun.configuracion.gestor_rutas import GestorRutas
from comun.configuracion.identidad_empresa import (
    CLAVES_IDENTIDAD_EMPRESA,
    CLAVES_IDENTIDAD_LEGADAS_JUNTA,
    construir_identidad_empresa,
)
from comun.respaldo import (
    ConfiguracionProgramacionRespaldo,
    ConfiguracionRespaldoLocal,
    ServicioRespaldoLocal,
)
from modulos.configuracion.entidades import (
    EstadoConfiguracion,
    FacturaConfiguracion,
    IdentidadEmpresa,
    InformacionConfiguracion,
    OperacionConfiguracion,
    ParametrosCobro,
    ResultadoGestionConfiguracion,
    SeguridadConfiguracion,
)
from modulos.configuracion.repositorio import RepositorioConfiguracion


CLAVES_DATOS_EMPRESA = CLAVES_IDENTIDAD_EMPRESA + CLAVES_IDENTIDAD_LEGADAS_JUNTA
CLAVES_COBRO = (
    "cobro.precio_mensual_centavos",
    "cobro.mora_activa",
    "cobro.multa_mora_automatica_activa",
    "cobro.multa_mora_automatica_centavos",
    "cobro.corte_automatico_activo",
    "cobro.meses_para_corte",
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
    "factura.formato_salida",
    "documentos.firma_habilitada",
    "documentos.firma_nombre",
    "documentos.firma_cargo",
    "documentos.firma_identificador",
    "documentos.firma_texto_apoyo",
)
CLAVES_SISTEMA = (
    "sistema.nombre",
    "sistema.version",
    "sistema.respaldo_automatico",
    "seguridad.duracion_sesion_horas",
    "respaldo.ruta_principal",
    "respaldo.ruta_secundaria",
    "respaldo.secundaria_activa",
    "respaldo.comprimir_zip",
    "respaldo.organizar_por_periodo",
    "respaldo.retencion_dias",
    "respaldo.programacion_tipo",
    "respaldo.programacion_hora",
    "respaldo.programacion_dia_semana",
    "mantenimiento.ruta_respaldos",
    "mantenimiento.dias_retencion_respaldos",
)
FORMATOS_SALIDA_FACTURA_VALIDOS = ("PDF", "HTML", "TEXTO")
TIPOS_PROGRAMACION_RESPALDO_VALIDOS = ("DESACTIVADO", "DIARIO", "SEMANAL")
DIAS_SEMANA_VALIDOS = ("LUNES", "MARTES", "MIERCOLES", "JUEVES", "VIERNES", "SABADO", "DOMINGO")
DURACIONES_SESION_HORAS_VALIDAS = (0.5, 1.0, 2.0, 4.0, 8.0, 12.0)
MAXIMO_INTENTOS_FALLIDOS_OPERATIVO = 5


class ServicioConfiguracion:
    """Orquesta lectura y actualizacion de configuracion operativa real."""

    DURACION_SESION_PREDETERMINADA = 8.0

    def __init__(
        self,
        repositorio_configuracion: RepositorioConfiguracion,
        gestor_rutas: GestorRutas,
        servicio_respaldo: ServicioRespaldoLocal | None = None,
    ) -> None:
        self._repositorio_configuracion = repositorio_configuracion
        self._gestor_rutas = gestor_rutas
        self._servicio_respaldo = servicio_respaldo

    def obtener_estado(self) -> EstadoConfiguracion:
        claves = CLAVES_DATOS_EMPRESA + CLAVES_COBRO + CLAVES_FACTURA + CLAVES_SISTEMA
        parametros = self._repositorio_configuracion.listar_por_claves(claves)
        correlativo_actual, ultimo_comprobante, total_comprobantes = (
            self._repositorio_configuracion.obtener_resumen_comprobantes()
        )
        ultimo_respaldo_en, ultimo_respaldo_estado, total_respaldos = (
            self._repositorio_configuracion.obtener_resumen_respaldos()
        )
        detalle_respaldo = self._repositorio_configuracion.obtener_detalle_ultimo_respaldo()
        identidad = construir_identidad_empresa(parametros, nombre_predeterminado="SICAP")

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
            formato_salida=self._valor_parametro(parametros, "factura.formato_salida", "HTML").upper(),
            firma_habilitada=self._a_booleano(
                self._valor_parametro(parametros, "documentos.firma_habilitada", "0")
            ),
            firma_nombre=self._valor_parametro(parametros, "documentos.firma_nombre", ""),
            firma_cargo=self._valor_parametro(parametros, "documentos.firma_cargo", ""),
            firma_identificador=self._valor_parametro(parametros, "documentos.firma_identificador", ""),
            firma_texto_apoyo=self._valor_parametro(parametros, "documentos.firma_texto_apoyo", ""),
            correlativo_actual=self._formatear_correlativo(correlativo_actual),
            proximo_correlativo=self._formatear_correlativo(correlativo_actual + 1),
            ultimo_comprobante_emitido=ultimo_comprobante if ultimo_comprobante else "Sin comprobantes emitidos",
            total_comprobantes_emitidos=total_comprobantes,
        )
        duracion_sesion_horas = self._resolver_duracion_sesion_horas(parametros)
        configuracion_respaldo = self._construir_configuracion_respaldo(parametros)
        proxima_ejecucion = ""
        if self._servicio_respaldo is not None:
            try:
                proxima_ejecucion = self._servicio_respaldo.obtener_proxima_ejecucion_programada()
            except Exception:
                proxima_ejecucion = ""
        operacion = OperacionConfiguracion(
            respaldo_automatico=self._a_booleano(
                self._valor_parametro(parametros, "sistema.respaldo_automatico", "0")
            ),
            ultimo_respaldo_en=ultimo_respaldo_en,
            ultimo_respaldo_estado=ultimo_respaldo_estado or "SIN_REGISTRO",
            total_respaldos=total_respaldos,
            ultimo_respaldo_archivo=str(detalle_respaldo.get("nombre_archivo", "")),
            ultimo_respaldo_tamano_bytes=int(detalle_respaldo.get("tamano_bytes", 0) or 0),
            ultimo_respaldo_hash=str(detalle_respaldo.get("hash_archivo", "")),
            ruta_respaldos_principal=configuracion_respaldo.ruta_principal,
            ruta_respaldos_secundaria=configuracion_respaldo.ruta_secundaria,
            respaldo_secundario_activo=configuracion_respaldo.secundaria_activa,
            comprimir_zip=configuracion_respaldo.comprimir_zip,
            organizar_por_periodo=configuracion_respaldo.organizar_por_periodo,
            retencion_dias=configuracion_respaldo.retencion_dias,
            programacion_tipo=configuracion_respaldo.programacion.tipo,
            programacion_hora=configuracion_respaldo.programacion.hora,
            programacion_dia_semana=configuracion_respaldo.programacion.dia_semana,
            proxima_ejecucion_programada=proxima_ejecucion,
            ruta_exportaciones_comprobantes=str(self._gestor_rutas.obtener_ruta_exportaciones_comprobantes()),
            ruta_exportaciones_reportes=str(self._gestor_rutas.obtener_ruta_exportaciones_reportes()),
        )
        informacion = InformacionConfiguracion(
            nombre_sistema=self._valor_parametro(parametros, "sistema.nombre", "SICAP"),
            version_sistema=self._valor_parametro(parametros, "sistema.version", ""),
            ruta_base_datos=str(self._gestor_rutas.obtener_ruta_base_datos()),
            modo_operacion="Autenticacion local sin correo y con soporte administrativo",
            ultima_actualizacion=max(
                (
                    parametro.actualizado_en
                    for parametro in parametros.values()
                    if hasattr(parametro, "actualizado_en") and parametro.actualizado_en
                ),
                default="",
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
        subtitulo_documento: str,
        texto_legal_superior: str,
        texto_pie: str,
        texto_legal_inferior: str,
        etiqueta_copia: str,
        formato_salida: str,
        mostrar_correo: bool,
        mostrar_telefono: bool,
        mostrar_direccion: bool,
        mostrar_identificador_fiscal: bool,
        firma_habilitada: bool,
        firma_nombre: str,
        firma_cargo: str,
        firma_identificador: str,
        firma_texto_apoyo: str,
        actor_id: int | None = None,
    ) -> ResultadoGestionConfiguracion:
        titulo_documento = titulo_documento.strip()
        subtitulo_documento = subtitulo_documento.strip()
        texto_legal_superior = texto_legal_superior.strip()
        texto_pie = texto_pie.strip()
        texto_legal_inferior = texto_legal_inferior.strip()
        etiqueta_copia = etiqueta_copia.strip()
        formato_salida = formato_salida.strip().upper()
        firma_nombre = firma_nombre.strip()
        firma_cargo = firma_cargo.strip()
        firma_identificador = firma_identificador.strip()
        firma_texto_apoyo = firma_texto_apoyo.strip()

        if not titulo_documento:
            return ResultadoGestionConfiguracion(False, "Indica el titulo principal del recibo.", "VALIDACION")
        if not texto_pie:
            return ResultadoGestionConfiguracion(False, "Indica el texto inferior del comprobante.", "VALIDACION")
        if not etiqueta_copia:
            return ResultadoGestionConfiguracion(False, "Indica la etiqueta visible del recibo.", "VALIDACION")
        if formato_salida not in FORMATOS_SALIDA_FACTURA_VALIDOS:
            return ResultadoGestionConfiguracion(False, "Selecciona un formato de salida valido.", "VALIDACION")
        if firma_habilitada and not firma_nombre:
            return ResultadoGestionConfiguracion(False, "Indica el nombre visible de la firma compartida.", "VALIDACION")
        try:
            self._repositorio_configuracion.actualizar_valores(
                {
                    "factura.titulo_documento": titulo_documento,
                    "factura.subtitulo_documento": subtitulo_documento,
                    "factura.texto_legal_superior": texto_legal_superior,
                    "factura.texto_pie": texto_pie,
                    "factura.texto_legal_inferior": texto_legal_inferior,
                    "factura.etiqueta_copia": etiqueta_copia,
                    "factura.formato_salida": formato_salida,
                    "factura.mostrar_correo": "1" if mostrar_correo else "0",
                    "factura.mostrar_telefono": "1" if mostrar_telefono else "0",
                    "factura.mostrar_direccion": "1" if mostrar_direccion else "0",
                    "factura.mostrar_identificador_fiscal": "1" if mostrar_identificador_fiscal else "0",
                    "documentos.firma_habilitada": "1" if firma_habilitada else "0",
                    "documentos.firma_nombre": firma_nombre,
                    "documentos.firma_cargo": firma_cargo,
                    "documentos.firma_identificador": firma_identificador,
                    "documentos.firma_texto_apoyo": firma_texto_apoyo,
                },
                actor_id=actor_id,
            )
        except Exception:
            return ResultadoGestionConfiguracion(False, "No fue posible actualizar la configuracion de comprobantes.", "ERROR_SQLITE")
        return ResultadoGestionConfiguracion(True, "Documentos y comprobantes actualizados.", "OK")

    def guardar_parametros_cobro(
        self,
        precio_mensual_centavos: int,
        multa_mora_automatica_activa: bool,
        multa_mora_automatica_centavos: int,
        corte_automatico_activo: bool,
        meses_para_corte: int,
        permitir_pago_adelantado: bool,
        meses_adelanto_maximo: int,
        mora_leve_hasta_meses: int,
        mora_media_hasta_meses: int,
        actor_id: int | None = None,
    ) -> ResultadoGestionConfiguracion:
        if precio_mensual_centavos < 0:
            return ResultadoGestionConfiguracion(False, "El precio mensual no puede ser negativo.", "VALIDACION")
        if multa_mora_automatica_centavos < 0:
            return ResultadoGestionConfiguracion(False, "La multa automatica por mora no puede ser negativa.", "VALIDACION")
        if meses_para_corte < 1:
            return ResultadoGestionConfiguracion(False, "Define al menos un mes para el umbral de corte o alerta.", "VALIDACION")
        if permitir_pago_adelantado and meses_adelanto_maximo < 1:
            return ResultadoGestionConfiguracion(False, "Indica el maximo de meses adelantados permitidos.", "VALIDACION")
        if mora_leve_hasta_meses < 1:
            return ResultadoGestionConfiguracion(False, "El rango de mora leve debe iniciar al menos en 1 mes.", "VALIDACION")
        if mora_media_hasta_meses <= mora_leve_hasta_meses:
            return ResultadoGestionConfiguracion(False, "La mora media debe terminar despues del rango de mora leve.", "VALIDACION")
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
                    "cobro.mora_leve_hasta_meses": str(mora_leve_hasta_meses),
                    "cobro.mora_media_hasta_meses": str(mora_media_hasta_meses),
                },
                actor_id=actor_id,
            )
        except Exception:
            return ResultadoGestionConfiguracion(False, "No fue posible actualizar los parametros de cobro.", "ERROR_SQLITE")
        return ResultadoGestionConfiguracion(True, "Parametros de cobro actualizados.", "OK")

    def guardar_operacion_respaldo(
        self,
        respaldo_automatico: bool,
        ruta_principal: str,
        ruta_secundaria: str,
        secundaria_activa: bool,
        comprimir_zip: bool,
        organizar_por_periodo: bool,
        retencion_dias: int,
        programacion_tipo: str,
        programacion_hora: str,
        programacion_dia_semana: str,
        duracion_sesion_horas: float,
        actor_id: int | None = None,
    ) -> ResultadoGestionConfiguracion:
        ruta_principal = ruta_principal.strip()
        ruta_secundaria = ruta_secundaria.strip()
        programacion_tipo = programacion_tipo.strip().upper()
        programacion_hora = programacion_hora.strip()
        programacion_dia_semana = programacion_dia_semana.strip().upper()

        if duracion_sesion_horas not in DURACIONES_SESION_HORAS_VALIDAS:
            return ResultadoGestionConfiguracion(False, "Selecciona un tiempo de sesion valido.", "VALIDACION")
        if retencion_dias < 1:
            return ResultadoGestionConfiguracion(False, "La retencion minima debe ser de 1 dia.", "VALIDACION")
        if programacion_tipo not in TIPOS_PROGRAMACION_RESPALDO_VALIDOS:
            return ResultadoGestionConfiguracion(False, "Selecciona un tipo de programacion valido.", "VALIDACION")
        valido_principal, mensaje_principal = self._validar_directorio_respaldo(ruta_principal)
        if not valido_principal:
            return ResultadoGestionConfiguracion(False, mensaje_principal, "VALIDACION")
        if secundaria_activa:
            if Path(ruta_secundaria).expanduser().resolve() == Path(ruta_principal).expanduser().resolve():
                return ResultadoGestionConfiguracion(False, "La carpeta secundaria debe ser distinta a la principal.", "VALIDACION")
            valido_secundario, mensaje_secundario = self._validar_directorio_respaldo(ruta_secundaria)
            if not valido_secundario:
                return ResultadoGestionConfiguracion(False, mensaje_secundario, "VALIDACION")
        if respaldo_automatico and programacion_tipo == "DESACTIVADO":
            return ResultadoGestionConfiguracion(False, "Selecciona una programacion diaria o semanal para activar el respaldo automatico.", "VALIDACION")
        if programacion_tipo == "SEMANAL" and programacion_dia_semana not in DIAS_SEMANA_VALIDOS:
            return ResultadoGestionConfiguracion(False, "Selecciona un dia valido para la programacion semanal.", "VALIDACION")
        if programacion_hora not in self.opciones_horario_respaldo():
            return ResultadoGestionConfiguracion(False, "Selecciona una hora valida para la programacion.", "VALIDACION")

        try:
            self._repositorio_configuracion.actualizar_valores(
                {
                    "sistema.respaldo_automatico": "1" if respaldo_automatico else "0",
                    "seguridad.duracion_sesion_horas": self._duracion_a_texto(duracion_sesion_horas),
                    "respaldo.ruta_principal": ruta_principal,
                    "respaldo.ruta_secundaria": ruta_secundaria,
                    "respaldo.secundaria_activa": "1" if secundaria_activa else "0",
                    "respaldo.comprimir_zip": "1" if comprimir_zip else "0",
                    "respaldo.organizar_por_periodo": "1" if organizar_por_periodo else "0",
                    "respaldo.retencion_dias": str(retencion_dias),
                    "respaldo.programacion_tipo": programacion_tipo,
                    "respaldo.programacion_hora": programacion_hora,
                    "respaldo.programacion_dia_semana": programacion_dia_semana,
                },
                actor_id=actor_id,
            )
            if self._servicio_respaldo is not None:
                if respaldo_automatico and programacion_tipo != "DESACTIVADO":
                    self._servicio_respaldo.programar_respaldo_windows(
                        ConfiguracionProgramacionRespaldo(
                            tipo=programacion_tipo,
                            hora=programacion_hora,
                            dia_semana=programacion_dia_semana,
                        ),
                        self._servicio_respaldo.construir_comando_respaldo_programado(),
                    )
                else:
                    self._servicio_respaldo.quitar_programacion_respaldo_windows()
        except Exception:
            return ResultadoGestionConfiguracion(False, "No fue posible actualizar el control de respaldos.", "ERROR_SQLITE")
        return ResultadoGestionConfiguracion(True, "Control y respaldo actualizado.", "OK")

    def crear_respaldo_manual(self, actor_id: int | None = None) -> ResultadoGestionConfiguracion:
        return self._crear_respaldo("MANUAL", actor_id=actor_id)

    def crear_respaldo_automatico(self, actor_id: int | None = None) -> ResultadoGestionConfiguracion:
        return self._crear_respaldo("AUTOMATICO", actor_id=actor_id)

    def _crear_respaldo(
        self,
        tipo_respaldo: str,
        actor_id: int | None = None,
    ) -> ResultadoGestionConfiguracion:
        if self._servicio_respaldo is None:
            return ResultadoGestionConfiguracion(False, "El backend de respaldo no esta disponible.", "ERROR_CONFIG")
        estado = self.obtener_estado()
        try:
            detalle = self._servicio_respaldo.crear_respaldo_manual(
                configuracion=ConfiguracionRespaldoLocal(
                    ruta_principal=estado.operacion.ruta_respaldos_principal,
                    ruta_secundaria=estado.operacion.ruta_respaldos_secundaria,
                    secundaria_activa=estado.operacion.respaldo_secundario_activo,
                    comprimir_zip=estado.operacion.comprimir_zip,
                    organizar_por_periodo=estado.operacion.organizar_por_periodo,
                    retencion_dias=estado.operacion.retencion_dias,
                    programacion=ConfiguracionProgramacionRespaldo(
                        tipo=estado.operacion.programacion_tipo,
                        hora=estado.operacion.programacion_hora,
                        dia_semana=estado.operacion.programacion_dia_semana,
                    ),
                    version_sistema=estado.informacion.version_sistema or "Sin version",
                ),
                repositorio_historial=self._repositorio_configuracion,
                generado_por=actor_id,
                tipo_respaldo=tipo_respaldo,
            )
        except Exception as error:
            return ResultadoGestionConfiguracion(False, f"No fue posible generar el respaldo: {error}", "ERROR_RESPALDO")
        return ResultadoGestionConfiguracion(True, f"Respaldo generado: {detalle.nombre_archivo}", "OK")

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
    def opciones_horario_respaldo() -> tuple[str, ...]:
        return tuple(f"{hora:02d}:00" for hora in range(24))

    @staticmethod
    def opciones_dias_semana() -> tuple[str, ...]:
        return DIAS_SEMANA_VALIDOS

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
        ruta_predeterminada = self._valor_parametro(
            parametros,
            "respaldo.ruta_principal",
            self._valor_parametro(
                parametros,
                "mantenimiento.ruta_respaldos",
                str(self._gestor_rutas.obtener_ruta_respaldos()),
            ),
        )
        retencion_predeterminada = self._a_entero(
            self._valor_parametro(
                parametros,
                "respaldo.retencion_dias",
                self._valor_parametro(parametros, "mantenimiento.dias_retencion_respaldos", "30"),
            )
        )
        return ConfiguracionRespaldoLocal(
            ruta_principal=self._normalizar_ruta_configurada(ruta_predeterminada),
            ruta_secundaria=self._normalizar_ruta_configurada(
                self._valor_parametro(parametros, "respaldo.ruta_secundaria", "")
            ),
            secundaria_activa=self._a_booleano(self._valor_parametro(parametros, "respaldo.secundaria_activa", "0")),
            comprimir_zip=self._a_booleano(self._valor_parametro(parametros, "respaldo.comprimir_zip", "1")),
            organizar_por_periodo=self._a_booleano(
                self._valor_parametro(parametros, "respaldo.organizar_por_periodo", "1")
            ),
            retencion_dias=max(retencion_predeterminada, 1),
            programacion=ConfiguracionProgramacionRespaldo(
                tipo=self._valor_parametro(parametros, "respaldo.programacion_tipo", "DESACTIVADO").upper(),
                hora=self._valor_parametro(parametros, "respaldo.programacion_hora", "18:00"),
                dia_semana=self._valor_parametro(parametros, "respaldo.programacion_dia_semana", "VIERNES").upper(),
            ),
            version_sistema=self._valor_parametro(parametros, "sistema.version", ""),
        )

    def _validar_directorio_respaldo(self, ruta: str) -> tuple[bool, str]:
        if self._servicio_respaldo is None:
            if not ruta.strip():
                return False, "Selecciona una carpeta principal para respaldos."
            return True, ""
        return self._servicio_respaldo.validar_directorio_respaldo(ruta)

    def _normalizar_ruta_configurada(self, ruta: str) -> str:
        ruta_limpia = ruta.strip()
        if not ruta_limpia:
            return ""
        ruta_path = Path(ruta_limpia).expanduser()
        if not ruta_path.is_absolute():
            ruta_path = self._gestor_rutas.raiz_proyecto / ruta_path
        return str(ruta_path)
