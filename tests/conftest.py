import subprocess

import pytest

from whats_new.host import EXPORT_FLAMEGRAPH_SITE
from whats_new.host import EXPORT_PID
from whats_new.host import Host
from whats_new.runs import Capability
from whats_new.runs import Interpreters


@pytest.fixture(scope="session")
def interpreters() -> Interpreters:
    return Interpreters.resolve()


@pytest.fixture(scope="session")
def host(interpreters: Interpreters, tmp_path_factory: pytest.TempPathFactory) -> Host:
    return Host(
        interpreters=interpreters,
        flamegraph=EXPORT_FLAMEGRAPH_SITE,
        pid=EXPORT_PID,
        examples_copy=tmp_path_factory.mktemp("examples"),
    )


@pytest.fixture(scope="session")
def capabilities() -> frozenset[Capability]:
    """What this machine allows, probed rather than assumed: a container usually can't run perf."""
    perf = subprocess.run(["perf", "record", "-q", "-o", "/dev/null", "--", "true"], capture_output=True, check=False)
    return frozenset({Capability.PERF} if perf.returncode == 0 else set())
