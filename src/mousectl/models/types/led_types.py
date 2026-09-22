from dataclasses import dataclass
from enum import IntEnum
from typing import Any

from mousectl.exceptions import InvalidColorError


class LedMode(IntEnum):
    OFF = 0
    ON = 1
    CYCLE = 2
    BREATHING = 3


@dataclass(frozen=True, slots=True)
class Color:
    red: int
    green: int
    blue: int

    def __post_init__(self) -> None:
        for name, value in (("red", self.red), ("green", self.green), ("blue", self.blue)):
            if not 0 <= value <= 255:
                raise InvalidColorError(
                    f"El componente '{name}' debe estar entre 0 y 255, recibido {value}."
                )

    @classmethod
    def from_hex(cls, value: str) -> 'Color':
        text = value.lstrip("#")
        if len(text) != 6:
            raise InvalidColorError(f"Color hexadecimal inválido: '{value}'.")
        try:
            red = int(text[0:2], 16)
            green = int(text[2:4], 16)
            blue = int(text[4:6], 16)
        except ValueError as error:
            raise InvalidColorError(f"Color hexadecimal inválido: '{value}'.") from error
        return cls(red=red, green=green, blue=blue)

    def __str__(self) -> str:
        return f"#{self.red:02x}{self.green:02x}{self.blue:02x}"