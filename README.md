# mousectl

CLI para controlar mouses y periféricos compatibles con `libratbag`
(vía el daemon `ratbagd` sobre DBus), sin depender de Piper ni de su GUI.

## Por qué

Esto lo hice en un par de tardes para mi propio mouse (un Logitech
G502 HERO), intentando generalizarlo un poco por si alguien más
está en una situación parecida — no es una herramienta pulida ni
un reemplazo serio de Piper, es un side project para resolver una
fricción puntual.

Con Piper, cambiar de perfil o de alguna configuracion dentro de un perfil me
generaba fricción constante: el estado que mostraba la interfaz no
siempre correspondía al estado real del mouse, y arreglarlo
significaba entrar a la GUI, tocar algo, y aplicar.

`mousectl` resuelve esa fricción con dos cosas simples:

- Cambiar a un perfil específico es un solo comando, para recuperarme
  en segundos si algo se desconfigura.
- Los perfiles se pueden exportar a un archivo JSON y volver a
  cargar, así siempre tengo una forma de dejar el mouse "donde lo dejé".

## Requisitos

### Sistema

- `ratbagd` corriendo como servicio de sistema (paquete `libratbag`/`ratbagd`
  de tu distro). Verifica con:

```bash
  systemctl status ratbagd
```

- Tu usuario con permiso para hablar con el bus del sistema. En la
  mayoría de distros esto ya viene resuelto por la política DBus que
  instala el propio paquete `ratbagd`. Si `mousectl list-devices` no
  detecta nada aunque `ratbagd` esté corriendo, revisa los permisos
  del bus antes de sospechar de la instalación de Python.

### Paquetes

- Python 3.11+
- `dbus-python`. **Este es el punto que suele fallar** — ver más abajo.

### Instalando `dbus-python`

No mentire, esto lo puso la IA en la que me apoye para crear el proyecto, fue la IA
la que encontro la solucion, solo lo implmente y olvide cual era el fallo, confio en que
lo que describe en esta seccion es la realidad, si en el futuro recuerdo los fallos y
soluciones concretas las pondre y quitare este mensaje.

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

## Uso

Los comandos por defecto hacen `--commit` en cada comando, si no es el comportamiento que deseas,
puedes usar el flag `--no-commit`. En ese caso, los cambios solo se aplicaran
cuando ejecutes un comando con el flag `--commit`.

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

# Botones
mousectl button list
mousectl button set 3 --button 1              # botón 3 -> click del botón físico 1
mousectl button set 4 --special doubleclick   # botón 4 -> doble clic
# Los macros se pueden hacer de 3 formas distintas:
# Nota: Los ejemplos seran para asignar el comando ctrl + c.
# 1. por raw keycode
mousectl button set 5 --macro "press:29,press:46,release:46,release:29"
# 2. por keycode con mayusculas o minusculas
mousectl button set 5 --macro "press:KEY_LEFTCTRL,press:KEY_C,release:KEY_C,release:KEY_LEFTCTRL"
# 3. por button name sin importar mayusculas o minusculas
mousectl button set 5 --macro "press:leftctrl,press:c,release:c,release:leftctrl"

# para facilitar la escritura, añadí un alias para los keycodes comunes, por ejemplo:
# ctrl -> leftctrl
# shift -> leftshift
# alt -> leftalt
# por comodidad:
# meta -> leftmeta
# win -> leftmeta
# super -> leftmeta
```

Ejemplo de uso real:

```bash
# Mostrar dispositivos disponibles
mousectl list-devices
# Output:
Logitech G502 HERO Gaming Mouse (usb:046d:c08b:0) -> /org/freedesktop/ratbag1/device/hidraw3

# Ver estado del dispositivo (si solo hay uno conectado)
mousectl status
# Output:
Dispositivo: Logitech G502 HERO Gaming Mouse
Perfil activo: 1 (sin nombre)
DPI activo: 20000
Led 0: modo=ON, color=#ffffff
Led 1: modo=ON, color=#ffffff

# Si hay varios dispositivos, seleccionar por nombre
mousectl --device G502 status
# Output:
Dispositivo: Logitech G502 HERO Gaming Mouse
Perfil activo: 1 (sin nombre)
DPI activo: 20000
Led 0: modo=ON, color=#ffffff
Led 1: modo=ON, color=#ffffff

# Listar perfiles y cambiar al perfil 1
mousectl profile list
mousectl profile switch 1
# Output:
[ ] 0: sin nombre
[*] 1: sin nombre
[ ] 2: sin nombre
[ ] 3: sin nombre
[ ] 4: sin nombre
Perfil activo cambiado a 1.

# Ver botones disponibles
mousectl button list
# Output:
Perfil activo: 0 (sin nombre)
0: BUTTON -> botón físico 1
1: BUTTON -> botón físico 2
2: BUTTON -> botón físico 3
3: BUTTON -> botón físico 4
4: BUTTON -> botón físico 5
5: MACRO -> macro: press:KEY_LEFTCTRL press:KEY_W release:KEY_W release:KEY_LEFTCTRL
6: MACRO -> macro: press:KEY_LEFTCTRL press:KEY_C release:KEY_C release:KEY_LEFTCTRL
7: MACRO -> macro: press:KEY_LEFTCTRL press:KEY_V release:KEY_V release:KEY_LEFTCTRL
8: MACRO -> macro: press:KEY_LEFTALT press:KEY_F4 release:KEY_F4 release:KEY_LEFTALT
9: SPECIAL -> WHEEL_RIGHT
10: SPECIAL -> WHEEL_LEFT

# Cambiar color del LED a azul
mousectl led color "#0000ff"
# Output:
Led 0 actualizado a 0000ff en el perfil 1.

# Cambiar modo del LED a breathing
mousectl led mode breathing
# Output:
Led 0 cambiado a modo breathing en el perfil 1.

# Cambiar brillo del LED a 200
mousectl led brightness 200
# Output:
Led 0 brillo actualizado a 200 en el perfil 1.

# Cambiar botón 3 a click del botón físico 1
mousectl button set 3 --button 1
# Output:
Botón 3 actualizado en el perfil 1.

# Cambiar botón 4 a doble clic
mousectl button set 4 --special doubleclick
# Output:
Botón 4 actualizado en el perfil 1.

# Cambiar botón 5 a macro ctrl + c
mousectl button set 5 --macro "press:leftctrl,press:c,release:c,release:leftctrl"
# Output:
Botón 5 actualizado en el perfil 1.

# Cambiar DPI a 1600
mousectl dpi set 1600
# Output:
DPI actualizado a 1600 en el perfil 1.

# Guardar perfiles
mousectl save --profile 0 --profile 1 "path/to/file.json"
# Output:
Configuración guardada en path/to/file.json

# Cargar perfiles
mousectl load "path/to/file.json"
# Output:
Configuración cargada desde path/to/file.json (2 perfil(es))
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

## Limitaciones conocidas

- **Perfiles 2+ no funcionan en el Logitech G502 HERO con `ratbagd 0.17`.**
  Es un bug confirmado de `libratbag`
  ([libratbag/libratbag#1473](https://github.com/libratbag/libratbag/issues/1473)),
  no algo que `mousectl` pueda corregir desde este lado. Si tu mouse y
  versión de `ratbagd` coinciden con este caso, solo el perfil activo
  por defecto es confiable.

## Hoja de ruta

- **Soporte para múltiples dispositivos.** Los comandos actualmente
  asumen un solo dispositivo conectado (o requieren `--device` para
  desambiguar). La idea es soportar selección más flexible sin romper
  el comportamiento actual cuando solo hay un dispositivo.

- **Sintaxis más robusta para modificar perfiles sin depender del
  perfil activo.** Hoy los comandos operan implícitamente sobre el
  perfil activo (`active_profile`). La idea es poder targetear un
  perfil específico en el mismo comando, por ejemplo:

```bash
  mousectl button set 4 --macro "press:29,press:46,release:46,release:29" --profile 1
```

(o con flags cortas, `-m`/`-p`, si la CLI adopta ese estilo en el futuro).

- **`commit`** Pendiente de implementar, para encadenar comandos sin hacer commit en cada uno.

- **`copy` para `button` y `led`.** Se dejó fuera de la primera
  versión por diferencias entre la estructura planeada y la real del
  proyecto en el momento de implementarlos.

- **`--macro-default` para macros comunes** (Ctrl+C, Ctrl+V, etc.),
  para no tener que escribir la secuencia de keycodes a mano cada vez.
  Pendiente de evaluar si de verdad hace falta en un flujo de trabajo
  normal o si es sobre-ingeniería para un caso de uso poco frecuente.

## Tests

(debo actulaizar los tests, no son representativos del estado actual del proyecto,
asi que ignore esta seccion por ahora)

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

## Estructura

```
src/mousectl/
├── exceptions.py       # Excepciones de dominio
├── dbus/
│   ├── constants.py     # Nombres de bus/interfaces
│   ├── bus.py            # Wrapper de dbus.SystemBus()
│   ├── protocol.py       # Protocolo para el bus.
│   └── object.py         # Clase base RatbagObject (Get/Set/Call genéricos)
├── models/
│   ├── config/           # Configuración
│   ├── schemas/          # Schemas de los modelos.
│   ├── base_model.py     # Clase base para los modelos.
│   ├── device.py         # Device: enumera dispositivos, perfil activo, commit()
│   ├── keycodes.py       # Keycodes
│   ├── profile.py        # Profile: resoluciones, botones, leds
│   ├── resolution.py     # Resolution/Dpi
│   ├── button.py         # Button/ActionType/SpecialFunction/MacroEvent (API real: Mapping (uv))
│   └── led.py             # Led/LedMode/Color (con validación y from_hex)
└── cli.py                # Comandos click
```

## Licencia

MIT — ver [LICENSE](LICENSE).
