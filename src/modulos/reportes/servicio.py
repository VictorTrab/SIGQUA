"""Servicios del modulo de reportes administrativos."""

from __future__ import annotations

from datetime import datetime

from comun.configuracion.identidad_empresa import (
    CLAVES_IDENTIDAD_EMPRESA,
    CLAVES_IDENTIDAD_LEGADAS_JUNTA,
    construir_identidad_empresa,
)
from comun.configuracion.documentos import lineas_encabezado_documental
from comun.configuracion.gestor_rutas import GestorRutas
from modulos.configuracion.repositorio import RepositorioConfiguracionSQLite
from modulos.documentos import ServicioReportePdf
from modulos.reportes.entidades import (
    EstadoReportes,
    REPORTE_DEUDA_ABONADOS_ESTADO,
    REPORTE_HISTORIAL_ABONADO_CASA,
    REPORTE_INGRESOS_MENSUALES_DIARIOS,
    REPORTE_SERVICIO_CASAS,
    TarjetaReporte,
)
from modulos.reportes.repositorio import RepositorioReportes


class ServicioReportes:
    """Orquesta reportes administrativos con seleccion visual y filtros dinamicos."""

    CLAVES_IDENTIDAD_DOCUMENTAL = (
        *CLAVES_IDENTIDAD_EMPRESA,
        *CLAVES_IDENTIDAD_LEGADAS_JUNTA,
        "factura.mostrar_correo",
        "factura.mostrar_telefono",
        "factura.mostrar_direccion",
        "factura.mostrar_identificador_fiscal",
    )

    CATALOGO_REPORTES = (
        TarjetaReporte(
            codigo=REPORTE_DEUDA_ABONADOS_ESTADO,
            titulo="Deuda total por abonados",
            descripcion="Deuda administrativa global consolidada por abonado responsable.",
            icono="receipt-2.svg",
            resumen="Consolidado global",
        ),
        TarjetaReporte(
            codigo=REPORTE_SERVICIO_CASAS,
            titulo="Servicio por casa",
            descripcion="Estado fisico y administrativo de las viviendas.",
            icono="home.svg",
            resumen="Viviendas",
        ),
        TarjetaReporte(
            codigo=REPORTE_INGRESOS_MENSUALES_DIARIOS,
            titulo="Ingresos mensuales con detalle diario",
            descripcion="Ingresos confirmados por mes con desglose por dia.",
            icono="calendar-plus.svg",
            resumen="Mes y dia",
        ),
        TarjetaReporte(
            codigo=REPORTE_HISTORIAL_ABONADO_CASA,
            titulo="Historial por abonado/casa",
            descripcion="Pagos y comprobantes filtrables por abonado o casa.",
            icono="user.svg",
            resumen="Consulta historica",
        ),
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

    def obtener_estado(
        self,
        codigo_reporte: str = "",
        filtros: dict[str, str] | None = None,
    ) -> EstadoReportes:
        filtros_normalizados = self._normalizar_filtros(filtros)
        self._validar_rango(
            filtros_normalizados.get("fecha_desde", ""),
            filtros_normalizados.get("fecha_hasta", ""),
        )
        return self.repositorio_reportes.obtener_estado(
            catalogo=self.CATALOGO_REPORTES,
            codigo_reporte=codigo_reporte,
            filtros=filtros_normalizados,
        )

    def exportar_pdf(
        self,
        ruta_destino: str,
        codigo_reporte: str,
        filtros: dict[str, str] | None = None,
    ) -> str:
        estado = self.obtener_estado(codigo_reporte=codigo_reporte, filtros=filtros)
        if estado.tabla_actual is None:
            raise ValueError("No existe vista previa para el reporte seleccionado.")
        filtros_norm = self._normalizar_filtros(filtros)
        return self._servicio_reporte_pdf.generar_pdf(
            tabla=estado.tabla_actual,
            fecha_desde=filtros_norm.get("fecha_desde", ""),
            fecha_hasta=filtros_norm.get("fecha_hasta", ""),
            lineas_encabezado=self._obtener_lineas_encabezado_documental(),
            ruta_destino=ruta_destino,
        )

    @staticmethod
    def _normalizar_filtros(filtros: dict[str, str] | None) -> dict[str, str]:
        base = {
            "estado_abonado": "TODOS",
            "estado_servicio": "TODOS",
            "barrio": "TODOS",
            "abonado_id": "TODOS",
            "casa_id": "TODOS",
            "fecha_desde": "",
            "fecha_hasta": "",
            "incluir_mora": "1",
        }
        if filtros:
            base.update({clave: str(valor) for clave, valor in filtros.items() if valor is not None})
        return base

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

        return tuple(lineas_encabezado_documental(_ConfiguracionTemporal()))

    @staticmethod
    def _a_booleano(valor: str) -> bool:
        return str(valor).strip().upper() in {"1", "TRUE", "SI", "S", "YES", "ON"}
