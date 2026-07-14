import csv
import os
import shutil
import uuid
from pathlib import Path

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from starlette.templating import Jinja2Templates

from app.auth import authenticate_user, create_default_admin
from app.database import get_connection, init_db
from app.mapping import analyze_upload, list_uploads, run_basic_report
from app.local_sources import SOURCE_TYPES, create_local_source, init_local_sources_table, list_local_sources, get_local_source, refresh_local_source, source_columns

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

app = FastAPI(title="GLA CRM Dashboard Platform")

secret_key = os.getenv("SECRET_KEY", "temporary-dev-secret-key")
app.add_middleware(SessionMiddleware, secret_key=secret_key)

templates = Jinja2Templates(directory="templates")

if Path("github-pages").exists():
    app.mount("/dashboard-files", StaticFiles(directory="github-pages", html=True), name="dashboard_files")


@app.on_event("startup")
def startup():
    init_db()
    init_local_sources_table()
    create_default_admin()


def current_user(request: Request):
    return request.session.get("user")


def require_login(request: Request):
    user = current_user(request)
    if not user:
        return None
    return user


def count_csv_rows(path: Path):
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.reader(f)
            rows = list(reader)
            if not rows:
                return 0
            return max(len(rows) - 1, 0)
    except Exception:
        return None


@app.get("/")
def root(request: Request):
    if current_user(request):
        return RedirectResponse("/admin", status_code=303)
    return RedirectResponse("/login", status_code=303)


@app.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"error": None},
    )


@app.post("/login")
def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    user = authenticate_user(username, password)

    if not user:
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={"error": "Invalid username or password."},
        )

    request.session["user"] = user
    return RedirectResponse("/admin", status_code=303)


@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)


@app.get("/admin")
def admin(request: Request):
    user = require_login(request)
    if not user:
        return RedirectResponse("/login", status_code=303)

    conn = get_connection()
    cur = conn.cursor()

    upload_count = cur.execute("SELECT COUNT(*) AS count FROM uploads").fetchone()["count"]
    latest_uploads = cur.execute(
        "SELECT * FROM uploads ORDER BY uploaded_at DESC LIMIT 5"
    ).fetchall()

    conn.close()

    return templates.TemplateResponse(
        request=request,
        name="admin.html",
        context={
                        "user": user,
            "upload_count": upload_count,
            "latest_uploads": latest_uploads,
        },
    )


@app.get("/upload")
def upload_page(request: Request):
    user = require_login(request)
    if not user:
        return RedirectResponse("/login", status_code=303)

    upload_types = [
        "VRVH voter file",
        "purge list",
        "outreach/contact history",
        "registration apps",
        "zodiac data",
        "primary election data",
        "other",
    ]

    return templates.TemplateResponse(
        request=request,
        name="upload.html",
        context={"user": user, "upload_types": upload_types, "message": None},
    )


@app.post("/upload")
def upload_file(
    request: Request,
    upload_type: str = Form(...),
    file: UploadFile = File(...),
):
    user = require_login(request)
    if not user:
        return RedirectResponse("/login", status_code=303)

    original_filename = file.filename or "uploaded_file.csv"
    suffix = Path(original_filename).suffix.lower()

    if suffix not in [".csv", ".txt"]:
        upload_types = [
            "VRVH voter file",
            "purge list",
            "outreach/contact history",
            "registration apps",
            "zodiac data",
            "primary election data",
            "other",
        ]
        return templates.TemplateResponse(
            request=request,
            name="upload.html",
            context={
                                "user": user,
                "upload_types": upload_types,
                "message": "For this first version, please upload CSV files only.",
            },
        )

    stored_filename = f"{uuid.uuid4().hex}{suffix}"
    stored_path = UPLOAD_DIR / stored_filename

    with stored_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    row_count = count_csv_rows(stored_path)

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO uploads
        (original_filename, stored_filename, upload_type, uploaded_by, row_count, status)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            original_filename,
            stored_filename,
            upload_type,
            user["username"],
            row_count,
            "uploaded",
        ),
    )
    conn.commit()
    conn.close()

    return RedirectResponse("/uploads", status_code=303)


@app.get("/uploads")
def uploads_page(request: Request):
    user = require_login(request)
    if not user:
        return RedirectResponse("/login", status_code=303)

    conn = get_connection()
    cur = conn.cursor()
    uploads = cur.execute(
        "SELECT * FROM uploads ORDER BY uploaded_at DESC"
    ).fetchall()
    conn.close()

    return templates.TemplateResponse(
        request=request,
        name="uploads.html",
        context={"user": user, "uploads": uploads},
    )




@app.get("/local-sources")
def local_sources_page(request: Request):
    user = require_login(request)
    if not user:
        return RedirectResponse("/login", status_code=303)

    sources = list_local_sources()

    return templates.TemplateResponse(
        request=request,
        name="local_sources.html",
        context={"user": user, "sources": sources},
    )


@app.get("/local-sources/register")
def register_local_source_page(request: Request):
    user = require_login(request)
    if not user:
        return RedirectResponse("/login", status_code=303)

    return templates.TemplateResponse(
        request=request,
        name="register_local_source.html",
        context={"user": user, "source_types": SOURCE_TYPES},
    )


@app.post("/local-sources/register")
def register_local_source_submit(
    request: Request,
    source_name: str = Form(...),
    source_type: str = Form(...),
    file_path: str = Form(...),
):
    user = require_login(request)
    if not user:
        return RedirectResponse("/login", status_code=303)

    create_local_source(
        source_name=source_name,
        source_type=source_type,
        file_path=file_path,
        added_by=user["username"],
    )

    return RedirectResponse("/local-sources", status_code=303)


@app.get("/local-sources/{source_id}")
def local_source_detail_page(request: Request, source_id: int):
    user = require_login(request)
    if not user:
        return RedirectResponse("/login", status_code=303)

    source = get_local_source(source_id)

    if not source:
        return RedirectResponse("/local-sources", status_code=303)

    columns = source_columns(source)

    return templates.TemplateResponse(
        request=request,
        name="local_source_detail.html",
        context={"user": user, "source": source, "columns": columns},
    )


@app.post("/local-sources/{source_id}/refresh")
def local_source_refresh(request: Request, source_id: int):
    user = require_login(request)
    if not user:
        return RedirectResponse("/login", status_code=303)

    refresh_local_source(source_id)

    return RedirectResponse(f"/local-sources/{source_id}", status_code=303)


@app.get("/data-sources")
def data_sources_page(request: Request):
    user = require_login(request)
    if not user:
        return RedirectResponse("/login", status_code=303)

    uploads = list_uploads()

    return templates.TemplateResponse(
        request=request,
        name="data_sources.html",
        context={"user": user, "uploads": uploads},
    )


@app.get("/imports/{upload_id}")
def import_detail_page(request: Request, upload_id: int):
    user = require_login(request)
    if not user:
        return RedirectResponse("/login", status_code=303)

    analysis = analyze_upload(upload_id)

    if not analysis:
        return RedirectResponse("/data-sources", status_code=303)

    return templates.TemplateResponse(
        request=request,
        name="import_detail.html",
        context={"user": user, "analysis": analysis},
    )


@app.post("/imports/{upload_id}/run-report")
def import_run_report(
    request: Request,
    upload_id: int,
    report_name: str = Form(...),
):
    user = require_login(request)
    if not user:
        return RedirectResponse("/login", status_code=303)

    result = run_basic_report(upload_id, report_name)

    if not result:
        return RedirectResponse("/data-sources", status_code=303)

    return templates.TemplateResponse(
        request=request,
        name="report_results.html",
        context={"user": user, "result": result},
    )


@app.get("/reports")
def reports_page(request: Request):
    user = require_login(request)
    if not user:
        return RedirectResponse("/login", status_code=303)

    reports = [
        "Contacted voters report",
        "Registration after outreach report",
        "Purge status report",
        "Returned to VRVH report",
        "County performance report",
        "Follow-up needed report",
    ]

    return templates.TemplateResponse(
        request=request,
        name="reports.html",
        context={"user": user, "reports": reports},
    )



@app.get("/help")
def help_page(request: Request):
    user = require_login(request)
    if not user:
        return RedirectResponse("/login", status_code=303)

    return templates.TemplateResponse(
        request=request,
        name="help.html",
        context={"user": user},
    )


@app.get("/dashboard")
def dashboard(request: Request):
    user = require_login(request)
    if not user:
        return RedirectResponse("/login", status_code=303)

    return templates.TemplateResponse(
        request=request,
        name="dashboard_wrapper.html",
        context={"user": user},
    )
