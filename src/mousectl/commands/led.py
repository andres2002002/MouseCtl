from __future__ import annotations

import click

from mousectl.commons import HELP_SETTINGS, resolve_device
from mousectl.models.led import Color, LedMode


@click.group("led", context_settings=HELP_SETTINGS)
def led_group() -> None:
    """Controla los LEDs del perfil activo."""


def _get_leds(ctx: click.Context):
    device = resolve_device(ctx)
    return device, device.active_profile, device.active_profile.leds


@led_group.command("list")
@click.pass_context
def led_list(ctx: click.Context) -> None:
    """Lista los LEDs del perfil activo."""
    device, profile, leds = _get_leds(ctx)
    click.echo(f"Perfil activo: {profile.index} ({profile.name or 'sin nombre'})")
    for led in leds:
        click.echo(f"[{led.index}] {led.mode.name}: {led.color}")


@led_group.command("color")
@click.argument("color", type=str)
@click.option(
    "--index", "-i", "led_index", default=0, show_default=True, help="Índice del LED a modificar."
)
@click.option("--commit/--no-commit", default=True)
@click.pass_context
def led_color(ctx: click.Context, color: str, led_index: int, commit: bool) -> None:
    """Cambia el color de un LED."""
    device, profile, leds = _get_leds(ctx)
    if led_index < 0 or led_index >= len(leds):
        raise click.ClickException(f"El perfil solo tiene {len(leds)} LED(s).")
    leds[led_index].set_color(Color.from_hex(color))
    if commit:
        device.commit()
    click.echo(f"Led {led_index} actualizado a {color} en el perfil {profile.index}.")


@led_group.command("mode")
@click.argument("mode", type=click.Choice([m.name.lower() for m in LedMode]))
@click.option("--index", "-i", "led_index", default=0, show_default=True)
@click.option("--commit/--no-commit", default=True)
@click.pass_context
def led_mode(ctx: click.Context, mode: str, led_index: int, commit: bool) -> None:
    """Cambia el modo de un LED."""
    device, profile, leds = _get_leds(ctx)
    if led_index < 0 or led_index >= len(leds):
        raise click.ClickException(f"El perfil solo tiene {len(leds)} LED(s).")
    leds[led_index].set_mode(LedMode[mode.upper()])
    if commit:
        device.commit()
    click.echo(f"Led {led_index} cambiado a modo {mode} en el perfil {profile.index}.")


@led_group.command("brightness")
@click.argument("value", type=click.IntRange(0, 255))
@click.option("--index", "-i", "led_index", default=0, show_default=True)
@click.option("--commit/--no-commit", default=True)
@click.pass_context
def led_brightness(ctx: click.Context, value: int, led_index: int, commit: bool) -> None:
    """Fija el brillo (0-255) de un LED."""
    device, profile, leds = _get_leds(ctx)
    if led_index < 0 or led_index >= len(leds):
        raise click.ClickException(f"El perfil solo tiene {len(leds)} LED(s).")
    leds[led_index].set_brightness(value)
    if commit:
        device.commit()
    click.echo(f"Led {led_index} brillo actualizado a {value} en el perfil {profile.index}.")
