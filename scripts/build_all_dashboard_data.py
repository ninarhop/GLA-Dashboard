from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


def run(script_name: str) -> None:
    script = SCRIPTS / script_name
    print()
    print(f"Running {script_name}...")
    subprocess.run([sys.executable, str(script)], cwd=ROOT, check=True)


def main() -> None:
    run("build_intake_comparison.py")
    run("build_zodiac_aggregate.py")
    print()
    print("All dashboard aggregates are current.")


if __name__ == "__main__":
    main()
