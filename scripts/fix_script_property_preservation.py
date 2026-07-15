from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CODE_PATH = ROOT / "apps-script" / "Code.js"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        print(f"Already fixed: {label}")
        return text
    if old not in text:
        raise SystemExit(f"Could not find expected code for: {label}")
    return text.replace(old, new, 1)


def main() -> None:
    text = CODE_PATH.read_text(encoding="utf-8")

    text = replace_once(
        text,
        ".setProperties(properties, true);",
        ".setProperties(properties);",
        "dashboard file configuration preservation",
    )

    text = replace_once(
        text,
        """  PropertiesService.getScriptProperties().setProperties({
    [EZ_APP_DETAIL_FILE_PROPERTY]: detailId,
    [EZ_APP_ADMIN_EMAILS_PROPERTY]: emails.join(\",\")
  }, true);""",
        """  PropertiesService.getScriptProperties().setProperties({
    [EZ_APP_DETAIL_FILE_PROPERTY]: detailId,
    [EZ_APP_ADMIN_EMAILS_PROPERTY]: emails.join(\",\")
  });""",
        "EZ App admin configuration preservation",
    )

    CODE_PATH.write_text(text, encoding="utf-8")
    print(f"Updated {CODE_PATH}")


if __name__ == "__main__":
    main()
