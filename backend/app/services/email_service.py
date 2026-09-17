import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from dotenv import load_dotenv

load_dotenv()


def send_alert_email(subject: str, message: str) -> bool:

    sender_email = os.getenv("GMAIL_SENDER")
    app_password = os.getenv("GMAIL_APP_PASSWORD")
    receiver_email = os.getenv("ALERT_RECEIVER")

    print("\n========== EMAIL ALERT ==========")
    print("Sender:", sender_email)
    print("Receiver:", receiver_email)

    if not sender_email:
        print("❌ GMAIL_SENDER is missing")
        return False

    if not app_password:
        print("❌ GMAIL_APP_PASSWORD is missing")
        return False

    if not receiver_email:
        print("❌ ALERT_RECEIVER is missing")
        return False

    email = MIMEMultipart()
    email["From"] = sender_email
    email["To"] = receiver_email
    email["Subject"] = subject

    email.attach(MIMEText(message, "plain"))

    try:
        print("Connecting to Gmail SMTP...")

        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:

            print("Starting TLS...")
            server.starttls()

            print("Logging into Gmail...")
            server.login(sender_email, app_password)

            print("Sending email...")
            server.sendmail(
                sender_email,
                receiver_email,
                email.as_string()
            )

        print("✅ ALERT EMAIL SENT SUCCESSFULLY")
        print("================================\n")

        return True

    except smtplib.SMTPAuthenticationError as e:
        print("❌ Gmail authentication failed.")
        print("Check that:")
        print("1. Gmail address is correct")
        print("2. 2-Step Verification is enabled")
        print("3. Gmail App Password is correct")
        print("4. The App Password was not revoked")
        print("Error:", e)
        return False

    except smtplib.SMTPException as e:
        print("❌ Gmail SMTP error:")
        print(e)
        return False

    except Exception as e:
        print("❌ Unexpected email error:")
        print(type(e).__name__, e)
        return False