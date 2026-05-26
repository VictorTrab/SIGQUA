"""Servicios del modulo de historial de pagos."""

from __future__ import annotations

from datetime import datetime

from comun.configuracion.gestor_rutas import GestorRutas
from modulos.comprobantes import COPIA_AMBAS, RepositorioComprobantesSQLite, ServicioComprobantes
from modulos.historial_pagos.entidades import (
    DetalleHistorialPago,
    FILTRO_HISTORIAL_TODOS,
    FILTRO_METODO_TODOS,
    FiltroHistorialPagos,
    PaginaHistorialPagos,
    ResumenHistorialPagos,
    ResultadoHistorialPagos,
)
from modulos.historial_pagos.repositorio import RepositorioHistorialPagos


class ServicioHistorialPagos:
    """Orquesta filtros, detalle y reimpresion del historial."""

    TAMANO_PAGINA = 10

    def __init__(
        self,
        repositorio_historial: RepositorioHistorialPagos,
        gestor_rutas: GestorRutas | None = None,
        servicio_comprobantes: ServicioComprobantes | None = None,
    ) -> None:
        self._repositorio_historial = repositorio_historial
        self._gestor_rutas = gestor_rutas or GestorRutas()
        self._servicio_comprobantes = servicio_comprobantes or self._crear_servicio_comprobantes_predeterminado()

    def obtener_resumen(self, filtros: FiltroHistorialPagos | None = None) -> ResumenHistorialPagos:
        filtros = filtros or FiltroHistorialPagos()
        self._validar_rango(filtros.fecha_desde, filtros.fecha_hasta)
        return self._repositorio_historial.obtener_resumen_historial(filtros)

    def listar(
        self,
        filtros: FiltroHistorialPagos | None = None,
        pagina: int = 1,
    ) -> PaginaHistorialPagos:
        filtros = filtros or FiltroHistorialPagos()
        self._validar_rango(filtros.fecha_desde, filtros.fecha_hasta)
        pagina = max(1, pagina)
        total_registros = self._repositorio_historial.contar_historial(filtros)
        total_paginas = max(1, (total_registros + self.TAMANO_PAGINA - 1) // self.TAMANO_PAGINA)
        pagina = min(pagina, total_paginas)
        desplazamiento = (pagina - 1) * self.TAMANO_PAGINA
        items = self._repositorio_historial.listar_historial(
            filtros=filtros,
            limite=self.TAMANO_PAGINA,
            desplazamiento=desplazamiento,
        )
        return PaginaHistorialPagos(
            items=items,
            pagina_actual=pagina,
            tamano_pagina=self.TAMANO_PAGINA,
            total_registros=total_registros,
        )

    def obtener_detalle(self, pago_id: int) -> DetalleHistorialPago | None:
        return self._repositorio_historial.obtener_detalle_pago(pago_id)

    def reimprimir_comprobante(
        self,
        pago_id: int,
        tipo_copia: str = COPIA_AMBAS,
        actor_id: int | None = None,
    ) -> ResultadoHistorialPagos:
        comprobante = self._repositorio_historial.obtener_comprobante_para_reimpresion(pago_id)
        if comprobante is None:
            return ResultadoHistorialPagos(
                False,
                "No fue posible recuperar el comprobante seleccionado.",
                "NO_ENCONTRADO",
            )
        if self._servicio_comprobantes is None:
            return ResultadoHistorialPagos(
                False,
                "El servicio de impresion termica no esta disponible.",
                "ERROR_CONFIG",
            )
        resultado = self._servicio_comprobantes.imprimir_comprobante(
            pago_id,
            actor_id=actor_id,
            tipo_copia=tipo_copia,
            es_reimpresion=True,
        )
        return ResultadoHistorialPagos(resultado.exito, resultado.mensaje, resultado.codigo)

    def reimprimir_copia(self, pago_id: int) -> ResultadoHistorialPagos:
        return self.reimprimir_comprobante(pago_id, COPIA_AMBAS)

    @staticmethod
    def formatear_moneda(valor_centavos: int) -> str:
        return f"L {valor_centavos / 100:,.2f}"

    @staticmethod
    def formatear_fecha_hora(valor: str) -> str:
        if not valor:
            return "Sin registro"
        try:
            fecha = datetime.fromisoformat(valor)
        except ValueError:
            return valor
        return fecha.strftime("%d/%m/%Y %I:%M %p")

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

    @staticmethod
    def etiqueta_tipo_pago(tipo_pago: str) -> str:
        etiquetas = {
            "MENSUALIDAD": "Mensualidad",
            "PLAN_PAGO": "Plan",
            "CONEXION": "Conexion",
            "RECONEXION": "Reconexion",
        }
        return etiquetas.get(tipo_pago, tipo_pago)

    @staticmethod
    def filtro_inicial() -> FiltroHistorialPagos:
        return FiltroHistorialPagos(
            texto="",
            tipo_pago=FILTRO_HISTORIAL_TODOS,
            metodo_pago=FILTRO_METODO_TODOS,
            fecha_desde="",
            fecha_hasta="",
        )

    @staticmethod
    def _validar_rango(fecha_desde: str, fecha_hasta: str) -> None:
        if fecha_desde:
            datetime.strptime(fecha_desde, "%Y-%m-%d")
        if fecha_hasta:
            datetime.strptime(fecha_hasta, "%Y-%m-%d")
        if fecha_desde and fecha_hasta and fecha_desde > fecha_hasta:
            raise ValueError("La fecha inicial no puede ser mayor que la fecha final.")

    def _crear_servicio_comprobantes_predeterminado(self) -> ServicioComprobantes | None:
        gestor_base_datos = getattr(self._repositorio_historial, "_gestor_base_datos", None)
        if gestor_base_datos is None:
            return None
        return ServicioComprobantes(RepositorioComprobantesSQLite(gestor_base_datos))
