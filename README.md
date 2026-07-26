# Salesforce Project Group v5.2 patch

This patch focuses on 3 things:

1. Better-designed HTML emails for students
2. Fixes for the presentation request screen
3. Weekly homework scheduling with start and due dates

## Files included

- `static/v52-fixes.css`
- `templates/manage_homework.html`
- `templates/manage_week_schedule.html`
- `templates/emails/base.html`
- `templates/emails/homework_assigned.html`
- `templates/emails/weekly_due_set.html`
- `templates/emails/weekly_reviewed.html`
- `templates/emails/homework_reviewed.html`
- `templates/emails/account_approved.html`
- `sql_v52_patch.sql`
- `BACKEND_PATCH_NOTES.md`

## Important

This is a patch pack to apply on top of your current v5 codebase.
The HTML templates and CSS are ready to upload.
The backend notes explain the route, database, and notification additions needed in `app.py` and `seed.py`.
