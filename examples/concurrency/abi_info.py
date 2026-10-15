import sys

print(sys.abi_info)
print("GIL enabled:", sys._is_gil_enabled())
