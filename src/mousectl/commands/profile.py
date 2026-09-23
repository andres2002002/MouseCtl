from __future__ import annotations

import click

from mousectl.models.device import Device
from mousectl.models.profile import Profile

from .common import resolve_device


@click.group("profile")
def profile_group() -> None:
    """Gestiona los perfiles del dispositivo."""


@profile_group.group("name")
def profile_name_group() -> None:
    """Acciones sobre el nombre del perfil."""


@profile_name_group.command("set")
@click.option("index", "-i", type=int, default=None, show_default=True)
@click.argument("name", type=str)
@click.option("--commit/--no-commit", default=True)
@click.pass_context
def profile_name_set(ctx: click.Context, index: int | None, name: str, commit: bool) -> None:
    """Establece el nombre del perfil actual."""
    device = resolve_device(ctx)
    if index is None:
        index = device.active_profile.index
    profile = _get_profile(device, index)
    profile.set_name(name)
    if commit:
        device.commit()
    click.echo(f"Perfil {profile.index} renombrado a {profile.name}.")


@profile_name_group.command("get")
@click.option("index", "-i", type=int, default=None, show_default=True)
@click.pass_context
def profile_get(ctx: click.Context, index: int | None) -> None:
    """Obtiene el perfil con el índice INDEX."""
    device = resolve_device(ctx)
    if index is None:
        index = device.active_profile.index
    profile = _get_profile(device, index)
    click.echo(f"Perfil {profile.index}: {profile.name or 'sin nombre'}")


@profile_group.command("list")
@click.pass_context
def profile_list(ctx: click.Context) -> None:
    """Lista los perfiles disponibles, marcando el activo."""
    device = resolve_device(ctx)
    for profile in device.profiles:
        marker = "*" if profile.is_active else " "
        click.echo(f"[{marker}] {profile.index}: {profile.name or 'sin nombre'}")


@profile_group.command("select")
@click.argument("selector")
@click.pass_context
def profile_select(ctx: click.Context, selector: str) -> None:
    """Selecciona un perfil para los siguientes comandos."""
    session = ctx.obj["session"]
    session_store = ctx.obj["session_store"]

    device = resolve_device(ctx)

    try:
        profile_index = int(selector)
    except ValueError:
        raise click.ClickException(
            "Los perfiles integrados deben seleccionarse mediante su índice."
        )

    _get_profile(device, profile_index)

    session.profile = profile_index
    session_store.save(session)

    click.echo(f"Perfil seleccionado: {profile_index} (dispositivo: {device.name})")


@profile_group.command("switch")
@click.argument("index", type=int)
@click.option(
    "--commit/--no-commit", default=True, help="Aplica el cambio inmediatamente en el hardware."
)
@click.pass_context
def profile_switch(ctx: click.Context, index: int, commit: bool) -> None:
    """Activa el perfil con el índice INDEX."""
    device = resolve_device(ctx)
    profile = _get_profile(device, index)
    profile.set_active()
    if commit:
        device.commit()
    click.echo(f"Perfil activo cambiado a {index}.")


@profile_group.command("copy")
@click.argument("src", type=int)
@click.argument("dst", type=int)
@click.option("--commit/--no-commit", default=True)
@click.pass_context
def profile_copy(ctx: click.Context, src: int, dst: int, commit: bool) -> None:
    """Copia toda la configuración del perfil SRC al DST."""
    device = resolve_device(ctx)
    src_profile = _get_profile(device, src)
    dst_profile = _get_profile(device, dst)

    dst_profile.apply(src_profile.snapshot())

    if commit:
        device.commit()
    click.echo(f"Perfil {src} copiado a perfil {dst}.")


def _get_profile(device: Device, profile_index: int) -> Profile:
    for profile in device.profiles:
        if profile.index == profile_index:
            return profile
    raise click.ClickException(f"No existe el perfil con índice {profile_index}.")
