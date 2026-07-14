from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOCAL_CONFIG = ROOT / "config" / "data_sources.local.json"
EXAMPLE_CONFIG = ROOT / "config" / "data_sources.example.json"


def newest_file(folder: Path, pattern: str) -> Path:
    files = [path for path in folder.glob(pattern) if path.is_file()]
    if not files:
        raise SystemExit(f"No purge file found in {folder}")
    return max(files, key=lambda path: path.stat().st_mtime)


def main() -> None:
    config_path = LOCAL_CONFIG if LOCAL_CONFIG.exists() else EXAMPLE_CONFIG
    config = json.loads(config_path.read_text(encoding="utf-8"))

    root = Path(config["dashboard_root"])
    source = config["sources"]["purge"]
    path = newest_file(root / source["folder"], source["pattern"])

    counts: Counter[str] = Counter()

    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            value = (row.get("Last VRVH") or "").strip()
            counts[value or "[BLANK]"] += 1

    print(f"Purge file: {path.name}")
    print(f"Distinct Last VRVH values: {len(counts)}")
    print()

    for value, count in counts.most_common():
        print(f"{value}: {count:,}")


if __name__ == "__main__":
    main()
