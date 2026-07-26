# Salesforce Project Group Curriculum and Grading Upgrade

This package is additive. It does not delete the existing SQLite database, users, approvals, or submissions.

## Features added

- Eight-week curriculum page
- Full step-by-step study guide for every week
- Learning objectives, tools, checkpoints, evidence requirements, and quality gates
- Student study-step progress saved in the browser
- Student submission and revision tracking
- Five-category grading rubric, 20 points each, total 100
- Strengths, required revisions, and instructor coaching fields
- Review filters by status, student, and week
- Per-student progress page with weekly status and scores
- Automatic additive SQLite migration for the live database

## Replace files in GitHub

Upload this package into the root of `enginyasmun/SalesforceProjectGroup`, preserving the folder structure. Replace existing files when GitHub asks.

Changed existing files:

- `app.py`
- `schema.sql`
- `static/styles.css`
- `templates/base.html`
- `templates/student_dashboard.html`
- `templates/student_week.html`
- `templates/reviews.html`
- `templates/review_submission.html`
- `templates/instructor_students.html`

New files:

- `curriculum_content.py`
- `templates/_week_guide.html`
- `templates/curriculum.html`
- `templates/curriculum_week.html`
- `templates/student_progress.html`

Commit the upload to the `main` branch.

## Update PythonAnywhere

Open a Bash console and run:

```bash
cd /home/enginproject/SalesforceProjectGroup
git status
git pull origin main
workon projectgroup-env
python seed.py
```

Expected database message:

```text
Project Group database is ready.
```

Then open the PythonAnywhere **Web** tab and click **Reload**.

## Validate

Open:

```text
https://enginproject.pythonanywhere.com/health
```

Expected response:

```json
{"database":"ready","status":"ok"}
```

Then verify:

1. Instructor navigation contains **Curriculum**.
2. Curriculum displays all eight weeks.
3. A student week displays guided study steps and a submission form.
4. Instructor Reviews contains filters and numeric grading fields.
5. Student roster contains an **Open progress** link.

## Rollback

Before uploading, GitHub already retains the previous commit. If needed, use GitHub commit history to revert the upgrade commit. The database migration only adds nullable columns and does not remove existing data.
