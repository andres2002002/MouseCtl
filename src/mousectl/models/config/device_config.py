from dataclasses import dataclass
from typing import Any

from mousectl.models.base_model import BaseConfig
from mousectl.models.config.profile_config import ProfileConfig


@dataclass(frozen=True, slots=True)
class DeviceConfig(BaseConfig):
    """Snapshot de varios perfiles de un dispositivo, indexado por índice de
    perfil (no por posición en la lista) para tolerar perfiles deshabilitados
    entre guardar y cargar."""

    profiles: dict[int, ProfileConfig]

    def to_dict(self) -> dict[str, Any]:
        return {
            "profiles": {str(index): config.to_dict() for index, config in self.profiles.items()}
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DeviceConfig":
        return cls(
            profiles={
                int(index): ProfileConfig.from_dict(config)
                for index, config in data["profiles"].items()
            }
        )
