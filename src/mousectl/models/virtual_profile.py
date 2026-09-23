from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from mousectl.config.config import ConfigStore
from mousectl.exceptions import MousectlError
from mousectl.models.schemas.profile_schema import ProfileSchema

_VIRTUAL_PROFILE_NAME_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")


@dataclass(frozen=True, slots=True)
class VirtualProfile:
    """Perfil virtual de MouseCtl almacenado en el sistema."""

    name: str
    config: ProfileSchema

    @classmethod
    def directory(cls) -> Path:
        """Directorio donde se almacenan los perfiles virtuales."""
        return ConfigStore().load_config().profiles_dir

    @classmethod
    def _validate_name(cls, name: str) -> None:
        if not name:
            raise MousectlError("El nombre del perfil virtual no puede estar vacío.")

        if not _VIRTUAL_PROFILE_NAME_PATTERN.fullmatch(name):
            raise MousectlError(
                f"Nombre de perfil virtual inválido: '{name}'. "
                "Solo se permiten letras, números, '.', '_' y '-'."
            )

    @classmethod
    def _path_for(cls, name: str) -> Path:
        cls._validate_name(name)
        return cls.directory() / f"{name}.json"

    @property
    def path(self) -> Path:
        """Ruta del archivo que representa este perfil virtual."""
        return self._path_for(self.name)

    @classmethod
    def list(cls) -> list[VirtualProfile]:
        """Lista los perfiles virtuales almacenados."""
        directory = cls.directory()

        if not directory.is_dir():
            return []

        profiles: list[VirtualProfile] = []

        for path in sorted(directory.glob("*.json")):
            name = path.stem

            try:
                profiles.append(cls.load(name))
            except MousectlError:
                # Un perfil inválido no impide encontrar los demás.
                continue

        return profiles

    def rename(self, new_name: str) -> VirtualProfile:
        """Renombra el perfil virtual y su archivo."""
        new_path = self._path_for(new_name)

        if new_path.exists():
            raise MousectlError(f"Ya existe el perfil virtual '{new_name}'.")

        try:
            self.path.rename(new_path)
        except OSError as error:
            raise MousectlError(
                f"No se pudo renombrar el perfil virtual '{self.name}' a '{new_name}': {error}"
            ) from error

        return VirtualProfile(
            name=new_name,
            config=self.config,
        )

    def save(self) -> None:
        """Guarda el perfil virtual en el directorio configurado."""
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
    def load(cls, name: str) -> VirtualProfile:
        """Carga un perfil virtual existente."""
        path = cls._path_for(name)

        if not path.is_file():
            raise MousectlError(f"No existe el perfil virtual '{name}'.")

        try:
            data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
            config = ProfileSchema.from_dict(data)
        except (
            OSError,
            json.JSONDecodeError,
            KeyError,
            TypeError,
            ValueError,
        ) as error:
            raise MousectlError(f"No se pudo cargar el perfil virtual '{name}': {error}") from error

        return cls(name=name, config=config)
