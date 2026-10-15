rows = [[1, 2], [3, 4], [5]]
print([*row for row in rows])

configs = [{"debug": False, "port": 80}, {"debug": True}]
print({**config for config in configs})

print({*group for group in [{1, 2}, {2, 3}]})
