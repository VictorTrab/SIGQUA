"""Utilidades compartidas para hash y validacion de contrasenas."""

from __future__ import annotations

import hashlib
import hmac
import secrets


PREFIJO_HASH_SCRYPT = "scrypt"
LONGITUD_SAL_BYTES = 16
LONGITUD_HASH_BYTES = 64
PARAMETROS_SCRYPT = {
    "n": 16384,
    "r": 8,
    "p": 1,
    "dklen": LONGITUD_HASH_BYTES,
}


def validar_politica_contrasena(
    contrasena: str,
    confirmacion: str,
    *,
    nombre_usuario: str = "",
    correo: str = "",
) -> str | None:
    """Devuelve el primer incumplimiento de la politica o ``None``."""
    if not contrasena or not contrasena.strip():
        return "La contrasena no puede estar vacia ni contener solo espacios."
    if len(contrasena) < 8:
        return "La contrasena debe tener al menos 8 caracteres."
    if not any(caracter.isupper() for caracter in contrasena):
        return "La contrasena debe incluir una letra mayuscula."
    if not any(caracter.islower() for caracter in contrasena):
        return "La contrasena debe incluir una letra minuscula."
    if not any(caracter.isdigit() for caracter in contrasena):
        return "La contrasena debe incluir un numero."
    if not any(
        caracter.isprintable()
        and not caracter.isalnum()
        and not caracter.isspace()
        for caracter in contrasena
    ):
        return "La contrasena debe incluir un simbolo."
    if contrasena != confirmacion:
        return "Las contrasenas no coinciden."

    contrasena_comparable = contrasena.strip().casefold()
    if nombre_usuario.strip() and contrasena_comparable == nombre_usuario.strip().casefold():
        return "La contrasena no puede ser igual al nombre de usuario."
    if correo.strip() and contrasena_comparable == correo.strip().casefold():
        return "La contrasena no puede ser igual al correo."
    return None


def generar_hash_contrasena(contrasena_plana: str, sal: bytes | None = None) -> str:
    """Genera un hash scrypt versionado apto para persistencia."""
    sal_efectiva = sal or secrets.token_bytes(LONGITUD_SAL_BYTES)
    hash_contrasena = hashlib.scrypt(
        contrasena_plana.encode("utf-8"),
        salt=sal_efectiva,
        **PARAMETROS_SCRYPT,
    )
    return f"{PREFIJO_HASH_SCRYPT}${sal_efectiva.hex()}${hash_contrasena.hex()}"


def es_hash_scrypt_valido(hash_persistido: str) -> bool:
    """Indica si el valor persistido sigue el formato esperado."""
    partes = hash_persistido.split("$")
    return len(partes) == 3 and partes[0] == PREFIJO_HASH_SCRYPT


def verificar_contrasena(contrasena_plana: str, hash_persistido: str) -> bool:
    """Valida una contrasena plana contra un hash persistido."""
    if not es_hash_scrypt_valido(hash_persistido):
        return False

    _, sal_hexadecimal, hash_hexadecimal = hash_persistido.split("$", maxsplit=2)

    try:
        sal = bytes.fromhex(sal_hexadecimal)
        hash_esperado = bytes.fromhex(hash_hexadecimal)
    except ValueError:
        return False

    hash_actual = hashlib.scrypt(
        contrasena_plana.encode("utf-8"),
        salt=sal,
        **PARAMETROS_SCRYPT,
    )
    return hmac.compare_digest(hash_actual, hash_esperado)
