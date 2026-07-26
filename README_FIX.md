# Instructor Dashboard Design Fix v5.1

Replace/add these files in the repository root:

- templates/instructor_dashboard.html
- templates/base.html
- static/dashboard-fix.css

Then on PythonAnywhere:

```bash
cd /home/enginproject/SalesforceProjectGroup
git pull origin main
workon projectgroup-env
python -m py_compile app.py
python smoke_test.py
```

Reload the web app from the PythonAnywhere Web tab.

The base template changes the static asset version from 5.0 to 5.1 to force browsers and PythonAnywhere to load the corrected stylesheet.
