from __future__ import annotations

import click

from mousectl.dbus.bus import RatbagBus
from mousectl.exceptions import MultipleDevicesFoundError
from mousectl.models.device import Device
from mousectl.models.profile import Profile

HELP_SETTINGS = {
    "help_option_names": ["-h", "--help"],
}


def resolve_device(ctx: click.Context) -> Device:
    """Resuelve el dispositivo para el comando actual."""
    bus: RatbagBus = ctx.obj["bus"]

    device_name: str | None = ctx.obj.get("device_name")

    if device_name is None:
        session = ctx.obj["session"]
        device_name = session.device

    if device_name is not None:
        return Device.find(bus, device_name)

    devices = Device.list_all(bus)

    if not devices:
        raise click.ClickException("No se detectaron dispositivos.")

    if len(devices) > 1:
        names = ", ".join(f"'{device.name}'" for device in devices)
        raise MultipleDevicesFoundError(
            f"Hay varios dispositivos conectados ({names}). "
            "Usa 'mousectl device select' o --device para elegir uno."
        )

    return devices[0]


def resolve_profile(ctx: click.Context) -> Profile:
    """Resuelve el perfil seleccionado por la sesión actual."""
    device = resolve_device(ctx)
    profile_index = ctx.obj["session"].profile

    if profile_index is None:
        raise click.ClickException(
            "No hay un perfil seleccionado. Usa 'mousectl profile select <índice>'."
        )

    if not isinstance(profile_index, int):
        raise click.ClickException("El perfil seleccionado no es un perfil integrado válido.")

    for profile in device.profiles:
        if profile.index == profile_index:
            return profile

    raise click.ClickException(f"No existe el perfil seleccionado: {profile_index}.")
