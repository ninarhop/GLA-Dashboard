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

DETAIL_FILENAME = "GLA_EZ_APP_MATCH_DETAIL_CURRENT.csv"
SUMMARY_FILENAME = "GLA_EZ_APP_MATCH_SUMMARY_CURRENT.json"


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
    return re.sub(r"\s+COUNTY$", "", county)


def normalize_zip(value: Any) -> str:
    return re.sub(r"\D", "", clean(value))[:5]


def parse_date(value: Any) -> date | None:
    raw = clean(value)
    if not raw:
        return None
    for fmt in (
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%m/%d/%y",
        "%m-%d-%Y",
        "%Y/%m/%d",
        "%m/%d/%Y %H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
    ):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            pass
    return None


def date_key(value: Any) -> str:
    parsed = parse_date(value)
    return parsed.isoformat() if parsed else ""


def newest_file(folder: Path, pattern: str) -> Path | None:
    files = [path for path in folder.glob(pattern) if path.is_file()]
    return max(files, key=lambda path: path.stat().st_mtime) if files else None


def resolve_source(root: Path, source: dict[str, Any]) -> Path | None:
    folder = root / source["folder"]
    if "filename" in source:
        candidate = folder / source["filename"]
        return candidate if candidate.exists() else None
    return newest_file(folder, source["pattern"])


def open_csv(path: Path):
    return path.open("r", encoding="utf-8-sig", errors="replace", newline="")


def reader_for(file):
    reader = csv.DictReader(file)
    if reader.fieldnames:
        reader.fieldnames = [clean(header) for header in reader.fieldnames]
    return reader


def main() -> None:
    config_path = LOCAL_CONFIG if LOCAL_CONFIG.exists() else EXAMPLE_CONFIG
    config = load_json(config_path)
    columns = load_json(COLUMN_MAP)
    dashboard_root = Path(config["dashboard_root"])

    vrvh_path = resolve_source(dashboard_root, config["sources"]["vrvh"])
    ez_path = resolve_source(dashboard_root, config["sources"]["ez_app"])
    if vrvh_path is None or ez_path is None:
        raise SystemExit("The current VRVH and EZ App files are required.")

    ez_columns = columns["ez_app"]
    vrvh_columns = columns["vrvh"]

    submissions: list[dict[str, str]] = []
    submissions_by_key: dict[tuple[str, str, str], list[int]] = defaultdict(list)

    with open_csv(ez_path) as file:
        for row in reader_for(file):
            first = clean(row.get(ez_columns["first_name"]))
            middle = clean(row.get(ez_columns["middle_name"]))
            last = clean(row.get(ez_columns["last_name"]))
            birth = date_key(row.get(ez_columns["birth_date"]))
            submission_id = clean(row.get(ez_columns["submission_id"]))

            if not any((first, middle, last, birth, submission_id)):
                continue

            submission = {
                "First Name": first,
                "Middle Name": middle,
                "Last Name": last,
                "EZ App Submission ID": submission_id,
                "EZ App Submission Date": date_key(row.get(ez_columns["submission_date"])),
                "EZ App Address": clean(row.get(ez_columns["address"])),
                "EZ App City": clean(row.get(ez_columns["city"])),
                "EZ App County": clean(row.get(ez_columns["county"])),
                "EZ App ZIP": normalize_zip(row.get(ez_columns["zip"])),
                "Email": clean(row.get(ez_columns["email"])),
                "Home Phone": clean(row.get(ez_columns["home_phone"])),
                "Work Phone": clean(row.get(ez_columns["work_phone"])),
                "Match Status": "Missing required match fields",
                "Current VRVH Status": "Not checked",
                "VRVH County": "",
                "VRVH City": "",
                "VRVH ZIP": "",
                "VRVH Registration Date": "",
                "Registered On or After EZ App": "",
                "County Changed": "",
                "Address/County Review Note": "",
            }
            index = len(submissions)
            submissions.append(submission)

            key = (normalize_text(first), normalize_text(last), birth)
            if all(key):
                submissions_by_key[key].append(index)

    matched_indices: set[int] = set()
    ambiguous_indices: set[int] = set()

    with open_csv(vrvh_path) as file:
        for count, row in enumerate(reader_for(file), start=1):
            if count % 250000 == 0:
                print(f"Processed {count:,} VRVH rows for EZ App detail matching...")

            key = (
                normalize_text(row.get(vrvh_columns["first_name"])),
                normalize_text(row.get(vrvh_columns["last_name"])),
                date_key(row.get(vrvh_columns["birth_date"])),
            )
            candidate_indices = submissions_by_key.get(key)
            if not candidate_indices:
                continue

            vrvh_county = normalize_county(row.get(vrvh_columns["county"]))
            vrvh_zip = normalize_zip(row.get(vrvh_columns["zip"]))
            available = [i for i in candidate_indices if i not in matched_indices]
            if not available:
                continue

            if len(available) > 1:
                narrowed = [
                    i for i in available
                    if normalize_county(submissions[i]["EZ App County"]) == vrvh_county
                    or (submissions[i]["EZ App ZIP"] and submissions[i]["EZ App ZIP"] == vrvh_zip)
                ]
                if len(narrowed) != 1:
                    ambiguous_indices.update(available)
                    continue
                selected_index = narrowed[0]
            else:
                selected_index = available[0]

            matched_indices.add(selected_index)
            submission = submissions[selected_index]
            registration_date = date_key(row.get(vrvh_columns["registration_date"]))
            submission_date = submission["EZ App Submission Date"]
            current_status = normalize_text(row.get(vrvh_columns["status"]))
            county_changed = (
                normalize_county(submission["EZ App County"]) != vrvh_county
                if submission["EZ App County"] and vrvh_county
                else False
            )

            if submission_date and registration_date and registration_date >= submission_date:
                match_status = "Registered on or after EZ App submission"
                registered_after = "YES"
            else:
                match_status = "Found in current VRVH - registered before submission or date unavailable"
                registered_after = "NO / UNKNOWN"

            submission.update({
                "Match Status": match_status,
                "Current VRVH Status": current_status or "Unknown",
                "VRVH County": clean(row.get(vrvh_columns["county"])),
                "VRVH City": clean(row.get(vrvh_columns["city"])),
                "VRVH ZIP": vrvh_zip,
                "VRVH Registration Date": registration_date,
                "Registered On or After EZ App": registered_after,
                "County Changed": "YES" if county_changed else "NO",
                "Address/County Review Note": (
                    "Applicant appears in a different county than the EZ App submission."
                    if county_changed else ""
                ),
            })

    for index, submission in enumerate(submissions):
        if index in matched_indices:
            continue
        if index in ambiguous_indices:
            submission["Match Status"] = "Multiple possible VRVH matches - manual review"
            submission["Current VRVH Status"] = "Manual review required"
        elif submission["Match Status"] != "Missing required match fields":
            submission["Match Status"] = "Not found in current VRVH"
            submission["Current VRVH Status"] = "Not found"

    processed_dir = dashboard_root / "02_Processed_Data"
    processed_dir.mkdir(parents=True, exist_ok=True)
    detail_path = processed_dir / DETAIL_FILENAME
    summary_path = processed_dir / SUMMARY_FILENAME

    fieldnames = list(submissions[0].keys()) if submissions else []
    with detail_path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(submissions)

    status_counts = Counter(row["Match Status"] for row in submissions)
    ez_county_counts = Counter(clean(row["EZ App County"]) or "Unknown" for row in submissions)
    matched_county_counts = Counter(clean(row["VRVH County"]) or "Unknown" for row in submissions if row["VRVH County"])
    county_change_count = sum(row["County Changed"] == "YES" for row in submissions)

    summary = {
        "generatedAt": datetime.now().isoformat(timespec="seconds"),
        "privacy": "PRIVATE - contains names and contact information",
        "sources": {"vrvh": vrvh_path.name, "ezApp": ez_path.name},
        "totals": {
            "allSubmissions": len(submissions),
            "foundInCurrentVRVH": len(matched_indices),
            "notFoundInCurrentVRVH": status_counts["Not found in current VRVH"],
            "registeredOnOrAfterSubmission": status_counts["Registered on or after EZ App submission"],
            "foundButPreviouslyRegisteredOrDateUnavailable": status_counts["Found in current VRVH - registered before submission or date unavailable"],
            "multiplePossibleMatches": status_counts["Multiple possible VRVH matches - manual review"],
            "missingRequiredMatchFields": status_counts["Missing required match fields"],
            "countyChanged": county_change_count,
        },
        "byMatchStatus": [
            {"status": status, "count": count}
            for status, count in sorted(status_counts.items(), key=lambda item: (-item[1], item[0]))
        ],
        "byEZAppCounty": [
            {"county": county, "count": count}
            for county, count in sorted(ez_county_counts.items(), key=lambda item: (-item[1], item[0]))
        ],
        "byCurrentVRVHCounty": [
            {"county": county, "count": count}
            for county, count in sorted(matched_county_counts.items(), key=lambda item: (-item[1], item[0]))
        ],
        "detailFile": detail_path.name,
    }
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    print()
    print("Private EZ App follow-up report complete.")
    print(f"All submissions: {len(submissions):,}")
    print(f"Found in current VRVH: {len(matched_indices):,}")
    print(f"Not found in current VRVH: {status_counts['Not found in current VRVH']:,}")
    print(f"Registered on or after submission: {status_counts['Registered on or after EZ App submission']:,}")
    print(f"Detail report: {detail_path}")
    print(f"Summary report: {summary_path}")
    print("This report is private and must not be committed to GitHub or placed in the public dashboard data folder.")


if __name__ == "__main__":
    main()
