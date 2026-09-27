from __future__ import annotations

import click

from mousectl.dbus.bus import RatbagBus
from mousectl.exceptions import MultipleDevicesFoundError
from mousectl.models.device import Device
from mousectl.models.profile import Profile
from mousectl.models.virtual_profile import VirtualProfile

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
    """Resuelve el perfil seleccionado, que debe ser integrado."""
    device = resolve_device(ctx)
    profile_selector = ctx.obj["session"].profile

    if profile_selector is None:
        raise click.ClickException(
            "No hay un perfil seleccionado. Usa 'mousectl profile select <índice o nombre>'."
        )

    if isinstance(profile_selector, str):
        raise click.ClickException(
            f"El perfil seleccionado es el perfil virtual "
            f"'{profile_selector}'. "
            "Este comando requiere un perfil integrado."
        )

    for profile in device.profiles:
        if profile.index == profile_selector:
            return profile

    raise click.ClickException(f"No existe el perfil integrado seleccionado: {profile_selector}.")


def resolve_selected_profile(
    ctx: click.Context,
) -> Profile | VirtualProfile:
    """Resuelve el perfil actualmente seleccionado."""
    profile_selector = ctx.obj["session"].profile

    if profile_selector is None:
        raise click.ClickException(
            "No hay un perfil seleccionado. Usa 'mousectl profile select <índice o nombre>'."
        )

    if isinstance(profile_selector, int):
        return resolve_profile(ctx)

    return VirtualProfile.load(profile_selector)
