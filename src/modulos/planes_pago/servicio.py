"""Servicios del modulo de planes de pago."""

from __future__ import annotations

import csv
from calendar import monthrange
from dataclasses import dataclass
from datetime import date, datetime

from modulos.planes_pago.entidades import (
    DetallePlanPago,
    ESTADOS_PLAN_VALIDOS,
    FILTRO_PLANES_TODOS,
    FormularioPlanPago,
    OpcionAbonadoPlanPago,
    OpcionCasaPlanPago,
    PaginaPlanesPago,
    PlanPago,
    ResumenConfirmacionPlanPago,
    ResumenPlanesPago,
    ResultadoGestionPlanesPago,
    TIPOS_PLAN_VALIDOS,
)
from modulos.planes_pago.repositorio import RepositorioPlanesPago


@dataclass(slots=True)
class _EvaluacionPlanPago:
    casa: OpcionCasaPlanPago
    plan_actual: PlanPago | None
    metodo_nombre: str
    referencia_pago: str
    fecha_activacion: date
    deuda_financiada_centavos: int
    monto_activacion_centavos: int
    monto_total_centavos: int
    saldo_financiado_centavos: int
    cuota_regular_centavos: int
    cuotas: list[int]
    fechas_cuotas: list[str]
    cargos_vinculados: tuple[int, ...]
    es_creacion: bool


class ServicioPlanesPago:
    """Orquesta reglas de negocio del modulo de planes de pago."""

    TAMANO_PAGINA = 10

    def __init__(self, repositorio_planes_pago: RepositorioPlanesPago) -> None:
        self._repositorio_planes_pago = repositorio_planes_pago

    def obtener_resumen(self) -> ResumenPlanesPago:
        return self._repositorio_planes_pago.obtener_resumen()

    def listar(
        self,
        filtro: str = "",
        filtro_rapido: str = FILTRO_PLANES_TODOS,
        pagina: int = 1,
    ) -> PaginaPlanesPago:
        pagina = max(1, pagina)
        total_registros = self._repositorio_planes_pago.contar(filtro, filtro_rapido)
        total_paginas = max(1, (total_registros + self.TAMANO_PAGINA - 1) // self.TAMANO_PAGINA)
        pagina = min(pagina, total_paginas)
        items = self._repositorio_planes_pago.listar(
            filtro=filtro,
            filtro_rapido=filtro_rapido,
            limite=self.TAMANO_PAGINA,
            desplazamiento=(pagina - 1) * self.TAMANO_PAGINA,
        )
        return PaginaPlanesPago(
            items=items,
            pagina_actual=pagina,
            tamano_pagina=self.TAMANO_PAGINA,
            total_registros=total_registros,
        )

    def obtener_por_id(self, plan_id: int) -> PlanPago | None:
        return self._repositorio_planes_pago.obtener_por_id(plan_id)

    def obtener_detalle(self, plan_id: int) -> DetallePlanPago | None:
        return self._repositorio_planes_pago.obtener_detalle(plan_id)

    def listar_casas_disponibles(self) -> list[OpcionCasaPlanPago]:
        return self._repositorio_planes_pago.listar_casas_disponibles()

    def listar_casas_elegibles_nuevo_plan(self) -> list[OpcionCasaPlanPago]:
        return [
            casa
            for casa in self.listar_casas_disponibles()
            if self._es_casa_elegible_nuevo_plan(casa)
        ]

    def listar_abonados_nuevo_plan(self) -> list[OpcionAbonadoPlanPago]:
        casas = self.listar_casas_disponibles()
        casas_por_abonado: dict[int, list[OpcionCasaPlanPago]] = {}
        for casa in casas:
            casas_por_abonado.setdefault(casa.abonado_id, []).append(casa)

        abonados: list[OpcionAbonadoPlanPago] = []
        for abonado_id, casas_abonado in casas_por_abonado.items():
            casas_elegibles = tuple(
                casa for casa in casas_abonado if self._es_casa_elegible_nuevo_plan(casa)
            )
            muestra = casas_abonado[0]
            abonados.append(
                OpcionAbonadoPlanPago(
                    abonado_id=abonado_id,
                    abonado_nombre=muestra.abonado_nombre,
                    abonado_dni=muestra.abonado_dni,
                    apto_para_plan=bool(casas_elegibles),
                    motivo_no_apto="" if casas_elegibles else self._resolver_motivo_no_apto(casas_abonado),
                    casas_elegibles=casas_elegibles,
                )
            )
        abonados.sort(key=lambda item: (item.abonado_nombre.casefold(), item.abonado_dni))
        return abonados

    def listar_metodos_pago_activos(self):
        return self._repositorio_planes_pago.listar_metodos_pago_activos()

    def previsualizar_confirmacion(
        self,
        formulario: FormularioPlanPago,
    ) -> ResumenConfirmacionPlanPago | ResultadoGestionPlanesPago:
        evaluacion = self._evaluar_formulario(formulario)
        if isinstance(evaluacion, ResultadoGestionPlanesPago):
            return evaluacion
        return ResumenConfirmacionPlanPago(
            casa_id=evaluacion.casa.casa_id,
            casa_codigo=evaluacion.casa.casa_codigo,
            abonado_nombre=evaluacion.casa.abonado_nombre,
            abonado_dni=evaluacion.casa.abonado_dni,
            barrio_nombre=evaluacion.casa.barrio_nombre,
            tipo_plan=self._resolver_tipo_plan(evaluacion.casa),
            fecha_activacion=evaluacion.fecha_activacion.isoformat(),
            metodo_pago_nombre=evaluacion.metodo_nombre,
            referencia_pago=evaluacion.referencia_pago,
            deuda_financiada_centavos=evaluacion.deuda_financiada_centavos,
            monto_activacion_centavos=evaluacion.monto_activacion_centavos,
            monto_total_centavos=evaluacion.monto_total_centavos,
            prima_centavos=formulario.prima_centavos,
            saldo_financiado_centavos=evaluacion.saldo_financiado_centavos,
            cuota_regular_centavos=evaluacion.cuota_regular_centavos,
            cantidad_cuotas=formulario.cantidad_cuotas,
            primer_vencimiento=evaluacion.fechas_cuotas[0] if evaluacion.fechas_cuotas else "",
            ultimo_vencimiento=evaluacion.fechas_cuotas[-1] if evaluacion.fechas_cuotas else "",
            observaciones=formulario.observaciones.strip(),
        )

    def guardar(
        self,
        formulario: FormularioPlanPago,
        actor_id: int | None = None,
    ) -> ResultadoGestionPlanesPago:
        if actor_id is None or actor_id <= 0:
            return ResultadoGestionPlanesPago(False, "No hay un usuario valido registrando el plan.", "VALIDACION")
        evaluacion = self._evaluar_formulario(formulario)
        if isinstance(evaluacion, ResultadoGestionPlanesPago):
            return evaluacion
        casa = evaluacion.casa
        plan_actual = evaluacion.plan_actual
        estado_plan = "ACTIVO" if evaluacion.es_creacion else (
            plan_actual.estado if plan_actual is not None else "ACTIVO"
        )
        plan = PlanPago(
            identificador=formulario.identificador,
            casa_id=casa.casa_id,
            casa_codigo=casa.casa_codigo,
            abonado_id=casa.abonado_id,
            abonado_nombre=casa.abonado_nombre,
            abonado_dni=casa.abonado_dni,
            barrio_nombre=casa.barrio_nombre,
            tipo_plan=self._resolver_tipo_plan(casa),
            concepto_financiado=self._resolver_tipo_plan(casa),
            tipo_activacion_origen=self._resolver_tipo_plan(casa) if evaluacion.es_creacion else (
                plan_actual.tipo_activacion_origen if plan_actual is not None else self._resolver_tipo_plan(casa)
            ),
            fecha_corte_deuda=evaluacion.fecha_activacion.isoformat() if evaluacion.es_creacion else (
                plan_actual.fecha_corte_deuda if plan_actual is not None else ""
            ),
            deuda_financiada_centavos=evaluacion.deuda_financiada_centavos,
            monto_activacion_centavos=evaluacion.monto_activacion_centavos,
            prima_centavos=formulario.prima_centavos,
            saldo_financiado_centavos=evaluacion.saldo_financiado_centavos,
            monto_total_centavos=evaluacion.monto_total_centavos,
            cuota_regular_centavos=evaluacion.cuota_regular_centavos,
            cantidad_cuotas=formulario.cantidad_cuotas,
            estado=estado_plan,
            observaciones=formulario.observaciones.strip(),
        )
        try:
            self._repositorio_planes_pago.guardar_plan(
                plan=plan,
                cuotas=list(zip(evaluacion.fechas_cuotas, evaluacion.cuotas)),
                cargos_vinculados=evaluacion.cargos_vinculados,
                metodo_pago_id=formulario.metodo_pago_id if evaluacion.es_creacion else None,
                referencia_pago=evaluacion.referencia_pago,
                fecha_activacion=evaluacion.fecha_activacion.isoformat(),
                actor_id=actor_id,
                activar_servicio_con_plan=evaluacion.es_creacion,
            )
        except Exception as error:
            mensaje_error = str(error).strip() or error.__class__.__name__
            if "fecha" in mensaje_error.casefold():
                mensaje_error = f"Revisa la fecha de activacion o los vencimientos generados. {mensaje_error}"
            return ResultadoGestionPlanesPago(
                False,
                f"No fue posible guardar el plan de pago. {mensaje_error}",
                "ERROR_SQLITE",
            )
        mensaje = "Plan de pago actualizado correctamente." if formulario.identificador else "Plan de pago creado correctamente."
        return ResultadoGestionPlanesPago(True, mensaje, "OK")

    def exportar_csv(
        self,
        ruta_destino: str,
        filtro: str = "",
        filtro_rapido: str = FILTRO_PLANES_TODOS,
    ) -> ResultadoGestionPlanesPago:
        planes = self._repositorio_planes_pago.listar(
            filtro=filtro,
            filtro_rapido=filtro_rapido,
            limite=None,
            desplazamiento=0,
        )
        try:
            with open(ruta_destino, "w", newline="", encoding="utf-8") as archivo:
                escritor = csv.writer(archivo)
                escritor.writerow(
                    [
                        "Codigo",
                        "Casa",
                        "Abonado",
                        "Tipo de plan",
                        "Concepto financiado",
                        "Prima",
                        "Saldo financiado",
                        "Cuota",
                        "Cuotas pendientes",
                        "Estado",
                        "Creado",
                        "Ultima actualizacion",
                    ]
                )
                for plan in planes:
                    escritor.writerow(
                        [
                            plan.codigo,
                            plan.casa_codigo,
                            plan.abonado_nombre,
                            plan.tipo_plan,
                            plan.concepto_financiado,
                            self.formatear_moneda(plan.prima_centavos),
                            self.formatear_moneda(plan.saldo_financiado_centavos),
                            self.formatear_moneda(plan.cuota_regular_centavos),
                            plan.cuotas_pendientes,
                            plan.estado,
                            self.formatear_fecha(plan.creado_en),
                            self.formatear_fecha(plan.actualizado_en),
                        ]
                    )
        except OSError:
            return ResultadoGestionPlanesPago(False, "No fue posible exportar el listado de planes.", "ERROR_EXPORTACION")
        return ResultadoGestionPlanesPago(True, "Listado exportado correctamente.", "OK")

    @staticmethod
    def formatear_moneda(valor_centavos: int) -> str:
        return f"L {valor_centavos / 100:,.2f}"

    @staticmethod
    def calcular_cuota_regular(total_centavos: int, cantidad_cuotas: int) -> int:
        if total_centavos <= 0 or cantidad_cuotas <= 0:
            return 0
        return total_centavos // cantidad_cuotas

    @staticmethod
    def formatear_fecha(valor: str) -> str:
        if not valor:
            return "Sin registro"
        try:
            fecha = datetime.fromisoformat(valor)
        except ValueError:
            return valor
        return fecha.strftime("%d/%m/%Y")

    def _construir_cuotas(self, total: int, cuota_regular: int, cantidad: int) -> list[int] | None:
        cuotas: list[int] = []
        restante = total
        for indice in range(cantidad):
            cuota = cuota_regular if indice < cantidad - 1 else restante
            cuotas.append(cuota)
            restante -= cuota
        if restante != 0 or sum(cuotas) != total or any(cuota <= 0 for cuota in cuotas):
            return None
        return cuotas

    def _construir_fechas_cuotas(self, fecha_base: date, cantidad: int) -> list[str]:
        fechas: list[str] = []
        for desplazamiento in range(cantidad):
            mes = fecha_base.month + desplazamiento + 1
            anio = fecha_base.year + ((mes - 1) // 12)
            mes_real = ((mes - 1) % 12) + 1
            dia = min(fecha_base.day, monthrange(anio, mes_real)[1])
            fechas.append(date(anio, mes_real, dia).isoformat())
        return fechas

    @staticmethod
    def _resolver_tipo_plan(casa: OpcionCasaPlanPago) -> str:
        return "RECONEXION" if casa.ha_tenido_servicio_activo else "CONEXION"

    def _es_casa_elegible_nuevo_plan(self, casa: OpcionCasaPlanPago) -> bool:
        return (
            casa.abonado_id > 0
            and casa.abonado_estado == "ACTIVO"
            and casa.estado_administrativo == "OPERATIVA"
            and casa.estado_servicio == "CORTADO"
            and not casa.tiene_plan_activo
        )

    def _resolver_motivo_no_apto(self, casas_abonado: list[OpcionCasaPlanPago]) -> str:
        if not casas_abonado:
            return "No tiene casas asociadas"
        if all(casa.abonado_estado != "ACTIVO" for casa in casas_abonado):
            return "El abonado esta inactivo"
        if any(casa.tiene_plan_activo for casa in casas_abonado):
            return "Ya tiene un plan activo"
        if all(casa.estado_administrativo != "OPERATIVA" for casa in casas_abonado):
            return "Las casas no estan operativas"
        return "No tiene casas cortadas aptas para plan"

    def _evaluar_formulario(
        self,
        formulario: FormularioPlanPago,
    ) -> _EvaluacionPlanPago | ResultadoGestionPlanesPago:
        if formulario.casa_id is None or formulario.casa_id <= 0:
            return ResultadoGestionPlanesPago(False, "Selecciona la casa asociada al plan.", "VALIDACION")
        if formulario.prima_centavos <= 0:
            return ResultadoGestionPlanesPago(False, "La prima inicial del plan debe ser mayor a cero.", "VALIDACION")
        if formulario.cantidad_cuotas <= 0:
            return ResultadoGestionPlanesPago(False, "Indica la cantidad de cuotas.", "VALIDACION")

        opciones_casa = {opcion.casa_id: opcion for opcion in self.listar_casas_disponibles()}
        casa = opciones_casa.get(formulario.casa_id)
        if casa is None:
            return ResultadoGestionPlanesPago(False, "La casa seleccionada ya no esta disponible.", "VALIDACION")
        if casa.abonado_id <= 0:
            return ResultadoGestionPlanesPago(False, "La casa no tiene un abonado actual valido.", "VALIDACION")

        plan_actual = None
        es_creacion = formulario.identificador is None
        if not es_creacion:
            plan_actual = self.obtener_por_id(formulario.identificador or 0)
            if plan_actual is None:
                return ResultadoGestionPlanesPago(False, "El plan que intentas actualizar ya no existe.", "NO_ENCONTRADO")
            if not self._solo_actualiza_observaciones(formulario, plan_actual):
                return ResultadoGestionPlanesPago(
                    False,
                    "En esta fase solo puedes actualizar las observaciones del plan.",
                    "VALIDACION",
                )

        tipo_plan = self._resolver_tipo_plan(casa)
        if formulario.tipo_plan not in TIPOS_PLAN_VALIDOS or formulario.tipo_plan != tipo_plan:
            return ResultadoGestionPlanesPago(
                False,
                f"La casa seleccionada debe registrarse como {tipo_plan.lower()} segun su antecedente de servicio.",
                "VALIDACION",
            )
        if formulario.concepto_financiado not in TIPOS_PLAN_VALIDOS or formulario.concepto_financiado != tipo_plan:
            return ResultadoGestionPlanesPago(
                False,
                "El concepto financiado debe coincidir con el tipo de activacion del plan.",
                "VALIDACION",
            )
        if formulario.estado not in ESTADOS_PLAN_VALIDOS:
            return ResultadoGestionPlanesPago(False, "El estado del plan no es valido.", "VALIDACION")

        fecha_activacion = date.today()
        metodo_nombre = "No aplica"
        referencia = ""
        deuda_financiada = plan_actual.deuda_financiada_centavos if plan_actual is not None else 0
        monto_activacion = plan_actual.monto_activacion_centavos if plan_actual is not None else 0
        cargos_vinculados: tuple[int, ...] = ()

        if es_creacion:
            if not formulario.fecha_activacion.strip():
                return ResultadoGestionPlanesPago(False, "Indica la fecha de activacion del servicio.", "VALIDACION")
            try:
                fecha_activacion = date.fromisoformat(formulario.fecha_activacion.strip())
            except ValueError:
                return ResultadoGestionPlanesPago(False, "La fecha de activacion no es valida.", "VALIDACION")
            if formulario.monto_activacion_centavos <= 0:
                return ResultadoGestionPlanesPago(False, "Indica el monto de activacion a financiar.", "VALIDACION")
            if not self._es_casa_elegible_nuevo_plan(casa):
                return ResultadoGestionPlanesPago(
                    False,
                    "La casa seleccionada ya no cumple las reglas operativas para crear un plan de activacion.",
                    "VALIDACION",
                )
            metodo = self._repositorio_planes_pago.obtener_metodo_pago(formulario.metodo_pago_id or 0)
            if metodo is None:
                return ResultadoGestionPlanesPago(False, "Selecciona un metodo de pago activo para la prima.", "VALIDACION")
            referencia = formulario.referencia_pago.strip()
            if metodo.requiere_referencia and not referencia:
                return ResultadoGestionPlanesPago(False, "Este metodo de pago requiere una referencia.", "VALIDACION")
            metodo_nombre = metodo.nombre
            deuda_financiada = max(casa.deuda_total_centavos, 0)
            monto_activacion = formulario.monto_activacion_centavos
            cargos_vinculados = self._repositorio_planes_pago.obtener_cargos_vinculables(
                casa_id=formulario.casa_id,
                concepto_financiado=formulario.concepto_financiado,
            )

        monto_total = deuda_financiada + monto_activacion
        saldo_financiado = monto_total - formulario.prima_centavos
        if saldo_financiado <= 0:
            return ResultadoGestionPlanesPago(
                False,
                "La prima no puede cubrir la totalidad del monto financiado. Deja saldo para cuotas.",
                "VALIDACION",
            )
        cuota_regular = self.calcular_cuota_regular(saldo_financiado, formulario.cantidad_cuotas)
        cuotas = self._construir_cuotas(saldo_financiado, cuota_regular, formulario.cantidad_cuotas)
        if cuotas is None:
            return ResultadoGestionPlanesPago(
                False,
                "La cuota y la cantidad de cuotas no cubren el saldo financiado indicado.",
                "VALIDACION",
            )
        fechas_cuotas = self._construir_fechas_cuotas(fecha_activacion, len(cuotas))
        return _EvaluacionPlanPago(
            casa=casa,
            plan_actual=plan_actual,
            metodo_nombre=metodo_nombre,
            referencia_pago=referencia,
            fecha_activacion=fecha_activacion,
            deuda_financiada_centavos=deuda_financiada,
            monto_activacion_centavos=monto_activacion,
            monto_total_centavos=monto_total,
            saldo_financiado_centavos=saldo_financiado,
            cuota_regular_centavos=cuota_regular,
            cuotas=cuotas,
            fechas_cuotas=fechas_cuotas,
            cargos_vinculados=cargos_vinculados,
            es_creacion=es_creacion,
        )

    @staticmethod
    def _solo_actualiza_observaciones(
        formulario: FormularioPlanPago,
        plan_actual: PlanPago,
    ) -> bool:
        return (
            formulario.casa_id == plan_actual.casa_id
            and formulario.tipo_plan == plan_actual.tipo_plan
            and formulario.concepto_financiado == plan_actual.concepto_financiado
            and formulario.prima_centavos == plan_actual.prima_centavos
            and formulario.saldo_financiado_centavos == plan_actual.saldo_financiado_centavos
            and formulario.cuota_regular_centavos == plan_actual.cuota_regular_centavos
            and formulario.cantidad_cuotas == plan_actual.cantidad_cuotas
            and formulario.estado == plan_actual.estado
            and formulario.monto_activacion_centavos == plan_actual.monto_activacion_centavos
        )
