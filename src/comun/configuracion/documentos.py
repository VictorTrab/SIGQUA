"""Helpers documentales compartidos por reportes y tickets."""

from __future__ import annotations

from typing import Protocol


class ConfiguracionEncabezadoDocumental(Protocol):
    nombre_junta: str
    telefono_junta: str
    correo_junta: str
    direccion_junta: str
    identificador_fiscal: str
    sitio_web: str
    mensaje_contacto: str
    mostrar_correo: bool
    mostrar_telefono: bool
    mostrar_direccion: bool
    mostrar_identificador_fiscal: bool


def lineas_encabezado_documental(configuracion: ConfiguracionEncabezadoDocumental) -> tuple[str, ...]:
    """Compone lineas visibles de identidad sin depender de un backend documental."""

    lineas: list[str] = []
    if configuracion.nombre_junta.strip():
        lineas.append(configuracion.nombre_junta.strip())
    if configuracion.mostrar_identificador_fiscal and configuracion.identificador_fiscal.strip():
        lineas.append(f"ID fiscal: {configuracion.identificador_fiscal.strip()}")
    if configuracion.mostrar_telefono and configuracion.telefono_junta.strip():
        lineas.append(configuracion.telefono_junta.strip())
    if configuracion.mostrar_correo and configuracion.correo_junta.strip():
        lineas.append(configuracion.correo_junta.strip())
    if configuracion.mostrar_direccion and configuracion.direccion_junta.strip():
        lineas.append(configuracion.direccion_junta.strip())
    if configuracion.sitio_web.strip():
        lineas.append(configuracion.sitio_web.strip())
    if configuracion.mensaje_contacto.strip():
        lineas.append(configuracion.mensaje_contacto.strip())
    return tuple(lineas or ("Empresa no configurada",))
