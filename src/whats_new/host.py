"""
What the deck resolves about the machine it runs on, once, at startup, so anything missing fails at launch
rather than on a key press on stage: the interpreters, and where Tachyon's flamegraph is served.
"""

import json
import urllib.request
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from whats_new.runs import Interpreters

FLAMEGRAPH_PORT = 8315
REFLECTION_URL = "https://reflection.int.exe.xyz/"
BASE_URL_VARIABLE = "WHATS_NEW_FLAMEGRAPH_BASE_URL"
BIND_VARIABLE = "WHATS_NEW_FLAMEGRAPH_BIND"


@dataclass(frozen=True, slots=True)
class FlamegraphSite:
    """Where the deck serves Tachyon's flamegraphs from (`bind`), and the URL a browser opens them at."""

    base_url: str
    bind: str
    port: int = FLAMEGRAPH_PORT

    @classmethod
    def resolve(cls, environ: Mapping[str, str]) -> FlamegraphSite:
        """
        From the environment if it names a base URL (as the image does), and otherwise from exe.dev's reflection
        integration, which names this VM, whose HTTPS proxy forwards the port behind the same login as zellij web.
        """
        if (base_url := environ.get(BASE_URL_VARIABLE)) is not None:
            return cls(base_url=base_url.rstrip("/"), bind=environ.get(BIND_VARIABLE, "0.0.0.0"))
        with urllib.request.urlopen(REFLECTION_URL, timeout=5) as response:
            name = json.load(response)["name"]
        return cls(base_url=f"https://{name}.exe.xyz:{FLAMEGRAPH_PORT}", bind="127.0.0.1")

    def url(self, file_name: str) -> str:
        return f"{self.base_url}/{file_name}"


EXPORT_FLAMEGRAPH_SITE = FlamegraphSite(base_url="http://127.0.0.1:8315", bind="127.0.0.1")
"""For headless renders (the export, the smoke test), which never serve or show a flamegraph."""


@dataclass(frozen=True, slots=True)
class Host:
    interpreters: Interpreters
    flamegraph: FlamegraphSite
    examples_copy: Path
    """
    Where each run copies `examples/` to, with the slide's edits written over their files, and runs from.
    Never `examples/` itself, since `just watch` restarts the deck when a file there changes.
    """
