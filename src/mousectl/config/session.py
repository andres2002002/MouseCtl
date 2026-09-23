from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class Session:
    """Estado persistente de selección de la CLI."""

    device: str | None = None
    profile: int | str | None = None

    def to_dict(self) -> dict:
        return {
            "device": self.device,
            "profile": self.profile,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Session:
        return cls(
            device=data.get("device"),
            profile=data.get("profile"),
        )


class SessionStore:
    """Persistencia del estado de sesión de la CLI."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> Session:
        if not self.path.exists():
            return Session()

        data = json.loads(self.path.read_text(encoding="utf-8"))
        return Session.from_dict(data)

    def save(self, session: Session) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)

        self.path.write_text(
            json.dumps(
                session.to_dict(),
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )
