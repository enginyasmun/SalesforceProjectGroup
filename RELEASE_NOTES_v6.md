# Salesforce Project Group v6.0.0

## Release objective

This release converts the previous v5, v5.1, and partial v5.2 patch files into one integrated, production-ready application.

## Major improvements

### Education and coaching

- Establishes the learning loop: **Learn → Build → Prove → Explain → Defend → Improve**.
- Expands the eight-week curriculum with knowledge checks, technical defense questions, quality gates, and interview preparation.
- Expands all 19 Salesforce project steps with required evidence, Definition of Done, and instructor review questions.
- Keeps project implementation and presentation as two separately reviewed weekly requirements.
- Adds professional 100-point grading across business understanding, evidence, Salesforce reasoning, communication, and professionalism.

### Scheduling and assignments

- Fully integrates the eight-week schedule into the database and backend.
- Adds open date, due date, open/closed state, upcoming state, and overdue state.
- Adds instructor-controlled weekly instructions and presentation expectations.
- Corrects all presentation-homework template/backend field mismatches.
- Adds availability dates, due dates, examples, assignment monitoring, revisions, scoring, and notifications.

### Student and instructor experience

- Modern responsive dashboards for students and instructors.
- Cohort, blocker, certification, project-step, weekly score, and homework tracking.
- Student avatars and instructor-scoped access.
- Clear empty states, feedback areas, status badges, and mobile navigation.
- Project and curriculum admin screens remain editable without seeded content overwriting instructor changes.

### Communications

- Branded multipart HTML and plain-text email.
- In-app notification history with email delivery status.
- Designed messages for approval, weekly schedule changes, weekly reviews, homework assignments, and homework reviews.
- Email failure never rolls back a portal action.

### Reliability and security

- Safe migration of the existing SQLite database and persistent uploads.
- CSRF validation on every POST request.
- PBKDF2 password hashing and session hardening.
- Authorized access to uploaded evidence, examples, and custom avatars.
- HTTP/HTTPS URL validation for externally supplied links.
- Security headers, Content Security Policy, HSTS in secure production mode, and no-store caching for authenticated pages.
- SQLite WAL mode and busy timeout.
- GitHub Actions validation and a temporary-database smoke test.

## Compatibility

- Existing production users, submissions, projects, project steps, certifications, uploads, grades, and notifications are retained.
- New tables and columns are added through idempotent migration logic.
- Existing instructor-edited curriculum/project content is preserved.
