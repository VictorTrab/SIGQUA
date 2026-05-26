"""Servicio interno para impresion y reimpresion de comprobantes."""

from __future__ import annotations

from comun.impresion_termica import (
    ConfiguracionImpresoraTermica,
    RenderizadorTicketEscpos,
    TransporteWindowsRawEscpos,
)
from modulos.comprobantes.entidades import (
    COPIA_AMBAS,
    COPIA_JUNTA,
    COPIA_ORIGINAL,
    ESTADO_FALLIDO,
    ESTADO_IMPRESO,
    ResultadoComprobante,
)
from modulos.comprobantes.repositorio import RepositorioComprobantes


class ServicioComprobantes:
    """Orquesta tickets ESC/POS desde comprobantes persistidos."""

    COPIAS_VALIDAS = {COPIA_ORIGINAL, COPIA_JUNTA, COPIA_AMBAS}

    def __init__(
        self,
        repositorio_comprobantes: RepositorioComprobantes,
        renderizador: RenderizadorTicketEscpos | None = None,
        transporte: TransporteWindowsRawEscpos | None = None,
    ) -> None:
        self._repositorio = repositorio_comprobantes
        self._renderizador = renderizador or RenderizadorTicketEscpos()
        self._transporte = transporte or TransporteWindowsRawEscpos()

    def imprimir_comprobante(
        self,
        pago_id: int,
        *,
        actor_id: int | None,
        tipo_copia: str = COPIA_AMBAS,
        es_reimpresion: bool = False,
    ) -> ResultadoComprobante:
        tipo_copia = tipo_copia if tipo_copia in self.COPIAS_VALIDAS else COPIA_AMBAS
        ticket = self._repositorio.obtener_ticket_por_pago(pago_id)
        if ticket is None:
            return ResultadoComprobante(
                False,
                "No fue posible recuperar los datos del comprobante para impresion.",
                "NO_ENCONTRADO",
            )
        configuracion = self._repositorio.obtener_configuracion_termica()
        if not configuracion.nombre_impresora.strip():
            mensaje = "Pago registrado; no hay impresora termica configurada para imprimir el comprobante."
            self._registrar(ticket.comprobante_id, tipo_copia, es_reimpresion, ESTADO_FALLIDO, mensaje, actor_id)
            return ResultadoComprobante(False, mensaje, "SIN_IMPRESORA")

        resultado = self._enviar_ticket(ticket, configuracion, tipo_copia, es_reimpresion)
        estado = ESTADO_IMPRESO if resultado.exito else ESTADO_FALLIDO
        self._registrar(
            ticket.comprobante_id,
            tipo_copia,
            es_reimpresion,
            estado,
            "" if resultado.exito else resultado.mensaje,
            actor_id,
        )
        if resultado.exito:
            return ResultadoComprobante(True, f"Comprobante {ticket.numero_comprobante} enviado a impresion termica.", "OK")
        return ResultadoComprobante(False, resultado.mensaje, resultado.codigo)

    def imprimir_comprobantes(
        self,
        pagos_id: tuple[int, ...],
        *,
        actor_id: int | None,
    ) -> tuple[ResultadoComprobante, ...]:
        return tuple(
            self.imprimir_comprobante(pago_id, actor_id=actor_id, tipo_copia=COPIA_AMBAS)
            for pago_id in pagos_id
        )

    def contar_pendientes_impresion(self) -> int:
        return self._repositorio.contar_pendientes_impresion()

    def impresora_configurada(self) -> bool:
        return bool(self._repositorio.obtener_configuracion_termica().nombre_impresora.strip())

    def _enviar_ticket(
        self,
        ticket: object,
        configuracion: object,
        tipo_copia: str,
        es_reimpresion: bool,
    ) -> object:
        config = ConfiguracionImpresoraTermica(
            nombre_impresora=configuracion.nombre_impresora,
            ancho_papel_mm=configuracion.ancho_papel_mm,
            corte_automatico=configuracion.corte_automatico,
            codigo_pagina=configuracion.codigo_pagina,
        )
        datos = bytearray()
        copias = self._resolver_copias(tipo_copia)
        for copia in copias:
            datos.extend(
                self._renderizador.renderizar(
                    ticket,
                    config,
                    tipo_copia=copia,
                    es_reimpresion=es_reimpresion,
                )
            )
        return self._transporte.enviar(
            config.nombre_impresora,
            bytes(datos),
            f"SIGQUA {ticket.numero_comprobante}",
        )

    def _registrar(
        self,
        comprobante_id: int,
        tipo_copia: str,
        es_reimpresion: bool,
        estado: str,
        mensaje_error: str,
        actor_id: int | None,
    ) -> None:
        self._repositorio.registrar_intento_impresion(
            comprobante_id=comprobante_id,
            tipo_copia=tipo_copia,
            es_reimpresion=es_reimpresion,
            estado=estado,
            mensaje_error=mensaje_error,
            actor_id=actor_id,
        )

    @staticmethod
    def _resolver_copias(tipo_copia: str) -> tuple[str, ...]:
        if tipo_copia == COPIA_ORIGINAL:
            return ("ORIGINAL - ABONADO",)
        if tipo_copia == COPIA_JUNTA:
            return ("COPIA - JUNTA DE AGUA",)
        return ("ORIGINAL - ABONADO", "COPIA - JUNTA DE AGUA")
