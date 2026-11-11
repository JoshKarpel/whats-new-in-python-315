"""Builds a throwaway venv with a .pth that runs code at startup, then adds a matching .start,
starting `python -c pass` in it after each, and printing each command it starts."""

import subprocess
import sys
import tempfile
from pathlib import Path

PTH = 'import sys; print("  hello from greet.pth", file=sys.stderr)\n'
START = "greet:hello\n"
PACKAGE = 'import sys\n\ndef hello():\n    print("  hello from greet.start", file=sys.stderr)\n'

with tempfile.TemporaryDirectory() as directory:
    venv = Path(directory) / "venv"
    subprocess.run([sys.executable, "-m", "venv", "--without-pip", venv], check=True)
    interpreter = venv / "bin" / "python"
    site_packages = Path(
        subprocess.check_output([interpreter, "-c", "import site; print(site.getsitepackages()[0])"], text=True).strip()
    )
    (site_packages / "greet").mkdir()
    (site_packages / "greet" / "__init__.py").write_text(PACKAGE)

    (site_packages / "greet.pth").write_text(PTH)
    print("$ python -c pass            # site-packages has greet.pth", flush=True)
    subprocess.run([interpreter, "-c", "pass"])

    (site_packages / "greet.start").write_text(START)
    print("$ python -c pass            # ...and greet.start", flush=True)
    subprocess.run([interpreter, "-c", "pass"])

    print("$ python -v -c pass | grep suppressed", flush=True)
    verbose = subprocess.run([interpreter, "-v", "-c", "pass"], capture_output=True, text=True).stderr
    for line in verbose.splitlines():
        if "suppressed" in line:
            print(" ", line.replace(f"{site_packages}/", ""))
