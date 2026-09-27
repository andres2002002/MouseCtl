from __future__ import annotations

import click

from mousectl.commons import HELP_SETTINGS, resolve_device, resolve_selected_profile
from mousectl.models.schemas.profile_schema import ProfileSchema
from mousectl.models.schemas.resolution_schema import ResolutionSchema
from mousectl.models.virtual_profile import VirtualProfile


@click.group("dpi", context_settings=HELP_SETTINGS)
def dpi_group() -> None:
    """Controla los presets de resolución (DPI) del perfil activo."""


@dpi_group.command("list")
@click.pass_context
def dpi_list(ctx: click.Context) -> None:
    """Lista los presets de resolución del perfil activo."""
    profile = resolve_selected_profile(ctx)
    if isinstance(profile, VirtualProfile):
        click.echo(f"Perfil virtual: {profile.name}")

        if profile.config.resolutions is None:
            click.echo("No contiene configuración de resoluciones.")
            return

        for index, resolution in enumerate(profile.config.resolutions):
            marker = "*" if profile.config.active_resolution == resolution else " "
            click.echo(f"[{marker}] {index}: ({resolution.x} x, {resolution.y} y) dpi")

        return

    click.echo(f"Perfil integrado: {profile.index} ({profile.name or 'sin nombre'})")
    for resolution in profile.resolutions:
        marker = "*" if resolution.is_active else " "
        click.echo(f"[{marker}] {resolution.index}: {resolution.resolution}")


@dpi_group.command("get")
@click.option("--index", "-i", type=int, default=None)
@click.pass_context
def dpi_get(ctx: click.Context, index: int | None) -> None:
    """Muestra el DPI activo del perfil seleccionado o de un perfil integrado indicado con -i."""
    if index is not None:
        device = resolve_device(ctx)

        try:
            profile = next(profile for profile in device.profiles if profile.index == index)
        except StopIteration as error:
            raise click.ClickException(
                f"No existe el perfil integrado con índice {index}."
            ) from error

    else:
        profile = resolve_selected_profile(ctx)

    if isinstance(profile, VirtualProfile):
        resolution = profile.config.active_resolution

        if resolution is None:
            raise click.ClickException(
                f"El perfil virtual '{profile.name}' no tiene una resolución activa definida."
            )

        click.echo(f"Perfil virtual: {profile.name}")
        click.echo(f"DPI activo: {resolution.x} x {resolution.y}")

        return

    resolution = profile.active_resolution

    click.echo(f"Perfil integrado: {profile.index} ({profile.name or 'sin nombre'})")
    click.echo(f"DPI activo: {resolution.resolution}")


@dpi_group.command("set")
@click.argument("x", type=int)
@click.argument("y", type=int, required=False)
@click.option("--commit/--no-commit", default=True)
@click.option(
    "--apply",
    is_flag=True,
    default=False,
    help="Aplica el cambio al perfil integrado activo y confirma el cambio en el hardware.",
)
@click.pass_context
def dpi_set(
    ctx: click.Context,
    x: int,
    y: int | None,
    commit: bool,
    apply: bool,
) -> None:
    """Cambia el DPI activo del perfil seleccionado."""
    y_value = y if y is not None else x

    profile = resolve_selected_profile(ctx)

    if isinstance(profile, VirtualProfile):
        active_resolution = profile.config.active_resolution

        if active_resolution is None:
            raise click.ClickException(
                f"El perfil virtual '{profile.name}' no tiene una resolución activa definida."
            )

        new_resolution = ResolutionSchema(
            x=x,
            y=y_value,
        )

        new_config = ProfileSchema(
            resolutions=profile.config.resolutions,
            buttons=profile.config.buttons,
            leds=profile.config.leds,
            active_resolution=new_resolution,
        )

        VirtualProfile(
            name=profile.name,
            config=new_config,
        ).save()

        if apply:
            device = resolve_device(ctx)
            target = device.active_profile
            target.apply_resolutions(new_config.resolutions)
            device.commit()

            click.echo(
                f"DPI actualizado a {x} x {y_value} en el perfil virtual "
                f"'{profile.name}' y aplicado al perfil integrado "
                f"{target.index}."
            )
        else:
            click.echo(
                f"DPI actualizado a {x} x {y_value} "
                f"en el perfil virtual '{profile.name}'. "
                "El cambio se aplicará al hacer switch."
            )

        return

    resolution = profile.active_resolution
    resolution.set_resolution(x, y_value)

    if commit:
        resolve_device(ctx).commit()

    click.echo(f"DPI actualizado a {x} x {y_value} en el perfil {profile.index}.")
