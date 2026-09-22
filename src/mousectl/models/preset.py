from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from mousectl.exceptions import MousectlError
from mousectl.models.config.profile_config import ProfileConfig

_PRESET_NAME_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")


@dataclass(frozen=True, slots=True)
class Preset:
    """Preset virtual de MouseCtl almacenado en el sistema."""

    name: str
    config: ProfileConfig

    @classmethod
    def directory(cls) -> Path:
        """Directorio donde se almacenan los presets."""
        return Path.home() / ".config" / "mousectl" / "presets"

    @classmethod
    def _validate_name(cls, name: str) -> None:
        if not name:
            raise MousectlError("El nombre del preset no puede estar vacío.")

        if not _PRESET_NAME_PATTERN.fullmatch(name):
            raise MousectlError(
                f"Nombre de preset inválido: '{name}'. "
                "Solo se permiten letras, números, '.', '_' y '-'."
            )

    @classmethod
    def _path_for(cls, name: str) -> Path:
        cls._validate_name(name)
        return cls.directory() / f"{name}.json"

    def save(self) -> None:
        """Guarda el preset en el directorio de presets."""
        path = self._path_for(self.name)
        path.parent.mkdir(parents=True, exist_ok=True)

        path.write_text(
            json.dumps(
                self.config.to_dict(),
                indent=2,
                ensure_ascii=False,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

    @classmethod
    def load(cls, name: str) -> Preset:
        """Carga un preset existente desde el sistema."""
        path = cls._path_for(name)

        if not path.is_file():
            raise MousectlError(f"No existe el preset '{name}'.")

        try:
            data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
            config = ProfileConfig.from_dict(data)
        except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
            raise MousectlError(f"No se pudo cargar el preset '{name}': {error}") from error

        return cls(name=name, config=config)

    @classmethod
    def list(cls) -> list[Preset]:
        """Lista los presets almacenados."""
        directory = cls.directory()

        if not directory.is_dir():
            return []

        presets: list[Preset] = []

        for path in sorted(directory.glob("*.json")):
            name = path.stem

            try:
                presets.append(cls.load(name))
            except MousectlError:
                # Un preset inválido no impide encontrar los demás.
                continue

        return presets

    def delete(self) -> None:
        """Elimina este preset del sistema."""
        path = self._path_for(self.name)

        if not path.is_file():
            raise MousectlError(f"No existe el preset '{self.name}'.")

        try:
            path.unlink()
        except OSError as error:
            raise MousectlError(f"No se pudo eliminar el preset '{self.name}': {error}") from error

    @property
    def path(self) -> Path:
        """Ruta del archivo que representa este preset."""
        return self._path_for(self.name)
