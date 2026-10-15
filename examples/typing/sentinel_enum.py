import enum
from typing import Final, Literal

class _Missing(enum.Enum):
    MISSING = enum.auto()

MISSING: Final = _Missing.MISSING

def greet(name: str | Literal[_Missing.MISSING] = MISSING) -> str:
    if name is MISSING:
        return "Hello, stranger"
    return "Hello, " + name.upper()

greet(42)
