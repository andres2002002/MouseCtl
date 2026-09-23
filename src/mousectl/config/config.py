from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from mousectl.config.session import SessionStore

APP_NAME = "mousectl"


def get_config_dir() -> Path:
    """Devuelve el directorio de configuración de MouseCtl."""
    xdg_config_home = os.environ.get("XDG_CONFIG_HOME")

    if xdg_config_home:
        return Path(xdg_config_home) / APP_NAME

    return Path.home() / ".config" / APP_NAME


@dataclass(slots=True)
class Config:
    """Configuración persistente de MouseCtl."""

    config_dir: Path
    profiles_dir: Path

    @classmethod
    def default(cls) -> Config:
        config_dir = get_config_dir()

        return cls(
            config_dir=config_dir,
            profiles_dir=config_dir / "profiles",
        )

    @property
    def config_path(self) -> Path:
        return self.config_dir / "config.json"

    @property
    def session_path(self) -> Path:
        return self.config_dir / "session.json"

    def ensure_directories(self) -> None:
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.profiles_dir.mkdir(parents=True, exist_ok=True)

    def to_dict(self) -> dict[str, Any]:
        return {
            "profiles_dir": str(self.profiles_dir),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Config:
        default = cls.default()

        profiles_dir = data.get("profiles_dir")
        if profiles_dir is None:
            profiles_dir = default.profiles_dir
        else:
            profiles_dir = Path(profiles_dir).expanduser()

        return cls(
            config_dir=default.config_dir,
            profiles_dir=profiles_dir,
        )


class ConfigStore:
    """Persistencia de configuración y sesión de MouseCtl."""

    def __init__(self, config: Config | None = None) -> None:
        self.config = config or Config.default()
        self.config.ensure_directories()

    @property
    def session_store(self) -> SessionStore:
        return SessionStore(self.config.session_path)

    def load_config(self) -> Config:
        path = self.config.config_path

        if not path.exists():
            return self.config

        data = json.loads(path.read_text(encoding="utf-8"))
        return Config.from_dict(data)

    def save_config(self, config: Config) -> None:
        config.ensure_directories()

        config.config_path.write_text(
            json.dumps(
                config.to_dict(),
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )
