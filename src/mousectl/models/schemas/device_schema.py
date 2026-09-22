from dataclasses import dataclass
from typing import Any

from mousectl.models.base_model import BaseSchema
from mousectl.models.schemas.profile_schema import ProfileSchema


@dataclass(frozen=True, slots=True)
class DeviceSchema(BaseSchema):
    """Snapshot de varios perfiles de un dispositivo, indexado por índice de
    perfil (no por posición en la lista) para tolerar perfiles deshabilitados
    entre guardar y cargar."""

    profiles: dict[int, ProfileSchema]

    def to_dict(self) -> dict[str, Any]:
        return {
            "profiles": {str(index): config.to_dict() for index, config in self.profiles.items()}
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DeviceSchema":
        return cls(
            profiles={
                int(index): ProfileSchema.from_dict(config)
                for index, config in data["profiles"].items()
            }
        )
