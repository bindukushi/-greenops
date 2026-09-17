from app.services.email_service import send_alert_email

send_alert_email(
    subject="GreenAI Test Alert",
    message="""
This is a test email from GreenAI.

If you received this email, Gmail SMTP is working correctly.
"""
)