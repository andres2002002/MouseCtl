from __future__ import annotations

import click

from mousectl.commons import HELP_SETTINGS, resolve_device
from mousectl.models.button import ActionType, Button, MacroEvent, MacroEventType, SpecialFunction
from mousectl.models.keycodes import KeyCode

_MACRO_EVENT_ALIASES = {
    "press": MacroEventType.KEY_PRESSED,
    "release": MacroEventType.KEY_RELEASED,
    "wait": MacroEventType.WAIT,
}


def _get_button(device, button_index: int) -> Button:
    profile = device.active_profile
    for button in profile.buttons:
        if button.index == button_index:
            return button
    raise click.ClickException(f"No existe el botón con índice {button_index}.")


def _resolve_keycode(text: str) -> int:
    text = text.strip()
    try:
        return int(text)
    except ValueError:
        pass

    name = text.upper()
    if not name.startswith("KEY_"):
        name = "KEY_" + name
    try:
        return int(KeyCode[name])
    except KeyError as error:
        raise ValueError(
            f"Tecla desconocida: '{text}'. Usa un nombre de tecla "
            "(ej. 'A', 'KEY_A', 'LEFTCTRL', 'ENTER') o un código numérico."
            f"\nError: {error}"
        ) from error


def _keycode_name(value: int) -> str:
    try:
        return KeyCode(value).name
    except ValueError:
        return str(value)


def _describe_mapping(button: Button) -> str:
    if button.action_type is ActionType.BUTTON:
        return f"-> botón físico {button.button_mapping}"
    if button.action_type is ActionType.SPECIAL:
        return f"-> {button.special_function.name}"
    if button.action_type is ActionType.MACRO:
        parts = []
        for event in button.macro:
            if event.event_type is MacroEventType.NONE:
                continue
            if event.event_type is MacroEventType.WAIT:
                parts.append(f"wait:{event.value}")
            else:
                label = "press" if event.event_type is MacroEventType.KEY_PRESSED else "release"
                parts.append(f"{label}:{_keycode_name(event.value)}")
        return f"-> macro: {' '.join(parts)}"
    return ""


def _parse_macro_sequence(sequence: str) -> list[MacroEvent]:
    events: list[MacroEvent] = []
    for token in sequence.split(","):
        token = token.strip()
        if not token:
            continue
        try:
            kind, value_str = token.split(":", 1)
            event_type = _MACRO_EVENT_ALIASES[kind.strip().lower()]
            if event_type is MacroEventType.WAIT:
                value = int(value_str.strip())
            else:
                value = _resolve_keycode(value_str.strip())
        except (ValueError, KeyError) as error:
            raise click.ClickException(
                f"Evento de macro inválido: '{token}'. Formato esperado: "
                "'press:TECLA', 'release:TECLA' o 'wait:MILISEGUNDOS' "
                f"(TECLA es un nombre como 'A'/'KEY_A'/'LEFTCTRL' o un código numérico)."
                f"\nError: {error}"
            ) from error
        events.append(MacroEvent(event_type=event_type, value=value))
    return events


@click.group("button", context_settings=HELP_SETTINGS)
def button_group() -> None:
    """Controla las acciones de los botones del perfil activo."""


@button_group.command("list")
@click.pass_context
def button_list(ctx: click.Context) -> None:
    """Lista los botones del perfil activo."""
    device = resolve_device(ctx)
    profile = device.active_profile
    click.echo(f"Perfil activo: {profile.index} ({profile.name or 'sin nombre'})")
    for button in profile.buttons:
        click.echo(f"{button.index}: {button.action_type.name} {_describe_mapping(button)}")


@button_group.command("set")
@click.argument("index", type=int)
@click.option("--button", type=int, required=False)
@click.option("--special", type=str, required=False)
@click.option("--macro", type=str, required=False)
@click.option("--commit/--no-commit", default=True)
@click.pass_context
def button_set(
    ctx: click.Context,
    index: int,
    button: int | None,
    special: str | None,
    macro: str | None,
    commit: bool,
) -> None:
    """Fija la acción de un botón."""
    device = resolve_device(ctx)
    profile = device.active_profile

    if button is not None:
        profile.buttons[index].set_button_mapping(button)
    elif special is not None:
        profile.buttons[index].set_special(SpecialFunction[special.upper()])
    elif macro is not None:
        button_instance = _get_button(device, index)
        button_instance.set_macro(_parse_macro_sequence(macro))
    else:
        raise click.ClickException("Debe especificar --button, --special o --macro")

    if commit:
        device.commit()
    click.echo(f"Botón {index} actualizado en el perfil {profile.index}.")
