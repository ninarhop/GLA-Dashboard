from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "apps-script" / "DashboardApp.html"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        print(f"Already updated: {label}")
        return text
    if old not in text:
        raise SystemExit(f"Could not find expected dashboard block for: {