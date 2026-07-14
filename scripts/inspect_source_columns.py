from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LOCAL_CONFIG = ROOT / "config" / "data_sources.local.json"
EXAMPLE_CONFIG = ROOT / "config" / "data_sources.example.json"


def load_config() -> dict[str, Any]:
    config_path = LOCAL_CONFIG if LOCAL_CONFIG.exists() else EXAMPLE_CONFIG

    with config_path.open("r", encoding="utf-8") as file:
        return json.load(file)


def newest_file(folder: Path, pattern: str) -> Path | None:
    files = [path for path in folder.glob(pattern) if path.is_file()]

    if not files:
        return None

    return max(files, key=lambda path: path.stat().st_mtime)


def source_path(
    dashboard_root: Path,
    source: dict[str, Any],
) -> Path | None:
    folder = dashboard_root / source["folder"]

    if "filename" in source:
        path = folder / source["filename"]
        return path if path.exists() else None

    return newest_file(folder, source["pattern"])


def read_csv_headers(path: Path) -> list[str]:
    encodings = ("utf-8-sig", "utf-8", "cp1252")

    for encoding in encodings:
        try:
            with path.open(
                "r",
                encoding=encoding,
                errors="strict",
                newline="",
            ) as file:
                reader = csv.reader(file)
                return [header.strip() for header in next(reader)]
        except UnicodeDecodeError:
            continue

    raise RuntimeError(f"Unable to read CSV header: {path}")


def main() -> None:
    config = load_config()
    dashboard_root = Path(config["dashboard_root"])

    print()
    print("GLA Source Column Inspection")
    print(f"Dashboard root: {dashboard_root}")
    print()

    for source_name, source in config["sources"].items():
        path = source_path(dashboard_root, source)

        print("=" * 70)
        print(source_name.upper())

        if path is None:
            print("[MISSING] No matching file found.")
            continue

        print(f"File: {path}")

        if path.suffix.lower() != ".csv":
            print("[SKIPPED] This first checker currently supports CSV files.")
            continue

        headers = read_csv_headers(path)

        print(f"Columns found: {len(headers)}")

        for number, header in enumerate(headers, start=1):
            print(f"{number:>3}. {header}")

    print()
    print("Inspection complete.")
    print("No voter rows were copied or uploaded.")
    print()


if __name__ == "__main__":
    main()
