from __future__ import annotations

import click

from mousectl.commons import resolve_device
from mousectl.models.virtual_profile import Preset


@click.group("preset")
def preset_group() -> None:
    """Gestiona presets virtuales almacenados en el sistema."""


@preset_group.command("list")
def preset_list() -> None:
    """Lista los presets virtuales disponibles."""
    presets = Preset.list()
    if not presets:
        click.echo("No hay presets guardados.")
        return
    for preset in presets:
        click.echo(preset.name)


@preset_group.command("save")
@click.argument("name", type=str)
@click.pass_context
def preset_save(ctx: click.Context, name: str) -> None:
    """Guarda el perfil activo como un preset virtual."""
    device = resolve_device(ctx)
    profile = device.active_profile
    preset = Preset(name=name, config=profile.snapshot())
    preset.save()
    click.echo(
        f"Preset '{preset.name}' guardado desde el perfil "
        f"{profile.index} ({profile.name or 'sin nombre'})."
    )


@preset_group.command("load")
@click.argument("name", type=str)
@click.option("--commit/--no-commit", default=True)
@click.pass_context
def preset_load(ctx: click.Context, name: str, commit: bool) -> None:
    """Carga un preset sobre el perfil activo."""
    device = resolve_device(ctx)
    profile = device.active_profile
    preset = Preset.load(name)
    profile.apply(preset.config)
    if commit:
        device.commit()
    click.echo(
        f"Preset '{preset.name}' cargado sobre el perfil "
        f"{profile.index} ({profile.name or 'sin nombre'})."
    )


@preset_group.command("delete")
@click.argument("name", type=str)
@click.option("--yes", is_flag=True, help="Elimina el preset sin pedir confirmación.")
def preset_delete(name: str, yes: bool) -> None:
    """Elimina un preset virtual."""
    preset = Preset.load(name)
    if not yes:
        click.confirm(f"¿Eliminar el preset '{preset.name}'?", abort=True)
    preset.delete()
    click.echo(f"Preset '{preset.name}' eliminado.")
