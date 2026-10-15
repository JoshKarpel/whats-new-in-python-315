MISSING = sentinel("MISSING")

def greet(name: str | MISSING = MISSING) -> str:
    if name is MISSING:
        return "Hello, stranger"
    return "Hello, " + name.upper()

greet(42)
