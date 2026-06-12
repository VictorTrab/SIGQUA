"""Servicios del modulo de abonados."""

from __future__ import annotations

import csv
from datetime import datetime
from typing import Protocol

from comun.pagos_adelantados import (
    EstadoFinancieroCasaAbonado,
    LectorPagosAdelantados,
)
from modulos.abonados.entidades import (
    Abonado,
    FILTRO_ABONADOS_TODOS,
    OpcionBarrio,
    PaginaAbonados,
    ResumenAbonados,
    ResultadoGestionAbonados,
)
from modulos.abonados.repositorio import RepositorioAbonados


class RepositorioCasasRelacionado(Protocol):
    """Contrato minimo para integrar el estado de casas con abonados."""

    def suspender_casas_por_abonado_inactivo(
        self,
        abonado_id: int,
        actor_id: int | None = None,
    ) -> int:
        """Suspende casas operativas asociadas a un abonado inactivado."""

    def reactivar_casas_por_abonado_activado(
        self,
        abonado_id: int,
        actor_id: int | None = None,
    ) -> int:
        """Reactiva casas suspendidas por abonado inactivo una vez restaurado."""


class ServicioAbonados:
    """Orquesta reglas de negocio y presentacion operativa para abonados."""

    TAMANO_PAGINA = 10

    def __init__(
        self,
        repositorio_abonados: RepositorioAbonados,
        repositorio_casas_relacionado: RepositorioCasasRelacionado | None = None,
        lector_adelantos: LectorPagosAdelantados | None = None,
    ) -> None:
        self._repositorio_abonados = repositorio_abonados
        self._repositorio_casas_relacionado = repositorio_casas_relacionado
        self._lector_adelantos = lector_adelantos

    def obtener_resumen(self) -> ResumenAbonados:
        return self._repositorio_abonados.obtener_resumen()

    def listar(
        self,
        filtro: str = "",
        filtro_rapido: str = FILTRO_ABONADOS_TODOS,
        pagina: int = 1,
    ) -> PaginaAbonados:
        pagina = max(1, pagina)
        total_registros = self._repositorio_abonados.contar(filtro, filtro_rapido)
        total_paginas = max(1, (total_registros + self.TAMANO_PAGINA - 1) // self.TAMANO_PAGINA)
        pagina = min(pagina, total_paginas)
        desplazamiento = (pagina - 1) * self.TAMANO_PAGINA
        items = self._repositorio_abonados.listar(
            filtro=filtro,
            filtro_rapido=filtro_rapido,
            limite=self.TAMANO_PAGINA,
            desplazamiento=desplazamiento,
        )
        return PaginaAbonados(
            items=items,
            pagina_actual=pagina,
            tamano_pagina=self.TAMANO_PAGINA,
            total_registros=total_registros,
        )

    def obtener_por_id(self, abonado_id: int) -> Abonado | None:
        return self._repositorio_abonados.obtener_por_id(abonado_id)

    def listar_estados_casas(
        self,
        abonado_id: int,
    ) -> tuple[EstadoFinancieroCasaAbonado, ...]:
        if self._lector_adelantos is None:
            return ()
        return self._lector_adelantos.listar_estados_casas_abonado(abonado_id)

    def listar_barrios_disponibles(self) -> list[OpcionBarrio]:
        return self._repositorio_abonados.listar_barrios_disponibles()

    def guardar(
        self,
        identificador: int | None,
        dni: str,
        nombre_completo: str,
        telefono: str,
        barrio_id: int | None,
        direccion_referencia: str,
        observaciones: str,
        estado: str,
    ) -> ResultadoGestionAbonados:
        dni = dni.strip()
        nombre_completo = nombre_completo.strip()
        telefono = telefono.strip()
        direccion_referencia = direccion_referencia.strip()
        observaciones = observaciones.strip()
        estado = estado.strip().upper() or "ACTIVO"

        if len(dni) < 8:
            return ResultadoGestionAbonados(
                False,
                "El DNI debe tener al menos 8 caracteres.",
                "VALIDACION",
            )
        if not nombre_completo:
            return ResultadoGestionAbonados(
                False,
                "Indica el nombre completo del abonado.",
                "VALIDACION",
            )
        if barrio_id is None or barrio_id <= 0:
            return ResultadoGestionAbonados(
                False,
                "Selecciona un barrio valido para el abonado.",
                "VALIDACION",
            )
        if estado not in {"ACTIVO", "INACTIVO"}:
            return ResultadoGestionAbonados(
                False,
                "El estado del abonado no es valido.",
                "VALIDACION",
            )

        try:
            self._repositorio_abonados.guardar(
                Abonado(
                    identificador=identificador,
                    dni=dni,
                    nombre_completo=nombre_completo,
                    telefono=telefono,
                    barrio_id=barrio_id,
                    direccion_referencia=direccion_referencia,
                    observaciones=observaciones,
                    estado=estado,
                )
            )
        except Exception:
            return ResultadoGestionAbonados(
                False,
                "No fue posible guardar el abonado. Verifica que el DNI no este duplicado.",
                "ERROR_SQLITE",
            )

        mensaje = (
            "Abonado actualizado correctamente."
            if identificador
            else "Abonado creado correctamente."
        )
        return ResultadoGestionAbonados(True, mensaje, "OK")

    def cambiar_estado(
        self,
        abonado_id: int,
        estado_actual: str,
        actor_id: int | None = None,
    ) -> ResultadoGestionAbonados:
        nuevo_estado = "INACTIVO" if estado_actual == "ACTIVO" else "ACTIVO"
        try:
            self._repositorio_abonados.cambiar_estado(abonado_id, nuevo_estado)
            mensaje = f"Abonado marcado como {nuevo_estado.lower()}."
            if nuevo_estado == "INACTIVO" and self._repositorio_casas_relacionado is not None:
                total_suspendidas = self._repositorio_casas_relacionado.suspender_casas_por_abonado_inactivo(
                    abonado_id=abonado_id,
                    actor_id=actor_id,
                )
                if total_suspendidas > 0:
                    mensaje = (
                        f"Abonado marcado como inactivo. {total_suspendidas} casa(s) asociada(s) "
                        "pasaron a estado suspendido."
                    )
            elif nuevo_estado == "ACTIVO" and self._repositorio_casas_relacionado is not None:
                total_reactivadas = self._repositorio_casas_relacionado.reactivar_casas_por_abonado_activado(
                    abonado_id=abonado_id,
                    actor_id=actor_id,
                )
                if total_reactivadas > 0:
                    mensaje = (
                        f"Abonado marcado como activo. {total_reactivadas} casa(s) suspendida(s) "
                        "por esta causa volvieron a operativa."
                    )
        except Exception:
            return ResultadoGestionAbonados(
                False,
                "No fue posible actualizar el estado del abonado. Verifica los datos relacionados y la base de datos.",
                "ERROR_SQLITE",
            )
        return ResultadoGestionAbonados(True, mensaje, "OK")

    def exportar_csv(
        self,
        ruta_destino: str,
        filtro: str = "",
        filtro_rapido: str = FILTRO_ABONADOS_TODOS,
    ) -> ResultadoGestionAbonados:
        abonados = self._repositorio_abonados.listar(
            filtro=filtro,
            filtro_rapido=filtro_rapido,
            limite=None,
            desplazamiento=0,
        )
        try:
            with open(ruta_destino, "w", newline="", encoding="utf-8") as archivo_csv:
                escritor = csv.writer(archivo_csv)
                escritor.writerow(
                    [
                        "DNI",
                        "Abonado",
                        "Telefono",
                        "Barrio",
                        "Casas",
                        "Meses en mora",
                        "Estado",
                        "Creado",
                        "Ultima actualizacion",
                        "Tiene plan activo",
                        "Deuda pendiente",
                    ]
                )
                for abonado in abonados:
                    escritor.writerow(
                        [
                            abonado.dni,
                            abonado.nombre_completo,
                            abonado.telefono,
                            abonado.barrio_nombre,
                            abonado.total_casas,
                            abonado.meses_en_mora,
                            abonado.estado,
                            self.formatear_fecha_hora(abonado.creado_en),
                            self.formatear_fecha_hora(abonado.actualizado_en),
                            "Si" if abonado.tiene_plan_activo else "No",
                            self.formatear_moneda(abonado.deuda_total_centavos),
                        ]
                    )
        except OSError:
            return ResultadoGestionAbonados(
                False,
                "No fue posible generar el archivo de exportacion.",
                "ERROR_EXPORTACION",
            )
        return ResultadoGestionAbonados(True, "Listado exportado correctamente.", "OK")

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
    def formatear_moneda(valor_centavos: int) -> str:
        return f"L {valor_centavos / 100:,.2f}"
