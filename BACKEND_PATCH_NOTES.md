# Backend patch notes for v5.2

## 1. Add a weekly assignment schedule table

Create a table named `weekly_assignments`:

- id
- week_number INTEGER NOT NULL UNIQUE
- title TEXT
- instructions TEXT
- presentation_requirements TEXT
- start_on TEXT
- due_on TEXT
- is_open INTEGER NOT NULL DEFAULT 1
- notify_students INTEGER NOT NULL DEFAULT 1
- updated_by INTEGER
- updated_at TEXT

Use this SQL from `sql_v52_patch.sql`.

## 2. Seed default 8-week records

During `seed.py` or `ensure_schema()`, insert a row for each week 1 through 8 if missing.

Default data:
- title = curriculum week title
- instructions = empty
- presentation_requirements = empty
- start_on = null
- due_on = null
- is_open = 1

## 3. Add helper to send HTML email

Update your mail helper so it can send HTML and plain-text alternatives.

Recommended function signature:

```python
def send_portal_email(to_email, subject, html_body, text_body=""):
    ...
```

Use `email.mime.multipart.MIMEMultipart("alternative")`.
Attach:
- plain text part
- html part

## 4. Render branded HTML email templates

Use Jinja templates for email rendering.

Suggested email render helper:

```python
def render_email(template_name, **context):
    html = render_template(f"emails/{template_name}", **context)
    return html
```

Common email context:
- student_name
- portal_url
- instructor_name
- due_on
- week_number
- title
- topic
- instructions
- requirements
- review_status
- score

## 5. Trigger nice emails for these events

### A. New presentation homework
When instructor creates homework request:
- create in-app notifications
- send `emails/homework_assigned.html` to each assigned student

### B. Weekly start/due date update
When instructor saves the week schedule and `notify_students` is checked:
- create in-app notifications
- send `emails/weekly_due_set.html`

### C. Weekly review/grade saved
When instructor reviews weekly work:
- create in-app notification
- send `emails/weekly_reviewed.html`

### D. Presentation homework review saved
When instructor reviews homework:
- create in-app notification
- send `emails/homework_reviewed.html`

### E. Student approved
When instructor/admin approves account:
- create in-app notification
- send `emails/account_approved.html`

## 6. Add a manage-week-schedule instructor page

Suggested routes:

```python
@app.route("/instructor/weeks", methods=["GET", "POST"])
@instructor_required
def manage_week_schedule():
    ...
```

On GET:
- list all 8 weeks
- display current title, instructions, presentation requirements, start date, due date, open/closed

On POST:
- update the selected week
- optionally notify all approved students in instructor scope

## 7. Student view

In `/student/week/<int:week_number>` load the corresponding `weekly_assignments` row.
Display:
- open date
- due date
- title
- weekly instructions
- presentation requirements
- status badge (Open / Not open / Overdue)

## 8. Add start and due date to review/homework screens

For weekly work:
- show open date and due date

For presentation homework:
- show due date in cards and detail pages
- show an overdue badge if current date is greater than due date and not submitted

## 9. Navigation

Add a new instructor nav item:
- Week schedule

## 10. Notification message examples

Weekly schedule:
- "Week 3 is now open. Due date: Aug 12. Open the portal to see instructions."

Homework assignment:
- "New presentation homework assigned: Explain Flow vs Trigger. Due date: Aug 14."

Review saved:
- "Your Week 2 work was reviewed. Status: Revision. Open feedback in the portal."
