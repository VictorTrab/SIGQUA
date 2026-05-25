"""Siembra escenarios operativos de pagos para validacion local de SIGQUA."""

from __future__ import annotations

import sqlite3
import sys
from calendar import monthrange
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path


RAIZ_PROYECTO = Path(__file__).resolve().parents[1]
RUTA_SRC = RAIZ_PROYECTO / "src"
if str(RUTA_SRC) not in sys.path:
    sys.path.insert(0, str(RUTA_SRC))

from comun.base_datos import GestorBaseDatos  # noqa: E402
from modulos.casas.repositorio import RepositorioCasasSQLite  # noqa: E402
from modulos.casas.servicio import ServicioCasas  # noqa: E402
from modulos.pagos.entidades import FormularioPago, TIPO_PAGO_MENSUALIDAD  # noqa: E402
from modulos.pagos.repositorio import RepositorioPagosSQLite  # noqa: E402
from modulos.pagos.servicio import ServicioPagos  # noqa: E402
from modulos.planes_pago.entidades import FormularioPlanPago  # noqa: E402
from modulos.planes_pago.repositorio import RepositorioPlanesPagoSQLite  # noqa: E402
from modulos.planes_pago.servicio import ServicioPlanesPago  # noqa: E402


MARCADOR = "[ESCENARIO_PAGOS]"
USUARIO_ACTOR = "admin"
CODIGO_METODO_EFECTIVO = "EFECTIVO"
PRECIO_MENSUAL_DEFECTO = 15000


@dataclass(frozen=True, slots=True)
class EscenarioCasa:
    codigo: str
    nombre: str
    dni: str
    telefono: str
    barrio: str
    referencia: str
    estado_servicio: str
    observaciones: str
    estado_abonado: str = "ACTIVO"


def desplazar_mes(anio: int, mes: int, desplazamiento: int) -> tuple[int, int]:
    indice = (anio * 12) + (mes - 1) + desplazamiento
    return indice // 12, (indice % 12) + 1


def fecha_periodo(anio: int, mes: int) -> tuple[str, str, str]:
    ultimo_dia = monthrange(anio, mes)[1]
    return (
        f"{anio:04d}-{mes:02d}-01",
        f"{anio:04d}-{mes:02d}-{ultimo_dia:02d}",
        f"{anio:04d}-{mes:02d}-10",
    )


class SembradorEscenariosPagos:
    def __init__(self) -> None:
        self._gestor = GestorBaseDatos()
        self._repo_pagos = RepositorioPagosSQLite(self._gestor)
        self._servicio_pagos = ServicioPagos(self._repo_pagos)
        self._repo_casas = RepositorioCasasSQLite(self._gestor)
        self._servicio_casas = ServicioCasas(self._repo_casas)
        self._repo_planes = RepositorioPlanesPagoSQLite(self._gestor)
        self._servicio_planes = ServicioPlanesPago(self._repo_planes)
        self._hoy = date.today()
        self._admin_id: int | None = None
        self._metodo_efectivo_id: int | None = None

    def ejecutar(self) -> None:
        self._gestor.inicializar_base_datos()
        with self._gestor.obtener_conexion() as conexion:
            self._admin_id = self._obtener_id_usuario(conexion, USUARIO_ACTOR)
            self._metodo_efectivo_id = self._obtener_id_metodo(conexion, CODIGO_METODO_EFECTIVO)
            self._asegurar_periodos_base(conexion)
            self._asegurar_precio_mensual(conexion)

            self._sembrar_mensual_basico(conexion)
            self._sembrar_mora_critica(conexion)
            self._sembrar_suspendido_bloqueado(conexion)
            self._sembrar_cortado_reconexion(conexion)
            self._sembrar_plan_reconexion(conexion)
            self._sembrar_cambio_dueno(conexion)
            self._sembrar_conexion_inicial(conexion)

            conexion.commit()
            self._mostrar_resumen(conexion)

    def _sembrar_mensual_basico(self, conexion: sqlite3.Connection) -> None:
        escenario = EscenarioCasa(
            codigo="ESC-01",
            nombre="Rosa Martinez",
            dni="0801199501011",
            telefono="9890-1001",
            barrio="El Mirador",
            referencia="Casa verde frente a la cancha del mirador",
            estado_servicio="ACTIVO",
            observaciones=f"{MARCADOR} ESC-01 flujo mensual basico con tres mensualidades.",
        )
        casa_id, abonado_id = self._asegurar_casa_escenario(conexion, escenario)
        for desplazamiento, estado in [(-2, "VENCIDO"), (-1, "VENCIDO"), (0, "PENDIENTE")]:
            anio, mes = desplazar_mes(self._hoy.year, self._hoy.month, desplazamiento)
            periodo_id = self._asegurar_periodo(conexion, anio, mes)
            self._asegurar_cargo_mensual(
                conexion,
                casa_id=casa_id,
                abonado_id=abonado_id,
                periodo_id=periodo_id,
                anio=anio,
                mes=mes,
                descripcion=f"Mensualidad regular {mes:02d}/{anio:04d}",
                monto_centavos=self._obtener_precio_mensual(conexion),
                saldo_pendiente_centavos=self._obtener_precio_mensual(conexion),
                estado=estado,
                origen="MENSUAL",
            )

    def _sembrar_mora_critica(self, conexion: sqlite3.Connection) -> None:
        escenario = EscenarioCasa(
            codigo="ESC-02",
            nombre="Julio Perdomo",
            dni="0801199402022",
            telefono="9890-1002",
            barrio="La Laguna",
            referencia="Casa blanca al final de la calle de la laguna",
            estado_servicio="ACTIVO",
            observaciones=f"{MARCADOR} ESC-02 mora critica con recargo separado.",
        )
        casa_id, abonado_id = self._asegurar_casa_escenario(conexion, escenario)
        precio = self._obtener_precio_mensual(conexion)
        for desplazamiento in range(-5, 1):
            anio, mes = desplazar_mes(self._hoy.year, self._hoy.month, desplazamiento)
            periodo_id = self._asegurar_periodo(conexion, anio, mes)
            estado = "PENDIENTE" if desplazamiento == 0 else "VENCIDO"
            self._asegurar_cargo_mensual(
                conexion,
                casa_id=casa_id,
                abonado_id=abonado_id,
                periodo_id=periodo_id,
                anio=anio,
                mes=mes,
                descripcion=f"Mensualidad en mora {mes:02d}/{anio:04d}",
                monto_centavos=precio,
                saldo_pendiente_centavos=precio,
                estado=estado,
                origen="MENSUAL",
            )

        anio_mora, mes_mora = desplazar_mes(self._hoy.year, self._hoy.month, -1)
        periodo_mora_id = self._asegurar_periodo(conexion, anio_mora, mes_mora)
        self._asegurar_cargo_operativo(
            conexion,
            casa_id=casa_id,
            abonado_id=abonado_id,
            concepto_codigo="MORA",
            descripcion="[ESC-02] Recargo de mora acumulado",
            monto_centavos=3000,
            saldo_pendiente_centavos=3000,
            estado="VENCIDO",
            origen="MANUAL",
            fecha_vencimiento=f"{anio_mora:04d}-{mes_mora:02d}-10",
            periodo_id=periodo_mora_id,
        )

    def _sembrar_suspendido_bloqueado(self, conexion: sqlite3.Connection) -> None:
        escenario = EscenarioCasa(
            codigo="ESC-03",
            nombre="Marta Suazo",
            dni="0801199303033",
            telefono="9890-1003",
            barrio="Los Pinos",
            referencia="Casa celeste junto a la pulperia de los pinos",
            estado_servicio="SUSPENDIDO",
            observaciones=f"{MARCADOR} ESC-03 pago mensual bloqueado por suspension.",
        )
        casa_id, abonado_id = self._asegurar_casa_escenario(conexion, escenario)
        precio = self._obtener_precio_mensual(conexion)
        for desplazamiento in (-3, -2, -1):
            anio, mes = desplazar_mes(self._hoy.year, self._hoy.month, desplazamiento)
            periodo_id = self._asegurar_periodo(conexion, anio, mes)
            self._asegurar_cargo_mensual(
                conexion,
                casa_id=casa_id,
                abonado_id=abonado_id,
                periodo_id=periodo_id,
                anio=anio,
                mes=mes,
                descripcion=f"Mensualidad suspendida {mes:02d}/{anio:04d}",
                monto_centavos=precio,
                saldo_pendiente_centavos=precio,
                estado="VENCIDO",
                origen="MENSUAL",
            )

    def _sembrar_cortado_reconexion(self, conexion: sqlite3.Connection) -> None:
        escenario = EscenarioCasa(
            codigo="ESC-04",
            nombre="Oscar Velasquez",
            dni="0801199204044",
            telefono="9890-1004",
            barrio="Sector Norte",
            referencia="Casa amarilla a la par del tanque viejo",
            estado_servicio="CORTADO",
            observaciones=f"{MARCADOR} ESC-04 casa cortada con reconexion pendiente.",
        )
        casa_id, abonado_id = self._asegurar_casa_escenario(conexion, escenario)
        precio = self._obtener_precio_mensual(conexion)
        for desplazamiento in (-2, -1):
            anio, mes = desplazar_mes(self._hoy.year, self._hoy.month, desplazamiento)
            periodo_id = self._asegurar_periodo(conexion, anio, mes)
            self._asegurar_cargo_mensual(
                conexion,
                casa_id=casa_id,
                abonado_id=abonado_id,
                periodo_id=periodo_id,
                anio=anio,
                mes=mes,
                descripcion=f"Mensualidad cortada {mes:02d}/{anio:04d}",
                monto_centavos=precio,
                saldo_pendiente_centavos=precio,
                estado="VENCIDO",
                origen="MENSUAL",
            )
        self._asegurar_cargo_operativo(
            conexion,
            casa_id=casa_id,
            abonado_id=abonado_id,
            concepto_codigo="RECONEXION",
            descripcion="[ESC-04] Cargo de reconexion pendiente",
            monto_centavos=45000,
            saldo_pendiente_centavos=45000,
            estado="PENDIENTE",
            origen="PROCESO_SERVICIO",
            fecha_vencimiento=self._hoy.isoformat(),
        )

    def _sembrar_plan_reconexion(self, conexion: sqlite3.Connection) -> None:
        escenario = EscenarioCasa(
            codigo="ESC-05",
            nombre="Teresa Mejia",
            dni="0801199105055",
            telefono="9890-1005",
            barrio="La Esperanza",
            referencia="Casa rosada frente a la parada de buses",
            estado_servicio="CORTADO",
            observaciones=f"{MARCADOR} ESC-05 plan de pago de reconexion activo.",
        )
        casa_id, abonado_id = self._asegurar_casa_escenario(conexion, escenario)
        self._asegurar_cargo_operativo(
            conexion,
            casa_id=casa_id,
            abonado_id=abonado_id,
            concepto_codigo="RECONEXION",
            descripcion="[ESC-05] Reconexion financiada en plan activo",
            monto_centavos=90000,
            saldo_pendiente_centavos=90000,
            estado="PENDIENTE",
            origen="PROCESO_SERVICIO",
            fecha_vencimiento=self._hoy.isoformat(),
        )
        plan_id = self._asegurar_plan_reconexion(
            conexion,
            casa_id=casa_id,
            observaciones=f"{MARCADOR} ESC-05 plan de reconexion con cuotas reales.",
        )
        self._configurar_cuotas_plan_reconexion(conexion, plan_id)

    def _sembrar_cambio_dueno(self, conexion: sqlite3.Connection) -> None:
        escenario_inicial = EscenarioCasa(
            codigo="ESC-06",
            nombre="Mauricio Castro",
            dni="0801199006066",
            telefono="9890-1006",
            barrio="Buenos Aires",
            referencia="Casa de esquina con porton negro en Buenos Aires",
            estado_servicio="ACTIVO",
            observaciones=f"{MARCADOR} ESC-06 casa con traspaso y deuda migrada.",
        )
        casa_id, abonado_inicial_id = self._asegurar_casa_escenario(conexion, escenario_inicial)
        precio = self._obtener_precio_mensual(conexion)
        pago_historico_existente = self._existe_pago_por_referencia(conexion, "ESC-06-PAGO-001")
        for desplazamiento in (-4, -3, -2, -1):
            anio, mes = desplazar_mes(self._hoy.year, self._hoy.month, desplazamiento)
            periodo_id = self._asegurar_periodo(conexion, anio, mes)
            estado = "PAGADO" if desplazamiento == -4 and pago_historico_existente else "VENCIDO"
            saldo = 0 if desplazamiento == -4 and pago_historico_existente else precio
            self._asegurar_cargo_mensual(
                conexion,
                casa_id=casa_id,
                abonado_id=abonado_inicial_id,
                periodo_id=periodo_id,
                anio=anio,
                mes=mes,
                descripcion=f"Mensualidad historica {mes:02d}/{anio:04d}",
                monto_centavos=precio,
                saldo_pendiente_centavos=saldo,
                estado=estado,
                origen="MENSUAL",
            )

        if not pago_historico_existente:
            conexion.commit()
            resultado = self._servicio_pagos.registrar_pago(
                FormularioPago(
                    casa_id=casa_id,
                    tipo_pago=TIPO_PAGO_MENSUALIDAD,
                    cantidad_meses=1,
                    metodo_pago_id=self._metodo_efectivo_id,
                    referencia="ESC-06-PAGO-001",
                    observaciones=f"{MARCADOR} Pago historico antes del cambio de dueno.",
                ),
                actor_id=self._admin_id,
            )
            if not resultado.exito:
                raise RuntimeError(f"No fue posible crear el pago historico de ESC-06: {resultado.mensaje}")
            self._ajustar_fecha_pago(conexion, "ESC-06-PAGO-001", self._fecha_relativa(-110))

        abonado_intermedio_id = self._asegurar_abonado(
            conexion,
            dni="0801199007077",
            nombre="Elena Pineda",
            telefono="9890-1007",
            barrio_nombre="Buenos Aires",
            direccion_referencia="Pasaje central de Buenos Aires",
            observaciones=f"{MARCADOR} ESC-06 abonada intermedia del traspaso.",
            estado="ACTIVO",
        )
        abonado_final_id = self._asegurar_abonado(
            conexion,
            dni="0801199008088",
            nombre="Sonia Aguilar",
            telefono="9890-1008",
            barrio_nombre="Buenos Aires",
            direccion_referencia="Contiguo a la cancha de Buenos Aires",
            observaciones=f"{MARCADOR} ESC-06 abonada final del traspaso.",
            estado="ACTIVO",
        )
        self._aplicar_cambio_dueno_si_falta(
            conexion,
            casa_id=casa_id,
            nuevo_abonado_id=abonado_intermedio_id,
            motivo=f"{MARCADOR} ESC-06 venta inicial con deuda pendiente.",
            fecha_evento=self._fecha_relativa(-70),
        )
        self._aplicar_cambio_dueno_si_falta(
            conexion,
            casa_id=casa_id,
            nuevo_abonado_id=abonado_final_id,
            motivo=f"{MARCADOR} ESC-06 regularizacion final y nuevo responsable.",
            fecha_evento=self._fecha_relativa(-25),
        )
        self._alinear_responsable_actual(
            conexion,
            casa_id=casa_id,
            abonado_id=abonado_final_id,
        )

    def _sembrar_conexion_inicial(self, conexion: sqlite3.Connection) -> None:
        escenario = EscenarioCasa(
            codigo="ESC-07",
            nombre="Ricardo Cerrato",
            dni="0801199009099",
            telefono="9890-1009",
            barrio="San Jorge",
            referencia="Lote nuevo al final del callejon del sector escuela",
            estado_servicio="INACTIVO",
            observaciones=f"{MARCADOR} ESC-07 conexion inicial con prima y cargo principal.",
        )
        casa_id, abonado_id = self._asegurar_casa_escenario(conexion, escenario)
        self._asegurar_cargo_operativo(
            conexion,
            casa_id=casa_id,
            abonado_id=abonado_id,
            concepto_codigo="PRIMA",
            descripcion="[ESC-07] Prima de conexion pendiente",
            monto_centavos=30000,
            saldo_pendiente_centavos=30000,
            estado="PENDIENTE",
            origen="PROCESO_SERVICIO",
            fecha_vencimiento=self._hoy.isoformat(),
        )
        self._asegurar_cargo_operativo(
            conexion,
            casa_id=casa_id,
            abonado_id=abonado_id,
            concepto_codigo="CONEXION",
            descripcion="[ESC-07] Cargo principal de conexion",
            monto_centavos=120000,
            saldo_pendiente_centavos=120000,
            estado="PENDIENTE",
            origen="PROCESO_SERVICIO",
            fecha_vencimiento=self._hoy.isoformat(),
        )

    def _asegurar_periodos_base(self, conexion: sqlite3.Connection) -> None:
        for desplazamiento in range(-6, 4):
            anio, mes = desplazar_mes(self._hoy.year, self._hoy.month, desplazamiento)
            self._asegurar_periodo(conexion, anio, mes)

    def _asegurar_precio_mensual(self, conexion: sqlite3.Connection) -> None:
        conexion.execute(
            """
            UPDATE configuracion_sistema
            SET valor = COALESCE(NULLIF(valor, ''), ?),
                actualizado_en = datetime('now', 'localtime')
            WHERE clave = 'cobro.precio_mensual_centavos';
            """,
            (str(PRECIO_MENSUAL_DEFECTO),),
        )

    def _obtener_precio_mensual(self, conexion: sqlite3.Connection) -> int:
        fila = conexion.execute(
            "SELECT valor FROM configuracion_sistema WHERE clave = 'cobro.precio_mensual_centavos';"
        ).fetchone()
        if fila is None:
            return PRECIO_MENSUAL_DEFECTO
        try:
            return int(str(fila["valor"] or PRECIO_MENSUAL_DEFECTO))
        except ValueError:
            return PRECIO_MENSUAL_DEFECTO

    def _asegurar_abonado(
        self,
        conexion: sqlite3.Connection,
        *,
        dni: str,
        nombre: str,
        telefono: str,
        barrio_nombre: str,
        direccion_referencia: str,
        observaciones: str,
        estado: str,
    ) -> int:
        barrio_id = self._asegurar_barrio(conexion, barrio_nombre)
        fila = conexion.execute(
            "SELECT id FROM abonados WHERE dni = ? LIMIT 1;",
            (dni,),
        ).fetchone()
        if fila is None:
            cursor = conexion.execute(
                """
                INSERT INTO abonados(
                    dni,
                    nombre_completo,
                    telefono,
                    barrio_id,
                    direccion_referencia,
                    observaciones,
                    estado
                )
                VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                (dni, nombre, telefono, barrio_id, direccion_referencia, observaciones, estado),
            )
            return int(cursor.lastrowid)
        abonado_id = int(fila["id"])
        conexion.execute(
            """
            UPDATE abonados
            SET nombre_completo = ?,
                telefono = ?,
                barrio_id = ?,
                direccion_referencia = ?,
                observaciones = ?,
                estado = ?,
                actualizado_en = datetime('now', 'localtime')
            WHERE id = ?;
            """,
            (nombre, telefono, barrio_id, direccion_referencia, observaciones, estado, abonado_id),
        )
        return abonado_id

    def _asegurar_casa_escenario(
        self,
        conexion: sqlite3.Connection,
        escenario: EscenarioCasa,
    ) -> tuple[int, int]:
        abonado_id = self._asegurar_abonado(
            conexion,
            dni=escenario.dni,
            nombre=escenario.nombre,
            telefono=escenario.telefono,
            barrio_nombre=escenario.barrio,
            direccion_referencia=escenario.referencia,
            observaciones=escenario.observaciones,
            estado=escenario.estado_abonado,
        )
        barrio_id = self._asegurar_barrio(conexion, escenario.barrio)
        fila = conexion.execute(
            """
            SELECT id
            FROM casas
            WHERE observaciones = ?
            LIMIT 1;
            """,
            (escenario.observaciones,),
        ).fetchone()
        if fila is None:
            cursor = conexion.execute(
                """
                INSERT INTO casas(
                    abonado_id,
                    barrio_id,
                    direccion_referencia,
                    estado_servicio,
                    observaciones
                )
                VALUES (?, ?, ?, ?, ?);
                """,
                (
                    abonado_id,
                    barrio_id,
                    escenario.referencia,
                    escenario.estado_servicio,
                    escenario.observaciones,
                ),
            )
            return int(cursor.lastrowid), abonado_id

        casa_id = int(fila["id"])
        conexion.execute(
            """
            UPDATE casas
            SET abonado_id = ?,
                barrio_id = ?,
                direccion_referencia = ?,
                estado_servicio = ?,
                observaciones = ?,
                actualizado_en = datetime('now', 'localtime')
            WHERE id = ?;
            """,
            (
                abonado_id,
                barrio_id,
                escenario.referencia,
                escenario.estado_servicio,
                escenario.observaciones,
                casa_id,
            ),
        )
        return casa_id, abonado_id

    def _asegurar_barrio(self, conexion: sqlite3.Connection, nombre: str) -> int:
        fila = conexion.execute(
            "SELECT id FROM barrios WHERE lower(nombre) = lower(?) LIMIT 1;",
            (nombre,),
        ).fetchone()
        if fila is None:
            cursor = conexion.execute(
                "INSERT INTO barrios(nombre, estado, observaciones) VALUES (?, 'ACTIVO', ?);",
                (nombre, f"{MARCADOR} Barrio para escenarios de simulacion."),
            )
            return int(cursor.lastrowid)
        barrio_id = int(fila["id"])
        conexion.execute(
            """
            UPDATE barrios
            SET estado = 'ACTIVO'
            WHERE id = ?;
            """,
            (barrio_id,),
        )
        return barrio_id

    def _asegurar_periodo(self, conexion: sqlite3.Connection, anio: int, mes: int) -> int:
        fila = conexion.execute(
            "SELECT id FROM periodos_cobro WHERE anio = ? AND mes = ? LIMIT 1;",
            (anio, mes),
        ).fetchone()
        if fila is not None:
            return int(fila["id"])
        fecha_inicio, fecha_fin, fecha_vencimiento = fecha_periodo(anio, mes)
        cursor = conexion.execute(
            """
            INSERT INTO periodos_cobro(
                anio,
                mes,
                nombre,
                fecha_inicio,
                fecha_fin,
                fecha_vencimiento,
                estado
            )
            VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            (
                anio,
                mes,
                f"Periodo {mes:02d}/{anio:04d}",
                fecha_inicio,
                fecha_fin,
                fecha_vencimiento,
                "CERRADO" if date(anio, mes, 1) < date(self._hoy.year, self._hoy.month, 1) else "ABIERTO",
            ),
        )
        return int(cursor.lastrowid)

    def _asegurar_cargo_mensual(
        self,
        conexion: sqlite3.Connection,
        *,
        casa_id: int,
        abonado_id: int,
        periodo_id: int,
        anio: int,
        mes: int,
        descripcion: str,
        monto_centavos: int,
        saldo_pendiente_centavos: int,
        estado: str,
        origen: str,
    ) -> int:
        concepto_id = self._obtener_id_concepto(conexion, "SERVICIO_MENSUAL")
        fecha_vencimiento = fecha_periodo(anio, mes)[2]
        fila = conexion.execute(
            """
            SELECT id
            FROM cargos
            WHERE casa_id = ?
              AND periodo_id = ?
              AND concepto_id = ?
            LIMIT 1;
            """,
            (casa_id, periodo_id, concepto_id),
        ).fetchone()
        parametros = (
            casa_id,
            abonado_id,
            periodo_id,
            concepto_id,
            descripcion,
            monto_centavos,
            saldo_pendiente_centavos,
            fecha_vencimiento,
            estado,
            origen,
        )
        if fila is None:
            cursor = conexion.execute(
                """
                INSERT INTO cargos(
                    casa_id,
                    abonado_id,
                    periodo_id,
                    concepto_id,
                    descripcion,
                    monto_centavos,
                    saldo_pendiente_centavos,
                    fecha_vencimiento,
                    estado,
                    origen
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                parametros,
            )
            return int(cursor.lastrowid)
        cargo_id = int(fila["id"])
        conexion.execute(
            """
            UPDATE cargos
            SET abonado_id = ?,
                descripcion = ?,
                monto_centavos = ?,
                saldo_pendiente_centavos = ?,
                fecha_vencimiento = ?,
                estado = ?,
                origen = ?,
                actualizado_en = datetime('now', 'localtime'),
                anulado_en = NULL,
                anulado_por = NULL,
                motivo_anulacion = NULL
            WHERE id = ?;
            """,
            (
                abonado_id,
                descripcion,
                monto_centavos,
                saldo_pendiente_centavos,
                fecha_vencimiento,
                estado,
                origen,
                cargo_id,
            ),
        )
        return cargo_id

    def _asegurar_cargo_operativo(
        self,
        conexion: sqlite3.Connection,
        *,
        casa_id: int,
        abonado_id: int,
        concepto_codigo: str,
        descripcion: str,
        monto_centavos: int,
        saldo_pendiente_centavos: int,
        estado: str,
        origen: str,
        fecha_vencimiento: str,
        periodo_id: int | None = None,
    ) -> int:
        concepto_id = self._obtener_id_concepto(conexion, concepto_codigo)
        fila = conexion.execute(
            """
            SELECT id
            FROM cargos
            WHERE casa_id = ?
              AND concepto_id = ?
              AND descripcion = ?
            LIMIT 1;
            """,
            (casa_id, concepto_id, descripcion),
        ).fetchone()
        parametros = (
            casa_id,
            abonado_id,
            periodo_id,
            concepto_id,
            descripcion,
            monto_centavos,
            saldo_pendiente_centavos,
            fecha_vencimiento,
            estado,
            origen,
        )
        if fila is None:
            cursor = conexion.execute(
                """
                INSERT INTO cargos(
                    casa_id,
                    abonado_id,
                    periodo_id,
                    concepto_id,
                    descripcion,
                    monto_centavos,
                    saldo_pendiente_centavos,
                    fecha_vencimiento,
                    estado,
                    origen
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                parametros,
            )
            return int(cursor.lastrowid)
        cargo_id = int(fila["id"])
        conexion.execute(
            """
            UPDATE cargos
            SET abonado_id = ?,
                periodo_id = ?,
                monto_centavos = ?,
                saldo_pendiente_centavos = ?,
                fecha_vencimiento = ?,
                estado = ?,
                origen = ?,
                actualizado_en = datetime('now', 'localtime'),
                anulado_en = NULL,
                anulado_por = NULL,
                motivo_anulacion = NULL
            WHERE id = ?;
            """,
            (
                abonado_id,
                periodo_id,
                monto_centavos,
                saldo_pendiente_centavos,
                fecha_vencimiento,
                estado,
                origen,
                cargo_id,
            ),
        )
        return cargo_id

    def _asegurar_plan_reconexion(
        self,
        conexion: sqlite3.Connection,
        *,
        casa_id: int,
        observaciones: str,
    ) -> int:
        fila = conexion.execute(
            "SELECT id FROM planes_pago WHERE observaciones = ? LIMIT 1;",
            (observaciones,),
        ).fetchone()
        if fila is not None:
            return int(fila["id"])
        conexion.commit()
        resultado = self._servicio_planes.guardar(
            FormularioPlanPago(
                identificador=None,
                casa_id=casa_id,
                tipo_plan="RECONEXION",
                concepto_financiado="RECONEXION",
                prima_centavos=0,
                saldo_financiado_centavos=90000,
                cuota_regular_centavos=30000,
                cantidad_cuotas=3,
                estado="ACTIVO",
                observaciones=observaciones,
            ),
            actor_id=self._admin_id,
        )
        if not resultado.exito:
            raise RuntimeError(f"No fue posible crear el plan ESC-05: {resultado.mensaje}")
        fila = conexion.execute(
            "SELECT id FROM planes_pago WHERE observaciones = ? LIMIT 1;",
            (observaciones,),
        ).fetchone()
        if fila is None:
            raise RuntimeError("El plan ESC-05 no pudo recuperarse despues de crearse.")
        return int(fila["id"])

    def _configurar_cuotas_plan_reconexion(self, conexion: sqlite3.Connection, plan_id: int) -> None:
        cuotas = conexion.execute(
            """
            SELECT id, numero_cuota
            FROM cuotas_plan_pago
            WHERE plan_pago_id = ?
            ORDER BY numero_cuota ASC;
            """,
            (plan_id,),
        ).fetchall()
        if len(cuotas) < 3:
            raise RuntimeError("El plan ESC-05 no genero las tres cuotas esperadas.")
        configuracion = {
            1: ("PAGADO", 0, self._fecha_relativa(-45)),
            2: ("VENCIDO", 30000, self._fecha_relativa(-10)),
            3: ("PENDIENTE", 30000, self._fecha_relativa(20)),
        }
        for cuota in cuotas:
            numero = int(cuota["numero_cuota"])
            estado, saldo, fecha = configuracion[numero]
            conexion.execute(
                """
                UPDATE cuotas_plan_pago
                SET estado = ?,
                    saldo_pendiente_centavos = ?,
                    fecha_vencimiento = ?,
                    actualizado_en = datetime('now', 'localtime')
                WHERE id = ?;
                """,
                (estado, saldo, fecha, int(cuota["id"])),
            )
        conexion.execute(
            """
            UPDATE planes_pago
            SET cuotas_pagadas = 1,
                actualizado_en = datetime('now', 'localtime')
            WHERE id = ?;
            """,
            (plan_id,),
        )

    def _aplicar_cambio_dueno_si_falta(
        self,
        conexion: sqlite3.Connection,
        *,
        casa_id: int,
        nuevo_abonado_id: int,
        motivo: str,
        fecha_evento: str,
    ) -> None:
        fila = conexion.execute(
            """
            SELECT id
            FROM historial_propietarios_casa
            WHERE casa_id = ?
              AND motivo = ?
            LIMIT 1;
            """,
            (casa_id, motivo),
        ).fetchone()
        if fila is None:
            conexion.commit()
            resultado = self._servicio_casas.cambiar_dueno(
                casa_id=casa_id,
                nuevo_abonado_id=nuevo_abonado_id,
                motivo=motivo,
                actor_id=self._admin_id,
            )
            if not resultado.exito:
                raise RuntimeError(f"No fue posible aplicar cambio de dueno: {resultado.mensaje}")
        conexion.execute(
            """
            UPDATE historial_propietarios_casa
            SET fecha_cambio = ?
            WHERE casa_id = ?
              AND motivo = ?;
            """,
            (fecha_evento, casa_id, motivo),
        )

    def _alinear_responsable_actual(
        self,
        conexion: sqlite3.Connection,
        *,
        casa_id: int,
        abonado_id: int,
    ) -> None:
        conexion.execute(
            """
            UPDATE casas
            SET abonado_id = ?,
                actualizado_en = datetime('now', 'localtime')
            WHERE id = ?;
            """,
            (abonado_id, casa_id),
        )
        conexion.execute(
            """
            UPDATE cargos
            SET abonado_id = ?,
                actualizado_en = datetime('now', 'localtime')
            WHERE casa_id = ?
              AND anulado_en IS NULL
              AND estado IN ('PENDIENTE', 'PARCIAL', 'VENCIDO')
              AND saldo_pendiente_centavos > 0;
            """,
            (abonado_id, casa_id),
        )
        conexion.execute(
            """
            UPDATE planes_pago
            SET abonado_id = ?,
                actualizado_en = datetime('now', 'localtime')
            WHERE casa_id = ?
              AND estado = 'ACTIVO';
            """,
            (abonado_id, casa_id),
        )

    def _ajustar_fecha_pago(self, conexion: sqlite3.Connection, referencia: str, fecha_hora: str) -> None:
        fila = conexion.execute(
            """
            SELECT id
            FROM pagos
            WHERE referencia_externa = ?
            LIMIT 1;
            """,
            (referencia,),
        ).fetchone()
        if fila is None:
            return
        pago_id = int(fila["id"])
        conexion.execute(
            "UPDATE pagos SET fecha_pago = ?, actualizado_en = datetime('now', 'localtime') WHERE id = ?;",
            (fecha_hora, pago_id),
        )
        conexion.execute(
            "UPDATE comprobantes SET generado_en = ? WHERE pago_id = ?;",
            (fecha_hora, pago_id),
        )
        conexion.execute(
            "UPDATE pagos_detalle SET creado_en = ? WHERE pago_id = ?;",
            (fecha_hora, pago_id),
        )

    def _existe_pago_por_referencia(self, conexion: sqlite3.Connection, referencia: str) -> bool:
        fila = conexion.execute(
            "SELECT 1 FROM pagos WHERE referencia_externa = ? LIMIT 1;",
            (referencia,),
        ).fetchone()
        return fila is not None

    def _obtener_id_concepto(self, conexion: sqlite3.Connection, codigo: str) -> int:
        fila = conexion.execute(
            "SELECT id FROM conceptos_cobro WHERE codigo = ? LIMIT 1;",
            (codigo,),
        ).fetchone()
        if fila is None:
            raise RuntimeError(f"No existe el concepto {codigo}.")
        return int(fila["id"])

    def _obtener_id_usuario(self, conexion: sqlite3.Connection, nombre_usuario: str) -> int:
        fila = conexion.execute(
            "SELECT id FROM usuarios WHERE lower(nombre_usuario) = lower(?) LIMIT 1;",
            (nombre_usuario,),
        ).fetchone()
        if fila is None:
            raise RuntimeError(f"No existe el usuario actor {nombre_usuario}.")
        return int(fila["id"])

    def _obtener_id_metodo(self, conexion: sqlite3.Connection, codigo: str) -> int:
        fila = conexion.execute(
            "SELECT id FROM metodos_pago WHERE codigo = ? LIMIT 1;",
            (codigo,),
        ).fetchone()
        if fila is None:
            raise RuntimeError(f"No existe el metodo de pago {codigo}.")
        return int(fila["id"])

    def _fecha_relativa(self, dias: int) -> str:
        return (datetime.now().replace(microsecond=0) + timedelta(days=dias)).isoformat(sep=" ")

    def _mostrar_resumen(self, conexion: sqlite3.Connection) -> None:
        consulta = """
            SELECT
                printf('CA-%03d', c.id) AS casa_codigo,
                a.nombre_completo AS abonado,
                c.estado_servicio,
                COALESCE(b.nombre, '') AS barrio,
                c.observaciones
            FROM casas c
            INNER JOIN abonados a ON a.id = c.abonado_id
            LEFT JOIN barrios b ON b.id = c.barrio_id
            WHERE c.observaciones LIKE ?
            ORDER BY c.id;
        """
        filas = conexion.execute(consulta, (f"{MARCADOR}%",)).fetchall()
        print("Escenarios de pagos sembrados en la base local:")
        for fila in filas:
            print(
                f"- {fila['casa_codigo']} | {fila['abonado']} | {fila['estado_servicio']} | "
                f"{fila['barrio']} | {fila['observaciones']}"
            )


def main() -> None:
    sembrador = SembradorEscenariosPagos()
    sembrador.ejecutar()


if __name__ == "__main__":
    main()

