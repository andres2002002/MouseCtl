
from dataclasses import dataclass
from typing import Any
from mousectl.models.schemas.buttons_schemas import ActionType, MacroEvent, MacroEventType, SpecialFunction
from mousectl.models.base_model import BaseConfig

@dataclass(frozen=True, slots=True)
class ButtonConfig(BaseConfig):
    """Snapshot del mapeo de un botón. Solo uno de `button_target`/`special`/
    `macro` es relevante según `action_type`; los demás quedan en `None`."""

    action_type: ActionType
    button_target: int | None = None
    special: SpecialFunction | None = None
    macro: list[MacroEvent] | None = None

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {"action_type": self.action_type.name}
        if self.button_target is not None:
            data["button_target"] = self.button_target
        if self.special is not None:
            data["special"] = self.special.name
        if self.macro is not None:
            data["macro"] = [
                {"event_type": event.event_type.name, "value": event.value} for event in self.macro
            ]
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ButtonConfig":
        macro = None
        if "macro" in data:
            macro = [
                MacroEvent(
                    event_type=MacroEventType[event["event_type"]], value=int(event["value"])
                )
                for event in data["macro"]
            ]
        button_target = data.get("button_target")
        return cls(
            action_type=ActionType[data["action_type"]],
            button_target=int(button_target) if button_target is not None else None,
            special=SpecialFunction[data["special"]] if "special" in data else None,
            macro=macro,
        )
