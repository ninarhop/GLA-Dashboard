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
        raise SystemExit(f"No EZ App file found in {folder}")

    return max(files, key=lambda path: path.stat().st_mtime)


def main() -> None:
    config_path = LOCAL_CONFIG if LOCAL_CONFIG.exists() else EXAMPLE_CONFIG
    config = json.loads(config_path.read_text(encoding="utf-8"))

    dashboard_root = Path(config["dashboard_root"])
    source = config["sources"]["ez_app"]
    path = newest_file(
        dashboard_root / source["folder"],
        source["pattern"],
    )

    counts: Counter[str] = Counter()
    total_rows = 0

    with path.open(
        "r",
        encoding="utf-8-sig",
        errors="replace",
        newline="",
    ) as file:
        reader = csv.DictReader(file)
        headers = reader.fieldnames or []

        for row in reader:
            total_rows += 1

            for header in headers:
                value = str(row.get(header) or "").strip()

                if value:
                    counts[header] += 1

    print(f"File: {path.name}")
    print(f"Total rows: {total_rows:,}")
    print()
    print("Non-empty values by column:")

    for header in headers:
        print(f"{header}: {counts[header]:,}")

    print()
    print("No actual field values or individual records were displayed.")


if __name__ == "__main__":
    main()
