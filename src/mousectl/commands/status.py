from __future__ import annotations

import click

from mousectl.commons import HELP_SETTINGS, resolve_device, resolve_selected_profile
from mousectl.models.virtual_profile import VirtualProfile


@click.command("status", context_settings=HELP_SETTINGS)
@click.pass_context
def status(ctx: click.Context) -> None:
    """Muestra el estado del dispositivo y del perfil seleccionado."""
    device = resolve_device(ctx)
    selected = resolve_selected_profile(ctx)
    active = device.active_profile

    click.echo(f"Dispositivo: {device.name}")
    click.echo(f"Perfil integrado activo: {active.index} ({active.name or 'sin nombre'})")

    if isinstance(selected, VirtualProfile):
        click.echo(f"Perfil seleccionado: {selected.name}")
        click.echo("Tipo: virtual")

        if selected.config.active_resolution is not None:
            resolution = selected.config.active_resolution
            click.echo(f"DPI configurado: {resolution.x} x {resolution.y}")
        else:
            click.echo("DPI configurado: no especificado")

        return

    click.echo(f"Perfil seleccionado: {selected.index} ({selected.name or 'sin nombre'})")
    click.echo("Tipo: integrado")

    resolution = selected.active_resolution
    click.echo(f"DPI: {resolution.resolution}")
