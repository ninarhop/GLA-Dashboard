from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
LOCAL_CONFIG = ROOT / "config" / "data_sources.local.json"
EXAMPLE_CONFIG = ROOT / "config" / "data_sources.example.json"
COLUMN_MAP = ROOT / "config" / "source_columns.json"
PUBLIC_OUTPUT = ROOT / "github-pages" / "data" / "intake-comparison.json"

ZODIAC_ORDER = (
    "Aries",
    "Taurus",
    "Gemini",
    "Cancer",
    "Leo",
    "Virgo",
    "Libra",
    "Scorpio",
    "Sagittarius",
    "Capricorn",
    "Aquarius",
    "Pisces",
)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def clean(value: Any) -> str:
    return str(value or "").strip()


def parse_date(value: Any) -> date | None:
    raw = clean(value)
    if not raw:
        return None

    formats = (
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%m/%d/%y",
        "%m-%d-%Y",
        "%Y/%m/%d",
        "%m/%d/%Y %H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
    )

    for fmt in formats:
        try:
            parsed = datetime.strptime(raw, fmt).date()
            if 1900 <= parsed.year <= date.today().year:
                return parsed
        except ValueError:
            continue

    return None


def normalize_county(value: Any) -> str:
    text = re.sub(r"[^A-Z0-9 ]+", "", clean(value).upper())
    text = re.sub(r"\s+", " ", text).strip()
    return re.sub(r"\s+COUNTY$", "", text) or "UNKNOWN"


def zodiac_sign(birth_date: date) -> str:
    month_day = (birth_date.month, birth_date.day)
    if (3, 21) <= month_day <= (4, 19):
        return "Aries"
    if (4, 20) <= month_day <= (5, 20):
        return "Taurus"
    if (5, 21) <= month_day <= (6, 20):
        return "Gemini"
    if (6, 21) <= month_day <= (7, 22):
        return "Cancer"
    if (7, 23) <= month_day <= (8, 22):
        return "Leo"
    if (8, 23) <= month_day <= (9, 22):
        return "Virgo"
    if (9, 23) <= month_day <= (10, 22):
        return "Libra"
    if (10, 23) <= month_day <= (11, 21):
        return "Scorpio"
    if (11, 22) <= month_day <= (12, 21):
        return "Sagittarius"
    if month_day >= (12, 22) or month_day <= (1, 19):
        return "Capricorn"
    if (1, 20) <= month_day <= (2, 18):
        return "Aquarius"
    return "Pisces"


def newest_file(folder: Path, pattern: str) -> Path | None:
    files = [path for path in folder.glob(pattern) if path.is_file()]
    return max(files, key=lambda path: path.stat().st_mtime) if files else None


def resolve_source(dashboard_root: Path, source: dict[str, Any]) -> Path | None:
    folder = dashboard_root / source["folder"]
    if "filename" in source:
        candidate = folder / source["filename"]
        return candidate if candidate.exists() else None
    return newest_file(folder, source["pattern"])


def is_recent_election_column(header: str) -> bool:
    name = clean(header)
    if not re.match(r"^20(24|26)\b", name):
        return False

    excluded_suffixes = (
        "CountyVotedIn",
        "VotedIn",
        "PartyVoted",
        "HowVoted",
    )
    return not name.endswith(excluded_suffixes)


def election_id(label: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-")


def election_sort_key(label: str) -> tuple[int, int, str]:
    year_match = re.match(r"^(\d{4})", label)
    year = int(year_match.group(1)) if year_match else 0
    rank = 0
    normalized = label.lower()
    if "general" in normalized:
        rank = 5
    elif "runoff" in normalized:
        rank = 4
    elif "preferential primary" in normalized:
        rank = 3
    elif "primary" in normalized:
        rank = 2
    elif "special" in normalized:
        rank = 1
    return (-year, -rank, label)


def rate(voted: int, registered: int) -> float:
    return round((voted / registered * 100), 2) if registered else 0.0


def sign_rows(
    registered: Counter[str],
    voted: Counter[str],
) -> list[dict[str, Any]]:
    return [
        {
            "zodiacSign": sign,
            "registeredVoters": registered[sign],
            "voted": voted[sign],
            "votingRate": rate(voted[sign], registered[sign]),
        }
        for sign in ZODIAC_ORDER
    ]


def main() -> None:
    config_path = LOCAL_CONFIG if LOCAL_CONFIG.exists() else EXAMPLE_CONFIG
    config = load_json(config_path)
    columns = load_json(COLUMN_MAP)

    dashboard_root = Path(config["dashboard_root"])
    vrvh_path = resolve_source(dashboard_root, config["sources"]["vrvh"])
    if vrvh_path is None:
        raise SystemExit("No current VRVH file was found.")

    if not PUBLIC_OUTPUT.exists():
        raise SystemExit(
            "Run build_intake_comparison.py first so intake-comparison.json exists."
        )

    vrvh_columns = columns["vrvh"]
    birth_column = vrvh_columns["birth_date"]
    county_column = vrvh_columns["county"]

    with vrvh_path.open(
        "r",
        encoding="utf-8-sig",
        errors="replace",
        newline="",
    ) as file:
        reader = csv.DictReader(file)
        headers = [clean(header) for header in (reader.fieldnames or [])]
        election_columns = sorted(
            [header for header in headers if is_recent_election_column(header)],
            key=election_sort_key,
        )

        if not election_columns:
            raise SystemExit("No recent 2024 or 2026 election columns were found.")

        total_rows = 0
        registered_with_birth_date = 0
        missing_or_invalid_birth_date = 0
        statewide_registered: Counter[str] = Counter()
        county_registered: dict[str, Counter[str]] = defaultdict(Counter)
        statewide_voted: dict[str, Counter[str]] = {
            column: Counter() for column in election_columns
        }
        county_voted: dict[str, dict[str, Counter[str]]] = {
            column: defaultdict(Counter) for column in election_columns
        }

        for row in reader:
            total_rows += 1
            if total_rows % 250000 == 0:
                print(f"Processed {total_rows:,} VRVH rows for Zodiac...")

            birth_date = parse_date(row.get(birth_column))
            if not birth_date:
                missing_or_invalid_birth_date += 1
                continue

            registered_with_birth_date += 1
            sign = zodiac_sign(birth_date)
            county = normalize_county(row.get(county_column))
            statewide_registered[sign] += 1
            county_registered[county][sign] += 1

            for election in election_columns:
                if clean(row.get(election)):
                    statewide_voted[election][sign] += 1
                    county_voted[election][county][sign] += 1

    elections = [
        {"id": election_id(label), "label": label}
        for label in election_columns
    ]

    statewide_by_election: dict[str, list[dict[str, Any]]] = {}
    county_by_election: dict[str, list[dict[str, Any]]] = {}

    for election in election_columns:
        key = election_id(election)
        statewide_by_election[key] = sign_rows(
            statewide_registered,
            statewide_voted[election],
        )

        county_rows: list[dict[str, Any]] = []
        for county in sorted(county_registered):
            registered_total = sum(county_registered[county].values())
            voted_total = sum(county_voted[election][county].values())
            by_sign = sign_rows(
                county_registered[county],
                county_voted[election][county],
            )
            top_sign = max(
                by_sign,
                key=lambda row: (row["votingRate"], row["voted"]),
            )["zodiacSign"] if registered_total else "Unknown"

            county_rows.append(
                {
                    "county": county.title(),
                    "registeredVoters": registered_total,
                    "voted": voted_total,
                    "votingRate": rate(voted_total, registered_total),
                    "topZodiacByVotingRate": top_sign,
                    "bySign": by_sign,
                }
            )

        county_by_election[key] = county_rows

    output = load_json(PUBLIC_OUTPUT)
    output["zodiac"] = {
        "source": vrvh_path.name,
        "registeredVoters": total_rows,
        "registeredWithBirthDate": registered_with_birth_date,
        "missingOrInvalidBirthDate": missing_or_invalid_birth_date,
        "elections": elections,
        "defaultElectionId": elections[0]["id"],
        "statewideByElection": statewide_by_election,
        "countyByElection": county_by_election,
    }

    encoded = json.dumps(output, indent=2, ensure_ascii=False)
    PUBLIC_OUTPUT.write_text(encoded + "\n", encoding="utf-8")

    processed_dir = dashboard_root / "02_Processed_Data"
    processed_dir.mkdir(parents=True, exist_ok=True)
    drive_output = processed_dir / "GLA_AGGREGATE_COMPARISON_CURRENT.json"
    drive_output.write_text(encoded + "\n", encoding="utf-8")

    print()
    print("Zodiac aggregate complete.")
    print(f"Current registered voters: {total_rows:,}")
    print(f"Categorized by Zodiac: {registered_with_birth_date:,}")
    print(f"Missing/invalid birth date: {missing_or_invalid_birth_date:,}")
    print("Election filters:")
    for election in elections:
        print(f"  - {election['label']}")
    print(f"Updated public output: {PUBLIC_OUTPUT}")
    print(f"Updated Drive output: {drive_output}")
    print("No birth dates or person-level records were written.")


if __name__ == "__main__":
    main()
