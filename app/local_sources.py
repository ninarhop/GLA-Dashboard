import csv
from pathlib import Path

from app.database import get_connection

SOURCE_TYPES = [
    "VRVH voter file",
    "purge list",
    "outreach/contact history",
    "registration apps",
    "zodiac data",
    "primary election data",
    "other",
]


def init_local_sources_table():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS local_sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_name TEXT NOT NULL,
            source_type TEXT NOT NULL,
            file_path TEXT NOT NULL,
            added_by TEXT NOT NULL,
            added_at TEXT DEFAULT CURRENT_TIMESTAMP,
            row_count INTEGER,
            columns TEXT,
            status TEXT NOT NULL DEFAULT 'registered'
        )
        """
    )

    conn.commit()
    conn.close()


def file_exists(file_path: str) -> bool:
    return Path(file_path).exists()


def inspect_csv_path(file_path: str, row_limit=None):
    path = Path(file_path)

    if not path.exists():
        return {
            "exists": False,
            "row_count": None,
            "columns": [],
            "status": "registered - path not accessible from this environment",
        }

    columns = []
    row_count = 0

    try:
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.reader(f)

            try:
                columns = next(reader, [])
            except StopIteration:
                columns = []

            for row_count, _ in enumerate(reader, start=1):
                if row_limit and row_count >= row_limit:
                    break

        return {
            "exists": True,
            "row_count": row_count,
            "columns": columns,
            "status": "accessible",
        }

    except Exception as exc:
        return {
            "exists": False,
            "row_count": None,
            "columns": [],
            "status": f"error reading file: {exc}",
        }


def create_local_source(source_name, source_type, file_path, added_by):
    inspection = inspect_csv_path(file_path)
    columns_text = "|".join(inspection["columns"])

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO local_sources
        (source_name, source_type, file_path, added_by, row_count, columns, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            source_name,
            source_type,
            file_path,
            added_by,
            inspection["row_count"],
            columns_text,
            inspection["status"],
        ),
    )

    conn.commit()
    conn.close()


def list_local_sources():
    conn = get_connection()
    cur = conn.cursor()

    rows = cur.execute(
        "SELECT * FROM local_sources ORDER BY added_at DESC"
    ).fetchall()

    conn.close()
    return rows


def get_local_source(source_id):
    conn = get_connection()
    cur = conn.cursor()

    row = cur.execute(
        "SELECT * FROM local_sources WHERE id = ?",
        (source_id,),
    ).fetchone()

    conn.close()
    return row


def refresh_local_source(source_id):
    source = get_local_source(source_id)

    if not source:
        return None

    inspection = inspect_csv_path(source["file_path"])
    columns_text = "|".join(inspection["columns"])

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE local_sources
        SET row_count = ?, columns = ?, status = ?
        WHERE id = ?
        """,
        (
            inspection["row_count"],
            columns_text,
            inspection["status"],
            source_id,
        ),
    )

    conn.commit()
    conn.close()

    return get_local_source(source_id)


def source_columns(source):
    if not source or not source["columns"]:
        return []
    return [column for column in source["columns"].split("|") if column]
