from typing import TypedDict

class Headers(TypedDict, extra_items=str):
    host: str

headers: Headers = {"host": "python.org", "accept": "text/html"}
headers["user-agent"] = "curl/8"
headers["retries"] = 3
