# PythonAnywhere deployment

These instructions assume:

- PythonAnywhere username: `enginproject`
- Repository folder: `/home/enginproject/SalesforceProjectGroup`
- Virtual environment: `projectgroup-env`
- Production site: `https://enginproject.pythonanywhere.com`

## Recommended automated deployment

After the v6 files are merged into the GitHub `main` branch:

```bash
cd /home/enginproject/SalesforceProjectGroup
bash deploy_pythonanywhere.sh
```

The script creates consistent backups, pulls `main`, installs dependencies, compiles the project, runs the temporary-database smoke test, and safely migrates production data. Reload the web app from the PythonAnywhere **Web** tab only after the script succeeds.

## Manual deployment

### 1. Back up production data

```bash
mkdir -p /home/enginproject/project-group-backups
STAMP=$(date +%Y%m%d_%H%M%S)

SOURCE_DB=/home/enginproject/project-group-data/project_group.db \
BACKUP_DB=/home/enginproject/project-group-backups/project_group_$STAMP.db \
python - <<'PY'
import os
import sqlite3

source = sqlite3.connect(os.environ["SOURCE_DB"])
target = sqlite3.connect(os.environ["BACKUP_DB"])
try:
    source.backup(target)
finally:
    target.close()
    source.close()
PY

mkdir -p /home/enginproject/project-group-data/uploads
mkdir -p /home/enginproject/project-group-data/avatars

tar -czf /home/enginproject/project-group-backups/files_$STAMP.tar.gz \
  -C /home/enginproject/project-group-data uploads avatars
```

The SQLite backup API is used so the backup remains consistent while WAL mode is enabled.

### 2. Pull the GitHub update

```bash
cd /home/enginproject/SalesforceProjectGroup
git status
git fetch origin
git pull --ff-only origin main
```

### 3. Prepare dependencies

```bash
source /home/enginproject/.virtualenvs/projectgroup-env/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 4. Validate before production migration

```bash
python -m py_compile app.py curriculum_content.py project_content.py seed.py smoke_test.py email_test.py
python smoke_test.py
```

Expected result:

```text
PASS: integrated v6 registration, schedule, weekly work, grading, homework, notifications, tracking, and project learning.
```

### 5. Configure the WSGI environment

Open the PythonAnywhere **Web** tab, open the WSGI configuration file, and use the values in `pythonanywhere_wsgi.py.example`.

Generate a strong secret with:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Do not commit passwords, app passwords, or the secret key to GitHub.

For a brand-new database, export `ADMIN_EMAIL`, `ADMIN_PASSWORD`, and optionally `ADMIN_NAME` in the Bash console before running `seed.py`. An existing production administrator is preserved and does not require resetting the password.

### 6. Migrate the production database

```bash
cd /home/enginproject/SalesforceProjectGroup
source /home/enginproject/.virtualenvs/projectgroup-env/bin/activate
python seed.py
```

Expected output:

```text
Database ready: /home/enginproject/project-group-data/project_group.db
Application version: 6.0.0
```

The migration adds missing tables and columns without deleting existing users, submissions, projects, files, grades, or notifications.

### 7. Reload and verify

Reload the web app from the PythonAnywhere **Web** tab, then run:

```bash
curl -s https://enginproject.pythonanywhere.com/health
```

Expected response:

```json
{"database":"ready","status":"ok","version":"6.0.0"}
```

Verify these browser workflows:

1. Administrator login
2. Instructor dashboard
3. Week schedule
4. Presentation-homework form
5. Student weekly submission
6. Instructor weekly review
7. Notifications
8. Student project-step page

## Optional Gmail email setup

Use a Google App Password, not the normal Gmail password. Set `EMAIL_ENABLED=1` in the WSGI file, reload, and run:

```bash
cd /home/enginproject/SalesforceProjectGroup
source /home/enginproject/.virtualenvs/projectgroup-env/bin/activate
python email_test.py YOUR_EMAIL_ADDRESS
```

Email failure never blocks a portal action. Notification history records the delivery status and any SMTP error.

## Rollback

```bash
cd /home/enginproject/SalesforceProjectGroup
git log --oneline -5
git checkout <PREVIOUS_COMMIT_SHA> -- .
cp /home/enginproject/project-group-backups/project_group_<STAMP>.db \
  /home/enginproject/project-group-data/project_group.db
```

Reload the PythonAnywhere web app after rollback.
