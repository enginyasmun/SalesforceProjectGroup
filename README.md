# Salesforce Project Group Portal v4

A Flask portal built around two student jobs:

1. Follow the eight-week guide and submit weekly work.
2. Learn the assigned Salesforce project step by step.

## Included

- Student self-registration and instructor approval
- Student home with two primary actions
- Eight-week guided training and weekly submission workflow
- Instructor scoring, feedback, revisions, and review filters
- Project learning library with numbered project steps
- Default HR Management Application with 19 project steps
- Original HR project brief available to assigned students
- Student checklist for project step, Admin certification, Developer certification, and weekly work
- Instructor Batch-style student tracker
- Admin project and project-step management
- Safe SQLite migrations for the existing portal database
- End-to-end smoke test

## PythonAnywhere update

```bash
cd /home/enginproject/SalesforceProjectGroup
git pull origin main
workon projectgroup-env
pip install -r requirements.txt
python -m py_compile app.py curriculum_content.py project_content.py seed.py smoke_test.py
python seed.py
python smoke_test.py
```

Then reload the web app from the PythonAnywhere Web tab.

## Persistent data

Keep the production database and uploads outside the Git checkout:

```text
/home/enginproject/project-group-data/project_group.db
/home/enginproject/project-group-data/uploads
```
