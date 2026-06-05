"""Backend seguro de respaldo local para SIGQUA."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import tempfile
from typing import Protocol
import zipfile

from comun.base_datos import GestorBaseDatos
from comun.configuracion.gestor_rutas import GestorRutas


FORMATO_FECHA_RESPALDO = "%Y-%m-%d %H:%M:%S"


@dataclass(slots=True)
class ConfiguracionRespaldoLocal:
    """Configuracion operativa del flujo de respaldo local."""

    ruta_principal: str
    ruta_secundaria: str
    secundaria_activa: bool
    comprimir_zip: bool
    organizar_por_periodo: bool
    retencion_maxima: int
    version_sistema: str


@dataclass(slots=True)
class DetalleRespaldoLocal:
    """Resultado tecnico y operativo de un respaldo generado."""

    nombre_archivo: str
    ruta_archivo: str
    tamano_bytes: int
    hash_archivo: str
    tipo_respaldo: str
    estado: str
    generado_en: str
    observaciones: str = ""
    ruta_archivo_secundaria: str = ""


@dataclass(slots=True)
class ResultadoRestauracionLocal:
    """Resultado tecnico de una restauracion de respaldo."""

    nombre_archivo: str
    ruta_archivo: str
    respaldo_seguridad: str
    estado: str
    observaciones: str


class RepositorioHistorialRespaldos(Protocol):
    """Contrato minimo para registrar respaldos desde configuracion."""

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


class ServicioRespaldoLocal:
    """Genera respaldos seguros de SQLite."""

    def __init__(
        self,
        gestor_base_datos: GestorBaseDatos,
        gestor_rutas: GestorRutas | None = None,
    ) -> None:
        self._gestor_base_datos = gestor_base_datos
        self._gestor_rutas = gestor_rutas or GestorRutas()

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
            return False, "La carpeta seleccionada no esta disponible para escritura."
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
        if configuracion.retencion_maxima < 1:
            return
        rutas = (
            configuracion.ruta_principal,
            configuracion.ruta_secundaria if configuracion.secundaria_activa else "",
        )
        for ruta_base in filter(None, rutas):
            directorio = Path(ruta_base).expanduser()
            if not directorio.exists():
                continue
            archivos = sorted(
                (
                    archivo
                    for archivo in directorio.rglob("SIGQUA_RESPALDO_*")
                    if archivo.is_file() and archivo.suffix.lower() in {".zip", ".db"}
                ),
                key=lambda archivo: archivo.stat().st_mtime,
                reverse=True,
            )
            for archivo in archivos[configuracion.retencion_maxima :]:
                archivo.unlink(missing_ok=True)

    def restaurar_respaldo(
        self,
        ruta_respaldo: str,
        hash_esperado: str,
        configuracion: ConfiguracionRespaldoLocal,
        repositorio_historial: RepositorioHistorialRespaldos,
        generado_por: int | None = None,
    ) -> ResultadoRestauracionLocal:
        ruta_origen = Path(ruta_respaldo).expanduser()
        if not ruta_origen.exists() or not ruta_origen.is_file():
            raise FileNotFoundError("El archivo de respaldo registrado no existe.")

        hash_actual = self._calcular_hash_archivo(ruta_origen)
        if hash_esperado.strip() and hash_actual.lower() != hash_esperado.strip().lower():
            raise ValueError("El hash del respaldo no coincide con el historial.")

        with tempfile.TemporaryDirectory(prefix="sigqua_restauracion_") as directorio_temporal:
            ruta_temporal_db = Path(directorio_temporal) / "sigqua_restaurada.db"
            self._extraer_base_respaldo(ruta_origen, ruta_temporal_db)
            self._validar_base_generada(ruta_temporal_db)

            respaldo_seguridad = self.crear_respaldo_manual(
                configuracion=configuracion,
                repositorio_historial=repositorio_historial,
                generado_por=generado_por,
                tipo_respaldo="PRE_MANTENIMIENTO",
            )
            ruta_base_datos = self._gestor_rutas.obtener_ruta_base_datos()
            ruta_base_datos.parent.mkdir(parents=True, exist_ok=True)
            self._reemplazar_base_datos(ruta_temporal_db, ruta_base_datos)

        return ResultadoRestauracionLocal(
            nombre_archivo=ruta_origen.name,
            ruta_archivo=str(ruta_origen),
            respaldo_seguridad=respaldo_seguridad.ruta_archivo,
            estado="RESTAURADO",
            observaciones="Base restaurada correctamente. Reinicia SIGQUA para recargar la sesion.",
        )

    @staticmethod
    def _extraer_base_respaldo(ruta_origen: Path, ruta_destino: Path) -> None:
        if ruta_origen.suffix.lower() == ".zip":
            with zipfile.ZipFile(ruta_origen, "r") as archivo_zip:
                nombres = set(archivo_zip.namelist())
                if "sigqua.db" not in nombres:
                    raise ValueError("El ZIP de respaldo no contiene sigqua.db.")
                with archivo_zip.open("sigqua.db", "r") as origen, ruta_destino.open("wb") as destino:
                    shutil.copyfileobj(origen, destino)
            return
        if ruta_origen.suffix.lower() == ".db":
            shutil.copy2(ruta_origen, ruta_destino)
            return
        raise ValueError("El respaldo debe ser un archivo .zip o .db generado por SIGQUA.")

    def _copiar_base_segura(self, ruta_destino: Path) -> None:
        conexion_origen = self._gestor_base_datos.obtener_conexion()
        conexion_destino = sqlite3.connect(ruta_destino)
        try:
            conexion_origen.backup(conexion_destino)
        finally:
            conexion_destino.close()
            conexion_origen.close()

    def _reemplazar_base_datos(self, ruta_origen: Path, ruta_base_datos: Path) -> None:
        self._cerrar_estado_sqlite_pendiente(ruta_base_datos)
        conexion_origen = sqlite3.connect(ruta_origen)
        conexion_destino = sqlite3.connect(ruta_base_datos)
        try:
            conexion_origen.backup(conexion_destino)
            conexion_destino.execute("PRAGMA wal_checkpoint(TRUNCATE);")
        finally:
            conexion_destino.close()
            conexion_origen.close()
        self._validar_base_generada(ruta_base_datos)

    @staticmethod
    def _cerrar_estado_sqlite_pendiente(ruta_base_datos: Path) -> None:
        if not ruta_base_datos.exists():
            return
        conexion = sqlite3.connect(ruta_base_datos)
        try:
            conexion.execute("PRAGMA wal_checkpoint(TRUNCATE);")
        finally:
            conexion.close()

    @staticmethod
    def _validar_base_generada(ruta_base_datos: Path) -> None:
        conexion = sqlite3.connect(ruta_base_datos)
        try:
            resultado = conexion.execute("PRAGMA integrity_check;").fetchone()
            if not resultado or str(resultado[0]).lower() != "ok":
                raise RuntimeError("La copia de respaldo no supero la validacion de integridad.")
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
