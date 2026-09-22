from __future__ import annotations

import click

from .common import resolve_device


@click.group("dpi")
def dpi_group() -> None:
    """Controla los presets de resolución (DPI) del perfil activo."""


@dpi_group.command("list")
@click.pass_context
def dpi_list(ctx: click.Context) -> None:
    """Lista los presets de resolución del perfil activo."""
    device = resolve_device(ctx)
    profile = device.active_profile
    for resolution in profile.resolutions:
        marker = "*" if resolution.is_active else " "
        click.echo(f"[{marker}] {resolution.index}: {resolution.resolution}")


@dpi_group.command("get")
@click.option("--index", "-i", type=int, default=None, show_default=True)
@click.pass_context
def dpi_get(ctx: click.Context, index: int | None) -> None:
    """Obtiene el DPI activo."""
    device = resolve_device(ctx)
    if index is None:
        index = device.active_profile.index
    if index < 0 or index >= len(device.profiles):
        raise click.ClickException(f"No existe el perfil con índice {index}.")
    profile = device.profiles[index]
    resolution = profile.active_resolution
    click.echo(f"Perfil {profile.index}: {profile.name or 'sin nombre'}")
    click.echo(f"DPI activo: {resolution.resolution}")


@dpi_group.command("set")
@click.argument("x", type=int)
@click.argument("y", type=int, required=False)
@click.option("--commit/--no-commit", default=True)
@click.pass_context
def dpi_set(ctx: click.Context, x: int, y: int | None, commit: bool) -> None:
    """Fija el DPI activo. Si Y se omite, usa el mismo valor que X."""
    device = resolve_device(ctx)
    profile = device.active_profile
    resolution = profile.active_resolution
    y_value = y if y is not None else x
    resolution.set_resolution(x, y_value)
    if commit:
        device.commit()
    click.echo(f"DPI actualizado a {x} x {y_value} en el perfil {profile.index}.")
