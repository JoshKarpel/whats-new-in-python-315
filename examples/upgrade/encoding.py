import sys

with open(__file__) as file:
    print("open() encoding:", file.encoding)
print("UTF-8 mode:", sys.flags.utf8_mode)
