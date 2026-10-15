DEFAULTS = frozendict(retries=3, timeout=10.0)

def fetch(url, options=DEFAULTS):
    options = options | {"url": url}  # a new frozendict
    return options

print(f"{fetch("https://python.org")=}")
print(f"{DEFAULTS=}")
