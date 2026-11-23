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

    try:
        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = receiver_email
        msg["Subject"] = subject

        msg.attach(MIMEText(message, "plain"))

        print("Connecting to Gmail SMTP...")

        with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
            server.ehlo()

            print("Starting TLS...")
            server.starttls()

            server.ehlo()

            print("Logging into Gmail...")
            server.login(sender_email, app_password.replace(" ", ""))

            print("Sending email...")
            server.sendmail(
                sender_email,
                receiver_email,
                msg.as_string()
            )

        print("✅ Email sent successfully!")
        return True

    except smtplib.SMTPAuthenticationError:
        print("❌ Gmail authentication failed.")
        print("Check that GMAIL_APP_PASSWORD is a valid Gmail App Password.")

    except smtplib.SMTPConnectError as e:
        print("❌ Could not connect to Gmail SMTP:", e)

    except TimeoutError:
        print("❌ Gmail SMTP connection timed out.")

    except Exception as e:
        print("❌ Gmail SMTP error:", e)

    return False