#!/usr/bin/env python3
"""Build aggregate-only JSON for the public GLA GitHub Pages dashboard.

Input may contain private voter-level fields. Output must not.
"""
from __future__ import annotations
import csv, json, re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT.parent / "GLA_2026_Registration_Outreach_Tracking.csv"
DEFAULT_OUTPUT = ROOT / "github-pages" / "data" / "public-dashboard.json"
PRIVATE_TERMS = re.compile(r"first name|last name|voterid|voter id|full address|phone number|email address|birth date|birthday", re.I)

def clean(value: str | None) -> str:
    value = (value or "").strip()
    return value if value else "Unknown"

def main(input_path: str | None = None, output_path: str | None = None) -> None:
    in_path = Path(input_path) if input_path else DEFAULT_INPUT
    out_path = Path(output_path) if output_path else DEFAULT_OUTPUT
    rows = []
    with in_path.open(newline="", encoding="utf-8-sig", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    total = len(rows)
    counties = defaultdict(lambda: Counter(people=0, addedToCurrentVrvh=0, contacted=0, active=0, inactive=0))
    sources = defaultdict(lambda: Counter(people=0, addedToCurrentVrvh=0, notInGlaContactFile=0))
    reg_status = Counter()
    change_status = Counter()
    removed_status = Counter()
    contact_status = Counter()

    for row in rows:
        county = clean(row.get("c.County"))
        status = clean(row.get("Registration Status"))
        change = clean(row.get("Change Status"))
        removed = clean(row.get("Removed Tracking Status"))
        contact = clean(row.get("GLA Contact Status"))
        source = clean(row.get("Updated GLA Contact Source"))
        added = change.upper() == "ADDED TO CURRENT VRVH"
        contacted = contact.upper() != "NOT IN GLA CONTACT FILE"
        active = status.upper() == "A"
        inactive = status.upper() == "I"

        counties[county]["people"] += 1
        counties[county]["addedToCurrentVrvh"] += int(added)
        counties[county]["contacted"] += int(contacted)
        counties[county]["active"] += int(active)
        counties[county]["inactive"] += int(inactive)
        sources[source]["people"] += 1
        sources[source]["addedToCurrentVrvh"] += int(added)
        sources[source]["notInGlaContactFile"] += int(contact.upper() == "NOT IN GLA CONTACT FILE")
        reg_status[status] += 1
        change_status[change] += 1
        removed_status[removed] += 1
        contact_status[contact] += 1

    added_total = sum(1 for r in rows if clean(r.get("Change Status")).upper() == "ADDED TO CURRENT VRVH")
    contacted_total = sum(1 for r in rows if clean(r.get("GLA Contact Status")).upper() != "NOT IN GLA CONTACT FILE")
    active_total = sum(1 for r in rows if clean(r.get("Registration Status")).upper() == "A")
    inactive_total = sum(1 for r in rows if clean(r.get("Registration Status")).upper() == "I")
    not_in_gla = contact_status.get("NOT IN GLA CONTACT FILE", 0)

    def counter_rows(counter: Counter, label: str):
        return [{label: k, "count": v} for k, v in counter.most_common()]
    def county_rows():
        return [{"county": k, **dict(v)} for k, v in sorted(counties.items(), key=lambda item: (-item[1]["people"], item[0]))]
    def source_rows():
        return [{"source": k, **dict(v)} for k, v in sorted(sources.items(), key=lambda item: (-item[1]["people"], item[0]))]

    data = {
        "meta": {"title": "Get Loud Arkansas Public Dashboard", "generatedAt": datetime.now(timezone.utc).date().isoformat(), "privacy": "aggregate-only"},
        "overview": {"totalPeople": total, "addedToCurrentVrvh": added_total, "contacted": contacted_total, "notInGlaContactFile": not_in_gla, "counties": len(counties), "contactRate": round((contacted_total / total * 100), 1) if total else 0},
        "tracking": {"summary": {"totalPeople": total, "addedToCurrentVrvh": added_total, "notInGlaContactFile": not_in_gla, "counties": len(counties)}, "sourceTotals": source_rows(), "countyTotals": county_rows()},
        "voterFile": {"summary": {"totalPeople": total, "active": active_total, "inactive": inactive_total}, "registrationStatus": counter_rows(reg_status, "status")},
        "purge": {"summary": {"totalPeople": total, "addedToCurrentVrvh": added_total}, "removedTrackingStatus": counter_rows(removed_status, "status")},
        "outreach": {"summary": {"totalPeople": total, "contacted": contacted_total, "notInGlaContactFile": not_in_gla, "contactRate": round((contacted_total / total * 100), 1) if total else 0}, "contactStatus": counter_rows(contact_status, "status")},
        "registration": {"summary": {"totalPeople": total, "addedToCurrentVrvh": added_total, "active": active_total, "inactive": inactive_total}, "changeStatus": counter_rows(change_status, "status")},
        "geography": {"counties": county_rows()}
    }

    encoded = json.dumps(data, indent=2, ensure_ascii=False)
    if PRIVATE_TERMS.search(encoded):
        raise SystemExit("Refusing to write public JSON because private field names were detected.")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(encoded + "\n", encoding="utf-8")
    print(f"Wrote {out_path} from {total:,} private source rows; output is aggregate-only.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=None)
    parser.add_argument("--output", default=None)
    args = parser.parse_args()
    main(args.input, args.output)
