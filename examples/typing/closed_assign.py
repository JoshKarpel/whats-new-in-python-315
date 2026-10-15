from typing import TypedDict


class Book(TypedDict, closed=True):
    isbn: str


class Hardback(TypedDict):
    isbn: str
    pages: int


hardback: Hardback = {"isbn": "978-0", "pages": 300}
book: Book = hardback
