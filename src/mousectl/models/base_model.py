from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar


class BaseSchema(ABC):
    """Schema base para modelos ratbag."""

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """Convierte el objeto a un diccionario."""
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def from_dict(cls, data: dict[str, Any]) -> BaseSchema:
        """Crea un schema a partir de un diccionario."""
        raise NotImplementedError


SchemaT = TypeVar("SchemaT", bound=BaseSchema)


class BaseModel(ABC, Generic[SchemaT]):
    """Interfaz genérica para modelos respaldados por una configuración especifica."""

    @abstractmethod
    def snapshot(self) -> SchemaT:
        """Obtiene una configuración del estado actual."""
        raise NotImplementedError

    @abstractmethod
    def apply(self, config: SchemaT) -> None:
        """Aplica una configuración al modelo."""
        raise NotImplementedError
