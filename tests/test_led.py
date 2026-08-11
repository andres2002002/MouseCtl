from __future__ import annotations

import pytest
from conftest import FakeRatbagBus

from mousectl.exceptions import InvalidColorError, InvalidLedModeError, InvalidValueError
from mousectl.models.led import Color, Led, LedMode

LED_PATH = "/org/freedesktop/ratbag1/led/0"


def _register_led(fake_bus: FakeRatbagBus, *, mode: LedMode = LedMode.ON) -> None:
    fake_bus.register(
        LED_PATH,
        {
            "Index": 0,
            "Mode": int(mode),
            "Modes": [int(LedMode.OFF), int(LedMode.ON), int(LedMode.CYCLE)],
            "Color": (0, 255, 0),
            "ColorDepth": 3,
            "Brightness": 255,
            "EffectDuration": 1000,
        },
    )


class TestColor:
    def test_valid_color_accepted(self) -> None:
        color = Color(red=10, green=20, blue=30)
        assert (color.red, color.green, color.blue) == (10, 20, 30)

    @pytest.mark.parametrize("channel", ["red", "green", "blue"])
    def test_out_of_range_channel_rejected(self, channel: str) -> None:
        kwargs = {"red": 0, "green": 0, "blue": 0, channel: 256}
        with pytest.raises(InvalidColorError):
            Color(**kwargs)

    def test_from_hex_parses_correctly(self) -> None:
        assert Color.from_hex("#ff0080") == Color(red=255, green=0, blue=128)
        assert Color.from_hex("00ff00") == Color(red=0, green=255, blue=0)

    @pytest.mark.parametrize("value", ["#fff", "#gggggg", "not-a-color", "#12345"])
    def test_from_hex_rejects_invalid_input(self, value: str) -> None:
        with pytest.raises(InvalidColorError):
            Color.from_hex(value)

    def test_str_formats_as_hex(self) -> None:
        assert str(Color(red=255, green=0, blue=128)) == "#ff0080"


class TestLed:
    def test_reads_basic_properties(self, fake_bus: FakeRatbagBus) -> None:
        _register_led(fake_bus)
        led = Led(fake_bus, LED_PATH)

        assert led.index == 0
        assert led.mode == LedMode.ON
        assert led.modes == [LedMode.OFF, LedMode.ON, LedMode.CYCLE]
        assert led.color == Color(red=0, green=255, blue=0)

    def test_set_color_wraps_channels_via_bus(self, fake_bus: FakeRatbagBus) -> None:
        _register_led(fake_bus)
        led = Led(fake_bus, LED_PATH)

        led.set_color(Color.from_hex("#ff0000"))

        assert led.color == Color(red=255, green=0, blue=0)

    def test_set_mode_accepts_supported_mode(self, fake_bus: FakeRatbagBus) -> None:
        _register_led(fake_bus)
        led = Led(fake_bus, LED_PATH)

        led.set_mode(LedMode.CYCLE)

        assert led.mode == LedMode.CYCLE

    def test_set_mode_rejects_unsupported_mode(self, fake_bus: FakeRatbagBus) -> None:
        _register_led(fake_bus)
        led = Led(fake_bus, LED_PATH)

        with pytest.raises(InvalidLedModeError):
            led.set_mode(LedMode.BREATHING)

    @pytest.mark.parametrize("value", [-1, 256])
    def test_set_brightness_rejects_out_of_range(
        self, fake_bus: FakeRatbagBus, value: int
    ) -> None:
        _register_led(fake_bus)
        led = Led(fake_bus, LED_PATH)

        with pytest.raises(InvalidValueError):
            led.set_brightness(value)

    def test_set_brightness_accepts_valid_value(self, fake_bus: FakeRatbagBus) -> None:
        _register_led(fake_bus)
        led = Led(fake_bus, LED_PATH)

        led.set_brightness(128)

        assert led.brightness == 128

    def test_set_effect_duration_rejects_negative(self, fake_bus: FakeRatbagBus) -> None:
        _register_led(fake_bus)
        led = Led(fake_bus, LED_PATH)

        with pytest.raises(InvalidValueError):
            led.set_effect_duration(-1)
