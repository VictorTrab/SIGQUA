"""Backend seguro de respaldo local para SIGQUA."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from typing import Protocol
import zipfile

from comun.base_datos import GestorBaseDatos
from comun.configuracion.gestor_rutas import GestorRutas


FORMATO_FECHA_RESPALDO = "%Y-%m-%d %H:%M:%S"
NOMBRE_TAREA_RESPALDO = "SIGQUA-RespaldoAutomatico"
TIPOS_PROGRAMACION_VALIDOS = ("DESACTIVADO", "DIARIO", "SEMANAL")
DIAS_SEMANA_VALIDOS = ("LUNES", "MARTES", "MIERCOLES", "JUEVES", "VIERNES", "SABADO", "DOMINGO")


@dataclass(slots=True)
class ConfiguracionProgramacionRespaldo:
    """Parámetros simples de programación visibles para usuarios operativos."""

    tipo: str
    hora: str
    dia_semana: str


@dataclass(slots=True)
class ConfiguracionRespaldoLocal:
    """Configuración operativa del flujo de respaldo local."""

    ruta_principal: str
    ruta_secundaria: str
    secundaria_activa: bool
    comprimir_zip: bool
    organizar_por_periodo: bool
    retencion_dias: int
    programacion: ConfiguracionProgramacionRespaldo
    version_sistema: str


@dataclass(slots=True)
class DetalleRespaldoLocal:
    """Resultado técnico y operativo de un respaldo generado."""

    nombre_archivo: str
    ruta_archivo: str
    tamano_bytes: int
    hash_archivo: str
    tipo_respaldo: str
    estado: str
    generado_en: str
    observaciones: str = ""
    ruta_archivo_secundaria: str = ""


class RepositorioHistorialRespaldos(Protocol):
    """Contrato mínimo para registrar respaldos desde configuración."""

    def registrar_respaldo(
        self,
        nombre_archivo: str,
        ruta_archivo: str,
        tamano_bytes: int,
        hash_archivo: str,
        tipo_respaldo: str,
        estado: str,
        observaciones: str,
        generado_por: int | None = None,
    ) -> None:
        """Guarda el respaldo generado en historial_respaldos."""


class ProgramadorTareasWindows(Protocol):
    """Abstrae la interacción con el Programador de tareas."""

    def programar(self, configuracion: ConfiguracionProgramacionRespaldo, comando: str) -> None:
        """Crea o actualiza la tarea automática."""

    def quitar(self) -> None:
        """Elimina la tarea si existe."""

    def obtener_proxima_ejecucion(self) -> str:
        """Consulta la siguiente ejecución programada si existe."""


class ProgramadorTareasWindowsSchtasks:
    """Implementación simple basada en schtasks.exe sin .bat intermedio."""

    MAPA_DIAS = {
        "LUNES": "MON",
        "MARTES": "TUE",
        "MIERCOLES": "WED",
        "JUEVES": "THU",
        "VIERNES": "FRI",
        "SABADO": "SAT",
        "DOMINGO": "SUN",
    }

    def programar(self, configuracion: ConfiguracionProgramacionRespaldo, comando: str) -> None:
        tipo = configuracion.tipo.strip().upper()
        if tipo not in ("DIARIO", "SEMANAL"):
            raise ValueError("La programación automática solo admite DIARIO o SEMANAL.")

        argumentos = [
            "schtasks",
            "/create",
            "/f",
            "/tn",
            NOMBRE_TAREA_RESPALDO,
            "/tr",
            comando,
        ]
        if tipo == "DIARIO":
            argumentos.extend(["/sc", "daily", "/st", configuracion.hora])
        else:
            argumentos.extend(
                [
                    "/sc",
                    "weekly",
                    "/d",
                    self.MAPA_DIAS[configuracion.dia_semana.strip().upper()],
                    "/st",
                    configuracion.hora,
                ]
            )
        self._ejecutar(argumentos)

    def quitar(self) -> None:
        self._ejecutar(["schtasks", "/delete", "/f", "/tn", NOMBRE_TAREA_RESPALDO], tolerar_error=True)

    def obtener_proxima_ejecucion(self) -> str:
        resultado = subprocess.run(
            ["schtasks", "/query", "/tn", NOMBRE_TAREA_RESPALDO, "/fo", "list", "/v"],
            capture_output=True,
            text=True,
            check=False,
            shell=False,
        )
        if resultado.returncode != 0:
            return ""
        for linea in resultado.stdout.splitlines():
            if linea.lower().startswith("next run time".lower()):
                _, _, valor = linea.partition(":")
                return valor.strip()
        return ""

    @staticmethod
    def _ejecutar(argumentos: list[str], tolerar_error: bool = False) -> None:
        resultado = subprocess.run(
            argumentos,
            capture_output=True,
            text=True,
            check=False,
            shell=False,
        )
        if resultado.returncode != 0 and not tolerar_error:
            mensaje = (resultado.stderr or resultado.stdout or "No fue posible programar la tarea.").strip()
            raise RuntimeError(mensaje)


class ServicioRespaldoLocal:
    """Genera respaldos seguros de SQLite y administra su programación."""

    def __init__(
        self,
        gestor_base_datos: GestorBaseDatos,
        gestor_rutas: GestorRutas | None = None,
        programador_tareas: ProgramadorTareasWindows | None = None,
    ) -> None:
        self._gestor_base_datos = gestor_base_datos
        self._gestor_rutas = gestor_rutas or GestorRutas()
        self._programador_tareas = programador_tareas or ProgramadorTareasWindowsSchtasks()

    def validar_directorio_respaldo(self, ruta: str) -> tuple[bool, str]:
        ruta_normalizada = self._normalizar_directorio(Path(ruta).expanduser())
        if not str(ruta).strip():
            return False, "Selecciona una carpeta de respaldos."
        if ruta_normalizada.resolve() == self._gestor_rutas.obtener_ruta_base_datos().resolve():
            return False, "La carpeta de respaldo no puede ser el mismo archivo de base de datos."
        try:
            ruta_normalizada.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(prefix="sigqua_probe_", dir=ruta_normalizada, delete=False) as temporal:
                ruta_temporal = Path(temporal.name)
            ruta_temporal.unlink(missing_ok=True)
        except Exception:
            return False, "La carpeta seleccionada no está disponible para escritura."
        return True, ""

    def crear_respaldo_manual(
        self,
        configuracion: ConfiguracionRespaldoLocal,
        repositorio_historial: RepositorioHistorialRespaldos,
        generado_por: int | None = None,
        tipo_respaldo: str = "MANUAL",
    ) -> DetalleRespaldoLocal:
        ruta_principal = self._resolver_directorio_destino(
            configuracion.ruta_principal,
            configuracion.organizar_por_periodo,
        )
        ruta_secundaria = None
        if configuracion.secundaria_activa and configuracion.ruta_secundaria.strip():
            ruta_secundaria = self._resolver_directorio_destino(
                configuracion.ruta_secundaria,
                configuracion.organizar_por_periodo,
            )
        nombre_base = f"SIGQUA_RESPALDO_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        extension = ".zip" if configuracion.comprimir_zip else ".db"
        nombre_archivo = f"{nombre_base}{extension}"

        with tempfile.TemporaryDirectory(prefix="sigqua_respaldo_") as directorio_temporal:
            ruta_temporal_db = Path(directorio_temporal) / "sigqua.db"
            self._copiar_base_segura(ruta_temporal_db)
            self._validar_base_generada(ruta_temporal_db)

            manifiesto = {
                "nombre_archivo": nombre_archivo,
                "tipo_respaldo": tipo_respaldo,
                "generado_en": self._ahora_texto(),
                "version_sistema": configuracion.version_sistema,
                "origen_base_datos": str(self._gestor_rutas.obtener_ruta_base_datos()),
                "generado_por": generado_por,
            }

            if configuracion.comprimir_zip:
                ruta_temporal_final = Path(directorio_temporal) / nombre_archivo
                with zipfile.ZipFile(
                    ruta_temporal_final,
                    mode="w",
                    compression=zipfile.ZIP_DEFLATED,
                    allowZip64=True,
                ) as archivo_zip:
                    archivo_zip.write(ruta_temporal_db, arcname="sigqua.db")
                    archivo_zip.writestr(
                        "manifiesto.json",
                        json.dumps(manifiesto, ensure_ascii=True, indent=2),
                    )
            else:
                ruta_temporal_final = Path(directorio_temporal) / nombre_archivo
                shutil.copy2(ruta_temporal_db, ruta_temporal_final)

            tamano_bytes = ruta_temporal_final.stat().st_size
            hash_archivo = self._calcular_hash_archivo(ruta_temporal_final)
            manifiesto["tamano_bytes"] = tamano_bytes
            manifiesto["hash_archivo"] = hash_archivo

            ruta_final_principal = ruta_principal / nombre_archivo
            shutil.move(str(ruta_temporal_final), ruta_final_principal)
            ruta_final_secundaria = ""
            if ruta_secundaria is not None:
                ruta_secundaria_archivo = ruta_secundaria / nombre_archivo
                shutil.copy2(ruta_final_principal, ruta_secundaria_archivo)
                ruta_final_secundaria = str(ruta_secundaria_archivo)

        detalle = DetalleRespaldoLocal(
            nombre_archivo=nombre_archivo,
            ruta_archivo=str(ruta_final_principal),
            tamano_bytes=tamano_bytes,
            hash_archivo=hash_archivo,
            tipo_respaldo=tipo_respaldo,
            estado="GENERADO",
            generado_en=self._ahora_texto(),
            observaciones="Respaldo generado correctamente.",
            ruta_archivo_secundaria=ruta_final_secundaria,
        )
        repositorio_historial.registrar_respaldo(
            nombre_archivo=detalle.nombre_archivo,
            ruta_archivo=detalle.ruta_archivo,
            tamano_bytes=detalle.tamano_bytes,
            hash_archivo=detalle.hash_archivo,
            tipo_respaldo=detalle.tipo_respaldo,
            estado=detalle.estado,
            observaciones=detalle.observaciones,
            generado_por=generado_por,
        )
        self.aplicar_retencion(configuracion)
        return detalle

    def aplicar_retencion(self, configuracion: ConfiguracionRespaldoLocal) -> None:
        if configuracion.retencion_dias < 1:
            return
        limite = datetime.now() - timedelta(days=configuracion.retencion_dias)
        for ruta_base in filter(None, (configuracion.ruta_principal, configuracion.ruta_secundaria if configuracion.secundaria_activa else "")):
            directorio = Path(ruta_base).expanduser()
            if not directorio.exists():
                continue
            for archivo in directorio.rglob("SIGQUA_RESPALDO_*"):
                if not archivo.is_file():
                    continue
                if datetime.fromtimestamp(archivo.stat().st_mtime) < limite:
                    archivo.unlink(missing_ok=True)

    def programar_respaldo_windows(
        self,
        configuracion: ConfiguracionProgramacionRespaldo,
        comando: str,
    ) -> str:
        tipo = configuracion.tipo.strip().upper()
        if tipo == "DESACTIVADO":
            self.quitar_programacion_respaldo_windows()
            return ""
        self._validar_programacion(configuracion)
        self._programador_tareas.programar(configuracion, comando)
        return self._programador_tareas.obtener_proxima_ejecucion()

    def quitar_programacion_respaldo_windows(self) -> None:
        self._programador_tareas.quitar()

    def obtener_proxima_ejecucion_programada(self) -> str:
        return self._programador_tareas.obtener_proxima_ejecucion()

    def construir_comando_respaldo_programado(self) -> str:
        return (
            f'"{Path(sys.executable)}" '
            f'"{self._gestor_rutas.raiz_proyecto / "scripts" / "ejecutar_respaldo_automatico.py"}"'
        )

    def _copiar_base_segura(self, ruta_destino: Path) -> None:
        conexion_origen = self._gestor_base_datos.obtener_conexion()
        conexion_destino = sqlite3.connect(ruta_destino)
        try:
            conexion_origen.backup(conexion_destino)
        finally:
            conexion_destino.close()
            conexion_origen.close()

    @staticmethod
    def _validar_base_generada(ruta_base_datos: Path) -> None:
        conexion = sqlite3.connect(ruta_base_datos)
        try:
            resultado = conexion.execute("PRAGMA integrity_check;").fetchone()
            if not resultado or str(resultado[0]).lower() != "ok":
                raise RuntimeError("La copia de respaldo no superó la validación de integridad.")
        finally:
            conexion.close()

    @staticmethod
    def _calcular_hash_archivo(ruta_archivo: Path) -> str:
        acumulador = hashlib.sha256()
        with ruta_archivo.open("rb") as archivo:
            for bloque in iter(lambda: archivo.read(1024 * 1024), b""):
                acumulador.update(bloque)
        return acumulador.hexdigest()

    @staticmethod
    def _ahora_texto() -> str:
        return datetime.now().strftime(FORMATO_FECHA_RESPALDO)

    def _resolver_directorio_destino(self, ruta: str, organizar_por_periodo: bool) -> Path:
        directorio = self._normalizar_directorio(Path(ruta).expanduser())
        if organizar_por_periodo:
            ahora = datetime.now()
            directorio = directorio / f"{ahora:%Y}" / f"{ahora:%m}"
        directorio.mkdir(parents=True, exist_ok=True)
        return directorio

    def _normalizar_directorio(self, ruta: Path) -> Path:
        return ruta if ruta.is_absolute() else self._gestor_rutas.raiz_proyecto / ruta

    @staticmethod
    def _validar_programacion(configuracion: ConfiguracionProgramacionRespaldo) -> None:
        if configuracion.tipo not in TIPOS_PROGRAMACION_VALIDOS:
            raise ValueError("Selecciona un tipo de programación válido.")
        if len(configuracion.hora.strip()) != 5 or ":" not in configuracion.hora:
            raise ValueError("Define una hora válida para la programación automática.")
        if configuracion.tipo == "SEMANAL" and configuracion.dia_semana not in DIAS_SEMANA_VALIDOS:
            raise ValueError("Selecciona un día de semana válido para la programación automática.")
