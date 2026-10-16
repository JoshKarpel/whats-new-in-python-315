from functools import cache

@cache
def render(template, context):
    print("cache miss...")
    return template.format_map(context)

print(render("Hi {name}", frozendict(name="Ada")))
print(render("Hi {name}", frozendict(name="Ada")))
print(render("Hi {name}", {"name": "Ada"}))
