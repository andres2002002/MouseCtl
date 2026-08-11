from dataclasses import dataclass, field
from typing import Any

from mousectl.models.config.button_config import ButtonConfig
from mousectl.models.config.resolution_config import ResolutionConfig
from mousectl.models.config.led_config import LedConfig
from mousectl.models.base_model import BaseConfig

@dataclass(frozen=True, slots=True)
class ProfileConfig(BaseConfig):
    """Snapshot parcial o completo de un perfil.

    Cada campo es opcional: `None` significa "no incluido" — ni en el JSON
    guardado, ni al aplicar sobre un perfil real (ese aspecto se deja
    intacto). Esto es lo que permite `--only leds`/`--only buttons`/etc.
    en `save`/`load`.
    """

    resolutions: list[ResolutionConfig] | None = field(default=None)
    buttons: list[ButtonConfig] | None = field(default=None)
    leds: list[LedConfig] | None = field(default=None)

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {}
        if self.resolutions is not None:
            data["resolutions"] = [r.to_dict() for r in self.resolutions]
        if self.buttons is not None:
            data["buttons"] = [b.to_dict() for b in self.buttons]
        if self.leds is not None:
            data["leds"] = [led.to_dict() for led in self.leds]
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProfileConfig":
        return cls(
            resolutions=(
                [ResolutionConfig.from_dict(r) for r in data["resolutions"]]
                if "resolutions" in data
                else None
            ),
            buttons=(
                [ButtonConfig.from_dict(b) for b in data["buttons"]] if "buttons" in data else None
            ),
            leds=([LedConfig.from_dict(led) for led in data["leds"]] if "leds" in data else None),
        )
