from __future__ import annotations

import json
import sys
from pathlib import Path


import click

from mousectl import __version__
from mousectl.dbus.bus import RatbagBus
from mousectl.exceptions import MousectlError, MultipleDevicesFoundError
from mousectl.models.button import ActionType, Button, MacroEvent, MacroEventType, SpecialFunction
from mousectl.models.config.device_config import DeviceConfig
from mousectl.models.device import Device
from mousectl.models.led import Color, LedMode
from mousectl.models.keycodes import KeyCode
from mousectl.models.profile import Profile


@click.group()
@click.version_option(__version__, prog_name="mousectl")
@click.option(
    "--device",
    "-d",
    "device_name",
    default=None,
    help=(
        "Subcadena del nombre del dispositivo a controlar. "
        "Si se omite, se usa el único dispositivo detectado."
    ),
)
@click.pass_context
def main(ctx: click.Context, device_name: str | None) -> None:
    """CLI para controlar ratones y periféricos compatibles con libratbag (ratbagd)."""
    ctx.ensure_object(dict)
    ctx.obj["bus"] = RatbagBus()
    ctx.obj["device_name"] = device_name


def _resolve_device(ctx: click.Context) -> Device:
    bus: RatbagBus = ctx.obj["bus"]
    device_name: str | None = ctx.obj["device_name"]

    if device_name is not None:
        return Device.find(bus, device_name)

    devices = Device.list_all(bus)
    if len(devices) > 1:
        names = ", ".join(f"'{device.name}'" for device in devices)
        raise MultipleDevicesFoundError(
            f"Hay varios dispositivos conectados ({names}). Usa --device para elegir uno."
        )
    return devices[0]


@main.command("list-devices")
@click.pass_context
def list_devices(ctx: click.Context) -> None:
    """Lista los dispositivos ratbag detectados en el bus."""
    bus: RatbagBus = ctx.obj["bus"]
    for device in Device.list_all(bus):
        click.echo(f"{device.name} ({device.model}) -> {device.path}")


@main.command("status")
@click.pass_context
def status(ctx: click.Context) -> None:
    """Muestra el estado actual del dispositivo: perfil, dpi y leds."""
    device = _resolve_device(ctx)
    profile = device.active_profile

    click.echo(f"Dispositivo: {device.name}")
    click.echo(f"Perfil activo: {profile.index} ({profile.name or 'sin nombre'})")
    click.echo(f"DPI activo: {profile.active_resolution.resolution}")

    for led in profile.leds:
        click.echo(f"Led {led.index}: modo={led.mode.name}, color={led.color}")


@main.group("profile")
def profile_group() -> None:
    """Gestiona los perfiles del dispositivo."""


@profile_group.group("name")
def profile_name_group() -> None:
    """Subgrupo para acciones sobre el nombre del perfil."""


@profile_name_group.command("set")
@click.option("index", "-i", type=int, default=None, show_default=True)
@click.argument("name", type=str)
@click.option("--commit/--no-commit", default=True)
@click.pass_context
def profile_name_set(ctx: click.Context, index: int | None, name: str, commit: bool) -> None:
    """Establece el nombre del perfil actual."""
    device = _resolve_device(ctx)
    if index is None:
        index = device.active_profile.index
    profile = device.profiles[index]
    profile.set_name(name)
    if commit:
        device.commit()
    click.echo(f"Perfil {profile.index} renombrado a {profile.name}.")

@profile_name_group.command("get")
@click.option("index", "-i", type=int, default=None, show_default=True)
@click.pass_context
def profile_get(ctx: click.Context, index: int | None) -> None:
    """Obtiene el perfil con el índice INDEX."""
    device = _resolve_device(ctx)
    if index is None:
        index = device.active_profile.index
    
    if index < 0 or index >= len(device.profiles):
        raise click.ClickException(f"No existe el perfil con índice {index}.")
    
    profile = device.profiles[index]
    click.echo(f"Perfil {profile.index}: {profile.name or 'sin nombre'}")

@profile_group.command("list")
@click.pass_context
def profile_list(ctx: click.Context) -> None:
    """Lista los perfiles disponibles, marcando el activo."""
    device = _resolve_device(ctx)
    for profile in device.profiles:
        marker = "*" if profile.is_active else " "
        click.echo(f"[{marker}] {profile.index}: {profile.name or 'sin nombre'}")


@profile_group.command("switch")
@click.argument("index", type=int)
@click.option(
    "--commit/--no-commit",
    default=True,
    help="Aplica el cambio inmediatamente en el hardware.",
)
@click.pass_context
def profile_switch(ctx: click.Context, index: int, commit: bool) -> None:
    """Activa el perfil con el índice INDEX."""
    device = _resolve_device(ctx)
    for profile in device.profiles:
        if profile.index == index:
            profile.set_active()
            if commit:
                device.commit()
            click.echo(f"Perfil activo cambiado a {index}.")
            return
    raise click.ClickException(f"No existe el perfil con índice {index}.")

def _get_profile(device: Device, profile_index: int) -> Profile:
    for profile in device.profiles:
        if profile.index == profile_index:
            return profile
    raise click.ClickException(f"No existe el perfil con índice {profile_index}.")


@profile_group.command("copy")
@click.argument("src", type=int)
@click.argument("dst", type=int)
@click.option("--commit/--no-commit", default=True)
@click.pass_context
def profile_copy(ctx: click.Context, src: int, dst: int, commit: bool) -> None:
    """Copia toda la configuración (resoluciones, botones, leds) del perfil SRC al DST."""
    device = _resolve_device(ctx)
    src_profile = _get_profile(device, src)
    dst_profile = _get_profile(device, dst)

    dst_profile.apply(src_profile.snapshot())

    if commit:
        device.commit()
    click.echo(f"Perfil {src} copiado a perfil {dst}.")


@main.group("led")
def led_group() -> None:
    """Controla los LEDs del perfil activo."""

@led_group.command("list")
@click.pass_context
def led_list(ctx: click.Context) -> None:
    """Lista los LEDs del perfil activo."""
    device = _resolve_device(ctx)
    profile = device.active_profile
    click.echo(f"Perfil activo: {profile.index} ({profile.name or 'sin nombre'})")
    for led in profile.leds:
        click.echo(f"[{led.index}] {led.mode.name}: {led.color}")

@led_group.command("color")
@click.argument("color", type=str)
@click.option(
    "--index", "-i", "led_index", default=0, show_default=True, help="Índice del LED a modificar."
)
@click.option("--commit/--no-commit", default=True)
@click.pass_context
def led_color(ctx: click.Context, color: str, led_index: int, commit: bool) -> None:
    """Cambia el color de un LED. COLOR en formato hexadecimal, ej. #ff0000."""
    device = _resolve_device(ctx)
    profile = device.active_profile
    leds = profile.leds

    if led_index >= len(leds):
        raise click.ClickException(f"El perfil solo tiene {len(leds)} LED(s).")

    leds[led_index].set_color(Color.from_hex(color))

    if commit:
        device.commit()
    click.echo(f"Led {led_index} actualizado a {color} en el perfil {profile.index}.")


@led_group.command("mode")
@click.argument("mode", type=click.Choice([m.name.lower() for m in LedMode]))
@click.option("--index", "-i", "led_index", default=0, show_default=True)
@click.option("--commit/--no-commit", default=True)
@click.pass_context
def led_mode(ctx: click.Context, mode: str, led_index: int, commit: bool) -> None:
    """Cambia el modo de un LED (off, on, cycle, breathing)."""
    device = _resolve_device(ctx)
    profile = device.active_profile
    leds = profile.leds

    if led_index >= len(leds):
        raise click.ClickException(f"El perfil solo tiene {len(leds)} LED(s).")

    leds[led_index].set_mode(LedMode[mode.upper()])

    if commit:
        device.commit()
    click.echo(f"Led {led_index} cambiado a modo {mode} en el perfil {profile.index}.")


@led_group.command("brightness")
@click.argument("value", type=click.IntRange(0, 255))
@click.option("--index", "-i", "led_index", default=0, show_default=True)
@click.option("--commit/--no-commit", default=True)
@click.pass_context
def led_brightness(ctx: click.Context, value: int, led_index: int, commit: bool) -> None:
    """Fija el brillo (0-255) de un LED."""
    device = _resolve_device(ctx)
    profile = device.active_profile
    leds = profile.leds

    if led_index >= len(leds):
        raise click.ClickException(f"El perfil solo tiene {len(leds)} LED(s).")

    leds[led_index].set_brightness(value)

    if commit:
        device.commit()
    click.echo(f"Led {led_index} brillo actualizado a {value} en el perfil {profile.index}.")


@main.group("dpi")
def dpi_group() -> None:
    """Controla los presets de resolución (DPI) del perfil activo."""


@dpi_group.command("list")
@click.pass_context
def dpi_list(ctx: click.Context) -> None:
    """Lista los presets de resolución (DPI) del perfil activo."""
    device = _resolve_device(ctx)
    profile = device.active_profile
    for resolution in profile.resolutions:
        marker = "*" if resolution.is_active else " "
        click.echo(f"[{marker}] {resolution.index}: {resolution.resolution}")

@dpi_group.command("get")
@click.option("--index", "-i", type=int, default=None, show_default=True)
@click.pass_context
def dpi_get(ctx: click.Context, index: int | None) -> None:
    """Obtiene el DPI activo."""
    device = _resolve_device(ctx)
    if index is None:
        index = device.active_profile.index
    
    if index < 0 or index >= len(device.profiles):
        raise click.ClickException(f"No existe el perfil con índice {index}.")
    
    profile = device.profiles[index]
    resolution = profile.active_resolution
    click.echo(f"Perfil {profile.index}: {profile.name or 'sin nombre'}")
    click.echo(f"DPI activo: {resolution.resolution}")

@dpi_group.command("set")
@click.argument("x", type=int)
@click.argument("y", type=int, required=False)
@click.option("--commit/--no-commit", default=True)
@click.pass_context
def dpi_set(ctx: click.Context, x: int, y: int | None, commit: bool) -> None:
    """Fija el DPI activo. Si Y se omite, se usa el mismo valor que X."""
    device = _resolve_device(ctx)
    profile = device.active_profile
    resolution = profile.active_resolution

    y_value = y if y is not None else x
    resolution.set_resolution(x, y_value)

    if commit:
        device.commit()
    click.echo(f"DPI actualizado a {x} x {y_value} en el perfil {profile.index}.")


def _get_button(device: Device, button_index: int) -> Button:
    profile = device.active_profile
    for button in profile.buttons:
        if button.index == button_index:
            return button
    raise click.ClickException(f"No existe el botón con índice {button_index}.")

_MACRO_EVENT_ALIASES = {
    "press": MacroEventType.KEY_PRESSED,
    "release": MacroEventType.KEY_RELEASED,
    "wait": MacroEventType.WAIT,
}

def _resolve_keycode(text: str) -> int:
    """Resuelve 'A', 'KEY_A' o un código numérico crudo a su valor entero.

    Prioriza el código numérico si el texto es un entero puro (compatible
    con lo que ya existía); si no, busca el nombre en `KeyCode` aceptando
    el prefijo 'KEY_' opcional, insensible a mayúsculas.
    """
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
    """Nombre legible de un código de tecla, o el número si no está en `KeyCode`."""
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
                continue  # terminador interno, no aporta información al usuario
            if event.event_type is MacroEventType.WAIT:
                parts.append(f"wait:{event.value}")
            else:
                label = "press" if event.event_type is MacroEventType.KEY_PRESSED else "release"
                parts.append(f"{label}:{_keycode_name(event.value)}")
        return f"-> macro: {' '.join(parts)}"
    return ""

def _parse_macro_sequence(sequence: str) -> list[MacroEvent]:
    """Parsea 'press:A,release:A,wait:200,press:LEFTCTRL,release:LEFTCTRL' a
    `MacroEvent`s.

    El valor de 'press'/'release' acepta un nombre de `KeyCode` (con o sin
    prefijo 'KEY_', insensible a mayúsculas) o un código numérico crudo de
    `linux/input-event-codes.h`. El valor de 'wait' son milisegundos.
    """
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
                "'press:TECLA', 'release:TECLA' o 'wait:MILISEGUNDOS' (TECLA es "
                "un nombre como 'A'/'KEY_A'/'LEFTCTRL' o un código numérico)."
                f"\nError: {error}"
            ) from error
        events.append(MacroEvent(event_type=event_type, value=value))
    return events


@main.group("button")
def button_group() -> None:
    """Controla las acciones de los botones del perfil activo."""

@button_group.command("list")
@click.pass_context
def button_list(ctx: click.Context) -> None:
    """Lista los botones del perfil activo."""
    device = _resolve_device(ctx)
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
def button_set(ctx: click.Context, index: int, button: int | None, special: str | None, macro: str | None, commit: bool) -> None:
    """Fija la acción de un botón. Si la acción es un número, se interpreta como un mapeo de botón. Si es una palabra, se interpreta como una función especial."""
    device = _resolve_device(ctx)
    profile = device.active_profile

    if button is not None:
        profile.buttons[index].set_button_mapping(button)
    elif special is not None:
        profile.buttons[index].set_special(SpecialFunction[special.upper()])
    elif macro is not None:
        button_instance = _get_button(device, index)
        events = _parse_macro_sequence(macro)
        button_instance.set_macro(events)
    else:
        raise click.ClickException("Debe especificar --button, --special o --macro")

    if commit:
        device.commit()
    click.echo(f"Botón {index} actualizado en el perfil {profile.index}.")

_SAVE_SCOPES = {"resolutions", "buttons", "leds"}

@main.command("save")
@click.argument("path", type=click.Path(dir_okay=False, writable=True, path_type=Path))
@click.option(
    "--profile",
    "profile_indices",
    type=int,
    multiple=True,
    help="Perfil(es) a guardar (repetible, ej. --profile 0 --profile 1). Por defecto, todos.",
)
@click.option(
    "--only",
    "only_scopes",
    default=None,
    help="Subconjunto separado por comas: resolutions,buttons,leds. Por defecto, todo.",
)
@click.pass_context
def save(
    ctx: click.Context, path: Path, profile_indices: tuple[int, ...], only_scopes: str | None
) -> None:
    """Guarda la configuración actual del dispositivo (o de perfiles puntuales) en PATH."""
    device = _resolve_device(ctx)

    only: set[str] | None = None
    if only_scopes is not None:
        only = {scope.strip() for scope in only_scopes.split(",") if scope.strip()}
        unknown = only - _SAVE_SCOPES
        if unknown:
            raise click.ClickException(
                f"Valor(es) inválido(s) en --only: {sorted(unknown)}. "
                f"Válidos: {sorted(_SAVE_SCOPES)}."
            )

    indices = set(profile_indices) if profile_indices else None
    config = device.snapshot(profile_indices=indices, only=only)

    path.write_text(
        json.dumps(config.to_dict(), indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    click.echo(f"Configuración guardada en {path} ({len(config.profiles)} perfil(es)).")


@main.command("load")
@click.argument("path", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--commit/--no-commit", default=True)
@click.pass_context
def load(ctx: click.Context, path: Path, commit: bool) -> None:
    """Carga una configuración guardada con `save` desde PATH y la aplica al dispositivo."""
    device = _resolve_device(ctx)

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        config = DeviceConfig.from_dict(data)
    except (json.JSONDecodeError, KeyError, ValueError) as error:
        raise click.ClickException(
            f"No se pudo leer '{path}' como configuración de mousectl: {error}"
        ) from error

    device.apply(config)

    if commit:
        device.commit()
    click.echo(f"Configuración cargada desde {path} ({len(config.profiles)} perfil(es)).")


def run() -> None:
    """Punto de entrada del script (registrado en pyproject.toml)."""
    try:
        main(obj={})
    except MousectlError as error:
        click.echo(f"Error: {error}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    run()
