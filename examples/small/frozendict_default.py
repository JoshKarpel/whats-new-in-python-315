DEFAULTS = frozendict(retries=3, timeout=10.0)

def fetch(url, options=DEFAULTS):
    options = options | {"url": url}  # a new frozendict
    return options

first = fetch("https://python.org")
second = fetch("https://pypi.org")
print(f"{first=}")
print(f"{DEFAULTS=}")
