from __future__ import annotations

from mousectl.dbus.constants import IFACE_RESOLUTION
from mousectl.dbus.object import RatbagObject
from mousectl.dbus.protocol import RatbagBusLike
from mousectl.exceptions import InvalidValueError

from mousectl.models.base_model import BaseModel
from mousectl.models.schemas.resolution_schemas import Dpi
from mousectl.models.config.resolution_config import ResolutionConfig

class Resolution(RatbagObject, BaseModel):
    """Preset de resolución (DPI) de un perfil."""

    interface_name = IFACE_RESOLUTION

    def __init__(self, bus: RatbagBusLike, path: str) -> None:
        super().__init__(bus, path)

    @property
    def index(self) -> int:
        return int(self._get("Index"))

    @property
    def is_active(self) -> bool:
        return bool(self._get("IsActive"))

    @property
    def is_default(self) -> bool:
        return bool(self._get("IsDefault"))

    @property
    def resolution(self) -> Dpi:
        raw = self._get("Resolution")
        if isinstance(raw, tuple):
            x, y = raw
            return Dpi(x=int(x), y=int(y))
        value = int(raw)
        return Dpi(x=value, y=value)


    @property
    def resolutions(self) -> list[Dpi]:
        return [Dpi(x=int(x), y=int(y)) for x, y in self._get("Resolutions")]

    def set_resolution(self, x: int, y: int) -> None:
        raw = self._get("Resolution")
        if isinstance(raw, tuple):
            value = self.bus.make_struct(
                (self.bus.make_uint32(x), self.bus.make_uint32(y)), variant_level=2
            )
        else:
            if x != y:
                raise InvalidValueError(
                    "Este dispositivo solo soporta el mismo DPI en X e Y "
                    f"(recibido x={x}, y={y}); usa el mismo valor para ambos ejes."
                )
            value = self.bus.make_uint32(x, variant_level=2)
        self._set("Resolution", value)

    def set_active(self) -> None:
        self._call("SetActive")

    def set_default(self) -> None:
        self._call("SetDefault")
    
    def snapshot(self) -> ResolutionConfig:
        dpi = self.resolution
        return ResolutionConfig(x=dpi.x, y=dpi.y)

    def apply(self, config: ResolutionConfig) -> None:
        self.set_resolution(config.x, config.y)

    def __repr__(self) -> str:
        dpi = self.resolution
        return (
            f"Resolution(index={self.index}, dpi={dpi}, "
            f"active={self.is_active}, default={self.is_default})"
        )
