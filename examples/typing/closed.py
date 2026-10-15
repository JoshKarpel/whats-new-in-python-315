from typing import TypedDict

class Book(TypedDict, closed=True):
    isbn: str

class DVD(TypedDict, closed=True):
    region: int

def describe(item: Book | DVD) -> str:
    if "isbn" in item:
        reveal_type(item)
        return item["isbn"]
    reveal_type(item)
    return str(item["region"])
