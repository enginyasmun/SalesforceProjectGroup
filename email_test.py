"""Test the configured SMTP connection from a Bash console.

Set the same SMTP environment variables used in the WSGI file, then run:
    python email_test.py recipient@example.com
"""
import sys
from app import send_notification_email

recipient = sys.argv[1] if len(sys.argv) > 1 else None
if not recipient:
    raise SystemExit("Usage: python email_test.py recipient@example.com")
status, error = send_notification_email(
    recipient,
    "Salesforce Project Group email test",
    "Email alerts from the Salesforce Project Group portal are working.",
    "/notifications",
)
print(f"status={status}")
if error:
    print(f"error={error}")
if status != "sent":
    raise SystemExit(1)
