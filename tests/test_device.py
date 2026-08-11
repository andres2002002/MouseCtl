from __future__ import annotations

import pytest
from conftest import FakeRatbagBus

from mousectl.dbus.constants import ROOT_PATH
from mousectl.exceptions import DeviceNotFoundError, NoActiveProfileError, NoDevicesFoundError
from mousectl.models.device import Device

DEVICE_G502_PATH = "/org/freedesktop/ratbag1/device/0"
DEVICE_G303_PATH = "/org/freedesktop/ratbag1/device/1"
PROFILE_ACTIVE_PATH = "/org/freedesktop/ratbag1/profile/0"
PROFILE_INACTIVE_PATH = "/org/freedesktop/ratbag1/profile/1"


def _register_manager(fake_bus: FakeRatbagBus, device_paths: list[str]) -> None:
    fake_bus.register(ROOT_PATH, {"Devices": device_paths})


def _register_device(
    fake_bus: FakeRatbagBus, path: str, *, name: str, profiles: list[str]
) -> None:
    fake_bus.register(path, {"Name": name, "Model": "usb:046d:c08b", "Profiles": profiles})


class TestListAll:
    def test_returns_all_registered_devices(self, fake_bus: FakeRatbagBus) -> None:
        _register_manager(fake_bus, [DEVICE_G502_PATH, DEVICE_G303_PATH])
        _register_device(fake_bus, DEVICE_G502_PATH, name="Logitech G502", profiles=[])
        _register_device(fake_bus, DEVICE_G303_PATH, name="Logitech G303", profiles=[])

        devices = Device.list_all(fake_bus)

        assert [d.name for d in devices] == ["Logitech G502", "Logitech G303"]

    def test_raises_when_no_devices(self, fake_bus: FakeRatbagBus) -> None:
        _register_manager(fake_bus, [])

        with pytest.raises(NoDevicesFoundError):
            Device.list_all(fake_bus)


class TestFind:
    def test_finds_device_by_partial_name_case_insensitive(self, fake_bus: FakeRatbagBus) -> None:
        _register_manager(fake_bus, [DEVICE_G502_PATH, DEVICE_G303_PATH])
        _register_device(fake_bus, DEVICE_G502_PATH, name="Logitech G502", profiles=[])
        _register_device(fake_bus, DEVICE_G303_PATH, name="Logitech G303", profiles=[])

        device = Device.find(fake_bus, "g502")

        assert device.path == DEVICE_G502_PATH

    def test_raises_when_no_match(self, fake_bus: FakeRatbagBus) -> None:
        _register_manager(fake_bus, [DEVICE_G502_PATH])
        _register_device(fake_bus, DEVICE_G502_PATH, name="Logitech G502", profiles=[])

        with pytest.raises(DeviceNotFoundError):
            Device.find(fake_bus, "g903")


class TestActiveProfile:
    def test_returns_the_active_profile(self, fake_bus: FakeRatbagBus) -> None:
        _register_device(
            fake_bus,
            DEVICE_G502_PATH,
            name="Logitech G502",
            profiles=[PROFILE_ACTIVE_PATH, PROFILE_INACTIVE_PATH],
        )
        fake_bus.register(PROFILE_ACTIVE_PATH, {"Index": 0, "Name": "P1", "IsActive": True, "IsEnabled": True, "Resolutions": [], "Buttons": [], "Leds": []})
        fake_bus.register(PROFILE_INACTIVE_PATH, {"Index": 1, "Name": "P2", "IsActive": False, "IsEnabled": True, "Resolutions": [], "Buttons": [], "Leds": []})

        device = Device(fake_bus, DEVICE_G502_PATH)

        assert device.active_profile.path == PROFILE_ACTIVE_PATH

    def test_raises_when_no_active_profile(self, fake_bus: FakeRatbagBus) -> None:
        _register_device(fake_bus, DEVICE_G502_PATH, name="Logitech G502", profiles=[PROFILE_ACTIVE_PATH])
        fake_bus.register(PROFILE_ACTIVE_PATH, {"Index": 0, "Name": "P1", "IsActive": False, "IsEnabled": True, "Resolutions": [], "Buttons": [], "Leds": []})

        device = Device(fake_bus, DEVICE_G502_PATH)

        with pytest.raises(NoActiveProfileError):
            device.active_profile


def test_commit_records_call(fake_bus: FakeRatbagBus) -> None:
    _register_device(fake_bus, DEVICE_G502_PATH, name="Logitech G502", profiles=[])
    device = Device(fake_bus, DEVICE_G502_PATH)

    device.commit()

    assert (DEVICE_G502_PATH, "Commit", ()) in fake_bus.calls
