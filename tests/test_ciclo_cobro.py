"""Pruebas del ciclo automatico de cobro mensual."""

from __future__ import annotations

from contextlib import closing
from datetime import date
from pathlib import Path
import shutil
import sqlite3

import pytest

from comun.base_datos import GestorBaseDatos
from comun.cobros import (
    ErrorCicloCobro,
    RepositorioCicloCobroSQLite,
    ServicioCicloCobro,
)
from comun.configuracion.gestor_rutas import GestorRutas
from modulos.pagos.servicio import ServicioPagos


def _crear_entorno(tmp_path: Path) -> tuple[GestorBaseDatos, Path]:
    directorio = tmp_path / "database"
    directorio.mkdir(parents=True)
    plantilla = Path(__file__).resolve().parents[1] / "database" / "sigqua_base.db"
    shutil.copy2(plantilla, directorio / "sigqua_base.db")
    gestor = GestorBaseDatos(GestorRutas(raiz_proyecto=tmp_path))
    ruta = gestor.inicializar_base_datos()
    return gestor, ruta


def _insertar_casa(
    conexion: sqlite3.Connection,
    *,
    sufijo: int,
    estado_servicio: str = "ACTIVO",
    estado_administrativo: str = "OPERATIVA",
    estado_abonado: str = "ACTIVO",
    fecha_inicio_cobro: str = "2026-05-15",
    eliminada: bool = False,
) -> int:
    barrio_id = conexion.execute(
        """
        INSERT INTO barrios(nombre, estado)
        VALUES (?, 'ACTIVO');
        """,
        (f"Barrio {sufijo}",),
    ).lastrowid
    abonado_id = conexion.execute(
        """
        INSERT INTO abonados(
            dni, nombre_completo, barrio_id, estado, fecha_alta
        )
        VALUES (?, ?, ?, ?, '2026-05-15');
        """,
        (f"08011990{sufijo:05d}", f"Abonado {sufijo}", barrio_id, estado_abonado),
    ).lastrowid
    casa_id = conexion.execute(
        """
        INSERT INTO casas(
            abonado_id,
            barrio_id,
            direccion_referencia,
            estado_servicio,
            estado_administrativo,
            fecha_alta,
            fecha_inicio_cobro,
            eliminado_en
        )
        VALUES (?, ?, ?, ?, ?, '2026-05-15', ?, ?);
        """,
        (
            abonado_id,
            barrio_id,
            f"Casa {sufijo}",
            estado_servicio,
            estado_administrativo,
            fecha_inicio_cobro,
            "2026-10-01" if eliminada else None,
        ),
    ).lastrowid
    return int(casa_id)


def test_genera_meses_hasta_fecha_actual_y_es_idempotente(tmp_path: Path) -> None:
    gestor, ruta = _crear_entorno(tmp_path)
    with closing(sqlite3.connect(ruta)) as conexion:
        with conexion:
            casa_activa = _insertar_casa(conexion, sufijo=1)
            _insertar_casa(conexion, sufijo=2, estado_servicio="CORTADO")
            _insertar_casa(conexion, sufijo=3, estado_administrativo="SUSPENDIDA")
            _insertar_casa(conexion, sufijo=4, estado_abonado="INACTIVO")
            _insertar_casa(conexion, sufijo=5, eliminada=True)

    servicio = ServicioCicloCobro(RepositorioCicloCobroSQLite(gestor))
    resultado = servicio.ejecutar(date(2026, 11, 15))
    repeticion = servicio.ejecutar(date(2026, 11, 15))

    assert resultado.periodos_creados == 6
    assert resultado.cargos_creados == 6
    assert repeticion.periodos_creados == 0
    assert repeticion.cargos_creados == 0

    with closing(sqlite3.connect(ruta)) as conexion:
        filas = conexion.execute(
            """
            SELECT pc.mes, c.estado, c.monto_centavos
            FROM cargos c
            INNER JOIN periodos_cobro pc ON pc.id = c.periodo_id
            WHERE c.casa_id = ?
            ORDER BY pc.mes;
            """,
            (casa_activa,),
        ).fetchall()
        total_otras = conexion.execute(
            "SELECT COUNT(*) FROM cargos WHERE casa_id != ?;",
            (casa_activa,),
        ).fetchone()[0]

    assert filas == [(6, "VENCIDO", 35000), (7, "VENCIDO", 35000), (8, "VENCIDO", 35000),
                     (9, "VENCIDO", 35000), (10, "VENCIDO", 35000), (11, "VENCIDO", 35000)]
    assert total_otras == 0


def test_preserva_adelantos_y_completa_huecos_cronologicos(tmp_path: Path) -> None:
    gestor, ruta = _crear_entorno(tmp_path)
    with closing(sqlite3.connect(ruta)) as conexion:
        conexion.row_factory = sqlite3.Row
        with conexion:
            casa_id = _insertar_casa(conexion, sufijo=10)
            abonado_id = conexion.execute(
                "SELECT abonado_id FROM casas WHERE id = ?;",
                (casa_id,),
            ).fetchone()["abonado_id"]
            concepto_id = conexion.execute(
                "SELECT id FROM conceptos_cobro WHERE codigo = 'SERVICIO_MENSUAL';"
            ).fetchone()["id"]
            for mes in (6, 7):
                periodo_id = conexion.execute(
                    """
                    INSERT INTO periodos_cobro(
                        anio, mes, nombre, fecha_inicio, fecha_fin, fecha_vencimiento
                    )
                    VALUES (2026, ?, ?, ?, ?, ?);
                    """,
                    (
                        mes,
                        f"Periodo {mes:02d}/2026",
                        f"2026-{mes:02d}-01",
                        f"2026-{mes:02d}-30",
                        f"2026-{mes:02d}-10",
                    ),
                ).lastrowid
                conexion.execute(
                    """
                    INSERT INTO cargos(
                        casa_id, abonado_id, periodo_id, concepto_id, descripcion,
                        monto_centavos, saldo_pendiente_centavos,
                        fecha_generacion, fecha_vencimiento, estado, origen
                    )
                    VALUES (?, ?, ?, ?, ?, 35000, 0, ?, ?, 'PAGADO', 'ADELANTO');
                    """,
                    (
                        casa_id,
                        abonado_id,
                        periodo_id,
                        concepto_id,
                        f"Adelanto {mes:02d}/2026",
                        "2026-05-20",
                        f"2026-{mes:02d}-10",
                    ),
                )

    ServicioCicloCobro(RepositorioCicloCobroSQLite(gestor)).ejecutar(date(2026, 11, 5))

    with closing(sqlite3.connect(ruta)) as conexion:
        filas = conexion.execute(
            """
            SELECT pc.mes, c.estado, c.origen
            FROM cargos c
            INNER JOIN periodos_cobro pc ON pc.id = c.periodo_id
            WHERE c.casa_id = ?
            ORDER BY pc.mes;
            """,
            (casa_id,),
        ).fetchall()

    assert filas == [
        (6, "PAGADO", "ADELANTO"),
        (7, "PAGADO", "ADELANTO"),
        (8, "VENCIDO", "MENSUAL"),
        (9, "VENCIDO", "MENSUAL"),
        (10, "VENCIDO", "MENSUAL"),
        (11, "PENDIENTE", "MENSUAL"),
    ]


def test_reactivacion_reinicia_cobro_y_actualiza_vencimientos(tmp_path: Path) -> None:
    gestor, ruta = _crear_entorno(tmp_path)
    with closing(sqlite3.connect(ruta)) as conexion:
        conexion.row_factory = sqlite3.Row
        with conexion:
            casa_id = _insertar_casa(
                conexion,
                sufijo=20,
                fecha_inicio_cobro="2026-10-20",
            )
            abonado_id = conexion.execute(
                "SELECT abonado_id FROM casas WHERE id = ?;",
                (casa_id,),
            ).fetchone()["abonado_id"]
            plan_id = conexion.execute(
                """
                INSERT INTO planes_pago(
                    abonado_id, casa_id, fecha_inicio, fecha_fin,
                    monto_total_centavos, cuota_regular_centavos,
                    cantidad_cuotas, estado, tipo_plan, concepto_financiado
                )
                VALUES (?, ?, '2026-10-01', '2026-12-01', 70000, 35000, 2,
                        'ACTIVO', 'RECONEXION', 'RECONEXION');
                """,
                (abonado_id, casa_id),
            ).lastrowid
            conexion.execute(
                """
                INSERT INTO cuotas_plan_pago(
                    plan_pago_id, numero_cuota, fecha_vencimiento,
                    monto_centavos, saldo_pendiente_centavos, estado
                )
                VALUES (?, 1, '2026-10-10', 35000, 15000, 'PARCIAL');
                """,
                (plan_id,),
            )

    resultado = ServicioCicloCobro(
        RepositorioCicloCobroSQLite(gestor)
    ).ejecutar(date(2026, 11, 5))

    with closing(sqlite3.connect(ruta)) as conexion:
        meses = conexion.execute(
            """
            SELECT pc.mes, c.estado
            FROM cargos c
            INNER JOIN periodos_cobro pc ON pc.id = c.periodo_id
            WHERE c.casa_id = ?;
            """,
            (casa_id,),
        ).fetchall()
        estado_cuota = conexion.execute(
            "SELECT estado FROM cuotas_plan_pago WHERE plan_pago_id = ?;",
            (plan_id,),
        ).fetchone()[0]

    assert meses == [(11, "PENDIENTE")]
    assert resultado.cuotas_vencidas == 1
    assert estado_cuota == "VENCIDO"


def test_vencimiento_no_modifica_adelantos_ni_otros_conceptos(tmp_path: Path) -> None:
    gestor, ruta = _crear_entorno(tmp_path)
    with closing(sqlite3.connect(ruta)) as conexion:
        conexion.row_factory = sqlite3.Row
        with conexion:
            casa_id = _insertar_casa(
                conexion,
                sufijo=30,
                fecha_inicio_cobro="2026-12-01",
            )
            abonado_id = conexion.execute(
                "SELECT abonado_id FROM casas WHERE id = ?;",
                (casa_id,),
            ).fetchone()["abonado_id"]
            periodo_id = conexion.execute(
                """
                INSERT INTO periodos_cobro(
                    anio, mes, nombre, fecha_inicio, fecha_fin, fecha_vencimiento
                )
                VALUES (2026, 6, 'Periodo 06/2026', '2026-06-01',
                        '2026-06-30', '2026-06-10');
                """
            ).lastrowid
            mensual_id = conexion.execute(
                "SELECT id FROM conceptos_cobro WHERE codigo = 'SERVICIO_MENSUAL';"
            ).fetchone()["id"]
            conexion_id = conexion.execute(
                "SELECT id FROM conceptos_cobro WHERE codigo = 'CONEXION';"
            ).fetchone()["id"]
            for concepto_id, origen, descripcion in (
                (mensual_id, "ADELANTO", "Adelanto protegido"),
                (conexion_id, "MANUAL", "Conexion protegida"),
            ):
                conexion.execute(
                    """
                    INSERT INTO cargos(
                        casa_id, abonado_id, periodo_id, concepto_id, descripcion,
                        monto_centavos, saldo_pendiente_centavos,
                        fecha_generacion, fecha_vencimiento, estado, origen
                    )
                    VALUES (?, ?, ?, ?, ?, 35000, 35000, '2026-06-01',
                            '2026-06-10', 'PENDIENTE', ?);
                    """,
                    (casa_id, abonado_id, periodo_id, concepto_id, descripcion, origen),
                )

    ServicioCicloCobro(RepositorioCicloCobroSQLite(gestor)).ejecutar(date(2026, 11, 15))

    with closing(sqlite3.connect(ruta)) as conexion:
        estados = conexion.execute(
            "SELECT descripcion, estado FROM cargos ORDER BY descripcion;"
        ).fetchall()

    assert estados == [
        ("Adelanto protegido", "PENDIENTE"),
        ("Conexion protegida", "PENDIENTE"),
    ]


def test_fallo_de_configuracion_se_expone_como_error_tipado(tmp_path: Path) -> None:
    gestor, ruta = _crear_entorno(tmp_path)
    with closing(sqlite3.connect(ruta)) as conexion:
        with conexion:
            conexion.execute(
                """
                UPDATE configuracion_sistema
                SET valor = '0'
                WHERE clave = 'cobro.precio_mensual_centavos';
                """
            )

    with pytest.raises(ErrorCicloCobro):
        ServicioCicloCobro(RepositorioCicloCobroSQLite(gestor)).ejecutar(
            date(2026, 11, 5)
        )


def test_modulo_financiero_no_consulta_si_el_ciclo_falla() -> None:
    class CicloFallido:
        def ejecutar(self) -> None:
            raise ErrorCicloCobro("Ciclo no disponible.")

    servicio = ServicioPagos(
        repositorio_pagos=object(),
        servicio_comprobantes=object(),
        servicio_ciclo_cobro=CicloFallido(),
    )

    with pytest.raises(ErrorCicloCobro, match="Ciclo no disponible"):
        servicio.obtener_estado()
