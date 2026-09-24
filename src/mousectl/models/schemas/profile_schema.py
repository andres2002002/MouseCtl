from dataclasses import dataclass, field
from typing import Any

from mousectl.models.base_model import BaseSchema
from mousectl.models.schemas.button_schema import ButtonSchema
from mousectl.models.schemas.led_schema import LedSchema
from mousectl.models.schemas.resolution_schema import ResolutionSchema


@dataclass(frozen=True, slots=True)
class ProfileSchema(BaseSchema):
    """Snapshot parcial o completo de un perfil.

    Cada campo es opcional: `None` significa "no incluido" — ni en el JSON
    guardado, ni al aplicar sobre un perfil real (ese aspecto se deja
    intacto). Esto es lo que permite `--only leds`/`--only buttons`/etc.
    en `save`/`load`.
    """

    active_resolution: ResolutionSchema | None = field(default=None)
    resolutions: list[ResolutionSchema] | None = field(default=None)
    buttons: list[ButtonSchema] | None = field(default=None)
    leds: list[LedSchema] | None = field(default=None)

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {}
        if self.active_resolution is not None:
            data["active_resolution"] = self.active_resolution.to_dict()
        if self.resolutions is not None:
            data["resolutions"] = [r.to_dict() for r in self.resolutions]
        if self.buttons is not None:
            data["buttons"] = [b.to_dict() for b in self.buttons]
        if self.leds is not None:
            data["leds"] = [led.to_dict() for led in self.leds]
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProfileSchema":
        return cls(
            active_resolution=(
                ResolutionSchema.from_dict(data["active_resolution"])
                if "active_resolution" in data
                else None
            ),
            resolutions=(
                [ResolutionSchema.from_dict(r) for r in data["resolutions"]]
                if "resolutions" in data
                else None
            ),
            buttons=(
                [ButtonSchema.from_dict(b) for b in data["buttons"]] if "buttons" in data else None
            ),
            leds=([LedSchema.from_dict(led) for led in data["leds"]] if "leds" in data else None),
        )
