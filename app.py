import base64
import hashlib
import io
import os
import secrets
import sqlite3
from datetime import date, datetime, timezone
from functools import wraps
from pathlib import Path

from flask import (
    Flask, abort, flash, jsonify, redirect, render_template, request,
    send_file, send_from_directory, session, url_for
)
from werkzeug.utils import secure_filename

from curriculum_content import CURRICULUM, RUBRIC

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("PROJECT_GROUP_DATABASE", BASE_DIR / "project_group.db"))
UPLOAD_DIR = Path(os.environ.get("PROJECT_GROUP_UPLOADS", BASE_DIR / "uploads"))
SAMPLE_DIR = BASE_DIR / "static" / "sample_b64"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-this-in-production")
app.config["MAX_CONTENT_LENGTH"] = 12 * 1024 * 1024
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = os.environ.get("COOKIE_SECURE", "0") == "1"

PASSWORD_ITERATIONS = 260_000
ALLOWED_EXTENSIONS = {"pdf", "doc", "docx", "ppt", "pptx", "txt", "md", "png", "jpg", "jpeg", "zip"}
WEEKS = CURRICULUM
PROGRAM_PHASES = [
    {
        "number": 1,
        "title": "Build the project story",
        "description": "Position the bootcamp experience honestly, understand the business need, and translate it into Salesforce requirements.",
        "weeks": [1, 2, 3],
    },
    {
        "number": 2,
        "title": "Research before deciding",
        "description": "Learn how to find reliable Salesforce information, compare options, and make an evidence-based recommendation.",
        "weeks": [4],
    },
    {
        "number": 3,
        "title": "Design a defensible solution",
        "description": "Plan the data, security, automation, testing, deployment, and risk approach before building.",
        "weeks": [5, 6],
    },
    {
        "number": 4,
        "title": "Present and defend",
        "description": "Turn the work into a clear presentation and answer interview questions with specific ownership and reasoning.",
        "weeks": [7, 8],
    },
]
APP_VERSION = "3.0"
_SCHEMA_READY = False

SAMPLES = {
    "project": {
        "title": "EMA: Salesforce Event Management Application",
        "kind": "Complete project presentation",
        "description": "A model for explaining business capabilities, data architecture, security, automation, Apex standards, delivery steps, and business value.",
        "file": "Improved_EMA_Project_Sample.pptx",
        "b64": "Improved_EMA_Project_Sample.pptx.b64",
        "lessons": ["Start with the business problem", "Connect requirements to Salesforce capabilities", "Explain design decisions", "Close with measurable value"],
    },
    "research": {
        "title": "What Is an API?",
        "kind": "Research presentation",
        "description": "A model for turning a technical subject into a simple, well-researched explanation using analogies, real examples, structure, and a clear conclusion.",
        "file": "Improved_API_Research_Sample.pptx",
        "b64": "Improved_API_Research_Sample.pptx.b64",
        "lessons": ["Define the research question", "Teach from simple to complex", "Use credible examples", "Make one recommendation or takeaway"],
    },
}


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def generate_password_hash(password):
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), PASSWORD_ITERATIONS).hex()
    return f"pbkdf2_sha256${PASSWORD_ITERATIONS}${salt}${digest}"


def check_password_hash(stored, password):
    try:
        algorithm, iterations, salt, expected = stored.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), int(iterations)).hex()
        return secrets.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def query_one(sql, params=()):
    with get_db() as conn:
        return conn.execute(sql, params).fetchone()


def query_all(sql, params=()):
    with get_db() as conn:
        return conn.execute(sql, params).fetchall()


def execute(sql, params=()):
    with get_db() as conn:
        cur = conn.execute(sql, params)
        conn.commit()
        return cur.lastrowid


def init_db():
    with get_db() as conn:
        conn.executescript((BASE_DIR / "schema.sql").read_text(encoding="utf-8"))
        conn.commit()
    bootstrap_admin()


def bootstrap_admin():
    email = os.environ.get("ADMIN_EMAIL", "admin@projectgroup.local").strip().lower()
    password = os.environ.get("ADMIN_PASSWORD", "ChangeMe123!")
    name = os.environ.get("ADMIN_NAME", "Academy Administrator").strip()
    if not query_one("SELECT id FROM users WHERE lower(email)=?", (email,)):
        execute(
            """
            INSERT INTO users(name,email,password_hash,role,is_admin,is_active,approval_status,created_at)
            VALUES (?,?,?,'instructor',1,1,'approved',?)
            """,
            (name, email, generate_password_hash(password), now_iso()),
        )


def ensure_column(table, column, definition):
    columns = {row["name"] for row in query_all(f"PRAGMA table_info({table})")}
    if column not in columns:
        execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def migrate_schema():
    additions = {
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
    }
    for column, definition in additions.items():
        ensure_column("submissions", column, definition)


def ensure_schema():
    global _SCHEMA_READY
    if _SCHEMA_READY:
        return
    required = query_one("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    if not required:
        init_db()
    else:
        migrate_schema()
        bootstrap_admin()
    _SCHEMA_READY = True


def current_user():
    if "user_id" not in session:
        return None
    return query_one("SELECT * FROM users WHERE id=?", (session["user_id"],))


def csrf_token():
    token = session.get("_csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["_csrf_token"] = token
    return token


def user_can_access_student(student_id, user=None):
    user = user or current_user()
    if not user:
        return False
    if user["role"] == "student":
        return user["id"] == student_id
    if user["is_admin"]:
        return True
    student = query_one("SELECT selected_instructor_id FROM users WHERE id=? AND role='student'", (student_id,))
    return bool(student and student["selected_instructor_id"] == user["id"])


def parse_score(name):
    value = request.form.get(name, "").strip()
    if value == "":
        return None
    try:
        score = float(value)
    except ValueError:
        raise ValueError("Scores must be numeric.")
    if score < 0 or score > 20:
        raise ValueError("Each rubric score must be between 0 and 20.")
    return score


@app.before_request
def before_request():
    ensure_schema()
    if request.method == "POST":
        expected = session.get("_csrf_token", "")
        sent = request.form.get("csrf_token", "")
        if not expected or not sent or not secrets.compare_digest(expected, sent):
            abort(400)


@app.context_processor
def inject_globals():
    return {
        "current_user": current_user(),
        "csrf_token": csrf_token(),
        "weeks": WEEKS,
        "rubric": RUBRIC,
        "program_phases": PROGRAM_PHASES,
        "current_year": date.today().year,
    }


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user():
            flash("Please sign in to continue.", "warning")
            return redirect(url_for("login"))
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
        return view(*args, **kwargs)
    return wrapped


def program_access_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = current_user()
        if not user:
            return redirect(url_for("login"))
        if user["role"] == "student" and (user["approval_status"] != "approved" or not user["is_active"]):
            return redirect(url_for("pending_account"))
        if user["role"] == "instructor" and not user["is_active"]:
            abort(403)
        return view(*args, **kwargs)
    return wrapped


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/health")
def health():
    database_ready = bool(query_one("SELECT name FROM sqlite_master WHERE type='table' AND name='users'"))
    return jsonify({"status": "ok", "database": "ready" if database_ready else "missing", "version": APP_VERSION})


@app.route("/")
def landing():
    user = current_user()
    if user:
        return redirect(url_for("dashboard"))
    instructors = query_all("SELECT id,name FROM users WHERE role='instructor' AND is_active=1 ORDER BY is_admin DESC,name")
    return render_template("landing.html", instructors=instructors, samples=SAMPLES)


@app.route("/register", methods=["GET", "POST"])
def register():
    instructors = query_all("SELECT id,name FROM users WHERE role='instructor' AND is_active=1 ORDER BY is_admin DESC,name")
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        bootcamp = request.form.get("bootcamp_name", "").strip()
        graduation_date = request.form.get("graduation_date", "").strip()
        linkedin_url = request.form.get("linkedin_url", "").strip()
        try:
            instructor_id = int(request.form.get("selected_instructor_id", "0"))
        except ValueError:
            instructor_id = 0
        instructor = query_one("SELECT id FROM users WHERE id=? AND role='instructor' AND is_active=1", (instructor_id,))
        if not name or not email or len(password) < 8 or not instructor:
            flash("Complete all required fields and use a password with at least 8 characters.", "danger")
        elif query_one("SELECT id FROM users WHERE lower(email)=?", (email,)):
            flash("An account already exists for this email address.", "danger")
        else:
            user_id = execute(
                """
                INSERT INTO users(name,email,password_hash,role,is_admin,is_active,approval_status,
                    selected_instructor_id,bootcamp_name,graduation_date,linkedin_url,created_at)
                VALUES (?,?,?,'student',0,0,'pending',?,?,?,?,?)
                """,
                (name, email, generate_password_hash(password), instructor_id, bootcamp, graduation_date, linkedin_url, now_iso()),
            )
            session.clear()
            session["user_id"] = user_id
            flash("Registration received. Your selected instructor must approve your account.", "success")
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
        if not name or not email:
            flash("Name and email are required.", "danger")
            return redirect(request.url)
        duplicate = query_one("SELECT id FROM users WHERE lower(email)=? AND id<>?", (email, user["id"]))
        if duplicate:
            flash("Another account already uses that email address.", "danger")
            return redirect(request.url)
        password_hash = user["password_hash"]
        if new_password:
            if len(new_password) < 8 or not check_password_hash(user["password_hash"], current_password):
                flash("Enter your current password and use a new password with at least 8 characters.", "danger")
                return redirect(request.url)
            password_hash = generate_password_hash(new_password)
        execute("UPDATE users SET name=?,email=?,password_hash=? WHERE id=?", (name, email, password_hash, user["id"]))
        flash("Account updated.", "success")
        return redirect(request.url)
    return render_template("account.html", user=user)


@app.route("/samples")
def samples():
    return render_template("samples.html", samples=SAMPLES)


@app.route("/samples/<sample_key>/download")
def download_sample(sample_key):
    sample = SAMPLES.get(sample_key)
    if not sample:
        abort(404)
    direct_file = SAMPLE_DIR / sample["file"]
    if direct_file.exists():
        return send_file(direct_file, as_attachment=True, download_name=sample["file"])
    encoded_file = SAMPLE_DIR / sample["b64"]
    if not encoded_file.exists():
        abort(404)
    payload = base64.b64decode(encoded_file.read_text(encoding="ascii"))
    return send_file(
        io.BytesIO(payload),
        as_attachment=True,
        download_name=sample["file"],
        mimetype="application/vnd.openxmlformats-officedocument.presentationml.presentation",
    )


@app.route("/curriculum")
@program_access_required
def curriculum():
    user = current_user()
    submissions = []
    by_week = {}
    if user["role"] == "student":
        submissions = query_all("SELECT * FROM submissions WHERE student_id=? ORDER BY week_number", (user["id"],))
        by_week = {row["week_number"]: row for row in submissions}
    return render_template("curriculum.html", by_week=by_week)


@app.route("/curriculum/week/<int:week_number>")
@program_access_required
def curriculum_week(week_number):
    if not 1 <= week_number <= 8:
        abort(404)
    user = current_user()
    if user["role"] == "student":
        return redirect(url_for("student_week", week_number=week_number))
    return render_template("curriculum_week.html", week=WEEKS[week_number - 1])


@app.route("/student")
@student_required
def student_dashboard():
    user = current_user()
    submissions = query_all("SELECT * FROM submissions WHERE student_id=? ORDER BY week_number", (user["id"],))
    by_week = {row["week_number"]: row for row in submissions}
    approved = sum(1 for row in submissions if row["status"] == "approved")
    submitted = sum(1 for row in submissions if row["status"] in {"submitted", "under_review", "revision", "approved"})
    approved_scores = [row["total_score"] for row in submissions if row["status"] == "approved" and row["total_score"] is not None]
    average_score = round(sum(approved_scores) / len(approved_scores), 1) if approved_scores else None
    next_week = next((week["number"] for week in WEEKS if not by_week.get(week["number"]) or by_week[week["number"]]["status"] != "approved"), None)
    return render_template(
        "student_dashboard.html",
        by_week=by_week,
        approved=approved,
        submitted=submitted,
        average_score=average_score,
        next_week=next_week,
    )


@app.route("/student/week/<int:week_number>", methods=["GET", "POST"])
@student_required
def student_week(week_number):
    if not 1 <= week_number <= 8:
        abort(404)
    user = current_user()
    week = WEEKS[week_number - 1]
    submission = query_one("SELECT * FROM submissions WHERE student_id=? AND week_number=?", (user["id"], week_number))
    if request.method == "POST":
        if submission and submission["status"] == "approved":
            flash("This week is approved. Ask your instructor to reopen it before making changes.", "warning")
            return redirect(request.url)
        action = request.form.get("action", "draft")
        status = "submitted" if action == "submit" else "draft"
        project_story = request.form.get("project_story", "").strip()
        requirement_notes = request.form.get("requirement_notes", "").strip()
        research_notes = request.form.get("research_notes", "").strip()
        design_notes = request.form.get("design_notes", "").strip()
        presentation_url = request.form.get("presentation_url", "").strip()
        reflection = request.form.get("reflection", "").strip()
        if status == "submitted" and not project_story:
            flash("Add the main weekly answer before submitting for review.", "danger")
            return redirect(request.url)
        file_name = submission["file_name"] if submission else None
        uploaded = request.files.get("file")
        if uploaded and uploaded.filename:
            if not allowed_file(uploaded.filename):
                flash("Unsupported file type.", "danger")
                return redirect(request.url)
            safe = secure_filename(uploaded.filename)
            file_name = f"{user['id']}_{week_number}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{safe}"
            uploaded.save(UPLOAD_DIR / file_name)
        now = now_iso()
        submitted_at = now if status == "submitted" else (submission["submitted_at"] if submission else None)
        revision_number = submission["revision_number"] if submission else 0
        if submission and submission["status"] == "revision" and status == "submitted":
            revision_number += 1
        if submission:
            execute(
                """
                UPDATE submissions SET status=?,project_story=?,requirement_notes=?,research_notes=?,
                    design_notes=?,presentation_url=?,reflection=?,file_name=?,submitted_at=?,
                    revision_number=?,updated_at=? WHERE id=? AND student_id=?
                """,
                (
                    status, project_story, requirement_notes, research_notes, design_notes,
                    presentation_url, reflection, file_name, submitted_at, revision_number,
                    now, submission["id"], user["id"],
                ),
            )
        else:
            execute(
                """
                INSERT INTO submissions(student_id,week_number,status,project_story,requirement_notes,
                    research_notes,design_notes,presentation_url,reflection,file_name,submitted_at,
                    revision_number,updated_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    user["id"], week_number, status, project_story, requirement_notes,
                    research_notes, design_notes, presentation_url, reflection, file_name,
                    submitted_at, revision_number, now,
                ),
            )
        flash("Week submitted for review." if status == "submitted" else "Draft saved.", "success")
        return redirect(request.url)
    return render_template("student_week.html", week=week, submission=submission)


@app.route("/uploads/<path:filename>")
@login_required
def uploaded_file(filename):
    user = current_user()
    row = query_one(
        "SELECT s.*,u.selected_instructor_id FROM submissions s JOIN users u ON u.id=s.student_id WHERE s.file_name=?",
        (filename,),
    )
    if not row:
        abort(404)
    if user["role"] == "student" and row["student_id"] != user["id"]:
        abort(403)
    if user["role"] == "instructor" and not user["is_admin"] and row["selected_instructor_id"] != user["id"]:
        abort(403)
    return send_from_directory(UPLOAD_DIR, filename, as_attachment=True)


@app.route("/instructor")
@instructor_required
def instructor_dashboard():
    user = current_user()
    scope_sql = "" if user["is_admin"] else " AND u.selected_instructor_id=?"
    params = [] if user["is_admin"] else [user["id"]]
    pending = query_one("SELECT COUNT(*) AS total FROM users u WHERE u.role='student' AND u.approval_status='pending'" + scope_sql, params)["total"]
    students = query_one("SELECT COUNT(*) AS total FROM users u WHERE u.role='student' AND u.approval_status='approved'" + scope_sql, params)["total"]
    reviews = query_one(
        """
        SELECT COUNT(*) AS total FROM submissions s JOIN users u ON u.id=s.student_id
        WHERE s.status='submitted'
        """ + scope_sql,
        params,
    )["total"]
    recent = query_all(
        """
        SELECT s.*,u.name AS student_name FROM submissions s JOIN users u ON u.id=s.student_id
        WHERE s.status IN ('submitted','under_review','revision')
        """ + scope_sql + " ORDER BY s.updated_at DESC LIMIT 10",
        params,
    )
    return render_template("instructor_dashboard.html", pending=pending, students=students, reviews=reviews, recent=recent)


@app.route("/instructor/approvals")
@instructor_required
def approvals():
    user = current_user()
    sql = """
        SELECT u.*,i.name AS instructor_name FROM users u
        LEFT JOIN users i ON i.id=u.selected_instructor_id
        WHERE u.role='student' AND u.approval_status='pending'
    """
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
    flash(f"{student['name']} was {decision}.", "success")
    return redirect(url_for("approvals"))


@app.route("/instructor/students")
@instructor_required
def instructor_students():
    user = current_user()
    sql = """
        SELECT u.*,COUNT(s.id) AS submission_count,
               SUM(CASE WHEN s.status='approved' THEN 1 ELSE 0 END) AS approved_weeks,
               ROUND(AVG(CASE WHEN s.status='approved' THEN s.total_score END),1) AS average_score
        FROM users u LEFT JOIN submissions s ON s.student_id=u.id
        WHERE u.role='student' AND u.approval_status='approved'
    """
    params = []
    if not user["is_admin"]:
        sql += " AND u.selected_instructor_id=?"
        params.append(user["id"])
    sql += " GROUP BY u.id ORDER BY u.name"
    return render_template("instructor_students.html", students=query_all(sql, params))


@app.route("/instructor/student/<int:student_id>")
@instructor_required
def student_progress(student_id):
    user = current_user()
    if not user_can_access_student(student_id, user):
        abort(403)
    student = query_one(
        """
        SELECT s.*,i.name AS instructor_name FROM users s
        LEFT JOIN users i ON i.id=s.selected_instructor_id
        WHERE s.id=? AND s.role='student'
        """,
        (student_id,),
    )
    if not student:
        abort(404)
    submissions = query_all("SELECT * FROM submissions WHERE student_id=? ORDER BY week_number", (student_id,))
    by_week = {row["week_number"]: row for row in submissions}
    approved_scores = [row["total_score"] for row in submissions if row["status"] == "approved" and row["total_score"] is not None]
    average_score = round(sum(approved_scores) / len(approved_scores), 1) if approved_scores else None
    return render_template("student_progress.html", student=student, by_week=by_week, average_score=average_score)


@app.route("/instructor/reviews")
@instructor_required
def reviews():
    user = current_user()
    status = request.args.get("status", "").strip()
    student_id = request.args.get("student_id", "").strip()
    week_number = request.args.get("week", "").strip()
    sql = """
        SELECT s.*,u.name AS student_name FROM submissions s JOIN users u ON u.id=s.student_id
        WHERE s.status IN ('submitted','under_review','revision','approved')
    """
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
        "reviews.html",
        submissions=query_all(sql, params),
        students=query_all(student_sql, student_params),
        selected_status=status,
        selected_student=student_id,
        selected_week=week_number,
    )


@app.route("/instructor/review/<int:submission_id>", methods=["GET", "POST"])
@instructor_required
def review_submission(submission_id):
    user = current_user()
    row = query_one(
        """
        SELECT s.*,u.name AS student_name,u.email AS student_email,u.selected_instructor_id
        FROM submissions s JOIN users u ON u.id=s.student_id WHERE s.id=?
        """,
        (submission_id,),
    )
    if not row:
        abort(404)
    if not user["is_admin"] and row["selected_instructor_id"] != user["id"]:
        abort(403)
    if request.method == "POST":
        status = request.form.get("status", "under_review")
        if status not in {"under_review", "revision", "approved"}:
            abort(400)
        try:
            scores = {
                "business": parse_score("score_business"),
                "evidence": parse_score("score_evidence"),
                "salesforce": parse_score("score_salesforce"),
                "communication": parse_score("score_communication"),
                "professionalism": parse_score("score_professionalism"),
            }
        except ValueError as exc:
            flash(str(exc), "danger")
            return redirect(request.url)
        if status in {"revision", "approved"} and any(value is None for value in scores.values()):
            flash("Complete all five rubric scores before requiring revision or approving the week.", "danger")
            return redirect(request.url)
        feedback = request.form.get("instructor_feedback", "").strip()
        strengths = request.form.get("strengths", "").strip()
        revision_actions = request.form.get("revision_actions", "").strip()
        if status == "revision" and not revision_actions:
            flash("List the specific revision actions the student must complete.", "danger")
            return redirect(request.url)
        total_score = round(sum(value for value in scores.values() if value is not None), 1) if any(value is not None for value in scores.values()) else None
        execute(
            """
            UPDATE submissions SET status=?,score_business=?,score_evidence=?,score_salesforce=?,
                score_communication=?,score_professionalism=?,total_score=?,strengths=?,
                revision_actions=?,instructor_feedback=?,reviewed_by=?,reviewed_at=?,updated_at=?
            WHERE id=?
            """,
            (
                status, scores["business"], scores["evidence"], scores["salesforce"],
                scores["communication"], scores["professionalism"], total_score,
                strengths, revision_actions, feedback, user["id"], now_iso(), now_iso(), submission_id,
            ),
        )
        flash("Grade and feedback saved.", "success")
        return redirect(request.url)
    return render_template("review_submission.html", row=row, week=WEEKS[row["week_number"] - 1])


@app.route("/instructor/manage", methods=["GET", "POST"])
@admin_required
def manage_instructors():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not name or not email or len(password) < 8:
            flash("Name, email, and an 8-character temporary password are required.", "danger")
        elif query_one("SELECT id FROM users WHERE lower(email)=?", (email,)):
            flash("That email is already in use.", "danger")
        else:
            execute(
                "INSERT INTO users(name,email,password_hash,role,is_admin,is_active,approval_status,created_at) VALUES (?,?,?,'instructor',0,1,'approved',?)",
                (name, email, generate_password_hash(password), now_iso()),
            )
            flash("Instructor account created.", "success")
            return redirect(request.url)
    instructors = query_all(
        """
        SELECT i.*,COUNT(s.id) AS selected_students FROM users i
        LEFT JOIN users s ON s.selected_instructor_id=i.id AND s.role='student'
        WHERE i.role='instructor' GROUP BY i.id ORDER BY i.is_admin DESC,i.name
        """
    )
    return render_template("manage_instructors.html", instructors=instructors)


@app.errorhandler(400)
def error_400(_):
    return render_template("error.html", code=400, message="The request could not be validated."), 400


@app.errorhandler(403)
def error_403(_):
    return render_template("error.html", code=403, message="You do not have access to this page."), 403


@app.errorhandler(404)
def error_404(_):
    return render_template("error.html", code=404, message="The requested page was not found."), 404


if __name__ == "__main__":
    ensure_schema()
    app.run(debug=True)
