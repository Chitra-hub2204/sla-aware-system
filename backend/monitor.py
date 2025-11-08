import random
from datetime import datetime
from models import ServiceOrder, MetricRecord, Alert, db
from flask_mail import Message
from flask import current_app

# ---- SLA Evaluation Function ----
def evaluate_sla(order: ServiceOrder, recent_metrics):
    """Compare last few metrics against SLA thresholds"""
    if not recent_metrics:
        return "PENDING", None

    breached_reasons = []
    for m in recent_metrics:
        if m.uptime_pct < order.sla_uptime_pct:
            breached_reasons.append(f"uptime {m.uptime_pct}% < {order.sla_uptime_pct}%")
        if m.latency_ms > order.sla_latency_ms:
            breached_reasons.append(f"latency {m.latency_ms}ms > {order.sla_latency_ms}ms")

    if breached_reasons:
        return "BREACHED", "; ".join(breached_reasons)
    return "OK", None


# ---- Metric Generator ----
def generate_metric_for_order(order: ServiceOrder, deterministic=None):
    """
    Generates realistic metrics:
    - 70% chance SLA is met (OK)
    - 30% chance SLA is breached (BAD)
    """

    # Optional: deterministic override (for manual simulate API)
    if deterministic:
        up = deterministic.get("uptime_pct", 99.0)
        lat = deterministic.get("latency_ms", 200)
    else:
        chance = random.random()

        # 🎯 Keep 'Chitra' service always healthy for demo
        if order.user_name.lower() == "chitra":
            up = 99.9
            lat = 200

        # 70% OK, 30% BREACHED
        elif chance < 0.7:
            up = random.uniform(order.sla_uptime_pct + 0.2, 100.0)
            lat = random.uniform(100, order.sla_latency_ms * 0.9)
        else:
            up = random.uniform(order.sla_uptime_pct - 8, order.sla_uptime_pct - 1)
            lat = random.uniform(order.sla_latency_ms * 1.3, order.sla_latency_ms * 2.0)

    # Create a metric record
    m = MetricRecord(
        order_id=order.id,
        uptime_pct=round(up, 2),
        latency_ms=round(lat, 2),
        timestamp=datetime.utcnow()
    )
    db.session.add(m)
    db.session.commit()

    # ---- SLA evaluation based on recent 5 metrics ----
    recent = MetricRecord.query.filter_by(order_id=order.id) \
        .order_by(MetricRecord.timestamp.desc()) \
        .limit(5).all()

    status, reason = evaluate_sla(order, recent)
    prev_status = order.status
    order.status = status
    db.session.commit()

    # ---- Alerts ----
    if status == "BREACHED" and prev_status != "BREACHED":
        alert = Alert(order_id=order.id, type="SLA_BREACH", details=reason)
        db.session.add(alert)
        db.session.commit()

        send_email_alert(alert, order)

    elif status == "OK" and prev_status == "BREACHED":
        alert = Alert(order_id=order.id, type="RECOVERY", details="Service recovered within SLA")
        db.session.add(alert)
        db.session.commit()

        send_email_alert(alert, order)

    return m


# ---- Email Notification Helper ----
def send_email_alert(alert, order):
    """Send SLA alert email notification"""
    try:
        mail = current_app.extensions.get("mail")
        if not mail:
            print("⚠️ Mail extension not initialized.")
            return

        subject = f"SLA Alert: {alert.type} for {order.service_type}"
        body = f"""
SLA Notification

Order ID: {alert.order_id}
User: {order.user_name}
Service: {order.service_type}
Type: {alert.type}
Details: {alert.details}
Time: {alert.timestamp}

Current Status: {order.status}
"""

        msg = Message(
            subject=subject,
            recipients=[current_app.config["MAIL_USERNAME"]],  # send to yourself
            body=body
        )

        mail.send(msg)
        print(f"✅ Email alert sent successfully for Order {order.id} ({alert.type})")
    except Exception as e:
        print(f"⚠️ Failed to send email alert: {e}")


# ---- Scheduler Trigger ----
def scheduled_generate(app):
    """Called automatically by APScheduler every few seconds"""
    with app.app_context():
        orders = ServiceOrder.query.all()
        for o in orders:
            generate_metric_for_order(o)
