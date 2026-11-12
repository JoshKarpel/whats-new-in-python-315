DEFAULTS = {"retries": 3, "timeout": 10.0}

def fetch(url, options=DEFAULTS):
    options["url"] = url  # changes the default, for every later call
    return options

first = fetch("https://python.org")
second = fetch("https://pypi.org")
print(f"{first=}")
print(f"{DEFAULTS=}")
