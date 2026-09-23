from __future__ import annotations

import click

from mousectl.commons import (
    HELP_SETTINGS,
    resolve_device,
    resolve_profile,
)
from mousectl.models.button import (
    ActionType,
    Button,
    MacroEvent,
    MacroEventType,
    SpecialFunction,
)
from mousectl.models.keycodes import KeyCode
from mousectl.models.profile import Profile
from mousectl.models.schemas.button_schema import ButtonSchema
from mousectl.models.schemas.profile_schema import ProfileSchema
from mousectl.models.virtual_profile import VirtualProfile

_MACRO_EVENT_ALIASES = {
    "press": MacroEventType.KEY_PRESSED,
    "release": MacroEventType.KEY_RELEASED,
    "wait": MacroEventType.WAIT,
}


def _resolve_selected_profile(
    ctx: click.Context,
) -> Profile | VirtualProfile:
    """Resuelve el perfil actualmente seleccionado."""
    profile_selector = ctx.obj["session"].profile

    if profile_selector is None:
        raise click.ClickException(
            "No hay un perfil seleccionado. Usa 'mousectl profile select <índice o nombre>'."
        )

    if isinstance(profile_selector, int):
        return resolve_profile(ctx)

    return VirtualProfile.load(profile_selector)


def _get_button(profile: Profile, button_index: int) -> Button:
    for button in profile.buttons:
        if button.index == button_index:
            return button

    raise click.ClickException(f"No existe el botón con índice {button_index}.")


def _get_virtual_button(
    profile: VirtualProfile,
    button_index: int,
) -> ButtonSchema:
    if profile.config.buttons is None:
        raise click.ClickException(
            f"El perfil virtual '{profile.name}' no contiene configuración de botones."
        )

    if button_index < 0 or button_index >= len(profile.config.buttons):
        raise click.ClickException(f"No existe el botón con índice {button_index}.")

    return profile.config.buttons[button_index]


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


def _describe_schema_mapping(button: ButtonSchema) -> str:
    if button.action_type is ActionType.BUTTON:
        return f"-> botón físico {button.button_target}"

    if button.action_type is ActionType.SPECIAL:
        return f"-> {button.special.name if button.special is not None else 'no especificado'}"

    if button.action_type is ActionType.MACRO:
        parts = []

        if button.macro is not None:
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
                "(TECLA es un nombre como 'A'/'KEY_A'/'LEFTCTRL' "
                "o un código numérico)."
                f"\nError: {error}"
            ) from error

        events.append(
            MacroEvent(
                event_type=event_type,
                value=value,
            )
        )

    return events


def _build_button_schema(
    button: int | None,
    special: str | None,
    macro: str | None,
) -> ButtonSchema:
    if button is not None:
        return ButtonSchema(
            action_type=ActionType.BUTTON,
            button_target=button,
        )

    if special is not None:
        try:
            special_function = SpecialFunction[special.upper()]
        except KeyError as error:
            raise click.ClickException(f"Función especial desconocida: '{special}'.") from error

        return ButtonSchema(
            action_type=ActionType.SPECIAL,
            special=special_function,
        )

    if macro is not None:
        return ButtonSchema(
            action_type=ActionType.MACRO,
            macro=_parse_macro_sequence(macro),
        )

    raise click.ClickException("Debe especificar --button, --special o --macro.")


@click.group("button", context_settings=HELP_SETTINGS)
def button_group() -> None:
    """Controla las acciones de los botones del perfil seleccionado."""


@button_group.command("list")
@click.pass_context
def button_list(ctx: click.Context) -> None:
    """Lista los botones del perfil seleccionado."""
    profile = _resolve_selected_profile(ctx)

    if isinstance(profile, VirtualProfile):
        click.echo(f"Perfil virtual: {profile.name}")

        if profile.config.buttons is None:
            click.echo("No contiene configuración de botones.")
            return

        for index, button in enumerate(profile.config.buttons):
            click.echo(f"{index}: {button.action_type.name} {_describe_schema_mapping(button)}")

        return

    click.echo(f"Perfil integrado: {profile.index} ({profile.name or 'sin nombre'})")

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
    """Cambia la acción de un botón del perfil seleccionado."""
    profile = _resolve_selected_profile(ctx)

    if isinstance(profile, VirtualProfile):
        new_button = _build_button_schema(
            button=button,
            special=special,
            macro=macro,
        )

        buttons = list(profile.config.buttons or [])
        if index < 0 or index >= len(buttons):
            raise click.ClickException(f"No existe el botón con índice {index}.")

        buttons[index] = new_button

        new_config = ProfileSchema(
            resolutions=profile.config.resolutions,
            buttons=buttons,
            leds=profile.config.leds,
        )

        updated_profile = VirtualProfile(
            name=profile.name,
            config=new_config,
        )
        updated_profile.save()

        click.echo(f"Botón {index} actualizado en el perfil virtual '{profile.name}'.")
        return

    button_instance = _get_button(profile, index)

    if button is not None:
        button_instance.set_button_mapping(button)

    elif special is not None:
        try:
            special_function = SpecialFunction[special.upper()]
        except KeyError as error:
            raise click.ClickException(f"Función especial desconocida: '{special}'.") from error

        button_instance.set_special(special_function)

    elif macro is not None:
        button_instance.set_macro(_parse_macro_sequence(macro))

    else:
        raise click.ClickException("Debe especificar --button, --special o --macro.")

    if commit:
        resolve_device(ctx).commit()

    click.echo(f"Botón {index} actualizado en el perfil {profile.index}.")


@button_group.command("get")
@click.argument("index", type=int)
@click.pass_context
def button_get(
    ctx: click.Context,
    index: int,
) -> None:
    """Muestra la configuración de un botón del perfil seleccionado."""
    profile = _resolve_selected_profile(ctx)

    if isinstance(profile, VirtualProfile):
        button = _get_virtual_button(profile, index)

        click.echo(f"Perfil virtual: {profile.name}")
        click.echo(f"Botón {index}: {button.action_type.name} {_describe_schema_mapping(button)}")
        return

    button = _get_button(profile, index)

    click.echo(f"Perfil integrado: {profile.index} ({profile.name or 'sin nombre'})")
    click.echo(f"Botón {index}: {button.action_type.name} {_describe_mapping(button)}")
