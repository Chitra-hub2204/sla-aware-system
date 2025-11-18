import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

class EmailService:
    def __init__(self):
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587

        self.sender_email = os.getenv("SMTP_EMAIL")
        self.sender_password = os.getenv("SMTP_PASSWORD")
        self.recipient_email = os.getenv("SMTP_RECIPIENT")

        print(f"ℹ️ Email configured: server={self.smtp_server}:{self.smtp_port}, "
              f"sender={self.sender_email}, recipient={self.recipient_email}")

    def send_breach_alert(self, service_id, latency, uptime):
        subject = f"SLA BREACH ALERT: {service_id}"
        body = f"SLA breach detected!\n\nLatency={latency}\nUptime={uptime}"
        self._send_email(subject, body)

    def send_restoration_alert(self, service_id, latency, uptime):
        subject = f"SLA RESTORED: {service_id}"
        body = f"SLA restored.\n\nLatency={latency}\nUptime={uptime}"
        self._send_email(subject, body)

    def _send_email(self, subject, body):
        try:
            msg = MIMEMultipart()
            msg["From"] = self.sender_email
            msg["To"] = self.recipient_email
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)

            print(f"✅ Email sent: {subject}")

        except Exception as e:
            print(f"⚠️ Failed to send email: {e}")
