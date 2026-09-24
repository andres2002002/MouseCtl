from __future__ import annotations

from mousectl.dbus.constants import IFACE_PROFILE
from mousectl.dbus.object import RatbagObject
from mousectl.dbus.protocol import RatbagBusLike
from mousectl.exceptions import MousectlError
from mousectl.models.base_model import BaseModel
from mousectl.models.button import Button
from mousectl.models.led import Led
from mousectl.models.resolution import Resolution
from mousectl.models.schemas.profile_schema import ProfileSchema

_ALL_SCOPES = {"active_resolution", "resolutions", "buttons", "leds"}


class Profile(RatbagObject, BaseModel[ProfileSchema]):
    """Perfil configurable de un dispositivo (resoluciones, botones, leds)."""

    interface_name = IFACE_PROFILE

    def __init__(self, bus: RatbagBusLike, path: str) -> None:
        super().__init__(bus, path)

    @property
    def index(self) -> int:
        return int(self._get("Index"))

    @property
    def name(self) -> str:
        return str(self._get("Name"))

    @property
    def is_active(self) -> bool:
        return bool(self._get("IsActive"))

    @property
    def is_enabled(self) -> bool:
        return bool(self._get("IsEnabled"))

    @property
    def resolutions(self) -> list[Resolution]:
        return [Resolution(self.bus, path) for path in self._get("Resolutions")]

    @property
    def active_resolution(self) -> Resolution:
        for resolution in self.resolutions:
            if resolution.is_active:
                return resolution
        raise MousectlError(f"El perfil {self.index} no tiene una resolución activa.")

    @property
    def buttons(self) -> list[Button]:
        return [Button(self.bus, path) for path in self._get("Buttons")]

    @property
    def leds(self) -> list[Led]:
        return [Led(self.bus, path) for path in self._get("Leds")]

    def set_name(self, name: str) -> None:
        self._set("Name", name)

    def set_active(self) -> None:
        self._call("SetActive")

    def set_enabled(self, enabled: bool) -> None:
        self._set("IsEnabled", enabled)

    def snapshot(self, only: set[str] | None = None) -> ProfileSchema:
        """Captura el estado actual. `only` restringe qué se incluye
        (subconjunto de {"resolutions", "buttons", "leds"}); por defecto,
        todo."""
        include = only if only is not None else _ALL_SCOPES
        return ProfileSchema(
            active_resolution=(
                self.active_resolution.snapshot() if "active_resolution" in include else None
            ),
            resolutions=(
                [r.snapshot() for r in self.resolutions] if "resolutions" in include else None
            ),
            buttons=([b.snapshot() for b in self.buttons] if "buttons" in include else None),
            leds=([led.snapshot() for led in self.leds] if "leds" in include else None),
        )

    def apply(self, config: ProfileSchema) -> None:
        """Aplica un `ProfileConfig` sobre este perfil. Solo toca los campos
        presentes en `config` (los que sean `None` se dejan intactos).

        Si el número de resoluciones/botones/leds del `config` no coincide
        con el de este perfil (ej. cargando el config de otro dispositivo),
        falla explícito en vez de aplicar parcialmente o truncar en silencio.
        """
        if config.resolutions is not None:
            targets = self.resolutions
            if len(targets) != len(config.resolutions):
                raise MousectlError(
                    f"El perfil tiene {len(targets)} resoluciones pero el config trae "
                    f"{len(config.resolutions)}."
                )
            for resolution, res_config in zip(targets, config.resolutions, strict=True):
                resolution.apply(res_config)

        # First Apply resolutions then apply active resolution,
        if config.active_resolution is not None:
            self.active_resolution.apply(config.active_resolution)

        if config.buttons is not None:
            targets_b = self.buttons
            if len(targets_b) != len(config.buttons):
                raise MousectlError(
                    f"El perfil tiene {len(targets_b)} botones pero el config trae "
                    f"{len(config.buttons)}."
                )
            for button, btn_config in zip(targets_b, config.buttons, strict=True):
                button.apply(btn_config)

        if config.leds is not None:
            targets_l = self.leds
            if len(targets_l) != len(config.leds):
                raise MousectlError(
                    f"El perfil tiene {len(targets_l)} leds pero el config trae {len(config.leds)}."
                )
            for led, led_config in zip(targets_l, config.leds, strict=True):
                led.apply(led_config)

    def __repr__(self) -> str:
        return (
            f"Profile(index={self.index}, name='{self.name}', "
            f"active={self.is_active}, enabled={self.is_enabled})"
        )
