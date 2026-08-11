from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import pytest


class FakeProperties:
    """Sustituye a `dbus.Interface(obj, IFACE_PROPERTIES)`."""

    def __init__(self, store: dict[str, Any]) -> None:
        self._store = store

    def Get(self, iface: str, name: str) -> Any:  # noqa: N802 (respeta la API DBus)
        return self._store[name]

    def Set(self, iface: str, name: str, value: Any) -> None:  # noqa: N802
        self._store[name] = value


class FakeInterface:
    """Sustituye a `dbus.Interface(obj, iface)` para llamadas a métodos.

    Cualquier atributo accedido se resuelve como un método que registra
    la llamada en `bus.calls` para poder aserirla en los tests.
    """

    def __init__(self, bus: FakeRatbagBus, path: str) -> None:
        self._bus = bus
        self._path = path

    def __getattr__(self, name: str) -> Any:
        def _record(*args: Any) -> None:
            self._bus.calls.append((self._path, name, args))

        return _record


class FakeRatbagBus:
    """Doble de prueba de `RatbagBusLike` que no toca DBus ni requiere
    dbus-python instalado. Guarda propiedades en memoria por `path` y
    registra las llamadas a métodos para verificarlas en los asserts.
    """

    def __init__(self) -> None:
        self._properties: dict[str, dict[str, Any]] = {}
        self.calls: list[tuple[str, str, tuple[Any, ...]]] = []

    def register(self, path: str, properties: dict[str, Any]) -> None:
        """Da de alta un objeto simulado en `path` con sus propiedades iniciales."""
        self._properties[path] = dict(properties)

    def object(self, path: str) -> Any:
        return path

    def properties(self, path: str) -> FakeProperties:
        return FakeProperties(self._properties[path])

    def interface(self, path: str, iface: str) -> FakeInterface:
        return FakeInterface(self, path)

    def make_uint32(self, value: int, variant_level: int = 0) -> int:
        return int(value)

    def make_struct(self, values: Iterable[Any], signature: str | None = None, variant_level: int = 0) -> tuple[Any, ...]:
        return tuple(values)


@pytest.fixture
def fake_bus() -> FakeRatbagBus:
    return FakeRatbagBus()
