# Salesforce Project Group Portal

A separate Flask application for an 8-week post-bootcamp Salesforce interview-readiness program.

## What is included

- Public program and curriculum website
- Student self-registration
- Student selects an instructor during registration
- Pending approval workflow
- Selected instructor or academy administrator can approve the student
- Eight weekly student workspaces
- Draft, submit, revision, and approval statuses
- Instructor review queue and feedback
- Administrator-managed instructor accounts
- One improved project-presentation sample
- One improved research-presentation sample
- SQLite database and secure PBKDF2 password hashing
- CSRF protection and protected uploads

## Local setup

```bash
cd project_group_portal
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export SECRET_KEY='replace-with-a-long-random-value'
export ADMIN_EMAIL='your-admin-email@example.com'
export ADMIN_PASSWORD='replace-this-password'
python seed.py
python app.py
```

Open `http://127.0.0.1:5000`.

## PythonAnywhere deployment

Use a separate PythonAnywhere account for this portal.

### 1. Clone the GitHub repository

```bash
git clone https://github.com/enginyasmun/LearningPortal.git
cd LearningPortal/project_group_portal
```

### 2. Create the virtual environment

```bash
mkvirtualenv --python=/usr/bin/python3.13 projectgroup-env
pip install -r requirements.txt
```

### 3. Set environment variables

Add these near the top of the PythonAnywhere WSGI file before importing the app:

```python
import os
os.environ['SECRET_KEY'] = 'PASTE_A_LONG_RANDOM_SECRET'
os.environ['ADMIN_NAME'] = 'Engin Yasmun'
os.environ['ADMIN_EMAIL'] = 'YOUR_ADMIN_EMAIL'
os.environ['ADMIN_PASSWORD'] = 'YOUR_TEMPORARY_ADMIN_PASSWORD'
os.environ['PROJECT_GROUP_DATABASE'] = '/home/YOUR_USERNAME/project-group-data/project_group.db'
os.environ['PROJECT_GROUP_UPLOADS'] = '/home/YOUR_USERNAME/project-group-data/uploads'
os.environ['COOKIE_SECURE'] = '1'
```

Create the persistent folders:

```bash
mkdir -p /home/YOUR_USERNAME/project-group-data/uploads
```

Initialize the database:

```bash
cd /home/YOUR_USERNAME/LearningPortal/project_group_portal
workon projectgroup-env
python seed.py
```

### 4. Create a Manual Configuration web app

Use the same Python version as the virtual environment. Set the virtualenv path to:

```text
/home/YOUR_USERNAME/.virtualenvs/projectgroup-env
```

Replace the Flask section of the WSGI file with:

```python
import os
import sys

os.environ['SECRET_KEY'] = 'PASTE_A_LONG_RANDOM_SECRET'
os.environ['ADMIN_NAME'] = 'Engin Yasmun'
os.environ['ADMIN_EMAIL'] = 'YOUR_ADMIN_EMAIL'
os.environ['ADMIN_PASSWORD'] = 'YOUR_TEMPORARY_ADMIN_PASSWORD'
os.environ['PROJECT_GROUP_DATABASE'] = '/home/YOUR_USERNAME/project-group-data/project_group.db'
os.environ['PROJECT_GROUP_UPLOADS'] = '/home/YOUR_USERNAME/project-group-data/uploads'
os.environ['COOKIE_SECURE'] = '1'

path = '/home/YOUR_USERNAME/LearningPortal/project_group_portal'
if path not in sys.path:
    sys.path.insert(0, path)

from app import app as application
```

### 5. Static files

On the Web tab add:

- URL: `/static/`
- Directory: `/home/YOUR_USERNAME/LearningPortal/project_group_portal/static/`

Reload the web app.

## Updating from GitHub

```bash
cd /home/YOUR_USERNAME/LearningPortal
git pull origin main
workon projectgroup-env
pip install -r project_group_portal/requirements.txt
python project_group_portal/seed.py
```

Then reload the web app from the PythonAnywhere Web tab.

## Security notes

- Change the bootstrap administrator password immediately after first deployment by replacing the environment variable before sharing the site.
- Use a long random `SECRET_KEY`.
- Keep the database and uploaded files outside the Git checkout.
- Enable HTTPS and set `COOKIE_SECURE=1` in production.
