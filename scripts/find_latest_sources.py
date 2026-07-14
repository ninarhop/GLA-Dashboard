from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "data_sources.example.json"


def load_config() -> dict[str, Any]:
    with CONFIG_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def newest_file(folder: Path, pattern: str) -> Path | None:
    matches = [path for path in folder.glob(pattern) if path.is_file()]
    if not matches:
        return None
    return max(matches, key=lambda path: path.stat().st_mtime)


def main() -> None:
    config = load_config()
    dashboard_root = Path(config["dashboard_root"])

    print(f"Dashboard root: {dashboard_root}")
    print()

    for source_name, source in config["sources"].items():
        folder = dashboard_root / source["folder"]

        if "filename" in source:
            candidate = folder / source["filename"]
        else:
            candidate = newest_file(folder, source["pattern"])

        if candidate and candidate.exists():
            print(f"[FOUND] {source_name}: {candidate}")
        else:
            print(f"[MISSING] {source_name}: {folder}")


if __name__ == "__main__":
    main()
