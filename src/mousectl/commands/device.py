from __future__ import annotations

import click

from mousectl.commons import HELP_SETTINGS, resolve_device
from mousectl.models.device import Device


@click.group("device", context_settings=HELP_SETTINGS)
def device_group() -> None:
    """Gestiona los dispositivos ratbag detectados."""


@device_group.command("list")
@click.pass_context
def device_list(ctx: click.Context) -> None:
    """Lista los dispositivos ratbag detectados en el bus."""
    bus = ctx.obj["bus"]
    for device in Device.list_all(bus):
        click.echo(f"{device.name} ({device.model}) -> {device.path}")


@device_group.command("select")
@click.argument("name")
@click.pass_context
def device_select(ctx: click.Context, name: str) -> None:
    """Selecciona un dispositivo para los siguientes comandos."""
    bus = ctx.obj["bus"]
    session = ctx.obj["session"]
    session_store = ctx.obj["session_store"]

    device = Device.find(bus, name)

    session.device = device.name
    session.profile = None

    session_store.save(session)

    click.echo(f"Dispositivo seleccionado: {device.name}")


@device_group.command("status")
@click.pass_context
def device_status(ctx: click.Context) -> None:
    """Muestra el estado actual del dispositivo: perfil, dpi y leds."""
    device = resolve_device(ctx)
    profile = device.active_profile

    click.echo(f"Dispositivo: {device.name}")
    click.echo(f"Perfil activo: {profile.index} ({profile.name or 'sin nombre'})")
    click.echo(f"DPI activo: {profile.active_resolution.resolution}")

    for led in profile.leds:
        click.echo(f"Led {led.index}: modo={led.mode.name}, color={led.color}")
