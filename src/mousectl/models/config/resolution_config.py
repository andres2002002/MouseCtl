
from dataclasses import dataclass
from typing import Any
from mousectl.models.base_model import BaseConfig

@dataclass(frozen=True, slots=True)
class ResolutionConfig(BaseConfig):
    """Snapshot de un preset de DPI (solo el valor, no el estado
    activo/default — esos son punteros de perfil, no algo que tenga
    sentido copiar/cargar a otro slot)."""

    x: int
    y: int

    def to_dict(self) -> dict[str, Any]:
        return {"x": self.x, "y": self.y}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ResolutionConfig":
        return cls(x=int(data["x"]), y=int(data["y"]))
