import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-f", "-foo")
print(f"{parser.parse_args(["-f", "bar"])=}")
