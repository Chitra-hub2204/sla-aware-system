import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os


class EmailService:
    """Email service for sending SLA breach and restoration alerts."""

    def _init_(self):
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587

        # Read from environment variables (Railway → Variables)
        self.sender_email = os.getenv("EMAIL_USER")
        self.sender_password = os.getenv("EMAIL_PASS")
        self.recipient_email = os.getenv("EMAIL_TO")

        if not all([self.sender_email, self.sender_password, self.recipient_email]):
            print("⚠ Email service NOT configured: missing environment variables")

    def send_breach_alert(self, service_id: str, latency: float, uptime: float):
        subject = f"SLA Breach Alert: {service_id}"
        body = f"""SLA BREACH DETECTED!

Service: {service_id}
Latency: {latency} ms
Uptime: {uptime} %
"""
        self._send_email(subject, body)

    def send_restoration_alert(self, service_id: str, latency: float, uptime: float):
        subject = f"SLA Restored: {service_id}"
        body = f"""SLA RESTORED ✔

Service: {service_id}
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

            print(f"✅ Email Sent: {subject}")

        except Exception as e:
            print(f"⚠ Email sending failed: {e}")