# Modern Simple Design Update v3.1

This package is a complete repository replacement for the application code. It does not include the production SQLite database.

## 1. Back up the PythonAnywhere database

In a PythonAnywhere Bash console:

```bash
cp /home/enginproject/project-group-data/project_group.db \
   /home/enginproject/project-group-data/project_group-backup-before-v3.db
```

## 2. Upload the package contents to GitHub

Upload the files and folders inside this package to the root of:

```text
enginyasmun/SalesforceProjectGroup
```

Commit message:

```text
Simplify portal and add modern learning workflow
```

## 3. Pull on PythonAnywhere

```bash
cd /home/enginproject/SalesforceProjectGroup
git pull origin main
workon projectgroup-env
pip install -r requirements.txt
python -m py_compile app.py curriculum_content.py smoke_test.py
python seed.py
python smoke_test.py
```

Expected smoke-test result:

```text
PASS: registration, approval, curriculum, submission, grading, feedback, and progress all work.
```

## 4. Reload

Open the PythonAnywhere **Web** tab and click **Reload**.

## 5. Verify

```text
https://enginproject.pythonanywhere.com/health
```

Expected:

```json
{"database":"ready","status":"ok","version":"3.0"}
```
