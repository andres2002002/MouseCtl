from __future__ import annotations

from collections.abc import Iterable
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class RatbagBusLike(Protocol):
    """Contrato mínimo que necesitan los modelos de `mousectl.models`.

    Los modelos dependen de esta abstracción, no de `RatbagBus` ni de
    `dbus-python` directamente (Dependency Inversion). Esto permite:
      - Testear los modelos con un doble de prueba en memoria, sin dbus-python
        instalado ni un bus de sistema real disponible.
      - Sustituir el transporte (por ejemplo, mock para tests de integración)
        sin tocar una sola línea de `models/`.
    """

    def object(self, path: str) -> Any: ...

    def properties(self, path: str) -> Any: ...

    def interface(self, path: str, iface: str) -> Any: ...

    def make_uint32(self, value: int, variant_level: int = 0) -> Any:
        """Envuelve un entero como uint32 del tipo nativo del transporte."""
        ...
    def make_array(self, values: Iterable[Any], signature: str, variant_level: int = 0) -> Any:
        """Envuelve una secuencia como array del tipo nativo del transporte."""
        ...

    def make_struct(self, values: Iterable[Any], signature: str | None = None, variant_level: int = 0) -> Any:
        """Envuelve una secuencia como struct del tipo nativo del transporte."""
        ...
