from typing import Final

MISSING: Final = object()

def greet(name: str | object = MISSING) -> str:
    if name is MISSING:
        return "Hello, stranger"
    return "Hello, " + name.upper()

greet(42)
