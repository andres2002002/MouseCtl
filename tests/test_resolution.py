from __future__ import annotations

import pytest
from conftest import FakeRatbagBus

from mousectl.exceptions import InvalidValueError
from mousectl.models.resolution import Dpi, Resolution

RES_PATH = "/org/freedesktop/ratbag1/resolution/0"


def _register_single_axis(fake_bus: FakeRatbagBus, *, active: bool = True) -> None:
    """Forma `u` — confirmada contra hardware real (G502 HERO: 19500)."""
    fake_bus.register(
        RES_PATH,
        {
            "Index": 0,
            "IsActive": active,
            "IsDefault": True,
            "Resolution": 800,
            "Resolutions": [400, 800, 1600],
        },
    )


def _register_dual_axis(fake_bus: FakeRatbagBus, *, active: bool = True) -> None:
    """Forma `(uu)` — documentada, no confirmada contra hardware propio."""
    fake_bus.register(
        RES_PATH,
        {
            "Index": 0,
            "IsActive": active,
            "IsDefault": True,
            "Resolution": (800, 800),
            "Resolutions": [400, 800, 1600],
        },
    )


class TestSingleAxisShape:
    def test_reads_resolution_as_uniform_dpi(self, fake_bus: FakeRatbagBus) -> None:
        _register_single_axis(fake_bus)
        resolution = Resolution(fake_bus, RES_PATH)

        assert resolution.resolution == Dpi(x=800, y=800)

    def test_set_resolution_preserves_single_axis_shape(self, fake_bus: FakeRatbagBus) -> None:
        _register_single_axis(fake_bus)
        resolution = Resolution(fake_bus, RES_PATH)

        resolution.set_resolution(1600, 1600)

        assert resolution.resolution == Dpi(x=1600, y=1600)

    def test_set_resolution_rejects_mismatched_axes(self, fake_bus: FakeRatbagBus) -> None:
        _register_single_axis(fake_bus)
        resolution = Resolution(fake_bus, RES_PATH)

        with pytest.raises(InvalidValueError):
            resolution.set_resolution(1600, 2400)


class TestDualAxisShape:
    def test_reads_resolution_with_independent_axes(self, fake_bus: FakeRatbagBus) -> None:
        _register_dual_axis(fake_bus)
        resolution = Resolution(fake_bus, RES_PATH)

        assert resolution.resolution == Dpi(x=800, y=800)

    def test_set_resolution_preserves_dual_axis_shape(self, fake_bus: FakeRatbagBus) -> None:
        _register_dual_axis(fake_bus)
        resolution = Resolution(fake_bus, RES_PATH)

        resolution.set_resolution(1600, 2400)

        assert resolution.resolution == Dpi(x=1600, y=2400)


def test_reads_basic_properties(fake_bus: FakeRatbagBus) -> None:
    _register_single_axis(fake_bus)
    resolution = Resolution(fake_bus, RES_PATH)

    assert resolution.index == 0
    assert resolution.is_active is True
    assert resolution.is_default is True


def test_reads_available_resolutions_as_flat_list(fake_bus: FakeRatbagBus) -> None:
    _register_single_axis(fake_bus)
    resolution = Resolution(fake_bus, RES_PATH)

    assert resolution.resolutions == [Dpi(x=400, y=400), Dpi(x=800, y=800), Dpi(x=1600, y=1600)]


def test_set_active_records_method_call(fake_bus: FakeRatbagBus) -> None:
    _register_single_axis(fake_bus)
    resolution = Resolution(fake_bus, RES_PATH)

    resolution.set_active()

    assert (RES_PATH, "SetActive", ()) in fake_bus.calls


def test_set_default_records_method_call(fake_bus: FakeRatbagBus) -> None:
    _register_single_axis(fake_bus)
    resolution = Resolution(fake_bus, RES_PATH)

    resolution.set_default()

    assert (RES_PATH, "SetDefault", ()) in fake_bus.calls


def test_dpi_str_collapses_equal_axes() -> None:
    assert str(Dpi(x=800, y=800)) == "800"
    assert str(Dpi(x=800, y=1200)) == "800 x 1200"