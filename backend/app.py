import os
from datetime import datetime
import threading

from flask import Flask, jsonify, request, Response
from flask_cors import CORS
from prometheus_client import (
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    CONTENT_TYPE_LATEST,
    generate_latest,
)

from models import db, ServiceOrder, MetricRecord, Alert
from orchestrator import ServiceOrchestrator
from email_service import EmailService


registry = CollectorRegistry()
# Keep default collectors enabled for process metrics

sla_latency = Gauge(
    "sla_latency",
    "Latency target for the requested service",
    ["service_id"],
    registry=registry,
)
sla_latency_histogram = Histogram(
    "sla_latency_histogram",
    "Observed SLA latency distributions",
    ["service_id"],
    registry=registry,
)
service_activation_status = Gauge(
    "service_activation_status",
    "Indicates if the service activation was successful (1) or failed (0)",
    ["service_id"],
    registry=registry,
)
api_request_count = Counter(
    "api_request_count",
    "Total number of API requests received",
    ["endpoint", "method"],
    registry=registry,
)
api_error_count = Counter(
    "api_error_count",
    "Total number of API errors per endpoint",
    ["endpoint", "method"],
    registry=registry,
)
sla_uptime = Gauge(
    "sla_uptime",
    "Uptime percentage for the service",
    ["service_id"],
    registry=registry,
)
sla_breach = Gauge(
    "sla_breach",
    "SLA breach status (1 = breached, 0 = healthy)",
    ["service_id"],
    registry=registry,
)

# Process metrics will be provided by prometheus_client default collectors


def _increment_error_counter():
    api_error_count.labels(endpoint=request.path, method=request.method).inc()


def create_app():
    app = Flask(__name__)

    # CORS for Netlify frontend
    CORS(app, resources={r"/*": {"origins": "*"}})

    database_path = os.path.join(os.path.dirname(__file__), "sla_demo.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{database_path}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)

    orchestrator = ServiceOrchestrator()
    email_service = EmailService()

    with app.app_context():
        db.create_all()
        # Initialize process metrics
        try:
            import psutil
            import time
            process = psutil.Process()
            start_time = time.time()

            def update_process_metrics():
                # Process metrics are handled by prometheus_client default collectors
                # This thread is kept for future custom metrics if needed
                while True:
                    time.sleep(60)

            metric_thread = threading.Thread(target=update_process_metrics, daemon=True)
            metric_thread.start()
        except ImportError:
            print("⚠️ psutil not available, process metrics disabled")

    @app.before_request
    def record_request():
        api_request_count.labels(endpoint=request.path, method=request.method).inc()

    @app.route("/order_service", methods=["POST"])
    def order_service():
        payload = request.get_json(silent=True) or {}
        service_id = payload.get("service_id")
        sla_params = payload.get("sla") or payload.get("sla_params")

        if not service_id or not isinstance(sla_params, dict):
            _increment_error_counter()
            return jsonify({"error": "service_id and sla parameters are required"}), 400

        try:
            print(f"[order_service] Processing service_id={service_id}, payload={sla_params}")
            result = orchestrator.order_service(service_id=service_id, sla_params=sla_params)

            latency_value = float(sla_params.get("latency", 0))
            uptime_value = float(sla_params.get("uptime", 99.0))
            sla_latency.labels(service_id=service_id).set(latency_value)
            sla_latency_histogram.labels(service_id=service_id).observe(latency_value)
            sla_uptime.labels(service_id=service_id).set(uptime_value)
            activation_value = 1 if result.get("status") == "ACTIVATED" else 0
            service_activation_status.labels(service_id=service_id).set(activation_value)

            return jsonify({"service_id": service_id, "details": result}), 201
        except Exception as exc:
            service_activation_status.labels(service_id=service_id).set(0)
            _increment_error_counter()
            return jsonify({"error": str(exc)}), 500


    # ========================================================================
    #  ⭐ THE ONLY CHANGED SECTION — 60% OK, 40% BREACH DEMO LOGIC
    # ========================================================================
    import random
    def check_sla_breach(latency: float, uptime: float) -> bool:
        """
        Mixed-mode SLA evaluation for demo:
        - 60% chance: SLA OK
        - 40% chance: SLA BREACHED
        - But if latency > 700 OR uptime < 95 → ALWAYS BREACH
        """

        # Hard breach (real technical failure)
        if latency > 700 or uptime < 95:
            return True

        # 60% OK, 40% breach
        breach_probability = 0.40
        return random.random() < breach_probability
    # ========================================================================


    def update_order_sla_status(order_id: int, latency: float, uptime: float):
        """Update order status based on SLA breach detection."""
        order = ServiceOrder.query.get(order_id)
        if not order:
            return

        is_breached = check_sla_breach(latency, uptime)
        previous_status = order.status

        if is_breached:
            order.status = "BREACHED"
            sla_breach.labels(service_id=f"order-{order_id}").set(1)
            if previous_status != "BREACHED":
                email_service.send_breach_alert(
                    service_id=f"order-{order_id}",
                    latency=latency,
                    uptime=uptime
                )
                alert = Alert(
                    order_id=order_id,
                    type="SLA_BREACH",
                    details=f"Latency: {latency}ms, Uptime: {uptime}%"
                )
                db.session.add(alert)
        else:
            if previous_status == "BREACHED":
                order.status = "OK"
                sla_breach.labels(service_id=f"order-{order_id}").set(0)
                email_service.send_restoration_alert(
                    service_id=f"order-{order_id}",
                    latency=latency,
                    uptime=uptime
                )
                alert = Alert(
                    order_id=order_id,
                    type="SLA_RESTORED",
                    details=f"Latency: {latency}ms, Uptime: {uptime}%"
                )
                db.session.add(alert)
            else:
                order.status = "OK"
                sla_breach.labels(service_id=f"order-{order_id}").set(0)

        db.session.commit()

    @app.route("/orders", methods=["POST"])
    def create_order():
        data = request.get_json(silent=True) or {}
        required = ["user_name", "service_type", "sla_uptime_pct", "sla_latency_ms"]

        if not all(key in data for key in required):
            _increment_error_counter()
            return jsonify({"error": "Invalid payload"}), 400

        try:
            order = ServiceOrder(
                user_name=data["user_name"],
                service_type=data["service_type"],
                sla_uptime_pct=float(data["sla_uptime_pct"]),
                sla_latency_ms=float(data["sla_latency_ms"]),
                status="PENDING"
            )
            db.session.add(order)
            db.session.commit()

            service_id = f"order-{order.id}"

            try:
                sla_params = {
                    "latency": order.sla_latency_ms,
                    "uptime": order.sla_uptime_pct,
                    "throughput": 1000.0,
                    "jitter": 5.0
                }
                result = orchestrator.order_service(service_id=service_id, sla_params=sla_params)
                print(f"[NETCONF] Service {service_id} activated: {result}")
            except Exception as e:
                print(f"[NETCONF] Activation failed (continuing): {e}")

            latency_value = float(order.sla_latency_ms)
            uptime_value = float(order.sla_uptime_pct)
            sla_latency.labels(service_id=service_id).set(latency_value)
            sla_latency_histogram.labels(service_id=service_id).observe(latency_value)
            sla_uptime.labels(service_id=service_id).set(uptime_value)
            service_activation_status.labels(service_id=service_id).set(1)

            update_order_sla_status(order.id, latency_value, uptime_value)

            return jsonify({
                "id": order.id,
                "user_name": order.user_name,
                "service_type": order.service_type,
                "sla_uptime_pct": order.sla_uptime_pct,
                "sla_latency_ms": order.sla_latency_ms,
                "status": order.status
            }), 201
        except Exception as exc:
            db.session.rollback()
            _increment_error_counter()
            return jsonify({"error": str(exc)}), 500

    @app.route("/orders", methods=["GET"])
    def list_orders():
        orders = ServiceOrder.query.order_by(ServiceOrder.created_at.desc()).all()
        return jsonify([
            {
                "id": order.id,
                "user_name": order.user_name,
                "service_type": order.service_type,
                "sla_uptime_pct": order.sla_uptime_pct,
                "sla_latency_ms": order.sla_latency_ms,
                "created_at": order.created_at.isoformat(),
                "status": order.status
            }
            for order in orders
        ])

    @app.route("/orders/<int:order_id>", methods=["GET"])
    def get_order(order_id):
        order = ServiceOrder.query.get_or_404(order_id)
        metrics = MetricRecord.query.filter_by(order_id=order.id).order_by(MetricRecord.timestamp.asc()).all()
        alerts = Alert.query.filter_by(order_id=order.id).order_by(Alert.timestamp.desc()).all()

        return jsonify({
            "id": order.id,
            "user_name": order.user_name,
            "service_type": order.service_type,
            "sla_uptime_pct": order.sla_uptime_pct,
            "sla_latency_ms": order.sla_latency_ms,
            "created_at": order.created_at.isoformat(),
            "status": order.status,
            "metrics": [
                {"timestamp": metric.timestamp.isoformat(), "uptime_pct": metric.uptime_pct, "latency_ms": metric.latency_ms}
                for metric in metrics
            ],
            "alerts": [
                {"id": alert.id, "timestamp": alert.timestamp.isoformat(), "type": alert.type, "details": alert.details}
                for alert in alerts
            ]
        })

    @app.route("/metrics", methods=["GET"])
    def metrics():
        from prometheus_client import REGISTRY as DEFAULT_REGISTRY
        
        custom_metrics = generate_latest(registry)
        default_metrics = generate_latest(DEFAULT_REGISTRY)
        
        combined = custom_metrics + b"\n" + default_metrics
        return Response(combined, mimetype=CONTENT_TYPE_LATEST)

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok", "time": datetime.utcnow().isoformat()})

    return app


if __name__ == "__main__":
    application = create_app()
    port = int(os.getenv("PORT", 8080))
    application.run(host="0.0.0.0", port=port)

