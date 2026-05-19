"""Utilidades compartidas para resolver identidad institucional configurable."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(slots=True)
class IdentidadEmpresaConfigurada:
    """Identidad institucional genérica visible en documentos y cabeceras."""

    nombre: str
    telefono: str
    correo: str
    direccion: str
    identificador_fiscal: str = ""
    sitio_web: str = ""
    mensaje_contacto: str = ""


CLAVES_IDENTIDAD_EMPRESA = (
    "empresa.nombre",
    "empresa.telefono",
    "empresa.correo",
    "empresa.direccion",
    "empresa.identificador_fiscal",
    "empresa.sitio_web",
    "empresa.mensaje_contacto",
)

CLAVES_IDENTIDAD_LEGADAS_JUNTA = (
    "junta.nombre",
    "junta.telefono",
    "junta.correo",
    "junta.direccion",
    "junta.identificador_fiscal",
    "junta.sitio_web",
    "junta.mensaje_contacto",
)


def construir_identidad_empresa(
    parametros: Mapping[str, object],
    nombre_predeterminado: str = "SICAP",
) -> IdentidadEmpresaConfigurada:
    """Resuelve identidad moderna con compatibilidad hacia claves legadas."""

    return IdentidadEmpresaConfigurada(
        nombre=_resolver_valor(parametros, "empresa.nombre", "junta.nombre", nombre_predeterminado),
        telefono=_resolver_valor(parametros, "empresa.telefono", "junta.telefono"),
        correo=_resolver_valor(parametros, "empresa.correo", "junta.correo"),
        direccion=_resolver_valor(parametros, "empresa.direccion", "junta.direccion"),
        identificador_fiscal=_resolver_valor(
            parametros,
            "empresa.identificador_fiscal",
            "junta.identificador_fiscal",
        ),
        sitio_web=_resolver_valor(parametros, "empresa.sitio_web", "junta.sitio_web"),
        mensaje_contacto=_resolver_valor(
            parametros,
            "empresa.mensaje_contacto",
            "junta.mensaje_contacto",
        ),
    )


def _resolver_valor(
    parametros: Mapping[str, object],
    clave_empresa: str,
    clave_legada: str,
    predeterminado: str = "",
) -> str:
    valor_empresa = _normalizar_valor(parametros.get(clave_empresa))
    if valor_empresa:
        return valor_empresa
    valor_legado = _normalizar_valor(parametros.get(clave_legada))
    if valor_legado:
        return valor_legado
    return predeterminado


def _normalizar_valor(valor: object) -> str:
    if valor is None:
        return ""
    if hasattr(valor, "valor"):
        return str(getattr(valor, "valor") or "").strip()
    return str(valor or "").strip()
