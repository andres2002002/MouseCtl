from __future__ import annotations

from pathlib import Path

import click

from mousectl.commons import HELP_SETTINGS
from mousectl.config.config import ConfigStore


@click.group("config", context_settings=HELP_SETTINGS)
def config_group() -> None:
    """Gestiona la configuración de MouseCtl."""


@config_group.group("profiles-dir")
def profiles_dir_group() -> None:
    """Gestiona el directorio donde se almacenan los perfiles."""


@profiles_dir_group.command("get")
def profiles_dir_get() -> None:
    """Muestra el directorio configurado para los perfiles."""
    store = ConfigStore()
    config = store.load_config()

    click.echo(config.profiles_dir)


@profiles_dir_group.command("set")
@click.argument(
    "path",
    type=click.Path(path_type=Path),
)
def profiles_dir_set(path: Path) -> None:
    """Establece el directorio donde se almacenan los perfiles."""
    store = ConfigStore()
    config = store.load_config()

    config.profiles_dir = path.expanduser()
    store.save_config(config)

    click.echo(f"Directorio de perfiles: {config.profiles_dir}")
