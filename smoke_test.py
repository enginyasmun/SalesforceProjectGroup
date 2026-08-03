"""End-to-end test using the actual HTML form field contracts.

The test uses a temporary SQLite database and temporary upload folders.
It never touches production data and does not send email.
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

os.environ.update(
    SECRET_KEY="smoke-test-secret",
    ADMIN_NAME="Test Admin",
    ADMIN_EMAIL="admin@example.com",
    ADMIN_PASSWORD="AdminPass123!",
    COOKIE_SECURE="0",
    EMAIL_ENABLED="0",
)

import app as portal


def run() -> None:
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
        root = Path(temp_dir)
        portal.DB_PATH = root / "test.db"
        portal.UPLOAD_DIR = root / "uploads"
        portal.AVATAR_DIR = root / "avatars"
        portal.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        portal.AVATAR_DIR.mkdir(parents=True, exist_ok=True)
        portal._SCHEMA_READY = False
        portal.app.config.update(TESTING=True, SECRET_KEY="smoke-test-secret", SESSION_COOKIE_SECURE=False)
        client = portal.app.test_client()

        def get(path: str):
            response = client.get(path, follow_redirects=True)
            assert response.status_code == 200, (path, response.status_code, response.data[:800])
            return response

        def token() -> str:
            with client.session_transaction() as flask_session:
                value = flask_session.get("_csrf_token")
                assert value, "CSRF token was not created"
                return value

        def post(path: str, data):
            payload = {"csrf_token": token(), **data}
            response = client.post(path, data=payload, follow_redirects=True)
            assert response.status_code == 200, (path, response.status_code, response.data[:1200])
            return response

        health = get("/health").get_json()
        assert health == {"status": "ok", "database": "ready", "version": "6.0.0"}
        assert portal.query_one("SELECT COUNT(*) AS total FROM weekly_assignments")["total"] == 8
        assert portal.query_one("SELECT COUNT(*) AS total FROM project_steps")["total"] == 19

        get("/")
        get("/login")
        response = post("/login", {"email": "admin@example.com", "password": "AdminPass123!"})
        assert b"Assign, review, schedule, and coach" in response.data

        response = post("/instructor/manage", {
            "name": "Test Instructor",
            "email": "instructor@example.com",
            "password": "Instructor123!",
        })
        assert b"Instructor account created" in response.data
        instructor = portal.query_one("SELECT id FROM users WHERE email='instructor@example.com'")
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
            "avatar_preset": "avatar-03.svg",
        })
        assert b"waiting for instructor approval" in response.data.lower()
        student = portal.query_one("SELECT id,avatar_filename FROM users WHERE email='student@example.com'")
        assert student and student["avatar_filename"] == "preset:avatar-03.svg"

        get("/logout")
        post("/login", {"email": "admin@example.com", "password": "AdminPass123!"})
        response = post(f"/instructor/student/{student['id']}/decision", {"decision": "approved"})
        assert b"was approved" in response.data

        response = post("/instructor/weeks", {
            "week_number": "1",
            "title": "Project truth and ownership",
            "start_on": "2026-01-01",
            "due_on": "2026-12-31",
            "instructions": "Complete project Step 1 and identify evidence for every claim.",
            "presentation_requirements": "Five slides and three technical defense questions.",
            "is_open": "1",
            "notify_students": "1",
        })
        assert b"Week 1 schedule saved" in response.data
        schedule = portal.query_one("SELECT * FROM weekly_assignments WHERE week_number=1")
        assert schedule["title"] == "Project truth and ownership" and schedule["due_on"] == "2026-12-31"

        get("/logout")
        post("/login", {"email": "student@example.com", "password": "StudentPass123!"})
        get("/student")
        get("/curriculum")
        get("/curriculum/week/1")
        get("/student/project")
        get("/student/project/step/1")
        get("/student/week/1")
        response = post("/student/week/1", {
            "action": "submit",
            "project_step_number": "1",
            "project_story": "I created and tested the project foundation and security configuration.",
            "requirement_notes": "The design supports HR Managers, Candidates, Interviewers, and least-privilege access.",
            "research_notes": "I reviewed official Salesforce security and relationship guidance.",
            "design_notes": "I documented objects, fields, relationships, sharing, validation, and duplicate controls.",
            "project_evidence_url": "https://example.com/project-evidence",
            "presentation_title": "Week 1 Project Foundation",
            "presentation_summary": "Five slides explaining the problem, users, my work, evidence, and improvements.",
            "presentation_link": "https://example.com/week-1-presentation",
            "reflection": "I need to improve my explanation of relationship tradeoffs.",
        })
        assert b"Both weekly requirements were submitted" in response.data
        submission = portal.query_one("SELECT * FROM submissions WHERE student_id=? AND week_number=1", (student["id"],))
        assert submission and submission["project_step_number"] == 1 and submission["presentation_title"]

        get("/logout")
        post("/login", {"email": "admin@example.com", "password": "AdminPass123!"})
        get("/instructor/reviews")
        response = post(f"/instructor/review/{submission['id']}", {
            "status": "approved",
            "project_review_status": "approved",
            "presentation_review_status": "approved",
            "project_feedback": "The evidence proves the configured project foundation.",
            "presentation_feedback": "The deck has a clear business-to-technical story.",
            "score_business": "18",
            "score_evidence": "18",
            "score_salesforce": "18",
            "score_communication": "18",
            "score_professionalism": "18",
            "strengths": "Clear ownership, security reasoning, and evidence.",
            "revision_actions": "",
            "instructor_feedback": "Add one measurable business result next week.",
        })
        assert b"Grade and feedback saved" in response.data
        reviewed = portal.query_one("SELECT * FROM submissions WHERE id=?", (submission["id"],))
        assert reviewed["total_score"] == 90 and reviewed["status"] == "approved"

        response = post("/instructor/homework", {
            "title": "Defend validation and duplicate rules",
            "topic": "Data quality",
            "instructions": "Explain each rule, its business purpose, and positive and negative test scenarios.",
            "presentation_requirements": "Five to seven slides, evidence, and answers to three follow-up questions.",
            "start_on": "2026-01-01",
            "due_date": "2026-12-31",
            "example_url": "https://example.com/example-deck",
            "student_ids": [str(student["id"])],
        })
        assert b"Assignment progress" in response.data
        homework = portal.query_one("SELECT * FROM homework_requests ORDER BY id DESC LIMIT 1")
        assignment = portal.query_one("SELECT * FROM homework_assignments WHERE request_id=?", (homework["id"],))
        assert homework["presentation_requirements"].startswith("Five to seven")
        assert homework["start_on"] == "2026-01-01" and homework["due_date"] == "2026-12-31"
        assert assignment and assignment["status"] == "assigned"

        get("/logout")
        post("/login", {"email": "student@example.com", "password": "StudentPass123!"})
        get("/student/homework")
        response = post(f"/student/homework/{assignment['id']}", {
            "action": "submit",
            "presentation_title": "Validation and Duplicate Rules",
            "submission_notes": "I explain rule purpose, examples, and test results.",
            "presentation_url": "https://example.com/homework-presentation",
        })
        assert b"Presentation homework submitted" in response.data

        get("/logout")
        post("/login", {"email": "admin@example.com", "password": "AdminPass123!"})
        response = post(f"/instructor/homework/review/{assignment['id']}", {
            "status": "approved",
            "score": "92",
            "instructor_comment": "Strong business examples and clear technical defense.",
        })
        assert b"Homework review saved" in response.data

        get("/instructor/students")
        get(f"/instructor/student/{student['id']}")
        get("/instructor/projects")
        get("/samples")
        get("/notifications")

        notifications = portal.query_all("SELECT * FROM notifications WHERE user_id=?", (student["id"],))
        assert len(notifications) >= 5
        assert all(row["email_status"] == "not_configured" for row in notifications)

    print("PASS: integrated v6 registration, schedule, weekly work, grading, homework, notifications, tracking, and project learning.")


if __name__ == "__main__":
    run()
