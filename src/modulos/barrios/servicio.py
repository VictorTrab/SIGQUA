"""Servicios del modulo de barrios."""

from __future__ import annotations

import csv
from datetime import datetime

from modulos.barrios.entidades import (
    Barrio,
    FILTRO_BARRIOS_TODOS,
    PaginaBarrios,
    ResumenBarrios,
    ResultadoGestionBarrios,
)
from modulos.barrios.repositorio import RepositorioBarrios


class ServicioBarrios:
    """Orquesta reglas de negocio y presentacion operativa para barrios."""

    TAMANO_PAGINA = 10

    def __init__(self, repositorio_barrios: RepositorioBarrios) -> None:
        self.repositorio_barrios = repositorio_barrios

    def obtener_resumen(self) -> ResumenBarrios:
        return self.repositorio_barrios.obtener_resumen()

    def listar(
        self,
        filtro: str = "",
        filtro_rapido: str = FILTRO_BARRIOS_TODOS,
        pagina: int = 1,
    ) -> PaginaBarrios:
        pagina = max(1, pagina)
        total_registros = self.repositorio_barrios.contar(filtro, filtro_rapido)
        total_paginas = max(1, (total_registros + self.TAMANO_PAGINA - 1) // self.TAMANO_PAGINA)
        pagina = min(pagina, total_paginas)
        desplazamiento = (pagina - 1) * self.TAMANO_PAGINA
        items = self.repositorio_barrios.listar(
            filtro=filtro,
            filtro_rapido=filtro_rapido,
            limite=self.TAMANO_PAGINA,
            desplazamiento=desplazamiento,
        )
        return PaginaBarrios(
            items=items,
            pagina_actual=pagina,
            tamano_pagina=self.TAMANO_PAGINA,
            total_registros=total_registros,
        )

    def obtener_por_id(self, barrio_id: int) -> Barrio | None:
        return self.repositorio_barrios.obtener_por_id(barrio_id)

    def guardar(
        self,
        identificador: int | None,
        nombre: str,
        estado: str,
        observaciones: str,
    ) -> ResultadoGestionBarrios:
        nombre = nombre.strip()
        estado = estado.strip().upper() or "ACTIVO"
        if not nombre:
            return ResultadoGestionBarrios(False, "Indica el nombre del barrio.", "VALIDACION")
        if estado not in {"ACTIVO", "INACTIVO"}:
            return ResultadoGestionBarrios(False, "El estado del barrio no es valido.", "VALIDACION")

        try:
            self.repositorio_barrios.guardar(
                Barrio(
                    identificador=identificador,
                    nombre=nombre,
                    estado=estado,
                    observaciones=observaciones.strip(),
                )
            )
        except Exception:
            return ResultadoGestionBarrios(
                False,
                "No fue posible guardar el barrio. Verifica que el nombre no este duplicado.",
                "ERROR_SQLITE",
            )
        mensaje = "Barrio actualizado correctamente." if identificador else "Barrio creado correctamente."
        return ResultadoGestionBarrios(True, mensaje, "OK")

    def cambiar_estado(self, barrio_id: int, estado_actual: str) -> ResultadoGestionBarrios:
        nuevo_estado = "INACTIVO" if estado_actual == "ACTIVO" else "ACTIVO"
        self.repositorio_barrios.cambiar_estado(barrio_id, nuevo_estado)
        return ResultadoGestionBarrios(True, f"Barrio marcado como {nuevo_estado.lower()}.", "OK")

    def exportar_csv(
        self,
        ruta_destino: str,
        filtro: str = "",
        filtro_rapido: str = FILTRO_BARRIOS_TODOS,
    ) -> ResultadoGestionBarrios:
        barrios = self.repositorio_barrios.listar(
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
                        "Barrio",
                        "Abonados",
                        "Casas",
                        "Estado",
                        "Ultima actualizacion",
                        "Observaciones",
                    ]
                )
                for barrio in barrios:
                    escritor.writerow(
                        [
                            barrio.codigo,
                            barrio.nombre,
                            barrio.total_abonados,
                            barrio.total_casas,
                            barrio.estado,
                            self.formatear_fecha_hora(barrio.actualizado_en),
                            barrio.observaciones,
                        ]
                    )
        except OSError:
            return ResultadoGestionBarrios(
                False,
                "No fue posible generar el archivo de exportacion.",
                "ERROR_EXPORTACION",
            )

        return ResultadoGestionBarrios(True, "Listado exportado correctamente.", "OK")

    @staticmethod
    def formatear_fecha_hora(valor: str) -> str:
        if not valor:
            return "Sin registro"
        try:
            fecha = datetime.fromisoformat(valor)
        except ValueError:
            return valor
        return fecha.strftime("%d/%m/%Y %I:%M %p")
