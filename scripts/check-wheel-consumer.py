"""Install one built wheel in a clean temporary venv with offline dependencies."""

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import venv
from pathlib import Path

if len(sys.argv) != 3:
    raise SystemExit("Usage: python scripts/check-wheel-consumer.py /absolute/sdk.whl /absolute/wheelhouse")
wheel = Path(sys.argv[1]).resolve(strict=True)
wheelhouse = Path(sys.argv[2]).resolve(strict=True)
with tempfile.TemporaryDirectory(prefix="diesis-wheel-consumer-") as temporary:
    consumer = Path(temporary)
    venv.create(consumer / "venv", with_pip=True)
    python = consumer / "venv/bin/python"
    subprocess.run(
        [str(python), "-m", "pip", "install", "--no-index", "--find-links", str(wheelhouse), str(wheel)], check=True
    )
    fixture = consumer / "consumer.py"
    shutil.copyfile(Path(__file__).resolve().parents[1] / "tests/wheel_consumer.py", fixture)
    subprocess.run([str(python), str(fixture)], cwd=consumer, check=True)
    print(json.dumps({"wheelSha256": hashlib.sha256(wheel.read_bytes()).hexdigest(), "consumerRemoved": str(consumer)}))
