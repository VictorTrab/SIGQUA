"""Servicios del modulo de casas."""

from __future__ import annotations

import csv
from datetime import datetime

from modulos.casas.entidades import (
    Casa,
    DetalleCasa,
    ESTADO_ADMINISTRATIVO_OPERATIVA,
    ESTADO_ADMINISTRATIVO_SUSPENDIDA,
    ESTADO_SERVICIO_ACTIVO,
    ESTADO_SERVICIO_CORTADO,
    ESTADO_SERVICIO_INACTIVO,
    ESTADOS_ADMINISTRATIVOS_VALIDOS,
    ESTADOS_SERVICIO_VALIDOS,
    FILTRO_CASAS_TODAS,
    MOTIVO_ESTADO_ADMINISTRATIVO_ABONADO_INACTIVO,
    MOTIVO_ESTADO_ADMINISTRATIVO_NINGUNO,
    MOTIVO_ESTADO_ADMINISTRATIVO_REVISION_ADMINISTRATIVA,
    MOTIVOS_ESTADO_ADMINISTRATIVO_VALIDOS,
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
        estado_administrativo: str,
        motivo_estado_administrativo: str,
        ha_tenido_servicio_activo: bool,
    ) -> ResultadoGestionCasas:
        estado_servicio = estado_servicio.strip().upper() or ESTADO_SERVICIO_ACTIVO
        estado_administrativo = estado_administrativo.strip().upper() or ESTADO_ADMINISTRATIVO_OPERATIVA
        motivo_estado_administrativo = (
            motivo_estado_administrativo.strip().upper() or MOTIVO_ESTADO_ADMINISTRATIVO_NINGUNO
        )
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
        if estado_servicio not in ESTADOS_SERVICIO_VALIDOS:
            return ResultadoGestionCasas(
                False,
                "El estado fisico del servicio no es valido.",
                "VALIDACION",
            )
        if estado_administrativo not in ESTADOS_ADMINISTRATIVOS_VALIDOS:
            return ResultadoGestionCasas(
                False,
                "El estado administrativo de la casa no es valido.",
                "VALIDACION",
            )
        if motivo_estado_administrativo not in MOTIVOS_ESTADO_ADMINISTRATIVO_VALIDOS:
            return ResultadoGestionCasas(
                False,
                "El motivo administrativo seleccionado no es valido.",
                "VALIDACION",
            )
        if estado_administrativo == ESTADO_ADMINISTRATIVO_OPERATIVA:
            motivo_estado_administrativo = MOTIVO_ESTADO_ADMINISTRATIVO_NINGUNO
        elif motivo_estado_administrativo == MOTIVO_ESTADO_ADMINISTRATIVO_NINGUNO:
            return ResultadoGestionCasas(
                False,
                "Selecciona el motivo administrativo cuando la casa quede suspendida.",
                "VALIDACION",
            )
        if estado_servicio == ESTADO_SERVICIO_INACTIVO and estado_administrativo != ESTADO_ADMINISTRATIVO_OPERATIVA:
            return ResultadoGestionCasas(
                False,
                "Una casa inactiva no debe quedar suspendida administrativamente.",
                "VALIDACION",
            )
        if casa_actual is not None and estado_servicio != casa_actual.estado_servicio:
            return ResultadoGestionCasas(
                False,
                "El estado fisico del servicio no se edita desde este formulario. Usa la accion operativa correspondiente.",
                "VALIDACION",
            )
        if casa_actual is not None and (
            ha_tenido_servicio_activo != casa_actual.ha_tenido_servicio_activo
            and not casa_actual.antecedente_servicio_editable
        ):
            return ResultadoGestionCasas(
                False,
                "El antecedente de servicio ya no se puede editar porque la casa tiene trazabilidad de activacion.",
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
                    estado_administrativo=estado_administrativo,
                    motivo_estado_administrativo=motivo_estado_administrativo,
                    ha_tenido_servicio_activo=ha_tenido_servicio_activo,
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

    def cambiar_estado(
        self,
        casa_id: int,
        estado_administrativo_actual: str,
        motivo_actual: str,
    ) -> ResultadoGestionCasas:
        if estado_administrativo_actual == ESTADO_ADMINISTRATIVO_SUSPENDIDA:
            nuevo_estado = ESTADO_ADMINISTRATIVO_OPERATIVA
            nuevo_motivo = MOTIVO_ESTADO_ADMINISTRATIVO_NINGUNO
        else:
            nuevo_estado = ESTADO_ADMINISTRATIVO_SUSPENDIDA
            nuevo_motivo = MOTIVO_ESTADO_ADMINISTRATIVO_REVISION_ADMINISTRATIVA
        try:
            self._repositorio_casas.cambiar_estado(
                casa_id,
                nuevo_estado,
                nuevo_motivo if nuevo_estado == ESTADO_ADMINISTRATIVO_SUSPENDIDA else motivo_actual,
            )
        except Exception:
            return ResultadoGestionCasas(
                False,
                "No fue posible actualizar el estado administrativo de la casa. Verifica los datos asociados y la base de datos.",
                "ERROR_SQLITE",
            )
        return ResultadoGestionCasas(
            True,
            (
                "Casa marcada como operativa."
                if nuevo_estado == ESTADO_ADMINISTRATIVO_OPERATIVA
                else "Casa marcada como suspendida administrativamente."
            ),
            "OK",
        )

    def cortar_servicio(
        self,
        casa_id: int,
        observaciones: str,
        actor_id: int | None,
    ) -> ResultadoGestionCasas:
        casa = self._repositorio_casas.obtener_por_id(casa_id)
        if casa is None:
            return ResultadoGestionCasas(
                False,
                "La casa que intentas cortar ya no existe.",
                "CASA_NO_ENCONTRADA",
            )
        if casa.estado_servicio == ESTADO_SERVICIO_CORTADO:
            return ResultadoGestionCasas(
                False,
                "La casa seleccionada ya tiene el servicio cortado.",
                "VALIDACION",
            )
        if casa.estado_servicio == ESTADO_SERVICIO_INACTIVO:
            return ResultadoGestionCasas(
                False,
                "No puedes cortar una casa inactiva.",
                "VALIDACION",
            )

        observaciones = observaciones.strip()
        if not observaciones:
            return ResultadoGestionCasas(
                False,
                "Describe las observaciones del corte para mantener trazabilidad.",
                "VALIDACION",
            )

        try:
            self._repositorio_casas.cortar_servicio(
                casa_id=casa_id,
                observaciones=observaciones,
                actor_id=actor_id,
            )
        except ValueError as error:
            return ResultadoGestionCasas(False, str(error), "VALIDACION")
        except Exception:
            return ResultadoGestionCasas(
                False,
                "No fue posible registrar el corte fisico del servicio.",
                "ERROR_SQLITE",
            )

        return ResultadoGestionCasas(
            True,
            "Servicio cortado correctamente. La reactivacion debe resolverse desde Pagos.",
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
                        "Creado",
                        "Ultima actualizacion",
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
                            casa.resumen_estado_compuesto,
                            self.formatear_fecha_hora(casa.creado_en),
                            self.formatear_fecha_hora(casa.actualizado_en),
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
