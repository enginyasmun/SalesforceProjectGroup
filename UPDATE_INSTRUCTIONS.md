# Update instructions

## 1. Back up the production database

```bash
cp /home/enginproject/project-group-data/project_group.db \
   /home/enginproject/project-group-data/project_group-backup-before-v4.db
```

## 2. Upload the contents of this package to the GitHub repository root

The repository must contain `app.py`, `project_content.py`, `curriculum_content.py`, `templates`, and `static` at the root.

Do not upload a `.db` file or the production uploads folder.

## 3. Pull and validate on PythonAnywhere

```bash
cd /home/enginproject/SalesforceProjectGroup
git pull origin main
workon projectgroup-env
pip install -r requirements.txt
python -m py_compile app.py curriculum_content.py project_content.py seed.py smoke_test.py
python seed.py
python smoke_test.py
```

Expected test result:

```text
PASS: portal, project learning, weekly submissions, grading, certifications, and student tracking all work.
```

## 4. Reload

Open the PythonAnywhere Web tab and click Reload.

Health check:

```text
https://enginproject.pythonanywhere.com/health
```

Expected response:

```json
{"database":"ready","status":"ok","version":"4.0"}
```
