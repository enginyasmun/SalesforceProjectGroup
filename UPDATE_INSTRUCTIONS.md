# Update existing PythonAnywhere deployment to v5

## 1. Back up the database

```bash
cp /home/enginproject/project-group-data/project_group.db \
   /home/enginproject/project-group-data/project_group-backup-before-v5.db
```

## 2. Pull the GitHub update

```bash
cd /home/enginproject/SalesforceProjectGroup
git pull origin main
workon projectgroup-env
pip install -r requirements.txt
mkdir -p /home/enginproject/project-group-data/uploads
mkdir -p /home/enginproject/project-group-data/avatars
python -m py_compile app.py curriculum_content.py project_content.py seed.py smoke_test.py email_test.py
python seed.py
python smoke_test.py
```

## 3. Update the WSGI file

Add:

```python
os.environ["PROJECT_GROUP_AVATARS"] = "/home/enginproject/project-group-data/avatars"
os.environ["APP_BASE_URL"] = "https://enginproject.pythonanywhere.com"
```

To enable Gmail email alerts, also add:

```python
os.environ["EMAIL_ENABLED"] = "1"
os.environ["SMTP_HOST"] = "smtp.gmail.com"
os.environ["SMTP_PORT"] = "587"
os.environ["SMTP_USE_TLS"] = "1"
os.environ["SMTP_USERNAME"] = "YOUR_GMAIL_ADDRESS"
os.environ["SMTP_PASSWORD"] = "YOUR_16_CHARACTER_GOOGLE_APP_PASSWORD"
os.environ["EMAIL_FROM"] = "YOUR_GMAIL_ADDRESS"
```

Reload the web app after saving the WSGI file.

## 4. Verify

Open:

```text
https://enginproject.pythonanywhere.com/health
```

Expected version: `5.0`.
