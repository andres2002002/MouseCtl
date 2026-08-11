from __future__ import annotations

from mousectl.dbus.constants import IFACE_DEVICE, IFACE_MANAGER, ROOT_PATH
from mousectl.dbus.object import RatbagObject
from mousectl.dbus.protocol import RatbagBusLike
from mousectl.exceptions import DeviceNotFoundError, InvalidValueError, NoActiveProfileError, NoDevicesFoundError
from mousectl.models.profile import Profile
from mousectl.models.base_model import BaseModel
from mousectl.models.config.device_config import DeviceConfig


class Device(RatbagObject, BaseModel):
    """Dispositivo ratbag genérico (ratón, teclado, etc.).

    A diferencia del PoC original, no asume ningún modelo concreto: la
    resolución de qué dispositivo usar se hace en `Device.list_all` /
    `Device.find`, dejando el filtrado explícito en manos del llamador (la CLI).
    """

    interface_name = IFACE_DEVICE

    def __init__(self, bus: RatbagBusLike, path: str) -> None:
        super().__init__(bus, path)

    @property
    def name(self) -> str:
        return str(self._get("Name"))

    @property
    def model(self) -> str:
        return str(self._get("Model"))

    @property
    def profiles(self) -> list[Profile]:
        return [Profile(self.bus, path) for path in self._get("Profiles")]

    @property
    def active_profile(self) -> Profile:
        for profile in self.profiles:
            if profile.is_active:
                return profile
        raise NoActiveProfileError(f"El dispositivo '{self.name}' no tiene un perfil activo.")

    def commit(self) -> None:
        self._call("Commit")


    def snapshot(
        self, profile_indices: set[int] | None = None, only: set[str] | None = None
    ) -> DeviceConfig:
        """Captura el estado de uno o varios perfiles. `profile_indices=None`
        captura todos; `only` se pasa tal cual a `Profile.snapshot`."""
        profiles = self.profiles
        selected = [p for p in profiles if profile_indices is None or p.index in profile_indices]
        return DeviceConfig(profiles={p.index: p.snapshot(only=only) for p in selected})

    def apply(self, config: DeviceConfig) -> None:
        """Aplica un `DeviceConfig` — cada entrada se aplica al perfil con
        ese índice. Falla explícito si un índice del config no existe en
        este dispositivo (ej. config guardado de un dispositivo con más
        perfiles)."""
        by_index = {p.index: p for p in self.profiles}
        for index, profile_config in config.profiles.items():
            if index not in by_index:
                raise InvalidValueError(
                    f"El config trae el perfil {index}, pero este dispositivo no lo tiene."
                )
            by_index[index].apply(profile_config)


    def __repr__(self) -> str:
        return f"Device(name='{self.name}', model='{self.model}', path='{self.path}')"

    @staticmethod
    def list_all(bus: RatbagBusLike) -> list[Device]:
        manager = bus.properties(ROOT_PATH)
        paths = manager.Get(IFACE_MANAGER, "Devices")

        if not paths:
            raise NoDevicesFoundError("No hay dispositivos ratbag registrados en el bus.")

        return [Device(bus, path) for path in paths]

    @staticmethod
    def find(bus: RatbagBusLike, name_contains: str) -> Device:
        for device in Device.list_all(bus):
            if name_contains.lower() in device.name.lower():
                return device

        raise DeviceNotFoundError(
            f"No se encontró un dispositivo cuyo nombre contenga '{name_contains}'."
        )
