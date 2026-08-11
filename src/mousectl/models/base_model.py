from __future__ import annotations
from typing import Any
from abc import ABC, abstractmethod
from typing import Any


class BaseConfig(ABC):
    """Configuración serializable de un modelo ratbag."""

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """Convierte la configuración a un diccionario."""
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def from_dict(cls, data: dict[str, Any]) -> "BaseConfig":
        """Crea una configuración a partir de un diccionario."""
        raise NotImplementedError


class BaseModel(ABC):
    """Interfaz para modelos que pueden guardar y aplicar configuración."""

    @abstractmethod
    def snapshot(self) -> BaseConfig:
        """Crea una copia inmutable del estado actual."""
        raise NotImplementedError

    @abstractmethod
    def apply(self, target: BaseConfig) -> None:
        """Aplica una configuración al objeto."""
        raise NotImplementedError