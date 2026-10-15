from unicodedata import iter_graphemes

band = "Spin̈al Tap"
print(f"{len(band)=}")
print(f"{len(list(iter_graphemes(band)))=}")
print(f"{band[::-1]=}")
print(f"{"".join(str(g) for g in reversed(list(iter_graphemes(band))))=}")
