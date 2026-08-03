from __future__ import annotations

import base64
import hashlib
import io
import os
import re
import secrets
import smtplib
import sqlite3
from datetime import date, datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from functools import wraps
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse

from flask import (
    Flask,
    abort,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    send_from_directory,
    session,
    url_for,
)
from werkzeug.utils import secure_filename

from curriculum_content import CURRICULUM, RUBRIC
from project_content import CERTIFICATIONS, HR_PROJECT, HR_PROJECT_STEPS

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("PROJECT_GROUP_DATABASE", BASE_DIR / "project_group.db"))
UPLOAD_DIR = Path(os.environ.get("PROJECT_GROUP_UPLOADS", BASE_DIR / "uploads"))
AVATAR_DIR = Path(os.environ.get("PROJECT_GROUP_AVATARS", BASE_DIR / "avatars"))
PROJECT_FILE_DIR = BASE_DIR / "project_files"
SAMPLE_DIR = BASE_DIR / "static" / "samples"

for folder in (DB_PATH.parent, UPLOAD_DIR, AVATAR_DIR, PROJECT_FILE_DIR, SAMPLE_DIR):
    folder.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get("SECRET_KEY", secrets.token_hex(32)),
    MAX_CONTENT_LENGTH=int(os.environ.get("MAX_UPLOAD_BYTES", 12 * 1024 * 1024)),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE", "1") == "1",
)

APP_VERSION = "6.0.0"
PASSWORD_ITERATIONS = 390_000
WEEKS = CURRICULUM
_SCHEMA_READY = False

ALLOWED_EXTENSIONS = {"pdf", "doc", "docx", "ppt", "pptx", "txt", "md", "png", "jpg", "jpeg", "zip"}
PRESENTATION_EXTENSIONS = {"ppt", "pptx", "pdf"}
AVATAR_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
AVATAR_PRESETS = [f"avatar-{index:02d}.svg" for index in range(1, 9)]

CERT_STATUS = {
    "not_started": "Not started",
    "studying": "Studying",
    "scheduled": "Exam scheduled",
    "passed": "Passed",
}
PROJECT_STATUS = {
    "not_started": "Not started",
    "active": "In progress",
    "blocked": "Needs help",
    "completed": "Completed",
}

SAMPLES = {
    "project": {
        "title": "Salesforce project presentation outline",
        "kind": "Project presentation template",
        "description": "A professional sequence for presenting business value, architecture, implementation, testing, contribution, and lessons.",
        "file": "project-presentation-outline.md",
    },
    "research": {
        "title": "Technical research presentation outline",
        "kind": "Research presentation template",
        "description": "A structure for comparing technical options and presenting a supported recommendation.",
        "file": "research-presentation-outline.md",
    },
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def today_iso() -> str:
    return date.today().isoformat()


def split_lines(value) -> list[str]:
    if not value:
        return []
    return [line.strip() for line in str(value).splitlines() if line.strip()]


def valid_iso_date(value: str, required: bool = False) -> str | None:
    value = (value or "").strip()
    if not value:
        if required:
            raise ValueError("A date is required.")
        return None
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError as exc:
        raise ValueError("Enter a valid date.") from exc


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or secrets.token_hex(4)


def valid_email(value: str) -> bool:
    value = (value or "").strip()
    return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value))


def valid_web_url(value: str, field_label: str = "Link") -> str | None:
    value = (value or "").strip()
    if not value:
        return None
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"{field_label} must be a complete http:// or https:// address.")
    return value


def generate_password_hash(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), PASSWORD_ITERATIONS).hex()
    return f"pbkdf2_sha256${PASSWORD_ITERATIONS}${salt}${digest}"


def check_password_hash(stored: str, password: str) -> bool:
    try:
        algorithm, iterations, salt, expected = stored.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), int(iterations)).hex()
        return secrets.compare_digest(actual, expected)
    except (AttributeError, TypeError, ValueError):
        return False


def get_db() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH, timeout=30)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute("PRAGMA busy_timeout = 5000")
    return connection


def query_one(sql: str, params: Iterable = ()):
    connection = get_db()
    try:
        return connection.execute(sql, tuple(params)).fetchone()
    finally:
        connection.close()


def query_all(sql: str, params: Iterable = ()):
    connection = get_db()
    try:
        return connection.execute(sql, tuple(params)).fetchall()
    finally:
        connection.close()


def execute(sql: str, params: Iterable = ()) -> int:
    connection = get_db()
    try:
        cursor = connection.execute(sql, tuple(params))
        connection.commit()
        return cursor.lastrowid
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def executescript(script: str) -> None:
    connection = get_db()
    try:
        connection.executescript(script)
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def ensure_column(table: str, column: str, definition: str) -> None:
    safe_table = re.sub(r"[^A-Za-z0-9_]", "", table)
    columns = {row["name"] for row in query_all(f"PRAGMA table_info({safe_table})")}
    if column not in columns:
        execute(f"ALTER TABLE {safe_table} ADD COLUMN {column} {definition}")


def bootstrap_admin() -> None:
    if query_one("SELECT id FROM users WHERE role='instructor' AND is_admin=1 LIMIT 1"):
        return
    email = os.environ.get("ADMIN_EMAIL", "").strip().lower()
    password = os.environ.get("ADMIN_PASSWORD", "")
    name = os.environ.get("ADMIN_NAME", "Academy Administrator").strip() or "Academy Administrator"
    if not email or len(password) < 12:
        if app.config.get("TESTING") or os.environ.get("ALLOW_DEFAULT_ADMIN", "0") == "1":
            email = email or "admin@projectgroup.local"
            password = password or "ChangeMe123!"
        else:
            raise RuntimeError(
                "No administrator exists. Set ADMIN_EMAIL and ADMIN_PASSWORD (minimum 12 characters) in the WSGI environment."
            )
    execute(
        """
        INSERT INTO users(name,email,password_hash,role,is_admin,is_active,approval_status,created_at)
        VALUES (?,?,?,'instructor',1,1,'approved',?)
        """,
        (name, email, generate_password_hash(password), now_iso()),
    )


def seed_reference_data() -> None:
    for item in CERTIFICATIONS:
        execute(
            """
            INSERT INTO certifications(code,name,short_name,sort_order,is_active)
            VALUES (?,?,?,?,1)
            ON CONFLICT(code) DO UPDATE SET name=excluded.name,short_name=excluded.short_name,
                sort_order=excluded.sort_order,is_active=1
            """,
            (item["code"], item["name"], item["short_name"], item["sort_order"]),
        )

    project = query_one("SELECT id FROM projects WHERE slug=?", (HR_PROJECT["slug"],))
    if project:
        project_id = project["id"]
        # Preserve instructor-edited project content. Only fill fields that are still empty.
        execute(
            """
            UPDATE projects SET
                name=COALESCE(NULLIF(name,''),?),
                short_name=COALESCE(NULLIF(short_name,''),?),
                summary=COALESCE(NULLIF(summary,''),?),
                business_problem=COALESCE(NULLIF(business_problem,''),?),
                users=COALESCE(NULLIF(users,''),?),
                objects=COALESCE(NULLIF(objects,''),?),
                outcomes=COALESCE(NULLIF(outcomes,''),?),
                source_filename=COALESCE(NULLIF(source_filename,''),?),
                updated_at=COALESCE(updated_at,?)
            WHERE id=?
            """,
            (
                HR_PROJECT["name"], HR_PROJECT["short_name"], HR_PROJECT["summary"],
                HR_PROJECT["business_problem"], HR_PROJECT["users"], HR_PROJECT["objects"],
                HR_PROJECT["outcomes"], HR_PROJECT["source_filename"], now_iso(), project_id,
            ),
        )
    else:
        project_id = execute(
            """
            INSERT INTO projects(name,slug,short_name,summary,business_problem,users,objects,outcomes,
                source_filename,is_active,created_at,updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,1,?,?)
            """,
            (
                HR_PROJECT["name"], HR_PROJECT["slug"], HR_PROJECT["short_name"], HR_PROJECT["summary"],
                HR_PROJECT["business_problem"], HR_PROJECT["users"], HR_PROJECT["objects"],
                HR_PROJECT["outcomes"], HR_PROJECT["source_filename"], now_iso(), now_iso(),
            ),
        )

    for item in HR_PROJECT_STEPS:
        execute(
            """
            INSERT INTO project_steps(project_id,step_number,phase,title,summary,tasks,deliverables,
                definition_of_done,review_questions,source_reference,is_published,created_at,updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,1,?,?)
            ON CONFLICT(project_id,step_number) DO UPDATE SET
                phase=COALESCE(NULLIF(project_steps.phase,''),excluded.phase),
                title=COALESCE(NULLIF(project_steps.title,''),excluded.title),
                summary=COALESCE(NULLIF(project_steps.summary,''),excluded.summary),
                tasks=COALESCE(NULLIF(project_steps.tasks,''),excluded.tasks),
                deliverables=COALESCE(NULLIF(project_steps.deliverables,''),excluded.deliverables),
                definition_of_done=COALESCE(NULLIF(project_steps.definition_of_done,''),excluded.definition_of_done),
                review_questions=COALESCE(NULLIF(project_steps.review_questions,''),excluded.review_questions),
                source_reference=COALESCE(NULLIF(project_steps.source_reference,''),excluded.source_reference),
                updated_at=COALESCE(project_steps.updated_at,excluded.updated_at)
            """,
            (
                project_id,
                item["step_number"],
                item["phase"],
                item["title"],
                item["summary"],
                "\n".join(item["tasks"]),
                "\n".join(item["deliverables"]),
                "\n".join(item["definition_of_done"]),
                "\n".join(item["review_questions"]),
                item["source_reference"],
                now_iso(),
                now_iso(),
            ),
        )

    for week in WEEKS:
        execute(
            """
            INSERT INTO weekly_assignments(week_number,title,instructions,presentation_requirements,is_open,notify_students,updated_at)
            VALUES (?,?,?,?,1,1,?)
            ON CONFLICT(week_number) DO UPDATE SET title=COALESCE(NULLIF(weekly_assignments.title,''),excluded.title),
                updated_at=COALESCE(weekly_assignments.updated_at,excluded.updated_at)
            """,
            (week["number"], week["title"], "", week["presentation_requirement"], now_iso()),
        )


def ensure_student_tracking(student_id: int) -> None:
    if not query_one("SELECT id FROM student_projects WHERE student_id=?", (student_id,)):
        project = query_one("SELECT id FROM projects WHERE is_active=1 ORDER BY id LIMIT 1")
        if project:
            execute(
                """
                INSERT INTO student_projects(student_id,project_id,current_step,status,started_at,updated_at)
                VALUES (?,?,1,'active',?,?)
                """,
                (student_id, project["id"], now_iso(), now_iso()),
            )
    for certification in query_all("SELECT id FROM certifications WHERE is_active=1"):
        execute(
            """
            INSERT INTO student_certifications(student_id,certification_id,status,updated_at)
            VALUES (?,?,'not_started',?) ON CONFLICT(student_id,certification_id) DO NOTHING
            """,
            (student_id, certification["id"], now_iso()),
        )


def ensure_schema() -> None:
    global _SCHEMA_READY
    if _SCHEMA_READY:
        return
    executescript((BASE_DIR / "schema.sql").read_text(encoding="utf-8"))

    migration_columns = {
        "users": {"avatar_filename": "TEXT"},
        "submissions": {
            "submitted_at": "TEXT",
            "revision_number": "INTEGER NOT NULL DEFAULT 0",
            "score_business": "REAL",
            "score_evidence": "REAL",
            "score_salesforce": "REAL",
            "score_communication": "REAL",
            "score_professionalism": "REAL",
            "total_score": "REAL",
            "strengths": "TEXT",
            "revision_actions": "TEXT",
            "project_step_number": "INTEGER",
            "project_evidence_url": "TEXT",
            "project_file_name": "TEXT",
            "presentation_title": "TEXT",
            "presentation_summary": "TEXT",
            "presentation_link": "TEXT",
            "presentation_file_name": "TEXT",
            "project_review_status": "TEXT NOT NULL DEFAULT 'pending'",
            "presentation_review_status": "TEXT NOT NULL DEFAULT 'pending'",
            "project_feedback": "TEXT",
            "presentation_feedback": "TEXT",
        },
        "project_steps": {"definition_of_done": "TEXT", "review_questions": "TEXT"},
        "homework_requests": {"start_on": "TEXT"},
    }
    for table, columns in migration_columns.items():
        for column, definition in columns.items():
            ensure_column(table, column, definition)

    execute("UPDATE submissions SET project_file_name=file_name WHERE project_file_name IS NULL AND file_name IS NOT NULL")
    execute("UPDATE submissions SET presentation_link=presentation_url WHERE presentation_link IS NULL AND presentation_url IS NOT NULL")

    bootstrap_admin()
    seed_reference_data()
    for student in query_all("SELECT id FROM users WHERE role='student' AND approval_status='approved'"):
        ensure_student_tracking(student["id"])
    _SCHEMA_READY = True


def current_user():
    user_id = session.get("user_id")
    return query_one("SELECT * FROM users WHERE id=?", (user_id,)) if user_id else None


def csrf_token() -> str:
    token = session.get("_csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["_csrf_token"] = token
    return token


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user():
            flash("Please sign in to continue.", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped


def student_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = current_user()
        if not user:
            return redirect(url_for("login"))
        if user["role"] != "student":
            abort(403)
        if user["approval_status"] != "approved" or not user["is_active"]:
            return redirect(url_for("pending_account"))
        ensure_student_tracking(user["id"])
        return view(*args, **kwargs)

    return wrapped


def instructor_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = current_user()
        if not user:
            return redirect(url_for("login"))
        if user["role"] != "instructor" or not user["is_active"]:
            abort(403)
        return view(*args, **kwargs)

    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = current_user()
        if not user:
            return redirect(url_for("login"))
        if user["role"] != "instructor" or not user["is_admin"]:
            abort(403)
        return view(*args, **kwargs)

    return wrapped


def program_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = current_user()
        if not user:
            return redirect(url_for("login"))
        if user["role"] == "student" and (user["approval_status"] != "approved" or not user["is_active"]):
            return redirect(url_for("pending_account"))
        return view(*args, **kwargs)

    return wrapped


def user_can_access_student(student_id: int, user=None) -> bool:
    user = user or current_user()
    if not user:
        return False
    if user["role"] == "student":
        return user["id"] == student_id
    if user["is_admin"]:
        return True
    student = query_one("SELECT selected_instructor_id FROM users WHERE id=? AND role='student'", (student_id,))
    return bool(student and student["selected_instructor_id"] == user["id"])


def save_upload(uploaded, destination: Path, prefix: str, allowed_extensions: set[str]) -> str | None:
    if not uploaded or not uploaded.filename:
        return None
    if "." not in uploaded.filename:
        raise ValueError("The uploaded file must have an extension.")
    extension = uploaded.filename.rsplit(".", 1)[1].lower()
    if extension not in allowed_extensions:
        raise ValueError("Unsupported file type.")
    stem = secure_filename(uploaded.filename.rsplit(".", 1)[0])[:60] or "file"
    filename = f"{prefix}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}_{stem}.{extension}"
    destination.mkdir(parents=True, exist_ok=True)
    uploaded.save(destination / filename)
    return filename


def avatar_src(filename=None, name="User") -> str:
    if filename and filename.startswith("preset:"):
        preset = filename.split(":", 1)[1]
        if preset in AVATAR_PRESETS:
            return url_for("static", filename=f"avatars/{preset}")
    if filename:
        return url_for("avatar_file", filename=filename)
    return url_for("static", filename="avatars/avatar-01.svg")


def project_for_student(student_id: int):
    return query_one(
        """
        SELECT sp.*,p.name AS project_name,p.short_name,p.summary,p.business_problem,p.users,p.objects,
               p.outcomes,p.source_filename,p.slug
        FROM student_projects sp JOIN projects p ON p.id=sp.project_id WHERE sp.student_id=?
        """,
        (student_id,),
    )


def certification_rows(student_id: int):
    return query_all(
        """
        SELECT sc.*,c.code,c.name,c.short_name,c.sort_order
        FROM certifications c LEFT JOIN student_certifications sc
          ON sc.certification_id=c.id AND sc.student_id=?
        WHERE c.is_active=1 ORDER BY c.sort_order,c.name
        """,
        (student_id,),
    )


def weekly_assignment(week_number: int):
    return query_one("SELECT * FROM weekly_assignments WHERE week_number=?", (week_number,))


def schedule_state(row) -> dict:
    today = date.today()
    if not row:
        return {"key": "open", "label": "Open", "is_open": True, "is_overdue": False}
    if not row["is_open"]:
        return {"key": "closed", "label": "Closed", "is_open": False, "is_overdue": False}
    start_on = date.fromisoformat(row["start_on"]) if row["start_on"] else None
    due_on = date.fromisoformat(row["due_on"]) if row["due_on"] else None
    if start_on and today < start_on:
        return {"key": "scheduled", "label": f"Opens {start_on:%b %d}", "is_open": False, "is_overdue": False}
    if due_on and today > due_on:
        return {"key": "overdue", "label": f"Overdue since {due_on:%b %d}", "is_open": True, "is_overdue": True}
    return {"key": "open", "label": f"Due {due_on:%b %d}" if due_on else "Open", "is_open": True, "is_overdue": False}


def homework_state(row) -> dict:
    today = date.today()
    start_value = row["start_on"] if "start_on" in row.keys() else None
    due_value = row["due_date"] if "due_date" in row.keys() else None
    start_on = date.fromisoformat(start_value) if start_value else None
    due_on = date.fromisoformat(due_value) if due_value else None
    if start_on and today < start_on:
        return {"key": "scheduled", "label": f"Opens {start_on:%b %d}", "is_open": False, "is_overdue": False}
    if due_on and today > due_on and row["status"] not in {"submitted", "under_review", "approved"}:
        return {"key": "overdue", "label": f"Overdue since {due_on:%b %d}", "is_open": True, "is_overdue": True}
    return {"key": "open", "label": f"Due {due_on:%b %d}" if due_on else "Open", "is_open": True, "is_overdue": False}


def parse_score(name: str) -> float | None:
    value = request.form.get(name, "").strip()
    if value == "":
        return None
    try:
        score = float(value)
    except ValueError as exc:
        raise ValueError("Scores must be numeric.") from exc
    if not 0 <= score <= 20:
        raise ValueError("Each rubric score must be between 0 and 20.")
    return score


def email_configured() -> bool:
    return os.environ.get("EMAIL_ENABLED", "0") == "1" and bool(
        os.environ.get("SMTP_USERNAME") and os.environ.get("SMTP_PASSWORD")
    )


def render_email(template_name: str, **context) -> str:
    return render_template(f"emails/{template_name}.html", **context)


def send_portal_email(recipient: str, subject: str, html_body: str, text_body: str = ""):
    if not email_configured():
        return "not_configured", None
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = os.environ.get("EMAIL_FROM", os.environ.get("SMTP_USERNAME"))
    message["To"] = recipient
    message.attach(MIMEText(text_body or re.sub(r"<[^>]+>", " ", html_body), "plain", "utf-8"))
    message.attach(MIMEText(html_body, "html", "utf-8"))
    try:
        host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
        port = int(os.environ.get("SMTP_PORT", "587"))
        with smtplib.SMTP(host, port, timeout=20) as server:
            server.ehlo()
            if os.environ.get("SMTP_USE_TLS", "1") == "1":
                server.starttls()
                server.ehlo()
            server.login(os.environ["SMTP_USERNAME"], os.environ["SMTP_PASSWORD"])
            server.sendmail(message["From"], [recipient], message.as_string())
        return "sent", None
    except Exception as exc:  # Email failure must never roll back the portal action.
        return "failed", str(exc)[:500]


def absolute_portal_url(link_url: str | None) -> str:
    base_url = os.environ.get("APP_BASE_URL", "https://enginproject.pythonanywhere.com").rstrip("/")
    if not link_url:
        return base_url
    return f"{base_url}{link_url}" if link_url.startswith("/") else link_url


def notify_user(
    user_id: int,
    title: str,
    message: str,
    link_url: str | None = None,
    kind: str = "general",
    email_template: str = "notification",
    email_context: dict | None = None,
):
    user = query_one("SELECT name,email FROM users WHERE id=?", (user_id,))
    if not user:
        return None
    notification_id = execute(
        """
        INSERT INTO notifications(user_id,kind,title,message,link_url,is_read,email_status,created_at)
        VALUES (?,?,?,?,?,0,'not_configured',?)
        """,
        (user_id, kind, title, message, link_url, now_iso()),
    )
    context = {
        "student_name": user["name"],
        "title": title,
        "message": message,
        "portal_url": absolute_portal_url(link_url),
    }
    context.update(email_context or {})
    try:
        html = render_email(email_template, **context)
    except Exception:
        html = render_email("notification", **context)
    status, error = send_portal_email(user["email"], title, html, f"{message}\n\nOpen the portal: {context['portal_url']}")
    execute(
        "UPDATE notifications SET email_status=?,email_error=?,emailed_at=? WHERE id=?",
        (status, error, now_iso() if status == "sent" else None, notification_id),
    )
    return notification_id


def homework_assignment_for_user(assignment_id: int, user):
    row = query_one(
        """
        SELECT ha.*,hr.title AS homework_title,hr.topic,hr.instructions,hr.presentation_requirements,
               hr.start_on,hr.due_date,hr.example_url,hr.example_file_name,
               u.name AS student_name,u.email AS student_email,u.selected_instructor_id,u.avatar_filename
        FROM homework_assignments ha JOIN homework_requests hr ON hr.id=ha.request_id
        JOIN users u ON u.id=ha.student_id WHERE ha.id=?
        """,
        (assignment_id,),
    )
    if not row:
        return None
    if user["role"] == "student" and row["student_id"] != user["id"]:
        return None
    if user["role"] == "instructor" and not user["is_admin"] and row["selected_instructor_id"] != user["id"]:
        return None
    return row


@app.before_request
def before_request():
    ensure_schema()
    if request.method == "POST":
        expected = session.get("_csrf_token", "")
        sent = request.form.get("csrf_token", "")
        if not expected or not sent or not secrets.compare_digest(expected, sent):
            abort(400, description="The form session expired. Refresh the page and try again.")


@app.after_request
def security_headers(response):
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    response.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
    response.headers.setdefault(
        "Content-Security-Policy",
        "default-src 'self'; img-src 'self' data:; script-src 'self'; "
        "style-src 'self' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; "
        "frame-ancestors 'self'; base-uri 'self'; form-action 'self'",
    )
    if session.get("user_id"):
        response.headers.setdefault("Cache-Control", "private, no-store")
    if app.config.get("SESSION_COOKIE_SECURE"):
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    return response


@app.context_processor
def inject_globals():
    user = current_user()
    unread = 0
    if user:
        unread = query_one("SELECT COUNT(*) AS total FROM notifications WHERE user_id=? AND is_read=0", (user["id"],))["total"]
    return {
        "current_user": user,
        "csrf_token": csrf_token(),
        "weeks": WEEKS,
        "rubric": RUBRIC,
        "cert_status": CERT_STATUS,
        "project_status": PROJECT_STATUS,
        "split_lines": split_lines,
        "avatar_src": avatar_src,
        "avatar_presets": AVATAR_PRESETS,
        "email_configured": email_configured(),
        "unread_notifications": unread,
        "current_year": date.today().year,
        "app_version": APP_VERSION,
        "schedule_state": schedule_state,
        "homework_state": homework_state,
        "today_iso": today_iso(),
    }


@app.errorhandler(400)
@app.errorhandler(403)
@app.errorhandler(404)
@app.errorhandler(413)
@app.errorhandler(500)
def handle_error(error):
    code = getattr(error, "code", 500)
    messages = {
        400: getattr(error, "description", "The request could not be completed."),
        403: "You do not have permission to open this page.",
        404: "The requested page or file was not found.",
        413: "The uploaded file is larger than the allowed limit.",
        500: "The portal encountered an unexpected error.",
    }
    return render_template("error.html", code=code, message=messages.get(code, messages[500])), code


@app.route("/health")
def health():
    ready = bool(query_one("SELECT name FROM sqlite_master WHERE type='table' AND name='users'"))
    return jsonify({"status": "ok", "database": "ready" if ready else "missing", "version": APP_VERSION})


@app.route("/")
def landing():
    if current_user():
        return redirect(url_for("dashboard"))
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    instructors = query_all("SELECT id,name FROM users WHERE role='instructor' AND is_active=1 ORDER BY is_admin DESC,name")
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        bootcamp = request.form.get("bootcamp_name", "").strip()
        graduation_date = request.form.get("graduation_date", "").strip()
        try:
            linkedin_url = valid_web_url(request.form.get("linkedin_url", ""), "LinkedIn profile")
        except ValueError as exc:
            flash(str(exc), "danger")
            return render_template("register.html", instructors=instructors)
        try:
            instructor_id = int(request.form.get("selected_instructor_id", "0"))
        except ValueError:
            instructor_id = 0
        instructor = query_one("SELECT id FROM users WHERE id=? AND role='instructor' AND is_active=1", (instructor_id,))
        if not name or not valid_email(email) or len(password) < 10 or not instructor:
            flash("Complete all required fields, enter a valid email, and use a password with at least 10 characters.", "danger")
        elif query_one("SELECT id FROM users WHERE lower(email)=?", (email,)):
            flash("An account already exists for that email address.", "danger")
        else:
            preset = request.form.get("avatar_preset", "avatar-01.svg")
            avatar_filename = f"preset:{preset}" if preset in AVATAR_PRESETS else "preset:avatar-01.svg"
            student_id = execute(
                """
                INSERT INTO users(name,email,password_hash,role,is_admin,is_active,approval_status,
                    selected_instructor_id,bootcamp_name,graduation_date,linkedin_url,avatar_filename,created_at)
                VALUES (?,?,?,'student',0,0,'pending',?,?,?,?,?,?)
                """,
                (
                    name,
                    email,
                    generate_password_hash(password),
                    instructor_id,
                    bootcamp,
                    graduation_date or None,
                    linkedin_url or None,
                    avatar_filename,
                    now_iso(),
                ),
            )
            try:
                uploaded_avatar = save_upload(request.files.get("avatar"), AVATAR_DIR, f"user_{student_id}", AVATAR_EXTENSIONS)
                if uploaded_avatar:
                    execute("UPDATE users SET avatar_filename=? WHERE id=?", (uploaded_avatar, student_id))
            except ValueError as exc:
                execute("DELETE FROM users WHERE id=?", (student_id,))
                flash(str(exc), "danger")
                return render_template("register.html", instructors=instructors)
            session.clear()
            session["user_id"] = student_id
            flash("Registration received. Your selected instructor must approve the account.", "success")
            return redirect(url_for("pending_account"))
    return render_template("register.html", instructors=instructors)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = query_one("SELECT * FROM users WHERE lower(email)=?", (email,))
        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session.permanent = True
            return redirect(url_for("dashboard"))
        flash("Invalid email or password.", "danger")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))


@app.route("/dashboard")
@login_required
def dashboard():
    user = current_user()
    if user["role"] == "instructor":
        return redirect(url_for("instructor_dashboard"))
    if user["approval_status"] != "approved" or not user["is_active"]:
        return redirect(url_for("pending_account"))
    return redirect(url_for("student_dashboard"))


@app.route("/pending")
@login_required
def pending_account():
    user = current_user()
    if user["role"] == "instructor":
        return redirect(url_for("instructor_dashboard"))
    instructor = query_one("SELECT name,email FROM users WHERE id=?", (user["selected_instructor_id"],))
    return render_template("pending.html", user=user, instructor=instructor)


@app.route("/account", methods=["GET", "POST"])
@login_required
def account():
    user = current_user()
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        current_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "")
        if not name or not valid_email(email):
            flash("Name and a valid email are required.", "danger")
            return redirect(request.url)
        if query_one("SELECT id FROM users WHERE lower(email)=? AND id<>?", (email, user["id"])):
            flash("Another account already uses that email address.", "danger")
            return redirect(request.url)
        password_hash = user["password_hash"]
        if new_password:
            if len(new_password) < 10 or not check_password_hash(user["password_hash"], current_password):
                flash("Enter the current password and use a new password with at least 10 characters.", "danger")
                return redirect(request.url)
            password_hash = generate_password_hash(new_password)
        avatar_filename = user["avatar_filename"]
        preset = request.form.get("avatar_preset", "")
        if preset in AVATAR_PRESETS:
            avatar_filename = f"preset:{preset}"
        try:
            uploaded_avatar = save_upload(request.files.get("avatar"), AVATAR_DIR, f"user_{user['id']}", AVATAR_EXTENSIONS)
            avatar_filename = uploaded_avatar or avatar_filename
        except ValueError as exc:
            flash(str(exc), "danger")
            return redirect(request.url)
        execute(
            "UPDATE users SET name=?,email=?,password_hash=?,avatar_filename=? WHERE id=?",
            (name, email, password_hash, avatar_filename, user["id"]),
        )
        flash("Account updated.", "success")
        return redirect(request.url)
    return render_template("account.html", user=user)


@app.route("/account/test-email", methods=["POST"])
@login_required
def test_email():
    user = current_user()
    notification_id = notify_user(
        user["id"],
        "Project Group email test",
        "Your portal notifications and email configuration are working.",
        url_for("notifications"),
        "system",
    )
    row = query_one("SELECT email_status,email_error FROM notifications WHERE id=?", (notification_id,))
    if row["email_status"] == "sent":
        flash("Test email sent successfully.", "success")
    elif row["email_status"] == "not_configured":
        flash("The in-app notification was created. Email is not configured yet.", "warning")
    else:
        flash(f"The notification was created, but email failed: {row['email_error']}", "danger")
    return redirect(url_for("account"))


@app.route("/avatars/<path:filename>")
@login_required
def avatar_file(filename):
    filename = secure_filename(filename)
    viewer = current_user()
    owner = query_one("SELECT id,role,selected_instructor_id FROM users WHERE avatar_filename=?", (filename,))
    if not owner:
        abort(404)
    allowed = viewer["id"] == owner["id"] or viewer["is_admin"]
    if viewer["role"] == "instructor" and owner["role"] == "student":
        allowed = allowed or owner["selected_instructor_id"] == viewer["id"]
    if viewer["role"] == "student" and owner["role"] == "instructor":
        allowed = allowed or viewer["selected_instructor_id"] == owner["id"]
    if not allowed:
        abort(403)
    return send_from_directory(AVATAR_DIR, filename)


@app.route("/uploads/<path:filename>")
@login_required
def uploaded_file(filename):
    filename = secure_filename(filename)
    user = current_user()
    row = query_one(
        """
        SELECT s.student_id,u.selected_instructor_id FROM submissions s
        JOIN users u ON u.id=s.student_id
        WHERE s.file_name=? OR s.project_file_name=? OR s.presentation_file_name=?
        """,
        (filename, filename, filename),
    )
    if not row:
        row = query_one(
            """
            SELECT ha.student_id,u.selected_instructor_id FROM homework_assignments ha
            JOIN users u ON u.id=ha.student_id WHERE ha.file_name=?
            """,
            (filename,),
        )
    if not row:
        example = query_one("SELECT id,created_by FROM homework_requests WHERE example_file_name=?", (filename,))
        if example:
            if user["role"] == "student":
                allowed = query_one(
                    """SELECT ha.id FROM homework_assignments ha JOIN homework_requests hr ON hr.id=ha.request_id
                       WHERE ha.student_id=? AND hr.example_file_name=?""",
                    (user["id"], filename),
                )
                if not allowed:
                    abort(403)
            elif not user["is_admin"] and example["created_by"] != user["id"]:
                abort(403)
            return send_from_directory(UPLOAD_DIR, filename, as_attachment=True)
        abort(404)
    if user["role"] == "student" and row["student_id"] != user["id"]:
        abort(403)
    if user["role"] == "instructor" and not user["is_admin"] and row["selected_instructor_id"] != user["id"]:
        abort(403)
    return send_from_directory(UPLOAD_DIR, filename, as_attachment=True)


@app.route("/samples")
@login_required
def samples():
    return render_template("samples.html", samples=SAMPLES)


@app.route("/samples/<sample_key>/download")
@login_required
def download_sample(sample_key):
    sample = SAMPLES.get(sample_key)
    if not sample:
        abort(404)
    path = SAMPLE_DIR / sample["file"]
    if not path.exists():
        abort(404)
    return send_file(path, as_attachment=True, download_name=sample["file"])


@app.route("/curriculum")
@program_required
def curriculum():
    schedules = {row["week_number"]: row for row in query_all("SELECT * FROM weekly_assignments ORDER BY week_number")}
    return render_template("curriculum.html", schedules=schedules)


@app.route("/curriculum/week/<int:week_number>")
@program_required
def curriculum_week(week_number):
    if not 1 <= week_number <= 8:
        abort(404)
    return render_template("curriculum_week.html", week=WEEKS[week_number - 1], assignment=weekly_assignment(week_number))


@app.route("/project/<int:project_id>/source")
@program_required
def download_project_source(project_id):
    user = current_user()
    project = query_one("SELECT * FROM projects WHERE id=?", (project_id,))
    if not project or not project["source_filename"]:
        abort(404)
    if user["role"] == "student" and not query_one(
        "SELECT id FROM student_projects WHERE student_id=? AND project_id=?", (user["id"], project_id)
    ):
        abort(403)
    return send_from_directory(PROJECT_FILE_DIR, project["source_filename"], as_attachment=True)


@app.route("/student")
@student_required
def student_dashboard():
    user = current_user()
    project = project_for_student(user["id"])
    certs = certification_rows(user["id"])
    submissions = query_all("SELECT * FROM submissions WHERE student_id=? ORDER BY week_number", (user["id"],))
    by_week = {row["week_number"]: row for row in submissions}
    approved = sum(row["status"] == "approved" for row in submissions)
    submitted = sum(row["status"] in {"submitted", "under_review", "revision", "approved"} for row in submissions)
    next_week = next((number for number in range(1, 9) if not by_week.get(number) or by_week[number]["status"] != "approved"), None)
    approved_scores = [row["total_score"] for row in submissions if row["status"] == "approved" and row["total_score"] is not None]
    average_score = round(sum(approved_scores) / len(approved_scores), 1) if approved_scores else None
    total_steps = query_one("SELECT COUNT(*) AS total FROM project_steps WHERE project_id=? AND is_published=1", (project["project_id"],))["total"] if project else 0
    homework_due = query_one(
        "SELECT COUNT(*) AS total FROM homework_assignments WHERE student_id=? AND status IN ('assigned','revision')", (user["id"],)
    )["total"]
    recent_notifications = query_all("SELECT * FROM notifications WHERE user_id=? ORDER BY created_at DESC LIMIT 4", (user["id"],))
    schedules = {row["week_number"]: row for row in query_all("SELECT * FROM weekly_assignments ORDER BY week_number")}
    return render_template(
        "student_dashboard.html",
        project=project,
        certs=certs,
        by_week=by_week,
        approved=approved,
        submitted=submitted,
        next_week=next_week,
        average_score=average_score,
        total_steps=total_steps,
        homework_due=homework_due,
        recent_notifications=recent_notifications,
        schedules=schedules,
    )


@app.route("/student/checklist")
@student_required
def student_checklist():
    user = current_user()
    project = project_for_student(user["id"])
    certs = certification_rows(user["id"])
    submissions = query_all("SELECT * FROM submissions WHERE student_id=? ORDER BY week_number", (user["id"],))
    by_week = {row["week_number"]: row for row in submissions}
    total_steps = query_one("SELECT COUNT(*) AS total FROM project_steps WHERE project_id=? AND is_published=1", (project["project_id"],))["total"] if project else 0
    return render_template("student_checklist.html", project=project, certs=certs, by_week=by_week, total_steps=total_steps)


@app.route("/student/project")
@student_required
def project_learning():
    user = current_user()
    project = project_for_student(user["id"])
    if not project:
        return render_template("error.html", code=409, message="No project has been assigned yet."), 409
    steps = query_all("SELECT * FROM project_steps WHERE project_id=? AND is_published=1 ORDER BY step_number", (project["project_id"],))
    return render_template("project_learning.html", project=project, steps=steps)


@app.route("/student/project/step/<int:step_number>")
@student_required
def project_step(step_number):
    user = current_user()
    project = project_for_student(user["id"])
    if not project:
        abort(404)
    row = query_one(
        "SELECT * FROM project_steps WHERE project_id=? AND step_number=? AND is_published=1",
        (project["project_id"], step_number),
    )
    if not row:
        abort(404)
    previous_step = query_one(
        "SELECT step_number FROM project_steps WHERE project_id=? AND step_number<? AND is_published=1 ORDER BY step_number DESC LIMIT 1",
        (project["project_id"], step_number),
    )
    next_step = query_one(
        "SELECT step_number FROM project_steps WHERE project_id=? AND step_number>? AND is_published=1 ORDER BY step_number LIMIT 1",
        (project["project_id"], step_number),
    )
    return render_template("project_step.html", project=project, step=row, previous_step=previous_step, next_step=next_step)


@app.route("/student/week/<int:week_number>", methods=["GET", "POST"])
@student_required
def student_week(week_number):
    if not 1 <= week_number <= 8:
        abort(404)
    user = current_user()
    week = WEEKS[week_number - 1]
    assignment = weekly_assignment(week_number)
    access = schedule_state(assignment)
    submission = query_one("SELECT * FROM submissions WHERE student_id=? AND week_number=?", (user["id"], week_number))
    project = project_for_student(user["id"])
    current_step = query_one(
        "SELECT * FROM project_steps WHERE project_id=? AND step_number=? AND is_published=1",
        (project["project_id"], project["current_step"]),
    ) if project else None

    if request.method == "POST":
        if not access["is_open"]:
            flash("This week is not open for submission yet.", "warning")
            return redirect(request.url)
        if submission and submission["status"] == "approved":
            flash("This week is approved and locked. Ask the instructor to reopen it before editing.", "warning")
            return redirect(request.url)
        action = request.form.get("action", "draft")
        status = "submitted" if action == "submit" else "draft"
        project_story = request.form.get("project_story", "").strip()
        requirement_notes = request.form.get("requirement_notes", "").strip()
        research_notes = request.form.get("research_notes", "").strip()
        design_notes = request.form.get("design_notes", "").strip()
        try:
            project_evidence_url = valid_web_url(request.form.get("project_evidence_url", ""), "Project evidence link")
            presentation_link = valid_web_url(request.form.get("presentation_link", ""), "Presentation link")
        except ValueError as exc:
            flash(str(exc), "danger")
            return redirect(request.url)
        presentation_title = request.form.get("presentation_title", "").strip()
        presentation_summary = request.form.get("presentation_summary", "").strip()
        reflection = request.form.get("reflection", "").strip()
        try:
            project_step_number = int(request.form.get("project_step_number", project["current_step"] if project else 0))
        except (TypeError, ValueError):
            project_step_number = project["current_step"] if project else None
        project_file_name = submission["project_file_name"] if submission else None
        presentation_file_name = submission["presentation_file_name"] if submission else None
        try:
            project_file_name = save_upload(
                request.files.get("project_file"), UPLOAD_DIR, f"project_{user['id']}_{week_number}", ALLOWED_EXTENSIONS
            ) or project_file_name
            presentation_file_name = save_upload(
                request.files.get("presentation_file"), UPLOAD_DIR, f"presentation_{user['id']}_{week_number}", PRESENTATION_EXTENSIONS
            ) or presentation_file_name
        except ValueError as exc:
            flash(str(exc), "danger")
            return redirect(request.url)
        if status == "submitted":
            if not project_story or not (project_evidence_url or project_file_name):
                flash("Requirement 1 needs a project summary and an evidence link or file.", "danger")
                return redirect(request.url)
            if not presentation_title or not presentation_summary or not (presentation_link or presentation_file_name):
                flash("Requirement 2 needs a title, summary, and presentation link or file.", "danger")
                return redirect(request.url)
        now = now_iso()
        submitted_at = now if status == "submitted" else (submission["submitted_at"] if submission else None)
        revision_number = submission["revision_number"] if submission else 0
        if submission and submission["status"] == "revision" and status == "submitted":
            revision_number += 1
        project_review_status = "pending" if status == "submitted" else (submission["project_review_status"] if submission else "pending")
        presentation_review_status = "pending" if status == "submitted" else (submission["presentation_review_status"] if submission else "pending")
        values = (
            status, project_story, requirement_notes, research_notes, design_notes, project_step_number,
            project_evidence_url or None, project_file_name, presentation_title, presentation_summary,
            presentation_link or None, presentation_file_name, presentation_link or None, reflection,
            submitted_at, revision_number, project_review_status, presentation_review_status, now,
        )
        if submission:
            execute(
                """
                UPDATE submissions SET status=?,project_story=?,requirement_notes=?,research_notes=?,design_notes=?,
                    project_step_number=?,project_evidence_url=?,project_file_name=?,presentation_title=?,
                    presentation_summary=?,presentation_link=?,presentation_file_name=?,presentation_url=?,reflection=?,
                    submitted_at=?,revision_number=?,project_review_status=?,presentation_review_status=?,updated_at=?
                WHERE id=? AND student_id=?
                """,
                values + (submission["id"], user["id"]),
            )
        else:
            execute(
                """
                INSERT INTO submissions(status,project_story,requirement_notes,research_notes,design_notes,
                    project_step_number,project_evidence_url,project_file_name,presentation_title,presentation_summary,
                    presentation_link,presentation_file_name,presentation_url,reflection,submitted_at,revision_number,
                    project_review_status,presentation_review_status,updated_at,student_id,week_number)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                values + (user["id"], week_number),
            )
        flash("Both weekly requirements were submitted for review." if status == "submitted" else "Draft saved.", "success")
        return redirect(request.url)
    return render_template(
        "student_week.html", week=week, assignment=assignment, access=access, submission=submission,
        project=project, current_step=current_step,
    )


@app.route("/student/homework")
@student_required
def student_homework():
    user = current_user()
    rows = query_all(
        """
        SELECT ha.*,hr.title,hr.topic,hr.start_on,hr.due_date,hr.instructions,hr.presentation_requirements
        FROM homework_assignments ha JOIN homework_requests hr ON hr.id=ha.request_id
        WHERE ha.student_id=? ORDER BY CASE ha.status WHEN 'revision' THEN 1 WHEN 'assigned' THEN 2
            WHEN 'submitted' THEN 3 WHEN 'under_review' THEN 4 ELSE 5 END,
            CASE WHEN hr.due_date IS NULL OR hr.due_date='' THEN 1 ELSE 0 END,hr.due_date,ha.assigned_at DESC
        """,
        (user["id"],),
    )
    return render_template("student_homework.html", assignments=rows)


@app.route("/student/homework/<int:assignment_id>", methods=["GET", "POST"])
@student_required
def student_homework_detail(assignment_id):
    user = current_user()
    row = homework_assignment_for_user(assignment_id, user)
    if not row:
        abort(404)
    state = homework_state(row)
    if request.method == "POST":
        if not state["is_open"]:
            flash("This assignment is not open yet.", "warning")
            return redirect(request.url)
        if row["status"] == "approved":
            flash("This presentation homework is approved and locked.", "warning")
            return redirect(request.url)
        status = "submitted" if request.form.get("action", "draft") == "submit" else "assigned"
        presentation_title = request.form.get("presentation_title", "").strip()
        submission_notes = request.form.get("submission_notes", "").strip()
        try:
            presentation_url = valid_web_url(request.form.get("presentation_url", ""), "Presentation link")
        except ValueError as exc:
            flash(str(exc), "danger")
            return redirect(request.url)
        file_name = row["file_name"]
        try:
            file_name = save_upload(
                request.files.get("presentation_file"), UPLOAD_DIR, f"homework_{user['id']}_{assignment_id}", PRESENTATION_EXTENSIONS
            ) or file_name
        except ValueError as exc:
            flash(str(exc), "danger")
            return redirect(request.url)
        if status == "submitted" and (not presentation_title or not (presentation_url or file_name)):
            flash("Add a presentation title and a presentation link or file.", "danger")
            return redirect(request.url)
        execute(
            """
            UPDATE homework_assignments SET status=?,presentation_title=?,submission_notes=?,presentation_url=?,
                file_name=?,submitted_at=?,updated_at=? WHERE id=? AND student_id=?
            """,
            (
                status, presentation_title, submission_notes, presentation_url or None, file_name,
                now_iso() if status == "submitted" else row["submitted_at"], now_iso(), assignment_id, user["id"],
            ),
        )
        flash("Presentation homework submitted." if status == "submitted" else "Homework draft saved.", "success")
        return redirect(request.url)
    return render_template("student_homework_detail.html", assignment=row, state=state)


@app.route("/notifications")
@login_required
def notifications():
    rows = query_all("SELECT * FROM notifications WHERE user_id=? ORDER BY created_at DESC LIMIT 100", (current_user()["id"],))
    return render_template("notifications.html", notifications=rows)


@app.route("/notifications/<int:notification_id>/open", methods=["POST"])
@login_required
def open_notification(notification_id):
    user = current_user()
    row = query_one("SELECT * FROM notifications WHERE id=? AND user_id=?", (notification_id, user["id"]))
    if not row:
        abort(404)
    execute("UPDATE notifications SET is_read=1 WHERE id=?", (notification_id,))
    return redirect(row["link_url"] or url_for("notifications"))


@app.route("/notifications/read-all", methods=["POST"])
@login_required
def read_all_notifications():
    execute("UPDATE notifications SET is_read=1 WHERE user_id=?", (current_user()["id"],))
    return redirect(url_for("notifications"))


@app.route("/instructor")
@instructor_required
def instructor_dashboard():
    user = current_user()
    scope = "" if user["is_admin"] else " AND u.selected_instructor_id=?"
    params = [] if user["is_admin"] else [user["id"]]
    pending = query_one("SELECT COUNT(*) AS total FROM users u WHERE u.role='student' AND u.approval_status='pending'" + scope, params)["total"]
    students = query_one("SELECT COUNT(*) AS total FROM users u WHERE u.role='student' AND u.approval_status='approved'" + scope, params)["total"]
    reviews = query_one("SELECT COUNT(*) AS total FROM submissions s JOIN users u ON u.id=s.student_id WHERE s.status='submitted'" + scope, params)["total"]
    needs_help = query_one("SELECT COUNT(*) AS total FROM student_projects sp JOIN users u ON u.id=sp.student_id WHERE sp.status='blocked'" + scope, params)["total"]
    homework_reviews = query_one("SELECT COUNT(*) AS total FROM homework_assignments ha JOIN users u ON u.id=ha.student_id WHERE ha.status='submitted'" + scope, params)["total"]
    recent = query_all(
        """SELECT s.*,u.name AS student_name FROM submissions s JOIN users u ON u.id=s.student_id
           WHERE s.status IN ('submitted','under_review','revision')""" + scope + " ORDER BY s.updated_at DESC LIMIT 8",
        params,
    )
    upcoming_weeks = query_all("SELECT * FROM weekly_assignments ORDER BY week_number")
    return render_template(
        "instructor_dashboard.html", pending=pending, students=students, reviews=reviews,
        needs_help=needs_help, homework_reviews=homework_reviews, recent=recent, upcoming_weeks=upcoming_weeks,
    )


@app.route("/instructor/approvals")
@instructor_required
def approvals():
    user = current_user()
    sql = """SELECT u.*,i.name AS instructor_name FROM users u LEFT JOIN users i ON i.id=u.selected_instructor_id
             WHERE u.role='student' AND u.approval_status='pending'"""
    params = []
    if not user["is_admin"]:
        sql += " AND u.selected_instructor_id=?"
        params.append(user["id"])
    sql += " ORDER BY u.created_at"
    return render_template("approvals.html", students=query_all(sql, params))


@app.route("/instructor/student/<int:student_id>/decision", methods=["POST"])
@instructor_required
def registration_decision(student_id):
    user = current_user()
    student = query_one("SELECT * FROM users WHERE id=? AND role='student'", (student_id,))
    if not student:
        abort(404)
    if not user["is_admin"] and student["selected_instructor_id"] != user["id"]:
        abort(403)
    decision = request.form.get("decision")
    if decision not in {"approved", "rejected"}:
        abort(400)
    execute(
        "UPDATE users SET approval_status=?,is_active=?,approved_by=?,approved_at=? WHERE id=?",
        (decision, 1 if decision == "approved" else 0, user["id"], now_iso(), student_id),
    )
    if decision == "approved":
        ensure_student_tracking(student_id)
        notify_user(
            student_id,
            "Your Project Group account was approved",
            "You can now open the curriculum, project learning, weekly work, checklist, and presentation homework.",
            url_for("student_dashboard"),
            "approval",
            "account_approved",
            {"instructor_name": user["name"]},
        )
    else:
        notify_user(
            student_id,
            "Project Group registration update",
            "Your registration was not approved. Contact the selected instructor for more information.",
            url_for("pending_account"),
            "approval",
        )
    flash(f"{student['name']} was {decision}.", "success")
    return redirect(url_for("approvals"))


@app.route("/instructor/students")
@instructor_required
def instructor_students():
    user = current_user()
    cohort = request.args.get("cohort", "").strip()
    sql = """
        SELECT u.*,sp.current_step,sp.status AS project_status,p.short_name AS project_name,
               COUNT(DISTINCT s.id) AS submission_count,
               COUNT(DISTINCT CASE WHEN s.status='approved' THEN s.id END) AS approved_weeks,
               ROUND(AVG(CASE WHEN s.status='approved' THEN s.total_score END),1) AS average_score,
               MAX(CASE WHEN c.code='ADMIN' THEN sc.status END) AS admin_cert_status,
               MAX(CASE WHEN c.code='PDI' THEN sc.status END) AS developer_cert_status
        FROM users u LEFT JOIN student_projects sp ON sp.student_id=u.id
        LEFT JOIN projects p ON p.id=sp.project_id LEFT JOIN submissions s ON s.student_id=u.id
        LEFT JOIN student_certifications sc ON sc.student_id=u.id LEFT JOIN certifications c ON c.id=sc.certification_id
        WHERE u.role='student' AND u.approval_status='approved'
    """
    params = []
    if not user["is_admin"]:
        sql += " AND u.selected_instructor_id=?"
        params.append(user["id"])
    if cohort:
        sql += " AND u.bootcamp_name=?"
        params.append(cohort)
    sql += " GROUP BY u.id ORDER BY u.bootcamp_name,u.name"
    cohort_sql = "SELECT DISTINCT bootcamp_name FROM users WHERE role='student' AND approval_status='approved' AND bootcamp_name<>''"
    cohort_params = []
    if not user["is_admin"]:
        cohort_sql += " AND selected_instructor_id=?"
        cohort_params.append(user["id"])
    cohort_sql += " ORDER BY bootcamp_name"
    return render_template(
        "instructor_students.html", students=query_all(sql, params), cohorts=query_all(cohort_sql, cohort_params), selected_cohort=cohort,
    )


@app.route("/instructor/student/<int:student_id>", methods=["GET", "POST"])
@instructor_required
def student_progress(student_id):
    user = current_user()
    if not user_can_access_student(student_id, user):
        abort(403)
    student = query_one(
        """SELECT s.*,i.name AS instructor_name FROM users s LEFT JOIN users i ON i.id=s.selected_instructor_id
           WHERE s.id=? AND s.role='student'""",
        (student_id,),
    )
    if not student:
        abort(404)
    ensure_student_tracking(student_id)
    if request.method == "POST":
        action = request.form.get("action")
        if action == "project":
            try:
                project_id = int(request.form.get("project_id", "0"))
                current_step_number = int(request.form.get("current_step", "1"))
            except ValueError:
                flash("Select a valid project and step.", "danger")
                return redirect(request.url)
            project_row = query_one("SELECT id FROM projects WHERE id=? AND is_active=1", (project_id,))
            max_step = query_one("SELECT MAX(step_number) AS value FROM project_steps WHERE project_id=? AND is_published=1", (project_id,))["value"] or 1
            status = request.form.get("project_status", "active")
            note = request.form.get("instructor_note", "").strip()
            if not project_row or status not in PROJECT_STATUS or not 1 <= current_step_number <= max_step:
                flash("Select a valid project status and step.", "danger")
                return redirect(request.url)
            execute(
                "UPDATE student_projects SET project_id=?,current_step=?,status=?,instructor_note=?,updated_at=? WHERE student_id=?",
                (project_id, current_step_number, status, note, now_iso(), student_id),
            )
            notify_user(
                student_id,
                "Your project tracker was updated",
                f"Your current project step is {current_step_number} and the status is {PROJECT_STATUS[status]}.",
                url_for("project_learning"),
                "project",
            )
            flash("Project tracker updated and the student was notified.", "success")
        elif action == "certification":
            try:
                certification_id = int(request.form.get("certification_id", "0"))
            except ValueError:
                certification_id = 0
            status = request.form.get("certification_status", "not_started")
            target_date = request.form.get("target_date", "").strip()
            notes = request.form.get("certification_notes", "").strip()
            if status not in CERT_STATUS or not query_one("SELECT id FROM certifications WHERE id=?", (certification_id,)):
                flash("Select a valid certification status.", "danger")
                return redirect(request.url)
            execute(
                """
                UPDATE student_certifications SET status=?,target_date=?,notes=?,verified_by=?,verified_at=?,updated_at=?
                WHERE student_id=? AND certification_id=?
                """,
                (
                    status, target_date or None, notes, user["id"] if status == "passed" else None,
                    now_iso() if status == "passed" else None, now_iso(), student_id, certification_id,
                ),
            )
            certification = query_one("SELECT short_name FROM certifications WHERE id=?", (certification_id,))
            notify_user(
                student_id,
                f"{certification['short_name']} tracker updated",
                f"Your certification status is now {CERT_STATUS[status]}.",
                url_for("student_checklist"),
                "certification",
            )
            flash("Certification tracker updated and the student was notified.", "success")
        return redirect(request.url)

    project = project_for_student(student_id)
    certs = certification_rows(student_id)
    submissions = query_all("SELECT * FROM submissions WHERE student_id=? ORDER BY week_number", (student_id,))
    by_week = {row["week_number"]: row for row in submissions}
    approved_scores = [row["total_score"] for row in submissions if row["status"] == "approved" and row["total_score"] is not None]
    average_score = round(sum(approved_scores) / len(approved_scores), 1) if approved_scores else None
    projects = query_all("SELECT id,name FROM projects WHERE is_active=1 ORDER BY name")
    max_step = query_one("SELECT MAX(step_number) AS value FROM project_steps WHERE project_id=? AND is_published=1", (project["project_id"],))["value"] if project else 1
    return render_template(
        "student_progress.html", student=student, project=project, certs=certs, by_week=by_week,
        average_score=average_score, projects=projects, max_step=max_step or 1,
    )


@app.route("/instructor/reviews")
@instructor_required
def reviews():
    user = current_user()
    status = request.args.get("status", "").strip()
    student_id = request.args.get("student_id", "").strip()
    week_number = request.args.get("week", "").strip()
    sql = """SELECT s.*,u.name AS student_name,u.avatar_filename FROM submissions s JOIN users u ON u.id=s.student_id
             WHERE s.status IN ('submitted','under_review','revision','approved')"""
    params = []
    if not user["is_admin"]:
        sql += " AND u.selected_instructor_id=?"
        params.append(user["id"])
    if status in {"submitted", "under_review", "revision", "approved"}:
        sql += " AND s.status=?"
        params.append(status)
    if student_id.isdigit():
        sql += " AND s.student_id=?"
        params.append(int(student_id))
    if week_number.isdigit() and 1 <= int(week_number) <= 8:
        sql += " AND s.week_number=?"
        params.append(int(week_number))
    sql += " ORDER BY CASE s.status WHEN 'submitted' THEN 1 WHEN 'under_review' THEN 2 WHEN 'revision' THEN 3 ELSE 4 END,s.updated_at DESC"
    student_sql = "SELECT id,name FROM users WHERE role='student' AND approval_status='approved'"
    student_params = []
    if not user["is_admin"]:
        student_sql += " AND selected_instructor_id=?"
        student_params.append(user["id"])
    student_sql += " ORDER BY name"
    return render_template(
        "reviews.html", submissions=query_all(sql, params), students=query_all(student_sql, student_params),
        selected_status=status, selected_student=student_id, selected_week=week_number,
    )


@app.route("/instructor/review/<int:submission_id>", methods=["GET", "POST"])
@instructor_required
def review_submission(submission_id):
    user = current_user()
    row = query_one(
        """
        SELECT s.*,u.name AS student_name,u.email AS student_email,u.selected_instructor_id,u.avatar_filename,
               p.name AS project_name
        FROM submissions s JOIN users u ON u.id=s.student_id
        LEFT JOIN student_projects sp ON sp.student_id=u.id LEFT JOIN projects p ON p.id=sp.project_id
        WHERE s.id=?
        """,
        (submission_id,),
    )
    if not row:
        abort(404)
    if not user["is_admin"] and row["selected_instructor_id"] != user["id"]:
        abort(403)
    if request.method == "POST":
        status = request.form.get("status", "under_review")
        project_review_status = request.form.get("project_review_status", "pending")
        presentation_review_status = request.form.get("presentation_review_status", "pending")
        valid_review_statuses = {"pending", "revision", "approved"}
        if status not in {"under_review", "revision", "approved"} or project_review_status not in valid_review_statuses or presentation_review_status not in valid_review_statuses:
            abort(400)
        if status == "approved" and (project_review_status != "approved" or presentation_review_status != "approved"):
            flash("Approve both requirements before approving the entire week.", "danger")
            return redirect(request.url)
        try:
            scores = {item["key"]: parse_score(f"score_{item['key']}") for item in RUBRIC}
        except ValueError as exc:
            flash(str(exc), "danger")
            return redirect(request.url)
        if status in {"revision", "approved"} and any(value is None for value in scores.values()):
            flash("Complete all five rubric scores before revision or approval.", "danger")
            return redirect(request.url)
        strengths = request.form.get("strengths", "").strip()
        revision_actions = request.form.get("revision_actions", "").strip()
        instructor_feedback = request.form.get("instructor_feedback", "").strip()
        project_feedback = request.form.get("project_feedback", "").strip()
        presentation_feedback = request.form.get("presentation_feedback", "").strip()
        if status == "revision" and not (revision_actions or project_feedback or presentation_feedback):
            flash("Explain the required changes before returning the work for revision.", "danger")
            return redirect(request.url)
        total_score = round(sum(value for value in scores.values() if value is not None), 1) if any(value is not None for value in scores.values()) else None
        execute(
            """
            UPDATE submissions SET status=?,project_review_status=?,presentation_review_status=?,project_feedback=?,
                presentation_feedback=?,score_business=?,score_evidence=?,score_salesforce=?,score_communication=?,
                score_professionalism=?,total_score=?,strengths=?,revision_actions=?,instructor_feedback=?,reviewed_by=?,
                reviewed_at=?,updated_at=? WHERE id=?
            """,
            (
                status, project_review_status, presentation_review_status, project_feedback, presentation_feedback,
                scores["business"], scores["evidence"], scores["salesforce"], scores["communication"],
                scores["professionalism"], total_score, strengths, revision_actions, instructor_feedback,
                user["id"], now_iso(), now_iso(), submission_id,
            ),
        )
        status_label = status.replace("_", " ").title()
        score_text = f" Score: {total_score}/100." if total_score is not None else ""
        notify_user(
            row["student_id"],
            f"Week {row['week_number']} review completed",
            f"Your instructor marked the week as {status_label}.{score_text} Open the review for project and presentation feedback.",
            url_for("student_week", week_number=row["week_number"]),
            "weekly_review",
            "weekly_reviewed",
            {"week_number": row["week_number"], "review_status": status_label, "score": total_score},
        )
        flash("Grade and feedback saved. The student was notified.", "success")
        return redirect(request.url)
    return render_template("review_submission.html", row=row, week=WEEKS[row["week_number"] - 1], assignment=weekly_assignment(row["week_number"]))


@app.route("/instructor/homework", methods=["GET", "POST"])
@instructor_required
def manage_homework():
    user = current_user()
    student_sql = "SELECT id,name,email,bootcamp_name,avatar_filename FROM users WHERE role='student' AND approval_status='approved'"
    student_params = []
    if not user["is_admin"]:
        student_sql += " AND selected_instructor_id=?"
        student_params.append(user["id"])
    student_sql += " ORDER BY bootcamp_name,name"
    students = query_all(student_sql, student_params)
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        topic = request.form.get("topic", "").strip()
        instructions = request.form.get("instructions", "").strip()
        requirements = request.form.get("presentation_requirements", "").strip()
        try:
            example_url = valid_web_url(request.form.get("example_url", ""), "Example link")
            start_on = valid_iso_date(request.form.get("start_on", ""))
            due_date = valid_iso_date(request.form.get("due_date", ""), required=True)
        except ValueError as exc:
            flash(str(exc), "danger")
            return redirect(request.url)
        if start_on and due_date and start_on > due_date:
            flash("The available date cannot be after the due date.", "danger")
            return redirect(request.url)
        selected_ids = {int(value) for value in request.form.getlist("student_ids") if value.isdigit()}
        selected_ids &= {student["id"] for student in students}
        if not title or not topic or not instructions or not requirements or not selected_ids:
            flash("Add the title, topic, instructions, requirements, due date, and at least one student.", "danger")
        else:
            try:
                example_file_name = save_upload(
                    request.files.get("example_file"), UPLOAD_DIR, f"homework_example_{user['id']}", PRESENTATION_EXTENSIONS
                )
            except ValueError as exc:
                flash(str(exc), "danger")
                return redirect(request.url)
            request_id = execute(
                """
                INSERT INTO homework_requests(title,topic,instructions,presentation_requirements,start_on,due_date,
                    example_url,example_file_name,created_by,is_active,created_at,updated_at)
                VALUES (?,?,?,?,?,?,?,?,?,1,?,?)
                """,
                (
                    title, topic, instructions, requirements, start_on, due_date, example_url or None,
                    example_file_name, user["id"], now_iso(), now_iso(),
                ),
            )
            for student_id in sorted(selected_ids):
                assignment_id = execute(
                    """INSERT INTO homework_assignments(request_id,student_id,status,assigned_at,updated_at)
                       VALUES (?,?,'assigned',?,?)""",
                    (request_id, student_id, now_iso(), now_iso()),
                )
                notify_user(
                    student_id,
                    f"New presentation homework: {title}",
                    f"Topic: {topic}. Due date: {due_date}. Open the assignment for instructions and presentation requirements.",
                    url_for("student_homework_detail", assignment_id=assignment_id),
                    "homework",
                    "homework_assigned",
                    {
                        "topic": topic,
                        "due_on": due_date,
                        "instructions": instructions,
                        "requirements": requirements,
                    },
                )
            flash(f"Homework assigned to {len(selected_ids)} student(s).", "success")
            return redirect(url_for("homework_request_detail", request_id=request_id))
    request_sql = """
        SELECT hr.*,u.name AS creator_name,COUNT(ha.id) AS assigned_count,
               COUNT(CASE WHEN ha.status='submitted' THEN 1 END) AS ready_count
        FROM homework_requests hr JOIN users u ON u.id=hr.created_by
        LEFT JOIN homework_assignments ha ON ha.request_id=hr.id WHERE 1=1
    """
    params = []
    if not user["is_admin"]:
        request_sql += " AND hr.created_by=?"
        params.append(user["id"])
    request_sql += " GROUP BY hr.id ORDER BY hr.created_at DESC"
    return render_template("manage_homework.html", students=students, requests=query_all(request_sql, params))


@app.route("/instructor/homework/<int:request_id>")
@instructor_required
def homework_request_detail(request_id):
    user = current_user()
    homework = query_one(
        "SELECT hr.*,u.name AS creator_name FROM homework_requests hr JOIN users u ON u.id=hr.created_by WHERE hr.id=?",
        (request_id,),
    )
    if not homework or (not user["is_admin"] and homework["created_by"] != user["id"]):
        abort(404)
    assignments = query_all(
        """
        SELECT ha.*,u.name AS student_name,u.email AS student_email,u.avatar_filename
        FROM homework_assignments ha JOIN users u ON u.id=ha.student_id
        WHERE ha.request_id=? ORDER BY CASE ha.status WHEN 'submitted' THEN 1 WHEN 'revision' THEN 2
            WHEN 'under_review' THEN 3 WHEN 'assigned' THEN 4 ELSE 5 END,u.name
        """,
        (request_id,),
    )
    return render_template("homework_request_detail.html", homework=homework, assignments=assignments)


@app.route("/instructor/homework/review/<int:assignment_id>", methods=["GET", "POST"])
@instructor_required
def review_homework(assignment_id):
    user = current_user()
    row = homework_assignment_for_user(assignment_id, user)
    if not row:
        abort(404)
    if request.method == "POST":
        status = request.form.get("status", "under_review")
        if status not in {"under_review", "revision", "approved"}:
            abort(400)
        score_raw = request.form.get("score", "").strip()
        try:
            score = float(score_raw) if score_raw else None
        except ValueError:
            flash("Score must be a number.", "danger")
            return redirect(request.url)
        if score is not None and not 0 <= score <= 100:
            flash("Score must be between 0 and 100.", "danger")
            return redirect(request.url)
        comment = request.form.get("instructor_comment", "").strip()
        if status in {"revision", "approved"} and score is None:
            flash("Enter a score before revision or approval.", "danger")
            return redirect(request.url)
        if status == "revision" and not comment:
            flash("Explain what the student must revise.", "danger")
            return redirect(request.url)
        execute(
            """
            UPDATE homework_assignments SET status=?,score=?,instructor_comment=?,reviewed_by=?,reviewed_at=?,updated_at=?
            WHERE id=?
            """,
            (status, score, comment, user["id"], now_iso(), now_iso(), assignment_id),
        )
        status_label = status.replace("_", " ").title()
        notify_user(
            row["student_id"],
            f"Presentation homework reviewed: {row['homework_title']}",
            f"Your homework status is {status_label}." + (f" Score: {score}/100." if score is not None else ""),
            url_for("student_homework_detail", assignment_id=assignment_id),
            "homework_review",
            "homework_reviewed",
            {"review_status": status_label, "score": score, "comment": comment},
        )
        flash("Homework review saved and the student was notified.", "success")
        return redirect(request.url)
    return render_template("review_homework.html", assignment=row)


@app.route("/instructor/weeks", methods=["GET", "POST"])
@instructor_required
def manage_week_schedule():
    user = current_user()
    if request.method == "POST":
        try:
            week_number = int(request.form.get("week_number", "0"))
        except ValueError:
            abort(400)
        if not 1 <= week_number <= 8:
            abort(400)
        title = request.form.get("title", "").strip() or WEEKS[week_number - 1]["title"]
        instructions = request.form.get("instructions", "").strip()
        requirements = request.form.get("presentation_requirements", "").strip()
        try:
            start_on = valid_iso_date(request.form.get("start_on", ""))
            due_on = valid_iso_date(request.form.get("due_on", ""))
        except ValueError as exc:
            flash(str(exc), "danger")
            return redirect(request.url)
        if start_on and due_on and start_on > due_on:
            flash("The start date cannot be after the due date.", "danger")
            return redirect(request.url)
        is_open = 1 if request.form.get("is_open") == "1" else 0
        notify_students = request.form.get("notify_students") == "1"
        execute(
            """
            UPDATE weekly_assignments SET title=?,instructions=?,presentation_requirements=?,start_on=?,due_on=?,
                is_open=?,notify_students=?,updated_by=?,updated_at=? WHERE week_number=?
            """,
            (title, instructions, requirements, start_on, due_on, is_open, 1 if notify_students else 0, user["id"], now_iso(), week_number),
        )
        if notify_students:
            student_sql = "SELECT id FROM users WHERE role='student' AND approval_status='approved' AND is_active=1"
            params = []
            if not user["is_admin"]:
                student_sql += " AND selected_instructor_id=?"
                params.append(user["id"])
            for student in query_all(student_sql, params):
                state_text = "open" if is_open else "closed"
                due_text = f" Due date: {due_on}." if due_on else ""
                notify_user(
                    student["id"],
                    f"Week {week_number} schedule updated",
                    f"Week {week_number}, {title}, is {state_text}.{due_text} Open the portal for instructions.",
                    url_for("student_week", week_number=week_number),
                    "weekly_schedule",
                    "weekly_due_set",
                    {
                        "week_number": week_number,
                        "week_title": title,
                        "start_on": start_on,
                        "due_on": due_on,
                        "instructions": instructions,
                        "requirements": requirements,
                    },
                )
        flash(f"Week {week_number} schedule saved." + (" Students were notified." if notify_students else ""), "success")
        return redirect(url_for("manage_week_schedule"))
    return render_template("manage_week_schedule.html", week_assignments=query_all("SELECT * FROM weekly_assignments ORDER BY week_number"))


@app.route("/instructor/projects", methods=["GET", "POST"])
@instructor_required
def manage_projects():
    user = current_user()
    if request.method == "POST":
        if not user["is_admin"]:
            abort(403)
        name = request.form.get("name", "").strip()
        summary = request.form.get("summary", "").strip()
        if not name or not summary:
            flash("Project name and summary are required.", "danger")
        else:
            base_slug = slugify(name)
            slug = base_slug
            suffix = 2
            while query_one("SELECT id FROM projects WHERE slug=?", (slug,)):
                slug = f"{base_slug}-{suffix}"
                suffix += 1
            project_id = execute(
                """
                INSERT INTO projects(name,slug,short_name,summary,business_problem,users,objects,outcomes,is_active,created_at,updated_at)
                VALUES (?,?,?,?,?,?,?,?,1,?,?)
                """,
                (
                    name, slug, request.form.get("short_name", "").strip(), summary,
                    request.form.get("business_problem", "").strip(), request.form.get("users", "").strip(),
                    request.form.get("objects", "").strip(), request.form.get("outcomes", "").strip(), now_iso(), now_iso(),
                ),
            )
            flash("Project created. Add its implementation steps.", "success")
            return redirect(url_for("manage_project", project_id=project_id))
    rows = query_all(
        """
        SELECT p.*,COUNT(DISTINCT ps.id) AS step_count,COUNT(DISTINCT sp.student_id) AS student_count
        FROM projects p LEFT JOIN project_steps ps ON ps.project_id=p.id
        LEFT JOIN student_projects sp ON sp.project_id=p.id GROUP BY p.id ORDER BY p.name
        """
    )
    return render_template("manage_projects.html", projects=rows)


@app.route("/instructor/projects/<int:project_id>", methods=["GET", "POST"])
@instructor_required
def manage_project(project_id):
    user = current_user()
    project = query_one("SELECT * FROM projects WHERE id=?", (project_id,))
    if not project:
        abort(404)
    if request.method == "POST":
        if not user["is_admin"]:
            abort(403)
        action = request.form.get("action")
        if action == "project":
            name = request.form.get("name", "").strip()
            summary = request.form.get("summary", "").strip()
            if not name or not summary:
                flash("Project name and summary are required.", "danger")
            else:
                execute(
                    """
                    UPDATE projects SET name=?,short_name=?,summary=?,business_problem=?,users=?,objects=?,outcomes=?,
                        is_active=?,updated_at=? WHERE id=?
                    """,
                    (
                        name, request.form.get("short_name", "").strip(), summary,
                        request.form.get("business_problem", "").strip(), request.form.get("users", "").strip(),
                        request.form.get("objects", "").strip(), request.form.get("outcomes", "").strip(),
                        1 if request.form.get("is_active") == "1" else 0, now_iso(), project_id,
                    ),
                )
                flash("Project updated.", "success")
        elif action == "new_step":
            try:
                step_number = int(request.form.get("step_number", "0"))
            except ValueError:
                step_number = 0
            title = request.form.get("title", "").strip()
            if step_number < 1 or not title:
                flash("Step number and title are required.", "danger")
            elif query_one("SELECT id FROM project_steps WHERE project_id=? AND step_number=?", (project_id, step_number)):
                flash("That step number already exists.", "danger")
            else:
                step_id = execute(
                    """
                    INSERT INTO project_steps(project_id,step_number,phase,title,summary,tasks,deliverables,
                        definition_of_done,review_questions,source_reference,is_published,created_at,updated_at)
                    VALUES (?,?,?,?,?,?,?,?,?,?,1,?,?)
                    """,
                    (
                        project_id, step_number, request.form.get("phase", "Implementation").strip() or "Implementation",
                        title, request.form.get("summary", "").strip(), request.form.get("tasks", "").strip(),
                        request.form.get("deliverables", "").strip(), request.form.get("definition_of_done", "").strip(),
                        request.form.get("review_questions", "").strip(), request.form.get("source_reference", "").strip(),
                        now_iso(), now_iso(),
                    ),
                )
                flash("Project step created.", "success")
                return redirect(url_for("edit_project_step", step_id=step_id))
        return redirect(request.url)
    steps = query_all("SELECT * FROM project_steps WHERE project_id=? ORDER BY step_number", (project_id,))
    return render_template("manage_project.html", project=project, steps=steps)


@app.route("/instructor/project-step/<int:step_id>", methods=["GET", "POST"])
@admin_required
def edit_project_step(step_id):
    row = query_one("SELECT ps.*,p.name AS project_name FROM project_steps ps JOIN projects p ON p.id=ps.project_id WHERE ps.id=?", (step_id,))
    if not row:
        abort(404)
    if request.method == "POST":
        try:
            step_number = int(request.form.get("step_number", row["step_number"]))
        except ValueError:
            flash("Enter a valid step number.", "danger")
            return redirect(request.url)
        title = request.form.get("title", "").strip()
        if step_number < 1 or not title:
            flash("Step number and title are required.", "danger")
            return redirect(request.url)
        duplicate = query_one(
            "SELECT id FROM project_steps WHERE project_id=? AND step_number=? AND id<>?",
            (row["project_id"], step_number, step_id),
        )
        if duplicate:
            flash("That step number already exists in this project.", "danger")
            return redirect(request.url)
        execute(
            """
            UPDATE project_steps SET step_number=?,phase=?,title=?,summary=?,tasks=?,deliverables=?,definition_of_done=?,
                review_questions=?,source_reference=?,is_published=?,updated_at=? WHERE id=?
            """,
            (
                step_number, request.form.get("phase", "").strip(), title, request.form.get("summary", "").strip(),
                request.form.get("tasks", "").strip(), request.form.get("deliverables", "").strip(),
                request.form.get("definition_of_done", "").strip(), request.form.get("review_questions", "").strip(),
                request.form.get("source_reference", "").strip(), 1 if request.form.get("is_published") == "1" else 0,
                now_iso(), step_id,
            ),
        )
        flash("Project step updated.", "success")
        return redirect(request.url)
    return render_template("edit_project_step.html", step=row)


@app.route("/instructor/manage", methods=["GET", "POST"])
@admin_required
def manage_instructors():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not name or not valid_email(email) or len(password) < 10:
            flash("Name, a valid email, and a password of at least 10 characters are required.", "danger")
        elif query_one("SELECT id FROM users WHERE lower(email)=?", (email,)):
            flash("An account already exists for that email.", "danger")
        else:
            execute(
                """
                INSERT INTO users(name,email,password_hash,role,is_admin,is_active,approval_status,avatar_filename,created_at)
                VALUES (?,?,?,'instructor',0,1,'approved','preset:avatar-01.svg',?)
                """,
                (name, email, generate_password_hash(password), now_iso()),
            )
            flash("Instructor account created.", "success")
            return redirect(request.url)
    instructors = query_all(
        """
        SELECT i.*,COUNT(s.id) AS student_count FROM users i LEFT JOIN users s ON s.selected_instructor_id=i.id
        WHERE i.role='instructor' GROUP BY i.id ORDER BY i.is_admin DESC,i.name
        """
    )
    return render_template("manage_instructors.html", instructors=instructors)


@app.cli.command("init-db")
def init_db_command():
    """Create or migrate the database and seed reference data."""
    global _SCHEMA_READY
    _SCHEMA_READY = False
    ensure_schema()
    print(f"Database ready at {DB_PATH} (version {APP_VERSION}).")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")), debug=os.environ.get("FLASK_DEBUG", "0") == "1")
