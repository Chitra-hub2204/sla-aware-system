from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class ServiceOrder(db.Model):
    __tablename__ = "service_orders"
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(120), nullable=False)
    service_type = db.Column(db.String(80), nullable=False)
    sla_uptime_pct = db.Column(db.Float, nullable=False, default=99.0)
    sla_latency_ms = db.Column(db.Float, nullable=False, default=500)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(32), default="PENDING")  # PENDING, OK, DEGRADED, BREACHED

    metrics = db.relationship("MetricRecord", backref="order", lazy="dynamic", cascade="all, delete-orphan")
    alerts = db.relationship("Alert", backref="order", lazy="dynamic", cascade="all, delete-orphan")

class MetricRecord(db.Model):
    __tablename__ = "metric_records"
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("service_orders.id"), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    uptime_pct = db.Column(db.Float, nullable=False)
    latency_ms = db.Column(db.Float, nullable=False)

class Alert(db.Model):
    __tablename__ = "alerts"
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("service_orders.id"), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    type = db.Column(db.String(80), nullable=False)  # e.g., "SLA_BREACH", "RECOVERY"
    details = db.Column(db.String(400))
