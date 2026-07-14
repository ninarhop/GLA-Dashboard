import csv
from collections import Counter
from pathlib import Path

from app.database import get_connection

UPLOAD_DIR = Path("uploads")

REPORT_NAMES = [
    "Contacted voters report",
    "Registration after outreach report",
    "Purge status report",
    "Returned to VRVH report",
    "County performance report",
    "Follow-up needed report",
]

FIELD_ALIASES = {
    "voter_id": ["voterid", "voter_id", "voter id", "registrant id"],
    "first_name": ["firstname", "first name", "text_name_first", "fname"],
    "last_name": ["lastname", "last name", "text_name_last", "lname"],
    "county": ["county", "countyname", "county name"],
    "city": ["city", "text_res_city", "res city"],
    "zip": ["zip", "zipcode", "zip code", "text_res_zip5"],
    "contact_date": ["contact date", "date of last contact", "last contact date", "date"],
    "contact_method": ["method", "contact method", "source", "gla contact source", "outreach method"],
    "registration_status": ["registration status", "status", "vrvh status", "current vrvh match status"],
    "purge_status": ["purge status", "removed tracking status", "readded_status"],
}


def normalize(value):
    return (value or "").strip().lower().replace("_", " ")


def get_upload(upload_id):
    conn = get_connection()
    cur = conn.cursor()
    upload = cur.execute(
        "SELECT * FROM uploads WHERE id = ?",
        (upload_id,),
    ).fetchone()
    conn.close()
    return upload


def list_uploads():
    conn = get_connection()
    cur = conn.cursor()
    uploads = cur.execute(
        "SELECT * FROM uploads ORDER BY uploaded_at DESC"
    ).fetchall()
    conn.close()
    return uploads


def upload_file_path(upload):
    return UPLOAD_DIR / upload["stored_filename"]


def read_columns(upload):
    path = upload_file_path(upload)

    if not path.exists():
        return []

    try:
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.reader(f)
            return next(reader, [])
    except Exception:
        return []


def suggest_mapping(columns):
    normalized_columns = {normalize(column): column for column in columns}
    suggestions = []

    for canonical, aliases in FIELD_ALIASES.items():
        matched_column = None

        for alias in aliases:
            if alias in normalized_columns:
                matched_column = normalized_columns[alias]
                break

        suggestions.append(
            {
                "field": canonical,
                "matched_column": matched_column or "",
                "status": "matched" if matched_column else "needs review",
            }
        )

    return suggestions


def column_quality(upload, limit=500):
    path = upload_file_path(upload)
    columns = read_columns(upload)

    stats = {
        column: {
            "non_empty": 0,
            "blank": 0,
        }
        for column in columns
    }

    if not path.exists() or not columns:
        return stats

    try:
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)

            for index, row in enumerate(reader):
                if index >= limit:
                    break

                for column in columns:
                    value = (row.get(column) or "").strip()
                    if value:
                        stats[column]["non_empty"] += 1
                    else:
                        stats[column]["blank"] += 1
    except Exception:
        pass

    return stats


def analyze_upload(upload_id):
    upload = get_upload(upload_id)

    if not upload:
        return None

    columns = read_columns(upload)
    mapping = suggest_mapping(columns)
    stats = column_quality(upload)

    return {
        "upload": upload,
        "columns": columns,
        "mapping": mapping,
        "stats": stats,
        "reports": REPORT_NAMES,
    }


def find_best_column(columns, options):
    normalized = {normalize(column): column for column in columns}

    for option in options:
        option_normalized = normalize(option)
        if option_normalized in normalized:
            return normalized[option_normalized]

    return None


def report_group_column(report_name, columns):
    if report_name == "Contacted voters report":
        return find_best_column(columns, ["contact method", "method", "source", "gla contact source", "outreach method"]) or find_best_column(columns, ["county"])

    if report_name == "Registration after outreach report":
        return find_best_column(columns, ["registration status", "current vrvh match status", "vrvh status", "status"]) or find_best_column(columns, ["county"])

    if report_name == "Purge status report":
        return find_best_column(columns, ["purge status", "removed tracking status", "readded_status", "status"]) or find_best_column(columns, ["county"])

    if report_name == "Returned to VRVH report":
        return find_best_column(columns, ["current vrvh match status", "vrvh status", "readded_status", "status"]) or find_best_column(columns, ["county"])

    if report_name == "County performance report":
        return find_best_column(columns, ["county", "county name", "countyname"])

    if report_name == "Follow-up needed report":
        return find_best_column(columns, ["follow up", "follow-up", "status", "last contact date", "date of last contact"]) or find_best_column(columns, ["county"])

    return columns[0] if columns else None


def run_basic_report(upload_id, report_name):
    upload = get_upload(upload_id)

    if not upload:
        return None

    path = upload_file_path(upload)
    columns = read_columns(upload)
    group_column = report_group_column(report_name, columns)

    counts = Counter()
    total_rows = 0

    if path.exists() and group_column:
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)

            for row in reader:
                total_rows += 1
                value = (row.get(group_column) or "Blank / Unknown").strip()
                counts[value or "Blank / Unknown"] += 1

    rows = [
        {
            "label": label,
            "count": count,
            "percent": round((count / total_rows) * 100, 1) if total_rows else 0,
        }
        for label, count in counts.most_common(50)
    ]

    return {
        "upload": upload,
        "report_name": report_name,
        "group_column": group_column or "No matching column found",
        "total_rows": total_rows,
        "rows": rows,
    }
