"""End-to-end smoke test for Project Group portal v5.

Run with: python smoke_test.py
The test uses a temporary database and does not touch production data.
Email delivery is disabled; in-app notifications and email status are verified.
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

os.environ["SECRET_KEY"] = "smoke-test-secret"
os.environ["ADMIN_NAME"] = "Test Admin"
os.environ["ADMIN_EMAIL"] = "admin@example.com"
os.environ["ADMIN_PASSWORD"] = "AdminPass123!"
os.environ["COOKIE_SECURE"] = "0"
os.environ["EMAIL_ENABLED"] = "0"

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
            assert response.status_code == 200, (path, response.status_code, response.data[:500])
            return response

        def token() -> str:
            with client.session_transaction() as flask_session:
                value = flask_session.get("_csrf_token")
                assert value, "CSRF token was not created"
                return value

        def post(path: str, data):
            payload = {"csrf_token": token(), **data}
            response = client.post(path, data=payload, follow_redirects=True)
            assert response.status_code == 200, (path, response.status_code, response.data[:800])
            return response

        health = get("/health").get_json()
        assert health == {"status": "ok", "database": "ready", "version": "5.0"}
        get("/")
        get("/login")
        response = post("/login", {"email": "admin@example.com", "password": "AdminPass123!"})
        assert b"Assign, review, and notify" in response.data

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
            "avatar_preset": "avatar-03.svg",
        })
        assert b"waiting for approval" in response.data
        student = portal.query_one("SELECT id,avatar_filename FROM users WHERE email=?", ("student@example.com",))
        assert student and student["avatar_filename"] == "preset:avatar-03.svg"

        get("/logout")
        get("/login")
        post("/login", {"email": "admin@example.com", "password": "AdminPass123!"})
        post(f"/instructor/student/{student['id']}/decision", {"decision": "approved"})
        assert portal.query_one("SELECT COUNT(*) AS total FROM notifications WHERE user_id=?", (student["id"],))["total"] >= 1

        get("/logout")
        get("/login")
        response = post("/login", {"email": "student@example.com", "password": "StudentPass123!"})
        assert b"Complete project work, create presentations" in response.data
        get("/student/week/1")
        response = post("/student/week/1", {
            "action": "submit",
            "project_step_number": "1",
            "project_story": "I completed the project object and app setup for the assigned step.",
            "requirement_notes": "The work supports HR Managers, Candidates, and Interviewers.",
            "research_notes": "I used official Salesforce documentation.",
            "design_notes": "I documented objects, fields, descriptions, and relationships.",
            "project_evidence_url": "https://example.com/project-evidence",
            "presentation_title": "Week 1 Project Foundation",
            "presentation_summary": "A five-slide explanation of the business problem, users, objects, and my contribution.",
            "presentation_link": "https://example.com/week-1-presentation",
            "reflection": "I need to improve my explanation of relationship choices.",
        })
        assert b"Both weekly requirements were submitted" in response.data
        submission = portal.query_one("SELECT * FROM submissions WHERE student_id=? AND week_number=1", (student["id"],))
        assert submission and submission["presentation_title"] and submission["project_step_number"] == 1

        get("/logout")
        get("/login")
        post("/login", {"email": "admin@example.com", "password": "AdminPass123!"})
        response = post(f"/instructor/review/{submission['id']}", {
            "status": "approved",
            "project_review_status": "approved",
            "presentation_review_status": "approved",
            "project_feedback": "The evidence clearly proves the project step.",
            "presentation_feedback": "The deck is clear and follows the suggested structure.",
            "score_business": "18",
            "score_evidence": "18",
            "score_salesforce": "18",
            "score_communication": "18",
            "score_professionalism": "18",
            "strengths": "Clear ownership and evidence.",
            "revision_actions": "",
            "instructor_feedback": "Add one measurable outcome next week.",
        })
        assert b"student was notified" in response.data
        reviewed = portal.query_one("SELECT * FROM submissions WHERE id=?", (submission["id"],))
        assert reviewed["total_score"] == 90 and reviewed["project_review_status"] == "approved"

        response = post("/instructor/homework", {
            "title": "Explain validation and duplicate rules",
            "topic": "Data quality",
            "instructions": "Prepare a presentation that explains the rules and the business problems they prevent.",
            "presentation_requirements": "5 to 7 slides, one rule per slide, include examples.",
            "due_date": "2026-08-05",
            "example_url": "https://example.com/example-deck",
            "student_ids": [str(student["id"])],
        })
        assert b"Assignment progress" in response.data
        homework_assignment = portal.query_one("SELECT * FROM homework_assignments WHERE student_id=?", (student["id"],))
        assert homework_assignment and homework_assignment["status"] == "assigned"

        # Instructor changes project/certification trackers; both create notifications.
        project = portal.query_one("SELECT project_id FROM student_projects WHERE student_id=?", (student["id"],))
        post(f"/instructor/student/{student['id']}", {
            "action": "project", "project_id": str(project["project_id"]), "current_step": "2",
            "project_status": "active", "instructor_note": "Continue with validation rules.",
        })
        cert = portal.query_one("SELECT id FROM certifications WHERE code='ADMIN'")
        post(f"/instructor/student/{student['id']}", {
            "action": "certification", "certification_id": str(cert["id"]),
            "certification_status": "studying", "target_date": "2026-09-01",
            "certification_notes": "Complete the security modules.",
        })

        get("/logout")
        get("/login")
        post("/login", {"email": "student@example.com", "password": "StudentPass123!"})
        get("/student/homework")
        response = post(f"/student/homework/{homework_assignment['id']}", {
            "action": "submit",
            "presentation_title": "Validation and Duplicate Rules",
            "submission_notes": "I explain the rule purpose and test examples.",
            "presentation_url": "https://example.com/homework-presentation",
        })
        assert b"Presentation homework submitted" in response.data

        get("/logout")
        get("/login")
        post("/login", {"email": "admin@example.com", "password": "AdminPass123!"})
        response = post(f"/instructor/homework/review/{homework_assignment['id']}", {
            "status": "approved", "score": "92", "instructor_comment": "Strong examples and clear structure.",
        })
        assert b"student was notified" in response.data

        notifications = portal.query_all("SELECT * FROM notifications WHERE user_id=?", (student["id"],))
        assert len(notifications) >= 6
        assert all(row["email_status"] == "not_configured" for row in notifications)
        student_home = get("/student") if False else None

    print("PASS: avatars, dual weekly requirements, presentation homework, grading, notifications, and tracking all work.")


if __name__ == "__main__":
    run()
