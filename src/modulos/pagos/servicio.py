"""Servicios del modulo de pagos."""

from __future__ import annotations

from calendar import monthrange
from datetime import date, datetime

from comun.configuracion.gestor_rutas import GestorRutas
from modulos.documentos import ServicioComprobantePago
from modulos.pagos.entidades import (
    CargoPago,
    ComprobantePago,
    ConfiguracionReciboPago,
    DiagnosticoPagoPlan,
    DiagnosticoPagoActivacion,
    DiagnosticoPagoMensual,
    DetalleAplicacionPago,
    ESTADO_VISUAL_PAGO_BLOQUEADO,
    ESTADO_VISUAL_PAGO_OK,
    EstadoModuloPagos,
    FormularioPago,
    ResumenConfirmacionPago,
    ResultadoPago,
    TIPO_PAGO_CONEXION,
    TIPO_PAGO_MENSUALIDAD,
    TIPO_PAGO_PLAN,
    TIPO_PAGO_RECONEXION,
    TIPOS_PAGO_VALIDOS,
)
from modulos.pagos.repositorio import RepositorioPagos


class ServicioPagos:
    """Orquesta las reglas de negocio del modulo de pagos."""

    def __init__(
        self,
        repositorio_pagos: RepositorioPagos,
        gestor_rutas: GestorRutas | None = None,
        servicio_comprobante_pago: ServicioComprobantePago | None = None,
    ):
        self.repositorio_pagos = repositorio_pagos
        self._gestor_rutas = gestor_rutas or GestorRutas()
        self._servicio_comprobante_pago = servicio_comprobante_pago or ServicioComprobantePago(
            gestor_rutas=self._gestor_rutas,
        )

    def obtener_estado(self, filtro: str = "") -> EstadoModuloPagos:
        configuracion = self.obtener_configuracion_recibo()
        return EstadoModuloPagos(
            casas=tuple(self.repositorio_pagos.listar_casas(filtro=filtro)),
            metodos_pago=tuple(self.repositorio_pagos.listar_metodos_pago_activos()),
            cobrar_mensualidad_prorrateada_activacion=(
                self.repositorio_pagos.cobrar_mensualidad_prorrateada_en_activacion()
            ),
            abrir_pdf_automaticamente=configuracion.abrir_pdf_automaticamente,
            imprimir_pdf_automaticamente=configuracion.imprimir_pdf_automaticamente,
        )

    def obtener_cargos_mensuales(self, casa_id: int) -> tuple[CargoPago, ...]:
        return tuple(self.repositorio_pagos.listar_cargos_mensuales(casa_id))

    def obtener_casa(self, casa_id: int):
        return self.repositorio_pagos.obtener_casa(casa_id)

    def obtener_diagnostico_pago_mensual(self, casa_id: int) -> DiagnosticoPagoMensual | None:
        casa = self.repositorio_pagos.obtener_casa(casa_id)
        if casa is None:
            return None
        alertas: list[str] = []
        resultado = self._validar_estado_operativo_mensual(
            casa.abonado_estado,
            casa.estado_servicio,
            casa.estado_administrativo,
        )
        permite_continuar = resultado is None
        if resultado is not None:
            alertas.append(resultado.mensaje)
        if casa.meses_vencidos > 0:
            alertas.append(
                f"La casa tiene {casa.meses_vencidos} mes(es) vencido(s) y se cobraran primero."
            )
        if casa.estado_servicio == "CORTADO":
            alertas.append(
                "La casa esta cortada: en este flujo solo se permite regularizar deuda existente, sin adelantos."
            )
        if casa.deuda_total_centavos <= 0:
            alertas.append(
                "La casa no tiene deuda mensual pendiente; cualquier pago se tratara como adelanto si la regla vigente lo permite."
            )
        if not alertas:
            alertas.append("La casa cumple las reglas vigentes para continuar con el pago mensual.")
        return DiagnosticoPagoMensual(
            casa_id=casa.casa_id,
            permite_continuar=permite_continuar,
            estado_visual=ESTADO_VISUAL_PAGO_OK if permite_continuar else ESTADO_VISUAL_PAGO_BLOQUEADO,
            mensaje_diagnostico=alertas[0],
            alertas=tuple(alertas),
        )

    def obtener_diagnostico_conexion(self, casa_id: int) -> DiagnosticoPagoActivacion | None:
        return self._obtener_diagnostico_activacion(casa_id, TIPO_PAGO_CONEXION)

    def obtener_diagnostico_reconexion(self, casa_id: int) -> DiagnosticoPagoActivacion | None:
        return self._obtener_diagnostico_activacion(casa_id, TIPO_PAGO_RECONEXION)

    def obtener_diagnostico_plan(self, casa_id: int) -> DiagnosticoPagoPlan | None:
        diagnostico = self.repositorio_pagos.obtener_diagnostico_plan(casa_id)
        if diagnostico is None:
            return None
        casa = self.repositorio_pagos.obtener_casa(casa_id)
        if casa is None:
            return None
        alertas: list[str] = []
        resultado = self._validar_estado_operativo_plan(casa, diagnostico)
        permite_continuar = resultado is None and bool(diagnostico.cuotas_cobrables)
        if resultado is not None:
            alertas.append(resultado.mensaje)
        elif diagnostico.cuotas_cobrables:
            primera = diagnostico.cuotas_cobrables[0]
            alertas.append(
                f"Plan {diagnostico.codigo_plan} listo para cobro. La cuota {primera.numero_cuota} quedara preseleccionada por defecto."
            )
        else:
            alertas.append("El plan no tiene cuotas cobrables con saldo pendiente.")
        return DiagnosticoPagoPlan(
            casa_id=diagnostico.casa_id,
            cantidad_planes_activos=diagnostico.cantidad_planes_activos,
            plan_pago_id=diagnostico.plan_pago_id,
            codigo_plan=diagnostico.codigo_plan,
            tipo_plan=diagnostico.tipo_plan,
            estado_plan=diagnostico.estado_plan,
            cuotas_pendientes=diagnostico.cuotas_pendientes,
            cuotas_en_mora=diagnostico.cuotas_en_mora,
            saldo_vivo_centavos=diagnostico.saldo_vivo_centavos,
            cuotas_cobrables=diagnostico.cuotas_cobrables,
            permite_continuar=permite_continuar,
            estado_visual=ESTADO_VISUAL_PAGO_OK if permite_continuar else ESTADO_VISUAL_PAGO_BLOQUEADO,
            mensaje_diagnostico=alertas[0],
            alertas=tuple(alertas),
        )

    def previsualizar_pago_mensual(
        self,
        formulario: FormularioPago,
    ) -> ResumenConfirmacionPago | ResultadoPago:
        return self.preparar_confirmacion(formulario)

    def previsualizar_pago_conexion(
        self,
        formulario: FormularioPago,
    ) -> ResumenConfirmacionPago | ResultadoPago:
        return self._previsualizar_pago_activacion(formulario, TIPO_PAGO_CONEXION)

    def previsualizar_pago_reconexion(
        self,
        formulario: FormularioPago,
    ) -> ResumenConfirmacionPago | ResultadoPago:
        return self._previsualizar_pago_activacion(formulario, TIPO_PAGO_RECONEXION)

    def previsualizar_pago_plan(
        self,
        formulario: FormularioPago,
    ) -> ResumenConfirmacionPago | ResultadoPago:
        return self._previsualizar_cuota_plan(formulario)

    def preparar_confirmacion(self, formulario: FormularioPago) -> ResumenConfirmacionPago | ResultadoPago:
        if formulario.tipo_pago not in TIPOS_PAGO_VALIDOS:
            return ResultadoPago(False, "El tipo de pago no es valido.", "VALIDACION")
        if formulario.tipo_pago == TIPO_PAGO_CONEXION:
            return self.previsualizar_pago_conexion(formulario)
        if formulario.tipo_pago == TIPO_PAGO_RECONEXION:
            return self.previsualizar_pago_reconexion(formulario)
        if formulario.tipo_pago == TIPO_PAGO_PLAN:
            return self.previsualizar_pago_plan(formulario)
        if formulario.tipo_pago != TIPO_PAGO_MENSUALIDAD:
            return ResultadoPago(False, "El tipo de pago solicitado aun no esta disponible.", "FLUJO_PENDIENTE")
        if formulario.casa_id is None or formulario.casa_id <= 0:
            return ResultadoPago(False, "Selecciona una casa para registrar el pago.", "VALIDACION")
        if formulario.metodo_pago_id is None or formulario.metodo_pago_id <= 0:
            return ResultadoPago(False, "Selecciona un metodo de pago.", "VALIDACION")
        if formulario.cantidad_meses <= 0:
            return ResultadoPago(False, "Indica al menos un mes a pagar.", "VALIDACION")

        casa = self.repositorio_pagos.obtener_casa(formulario.casa_id)
        if casa is None:
            return ResultadoPago(False, "La casa seleccionada ya no existe.", "NO_ENCONTRADO")
        validacion_estado = self._validar_estado_operativo_mensual(
            casa.abonado_estado,
            casa.estado_servicio,
            casa.estado_administrativo,
        )
        if validacion_estado is not None:
            return validacion_estado

        metodo = self.repositorio_pagos.obtener_metodo_pago(formulario.metodo_pago_id)
        if metodo is None:
            return ResultadoPago(False, "El metodo de pago seleccionado no esta activo.", "VALIDACION")
        referencia = formulario.referencia.strip()
        if metodo.requiere_referencia and not referencia:
            return ResultadoPago(False, "Este metodo de pago requiere una referencia.", "VALIDACION")

        resumen_deuda = self.repositorio_pagos.obtener_resumen_deuda_pago(casa.casa_id)
        cargos = self.repositorio_pagos.listar_cargos_mensuales(casa.casa_id)
        precio_mensual = self.repositorio_pagos.obtener_precio_mensual_centavos()
        if precio_mensual <= 0:
            return ResultadoPago(False, "Configura primero el precio mensual del servicio.", "VALIDACION")

        detalles: list[DetalleAplicacionPago] = []
        meses_solicitados = formulario.cantidad_meses
        for cargo in cargos[:meses_solicitados]:
            etiqueta = "Vencido" if cargo.estado == "VENCIDO" else "Pendiente"
            detalles.append(
                DetalleAplicacionPago(
                    cargo_id=cargo.identificador,
                    periodo_id=cargo.periodo_id,
                    periodo_anio=cargo.periodo_anio,
                    periodo_mes=cargo.periodo_mes,
                    periodo_nombre=cargo.periodo_nombre,
                    concepto_codigo=cargo.concepto_codigo,
                    descripcion=cargo.descripcion,
                    monto_centavos=cargo.saldo_pendiente_centavos,
                    etiqueta=etiqueta,
                    es_adelantado=False,
                )
            )

        meses_adelantados = meses_solicitados - len(detalles)
        if meses_adelantados > 0:
            if casa.estado_servicio == "CORTADO":
                return ResultadoPago(
                    False,
                    "No se pueden registrar meses adelantados mientras la casa este cortada. Primero regulariza la deuda pendiente.",
                    "VALIDACION",
                )
            if resumen_deuda.deuda_vencida_no_mensual_centavos > 0:
                return ResultadoPago(
                    False,
                    "No se pueden registrar pagos adelantados mientras exista deuda vencida no mensual.",
                    "VALIDACION",
                )
            ultimo_anio, ultimo_mes = self._resolver_ultimo_periodo(cargos)
            for desplazamiento in range(1, meses_adelantados + 1):
                anio, mes = self._sumar_meses(ultimo_anio, ultimo_mes, desplazamiento)
                detalles.append(
                    DetalleAplicacionPago(
                        cargo_id=None,
                        periodo_id=None,
                        periodo_anio=anio,
                        periodo_mes=mes,
                        periodo_nombre=f"Periodo {mes:02d}/{anio:04d}",
                        concepto_codigo="SERVICIO_MENSUAL",
                        descripcion=f"Mensualidad adelantada {mes:02d}/{anio:04d}",
                        monto_centavos=precio_mensual,
                        etiqueta="Adelantado",
                        es_adelantado=True,
                    )
                )

        total_pago = sum(detalle.monto_centavos for detalle in detalles)
        monto_aplicado_deuda = sum(
            detalle.monto_centavos for detalle in detalles if not detalle.es_adelantado
        )
        saldo_posterior = max(0, casa.deuda_total_centavos - monto_aplicado_deuda)
        return ResumenConfirmacionPago(
            casa=casa,
            tipo_pago=formulario.tipo_pago,
            metodo_pago=metodo,
            detalles=tuple(detalles),
            saldo_anterior_centavos=casa.deuda_total_centavos,
            total_pago_centavos=total_pago,
            saldo_posterior_centavos=saldo_posterior,
            referencia=referencia,
            observaciones=formulario.observaciones.strip(),
            fecha_activacion="",
        )

    def registrar_pago(
        self,
        formulario: FormularioPago,
        actor_id: int | None,
    ) -> ResultadoPago:
        if actor_id is None or actor_id <= 0:
            return ResultadoPago(False, "No hay un usuario valido registrando el pago.", "VALIDACION")
        confirmacion = self.preparar_confirmacion(formulario)
        if isinstance(confirmacion, ResultadoPago):
            return confirmacion
        try:
            if confirmacion.es_operacion_compuesta and confirmacion.tipo_operacion_compuesta == "RECONEXION_COMPUESTA":
                comprobantes = self.repositorio_pagos.guardar_operacion_compuesta_confirmada(
                    resumen=confirmacion,
                    actor_id=actor_id,
                )
                comprobante = comprobantes[-1] if comprobantes else None
            else:
                comprobante = self.repositorio_pagos.guardar_pago_confirmado(
                    resumen=confirmacion,
                    actor_id=actor_id,
                )
                comprobantes = () if comprobante is None else (comprobante,)
        except Exception as error:
            return ResultadoPago(False, f"No fue posible registrar el pago. {error}", "ERROR_SQLITE")
        mensaje = f"Pago registrado correctamente. Comprobante {comprobante.numero_comprobante}." if comprobante is not None else "Pago registrado correctamente."
        if len(comprobantes) > 1:
            numeros = ", ".join(item.numero_comprobante for item in comprobantes)
            mensaje = f"Operacion registrada con comprobantes separados: {numeros}."
        return ResultadoPago(
            True,
            mensaje,
            "OK",
            comprobante,
            tuple(comprobantes),
        )

    def _validar_estado_operativo_mensual(
        self,
        abonado_estado: str,
        estado_servicio: str,
        estado_administrativo: str,
    ) -> ResultadoPago | None:
        if abonado_estado != "ACTIVO":
            return ResultadoPago(
                False,
                "Solo se puede registrar pago mensual cuando el abonado responsable esta ACTIVO.",
                "VALIDACION",
            )
        if estado_administrativo != "OPERATIVA":
            return ResultadoPago(
                False,
                "No se puede registrar pago mensual para una casa suspendida administrativamente. Reactiva o reasigna primero un abonado activo responsable.",
                "VALIDACION",
            )
        if estado_servicio == "INACTIVO":
            return ResultadoPago(False, "No se puede registrar pago mensual para una casa inactiva.", "VALIDACION")
        if estado_servicio not in {"ACTIVO", "CORTADO"}:
            return ResultadoPago(
                False,
                f"La casa debe estar ACTIVA o CORTADA para registrar regularizacion mensual. Estado actual: {estado_servicio}.",
                "VALIDACION",
            )
        return None

    def _validar_estado_operativo_plan(
        self,
        casa: object,
        diagnostico: DiagnosticoPagoPlan,
    ) -> ResultadoPago | None:
        if casa.abonado_estado != "ACTIVO":
            return ResultadoPago(
                False,
                "Solo se pueden cobrar cuotas de plan cuando el abonado responsable esta ACTIVO.",
                "VALIDACION",
            )
        if casa.estado_administrativo != "OPERATIVA":
            return ResultadoPago(
                False,
                "La casa esta suspendida administrativamente. Reactiva o reasigna primero el abonado responsable.",
                "VALIDACION",
            )
        if diagnostico.cantidad_planes_activos <= 0:
            return ResultadoPago(
                False,
                "La casa no tiene un plan activo disponible para este flujo.",
                "VALIDACION",
            )
        if diagnostico.cantidad_planes_activos > 1:
            return ResultadoPago(
                False,
                "La casa tiene mas de un plan activo. Debes corregir esa inconsistencia antes de cobrar cuotas.",
                "VALIDACION",
            )
        if diagnostico.plan_pago_id is None:
            return ResultadoPago(
                False,
                "No fue posible identificar el plan activo de la casa.",
                "VALIDACION",
            )
        if not diagnostico.cuotas_cobrables:
            return ResultadoPago(
                False,
                "El plan activo no tiene cuotas pendientes, parciales o vencidas con saldo pendiente.",
                "VALIDACION",
            )
        return None

    def _obtener_diagnostico_activacion(
        self,
        casa_id: int,
        tipo_pago: str,
    ) -> DiagnosticoPagoActivacion | None:
        casa = self.repositorio_pagos.obtener_casa(casa_id)
        if casa is None:
            return None
        alertas: list[str] = []
        resultado = self._validar_estado_operativo_activacion(casa, tipo_pago)
        permite_continuar = resultado is None
        if resultado is not None:
            alertas.append(resultado.mensaje)
        clasificacion = self._resolver_clasificacion_activacion(casa)
        if not alertas:
            alertas.append(
                f"La casa esta lista para {clasificacion.lower()} dentro del flujo de {tipo_pago.lower()}."
            )
        return DiagnosticoPagoActivacion(
            casa_id=casa.casa_id,
            tipo_pago=tipo_pago,
            clasificacion=clasificacion,
            permite_continuar=permite_continuar,
            estado_visual=ESTADO_VISUAL_PAGO_OK if permite_continuar else ESTADO_VISUAL_PAGO_BLOQUEADO,
            mensaje_diagnostico=alertas[0],
            alertas=tuple(alertas),
        )

    def _validar_estado_operativo_activacion(
        self,
        casa: object,
        tipo_pago: str,
    ) -> ResultadoPago | None:
        clasificacion = self._resolver_clasificacion_activacion(casa)
        if casa.abonado_estado != "ACTIVO":
            return ResultadoPago(
                False,
                "La activacion solo se permite cuando el abonado responsable esta ACTIVO.",
                "VALIDACION",
            )
        if casa.estado_administrativo != "OPERATIVA":
            return ResultadoPago(
                False,
                "La casa esta suspendida administrativamente. Resuelve primero el abonado o la reasignacion.",
                "VALIDACION",
            )
        if casa.estado_servicio != "CORTADO":
            return ResultadoPago(
                False,
                "Conexion y reconexion solo aplican cuando la casa esta fisicamente CORTADA.",
                "VALIDACION",
            )
        if casa.tiene_plan_activo:
            return ResultadoPago(
                False,
                "La casa tiene un plan de pago activo. Este flujo debe resolverse desde el flujo especifico del plan.",
                "VALIDACION",
            )
        if tipo_pago == TIPO_PAGO_CONEXION and clasificacion != TIPO_PAGO_CONEXION:
            return ResultadoPago(
                False,
                "Esta casa ya tuvo servicio activo antes. Debe cobrarse como reconexion.",
                "VALIDACION",
            )
        if tipo_pago == TIPO_PAGO_RECONEXION and clasificacion != TIPO_PAGO_RECONEXION:
            return ResultadoPago(
                False,
                "Esta casa nunca ha tenido servicio activo. Debe cobrarse como conexion.",
                "VALIDACION",
            )
        return None

    def _previsualizar_cuota_plan(
        self,
        formulario: FormularioPago,
    ) -> ResumenConfirmacionPago | ResultadoPago:
        if formulario.casa_id is None or formulario.casa_id <= 0:
            return ResultadoPago(False, "Selecciona una casa para registrar el pago.", "VALIDACION")
        if formulario.metodo_pago_id is None or formulario.metodo_pago_id <= 0:
            return ResultadoPago(False, "Selecciona un metodo de pago.", "VALIDACION")
        casa = self.repositorio_pagos.obtener_casa(formulario.casa_id)
        if casa is None:
            return ResultadoPago(False, "La casa seleccionada ya no existe.", "NO_ENCONTRADO")
        diagnostico = self.obtener_diagnostico_plan(formulario.casa_id)
        if diagnostico is None:
            return ResultadoPago(False, "No fue posible obtener el diagnostico del plan.", "ERROR")
        validacion = self._validar_estado_operativo_plan(casa, diagnostico)
        if validacion is not None:
            return validacion
        metodo = self.repositorio_pagos.obtener_metodo_pago(formulario.metodo_pago_id)
        if metodo is None:
            return ResultadoPago(False, "El metodo de pago seleccionado no esta activo.", "VALIDACION")
        referencia = formulario.referencia.strip()
        if metodo.requiere_referencia and not referencia:
            return ResultadoPago(False, "Este metodo de pago requiere una referencia.", "VALIDACION")
        cuotas_por_id = {cuota.cuota_id: cuota for cuota in diagnostico.cuotas_cobrables}
        cuotas_ids = tuple(int(cuota_id) for cuota_id in formulario.cuotas_plan_pago_ids if cuota_id)
        if not cuotas_ids:
            return ResultadoPago(False, "Selecciona al menos una cuota del plan.", "VALIDACION")
        detalles: list[DetalleAplicacionPago] = []
        total_pago = 0
        for cuota_id in cuotas_ids:
            cuota = cuotas_por_id.get(cuota_id)
            if cuota is None:
                return ResultadoPago(
                    False,
                    "Una de las cuotas seleccionadas ya no esta disponible para cobro.",
                    "VALIDACION",
                )
            descripcion = (
                f"Cuota {cuota.numero_cuota} del plan {diagnostico.codigo_plan} "
                f"(vence {cuota.fecha_vencimiento})"
            )
            detalles.append(
                DetalleAplicacionPago(
                    cargo_id=cuota.cuota_id,
                    periodo_id=None,
                    periodo_anio=None,
                    periodo_mes=None,
                    periodo_nombre=f"Cuota {cuota.numero_cuota}",
                    concepto_codigo="CUOTA_PLAN_PAGO",
                    descripcion=descripcion,
                    monto_centavos=cuota.saldo_pendiente_centavos,
                    etiqueta=cuota.estado.title(),
                )
            )
            total_pago += cuota.saldo_pendiente_centavos
        saldo_posterior = max(0, diagnostico.saldo_vivo_centavos - total_pago)
        return ResumenConfirmacionPago(
            casa=casa,
            tipo_pago=TIPO_PAGO_PLAN,
            metodo_pago=metodo,
            detalles=tuple(detalles),
            saldo_anterior_centavos=diagnostico.saldo_vivo_centavos,
            total_pago_centavos=total_pago,
            saldo_posterior_centavos=saldo_posterior,
            referencia=referencia,
            observaciones=formulario.observaciones.strip(),
            fecha_activacion="",
            plan_pago_id=diagnostico.plan_pago_id,
        )

    def _previsualizar_pago_activacion(
        self,
        formulario: FormularioPago,
        tipo_pago: str,
    ) -> ResumenConfirmacionPago | ResultadoPago:
        if formulario.casa_id is None or formulario.casa_id <= 0:
            return ResultadoPago(False, "Selecciona una casa para registrar el pago.", "VALIDACION")
        if formulario.metodo_pago_id is None or formulario.metodo_pago_id <= 0:
            return ResultadoPago(False, "Selecciona un metodo de pago.", "VALIDACION")
        casa = self.repositorio_pagos.obtener_casa(formulario.casa_id)
        if casa is None:
            return ResultadoPago(False, "La casa seleccionada ya no existe.", "NO_ENCONTRADO")
        validacion = self._validar_estado_operativo_activacion(casa, tipo_pago)
        if validacion is not None:
            return validacion

        metodo = self.repositorio_pagos.obtener_metodo_pago(formulario.metodo_pago_id)
        if metodo is None:
            return ResultadoPago(False, "El metodo de pago seleccionado no esta activo.", "VALIDACION")
        referencia = formulario.referencia.strip()
        if metodo.requiere_referencia and not referencia:
            return ResultadoPago(False, "Este metodo de pago requiere una referencia.", "VALIDACION")

        fecha_activacion = formulario.fecha_activacion.strip()
        if not fecha_activacion:
            return ResultadoPago(False, "Indica la fecha de activacion del servicio.", "VALIDACION")
        try:
            fecha_real = date.fromisoformat(fecha_activacion)
        except ValueError:
            return ResultadoPago(False, "La fecha de activacion no es valida.", "VALIDACION")

        detalles: list[DetalleAplicacionPago] = []
        if tipo_pago == TIPO_PAGO_RECONEXION:
            resumen_deuda = self.repositorio_pagos.obtener_resumen_deuda_pago(casa.casa_id)
            cargos_mensuales = self.repositorio_pagos.listar_cargos_mensuales(casa.casa_id)
            if resumen_deuda.deuda_total_centavos > 0 and not cargos_mensuales:
                return ResultadoPago(
                    False,
                    "La casa tiene deuda activa no mensual que debe regularizarse antes de la reconexion compuesta.",
                    "VALIDACION",
                )
            for cargo in cargos_mensuales:
                detalles.append(
                    DetalleAplicacionPago(
                        cargo_id=cargo.identificador,
                        periodo_id=cargo.periodo_id,
                        periodo_anio=cargo.periodo_anio,
                        periodo_mes=cargo.periodo_mes,
                        periodo_nombre=cargo.periodo_nombre,
                        concepto_codigo=cargo.concepto_codigo,
                        descripcion=cargo.descripcion,
                        monto_centavos=cargo.saldo_pendiente_centavos,
                        etiqueta="Regularizacion",
                        tipo_pago_destino=TIPO_PAGO_MENSUALIDAD,
                    )
                )
        if tipo_pago == TIPO_PAGO_CONEXION:
            if formulario.monto_conexion_centavos <= 0:
                return ResultadoPago(False, "Indica un monto valido para la conexion.", "VALIDACION")
            detalles.append(
                DetalleAplicacionPago(
                    cargo_id=None,
                    periodo_id=None,
                    periodo_anio=None,
                    periodo_mes=None,
                    periodo_nombre="Operacion de activacion",
                    concepto_codigo="CONEXION",
                    descripcion="Conexion de servicio",
                    monto_centavos=formulario.monto_conexion_centavos,
                    etiqueta="Conexion",
                    tipo_pago_destino=TIPO_PAGO_CONEXION,
                )
            )
        else:
            if formulario.monto_reconexion_centavos <= 0:
                return ResultadoPago(False, "Indica un monto valido para la reconexion.", "VALIDACION")
            detalles.append(
                DetalleAplicacionPago(
                    cargo_id=None,
                    periodo_id=None,
                    periodo_anio=None,
                    periodo_mes=None,
                    periodo_nombre="Operacion de activacion",
                    concepto_codigo="RECONEXION",
                    descripcion="Reconexion de servicio",
                    monto_centavos=formulario.monto_reconexion_centavos,
                    etiqueta="Reconexion",
                    tipo_pago_destino=TIPO_PAGO_RECONEXION,
                )
            )
            if formulario.multa_corte_centavos > 0:
                detalles.append(
                    DetalleAplicacionPago(
                        cargo_id=None,
                        periodo_id=None,
                        periodo_anio=None,
                        periodo_mes=None,
                        periodo_nombre="Operacion de activacion",
                        concepto_codigo="MULTA",
                        descripcion="Multa por corte",
                        monto_centavos=formulario.multa_corte_centavos,
                        etiqueta="Multa",
                        tipo_pago_destino=TIPO_PAGO_RECONEXION,
                    )
                )

        if self.repositorio_pagos.cobrar_mensualidad_prorrateada_en_activacion():
            precio_mensual = self.repositorio_pagos.obtener_precio_mensual_centavos()
            if precio_mensual <= 0:
                return ResultadoPago(
                    False,
                    "Configura primero el precio mensual del servicio para calcular el prorrateo.",
                    "VALIDACION",
                )
            dias_mes = monthrange(fecha_real.year, fecha_real.month)[1]
            dias_cobrados = (dias_mes - fecha_real.day) + 1
            monto_prorrateado = round((precio_mensual * dias_cobrados) / dias_mes)
            detalles.append(
                DetalleAplicacionPago(
                    cargo_id=None,
                    periodo_id=None,
                    periodo_anio=fecha_real.year,
                    periodo_mes=fecha_real.month,
                    periodo_nombre=f"Periodo {fecha_real.month:02d}/{fecha_real.year:04d}",
                    concepto_codigo="MENSUALIDAD_PRORRATEADA",
                    descripcion=f"Mensualidad prorrateada desde {fecha_real.isoformat()}",
                    monto_centavos=monto_prorrateado,
                    etiqueta="Prorrateo",
                    tipo_pago_destino=tipo_pago,
                )
            )

        total_pago = sum(detalle.monto_centavos for detalle in detalles)
        monto_regularizado = sum(
            detalle.monto_centavos
            for detalle in detalles
            if detalle.tipo_pago_destino == TIPO_PAGO_MENSUALIDAD
        )
        return ResumenConfirmacionPago(
            casa=casa,
            tipo_pago=tipo_pago,
            metodo_pago=metodo,
            detalles=tuple(detalles),
            saldo_anterior_centavos=casa.deuda_total_centavos,
            total_pago_centavos=total_pago,
            saldo_posterior_centavos=max(0, casa.deuda_total_centavos - monto_regularizado),
            referencia=referencia,
            observaciones=formulario.observaciones.strip(),
            fecha_activacion=fecha_activacion,
            es_operacion_compuesta=(tipo_pago == TIPO_PAGO_RECONEXION and monto_regularizado > 0),
            tipo_operacion_compuesta=(
                "RECONEXION_COMPUESTA"
                if tipo_pago == TIPO_PAGO_RECONEXION and monto_regularizado > 0
                else ""
            ),
        )

    @staticmethod
    def _resolver_clasificacion_activacion(casa: object) -> str:
        return TIPO_PAGO_RECONEXION if casa.ha_tenido_servicio_activo else TIPO_PAGO_CONEXION

    def obtener_comprobante(self, pago_id: int) -> ComprobantePago | None:
        return self.repositorio_pagos.obtener_comprobante(pago_id)

    def obtener_configuracion_recibo(self) -> ConfiguracionReciboPago:
        return self.repositorio_pagos.obtener_configuracion_recibo()

    def generar_comprobante_pdf(self, pago_id: int, ruta_destino: str | None = None) -> str:
        comprobante = self.obtener_comprobante(pago_id)
        if comprobante is None:
            raise ValueError("No fue posible recuperar el comprobante solicitado.")
        configuracion = self.obtener_configuracion_recibo()
        return self._servicio_comprobante_pago.generar_pdf(
            comprobante=comprobante,
            configuracion=configuracion,
            formateador_moneda=self.formatear_moneda,
            formateador_fecha=self.formatear_fecha,
            formateador_hora=self.formatear_hora,
            etiqueta_tipo_pago=self._etiqueta_tipo_pago,
            ruta_destino=ruta_destino,
        )

    def ruta_sugerida_comprobante(self, comprobante: ComprobantePago, extension: str = ".pdf") -> str:
        base = self._gestor_rutas.obtener_ruta_exportaciones_comprobantes()
        return str(base / f"{comprobante.numero_comprobante}{extension}")

    @staticmethod
    def formatear_moneda(valor_centavos: int) -> str:
        return f"L {valor_centavos / 100:,.2f}"

    @staticmethod
    def formatear_fecha(valor: str) -> str:
        if not valor:
            return "Sin registro"
        try:
            fecha = datetime.fromisoformat(valor)
        except ValueError:
            return valor
        return fecha.strftime("%d/%m/%Y")

    @staticmethod
    def formatear_hora(valor: str) -> str:
        if not valor:
            return "Sin registro"
        try:
            fecha = datetime.fromisoformat(valor)
        except ValueError:
            return valor
        return fecha.strftime("%H:%M")

    def _separar_fecha_hora(self, valor: str) -> tuple[str, str]:
        return self.formatear_fecha(valor), self.formatear_hora(valor)

    @staticmethod
    def _resolver_ultimo_periodo(cargos: list[object]) -> tuple[int, int]:
        periodos = [
            (cargo.periodo_anio, cargo.periodo_mes)
            for cargo in cargos
            if cargo.periodo_anio is not None and cargo.periodo_mes is not None
        ]
        if periodos:
            return max(periodos)
        hoy = date.today()
        if hoy.month == 1:
            return hoy.year - 1, 12
        return hoy.year, hoy.month - 1

    @staticmethod
    def _sumar_meses(anio: int, mes: int, desplazamiento: int) -> tuple[int, int]:
        indice = (anio * 12) + (mes - 1) + desplazamiento
        return indice // 12, (indice % 12) + 1

    @staticmethod
    def _etiqueta_tipo_pago(tipo_pago: str) -> str:
        etiquetas = {
            "MENSUALIDAD": "Mensualidad",
            "PLAN_PAGO": "Plan de pago",
            "CONEXION": "Conexion",
            "RECONEXION": "Reconexion",
        }
        return etiquetas.get(tipo_pago, tipo_pago)
