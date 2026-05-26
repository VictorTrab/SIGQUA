"""Persistencia SQLite del modulo interno de comprobantes."""

from __future__ import annotations

from contextlib import closing
from typing import Protocol

from comun.base_datos import GestorBaseDatos
from comun.configuracion.documentos import lineas_encabezado_documental
from comun.configuracion.identidad_empresa import (
    CLAVES_IDENTIDAD_EMPRESA,
    CLAVES_IDENTIDAD_LEGADAS_JUNTA,
    construir_identidad_empresa,
)
from modulos.comprobantes.entidades import (
    ConfiguracionComprobanteTermico,
    ESTADO_FALLIDO,
    ESTADO_IMPRESO,
    LineaTicketComprobante,
    TicketComprobantePago,
)


class RepositorioComprobantes(Protocol):
    """Contrato de datos para impresion de comprobantes."""

    def obtener_ticket_por_pago(self, pago_id: int) -> TicketComprobantePago | None:
        """Obtiene el snapshot imprimible de un comprobante."""

    def obtener_configuracion_termica(self) -> ConfiguracionComprobanteTermico:
        """Obtiene la configuracion vigente de impresora termica."""

    def registrar_intento_impresion(
        self,
        comprobante_id: int,
        tipo_copia: str,
        es_reimpresion: bool,
        estado: str,
        mensaje_error: str,
        actor_id: int | None,
    ) -> None:
        """Registra un intento de impresion."""

    def contar_pendientes_impresion(self) -> int:
        """Cuenta comprobantes sin impresion exitosa de ambas copias."""


class RepositorioComprobantesSQLite:
    """Implementacion SQLite del modulo interno de comprobantes."""

    def __init__(self, gestor_base_datos: GestorBaseDatos) -> None:
        self._gestor_base_datos = gestor_base_datos

    def obtener_ticket_por_pago(self, pago_id: int) -> TicketComprobantePago | None:
        consulta = """
            SELECT
                co.id AS comprobante_id,
                p.id AS pago_id,
                co.numero_comprobante,
                COALESCE(co.tipo_comprobante, p.tipo_pago, 'MENSUALIDAD') AS tipo_comprobante,
                COALESCE(co.generado_en, p.fecha_pago, '') AS generado_en,
                printf('CA-%03d', p.casa_id) AS casa_codigo,
                a.nombre_completo AS abonado_nombre,
                COALESCE(a.dni, '') AS abonado_dni,
                COALESCE(b.nombre, '') AS barrio_nombre,
                COALESCE(c.direccion_referencia, '') AS direccion_casa,
                COALESCE(mp.nombre, 'Sin metodo') AS metodo_pago,
                COALESCE(p.referencia_externa, '') AS referencia,
                COALESCE(u.nombre_completo, u.nombre_usuario, '') AS usuario_cobrador,
                COALESCE(p.total_pagado_centavos, 0) AS total_pagado_centavos
            FROM comprobantes co
            INNER JOIN pagos p ON p.id = co.pago_id
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
            SELECT COALESCE(descripcion, '') AS descripcion,
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
            configuracion = self._obtener_configuracion_documental(conexion)

        return TicketComprobantePago(
            comprobante_id=int(fila["comprobante_id"]),
            pago_id=int(fila["pago_id"]),
            lineas_encabezado=lineas_encabezado_documental(configuracion),
            numero_comprobante=str(fila["numero_comprobante"] or ""),
            tipo_comprobante=self._etiqueta_tipo_pago(str(fila["tipo_comprobante"] or "")),
            fecha_hora=str(fila["generado_en"] or ""),
            usuario_cobrador=str(fila["usuario_cobrador"] or "Sin registro"),
            abonado_nombre=str(fila["abonado_nombre"] or ""),
            abonado_dni=str(fila["abonado_dni"] or ""),
            casa_codigo=str(fila["casa_codigo"] or ""),
            barrio_nombre=str(fila["barrio_nombre"] or ""),
            direccion_casa=str(fila["direccion_casa"] or ""),
            metodo_pago=str(fila["metodo_pago"] or ""),
            referencia=str(fila["referencia"] or ""),
            lineas_detalle=tuple(
                LineaTicketComprobante(
                    descripcion=str(item["descripcion"] or ""),
                    monto=self._moneda(int(item["monto_pagado_centavos"] or 0)),
                )
                for item in filas_detalle
            ),
            total_pagado=self._moneda(int(fila["total_pagado_centavos"] or 0)),
            texto_pie=configuracion.texto_pie,
            firma_habilitada=configuracion.firma_habilitada,
            firma_texto_linea=configuracion.firma_texto_linea,
        )

    def obtener_configuracion_termica(self) -> ConfiguracionComprobanteTermico:
        claves = (
            "impresion_termica.nombre_impresora",
            "impresion_termica.ancho_papel_mm",
            "impresion_termica.corte_automatico",
            "impresion_termica.codigo_pagina",
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
        return ConfiguracionComprobanteTermico(
            nombre_impresora=valores.get("impresion_termica.nombre_impresora", "").strip(),
            ancho_papel_mm=self._entero(valores.get("impresion_termica.ancho_papel_mm", "80"), 80),
            corte_automatico=self._booleano(valores.get("impresion_termica.corte_automatico", "1")),
            codigo_pagina=valores.get("impresion_termica.codigo_pagina", "cp850").strip() or "cp850",
        )

    def registrar_intento_impresion(
        self,
        comprobante_id: int,
        tipo_copia: str,
        es_reimpresion: bool,
        estado: str,
        mensaje_error: str,
        actor_id: int | None,
    ) -> None:
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            with conexion:
                conexion.execute(
                    """
                    INSERT INTO comprobantes_impresiones(
                        comprobante_id,
                        tipo_copia,
                        es_reimpresion,
                        estado,
                        mensaje_error,
                        impreso_por
                    )
                    VALUES (?, ?, ?, ?, ?, ?);
                    """,
                    (
                        comprobante_id,
                        tipo_copia,
                        1 if es_reimpresion else 0,
                        ESTADO_IMPRESO if estado == ESTADO_IMPRESO else ESTADO_FALLIDO,
                        mensaje_error,
                        actor_id,
                    ),
                )

    def contar_pendientes_impresion(self) -> int:
        consulta = """
            SELECT COUNT(*) AS total
            FROM comprobantes co
            WHERE NOT EXISTS (
                SELECT 1
                FROM comprobantes_impresiones ci
                WHERE ci.comprobante_id = co.id
                  AND ci.estado = 'IMPRESO'
                  AND ci.tipo_copia = 'AMBAS'
                  AND ci.es_reimpresion = 0
            );
        """
        with closing(self._gestor_base_datos.obtener_conexion()) as conexion:
            fila = conexion.execute(consulta).fetchone()
        return int(fila["total"] or 0) if fila is not None else 0

    def _obtener_configuracion_documental(self, conexion: object) -> object:
        claves = (
            *CLAVES_IDENTIDAD_EMPRESA,
            *CLAVES_IDENTIDAD_LEGADAS_JUNTA,
            "factura.texto_pie",
            "factura.mostrar_correo",
            "factura.mostrar_telefono",
            "factura.mostrar_direccion",
            "factura.mostrar_identificador_fiscal",
            "documentos.firma_habilitada",
            "documentos.firma_texto_linea",
        )
        marcadores = ", ".join("?" for _ in claves)
        filas = conexion.execute(
            f"""
            SELECT clave, COALESCE(valor, '') AS valor
            FROM configuracion_sistema
            WHERE clave IN ({marcadores});
            """,
            claves,
        ).fetchall()
        valores = {str(fila["clave"]): str(fila["valor"] or "") for fila in filas}
        identidad = construir_identidad_empresa(valores, nombre_predeterminado="SIGQUA")

        class _ConfiguracionDocumental:
            nombre_junta = identidad.nombre
            telefono_junta = identidad.telefono
            correo_junta = identidad.correo
            direccion_junta = identidad.direccion
            identificador_fiscal = identidad.identificador_fiscal
            sitio_web = identidad.sitio_web
            mensaje_contacto = identidad.mensaje_contacto
            mostrar_correo = RepositorioComprobantesSQLite._booleano(
                valores.get("factura.mostrar_correo", "1")
            )
            mostrar_telefono = RepositorioComprobantesSQLite._booleano(
                valores.get("factura.mostrar_telefono", "1")
            )
            mostrar_direccion = RepositorioComprobantesSQLite._booleano(
                valores.get("factura.mostrar_direccion", "1")
            )
            mostrar_identificador_fiscal = RepositorioComprobantesSQLite._booleano(
                valores.get("factura.mostrar_identificador_fiscal", "0")
            )
            texto_pie = valores.get("factura.texto_pie", "")
            firma_habilitada = RepositorioComprobantesSQLite._booleano(
                valores.get("documentos.firma_habilitada", "0")
            )
            firma_texto_linea = valores.get("documentos.firma_texto_linea", "").strip() or "Firma autorizada"

        return _ConfiguracionDocumental()

    @staticmethod
    def _moneda(valor_centavos: int) -> str:
        return f"L {valor_centavos / 100:,.2f}"

    @staticmethod
    def _etiqueta_tipo_pago(tipo_pago: str) -> str:
        etiquetas = {
            "MENSUALIDAD": "Mensualidad",
            "PLAN_PAGO": "Plan de pago",
            "CONEXION": "Conexion",
            "RECONEXION": "Reconexion",
        }
        return etiquetas.get(tipo_pago, tipo_pago or "Comprobante")

    @staticmethod
    def _booleano(valor: str) -> bool:
        return str(valor).strip().upper() in {"1", "TRUE", "SI", "S", "YES", "ON"}

    @staticmethod
    def _entero(valor: str, predeterminado: int) -> int:
        try:
            return int(str(valor).strip())
        except ValueError:
            return predeterminado
