from __future__ import annotations

from typing import Any

from mousectl.dbus.constants import IFACE_BUTTON
from mousectl.dbus.object import RatbagObject
from mousectl.dbus.protocol import RatbagBusLike
from mousectl.exceptions import InvalidValueError, WrongActionTypeError

from mousectl.models.schemas.buttons_schemas import ActionType, MacroEvent, MacroEventType, SpecialFunction
from mousectl.models.base_model import BaseModel
from mousectl.models.config.button_config import ButtonConfig

class Button(RatbagObject, BaseModel):
    """Botón físico de un perfil.

    La propiedad `Mapping` es `(uv)`: primer elemento `ActionType`, segundo
    un variant cuyo contenido depende de ese tipo. Confirmado contra
    hardware real para BUTTON (`(uv) 1 u 1` → botón físico 1). Special y
    Macro siguen la doc oficial (`u` y `a(uu)` respectivamente) pero no
    están verificados contra este hardware exacto todavía.

    No existen métodos separados `SetButtonMapping`/`SetSpecialMapping`/
    `SetMacro` en esta versión de ratbagd — todo se escribe seteando
    `Mapping` directamente.
    """

    interface_name = IFACE_BUTTON

    def __init__(self, bus: RatbagBusLike, path: str) -> None:
        super().__init__(bus, path)

    @property
    def index(self) -> int:
        return int(self._get("Index"))

    @property
    def action_types(self) -> list[ActionType]:
        return [ActionType(int(value)) for value in self._get("ActionTypes")]

    @property
    def action_type(self) -> ActionType:
        action_type, _value = self._get("Mapping")
        return ActionType(int(action_type))

    def _require_action_type(self, expected: ActionType) -> Any:
        action_type, value = self._get("Mapping")
        current = ActionType(int(action_type))
        if current is not expected:
            raise WrongActionTypeError(
                f"El botón {self.index} está mapeado a {current.name}, no a {expected.name}."
            )
        return value

    @property
    def button_mapping(self) -> int:
        """Botón físico al que apunta. Solo válido si `action_type is BUTTON`."""
        return int(self._require_action_type(ActionType.BUTTON))

    @property
    def special_function(self) -> SpecialFunction:
        """Función especial asignada. Solo válido si `action_type is SPECIAL`."""
        return SpecialFunction(int(self._require_action_type(ActionType.SPECIAL)))

    @property
    def macro(self) -> list[MacroEvent]:
        """Secuencia de eventos del macro. Solo válido si `action_type is MACRO`."""
        value = self._require_action_type(ActionType.MACRO)

        return [
            MacroEvent(event_type=MacroEventType(int(event_type)), value=int(raw_value))
            for event_type, raw_value in value
        ]

    def set_button_mapping(self, target_button: int) -> None:
        """Mapea este botón a otro botón físico (numeración lógica de ratbagd).

        Verificado contra hardware real.
        """
        if target_button < 0:
            raise InvalidValueError("El número de botón no puede ser negativo.")
        mapping = self.bus.make_struct(
            (
                self.bus.make_uint32(int(ActionType.BUTTON)),
                self.bus.make_uint32(target_button, variant_level=1),
            )
        )
        self._set("Mapping", mapping)

    def set_special(self, special: SpecialFunction) -> None:
        """Mapea este botón a una función especial (doubleclick, dpi cycle, etc.).

        No verificado todavía contra hardware real — si ratbagd rechaza el
        tipo interno, el error dirá exactamente qué tipo espera.
        """
        mapping = self.bus.make_struct(
            (
                self.bus.make_uint32(int(ActionType.SPECIAL)),
                self.bus.make_uint32(int(special), variant_level=1),
            )
        )
        self._set("Mapping", mapping)

    def set_macro(self, events: list[MacroEvent]) -> None:
        """Mapea este botón a una secuencia de teclas (macro).

        No verificado todavía contra hardware real — si ratbagd rechaza el
        tipo interno, el error dirá exactamente qué tipo espera.
        """
        if not events:
            raise InvalidValueError("Un macro necesita al menos un evento.")

        event_tuples = [
            self.bus.make_struct(
                (self.bus.make_uint32(int(event.event_type)), self.bus.make_uint32(event.value))
            )
            for event in events
        ]
        macro_value = self.bus.make_array(event_tuples, signature="(uu)", variant_level=1)
        mapping = self.bus.make_struct((self.bus.make_uint32(int(ActionType.MACRO)), macro_value))
        self._set("Mapping", mapping)

    def disable(self) -> None:
        self._call("Disable")

    def snapshot(self) -> ButtonConfig:
        action_type = self.action_type
        if action_type is ActionType.BUTTON:
            return ButtonConfig(action_type=action_type, button_target=self.button_mapping)
        if action_type is ActionType.SPECIAL:
            return ButtonConfig(action_type=action_type, special=self.special_function)
        if action_type is ActionType.MACRO:
            return ButtonConfig(action_type=action_type, macro=self.macro)
        # NONE (deshabilitado) / KEY / UNKNOWN: sin payload que capturar todavía.
        return ButtonConfig(action_type=action_type)

    def apply(self, config: ButtonConfig) -> None:
        if config.action_type is ActionType.BUTTON:
            if config.button_target is None:
                raise InvalidValueError("ButtonConfig de tipo BUTTON sin 'button_target'.")
            self.set_button_mapping(config.button_target)
        elif config.action_type is ActionType.SPECIAL:
            if config.special is None:
                raise InvalidValueError("ButtonConfig de tipo SPECIAL sin 'special'.")
            self.set_special(config.special)
        elif config.action_type is ActionType.MACRO:
            if not config.macro:
                raise InvalidValueError("ButtonConfig de tipo MACRO sin 'macro'.")
            self.set_macro(config.macro)
        elif config.action_type is ActionType.NONE:
            self.disable()
        else:
            raise WrongActionTypeError(
                f"No se puede aplicar un ButtonConfig con action_type={config.action_type.name} "
                "todavía (KEY/UNKNOWN no están soportados para escritura)."
            )


    def __repr__(self) -> str:
        return f"Button(index={self.index}, action_type={self.action_type.name})"