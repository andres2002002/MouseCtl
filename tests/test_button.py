from __future__ import annotations

from conftest import FakeRatbagBus

from mousectl.models.button import ActionType, Button

BUTTON_PATH = "/org/freedesktop/ratbag1/button/0"


def _register_button(fake_bus: FakeRatbagBus) -> None:
    fake_bus.register(
        BUTTON_PATH,
        {
            "Index": 0,
            "ActionType": int(ActionType.BUTTON),
            "ActionTypes": [int(ActionType.NONE), int(ActionType.BUTTON), int(ActionType.SPECIAL)],
            "ButtonMapping": 1,
            "Special": "",
        },
    )


def test_reads_basic_properties(fake_bus: FakeRatbagBus) -> None:
    _register_button(fake_bus)
    button = Button(fake_bus, BUTTON_PATH)

    assert button.index == 0
    assert button.action_type == ActionType.BUTTON
    assert button.action_types == [ActionType.NONE, ActionType.BUTTON, ActionType.SPECIAL]
    assert button.mapping == 1


def test_set_button_mapping_records_call(fake_bus: FakeRatbagBus) -> None:
    _register_button(fake_bus)
    button = Button(fake_bus, BUTTON_PATH)

    button.set_button_mapping(3)

    assert (BUTTON_PATH, "SetButtonMapping", (3,)) in fake_bus.calls


def test_set_special_records_call(fake_bus: FakeRatbagBus) -> None:
    _register_button(fake_bus)
    button = Button(fake_bus, BUTTON_PATH)

    button.set_special("doubleclick")

    assert (BUTTON_PATH, "SetSpecial", ("doubleclick",)) in fake_bus.calls


def test_disable_records_call(fake_bus: FakeRatbagBus) -> None:
    _register_button(fake_bus)
    button = Button(fake_bus, BUTTON_PATH)

    button.disable()

    assert (BUTTON_PATH, "Disable", ()) in fake_bus.calls
