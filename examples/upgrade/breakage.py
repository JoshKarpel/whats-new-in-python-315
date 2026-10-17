import base64, datetime, sqlite3, sys, warnings
from typing import NamedTuple, TypedDict

def attempt(label, call):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        try:
            result = f"ok {call()!r}"
        except Exception as error:
            result = f"{type(error).__name__}"
    warned = " (DeprecationWarning)" if any(w.category is DeprecationWarning for w in caught) else ""
    print(f"{label:<26} {result}{warned}")

print(sys.version.split()[0])
attempt('strptime("29", "%d")', lambda: datetime.datetime.strptime("29", "%d"))
attempt('connect(":memory:", 5.0)', lambda: sqlite3.connect(":memory:", 5.0))
attempt('NamedTuple("P", x=int)', lambda: NamedTuple("P", x=int))
attempt('TypedDict("TD")', lambda: TypedDict("TD"))
attempt('urlsafe_b64decode(b"aGk")', lambda: base64.urlsafe_b64decode(b"aGk"))
