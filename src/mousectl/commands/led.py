from __future__ import annotations

import click

from mousectl.commons import HELP_SETTINGS, resolve_device, resolve_selected_profile
from mousectl.models.led import Color, LedMode
from mousectl.models.schemas.led_schema import LedSchema
from mousectl.models.virtual_profile import VirtualProfile


@click.group("led", context_settings=HELP_SETTINGS)
def led_group() -> None:
    """Controla la iluminación del perfil seleccionado."""


@led_group.command("list")
@click.pass_context
def led_list(ctx: click.Context) -> None:
    """Lista los LEDs y su configuración del perfil seleccionado."""
    profile = resolve_selected_profile(ctx)

    if isinstance(profile, VirtualProfile):
        click.echo(f"Perfil virtual: {profile.name}")

        if profile.config.leds is None:
            click.echo("No contiene configuración de LEDs.")
            return

        for index, led in enumerate(profile.config.leds):
            click.echo(f"[{index}] {led.mode.name}: {led.color}, brillo={led.brightness}")
        return

    click.echo(f"Perfil integrado: {profile.index} ({profile.name or 'sin nombre'})")

    for led in profile.leds:
        click.echo(f"[{led.index}] {led.mode.name}: {led.color}, brillo={led.brightness}")


def _get_integrated_led(profile, index: int):
    if index < 0 or index >= len(profile.leds):
        raise click.ClickException(f"El perfil solo tiene {len(profile.leds)} LED(s).")
    return profile.leds[index]


def _get_virtual_led(profile: VirtualProfile, index: int) -> LedSchema:
    leds = profile.config.leds or []

    if index < 0 or index >= len(leds):
        raise click.ClickException(f"El perfil virtual solo tiene {len(leds)} LED(s).")

    return leds[index]


@led_group.command("get")
@click.argument("index", type=int)
@click.option("--color", "-c", is_flag=True, help="Muestra el color.")
@click.option("--mode", "-m", is_flag=True, help="Muestra el modo.")
@click.option("--brightness", "-b", is_flag=True, help="Muestra el brillo.")
@click.option("--duration", "-d", is_flag=True, help="Muestra la duración del efecto.")
@click.pass_context
def led_get(
    ctx: click.Context,
    index: int,
    color: bool,
    mode: bool,
    brightness: bool,
    duration: bool,
) -> None:
    """Obtiene una o varias propiedades del LED INDEX.

    Sin opciones muestra todas las propiedades. Con una o más opciones,
    muestra únicamente las propiedades solicitadas.
    """
    profile = resolve_selected_profile(ctx)

    show_all = not any((color, mode, brightness, duration))

    if isinstance(profile, VirtualProfile):
        led = _get_virtual_led(profile, index)

        click.echo(f"Perfil virtual: {profile.name}")
        click.echo(f"LED: {index}")

        if show_all or color:
            click.echo(f"Color: {led.color}")

        if show_all or mode:
            click.echo(f"Modo: {led.mode.name}")

        if show_all or brightness:
            click.echo(f"Brillo: {led.brightness}")

        if show_all or duration:
            click.echo(f"Duración: {led.effect_duration} ms")

        return

    led = _get_integrated_led(profile, index)

    click.echo(f"Perfil integrado: {profile.index} ({profile.name or 'sin nombre'})")
    click.echo(f"LED: {index}")

    if show_all or color:
        click.echo(f"Color: {led.color}")

    if show_all or mode:
        click.echo(f"Modo: {led.mode.name}")

    if show_all or brightness:
        click.echo(f"Brillo: {led.brightness}")

    if show_all or duration:
        click.echo(f"Duración: {led.effect_duration} ms")


@led_group.command("set")
@click.argument("index", type=int)
@click.option("--color", "-c", type=str, help="Color hexadecimal, por ejemplo ff0000.")
@click.option(
    "--mode",
    "-m",
    type=click.Choice([mode.name.lower() for mode in LedMode]),
    help="Modo de iluminación.",
)
@click.option(
    "--brightness",
    "-b",
    type=click.IntRange(0, 255),
    help="Brillo entre 0 y 255.",
)
@click.option(
    "--duration",
    "-d",
    type=click.IntRange(0),
    help="Duración del efecto en milisegundos.",
)
@click.option("--commit/--no-commit", default=True)
@click.option(
    "--apply",
    is_flag=True,
    default=False,
    help="Aplica los cambios al perfil integrado activo.",
)
@click.pass_context
def led_set(
    ctx: click.Context,
    index: int,
    color: str | None,
    mode: str | None,
    brightness: int | None,
    duration: int | None,
    commit: bool,
    apply: bool,
) -> None:
    """Cambia una o varias propiedades del LED INDEX.

    En un perfil integrado modifica directamente el dispositivo.
    En un perfil virtual modifica y guarda su configuración.
    Con --apply, los cambios de un perfil virtual también se aplican
    al perfil integrado activo.
    """
    if all(value is None for value in (color, mode, brightness, duration)):
        raise click.ClickException(
            "Debe especificar al menos una propiedad: --color, --mode, --brightness o --duration."
        )

    profile = resolve_selected_profile(ctx)

    if isinstance(profile, VirtualProfile):
        current_led = _get_virtual_led(profile, index)

        new_color = current_led.color
        new_mode = current_led.mode
        new_brightness = current_led.brightness
        new_duration = current_led.effect_duration

        if color is not None:
            try:
                new_color = Color.from_hex(color)
            except (TypeError, ValueError) as error:
                raise click.ClickException(f"Color hexadecimal inválido: '{color}'.") from error

        if mode is not None:
            new_mode = LedMode[mode.upper()]

        if brightness is not None:
            new_brightness = brightness

        if duration is not None:
            new_duration = duration

        new_led = LedSchema(
            mode=new_mode,
            color=new_color,
            brightness=new_brightness,
            effect_duration=new_duration,
        )

        leds = list(profile.config.leds or [])
        leds[index] = new_led

        new_config = profile.config.__class__(
            resolutions=profile.config.resolutions,
            buttons=profile.config.buttons,
            leds=leds,
            active_resolution=profile.config.active_resolution,
        )

        VirtualProfile(
            name=profile.name,
            config=new_config,
        ).save()

        if apply:
            device = resolve_device(ctx)
            target = device.active_profile
            target_led = _get_integrated_led(target, index)

            if color is not None:
                target_led.set_color(new_color)

            if mode is not None:
                target_led.set_mode(new_mode)

            if brightness is not None:
                target_led.set_brightness(new_brightness)

            if duration is not None:
                target_led.set_effect_duration(new_duration)

            device.commit()

            click.echo(
                f"LED {index} actualizado en el perfil virtual "
                f"'{profile.name}' y aplicado al perfil integrado "
                f"{target.index}."
            )
        else:
            click.echo(
                f"LED {index} actualizado en el perfil virtual "
                f"'{profile.name}'. El cambio se aplicará al hacer switch."
            )

        return

    led = _get_integrated_led(profile, index)

    if color is not None:
        try:
            led.set_color(Color.from_hex(color))
        except (TypeError, ValueError) as error:
            raise click.ClickException(f"Color hexadecimal inválido: '{color}'.") from error

    if mode is not None:
        led.set_mode(LedMode[mode.upper()])

    if brightness is not None:
        led.set_brightness(brightness)

    if duration is not None:
        led.set_effect_duration(duration)

    if commit:
        resolve_device(ctx).commit()

    click.echo(f"LED {index} actualizado en el perfil {profile.index}.")
