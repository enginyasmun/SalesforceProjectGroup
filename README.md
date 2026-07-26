# Salesforce Project Group Portal

A simple, modern Flask learning portal for an 8-week post-bootcamp Salesforce interview-readiness program.

## Main workflows

- Student self-registration and instructor selection
- Instructor or administrator approval
- Eight-week curriculum with guided study steps
- Draft, submit, revision, and approval workflow
- Five-part grading rubric with a score out of 100
- Instructor feedback, required revisions, and strengths
- Per-student progress and average scores
- One Salesforce project presentation example
- One research presentation example

## Technology

- Python and Flask
- SQLite
- Plain HTML, CSS, and JavaScript
- No front-end framework and no build step

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export SECRET_KEY='replace-with-a-long-random-value'
export ADMIN_EMAIL='your-email@example.com'
export ADMIN_PASSWORD='replace-this-password'
python seed.py
python app.py
```

Open `http://127.0.0.1:5000`.

## Validate before deployment

```bash
python -m py_compile app.py curriculum_content.py
python seed.py
python smoke_test.py
```

The smoke test uses a temporary database and does not touch production records.

## Update the existing PythonAnywhere deployment

After the updated files are committed to GitHub:

```bash
cd /home/enginproject/SalesforceProjectGroup
git pull origin main
workon projectgroup-env
pip install -r requirements.txt
python seed.py
python smoke_test.py
```

Then reload the web app from the PythonAnywhere **Web** tab.

The existing WSGI path remains:

```text
/home/enginproject/SalesforceProjectGroup
```

The existing persistent database remains:

```text
/home/enginproject/project-group-data/project_group.db
```

Do not delete or replace the production database. `seed.py` applies additive schema changes safely.

## Health check

Open:

```text
https://enginproject.pythonanywhere.com/health
```

Expected result:

```json
{"database":"ready","status":"ok","version":"3.0"}
```
