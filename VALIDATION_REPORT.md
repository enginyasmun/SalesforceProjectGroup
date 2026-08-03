# Validation report

## Completed checks

- Python compilation for all application, curriculum, project, seed, email-test, and smoke-test modules.
- Jinja syntax validation for all 40 web and email templates.
- Static resolution of every `url_for()` endpoint used by templates.
- Clean creation of the complete SQLite schema.
- Safe seed of one project, 19 project steps, eight weekly assignments, and two certifications.
- Verification that repeated seeding preserves instructor-edited project steps and weekly instructions.
- Route-logic integration test using the real SQL and real form field names for:
  - administrator and instructor creation
  - student registration and approval
  - week scheduling
  - weekly project/presentation submission
  - instructor grading
  - presentation-homework assignment
  - student homework submission
  - instructor homework review
  - notification creation
- Strict rendering validation for every HTML email template.
- Security checks for CSRF coverage, scoped file access, scoped avatar access, external URL validation, CSP compatibility, and authenticated no-store headers.

## Runtime smoke test

`smoke_test.py` is included and is also run by `.github/workflows/ci.yml` after dependencies are installed. It uses a temporary database and never touches production data.

Expected result:

```text
PASS: integrated v6 registration, schedule, weekly work, grading, homework, notifications, tracking, and project learning.
```
