"""Servicios del modulo de reportes."""

from __future__ import annotations

import csv
from datetime import datetime

from comun.configuracion.gestor_rutas import GestorRutas
from modulos.configuracion.repositorio import RepositorioConfiguracionSQLite
from modulos.documentos import ServicioReportePdf
from modulos.documentos.servicios.servicio_comprobante_pago import ServicioComprobantePago
from modulos.reportes.entidades import EstadoReportes
from modulos.reportes.repositorio import RepositorioReportes


class ServicioReportes:
    """Orquesta consultas de reportes basicos."""

    CLAVES_IDENTIDAD_DOCUMENTAL = (
        "junta.nombre",
        "junta.telefono",
        "junta.correo",
        "junta.direccion",
        "junta.identificador_fiscal",
        "junta.sitio_web",
        "junta.mensaje_contacto",
        "factura.mostrar_correo",
        "factura.mostrar_telefono",
        "factura.mostrar_direccion",
        "factura.mostrar_identificador_fiscal",
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
            return ("SICAP", "Sistema de Control Administrativo")
        parametros = self._repositorio_configuracion.listar_por_claves(
            self.CLAVES_IDENTIDAD_DOCUMENTAL
        )
        valores = {clave: parametro.valor for clave, parametro in parametros.items()}

        class _ConfiguracionTemporal:
            nombre_junta = valores.get("junta.nombre", "Junta de Agua")
            telefono_junta = valores.get("junta.telefono", "")
            correo_junta = valores.get("junta.correo", "")
            direccion_junta = valores.get("junta.direccion", "")
            identificador_fiscal = valores.get("junta.identificador_fiscal", "")
            sitio_web = valores.get("junta.sitio_web", "")
            mensaje_contacto = valores.get("junta.mensaje_contacto", "")
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
