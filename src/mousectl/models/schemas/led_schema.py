from dataclasses import dataclass
from typing import Any

from mousectl.models.base_model import BaseSchema
from mousectl.models.types.led_types import Color, LedMode


@dataclass(frozen=True, slots=True)
class LedSchema(BaseSchema):
    mode: LedMode
    color: Color
    brightness: int
    effect_duration: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode.name,
            "color": str(self.color),
            "brightness": self.brightness,
            "effect_duration": self.effect_duration,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LedSchema":
        return cls(
            mode=LedMode[data["mode"]],
            color=Color.from_hex(data["color"]),
            brightness=int(data["brightness"]),
            effect_duration=int(data["effect_duration"]),
        )
