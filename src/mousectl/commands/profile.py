from __future__ import annotations

import json
from pathlib import Path

import click

from mousectl.commons import HELP_SETTINGS, resolve_device, resolve_profile
from mousectl.exceptions import MousectlError
from mousectl.models.device import Device
from mousectl.models.profile import Profile
from mousectl.models.schemas import ProfileSchema
from mousectl.models.virtual_profile import VirtualProfile


@click.group("profile", context_settings=HELP_SETTINGS)
def profile_group() -> None:
    """Gestiona los perfiles integrados del dispositivo y los perfiles virtuales almacenados."""


@profile_group.group("name")
def profile_name_group() -> None:
    """Consulta o cambia el nombre de un perfil integrado o virtual."""


@profile_name_group.command("get")
@click.argument("selector", required=False)
@click.pass_context
def profile_name_get(
    ctx: click.Context,
    selector: str | None,
) -> None:
    """Muestra el nombre de un perfil.

    Sin selector, muestra el nombre del perfil actualmente seleccionado.
    Con un índice, muestra el nombre del perfil integrado indicado.
    Con un nombre, muestra el nombre del perfil virtual indicado."""
    if selector is None:
        session_profile = ctx.obj["session"].profile

        if session_profile is None:
            raise click.ClickException("No hay un perfil seleccionado.")

        if isinstance(session_profile, int):
            profile = resolve_profile(ctx)
            click.echo(profile.name or "sin nombre")
            return

        virtual_profile = VirtualProfile.load(session_profile)
        click.echo(virtual_profile.name)
        return

    profile = _resolve_profile_selector(ctx, selector)

    if isinstance(profile, VirtualProfile):
        click.echo(profile.name)
    else:
        click.echo(profile.name or "sin nombre")


@profile_name_group.command("set")
@click.argument("first", type=str)
@click.argument("second", required=False, type=str)
@click.option("--commit/--no-commit", default=True)
@click.pass_context
def profile_name_set(
    ctx: click.Context,
    first: str,
    second: str | None,
    commit: bool,
) -> None:
    """Cambia el nombre de un perfil integrado o virtual.

    Con un solo argumento, renombra el perfil actualmente seleccionado.
    Con dos argumentos, el primero identifica el perfil y el segundo es su nuevo nombre."""
    if second is None:
        selector = None
        name = first
    else:
        selector = first
        name = second

    if selector is None:
        profile_selector = ctx.obj["session"].profile

        if profile_selector is None:
            raise click.ClickException("No hay un perfil seleccionado.")

        if isinstance(profile_selector, int):
            profile = resolve_profile(ctx)
        else:
            profile = VirtualProfile.load(profile_selector)
    else:
        profile = _resolve_profile_selector(ctx, selector)

    if isinstance(profile, VirtualProfile):
        renamed = profile.rename(name)

        if ctx.obj["session"].profile == profile.name:
            ctx.obj["session"].profile = renamed.name
            ctx.obj["session_store"].save(ctx.obj["session"])

        click.echo(f"Perfil virtual '{profile.name}' renombrado a '{renamed.name}'.")
        return

    profile.set_name(name)

    if commit:
        resolve_device(ctx).commit()

    click.echo(f"Perfil {profile.index} renombrado a {profile.name}.")


@profile_group.command("save")
@click.option(
    "--output",
    type=click.Path(
        dir_okay=False,
        writable=True,
        path_type=Path,
    ),
    help="Guarda el perfil como una copia en el archivo indicado.",
)
@click.option(
    "--profile",
    "virtual_profile",
    type=str,
    help="Guarda el perfil como VirtualProfile con el nombre indicado.",
)
@click.pass_context
def profile_save(
    ctx: click.Context,
    output: Path | None,
    virtual_profile: str | None,
) -> None:
    """Guarda el perfil seleccionado como archivo o perfil virtual.

    El perfil seleccionado puede ser integrado o virtual.

    Usa --output para crear una copia en un archivo.
    Usa --profile para crear o reemplazar un perfil virtual.
    """
    destinations = int(output is not None) + int(virtual_profile is not None)

    if destinations != 1:
        raise click.UsageError(
            "Debes especificar exactamente uno de: --output PATH o --profile NAME."
        )

    profile = _resolve_selected_profile(ctx)

    if isinstance(profile, VirtualProfile):
        profile_schema = profile.config
        source_name = f"perfil virtual '{profile.name}'"
    else:
        profile_schema = profile.snapshot()
        source_name = f"perfil integrado {profile.index}"

    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(
                profile_schema.to_dict(),
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )
        click.echo(f"{source_name.capitalize()} guardado en '{output}'.")
        return

    if virtual_profile is not None:
        virtual = VirtualProfile(
            name=virtual_profile,
            config=profile_schema,
        )
        virtual.save()

        click.echo(f"{source_name.capitalize()} guardado como perfil virtual '{virtual.name}'.")
        return


@profile_group.command("load")
@click.argument(
    "path",
    type=click.Path(
        exists=True,
        dir_okay=False,
        path_type=Path,
    ),
)
@click.option(
    "--apply",
    is_flag=True,
    help="Aplica la configuración al perfil integrado seleccionado.",
)
@click.option(
    "--output",
    type=click.Path(
        dir_okay=False,
        path_type=Path,
    ),
    help="Guarda la configuración cargada en otro archivo.",
)
@click.option(
    "--profile",
    "virtual_profile",
    type=str,
    help="Guarda la configuración como VirtualProfile con el nombre indicado.",
)
@click.pass_context
def profile_load(
    ctx: click.Context,
    path: Path,
    apply: bool,
    output: Path | None,
    virtual_profile: str | None,
) -> None:
    """
    Carga una configuración de perfil desde un archivo y la dirige a un destino.

    Usa --apply para aplicar la configuración al perfil integrado seleccionado.
    Usa --output para guardar una copia en otro archivo.
    Usa --profile para crear o reemplazar un perfil virtual."""
    destinations = int(apply) + int(output is not None) + int(virtual_profile is not None)

    if destinations != 1:
        raise click.UsageError(
            "Debes especificar exactamente uno de: --apply, --output PATH o --profile NAME."
        )

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        profile_schema = ProfileSchema.from_dict(data)
    except (
        OSError,
        json.JSONDecodeError,
        KeyError,
        TypeError,
        ValueError,
    ) as error:
        raise click.ClickException(
            f"No se pudo leer '{path}' como configuración de perfil: {error}"
        ) from error

    if apply:
        profile = resolve_profile(ctx)

        if isinstance(ctx.obj["session"].profile, str):
            raise click.ClickException(
                "No se puede aplicar una configuración directamente "
                "sobre un perfil virtual. Selecciona un perfil integrado."
            )

        profile.apply(profile_schema)

        click.echo(f"Configuración de '{path}' aplicada al perfil {profile.index}.")
        return

    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)

        output.write_text(
            json.dumps(
                profile_schema.to_dict(),
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )

        click.echo(f"Configuración de '{path}' guardada en '{output}'.")
        return

    if virtual_profile is not None:
        virtual = VirtualProfile(
            name=virtual_profile,
            config=profile_schema,
        )
        virtual.save()

        click.echo(f"Configuración de '{path}' guardada como perfil virtual '{virtual.name}'.")
        return


@profile_group.command("list")
@click.pass_context
def profile_list(ctx: click.Context) -> None:
    """Lista los perfiles integrados del dispositivo y los perfiles virtuales disponibles."""
    device = resolve_device(ctx)

    click.echo("Perfiles integrados:")
    for profile in device.profiles:
        marker = "*" if profile.is_active else " "
        click.echo(f"[{marker}] {profile.index}: {profile.name or 'sin nombre'}")

    click.echo()
    click.echo("Perfiles virtuales:")

    virtual_profiles = VirtualProfile.list()

    if not virtual_profiles:
        click.echo("  No hay perfiles virtuales.")
        return

    for profile in virtual_profiles:
        click.echo(f"  {profile.name}")


@profile_group.command("select")
@click.argument("selector")
@click.pass_context
def profile_select(ctx: click.Context, selector: str) -> None:
    """Selecciona un perfil para las operaciones posteriores sin modificar el dispositivo.

    Un índice selecciona un perfil integrado y un nombre selecciona un perfil virtual.
    La selección se conserva entre ejecuciones de MouseCtl."""
    session = ctx.obj["session"]
    session_store = ctx.obj["session_store"]

    device = resolve_device(ctx)

    try:
        profile_index = int(selector)
    except ValueError:
        virtual_profile = VirtualProfile.load(selector)

        session.profile = virtual_profile.name
        session_store.save(session)

        click.echo(f"Perfil virtual seleccionado: {virtual_profile.name}")
        return

    _get_profile(device, profile_index)

    session.profile = profile_index
    session_store.save(session)

    click.echo(f"Perfil integrado seleccionado: {profile_index} (dispositivo: {device.name})")


@profile_group.command("switch")
@click.argument("selector")
@click.option(
    "--commit/--no-commit",
    default=True,
    help="Aplica el cambio inmediatamente en el hardware.",
)
@click.pass_context
def profile_switch(
    ctx: click.Context,
    selector: str,
    commit: bool,
) -> None:
    """Cambia la configuración que está utilizando actualmente el dispositivo.

    Un índice activa ese perfil integrado en el hardware.
    Un nombre carga el perfil virtual indicado sobre el perfil integrado actualmente activo."""
    device = resolve_device(ctx)

    try:
        profile_index = int(selector)
    except ValueError:
        virtual_profile = VirtualProfile.load(selector)
        active_profile = device.active_profile

        active_profile.apply(virtual_profile.config)

        if commit:
            device.commit()

        click.echo(
            f"Perfil virtual '{virtual_profile.name}' aplicado sobre "
            f"el perfil integrado {active_profile.index}."
        )
        return

    profile = _get_profile(device, profile_index)
    profile.set_active()

    if commit:
        device.commit()

    click.echo(f"Perfil integrado activo cambiado a {profile.index}.")


@profile_group.command("delete")
@click.argument("name")
@click.option(
    "-y",
    "--yes",
    is_flag=True,
    help="Omite la confirmación antes de eliminar el perfil.",
)
@click.pass_context
def profile_delete(
    ctx: click.Context,
    name: str,
    yes: bool,
) -> None:
    """Elimina un perfil virtual.

    Solo pueden eliminarse perfiles virtuales. Los perfiles integrados
    pertenecen al dispositivo y no pueden eliminarse mediante MouseCtl.
    """
    try:
        int(name)
    except ValueError:
        pass
    else:
        raise click.ClickException(
            "Solo pueden eliminarse perfiles virtuales. "
            "Los perfiles integrados no pueden eliminarse."
        )

    try:
        profile = VirtualProfile.load(name)
    except MousectlError as error:
        raise click.ClickException(str(error)) from error

    if not yes:
        click.confirm(
            f"¿Eliminar el perfil virtual '{profile.name}'?",
            abort=True,
        )

    try:
        profile.path.unlink()
    except OSError as error:
        raise click.ClickException(
            f"No se pudo eliminar el perfil virtual '{profile.name}': {error}"
        ) from error

    session = ctx.obj["session"]

    if session.profile == profile.name:
        session.profile = None
        ctx.obj["session_store"].save(session)

    click.echo(f"Perfil virtual '{profile.name}' eliminado.")


def _get_profile(device: Device, profile_index: int) -> Profile:
    for profile in device.profiles:
        if profile.index == profile_index:
            return profile
    raise click.ClickException(f"No existe el perfil con índice {profile_index}.")


def _resolve_profile_selector(
    ctx: click.Context,
    selector: str,
) -> Profile | VirtualProfile:
    device = resolve_device(ctx)

    try:
        index = int(selector)
    except ValueError:
        return VirtualProfile.load(selector)

    return _get_profile(device, index)


def _resolve_selected_profile(
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
