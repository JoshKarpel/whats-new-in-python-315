from pprint import pprint

config = {
    "project": {
        "name": "deck",
        "dependencies": ["counterweight", "numpy"],
    },
}
pprint(config, width=30)
pprint(config, expand=True, width=30)
