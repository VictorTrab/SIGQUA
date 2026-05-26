"""Persistencia SQLite del modulo de historial de pagos."""

from __future__ import annotations

from contextlib import closing
from typing import Protocol

from comun.base_datos import GestorBaseDatos
from comun.configuracion.identidad_empresa import (
    CLAVES_IDENTIDAD_EMPRESA,
    CLAVES_IDENTIDAD_LEGADAS_JUNTA,
    construir_identidad_empresa,
)
from modulos.historial_pagos.entidades import (
    DetalleHistorialPago,
    FILTRO_HISTORIAL_TODOS,
    FILTRO_METODO_TODOS,
    FilaHistorialPago,
    FiltroHistorialPagos,
    LineaDetalleHistorialPago,
    ResumenHistorialPagos,
)
from modulos.pagos.entidades import ComprobantePago, ConfiguracionReciboPago


class RepositorioHistorialPagos(Protocol):
    """Contrato de persistencia para historial de pagos."""

    def listar_historial(
        self,
        filtros: FiltroHistorialPagos,
        limite: int,
        desplazamiento: int,
    ) -> list[FilaHistorialPago]:
        """Lista pagos confirmados segun filtros."""

    def contar_historial(self, filtros: FiltroHistorialPagos) -> int:
        """Cuenta pagos confirmados segun filtros."""

    def obtener_resumen_historial(self, filtros: FiltroHistorialPagos) -> ResumenHistorialPagos:
        """Retorna metricas de cabecera segun filtros activos."""

    def obtener_detalle_pago(self, pago_id: int) -> DetalleHistorialPago | None:
        """Recupera detalle completo de un pago historico."""

    def obtener_comprobante_para_reimpresion(self, pago_id: int) -> ComprobantePago | None:
        """Retorna el comprobante del pago para regenerar su PDF."""

    def obtener_configuracion_recibo(self) -> ConfiguracionReciboPago:
        """Obtiene configuracion documental vigente del comprobante."""


class RepositorioHistorialPagosSQLite:
    """Implementacion SQLite para el historial de pagos."""

    def __init__(self, gestor_base_datos: GestorBaseDatos) -> None:
        self._gestor_base_datos = gestor_base_datos

    def listar_historial(
        self,
        filtros: FiltroHistorialPagos,
        limite: int,
        desplazamiento: int,
    ) -> list[FilaHistorialPago]:
        condiciones, parametros = self._resolver_filtros(filtros)
        consulta = f"""
            SELECT
                p.id AS pago_id,
                COALESCE(co.numero_comprobante, 'Sin comprobante') AS numero_comprobante,
                COALESCE(co.generado_en, p.fecha_pago, '') AS fecha_pago,
                COALESCE(p.tipo_pago, 'MENSUALIDAD') AS tipo_pago,
                a.nombre_completo AS abonado_nombre,
                a.dni AS abonado_dni,
                printf('CA-%03d', p.casa_id) AS casa_codigo,
                COALESCE(mp.codigo, 'OTRO') AS metodo_pago_codigo,
                COALESCE(mp.nombre, 'Sin metodo') AS metodo_pago,
                COALESCE(p.referencia_externa, '') AS referencia,
                COALESCE(p.total_pagado_centavos, 0) AS total_pagado_centavos,
                COALESCE(u.nombre_completo, u.nombre_usuario, '') AS usuario_registro
            FROM pagos p
            LEFT JOIN comprobantes co ON co.pago_id = p.id
            INNER JOIN abonados a ON a.id = p.abonado_id
            INNER JOIN casas c ON c.id = p.casa_id
            LEFT JOIN metodos_pago mp ON mp.id = p.metodo_pago_id
            LEFT JOIN usuarios u ON u.id = p.usuario_cobrador_id
            WHERE {' AND '.join(condiciones)}
            ORDER BY p.fecha_pago DESC, p.id DESC
            LIMIT ? OFFSET ?;
        """
        parametros.extend([limite, desplazamiento])
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            filas = conexion.execute(consulta, tuple(parametros)).fetchall()
        return [
            FilaHistorialPago(
                pago_id=int(fila["pago_id"]),
                numero_comprobante=str(fila["numero_comprobante"] or ""),
                fecha_pago=str(fila["fecha_pago"] or ""),
                tipo_pago=str(fila["tipo_pago"] or FILTRO_HISTORIAL_TODOS),
                abonado_nombre=str(fila["abonado_nombre"] or ""),
                abonado_dni=str(fila["abonado_dni"] or ""),
                casa_codigo=str(fila["casa_codigo"] or ""),
                metodo_pago_codigo=str(fila["metodo_pago_codigo"] or ""),
                metodo_pago=str(fila["metodo_pago"] or ""),
                referencia=str(fila["referencia"] or ""),
                total_pagado_centavos=int(fila["total_pagado_centavos"] or 0),
                usuario_registro=str(fila["usuario_registro"] or ""),
            )
            for fila in filas
        ]

    def contar_historial(self, filtros: FiltroHistorialPagos) -> int:
        condiciones, parametros = self._resolver_filtros(filtros)
        consulta = f"""
            SELECT COUNT(*) AS total
            FROM pagos p
            LEFT JOIN comprobantes co ON co.pago_id = p.id
            INNER JOIN abonados a ON a.id = p.abonado_id
            INNER JOIN casas c ON c.id = p.casa_id
            LEFT JOIN metodos_pago mp ON mp.id = p.metodo_pago_id
            WHERE {' AND '.join(condiciones)};
        """
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            fila = conexion.execute(consulta, tuple(parametros)).fetchone()
        return int(fila["total"] or 0) if fila else 0

    def obtener_resumen_historial(self, filtros: FiltroHistorialPagos) -> ResumenHistorialPagos:
        condiciones, parametros = self._resolver_filtros(filtros)
        consulta = f"""
            SELECT
                COUNT(*) AS total_pagos,
                COALESCE(
                    SUM(
                        CASE
                            WHEN date(COALESCE(co.generado_en, p.fecha_pago)) = date('now', 'localtime')
                            THEN 1
                            ELSE 0
                        END
                    ),
                    0
                ) AS pagos_hoy,
                COALESCE(
                    SUM(
                        CASE
                            WHEN date(COALESCE(co.generado_en, p.fecha_pago)) = date('now', 'localtime')
                            THEN p.total_pagado_centavos
                            ELSE 0
                        END
                    ),
                    0
                ) AS total_cobrado_hoy_centavos
            FROM pagos p
            LEFT JOIN comprobantes co ON co.pago_id = p.id
            INNER JOIN abonados a ON a.id = p.abonado_id
            INNER JOIN casas c ON c.id = p.casa_id
            LEFT JOIN metodos_pago mp ON mp.id = p.metodo_pago_id
            WHERE {' AND '.join(condiciones)};
        """
        consulta_ultimo = f"""
            SELECT COALESCE(co.numero_comprobante, '') AS numero_comprobante
            FROM pagos p
            LEFT JOIN comprobantes co ON co.pago_id = p.id
            INNER JOIN abonados a ON a.id = p.abonado_id
            INNER JOIN casas c ON c.id = p.casa_id
            LEFT JOIN metodos_pago mp ON mp.id = p.metodo_pago_id
            WHERE {' AND '.join(condiciones)}
            ORDER BY p.fecha_pago DESC, p.id DESC
            LIMIT 1;
        """
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            fila = conexion.execute(consulta, tuple(parametros)).fetchone()
            fila_ultimo = conexion.execute(consulta_ultimo, tuple(parametros)).fetchone()
        return ResumenHistorialPagos(
            total_pagos=int(fila["total_pagos"] or 0) if fila else 0,
            pagos_hoy=int(fila["pagos_hoy"] or 0) if fila else 0,
            total_cobrado_hoy_centavos=int(fila["total_cobrado_hoy_centavos"] or 0) if fila else 0,
            ultimo_comprobante=str(fila_ultimo["numero_comprobante"] or "") if fila_ultimo else "",
        )

    def obtener_detalle_pago(self, pago_id: int) -> DetalleHistorialPago | None:
        consulta = """
            SELECT
                p.id AS pago_id,
                COALESCE(co.numero_comprobante, 'Sin comprobante') AS numero_comprobante,
                COALESCE(co.generado_en, p.fecha_pago, '') AS fecha_pago,
                COALESCE(p.tipo_pago, 'MENSUALIDAD') AS tipo_pago,
                printf('CA-%03d', p.casa_id) AS casa_codigo,
                a.nombre_completo AS abonado_nombre,
                a.dni AS abonado_dni,
                COALESCE(b.nombre, '') AS barrio_nombre,
                COALESCE(c.direccion_referencia, '') AS direccion_casa,
                COALESCE(mp.nombre, 'Sin metodo') AS metodo_pago,
                COALESCE(p.referencia_externa, '') AS referencia,
                COALESCE(u.nombre_completo, u.nombre_usuario, '') AS usuario_registro,
                COALESCE(p.total_pagado_centavos, 0) AS total_pagado_centavos,
                COALESCE(co.saldo_posterior_centavos, 0) AS saldo_posterior_centavos
            FROM pagos p
            LEFT JOIN comprobantes co ON co.pago_id = p.id
            INNER JOIN abonados a ON a.id = p.abonado_id
            INNER JOIN casas c ON c.id = p.casa_id
            LEFT JOIN barrios b ON b.id = c.barrio_id
            LEFT JOIN metodos_pago mp ON mp.id = p.metodo_pago_id
            LEFT JOIN usuarios u ON u.id = p.usuario_cobrador_id
            WHERE p.id = ?
              AND p.estado = 'CONFIRMADO'
            LIMIT 1;
        """
        consulta_detalle = """
            SELECT
                COALESCE(descripcion, '') AS descripcion,
                COALESCE(monto_pagado_centavos, 0) AS monto_pagado_centavos
            FROM pagos_detalle
            WHERE pago_id = ?
            ORDER BY orden_aplicacion ASC, id ASC;
        """
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            fila = conexion.execute(consulta, (pago_id,)).fetchone()
            if fila is None:
                return None
            filas_detalle = conexion.execute(consulta_detalle, (pago_id,)).fetchall()
        return DetalleHistorialPago(
            pago_id=int(fila["pago_id"]),
            numero_comprobante=str(fila["numero_comprobante"] or ""),
            fecha_pago=str(fila["fecha_pago"] or ""),
            tipo_pago=str(fila["tipo_pago"] or ""),
            casa_codigo=str(fila["casa_codigo"] or ""),
            abonado_nombre=str(fila["abonado_nombre"] or ""),
            abonado_dni=str(fila["abonado_dni"] or ""),
            barrio_nombre=str(fila["barrio_nombre"] or ""),
            direccion_casa=str(fila["direccion_casa"] or ""),
            metodo_pago=str(fila["metodo_pago"] or ""),
            referencia=str(fila["referencia"] or ""),
            usuario_registro=str(fila["usuario_registro"] or ""),
            total_pagado_centavos=int(fila["total_pagado_centavos"] or 0),
            saldo_posterior_centavos=int(fila["saldo_posterior_centavos"] or 0),
            lineas_detalle=tuple(
                LineaDetalleHistorialPago(
                    descripcion=str(item["descripcion"] or ""),
                    monto_pagado_centavos=int(item["monto_pagado_centavos"] or 0),
                )
                for item in filas_detalle
            ),
        )

    def obtener_comprobante_para_reimpresion(self, pago_id: int) -> ComprobantePago | None:
        consulta = """
            SELECT
                p.id AS pago_id,
                COALESCE(co.numero_comprobante, 'Sin comprobante') AS numero_comprobante,
                COALESCE(co.tipo_comprobante, 'MENSUALIDAD') AS tipo_comprobante,
                COALESCE(co.formato_salida, 'PDF') AS formato_salida,
                COALESCE(co.ruta_archivo, '') AS ruta_archivo,
                COALESCE(co.saldo_posterior_centavos, 0) AS saldo_posterior_centavos,
                COALESCE(co.generado_en, p.fecha_pago, '') AS generado_en,
                printf('CA-%03d', p.casa_id) AS casa_codigo,
                a.nombre_completo AS abonado_nombre,
                a.dni AS abonado_dni,
                COALESCE(b.nombre, '') AS barrio_nombre,
                COALESCE(c.direccion_referencia, '') AS direccion_casa,
                COALESCE(mp.nombre, 'Sin metodo') AS metodo_pago,
                COALESCE(p.referencia_externa, '') AS referencia,
                COALESCE(u.nombre_completo, u.nombre_usuario, '') AS usuario_registro,
                COALESCE(p.total_pagado_centavos, 0) AS total_pagado_centavos
            FROM pagos p
            LEFT JOIN comprobantes co ON co.pago_id = p.id
            INNER JOIN abonados a ON a.id = p.abonado_id
            INNER JOIN casas c ON c.id = p.casa_id
            LEFT JOIN barrios b ON b.id = c.barrio_id
            LEFT JOIN metodos_pago mp ON mp.id = p.metodo_pago_id
            LEFT JOIN usuarios u ON u.id = p.usuario_cobrador_id
            WHERE p.id = ?
              AND p.estado = 'CONFIRMADO'
            LIMIT 1;
        """
        consulta_detalles = """
            SELECT
                COALESCE(descripcion, '') AS descripcion,
                COALESCE(monto_pagado_centavos, 0) AS monto_pagado_centavos
            FROM pagos_detalle
            WHERE pago_id = ?
            ORDER BY orden_aplicacion ASC, id ASC;
        """
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            fila = conexion.execute(consulta, (pago_id,)).fetchone()
            if fila is None:
                return None
            filas_detalle = conexion.execute(consulta_detalles, (pago_id,)).fetchall()
        detalles = tuple(
            f"{str(item['descripcion'] or '').strip()} - L {int(item['monto_pagado_centavos'] or 0) / 100:,.2f}"
            for item in filas_detalle
        )
        return ComprobantePago(
            pago_id=int(fila["pago_id"]),
            numero_comprobante=str(fila["numero_comprobante"] or ""),
            tipo_comprobante=str(fila["tipo_comprobante"] or "MENSUALIDAD"),
            generado_en=str(fila["generado_en"] or ""),
            casa_codigo=str(fila["casa_codigo"] or ""),
            abonado_nombre=str(fila["abonado_nombre"] or ""),
            abonado_dni=str(fila["abonado_dni"] or ""),
            barrio_nombre=str(fila["barrio_nombre"] or ""),
            direccion_casa=str(fila["direccion_casa"] or ""),
            metodo_pago=str(fila["metodo_pago"] or ""),
            referencia=str(fila["referencia"] or ""),
            usuario_registro=str(fila["usuario_registro"] or ""),
            total_pagado_centavos=int(fila["total_pagado_centavos"] or 0),
            saldo_posterior_centavos=int(fila["saldo_posterior_centavos"] or 0),
            detalles=detalles,
            formato_salida=str(fila["formato_salida"] or "PDF"),
            ruta_archivo=str(fila["ruta_archivo"] or ""),
        )

    def obtener_configuracion_recibo(self) -> ConfiguracionReciboPago:
        claves = (
            *CLAVES_IDENTIDAD_EMPRESA,
            *CLAVES_IDENTIDAD_LEGADAS_JUNTA,
            "factura.titulo_documento",
            "factura.subtitulo_documento",
            "factura.texto_legal_superior",
            "factura.texto_pie",
            "factura.texto_legal_inferior",
            "factura.etiqueta_copia",
            "factura.mostrar_correo",
            "factura.mostrar_telefono",
            "factura.mostrar_direccion",
            "factura.mostrar_identificador_fiscal",
            "documentos.firma_habilitada",
            "documentos.firma_texto_linea",
            "documentos.abrir_pdf_automaticamente",
            "documentos.imprimir_pdf_automaticamente",
        )
        marcadores = ", ".join("?" for _ in claves)
        consulta = f"""
            SELECT clave, COALESCE(valor, '') AS valor
            FROM configuracion_sistema
            WHERE clave IN ({marcadores});
        """
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            filas = conexion.execute(consulta, claves).fetchall()
        valores = {str(fila["clave"]): str(fila["valor"] or "") for fila in filas}
        identidad = construir_identidad_empresa(valores, nombre_predeterminado="SIGQUA")
        return ConfiguracionReciboPago(
            nombre_junta=identidad.nombre,
            telefono_junta=identidad.telefono,
            correo_junta=identidad.correo,
            direccion_junta=identidad.direccion,
            identificador_fiscal=identidad.identificador_fiscal,
            sitio_web=identidad.sitio_web,
            mensaje_contacto=identidad.mensaje_contacto,
            titulo_documento=valores.get("factura.titulo_documento", "RECIBO DE PAGO") or "RECIBO DE PAGO",
            subtitulo_documento=valores.get("factura.subtitulo_documento", ""),
            texto_legal_superior=valores.get("factura.texto_legal_superior", ""),
            texto_pie=valores.get("factura.texto_pie", ""),
            texto_legal_inferior=valores.get("factura.texto_legal_inferior", ""),
            etiqueta_copia=valores.get("factura.etiqueta_copia", "ORIGINAL") or "ORIGINAL",
            mostrar_correo=self._a_booleano(valores.get("factura.mostrar_correo", "1")),
            mostrar_telefono=self._a_booleano(valores.get("factura.mostrar_telefono", "1")),
            mostrar_direccion=self._a_booleano(valores.get("factura.mostrar_direccion", "1")),
            mostrar_identificador_fiscal=self._a_booleano(
                valores.get("factura.mostrar_identificador_fiscal", "0")
            ),
            firma_habilitada=self._a_booleano(valores.get("documentos.firma_habilitada", "0")),
            firma_texto_linea=valores.get("documentos.firma_texto_linea", "").strip()
            or "Firma autorizada",
            abrir_pdf_automaticamente=self._a_booleano(
                valores.get("documentos.abrir_pdf_automaticamente", "1")
            ),
            imprimir_pdf_automaticamente=self._a_booleano(
                valores.get("documentos.imprimir_pdf_automaticamente", "0")
            ),
        )

    @staticmethod
    def _resolver_filtros(filtros: FiltroHistorialPagos) -> tuple[list[str], list[object]]:
        condiciones = ["p.estado = 'CONFIRMADO'"]
        parametros: list[object] = []

        texto = filtros.texto.strip()
        if texto:
            patron = f"%{texto}%"
            condiciones.append(
                """
                (
                    lower(COALESCE(co.numero_comprobante, '')) LIKE lower(?)
                    OR lower(COALESCE(a.nombre_completo, '')) LIKE lower(?)
                    OR COALESCE(a.dni, '') LIKE ?
                    OR lower(printf('CA-%03d', p.casa_id)) LIKE lower(?)
                    OR lower(COALESCE(p.referencia_externa, '')) LIKE lower(?)
                )
                """
            )
            parametros.extend([patron, patron, patron, patron, patron])

        if filtros.tipo_pago != FILTRO_HISTORIAL_TODOS:
            condiciones.append("COALESCE(p.tipo_pago, 'MENSUALIDAD') = ?")
            parametros.append(filtros.tipo_pago)

        if filtros.metodo_pago != FILTRO_METODO_TODOS:
            if filtros.metodo_pago == "OTRO":
                condiciones.append(
                    """
                    COALESCE(mp.codigo, 'OTRO') NOT IN ('EFECTIVO', 'TRANSFERENCIA', 'DEPOSITO')
                    """
                )
            else:
                condiciones.append("COALESCE(mp.codigo, 'OTRO') = ?")
                parametros.append(filtros.metodo_pago)

        if filtros.fecha_desde:
            condiciones.append("date(COALESCE(co.generado_en, p.fecha_pago)) >= date(?)")
            parametros.append(filtros.fecha_desde)
        if filtros.fecha_hasta:
            condiciones.append("date(COALESCE(co.generado_en, p.fecha_pago)) <= date(?)")
            parametros.append(filtros.fecha_hasta)

        return condiciones, parametros

    @staticmethod
    def _a_booleano(valor: str) -> bool:
        return valor.strip().upper() in {"1", "TRUE", "SI", "S", "YES", "ON"}
