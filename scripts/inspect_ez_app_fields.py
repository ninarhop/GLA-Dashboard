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


def classify_date(value: str) -> str:
    value = value.strip()

    if not value:
        return "Blank"

    if "/" in value:
        parts = value.split("/")
        return f"Slash date with {len(parts)} parts"

    if "-" in value:
        parts = value.split("-")
        return f"Dash date with {len(parts)} parts"

    if value.isdigit():
        return "Digits only"

    return "Other format"


def main() -> None:
    config_path = LOCAL_CONFIG if LOCAL_CONFIG.exists() else EXAMPLE_CONFIG
    config = json.loads(config_path.read_text(encoding="utf-8"))

    root = Path(config["dashboard_root"])
    source = config["sources"]["ez_app"]
    path = newest_file(root / source["folder"], source["pattern"])

    total = 0
    missing_first = 0
    missing_last = 0
    missing_birth = 0
    date_formats: Counter[str] = Counter()
    date_lengths: Counter[int] = Counter()

    with path.open(
        "r",
        encoding="utf-8-sig",
        errors="replace",
        newline="",
    ) as file:
        reader = csv.DictReader(file)

        for row in reader:
            total += 1

            first = (row.get("First Name") or "").strip()
            last = (row.get("Last Name") or "").strip()
            birth = (row.get("Date of Birth") or "").strip()

            if not first:
                missing_first += 1

            if not last:
                missing_last += 1

            if not birth:
                missing_birth += 1
            else:
                date_formats[classify_date(birth)] += 1
                date_lengths[len(birth)] += 1

    print(f"File: {path.name}")
    print(f"Total rows: {total:,}")
    print(f"Missing first name: {missing_first:,}")
    print(f"Missing last name: {missing_last:,}")
    print(f"Missing date of birth: {missing_birth:,}")
    print()
    print("Date format categories:")

    for label, count in date_formats.most_common():
        print(f"{label}: {count:,}")

    print()
    print("Date value lengths:")

    for length, count in sorted(date_lengths.items()):
        print(f"{length} characters: {count:,}")

    print()
    print("No names, dates of birth, or individual records were displayed.")


if __name__ == "__main__":
    main()
