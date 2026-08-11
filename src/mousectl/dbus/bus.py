from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import dbus
from dbus_fast import Variant

from mousectl.dbus.constants import BUS_NAME, IFACE_INTROSPECTABLE, IFACE_PROPERTIES


class RatbagBus:
    """Wrapper sobre el bus de sistema DBus para el servicio ratbagd.

    Es la ÚNICA clase del proyecto que importa `dbus-python` directamente.
    Centraliza la obtención de proxies e interfaces, y el marshalling a tipos
    DBus concretos (`make_uint32`/`make_struct`), para que `models/` dependa
    solo del protocolo `RatbagBusLike` y sea testable sin dbus-python instalado.
    """

    def __init__(self) -> None:
        self._bus = dbus.SystemBus()

    @property
    def raw(self) -> dbus.SystemBus:
        return self._bus

    def object(self, path: str) -> dbus.proxies.ProxyObject:
        return self._bus.get_object(BUS_NAME, path)

    def properties(self, path: str) -> dbus.Interface:
        return dbus.Interface(self.object(path), IFACE_PROPERTIES)

    def introspect(self, path: str) -> dbus.Interface:
        return dbus.Interface(self.object(path), IFACE_INTROSPECTABLE)

    def interface(self, path: str, iface: str) -> dbus.Interface:
        return dbus.Interface(self.object(path), iface)

    def make_uint32(self, value: int, variant_level: int = 0) -> dbus.UInt32:
        return dbus.UInt32(value, variant_level=variant_level)

    def make_array(self, values: Iterable[Any], signature: str, variant_level: int = 0) -> dbus.Array:
        return dbus.Array(tuple(values), signature=signature, variant_level=variant_level)

    def make_struct(self, values: Iterable[Any], signature: str | None = None, variant_level: int = 0) -> dbus.Struct:
        return dbus.Struct(tuple(values), signature=signature, variant_level=variant_level)

