#!/usr/bin/env python3
"""Validate that GitHub Pages output contains public aggregate data only."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PUBLIC_DIR = ROOT / "github-pages"

FORBIDDEN_KEYS = {
    "address",
    "addressline1",
    "addressline2",
    "birthdate",
    "birthday",
    "dateofbirth",
    "dob",
    "email",
    "emailaddress",
    "firstname",
    "fullname",
    "lastcontactdate",
    "lastname",
    "mobile",
    "mobilenumber",
    "mostrecentcontactdate",
    "name",
    "personid",
    "phone",
    "phonenumber",
    "residentialaddress",
    "streetaddress",
    "submitteddob",
    "submittedfirstname",
    "submittedlastname",
    "submittedmobile",
    "voterid",
    "voter_id",
    "wirelessphone",
}

PERSON_LEVEL_ARRAY_KEYS = {
    "addedcontactedrows",
    "matches",
    "people",
    "persondetail",
    "personhistory",
    "personrecords",
    "personrows",
    "persons",
    "voters",
    "voterrecords",
}

JS_DATA_ASSIGNMENT = re.compile(
    r"window\.GLA_(?:WEBSITE|DASHBOARD)_DATA(?:\.[A-Za-z_$][\w$]*)?\s*="
)
FALLBACK_FORBIDDEN_KEY = re.compile(
    r"(?i)(?:['\"]|\b)("
    r"firstName|lastName|fullName|birthDate|birth_date|dateOfBirth|date_of_birth|"
    r"voterId|voter_id|personId|person_id|phoneNumber|emailAddress|"
    r"mostRecentContactDate|addedContactedRows"
    r")(?:['\"]|\b)\s*:"
)


def normalize_key(value: object) -> str:
    return re.sub(r"[^a-z0-9_]", "", str(value).lower())


def parse_json_values_from_js(text: str) -> list[Any]:
    values: list[Any] = []
    decoder = json.JSONDecoder()
    for match in JS_DATA_ASSIGNMENT.finditer(text):
        remainder = text[match.end() :].lstrip()
        try:
            value, _ = decoder.raw_decode(remainder)
        except json.JSONDecodeError:
            continue
        values.append(value)
    return values


def data_files(public_dir: Path) -> list[Path]:
    candidates: list[Path] = []
    for path in public_dir.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() == ".json":
            candidates.append(path)
            continue
        if path.suffix.lower() == ".js" and (
            "Tables for Website data" in path.parts or path.name == "sample-data.js"
        ):
            candidates.append(path)
    return candidates


def check_value(value: Any, path: str, errors: list[str]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = normalize_key(key)
            child_path = f"{path}.{key}" if path else str(key)
            if normalized in FORBIDDEN_KEYS:
                errors.append(f"{child_path}: forbidden private data key")
            if normalized in PERSON_LEVEL_ARRAY_KEYS and isinstance(child, list) and child:
                errors.append(f"{child_path}: non-empty person-level array")
            check_value(child, child_path, errors)
        return

    if isinstance(value, list):
        for index, child in enumerate(value):
            check_value(child, f"{path}[{index}]", errors)


def validate_file(path: Path, public_dir: Path, errors: list[str]) -> int:
    relative = path.relative_to(public_dir)
    text = path.read_text(encoding="utf-8", errors="replace")
    parsed_values: list[Any] = []

    if path.suffix.lower() == ".json":
        try:
            parsed_values.append(json.loads(text))
        except json.JSONDecodeError as exc:
            errors.append(f"{relative}: invalid JSON: {exc}")
            return 0
    elif path.suffix.lower() == ".js":
        parsed_values.extend(parse_json_values_from_js(text))
        if not parsed_values:
            fallback_hit = FALLBACK_FORBIDDEN_KEY.search(text)
            if fallback_hit:
                key = fallback_hit.group(1)
                empty_array = re.search(rf"(?i)['\"]?{re.escape(key)}['\"]?\s*:\s*\[\s*\]", text)
                if not empty_array:
                    errors.append(f"{relative}: forbidden private data key in JS data: {key}")

    for index, value in enumerate(parsed_values):
        check_value(value, f"{relative}#{index}", errors)

    return len(parsed_values)


def validate_public_output(public_dir: Path = DEFAULT_PUBLIC_DIR) -> None:
    if not public_dir.exists():
        raise SystemExit(f"Public directory does not exist: {public_dir}")

    errors: list[str] = []
    parsed_count = 0
    files = data_files(public_dir)
    for path in files:
        parsed_count += validate_file(path, public_dir, errors)

    if errors:
        for error in errors:
            print(error)
        raise SystemExit("Public output validation failed.")

    print(
        f"Validated {len(files)} public data files and {parsed_count} structured data object(s); "
        "no forbidden private keys or non-empty person-level arrays found."
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--public-dir", type=Path, default=DEFAULT_PUBLIC_DIR)
    args = parser.parse_args()
    validate_public_output(args.public_dir)


if __name__ == "__main__":
    main()
