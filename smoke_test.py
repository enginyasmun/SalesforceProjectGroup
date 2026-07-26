"""End-to-end smoke test for the Project Group portal.

Run with: python smoke_test.py
The test uses a temporary database and does not touch production data.
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

os.environ.setdefault("SECRET_KEY", "smoke-test-secret")
os.environ.setdefault("ADMIN_NAME", "Test Admin")
os.environ.setdefault("ADMIN_EMAIL", "admin@example.com")
os.environ.setdefault("ADMIN_PASSWORD", "AdminPass123!")
os.environ.setdefault("COOKIE_SECURE", "0")

import app as portal


def run() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        portal.DB_PATH = root / "test.db"
        portal.UPLOAD_DIR = root / "uploads"
        portal.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        portal._SCHEMA_READY = False
        portal.app.config.update(TESTING=True, SECRET_KEY="smoke-test-secret", SESSION_COOKIE_SECURE=False)
        client = portal.app.test_client()

        def get(path: str):
            response = client.get(path, follow_redirects=True)
            assert response.status_code == 200, (path, response.status_code, response.data[:300])
            return response

        def token() -> str:
            with client.session_transaction() as session:
                value = session.get("_csrf_token")
                assert value, "CSRF token was not created"
                return value

        def post(path: str, data: dict[str, str]):
            payload = {"csrf_token": token(), **data}
            response = client.post(path, data=payload, follow_redirects=True)
            assert response.status_code == 200, (path, response.status_code, response.data[:500])
            return response

        health = get("/health").get_json()
        assert health == {"status": "ok", "database": "ready", "version": "3.0"}
        get("/")
        get("/samples")

        get("/login")
        response = post("/login", {"email": "admin@example.com", "password": "AdminPass123!"})
        assert b"Start with what needs attention" in response.data

        get("/instructor/manage")
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
            "bootcamp_name": "Salesforce Bootcamp",
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

        get("/logout")
        get("/login")
        response = post("/login", {"email": "student@example.com", "password": "StudentPass123!"})
        assert b"Build one strong Salesforce story" in response.data
        get("/curriculum")
        get("/student/week/1")
        response = post("/student/week/1", {
            "action": "submit",
            "project_story": "I worked on a structured Salesforce project that solved a clear business problem.",
            "requirement_notes": "Users, scope, constraints, and acceptance criteria.",
            "research_notes": "Official documentation and a comparison of options.",
            "design_notes": "Data model, security, Flow, testing, and deployment.",
            "presentation_url": "https://example.com/presentation",
            "reflection": "I need to make the result more measurable.",
        })
        assert b"Submitted" in response.data or b"submitted" in response.data
        submission = portal.query_one("SELECT id FROM submissions WHERE student_id=? AND week_number=1", (student["id"],))
        assert submission

        get("/logout")
        get("/login")
        post("/login", {"email": "admin@example.com", "password": "AdminPass123!"})
        get("/instructor/reviews")
        get(f"/instructor/review/{submission['id']}")
        response = post(f"/instructor/review/{submission['id']}", {
            "status": "approved",
            "score_business": "18",
            "score_evidence": "17",
            "score_salesforce": "19",
            "score_communication": "18",
            "score_professionalism": "18",
            "strengths": "Clear ownership and Salesforce reasoning.",
            "revision_actions": "",
            "instructor_feedback": "Use one measurable outcome in the final interview answer.",
        })
        assert b"90" in response.data
        get(f"/instructor/student/{student['id']}")

        get("/logout")
        get("/login")
        post("/login", {"email": "student@example.com", "password": "StudentPass123!"})
        dashboard = get("/student")
        assert b"90" in dashboard.data
        week = get("/student/week/1")
        assert b"Clear ownership" in week.data

    print("PASS: registration, approval, curriculum, submission, grading, feedback, and progress all work.")


if __name__ == "__main__":
    run()
