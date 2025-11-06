from flask import Flask, request, jsonify
from flask_cors import CORS
from models import db, ServiceOrder, MetricRecord, Alert
from config import DATABASE_URL, SCHEDULER_INTERVAL_SECONDS
from monitor import scheduled_generate, generate_metric_for_order
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import os

def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    CORS(app)

    with app.app_context():
        db.create_all()

    # Endpoints
    @app.route("/orders", methods=["POST"])
    def create_order():
        data = request.get_json()
        required = ["user_name", "service_type", "sla_uptime_pct", "sla_latency_ms"]
        if not data or not all(k in data for k in required):
            return jsonify({"error": "invalid payload"}), 400
        o = ServiceOrder(
            user_name=data["user_name"],
            service_type=data["service_type"],
            sla_uptime_pct=float(data["sla_uptime_pct"]),
            sla_latency_ms=float(data["sla_latency_ms"]),
            status="PENDING"
        )
        db.session.add(o)
        db.session.commit()
        return jsonify({"id": o.id, "user_name": o.user_name, "service_type": o.service_type,
                        "sla_uptime_pct": o.sla_uptime_pct, "sla_latency_ms": o.sla_latency_ms,
                        "status": o.status}), 201

    @app.route("/orders", methods=["GET"])
    def list_orders():
        orders = ServiceOrder.query.order_by(ServiceOrder.created_at.desc()).all()
        out = []
        for o in orders:
            out.append({
                "id": o.id,
                "user_name": o.user_name,
                "service_type": o.service_type,
                "sla_uptime_pct": o.sla_uptime_pct,
                "sla_latency_ms": o.sla_latency_ms,
                "created_at": o.created_at.isoformat(),
                "status": o.status
            })
        return jsonify(out)

    @app.route("/orders/<int:order_id>", methods=["GET"])
    def get_order(order_id):
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
            "metrics": [{"timestamp": m.timestamp.isoformat(), "uptime_pct": m.uptime_pct, "latency_ms": m.latency_ms} for m in metrics],
            "alerts": [{"id": a.id, "timestamp": a.timestamp.isoformat(), "type": a.type, "details": a.details} for a in alerts]
        })

    @app.route("/simulate/<int:order_id>", methods=["POST"])
    def simulate(order_id):
        o = ServiceOrder.query.get_or_404(order_id)
        # optional deterministic input in JSON to force a breach
        body = request.get_json(silent=True) or {}
        deterministic = None
        if "uptime_pct" in body or "latency_ms" in body:
            deterministic = {
                "uptime_pct": body.get("uptime_pct", None),
                "latency_ms": body.get("latency_ms", None)
            }
        m = generate_metric_for_order(o, deterministic=deterministic)
        return jsonify({"timestamp": m.timestamp.isoformat(), "uptime_pct": m.uptime_pct, "latency_ms": m.latency_ms})

    # start scheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(lambda: scheduled_generate(app), "interval", seconds=SCHEDULER_INTERVAL_SECONDS, id="metrics_gen", replace_existing=True)
    scheduler.start()

    # graceful shutdown hook
    @app.route("/health")
    def health():
        return jsonify({"status": "ok", "time": datetime.utcnow().isoformat()})

    return app

if __name__ == "__main__":
    import os
    app = create_app()
    port = int(os.environ.get("PORT", 5000))
    # debug=False in production
    app.run(host="0.0.0.0", port=port, debug=True)
