"""Servicios del modulo de reportes."""

from __future__ import annotations

import csv
from datetime import datetime

from comun.configuracion.identidad_empresa import (
    CLAVES_IDENTIDAD_EMPRESA,
    CLAVES_IDENTIDAD_LEGADAS_JUNTA,
    construir_identidad_empresa,
)
from comun.configuracion.gestor_rutas import GestorRutas
from modulos.configuracion.repositorio import RepositorioConfiguracionSQLite
from modulos.documentos import ServicioReportePdf
from modulos.documentos.servicios.servicio_comprobante_pago import ServicioComprobantePago
from modulos.reportes.entidades import EstadoReportes
from modulos.reportes.repositorio import RepositorioReportes


class ServicioReportes:
    """Orquesta consultas de reportes basicos."""

    CLAVES_IDENTIDAD_DOCUMENTAL = (
        *CLAVES_IDENTIDAD_EMPRESA,
        *CLAVES_IDENTIDAD_LEGADAS_JUNTA,
        "factura.mostrar_correo",
        "factura.mostrar_telefono",
        "factura.mostrar_direccion",
        "factura.mostrar_identificador_fiscal",
        "documentos.abrir_pdf_automaticamente",
        "documentos.imprimir_pdf_automaticamente",
    )

    def __init__(
        self,
        repositorio_reportes: RepositorioReportes,
        repositorio_configuracion: RepositorioConfiguracionSQLite | None = None,
        gestor_rutas: GestorRutas | None = None,
        servicio_reporte_pdf: ServicioReportePdf | None = None,
    ) -> None:
        self.repositorio_reportes = repositorio_reportes
        self._repositorio_configuracion = repositorio_configuracion
        self._gestor_rutas = gestor_rutas or GestorRutas()
        self._servicio_reporte_pdf = servicio_reporte_pdf or ServicioReportePdf(
            gestor_rutas=self._gestor_rutas,
        )

    def obtener_estado(self, fecha_desde: str = "", fecha_hasta: str = "") -> EstadoReportes:
        self._validar_rango(fecha_desde, fecha_hasta)
        return self.repositorio_reportes.obtener_estado(
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
        )

    def exportar_csv(
        self,
        ruta_destino: str,
        codigo_reporte: str,
        fecha_desde: str = "",
        fecha_hasta: str = "",
    ) -> str:
        estado = self.obtener_estado(fecha_desde=fecha_desde, fecha_hasta=fecha_hasta)
        tabla = next((item for item in estado.tablas if item.codigo == codigo_reporte), None)
        if tabla is None:
            raise ValueError("No existe el reporte seleccionado para exportacion.")
        with open(ruta_destino, "w", newline="", encoding="utf-8") as archivo:
            escritor = csv.writer(archivo)
            escritor.writerow(tabla.columnas)
            for fila in tabla.filas:
                escritor.writerow(fila)
        return ruta_destino

    def exportar_pdf(
        self,
        ruta_destino: str,
        codigo_reporte: str,
        fecha_desde: str = "",
        fecha_hasta: str = "",
    ) -> str:
        estado = self.obtener_estado(fecha_desde=fecha_desde, fecha_hasta=fecha_hasta)
        tabla = next((item for item in estado.tablas if item.codigo == codigo_reporte), None)
        if tabla is None:
            raise ValueError("No existe el reporte seleccionado para exportacion.")
        return self._servicio_reporte_pdf.generar_pdf(
            tabla=tabla,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            lineas_encabezado=self._obtener_lineas_encabezado_documental(),
            ruta_destino=ruta_destino,
        )

    def obtener_politica_documental(self) -> tuple[bool, bool]:
        if self._repositorio_configuracion is None:
            return True, False
        parametros = self._repositorio_configuracion.listar_por_claves(
            (
                "documentos.abrir_pdf_automaticamente",
                "documentos.imprimir_pdf_automaticamente",
            )
        )
        abrir = self._a_booleano(
            parametros.get("documentos.abrir_pdf_automaticamente").valor
            if parametros.get("documentos.abrir_pdf_automaticamente")
            else "1"
        )
        imprimir = self._a_booleano(
            parametros.get("documentos.imprimir_pdf_automaticamente").valor
            if parametros.get("documentos.imprimir_pdf_automaticamente")
            else "0"
        )
        return abrir, imprimir

    @staticmethod
    def _validar_rango(fecha_desde: str, fecha_hasta: str) -> None:
        if fecha_desde:
            datetime.strptime(fecha_desde, "%Y-%m-%d")
        if fecha_hasta:
            datetime.strptime(fecha_hasta, "%Y-%m-%d")
        if fecha_desde and fecha_hasta and fecha_desde > fecha_hasta:
            raise ValueError("La fecha inicial no puede ser mayor que la fecha final.")

    def _obtener_lineas_encabezado_documental(self) -> tuple[str, ...]:
        if self._repositorio_configuracion is None:
            return ("SIGQUA", "Sistema de Control Administrativo")
        parametros = self._repositorio_configuracion.listar_por_claves(
            self.CLAVES_IDENTIDAD_DOCUMENTAL
        )
        valores = {clave: parametro.valor for clave, parametro in parametros.items()}
        identidad = construir_identidad_empresa(valores, nombre_predeterminado="SIGQUA")

        class _ConfiguracionTemporal:
            nombre_junta = identidad.nombre
            telefono_junta = identidad.telefono
            correo_junta = identidad.correo
            direccion_junta = identidad.direccion
            identificador_fiscal = identidad.identificador_fiscal
            sitio_web = identidad.sitio_web
            mensaje_contacto = identidad.mensaje_contacto
            mostrar_correo = ServicioReportes._a_booleano(valores.get("factura.mostrar_correo", "1"))
            mostrar_telefono = ServicioReportes._a_booleano(valores.get("factura.mostrar_telefono", "1"))
            mostrar_direccion = ServicioReportes._a_booleano(valores.get("factura.mostrar_direccion", "1"))
            mostrar_identificador_fiscal = ServicioReportes._a_booleano(
                valores.get("factura.mostrar_identificador_fiscal", "0")
            )

        return tuple(
            ServicioComprobantePago.lineas_encabezado_desde_configuracion(_ConfiguracionTemporal())
        )

    @staticmethod
    def _a_booleano(valor: str) -> bool:
        return str(valor).strip().upper() in {"1", "TRUE", "SI", "S", "YES", "ON"}
