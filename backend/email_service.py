import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class EmailService:
    """Email service for sending SLA breach and restoration alerts via Gmail SMTP."""

    def __init__(self):
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587

        # 🔥 Load from environment instead of hardcoding
        self.sender_email = os.getenv("EMAIL_SENDER")
        self.sender_password = os.getenv("EMAIL_PASSWORD")
        self.recipient_email = os.getenv("EMAIL_RECIPIENT")

    def send_breach_alert(self, service_id: str, latency: float, uptime: float):
        subject = f"SLA Breach Alert: {service_id}"
        body = f"""Service {service_id} has breached SLA.
Latency: {latency} ms
Uptime: {uptime} %
"""
        self._send_email(subject, body)

    def send_restoration_alert(self, service_id: str, latency: float, uptime: float):
        subject = f"SLA Restored: {service_id}"
        body = f"""Service {service_id} is healthy again.
Latency: {latency} ms
Uptime: {uptime} %
"""
        self._send_email(subject, body)

    def _send_email(self, subject: str, body: str):
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
