from unicodedata import iter_graphemes

family = "👨‍👩‍👧‍👦"
print(len(family), len(list(iter_graphemes(family))))

text = "Café 🇯🇵 👩‍💻!"
print(text[::-1])
print("".join(str(g) for g in reversed(list(iter_graphemes(text)))))
