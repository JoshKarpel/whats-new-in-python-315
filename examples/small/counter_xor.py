from collections import Counter

def deletions_to_anagram(a, b):
    """How many letters must go to make `a` and `b` anagrams?"""
    return (Counter(a) ^ Counter(b)).total()

print(Counter("cde") ^ Counter("abc"))
print(deletions_to_anagram("cde", "abc"))
