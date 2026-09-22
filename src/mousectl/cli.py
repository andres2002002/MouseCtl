from __future__ import annotations

import sys

import click

from mousectl import __version__
from mousectl.commands.button import button_group
from mousectl.commands.config import load, save
from mousectl.commands.device import device_group
from mousectl.commands.dpi import dpi_group
from mousectl.commands.led import led_group
from mousectl.commands.preset import preset_group
from mousectl.commands.profile import profile_group
from mousectl.dbus.bus import RatbagBus
from mousectl.exceptions import MousectlError


@click.group()
@click.version_option(__version__, prog_name="mousectl")
@click.option(
    "--device",
    "-d",
    "device_name",
    default=None,
    help=(
        "Subcadena del nombre del dispositivo a controlar. "
        "Si se omite, se usa el único dispositivo detectado."
    ),
)
@click.pass_context
def main(ctx: click.Context, device_name: str | None) -> None:
    """CLI para controlar ratones y periféricos compatibles con libratbag (ratbagd)."""
    ctx.ensure_object(dict)
    ctx.obj["bus"] = RatbagBus()
    ctx.obj["device_name"] = device_name


main.add_command(device_group)
main.add_command(profile_group)
main.add_command(preset_group)
main.add_command(led_group)
main.add_command(dpi_group)
main.add_command(button_group)
main.add_command(save)
main.add_command(load)


def run() -> None:
    """Punto de entrada del script registrado en pyproject.toml."""
    try:
        main(obj={})
    except MousectlError as error:
        click.echo(f"Error: {error}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    run()
