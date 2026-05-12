"""Servicios del modulo de casas."""

from __future__ import annotations

import csv
from datetime import datetime

from modulos.casas.entidades import (
    Casa,
    DetalleCasa,
    FILTRO_CASAS_TODAS,
    OpcionAbonado,
    OpcionBarrio,
    PaginaCasas,
    ResumenCasas,
    ResultadoGestionCasas,
)
from modulos.casas.repositorio import RepositorioCasas


class ServicioCasas:
    """Orquesta reglas de negocio y presentacion operativa para casas."""

    TAMANO_PAGINA = 10

    def __init__(self, repositorio_casas: RepositorioCasas) -> None:
        self._repositorio_casas = repositorio_casas

    def obtener_resumen(self) -> ResumenCasas:
        return self._repositorio_casas.obtener_resumen()

    def listar(
        self,
        filtro: str = "",
        filtro_rapido: str = FILTRO_CASAS_TODAS,
        pagina: int = 1,
    ) -> PaginaCasas:
        pagina = max(1, pagina)
        total_registros = self._repositorio_casas.contar(filtro, filtro_rapido)
        total_paginas = max(1, (total_registros + self.TAMANO_PAGINA - 1) // self.TAMANO_PAGINA)
        pagina = min(pagina, total_paginas)
        desplazamiento = (pagina - 1) * self.TAMANO_PAGINA
        items = self._repositorio_casas.listar(
            filtro=filtro,
            filtro_rapido=filtro_rapido,
            limite=self.TAMANO_PAGINA,
            desplazamiento=desplazamiento,
        )
        return PaginaCasas(
            items=items,
            pagina_actual=pagina,
            tamano_pagina=self.TAMANO_PAGINA,
            total_registros=total_registros,
        )

    def obtener_por_id(self, casa_id: int) -> Casa | None:
        return self._repositorio_casas.obtener_por_id(casa_id)

    def obtener_detalle(self, casa_id: int) -> DetalleCasa | None:
        return self._repositorio_casas.obtener_detalle(casa_id)

    def listar_abonados_disponibles(self) -> list[OpcionAbonado]:
        return self._repositorio_casas.listar_abonados_disponibles()

    def listar_barrios_disponibles(self) -> list[OpcionBarrio]:
        return self._repositorio_casas.listar_barrios_disponibles()

    def listar_historial_propietarios(self, casa_id: int):
        return self._repositorio_casas.listar_historial_propietarios(casa_id)

    def guardar(
        self,
        identificador: int | None,
        abonado_id: int | None,
        barrio_id: int | None,
        direccion_referencia: str,
        observaciones: str,
        estado_servicio: str,
    ) -> ResultadoGestionCasas:
        estado_servicio = estado_servicio.strip().upper() or "ACTIVO"
        direccion_referencia = direccion_referencia.strip()
        observaciones = observaciones.strip()

        if abonado_id is None or abonado_id <= 0:
            return ResultadoGestionCasas(
                False,
                "Selecciona un abonado valido para la casa.",
                "VALIDACION",
            )
        if barrio_id is None or barrio_id <= 0:
            return ResultadoGestionCasas(
                False,
                "Selecciona un barrio valido para la casa.",
                "VALIDACION",
            )
        casa_actual = None
        if identificador is not None:
            casa_actual = self._repositorio_casas.obtener_por_id(identificador)
            if casa_actual is None:
                return ResultadoGestionCasas(
                    False,
                    "La casa que intentas actualizar ya no existe.",
                    "CASA_NO_ENCONTRADA",
                )
        abonados = {opcion.identificador: opcion for opcion in self.listar_abonados_disponibles()}
        abonado = abonados.get(abonado_id)
        if abonado is None:
            return ResultadoGestionCasas(
                False,
                "El abonado seleccionado no existe o ya no esta disponible.",
                "VALIDACION",
            )
        mismo_abonado_actual = (
            casa_actual is not None and casa_actual.abonado_id is not None and casa_actual.abonado_id == abonado_id
        )
        if abonado.estado != "ACTIVO" and not mismo_abonado_actual:
            return ResultadoGestionCasas(
                False,
                "Solo puedes asignar casas a abonados activos.",
                "VALIDACION",
            )
        if estado_servicio not in {"ACTIVO", "CORTADO", "SUSPENDIDO", "INACTIVO"}:
            return ResultadoGestionCasas(
                False,
                "El estado de servicio de la casa no es valido.",
                "VALIDACION",
            )

        try:
            self._repositorio_casas.guardar(
                Casa(
                    identificador=identificador,
                    abonado_id=abonado_id,
                    barrio_id=barrio_id,
                    direccion_referencia=direccion_referencia,
                    observaciones=observaciones,
                    estado_servicio=estado_servicio,
                )
            )
        except Exception:
            return ResultadoGestionCasas(
                False,
                "No fue posible guardar la casa. Revisa los datos asociados.",
                "ERROR_SQLITE",
            )

        mensaje = "Casa actualizada correctamente." if identificador else "Casa creada correctamente."
        return ResultadoGestionCasas(True, mensaje, "OK")

    def cambiar_estado(self, casa_id: int, estado_actual: str) -> ResultadoGestionCasas:
        transiciones = {
            "ACTIVO": "SUSPENDIDO",
            "SUSPENDIDO": "ACTIVO",
            "CORTADO": "ACTIVO",
            "INACTIVO": "ACTIVO",
        }
        nuevo_estado = transiciones.get(estado_actual, "ACTIVO")
        try:
            self._repositorio_casas.cambiar_estado(casa_id, nuevo_estado)
        except Exception:
            return ResultadoGestionCasas(
                False,
                "No fue posible actualizar el estado de la casa. Verifica los datos asociados y la base de datos.",
                "ERROR_SQLITE",
            )
        return ResultadoGestionCasas(
            True,
            f"Casa marcada como {nuevo_estado.lower()}.",
            "OK",
        )

    def cambiar_dueno(
        self,
        casa_id: int,
        nuevo_abonado_id: int | None,
        motivo: str,
        actor_id: int | None,
    ) -> ResultadoGestionCasas:
        motivo = motivo.strip()
        if nuevo_abonado_id is None or nuevo_abonado_id <= 0:
            return ResultadoGestionCasas(
                False,
                "Selecciona el nuevo abonado para completar el cambio.",
                "VALIDACION",
            )
        if not motivo:
            return ResultadoGestionCasas(
                False,
                "Indica el motivo u observacion del cambio de propietario.",
                "VALIDACION",
            )

        abonados = {opcion.identificador: opcion for opcion in self.listar_abonados_disponibles()}
        abonado_destino = abonados.get(nuevo_abonado_id)
        if abonado_destino is None:
            return ResultadoGestionCasas(
                False,
                "El abonado seleccionado ya no esta disponible.",
                "ABONADO_NO_ENCONTRADO",
            )
        if abonado_destino.estado != "ACTIVO":
            return ResultadoGestionCasas(
                False,
                "Solo puedes transferir la casa a un abonado activo.",
                "VALIDACION",
            )

        try:
            self._repositorio_casas.cambiar_dueno(
                casa_id=casa_id,
                nuevo_abonado_id=nuevo_abonado_id,
                motivo=motivo,
                actor_id=actor_id,
            )
        except ValueError as error:
            return ResultadoGestionCasas(False, str(error), "VALIDACION")
        except Exception:
            return ResultadoGestionCasas(
                False,
                "No fue posible completar el cambio de propietario.",
                "ERROR_SQLITE",
            )
        return ResultadoGestionCasas(
            True,
            "Cambio de propietario aplicado correctamente. La deuda pendiente y el plan activo fueron migrados.",
            "OK",
        )

    def exportar_csv(
        self,
        ruta_destino: str,
        filtro: str = "",
        filtro_rapido: str = FILTRO_CASAS_TODAS,
    ) -> ResultadoGestionCasas:
        casas = self._repositorio_casas.listar(
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
                        "Codigo",
                        "Abonado actual",
                        "DNI",
                        "Barrio",
                        "Referencia",
                        "Meses pendientes",
                        "Meses en mora",
                        "Estado",
                        "Plan activo",
                        "Deuda pendiente",
                    ]
                )
                for casa in casas:
                    escritor.writerow(
                        [
                            casa.codigo,
                            casa.resumen_propietario,
                            casa.abonado_dni,
                            casa.barrio_nombre,
                            casa.direccion_referencia,
                            casa.meses_pendientes,
                            casa.meses_en_mora,
                            casa.estado_servicio,
                            "Si" if casa.tiene_plan_activo else "No",
                            self.formatear_moneda(casa.deuda_total_centavos),
                        ]
                    )
        except OSError:
            return ResultadoGestionCasas(
                False,
                "No fue posible generar el archivo de exportacion.",
                "ERROR_EXPORTACION",
            )
        return ResultadoGestionCasas(True, "Listado exportado correctamente.", "OK")

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
    def formatear_moneda(valor_centavos: int) -> str:
        return f"L {valor_centavos / 100:,.2f}"
