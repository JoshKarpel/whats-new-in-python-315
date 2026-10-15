import sys
lazy import asyncio, decimal, email.mime.multipart, http.client
lazy import inspect, sqlite3, tomllib, typing, xml.etree.ElementTree, zipfile

if sys.argv[1:] == ["--version"]:
    print("mytool 1.0")
