from __future__ import annotations

import json
from pathlib import Path

import click

from mousectl.models.config.device_config import DeviceConfig
from .common import resolve_device


_SAVE_SCOPES = {"resolutions", "buttons", "leds"}


@click.command("save")
@click.argument("path", type=click.Path(dir_okay=False, writable=True, path_type=Path))
@click.option(
    "--profile",
    "profile_indices",
    type=int,
    multiple=True,
    help="Perfil(es) a guardar (repetible). Por defecto, todos.",
)
@click.option(
    "--only",
    "only_scopes",
    default=None,
    help="Subconjunto separado por comas: resolutions,buttons,leds. Por defecto, todo.",
)
@click.pass_context
def save(
    ctx: click.Context, path: Path, profile_indices: tuple[int, ...], only_scopes: str | None
) -> None:
    """Guarda la configuración actual del dispositivo en PATH."""
    device = resolve_device(ctx)

    only: set[str] | None = None
    if only_scopes is not None:
        only = {scope.strip() for scope in only_scopes.split(",") if scope.strip()}
        unknown = only - _SAVE_SCOPES
        if unknown:
            raise click.ClickException(
                f"Valor(es) inválido(s) en --only: {sorted(unknown)}. "
                f"Válidos: {sorted(_SAVE_SCOPES)}."
            )

    indices = set(profile_indices) if profile_indices else None
    config = device.snapshot(profile_indices=indices, only=only)
    path.write_text(
        json.dumps(config.to_dict(), indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    click.echo(f"Configuración guardada en {path} ({len(config.profiles)} perfil(es)).")


@click.command("load")
@click.argument("path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--commit/--no-commit", default=True)
@click.pass_context
def load(ctx: click.Context, path: Path, commit: bool) -> None:
    """Carga una configuración guardada y la aplica al dispositivo."""
    device = resolve_device(ctx)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        config = DeviceConfig.from_dict(data)
    except (json.JSONDecodeError, KeyError, ValueError) as error:
        raise click.ClickException(
            f"No se pudo leer '{path}' como configuración de mousectl: {error}"
        ) from error

    device.apply(config)
    if commit:
        device.commit()
    click.echo(f"Configuración cargada desde {path} ({len(config.profiles)} perfil(es)).")
