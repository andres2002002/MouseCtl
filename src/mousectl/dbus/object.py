from __future__ import annotations

import logging
from typing import Any, ClassVar

from mousectl.dbus.protocol import RatbagBusLike

logger = logging.getLogger(__name__)

class RatbagObject:
    """Clase base para envolver un objeto expuesto por ratbagd.

    Cada subclase (Device, Profile, Resolution, Button, Led) solo declara su
    `interface_name` y expone propiedades tipadas encima de `_get`/`_set`/`_call`.
    Evita repetir el patrón `dbus.Interface(...).Get(iface, name)` en cada modelo.

    Depende de `RatbagBusLike` (protocolo), no de `RatbagBus` (implementación
    concreta con dbus-python) — así se puede instanciar con un doble de
    prueba en los tests unitarios.
    """

    interface_name: ClassVar[str] = ""

    def __init__(self, bus: RatbagBusLike, path: str) -> None:
        self._bus = bus
        self._path = path

    @property
    def bus(self) -> RatbagBusLike:
        return self._bus

    @property
    def path(self) -> str:
        return self._path

    def _get(self, name: str) -> Any:
        try:
            return self._bus.properties(self._path).Get(self.interface_name, name)
        except Exception as e:
            logger.error("Error getting property %s: %s", name, e)
            raise

    def _set(self, name: str, value: Any) -> None:
        try:
            self._bus.properties(self._path).Set(self.interface_name, name, value)
        except Exception as e:
            logger.error("Error setting property %s: %s", name, e)
            raise

    def _call(self, method: str, *args: Any) -> Any:
        interface = self._bus.interface(self._path, self.interface_name)
        return getattr(interface, method)(*args)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, RatbagObject):
            return NotImplemented
        return self._path == other._path

    def __hash__(self) -> int:
        return hash(self._path)
