"""Servicios del modulo de reportes administrativos."""

from __future__ import annotations

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
from modulos.reportes.entidades import (
    EstadoReportes,
    REPORTE_ABONADOS_SIN_DEUDA,
    REPORTE_DEUDA_ABONADOS_ESTADO,
    REPORTE_HISTORIAL_ABONADO,
    REPORTE_HISTORIAL_CASA,
    REPORTE_INGRESOS_DIARIOS,
    REPORTE_INGRESOS_MENSUALES,
    REPORTE_PLANES_ACTIVOS,
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
        "documentos.abrir_pdf_automaticamente",
        "documentos.imprimir_pdf_automaticamente",
    )

    CATALOGO_REPORTES = (
        TarjetaReporte(
            codigo=REPORTE_DEUDA_ABONADOS_ESTADO,
            titulo="Deuda por abonado",
            descripcion="Deuda total consolidada por abonado responsable actual.",
            icono="receipt-2.svg",
            resumen="Activos e inactivos",
        ),
        TarjetaReporte(
            codigo=REPORTE_ABONADOS_SIN_DEUDA,
            titulo="Abonados sin deuda",
            descripcion="Responsables sin deuda base, mora ni saldo vivo de plan.",
            icono="circle-check.svg",
            resumen="Responsables al dia",
        ),
        TarjetaReporte(
            codigo=REPORTE_SERVICIO_CASAS,
            titulo="Servicio por casa",
            descripcion="Cuantas casas tienen servicio y cuantas no.",
            icono="home.svg",
            resumen="Resumen operativo",
        ),
        TarjetaReporte(
            codigo=REPORTE_INGRESOS_MENSUALES,
            titulo="Ingresos mensuales",
            descripcion="Resumen mensual de ingresos confirmados.",
            icono="calendar-plus.svg",
            resumen="Consolidado por mes",
        ),
        TarjetaReporte(
            codigo=REPORTE_INGRESOS_DIARIOS,
            titulo="Ingresos diarios",
            descripcion="Detalle por dia dentro del rango seleccionado.",
            icono="calendar-stats.svg",
            resumen="Detalle diario",
        ),
        TarjetaReporte(
            codigo=REPORTE_HISTORIAL_ABONADO,
            titulo="Historial por abonado",
            descripcion="Pagos confirmados filtrados por abonado responsable.",
            icono="user.svg",
            resumen="Consulta puntual",
        ),
        TarjetaReporte(
            codigo=REPORTE_HISTORIAL_CASA,
            titulo="Historial por casa",
            descripcion="Pagos confirmados filtrados por casa.",
            icono="home-2.svg",
            resumen="Consulta por inmueble",
        ),
        TarjetaReporte(
            codigo=REPORTE_PLANES_ACTIVOS,
            titulo="Planes activos",
            descripcion="Planes vigentes, cuotas pendientes y saldo vivo.",
            icono="notes.svg",
            resumen="Seguimiento financiero",
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

        return tuple(
            ServicioComprobantePago.lineas_encabezado_desde_configuracion(_ConfiguracionTemporal())
        )

    @staticmethod
    def _a_booleano(valor: str) -> bool:
        return str(valor).strip().upper() in {"1", "TRUE", "SI", "S", "YES", "ON"}
