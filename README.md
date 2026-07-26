# Salesforce Project Group Portal v5

A Flask portal for Salesforce bootcamp graduates. Students use it to complete project steps, create weekly presentations, submit presentation homework, receive instructor grading, and track certifications.

## Main workflows

### Weekly work
Every week has two required deliverables:

1. Complete the assigned project step and submit evidence.
2. Create and upload a presentation about the week's topic.

The instructor reviews both requirements separately, provides separate comments, applies the 100-point rubric, and approves or returns the week for revision.

### Presentation homework
Instructors can create presentation requests, assign one or many students, add a due date, attach an example deck, and provide exact requirements. Students submit PowerPoint, PDF, or a shareable link. The instructor scores, comments, approves, or requests revision.

### Notifications and email
The portal always creates in-app notifications for:

- New presentation homework
- Weekly grading or review
- Presentation-homework grading or review
- Project-step changes
- Certification changes
- Registration decisions

Email is optional and uses Gmail SMTP. Email failure never blocks the portal action.

### Avatars
Students choose a built-in avatar or upload a real PNG, JPG, JPEG, or WebP picture during registration. They can change it later from Account.

## PythonAnywhere persistent folders

```bash
mkdir -p /home/enginproject/project-group-data/uploads
mkdir -p /home/enginproject/project-group-data/avatars
```

Use these WSGI environment paths:

```python
os.environ["PROJECT_GROUP_DATABASE"] = "/home/enginproject/project-group-data/project_group.db"
os.environ["PROJECT_GROUP_UPLOADS"] = "/home/enginproject/project-group-data/uploads"
os.environ["PROJECT_GROUP_AVATARS"] = "/home/enginproject/project-group-data/avatars"
```

## Email setup

For a free PythonAnywhere account, Gmail SMTP is supported. Use a Google App Password, not your normal Gmail password.

Add the values from `pythonanywhere_wsgi.py.example`, then change:

```python
os.environ["EMAIL_ENABLED"] = "1"
```

After reloading, open Account and click **Send test notification**.

## Validation

```bash
python -m py_compile app.py curriculum_content.py project_content.py seed.py smoke_test.py email_test.py
python seed.py
python smoke_test.py
```

Expected result:

```text
PASS: avatars, dual weekly requirements, presentation homework, grading, notifications, and tracking all work.
```
