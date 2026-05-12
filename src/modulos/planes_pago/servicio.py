"""Servicios del modulo de planes de pago."""

from __future__ import annotations

import csv
from calendar import monthrange
from datetime import date, datetime

from modulos.planes_pago.entidades import (
    DetallePlanPago,
    ESTADOS_PLAN_VALIDOS,
    FILTRO_PLANES_TODOS,
    FormularioPlanPago,
    OpcionCasaPlanPago,
    PaginaPlanesPago,
    PlanPago,
    ResumenPlanesPago,
    ResultadoGestionPlanesPago,
    TIPOS_PLAN_VALIDOS,
)
from modulos.planes_pago.repositorio import RepositorioPlanesPago


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

    def guardar(
        self,
        formulario: FormularioPlanPago,
        actor_id: int | None = None,
    ) -> ResultadoGestionPlanesPago:
        if formulario.casa_id is None or formulario.casa_id <= 0:
            return ResultadoGestionPlanesPago(False, "Selecciona la casa asociada al plan.", "VALIDACION")
        if formulario.tipo_plan not in TIPOS_PLAN_VALIDOS:
            return ResultadoGestionPlanesPago(False, "El tipo de plan no es valido.", "VALIDACION")
        if formulario.concepto_financiado not in TIPOS_PLAN_VALIDOS:
            return ResultadoGestionPlanesPago(False, "El concepto financiado no es valido.", "VALIDACION")
        if formulario.estado not in ESTADOS_PLAN_VALIDOS:
            return ResultadoGestionPlanesPago(False, "El estado del plan no es valido.", "VALIDACION")
        if formulario.prima_centavos < 0:
            return ResultadoGestionPlanesPago(False, "La prima no puede ser negativa.", "VALIDACION")
        if formulario.saldo_financiado_centavos <= 0:
            return ResultadoGestionPlanesPago(False, "Indica el saldo financiado del plan.", "VALIDACION")
        if formulario.cuota_regular_centavos <= 0:
            return ResultadoGestionPlanesPago(False, "Indica el valor de la cuota.", "VALIDACION")
        if formulario.cantidad_cuotas <= 0:
            return ResultadoGestionPlanesPago(False, "Indica la cantidad de cuotas.", "VALIDACION")

        opciones_casa = {opcion.casa_id: opcion for opcion in self.listar_casas_disponibles()}
        casa = opciones_casa.get(formulario.casa_id)
        if casa is None:
            return ResultadoGestionPlanesPago(False, "La casa seleccionada ya no esta disponible.", "VALIDACION")
        if casa.abonado_id <= 0:
            return ResultadoGestionPlanesPago(False, "La casa no tiene un abonado actual valido.", "VALIDACION")

        plan_actual = None
        if formulario.identificador is not None:
            plan_actual = self.obtener_por_id(formulario.identificador)
            if plan_actual is None:
                return ResultadoGestionPlanesPago(False, "El plan que intentas actualizar ya no existe.", "NO_ENCONTRADO")
            cuotas_pagadas = self._repositorio_planes_pago.contar_cuotas_pagadas(formulario.identificador)
            if cuotas_pagadas > 0:
                cambios_estructurales = (
                    plan_actual.casa_id != formulario.casa_id
                    or plan_actual.prima_centavos != formulario.prima_centavos
                    or plan_actual.saldo_financiado_centavos != formulario.saldo_financiado_centavos
                    or plan_actual.cuota_regular_centavos != formulario.cuota_regular_centavos
                    or plan_actual.cantidad_cuotas != formulario.cantidad_cuotas
                )
                if cambios_estructurales:
                    return ResultadoGestionPlanesPago(
                        False,
                        "No puedes cambiar casa, montos o cuotas de un plan que ya tiene cuotas pagadas.",
                        "VALIDACION",
                    )

        monto_total = formulario.prima_centavos + formulario.saldo_financiado_centavos
        cuotas = self._construir_cuotas(
            total=formulario.saldo_financiado_centavos,
            cuota_regular=formulario.cuota_regular_centavos,
            cantidad=formulario.cantidad_cuotas,
        )
        if cuotas is None:
            return ResultadoGestionPlanesPago(
                False,
                "La cuota y la cantidad de cuotas no cubren el saldo financiado indicado.",
                "VALIDACION",
            )

        fechas = self._construir_fechas_cuotas(len(cuotas))
        cargos_vinculados = self._repositorio_planes_pago.obtener_cargos_vinculables(
            casa_id=formulario.casa_id,
            concepto_financiado=formulario.concepto_financiado,
        )
        plan = PlanPago(
            identificador=formulario.identificador,
            casa_id=casa.casa_id,
            casa_codigo=casa.casa_codigo,
            abonado_id=casa.abonado_id,
            abonado_nombre=casa.abonado_nombre,
            abonado_dni=casa.abonado_dni,
            barrio_nombre=casa.barrio_nombre,
            tipo_plan=formulario.tipo_plan,
            concepto_financiado=formulario.concepto_financiado,
            prima_centavos=formulario.prima_centavos,
            saldo_financiado_centavos=formulario.saldo_financiado_centavos,
            monto_total_centavos=monto_total,
            cuota_regular_centavos=formulario.cuota_regular_centavos,
            cantidad_cuotas=formulario.cantidad_cuotas,
            estado=formulario.estado,
            observaciones=formulario.observaciones.strip(),
        )
        try:
            self._repositorio_planes_pago.guardar_plan(
                plan=plan,
                cuotas=list(zip(fechas, cuotas)),
                cargos_vinculados=cargos_vinculados,
                actor_id=actor_id,
            )
        except Exception:
            return ResultadoGestionPlanesPago(
                False,
                "No fue posible guardar el plan de pago. Verifica los datos asociados.",
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
                        ]
                    )
        except OSError:
            return ResultadoGestionPlanesPago(False, "No fue posible exportar el listado de planes.", "ERROR_EXPORTACION")
        return ResultadoGestionPlanesPago(True, "Listado exportado correctamente.", "OK")

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

    def _construir_fechas_cuotas(self, cantidad: int) -> list[str]:
        hoy = date.today()
        fechas: list[str] = []
        for desplazamiento in range(cantidad):
            mes = hoy.month + desplazamiento
            anio = hoy.year + ((mes - 1) // 12)
            mes_real = ((mes - 1) % 12) + 1
            dia = min(hoy.day, monthrange(anio, mes_real)[1])
            fechas.append(date(anio, mes_real, dia).isoformat())
        return fechas
