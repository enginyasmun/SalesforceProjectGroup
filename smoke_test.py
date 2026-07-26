"""End-to-end smoke test for Project Group portal v4."""
from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path

ROOT = Path(tempfile.mkdtemp(prefix="project-group-v4-smoke-"))
os.environ["SECRET_KEY"] = "smoke-test-secret"
os.environ["ADMIN_NAME"] = "Test Admin"
os.environ["ADMIN_EMAIL"] = "admin@example.com"
os.environ["ADMIN_PASSWORD"] = "AdminPass123!"
os.environ["PROJECT_GROUP_DATABASE"] = str(ROOT / "test.db")
os.environ["PROJECT_GROUP_UPLOADS"] = str(ROOT / "uploads")
os.environ["COOKIE_SECURE"] = "0"

import app as portal


def run() -> None:
    portal.app.config.update(TESTING=True, SECRET_KEY="smoke-test-secret", SESSION_COOKIE_SECURE=False)
    client = portal.app.test_client()

    def get(path: str):
        response = client.get(path, follow_redirects=True)
        assert response.status_code == 200, (path, response.status_code, response.data[:500])
        return response

    def token() -> str:
        with client.session_transaction() as current_session:
            value = current_session.get("_csrf_token")
            assert value, "CSRF token was not created"
            return value

    def post(path: str, data: dict[str, str]):
        payload = {"csrf_token": token(), **data}
        response = client.post(path, data=payload, follow_redirects=True)
        assert response.status_code == 200, (path, response.status_code, response.data[:700])
        return response

    health = get("/health").get_json()
    assert health == {"status": "ok", "database": "ready", "version": "4.0"}
    assert portal.query_one("SELECT COUNT(*) AS total FROM project_steps")["total"] == 19
    assert portal.query_one("SELECT COUNT(*) AS total FROM certifications")["total"] == 2

    get("/")
    get("/login")
    response = post("/login", {"email": "admin@example.com", "password": "AdminPass123!"})
    assert b"Start with what needs attention" in response.data
    get("/instructor/projects")
    get("/instructor/project/1")

    post("/instructor/manage", {
        "name": "Test Instructor",
        "email": "instructor@example.com",
        "password": "Instructor123!",
    })
    instructor = portal.query_one("SELECT id FROM users WHERE email=?", ("instructor@example.com",))
    assert instructor

    get("/logout")
    get("/register")
    response = post("/register", {
        "name": "Test Student",
        "email": "student@example.com",
        "password": "StudentPass123!",
        "selected_instructor_id": str(instructor["id"]),
        "bootcamp_name": "Batch 33",
        "graduation_date": "2026-07-01",
        "linkedin_url": "https://www.linkedin.com/in/test-student",
    })
    assert b"waiting for approval" in response.data
    student = portal.query_one("SELECT id FROM users WHERE email=?", ("student@example.com",))
    assert student

    get("/logout")
    get("/login")
    post("/login", {"email": "admin@example.com", "password": "AdminPass123!"})
    get("/instructor/approvals")
    post(f"/instructor/student/{student['id']}/decision", {"decision": "approved"})
    assert portal.query_one("SELECT id FROM student_projects WHERE student_id=?", (student["id"],))
    assert portal.query_one("SELECT COUNT(*) AS total FROM student_certifications WHERE student_id=?", (student["id"],))["total"] == 2

    # Update project and certification tracker.
    progress = get(f"/instructor/student/{student['id']}")
    assert b"Project tracker" in progress.data
    project = portal.query_one("SELECT project_id FROM student_projects WHERE student_id=?", (student["id"],))
    post(f"/instructor/student/{student['id']}", {
        "action": "project",
        "project_id": str(project["project_id"]),
        "current_step": "4",
        "project_status": "active",
        "instructor_note": "Continue with the reusable Error Log service.",
    })
    admin_cert = portal.query_one("SELECT id FROM certifications WHERE code='ADMIN'")
    dev_cert = portal.query_one("SELECT id FROM certifications WHERE code='PDI'")
    post(f"/instructor/student/{student['id']}", {
        "action": "certification",
        "certification_id": str(admin_cert["id"]),
        "certification_status": "passed",
        "target_date": "2026-06-10",
        "certification_notes": "Verified by instructor.",
    })
    post(f"/instructor/student/{student['id']}", {
        "action": "certification",
        "certification_id": str(dev_cert["id"]),
        "certification_status": "studying",
        "target_date": "2026-09-01",
        "certification_notes": "Working through Apex and testing topics.",
    })
    tracker = get("/instructor/students?cohort=Batch+33")
    assert b"Passed" in tracker.data and b"Studying" in tracker.data and b">4<" in tracker.data

    get("/logout")
    get("/login")
    response = post("/login", {"email": "student@example.com", "password": "StudentPass123!"})
    assert b"What do you need to do today" in response.data
    assert b"Weekly work" in response.data and b"Project learning" in response.data
    project_page = get("/student/project")
    assert b"HR Management Application" in project_page.data
    source = get(f"/project/{project['project_id']}/source")
    assert len(source.data) > 1000
    assert b"Step 4" in project_page.data or b">4<" in project_page.data
    step_page = get("/student/project/step/4")
    assert b"Reusable Error Log service" in step_page.data
    checklist = get("/student/checklist")
    assert b"Passed" in checklist.data and b"Studying" in checklist.data
    get("/curriculum")
    get("/curriculum/week/1")

    response = post("/student/week/1", {
        "action": "submit",
        "project_story": "I can explain the HR Management Application, its users, and my specific contribution.",
        "requirement_notes": "The core users are HR Managers, Candidates, Interviewers, and administrators.",
        "research_notes": "I reviewed the project brief and official Salesforce documentation.",
        "design_notes": "The solution uses custom objects, junction objects, security, automation, Apex, integrations, and LWC.",
        "presentation_url": "https://example.com/project-evidence",
        "reflection": "I need to make the business outcome more measurable.",
    })
    assert b"Submitted" in response.data or b"submitted" in response.data
    submission = portal.query_one("SELECT id FROM submissions WHERE student_id=? AND week_number=1", (student["id"],))
    assert submission

    get("/logout")
    get("/login")
    post("/login", {"email": "admin@example.com", "password": "AdminPass123!"})
    get("/instructor/reviews")
    response = post(f"/instructor/review/{submission['id']}", {
        "status": "approved",
        "score_business": "18",
        "score_evidence": "17",
        "score_salesforce": "19",
        "score_communication": "18",
        "score_professionalism": "18",
        "strengths": "Clear ownership and project understanding.",
        "revision_actions": "",
        "instructor_feedback": "Add one measurable result to the final story.",
    })
    assert b"90" in response.data

    get("/logout")
    get("/login")
    post("/login", {"email": "student@example.com", "password": "StudentPass123!"})
    dashboard = get("/student")
    assert b"90" in dashboard.data
    week = get("/student/week/1")
    assert b"Clear ownership" in week.data

    print("PASS: portal, project learning, weekly submissions, grading, certifications, and student tracking all work.")


if __name__ == "__main__":
    try:
        run()
    finally:
        shutil.rmtree(ROOT, ignore_errors=True)
