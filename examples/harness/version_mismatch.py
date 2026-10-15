"""Attaches Tachyon from this interpreter to a process running another: TARGET_INTERPRETER."""

import subprocess
import sys
import time

target = subprocess.Popen([sys.argv[1], "-c", "import time; time.sleep(30)"])
try:
    time.sleep(0.5)
    print(f"attaching {sys.version.split()[0]}'s profiler to a {sys.argv[1].rsplit('/', 1)[-1]} process", flush=True)
    subprocess.run([sys.executable, "-m", "profiling.sampling", "dump", str(target.pid)])
finally:
    target.kill()
    target.wait()
