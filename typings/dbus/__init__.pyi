"""Stub mínimo para Pyright/mypy. `dbus-python` no publica anotaciones de
tipos y resuelve la mayoría de sus atributos dinámicamente en C, por lo que
el editor los marca como desconocidos. Este stub cubre únicamente la
superficie que usa `mousectl.dbus.bus.RatbagBus` (el único módulo del
proyecto que importa `dbus` directamente).

Si accedes a más símbolos de `dbus` desde `bus.py`, añádelos aquí.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from dbus import proxies as proxies

class SystemBus:
    def __init__(self, *args: Any, **kwargs: Any) -> None: ...
    def get_object(self, bus_name: str, object_path: str) -> proxies.ProxyObject: ...

class SessionBus:
    def __init__(self, *args: Any, **kwargs: Any) -> None: ...
    def get_object(self, bus_name: str, object_path: str) -> proxies.ProxyObject: ...

class Interface:
    def __init__(self, object: Any, dbus_interface: str) -> None: ...
    def __getattr__(self, name: str) -> Any: ...

class UInt32(int):
    def __new__(cls, value: int = ..., variant_level: int = ...) -> UInt32: ...

class Int32(int):
    def __new__(cls, value: int = ..., variant_level: int = ...) -> Int32: ...

class Boolean(int):
    def __new__(cls, value: int = ..., variant_level: int = ...) -> Boolean: ...

class String(str):
    def __new__(cls, value: str = ..., variant_level: int = ...) -> String: ...

class Struct(tuple[Any, ...]):
    def __new__(
        cls, iterable: Iterable[Any] = ..., signature: str | None = ..., variant_level: int = ...
    ) -> Struct: ...

class Array(list[Any]):
    def __init__(
        self, iterable: Iterable[Any] = ..., signature: str | None = ..., variant_level: int = ...
    ) -> None: ...
