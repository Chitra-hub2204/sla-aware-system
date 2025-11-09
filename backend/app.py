from flask import Flask, request, jsonify
from flask_cors import CORS
from models import db, ServiceOrder, MetricRecord, Alert
from config import DATABASE_URL, SCHEDULER_INTERVAL_SECONDS
from monitor import scheduled_generate, generate_metric_for_order
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from waitress import serve
from dotenv import load_dotenv
import os


def create_app():
    app = Flask(__name__)

    # ------------------ Database Config ------------------
    app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)

    # ------------------ Environment Setup ------------------
    load_dotenv()

    # ------------------ CORS Setup ------------------
    CORS(app, resources={
        r"/*": {
            "origins": [
                "https://legendary-frangipane-409a9d.netlify.app",
                "http://localhost:5173"
            ]
        }
    })

    # ------------------ Database Init ------------------
    with app.app_context():
        db.create_all()

    # ------------------ Routes ------------------

    @app.route("/orders", methods=["POST"])
    def create_order():
        """Create a new service order"""
        data = request.get_json()
        required = ["user_name", "service_type", "sla_uptime_pct", "sla_latency_ms"]

        if not data or not all(k in data for k in required):
            return jsonify({"error": "Invalid payload"}), 400

        try:
            o = ServiceOrder(
                user_name=data["user_name"],
                service_type=data["service_type"],
                sla_uptime_pct=float(data["sla_uptime_pct"]),
                sla_latency_ms=float(data["sla_latency_ms"]),
                status="PENDING"
            )
            db.session.add(o)
            db.session.commit()

            # Simulated notification (replaces email)
            print(f"[NOTIFY] New SLA order created by {o.user_name} for {o.service_type}")

            return jsonify({
                "id": o.id,
                "user_name": o.user_name,
                "service_type": o.service_type,
                "sla_uptime_pct": o.sla_uptime_pct,
                "sla_latency_ms": o.sla_latency_ms,
                "status": o.status
            }), 201

        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500

    @app.route("/orders", methods=["GET"])
    def list_orders():
        """List all service orders"""
        orders = ServiceOrder.query.order_by(ServiceOrder.created_at.desc()).all()
        result = [{
            "id": o.id,
            "user_name": o.user_name,
            "service_type": o.service_type,
            "sla_uptime_pct": o.sla_uptime_pct,
            "sla_latency_ms": o.sla_latency_ms,
            "created_at": o.created_at.isoformat(),
            "status": o.status
        } for o in orders]
        return jsonify(result)

    @app.route("/orders/<int:order_id>", methods=["GET"])
    def get_order(order_id):
        """Get order details with metrics and alerts"""
        o = ServiceOrder.query.get_or_404(order_id)
        metrics = MetricRecord.query.filter_by(order_id=o.id).order_by(MetricRecord.timestamp.asc()).all()
        alerts = Alert.query.filter_by(order_id=o.id).order_by(Alert.timestamp.desc()).all()

        return jsonify({
            "id": o.id,
            "user_name": o.user_name,
            "service_type": o.service_type,
            "sla_uptime_pct": o.sla_uptime_pct,
            "sla_latency_ms": o.sla_latency_ms,
            "created_at": o.created_at.isoformat(),
            "status": o.status,
            "metrics": [
                {"timestamp": m.timestamp.isoformat(), "uptime_pct": m.uptime_pct, "latency_ms": m.latency_ms}
                for m in metrics
            ],
            "alerts": [
                {"id": a.id, "timestamp": a.timestamp.isoformat(), "type": a.type, "details": a.details}
                for a in alerts
            ]
        })

    @app.route("/simulate/<int:order_id>", methods=["POST"])
    def simulate(order_id):
        """Simulate metrics for a specific order"""
        o = ServiceOrder.query.get_or_404(order_id)
        body = request.get_json(silent=True) or {}
        deterministic = None

        if "uptime_pct" in body or "latency_ms" in body:
            deterministic = {
                "uptime_pct": body.get("uptime_pct", None),
                "latency_ms": body.get("latency_ms", None)
            }

        m = generate_metric_for_order(o, deterministic=deterministic)

        # Log breach events instead of sending emails
        if m.uptime_pct < o.sla_uptime_pct or m.latency_ms > o.sla_latency_ms:
            print(f"[ALERT] SLA breach detected for {o.service_type} — "
                  f"Uptime: {m.uptime_pct}% | Latency: {m.latency_ms}ms")

        return jsonify({
            "timestamp": m.timestamp.isoformat(),
            "uptime_pct": m.uptime_pct,
            "latency_ms": m.latency_ms
        })

    @app.route("/health")
    def health():
        """Simple health check"""
        return jsonify({"status": "ok", "time": datetime.utcnow().isoformat()})

    # ------------------ Background Scheduler ------------------
    scheduler = BackgroundScheduler()
    scheduler.add_job(lambda: scheduled_generate(app), "interval",
                      seconds=SCHEDULER_INTERVAL_SECONDS,
                      id="metrics_gen", replace_existing=True)
    scheduler.start()

    return app


if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("PORT", 8080))
    serve(app, host="0.0.0.0", port=port)
