from dataclasses import dataclass
from enum import IntEnum

class ActionType(IntEnum):
    """Valores confirmados por introspección real (`busctl introspect` contra
    una G502 HERO, ratbagd 0.17-3build2) y por la doc `enums.html` de
    libratbag (`RATBAG_BUTTON_ACTION_TYPE_*`).

    OJO: esto difiere del `dbus.rst` de la rama `master` de GitHub, que
    describe una versión más nueva sin `KEY` (con `MACRO=3`). La versión
    empaquetada en Ubuntu 24.04 (y probablemente la mayoría de distros
    estables) sigue usando esta numeración con `KEY` como tipo separado.
    Verificado: `ActionTypes` de un botón real devolvió `[1, 2, 4]`
    (BUTTON, SPECIAL, MACRO) — sin `3` (KEY) para ese botón en particular.
    """

    INVALID = -1
    NONE = 0
    BUTTON = 1
    SPECIAL = 2
    KEY = 3
    MACRO = 4
    UNKNOWN = 1000


class SpecialFunction(IntEnum):
    """Tabla "Special button functions" del doc DBus. Base 0x40000000.

    NOTA: el tipo interno del variant de `Mapping` para ActionType.SPECIAL
    no está verificado contra hardware real todavía (solo confirmamos
    BUTTON, vía introspección). Antes de usar `set_special` en un botón
    importante, pruébalo primero en uno prescindible — si el tipo interno
    real no es `u`, ratbagd devolverá un error explícito tipo
    "expected X got Y" y lo ajustamos de inmediato.
    """

    UNKNOWN = 0x40000000
    DOUBLECLICK = 0x40000001
    WHEEL_LEFT = 0x40000002
    WHEEL_RIGHT = 0x40000003
    WHEEL_UP = 0x40000004
    WHEEL_DOWN = 0x40000005
    RATCHET_MODE_SWITCH = 0x40000006
    RESOLUTION_CYCLE_UP = 0x40000007
    RESOLUTION_CYCLE_DOWN = 0x40000008
    RESOLUTION_UP = 0x40000009
    RESOLUTION_DOWN = 0x4000000A
    RESOLUTION_ALTERNATE = 0x4000000B
    RESOLUTION_DEFAULT = 0x4000000C
    PROFILE_CYCLE_UP = 0x4000000D
    PROFILE_CYCLE_DOWN = 0x4000000E
    PROFILE_UP = 0x4000000F
    PROFILE_DOWN = 0x40000010
    SECOND_MODE = 0x40000011
    BATTERY_LEVEL = 0x40000012


class MacroEventType(IntEnum):
    """Tipo de evento dentro del array `a(uu)` de un macro."""

    NONE = 0
    KEY_PRESSED = 1
    KEY_RELEASED = 2
    WAIT = 3


@dataclass(frozen=True, slots=True)
class MacroEvent:
    """Un evento individual de un macro: `(tipo, keycode HID)`."""

    event_type: MacroEventType
    value: int

    def __repr__(self) -> str:
        if self.event_type is MacroEventType.WAIT:
            return f"MacroEvent(wait:{self.value}ms)"
        return f"MacroEvent({self.event_type.name.lower()}:{self.value})"