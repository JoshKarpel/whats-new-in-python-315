import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-f", "-foo")
print(parser.parse_args(["-f", "bar"]))
