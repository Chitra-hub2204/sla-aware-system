import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os


class EmailService:
    """Email service for sending SLA breach and restoration alerts via Gmail SMTP."""

    def __init__(self):
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.sender_email = "ugcet22055@gmail.com"
        self.sender_password = "rxbfnuvywknvxxoc"
        self.recipient_email = "ugcet22055@gmail.com"

    def send_breach_alert(self, service_id: str, latency: float, uptime: float):
        """Send email alert when SLA is breached."""
        subject = f"SLA Breach Alert: {service_id}"
        body = f"""Service {service_id} has breached SLA.
Latency: {latency} ms
Uptime: {uptime} %
"""
        self._send_email(subject, body)

    def send_restoration_alert(self, service_id: str, latency: float, uptime: float):
        """Send email alert when SLA is restored."""
        subject = f"SLA Restored: {service_id}"
        body = f"""Service {service_id} is healthy again.
Latency: {latency} ms
Uptime: {uptime} %
"""
        self._send_email(subject, body)

    def _send_email(self, subject: str, body: str):
        """Internal method to send email via SMTP."""
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

