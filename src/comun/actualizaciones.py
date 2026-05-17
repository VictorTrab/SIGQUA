"""Infraestructura minima de refresco interno entre modulos."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QObject, Signal


@dataclass(frozen=True, slots=True)
class EventoModuloActualizado:
    """Evento semantico emitido cuando un modulo cambia datos visibles."""

    modulo_origen: str
    modulos_afectados: tuple[str, ...]
    mensaje: str = "Informacion actualizada."


class BusActualizacionesModulos(QObject):
    """Bus simple de actualizaciones internas sin polling ni watchers."""

    actualizacion_emitida = Signal(object)

    def emitir(
        self,
        modulo_origen: str,
        modulos_afectados: tuple[str, ...],
        mensaje: str = "Informacion actualizada.",
    ) -> None:
        self.actualizacion_emitida.emit(
            EventoModuloActualizado(
                modulo_origen=modulo_origen,
                modulos_afectados=tuple(modulos_afectados),
                mensaje=mensaje,
            )
        )


bus_actualizaciones_modulos = BusActualizacionesModulos()

