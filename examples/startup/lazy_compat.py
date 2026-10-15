import sys

__lazy_modules__ = ["json"]

import json
import csv

print("json loaded:", "json" in sys.modules)
print("csv loaded:", "csv" in sys.modules)
