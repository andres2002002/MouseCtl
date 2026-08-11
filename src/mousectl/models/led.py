from __future__ import annotations

from mousectl.dbus.constants import IFACE_LED
from mousectl.dbus.object import RatbagObject
from mousectl.dbus.protocol import RatbagBusLike
from mousectl.exceptions import InvalidLedModeError, InvalidValueError
from mousectl.models.schemas.led_schemas import Color, LedMode
from mousectl.models.base_model import BaseModel
from mousectl.models.config.led_config import LedConfig

class Led(RatbagObject, BaseModel):
    """LED de un perfil (color, modo, brillo, duración del efecto)."""

    interface_name = IFACE_LED

    def __init__(self, bus: RatbagBusLike, path: str) -> None:
        super().__init__(bus, path)

    @property
    def index(self) -> int:
        return int(self._get("Index"))

    @property
    def mode(self) -> LedMode:
        return LedMode(int(self._get("Mode")))

    @property
    def modes(self) -> list[LedMode]:
        return [LedMode(int(value)) for value in self._get("Modes")]

    @property
    def color(self) -> Color:
        red, green, blue = self._get("Color")
        return Color(red=int(red), green=int(green), blue=int(blue))

    @property
    def color_depth(self) -> int:
        return int(self._get("ColorDepth"))

    @property
    def brightness(self) -> int:
        return int(self._get("Brightness"))

    @property
    def effect_duration(self) -> int:
        return int(self._get("EffectDuration"))

    def set_mode(self, mode: LedMode) -> None:
        if mode not in self.modes:
            supported = [m.name for m in self.modes]
            raise InvalidLedModeError(
                f"El modo '{mode.name}' no está soportado por este LED. "
                f"Modos disponibles: {supported}."
            )
        mode_u = self.bus.make_uint32(mode.value)
        self._set("Mode", mode_u)

    def set_color(self, color: Color) -> None:
        channels = (
            self.bus.make_uint32(color.red),
            self.bus.make_uint32(color.green),
            self.bus.make_uint32(color.blue),
        )
        color_u = self.bus.make_struct(channels)
        self._set("Color", color_u)

    def set_brightness(self, brightness: int) -> None:
        if not 0 <= brightness <= 255:
            raise InvalidValueError(
                f"El brillo debe estar entre 0 y 255, recibido {brightness}."
            )
        self._set("Brightness", self.bus.make_uint32(brightness))

    def set_effect_duration(self, milliseconds: int) -> None:
        if milliseconds < 0:
            raise InvalidValueError("La duración del efecto no puede ser negativa.")
        self._set("EffectDuration", self.bus.make_uint32(milliseconds))
    
    def snapshot(self) -> LedConfig:
        return LedConfig(
            mode=self.mode,
            color=self.color,
            brightness=self.brightness,
            effect_duration=self.effect_duration,
        )

    def apply(self, config: LedConfig) -> None:
        self.set_mode(config.mode)
        self.set_color(config.color)
        self.set_brightness(config.brightness)
        self.set_effect_duration(config.effect_duration)


    def __repr__(self) -> str:
        return f"Led(index={self.index}, mode={self.mode.name}, color={self.color})"
