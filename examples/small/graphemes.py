from unicodedata import iter_graphemes

band = "Spin\N{COMBINING DIAERESIS}al Tap"  # no one-code-point n-umlaut exists
graphemes = list(iter_graphemes(band))
print(f"{len(band)=}")
print(f"{len(graphemes)=}")
print(f"{band[::-1]=!a}")
print(f"{"".join(map(str, reversed(graphemes)))=!a}")
