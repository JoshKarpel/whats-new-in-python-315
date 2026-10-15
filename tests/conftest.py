import subprocess

import pytest

from whats_new.host import EXPORT_FLAMEGRAPH_SITE
from whats_new.host import Host
from whats_new.runs import Capability
from whats_new.runs import Interpreters


@pytest.fixture(scope="session")
def interpreters() -> Interpreters:
    return Interpreters.resolve()


@pytest.fixture(scope="session")
def host(interpreters: Interpreters) -> Host:
    return Host(interpreters=interpreters, flamegraph=EXPORT_FLAMEGRAPH_SITE)


@pytest.fixture(scope="session")
def capabilities() -> frozenset[Capability]:
    """What this machine allows, probed rather than assumed: a container usually can't run perf."""
    perf = subprocess.run(["perf", "record", "-q", "-o", "/dev/null", "--", "true"], capture_output=True, check=False)
    return frozenset({Capability.PERF} if perf.returncode == 0 else set())
