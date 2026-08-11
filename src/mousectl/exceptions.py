from __future__ import annotations


class MousectlError(Exception):
    """Excepción base para errores de mousectl."""


class NoDevicesFoundError(MousectlError):
    """No se encontró ningún dispositivo ratbag en el bus."""


class DeviceNotFoundError(MousectlError):
    """No se encontró un dispositivo que coincida con el criterio dado."""


class MultipleDevicesFoundError(MousectlError):
    """Hay varios dispositivos y no se especificó cuál usar."""


class NoActiveProfileError(MousectlError):
    """El dispositivo no tiene ningún perfil activo."""


class InvalidColorError(MousectlError):
    """El color proporcionado no es válido."""


class InvalidValueError(MousectlError):
    """Un valor numérico proporcionado está fuera de rango."""


class InvalidLedModeError(MousectlError):
    """El modo de LED proporcionado no está soportado por el hardware."""


class WrongActionTypeError(MousectlError):
    """Se intentó leer/escribir un valor de mapeo que no corresponde al
    ActionType actual del botón (ej. leer `button_mapping` cuando el botón
    está mapeado a Special o Macro)."""
