from __future__ import annotations

import pytest
from conftest import FakeRatbagBus

from mousectl.exceptions import MousectlError
from mousectl.models.profile import Profile

PROFILE_PATH = "/org/freedesktop/ratbag1/profile/0"
RES_ACTIVE_PATH = "/org/freedesktop/ratbag1/resolution/0"
RES_INACTIVE_PATH = "/org/freedesktop/ratbag1/resolution/1"
BUTTON_PATH = "/org/freedesktop/ratbag1/button/0"
LED_PATH = "/org/freedesktop/ratbag1/led/0"


def _register_profile(fake_bus: FakeRatbagBus, *, active: bool = True) -> None:
    fake_bus.register(
        PROFILE_PATH,
        {
            "Index": 0,
            "Name": "Perfil 1",
            "IsActive": active,
            "IsEnabled": True,
            "Resolutions": [RES_ACTIVE_PATH, RES_INACTIVE_PATH],
            "Buttons": [BUTTON_PATH],
            "Leds": [LED_PATH],
        },
    )
    fake_bus.register(
        RES_ACTIVE_PATH,
        {
            "Index": 0,
            "IsActive": True,
            "IsDefault": True,
            "Resolution": (800, 800),
            "Resolutions": [(800, 800)],
        },
    )
    fake_bus.register(
        RES_INACTIVE_PATH,
        {
            "Index": 1,
            "IsActive": False,
            "IsDefault": False,
            "Resolution": (1600, 1600),
            "Resolutions": [(1600, 1600)],
        },
    )
    fake_bus.register(
        BUTTON_PATH,
        {"Index": 0, "ActionType": 1, "ActionTypes": [0, 1], "ButtonMapping": 1, "Special": ""},
    )
    fake_bus.register(
        LED_PATH,
        {
            "Index": 0,
            "Mode": 1,
            "Modes": [0, 1],
            "Color": (0, 0, 0),
            "ColorDepth": 3,
            "Brightness": 255,
            "EffectDuration": 0,
        },
    )


def test_reads_basic_properties(fake_bus: FakeRatbagBus) -> None:
    _register_profile(fake_bus)
    profile = Profile(fake_bus, PROFILE_PATH)

    assert profile.index == 0
    assert profile.name == "Perfil 1"
    assert profile.is_active is True
    assert profile.is_enabled is True


def test_builds_child_resolutions_buttons_and_leds(fake_bus: FakeRatbagBus) -> None:
    _register_profile(fake_bus)
    profile = Profile(fake_bus, PROFILE_PATH)

    assert [r.path for r in profile.resolutions] == [RES_ACTIVE_PATH, RES_INACTIVE_PATH]
    assert [b.path for b in profile.buttons] == [BUTTON_PATH]
    assert [led.path for led in profile.leds] == [LED_PATH]


def test_active_resolution_returns_the_active_one(fake_bus: FakeRatbagBus) -> None:
    _register_profile(fake_bus)
    profile = Profile(fake_bus, PROFILE_PATH)

    assert profile.active_resolution.path == RES_ACTIVE_PATH


def test_active_resolution_raises_when_none_active(fake_bus: FakeRatbagBus) -> None:
    _register_profile(fake_bus)
    fake_bus._properties[RES_ACTIVE_PATH]["IsActive"] = False

    profile = Profile(fake_bus, PROFILE_PATH)

    with pytest.raises(MousectlError):
        profile.active_resolution


def test_set_active_records_call(fake_bus: FakeRatbagBus) -> None:
    _register_profile(fake_bus)
    profile = Profile(fake_bus, PROFILE_PATH)

    profile.set_active()

    assert (PROFILE_PATH, "SetActive", ()) in fake_bus.calls


def test_set_enabled_updates_store(fake_bus: FakeRatbagBus) -> None:
    _register_profile(fake_bus)
    profile = Profile(fake_bus, PROFILE_PATH)

    profile.set_enabled(False)

    assert profile.is_enabled is False
