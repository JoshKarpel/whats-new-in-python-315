import sys

with open(__file__) as file:
    print(f"{file.encoding=}")
print(f"{sys.flags.utf8_mode=}")
