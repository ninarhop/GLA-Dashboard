from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LOCAL_CONFIG = ROOT / "config" / "data_sources.local.json"
EXAMPLE_CONFIG = ROOT / "config" / "data_sources.example.json"
COLUMN_MAP = ROOT / "config" / "source_columns.json"

PUBLIC_OUTPUT = ROOT / "github-pages" / "data" / "intake-comparison.json"

FORBIDDEN_OUTPUT_TERMS = re.compile(
    r"first.?name|last.?name|middle.?name|voter.?id|birth.?date|"
    r"street.?address|phone|email|signature",
    re.IGNORECASE,
)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def clean(value: Any) -> str:
    return str(value or "").strip()


def normalize_text(value: Any) -> str:
    text = clean(value).upper()
    text = re.sub(r"[^A-Z0-9 ]+", "", text)
    return re.sub(r"\s+", " ", text).strip()


def normalize_county(value: Any) -> str:
    county = normalize_text(value)
    county = re.sub(r"\s+COUNTY$", "", county)
    return county


def normalize_zip(value: Any) -> str:
    digits = re.sub(r"\D", "", clean(value))
    return digits[:5]


def normalize_identifier(value: Any) -> str:
    value = clean(value)

    if value.endswith(".0"):
        value = value[:-2]

    return value


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
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue

    return None


def date_key(value: Any) -> str:
    parsed = parse_date(value)
    return parsed.isoformat() if parsed else ""


def newest_file(folder: Path, pattern: str) -> Path | None:
    files = [path for path in folder.glob(pattern) if path.is_file()]

    if not files:
        return None

    return max(files, key=lambda path: path.stat().st_mtime)


def resolve_source(
    dashboard_root: Path,
    source: dict[str, Any],
) -> Path | None:
    folder = dashboard_root / source["folder"]

    if "filename" in source:
        candidate = folder / source["filename"]
        return candidate if candidate.exists() else None

    return newest_file(folder, source["pattern"])


def open_csv(path: Path):
    return path.open(
        "r",
        encoding="utf-8-sig",
        errors="replace",
        newline="",
    )


def normalized_dict_reader(file):
    reader = csv.DictReader(file)

    if reader.fieldnames:
        reader.fieldnames = [
            clean(header)
            for header in reader.fieldnames
        ]

    return reader


def main() -> None:
    config_path = LOCAL_CONFIG if LOCAL_CONFIG.exists() else EXAMPLE_CONFIG
    config = load_json(config_path)
    columns = load_json(COLUMN_MAP)

    dashboard_root = Path(config["dashboard_root"])
    sources = config["sources"]

    vrvh_path = resolve_source(dashboard_root, sources["vrvh"])
    purge_path = resolve_source(dashboard_root, sources["purge"])
    ez_path = resolve_source(dashboard_root, sources["ez_app"])
    priority_path = resolve_source(
        dashboard_root,
        sources["priority_counties"],
    )

    required = {
        "VRVH": vrvh_path,
        "purge": purge_path,
        "EZ App": ez_path,
        "priority counties": priority_path,
    }

    missing = [name for name, path in required.items() if path is None]

    if missing:
        raise SystemExit(
            "Missing required source files: " + ", ".join(missing)
        )

    assert vrvh_path is not None
    assert purge_path is not None
    assert ez_path is not None
    assert priority_path is not None

    print()
    print("GLA Intake Comparison")
    print(f"VRVH: {vrvh_path.name}")
    print(f"Purge: {purge_path.name}")
    print(f"EZ App: {ez_path.name}")
    print(f"Priority counties: {priority_path.name}")
    print()

    priority_counties: set[str] = set()

    with open_csv(priority_path) as file:
        reader = normalized_dict_reader(file)
        county_column = columns["priority_counties"]["county"]
        status_column = columns["priority_counties"]["status"]

        for row in reader:
            status = normalize_text(row.get(status_column))

            if status == "PRIORITY":
                priority_counties.add(
                    normalize_county(row.get(county_column))
                )

    purge_columns = columns["purge"]
    purge_rules = columns["purge_reporting"]

    included_labels = {
        normalize_text(value)
        for value in purge_rules["include_last_vrvh_values"]
    }

    purge_period_dates = {
        normalize_text(label): effective_date
        for label, effective_date in purge_rules.get(
            "period_dates",
            {},
        ).items()
    }

    purge_ids: set[str] = set()
    removed_since_baseline = 0
    removed_by_county: Counter[str] = Counter()
    removed_by_ethnic_group: Counter[str] = Counter()
    removed_by_language: Counter[str] = Counter()
    removed_by_last_vrvh: Counter[str] = Counter()
    removed_by_date: Counter[str] = Counter()
    removed_by_date_county: Counter[tuple[str, str]] = Counter()

    with open_csv(purge_path) as file:
        reader = normalized_dict_reader(file)

        for row in reader:
            last_vrvh_raw = clean(row.get(purge_columns["last_vrvh"]))
            last_vrvh = normalize_text(last_vrvh_raw)

            if last_vrvh not in included_labels:
                continue

            removed_since_baseline += 1
            removed_by_last_vrvh[last_vrvh_raw or "Unknown"] += 1

            effective_date = purge_period_dates.get(last_vrvh)

            county = normalize_county(
                row.get(purge_columns["county"])
            ) or "UNKNOWN"

            removed_by_county[county] += 1

            if effective_date:
                removed_by_date[effective_date] += 1
                removed_by_date_county[(effective_date, county)] += 1

            ethnic_group = clean(
                row.get(purge_columns["ethnic_group"])
            ) or "Unknown"

            removed_by_ethnic_group[ethnic_group] += 1

            language = clean(
                row.get(purge_columns["language_preference"])
            ) or "Unknown"

            removed_by_language[language] += 1

            identifier = normalize_identifier(
                row.get(purge_columns["voter_id"])
            )

            if identifier:
                purge_ids.add(identifier)

    ez_columns = columns["ez_app"]

    ez_keys: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    total_ez_submissions = 0
    invalid_ez_match_fields = 0
    ez_submissions_by_county: Counter[str] = Counter()

    with open_csv(ez_path) as file:
        reader = normalized_dict_reader(file)

        for row in reader:
            first = normalize_text(row.get(ez_columns["first_name"]))
            last = normalize_text(row.get(ez_columns["last_name"]))
            birth = date_key(row.get(ez_columns["birth_date"]))

            if not first or not last or not birth:
                invalid_ez_match_fields += 1
                continue

            total_ez_submissions += 1

            county = normalize_county(
                row.get(ez_columns["county"])
            ) or "UNKNOWN"

            ez_submissions_by_county[county] += 1

            submission_date_text = date_key(
                row.get(ez_columns["submission_date"])
            )

            if submission_date_text:
                ez_submissions_by_date[submission_date_text] += 1

            ez_keys[(first, last, birth)].append(
                {
                    "county": county,
                    "zip": normalize_zip(row.get(ez_columns["zip"])),
                    "submission_date": date_key(
                        row.get(ez_columns["submission_date"])
                    ),
                }
            )

    vrvh_columns = columns["vrvh"]
    reporting_start = date.fromisoformat(
        purge_rules["reporting_start_date"]
    )

    current_vrvh_total = 0
    active_vrvh_total = 0
    inactive_vrvh_total = 0
    current_by_county: Counter[str] = Counter()

    registered_since_baseline = 0
    registered_since_by_county: Counter[str] = Counter()
    registrations_by_date: Counter[str] = Counter()
    registrations_by_date_county: Counter[tuple[str, str]] = Counter()

    readded_total = 0
    readded_by_county: Counter[str] = Counter()

    ez_exact_matches = 0
    ez_newly_registered_after_submission = 0
    ez_previously_registered = 0
    ez_ambiguous_matches = 0
    ez_matches_by_county: Counter[str] = Counter()
    ez_submissions_by_date: Counter[str] = Counter()
    ez_matches_by_date: Counter[str] = Counter()
    ez_registered_after_by_date: Counter[str] = Counter()
    matched_ez_keys: set[tuple[str, str, str]] = set()

    with open_csv(vrvh_path) as file:
        reader = normalized_dict_reader(file)

        for row_number, row in enumerate(reader, start=2):
            current_vrvh_total += 1

            if current_vrvh_total % 250000 == 0:
                print(
                    f"Processed {current_vrvh_total:,} current VRVH rows..."
                )

            county = normalize_county(
                row.get(vrvh_columns["county"])
            ) or "UNKNOWN"

            current_by_county[county] += 1

            status = normalize_text(row.get(vrvh_columns["status"]))

            if status == "A":
                active_vrvh_total += 1
            elif status == "I":
                inactive_vrvh_total += 1

            registration_date = parse_date(
                row.get(vrvh_columns["registration_date"])
            )

            if registration_date and registration_date >= reporting_start:
                registered_since_baseline += 1
                registered_since_by_county[county] += 1

                registration_date_text = registration_date.isoformat()
                registrations_by_date[registration_date_text] += 1
                registrations_by_date_county[
                    (registration_date_text, county)
                ] += 1

            identifier = normalize_identifier(
                row.get(vrvh_columns["voter_id"])
            )

            if identifier and identifier in purge_ids:
                readded_total += 1
                readded_by_county[county] += 1

            first = normalize_text(
                row.get(vrvh_columns["first_name"])
            )
            last = normalize_text(
                row.get(vrvh_columns["last_name"])
            )
            birth = date_key(
                row.get(vrvh_columns["birth_date"])
            )

            key = (first, last, birth)

            if key not in ez_keys:
                continue

            possible_submissions = ez_keys[key]

            if len(possible_submissions) > 1:
                vrvh_zip = normalize_zip(row.get(vrvh_columns["zip"]))

                narrowed = [
                    submission
                    for submission in possible_submissions
                    if (
                        submission["county"] == county
                        or (
                            vrvh_zip
                            and submission["zip"]
                            and submission["zip"] == vrvh_zip
                        )
                    )
                ]

                if len(narrowed) != 1:
                    ez_ambiguous_matches += 1
                    continue

                selected = narrowed[0]
            else:
                selected = possible_submissions[0]

            if key in matched_ez_keys:
                continue

            matched_ez_keys.add(key)
            ez_exact_matches += 1
            ez_matches_by_county[county] += 1

            submission_date = parse_date(
                selected["submission_date"]
            )

            if submission_date:
                ez_matches_by_date[
                    submission_date.isoformat()
                ] += 1

            if (
                submission_date
                and registration_date
                and registration_date >= submission_date
            ):
                ez_newly_registered_after_submission += 1
                ez_registered_after_by_date[
                    registration_date.isoformat()
                ] += 1
            else:
                ez_previously_registered += 1

    ez_not_found = max(total_ez_submissions - ez_exact_matches, 0)

    def counter_rows(
        counter: Counter[str],
        key_name: str,
    ) -> list[dict[str, Any]]:
        return [
            {key_name: key, "count": count}
            for key, count in sorted(
                counter.items(),
                key=lambda item: (-item[1], item[0]),
            )
        ]

    priority_rows = []

    for county in sorted(priority_counties):
        removed = removed_by_county[county]
        readded = readded_by_county[county]
        ez_submitted = ez_submissions_by_county[county]
        ez_matched = ez_matches_by_county[county]

        priority_rows.append(
            {
                "county": county.title(),
                "currentRegistered": current_by_county[county],
                "registeredSinceBaseline": registered_since_by_county[county],
                "removedSinceBaseline": removed,
                "returnedToCurrentFile": readded,
                "returnRate": round(
                    (readded / removed * 100),
                    2,
                ) if removed else 0,
                "ezAppSubmissions": ez_submitted,
                "ezAppMatches": ez_matched,
                "ezAppMatchRate": round(
                    (ez_matched / ez_submitted * 100),
                    2,
                ) if ez_submitted else 0,
            }
        )

    def dated_counter_rows(
        counter: Counter[str],
    ) -> list[dict[str, Any]]:
        return [
            {"date": key, "count": count}
            for key, count in sorted(counter.items())
        ]

    def dated_county_rows(
        counter: Counter[tuple[str, str]],
    ) -> list[dict[str, Any]]:
        return [
            {
                "date": date_value,
                "county": county,
                "count": count,
            }
            for (date_value, county), count in sorted(counter.items())
        ]

    output = {
        "meta": {
            "generatedAt": datetime.now().isoformat(timespec="seconds"),
            "privacy": "aggregate-only",
            "reportingStartDate": purge_rules["reporting_start_date"],
            "sources": {
                "vrvh": vrvh_path.name,
                "purge": purge_path.name,
                "ezApp": ez_path.name,
                "priorityCounties": priority_path.name,
            },
        },
        "voterFile": {
            "currentTotal": current_vrvh_total,
            "active": active_vrvh_total,
            "inactive": inactive_vrvh_total,
            "registeredSinceBaseline": registered_since_baseline,
        },
        "purge": {
            "removedSinceBaseline": removed_since_baseline,
            "returnedToCurrentFile": readded_total,
            "stillMissingFromCurrentFile": max(
                removed_since_baseline - readded_total,
                0,
            ),
            "returnRate": round(
                (readded_total / removed_since_baseline * 100),
                2,
            ) if removed_since_baseline else 0,
            "byLastFile": counter_rows(
                removed_by_last_vrvh,
                "sourcePeriod",
            ),
            "byCounty": counter_rows(
                removed_by_county,
                "county",
            ),
            "byEthnicGroup": counter_rows(
                removed_by_ethnic_group,
                "group",
            ),
            "byLanguagePreference": counter_rows(
                removed_by_language,
                "preference",
            ),
        },
        "ezApp": {
            "usableSubmissions": total_ez_submissions,
            "missingRequiredMatchFields": invalid_ez_match_fields,
            "matchedToCurrentFile": ez_exact_matches,
            "registeredOnOrAfterSubmission": (
                ez_newly_registered_after_submission
            ),
            "registeredBeforeSubmissionOrDateUnavailable": (
                ez_previously_registered
            ),
            "notFound": ez_not_found,
            "ambiguous": ez_ambiguous_matches,
            "matchRate": round(
                (ez_exact_matches / total_ez_submissions * 100),
                2,
            ) if total_ez_submissions else 0,
        },
        "priorityCounties": priority_rows,
        "dateSeries": {
            "registrations": dated_counter_rows(
                registrations_by_date
            ),
            "registrationsByCounty": dated_county_rows(
                registrations_by_date_county
            ),
            "purgeRemovals": dated_counter_rows(
                removed_by_date
            ),
            "purgeRemovalsByCounty": dated_county_rows(
                removed_by_date_county
            ),
            "ezAppSubmissions": dated_counter_rows(
                ez_submissions_by_date
            ),
            "ezAppMatches": dated_counter_rows(
                ez_matches_by_date
            ),
            "ezAppRegisteredAfterSubmission": dated_counter_rows(
                ez_registered_after_by_date
            )
        },
        "geography": {
            "currentByCounty": counter_rows(
                current_by_county,
                "county",
            ),
            "registeredSinceBaselineByCounty": counter_rows(
                registered_since_by_county,
                "county",
            ),
            "returnedToCurrentFileByCounty": counter_rows(
                readded_by_county,
                "county",
            ),
            "ezAppMatchesByCounty": counter_rows(
                ez_matches_by_county,
                "county",
            ),
        },
    }

    encoded = json.dumps(output, indent=2, ensure_ascii=False)

    if FORBIDDEN_OUTPUT_TERMS.search(encoded):
        raise SystemExit(
            "Privacy check failed: a forbidden person-level field "
            "was detected in the aggregate output."
        )

    PUBLIC_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    PUBLIC_OUTPUT.write_text(encoded + "\n", encoding="utf-8")

    processed_dir = dashboard_root / "02_Processed_Data"
    processed_dir.mkdir(parents=True, exist_ok=True)

    drive_output = processed_dir / "GLA_AGGREGATE_COMPARISON_CURRENT.json"
    drive_output.write_text(encoded + "\n", encoding="utf-8")

    print()
    print("Comparison complete.")
    print(f"Current VRVH rows: {current_vrvh_total:,}")
    print(f"Removed since baseline: {removed_since_baseline:,}")
    print(f"Returned to current file: {readded_total:,}")
    print(f"Usable EZ App submissions: {total_ez_submissions:,}")
    print(f"EZ App matches: {ez_exact_matches:,}")
    print()
    print(f"Public aggregate output: {PUBLIC_OUTPUT}")
    print(f"Drive aggregate output: {drive_output}")
    print("No names or person-level records were written.")
    print()


if __name__ == "__main__":
    main()
