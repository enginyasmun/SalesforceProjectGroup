"""Send one designed test email using the configured SMTP environment."""

import sys

import app as portal

recipient = sys.argv[1] if len(sys.argv) > 1 else portal.os.environ.get("SMTP_USERNAME", "")
if not recipient:
    raise SystemExit("Usage: python email_test.py recipient@example.com")

with portal.app.app_context():
    html = portal.render_email(
        "notification",
        student_name="Email Test",
        title="Project Group email test",
        message="The designed HTML email configuration is working.",
        portal_url=portal.absolute_portal_url("/login"),
    )
    status, error = portal.send_portal_email(
        recipient,
        "Project Group email test",
        html,
        "The designed HTML email configuration is working.",
    )
print(f"status={status}")
if error:
    print(f"error={error}")
if status != "sent":
    raise SystemExit(1)
