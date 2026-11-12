import enum
from datetime import timedelta
from typing import Final, Literal

class _Missing(enum.Enum):
    MISSING = enum.auto()

MISSING: Final = _Missing.MISSING

def wait(
    host: str, timeout: timedelta | None | Literal[_Missing.MISSING] = MISSING
) -> float | None:
    if timeout is MISSING:  # not passed: it depends on the host
        timeout = timedelta(seconds=1 if host == "localhost" else 30)
    return None if timeout is None else timeout.total_seconds()  # None: wait forever

wait("python.org", timeout=30)
