# Salesforce Project Group Portal v6.0

A professional Flask portal for Salesforce bootcamp graduates and instructors.

## Educational model

Every week follows the same professional learning loop:

**Learn → Build → Prove → Explain → Defend → Improve**

Students complete two required weekly deliverables:

1. Salesforce project implementation evidence
2. A technical presentation that the student can defend

Instructors approve both requirements separately and apply a 100-point rubric covering business understanding, evidence, Salesforce reasoning, communication, and professionalism.

## Included workflows

- Student registration and instructor approval
- Instructor-scoped student access
- Eight-week graduate curriculum
- Nineteen-step HR Management Salesforce project
- Project tasks, evidence, Definition of Done, and technical review questions
- Weekly open dates, due dates, instructions, and overdue status
- Project evidence and presentation submission
- Separate review of both weekly requirements
- Instructor-created presentation homework
- Designed HTML email plus in-app notifications
- Project, certification, blocker, cohort, and score tracking
- Admin project and instructor management
- Secure file authorization, CSRF protection, password hashing, and security headers
- Safe SQLite migration of the existing production database
- GitHub Actions validation and end-to-end smoke testing

## Persistent production data

Keep production data outside the Git checkout:

```text
/home/enginproject/project-group-data/project_group.db
/home/enginproject/project-group-data/uploads
/home/enginproject/project-group-data/avatars
```

The update process never replaces these folders.

## Local validation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export SECRET_KEY="local-development-secret"
export ADMIN_EMAIL="admin@example.com"
export ADMIN_PASSWORD="A-Strong-Admin-Password"
export COOKIE_SECURE="0"
python seed.py
python smoke_test.py
python app.py
```

Open `http://127.0.0.1:5000`.

## Production deployment

Read [DEPLOY_PYTHONANYWHERE.md](DEPLOY_PYTHONANYWHERE.md) before replacing the current code.
