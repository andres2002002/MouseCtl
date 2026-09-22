from __future__ import annotations

import click

from mousectl.dbus.bus import RatbagBus
from mousectl.exceptions import MultipleDevicesFoundError
from mousectl.models.device import Device


def resolve_device(ctx: click.Context) -> Device:
    """Resuelve el dispositivo seleccionado por la CLI actual."""
    bus: RatbagBus = ctx.obj["bus"]
    device_name: str | None = ctx.obj["device_name"]

    if device_name is not None:
        return Device.find(bus, device_name)

    devices = Device.list_all(bus)
    if len(devices) > 1:
        names = ", ".join(f"'{device.name}'" for device in devices)
        raise MultipleDevicesFoundError(
            f"Hay varios dispositivos conectados ({names}). Usa --device para elegir uno."
        )
    return devices[0]
