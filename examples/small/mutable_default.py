DEFAULTS = {"retries": 3, "timeout": 10.0}

def fetch(url, options=DEFAULTS):
    options["url"] = url  # changes the default, for every later call
    return options

print(f"{fetch("https://python.org")=}")
print(f"{DEFAULTS=}")
