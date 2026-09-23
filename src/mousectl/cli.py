from __future__ import annotations

import sys

import click

from mousectl import __version__
from mousectl.commands.button import button_group
from mousectl.commands.config import config_group
from mousectl.commands.device import device_group
from mousectl.commands.dpi import dpi_group
from mousectl.commands.led import led_group
from mousectl.commands.profile import profile_group
from mousectl.commons import HELP_SETTINGS
from mousectl.config import ConfigStore
from mousectl.dbus.bus import RatbagBus
from mousectl.exceptions import MousectlError


@click.group(context_settings=HELP_SETTINGS)
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

    config_store = ConfigStore()
    session = config_store.session_store.load()

    ctx.obj["bus"] = RatbagBus()
    ctx.obj["device_name"] = device_name
    ctx.obj["session"] = session
    ctx.obj["session_store"] = config_store.session_store


main.add_command(device_group)
main.add_command(profile_group)
main.add_command(led_group)
main.add_command(dpi_group)
main.add_command(button_group)
main.add_command(config_group)


def run() -> None:
    """Punto de entrada del script registrado en pyproject.toml."""
    try:
        main(obj={})
    except MousectlError as error:
        click.echo(f"Error: {error}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    run()
