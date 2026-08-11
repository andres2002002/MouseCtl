# mousectl

CLI para controlar ratones y periféricos compatibles con `libratbag` (a través del
daemon `ratbagd` vía DBus), sin depender de Piper ni de su GUI.

## Requisitos

- `ratbagd` corriendo como servicio de sistema (paquete `libratbag`/`ratbagd` de tu
  distro), con tu usuario en el grupo con permiso para hablar con el bus del sistema
  (o una regla polkit/dbus adecuada).
- Python 3.11+
- `dbus-python`. **Este es el punto que suele fallar** — ver más abajo.

### Instalando `dbus-python`

`dbus-python` compila un binding en C contra `libdbus-1`, no es puro Python.
`pip install dbus-python` invoca `meson`, y si faltan las cabeceras de
desarrollo de `dbus-1`, falla con `Dependency "dbus-1" not found (tried pkg-config)`.

Hay dos formas de resolverlo, de más a menos recomendada:

**Opción A — usar el paquete precompilado del sistema (recomendado en Linux):**

```bash
# Debian/Ubuntu
sudo apt install python3-dbus

# Fedora
sudo dnf install python3-dbus

# Arch
sudo pacman -S python-dbus
```

Luego crea el venv con `--system-site-packages` para que vea ese paquete:

```bash
python3 -m venv --system-site-packages venv
source venv/bin/activate
pip install -e ".[dev]"
```

Esto evita compilar nada y es la práctica estándar para bindings nativos de
DBus/GObject en Linux (lo mismo aplica a `pygobject`).

**Opción B — compilarlo con pip (si de verdad lo necesitas dentro del venv):**
instala antes las cabeceras de desarrollo:

```bash
# Debian/Ubuntu
sudo apt install libdbus-1-dev libglib2.0-dev pkg-config build-essential

# Fedora
sudo dnf install dbus-devel glib2-devel pkgconf-pkg-config gcc

# Arch
sudo pacman -S dbus glib2 pkgconf base-devel
```

y luego `pip install -e ".[dev]"` normalmente.

## Instalación

```bash
pip install .
# o, para desarrollo:
pip install -e ".[dev]"
```

## Tests

La capa `models/` no importa `dbus-python` en absoluto — depende de un
protocolo (`RatbagBusLike`) implementado tanto por `RatbagBus` (real, en
`dbus/bus.py`) como por un doble de prueba en `tests/conftest.py`. Esto
significa que puedes correr la suite completa **sin tener `dbus-python`
instalado ni un bus de sistema real disponible**:

```bash
pytest
# con cobertura
pytest --cov=mousectl --cov-report=term-missing
```

## Tipado / Pyright

`dbus-python` no publica stubs, así que el proyecto trae stubs mínimos en
`typings/dbus/` (cubren solo lo que usa `dbus/bus.py`, el único módulo que
importa `dbus` directamente) y un `pyrightconfig.json` que los registra vía
`stubPath`. Si tu editor sigue marcando `dbus.SystemBus` como desconocido,
comprueba que abre el proyecto desde la raíz (donde está `pyrightconfig.json`)
y no desde `src/`.

## Uso

```bash
# Ver dispositivos detectados
mousectl list-devices

# Ver estado del dispositivo (si solo hay uno conectado)
mousectl status

# Si hay varios dispositivos, seleccionar por nombre
mousectl --device G502 status

# Perfiles
mousectl profile list
mousectl profile switch 1

# LEDs
mousectl led color "#00ff00"
mousectl led mode breathing
mousectl led brightness 200

# DPI
mousectl dpi set 1600
mousectl dpi set 1600 2400   # X e Y distintos

# Botones
mousectl button list
mousectl button set-button 3 1              # botón 3 -> click del botón físico 1
mousectl button set-special 4 doubleclick   # botón 4 -> doble clic
mousectl button set-macro 5 "press:30,release:30,press:31,release:31"
mousectl button disable 6
```

### Sobre los keycodes de macros

`button set-macro` espera una lista de eventos `press:KEYCODE` / `release:KEYCODE`
separados por comas, **en orden**. El `KEYCODE` es el código HID de teclado que
usa `ratbagd` internamente para el evento — en la práctica, para teclas
alfanuméricas y de función coincide con las constantes `KEY_*` de
`linux/input-event-codes.h` (ej. `KEY_A = 30`, `KEY_B = 48`, `KEY_LEFTCTRL = 29`).
Puedes consultarlas con:

```bash
grep -E "define KEY_[A-Z0-9_]+\s+[0-9]" /usr/include/linux/input-event-codes.h
```

Ejemplo — macro que envía "Ctrl+C" (keydown Ctrl, keydown C, keyup C, keyup Ctrl):

```bash
mousectl button set-macro 5 "press:29,press:46,release:46,release:29"
```

Todos los comandos que modifican estado aceptan `--no-commit` para dejar el
cambio en el buffer del dispositivo sin escribirlo a hardware (equivalente al
`mouse.commit()` diferido del script de pruebas original).

## Estructura

```
src/mousectl/
├── exceptions.py       # Excepciones de dominio
├── dbus/
│   ├── constants.py     # Nombres de bus/interfaces
│   ├── bus.py            # Wrapper de dbus.SystemBus()
│   └── object.py         # Clase base RatbagObject (Get/Set/Call genéricos)
├── models/
│   ├── device.py         # Device: enumera dispositivos, perfil activo, commit()
│   ├── profile.py        # Profile: resoluciones, botones, leds
│   ├── resolution.py     # Resolution/Dpi
│   ├── button.py         # Button/ActionType/SpecialFunction/MacroEvent (API real: Mapping (uv))
│   └── led.py             # Led/LedMode/Color (con validación y from_hex)
└── cli.py                # Comandos click
```

## Licencia

MIT — ver [LICENSE](LICENSE).
