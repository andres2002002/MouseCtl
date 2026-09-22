from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class Dpi:
    x: int
    y: int

    def __str__(self) -> str:
        return f"{self.x} x {self.y}" if self.x != self.y else str(self.x)
