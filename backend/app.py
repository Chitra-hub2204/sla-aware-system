import os
import random
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

# FIXED IMPORTS (absolute package imports)
from backend.models import db, ServiceOrder, MetricRecord, Alert
from backend.orchestrator import ServiceOrchestrator
from backend.email_service import EmailService


# ============================================================================
# PROMETHEUS METRICS REGISTRY
# ============================================================================
registry = CollectorRegistry()

sla_latency = Gauge(
    "sla_latency", "Latency target for the requested service",
    ["service_id"], registry=registry
)

sla_latency_histogram = Histogram(
    "sla_latency_histogram", "Observed SLA latency distributions",
    ["service_id"], registry=registry
)

service_activation_status = Gauge(
    "service_activation_status",
    "Indicates if the service activation was successful (1) or failed (0)",
    ["service_id"], registry=registry
)

api_request_count = Counter(
    "api_request_count",
    "Total number of API requests received",
    ["endpoint", "method"], registry=registry
)

api_error_count = Counter(
    "api_error_count",
    "Total number of API errors per endpoint",
    ["endpoint", "method"], registry=registry
)

sla_uptime = Gauge(
    "sla_uptime",
    "Uptime percentage for the service",
    ["service_id"], registry=registry
)

sla_breach = Gauge(
    "sla_breach",
    "SLA breach status (1 = breached, 0 = healthy)",
    ["service_id"], registry=registry
)


def _increment_error_counter():
    api_error_count.labels(endpoint=request.path, method=request.method).inc()


# ============================================================================
# APPLICATION FACTORY
# ============================================================================
def create_app():
    app = Flask(__name__)
    CORS(app, resources={r"/*": {"origins": "*"}})

    # DB Configuration
    database_path = os.path.join(os.path.dirname(__file__), "sla_demo.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{database_path}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)

    orchestrator = ServiceOrchestrator()
    email_service = EmailService()

    # Init DB + metrics thread
    with app.app_context():
        db.create_all()
        try:
            import psutil
            import time

            def update_process_metrics():
                while True:
                    time.sleep(60)

            threading.Thread(target=update_process_metrics, daemon=True).start()

        except ImportError:
            print("⚠️ psutil not available — process metrics disabled")


    # Track every request
    @app.before_request
    def record_request():
        api_request_count.labels(endpoint=request.path, method=request.method).inc()


    # ============================================================================
    #  /order_service  (Your NETCONF mock — unchanged)
    # ============================================================================
    @app.route("/order_service", methods=["POST"])
    def order_service():
        payload = request.get_json(silent=True) or {}
        service_id = payload.get("service_id")
        sla_params = payload.get("sla") or payload.get("sla_params")

        if not service_id or not isinstance(sla_params, dict):
            _increment_error_counter()
            return jsonify({"error": "service_id and sla parameters are required"}), 400

        try:
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


    # ============================================================================
    #  ⭐ MIXED-MODE BREACH SYSTEM (60% OK / 40% BREACHED)
    # ============================================================================
    def check_sla_breach(latency, uptime):
        # Hard failures (always breach)
        if latency > 700 or uptime < 95:
            return True
        # 40% chance of breach
        import random
        return random.random() < 0.40


    # ============================================================================
    #  Update order status + send email alerts
    # ============================================================================
    def update_order_sla_status(order_id: int, latency: float, uptime: float):
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
                db.session.add(Alert(
                    order_id=order_id,
                    type="SLA_BREACH",
                    details=f"Latency: {latency}ms, Uptime: {uptime}%"
                ))

        else:
            order.status = "OK"
            sla_breach.labels(service_id=f"order-{order_id}").set(0)

            if previous_status == "BREACHED":
                email_service.send_restoration_alert(
                    service_id=f"order-{order_id}",
                    latency=latency,
                    uptime=uptime
                )
                db.session.add(Alert(
                    order_id=order_id,
                    type="SLA_RESTORED",
                    details=f"Latency: {latency}ms, Uptime: {uptime}%"
                ))

        db.session.commit()


    # ============================================================================
    #  CREATE ORDER  (frontend order creation)
    # ============================================================================
    @app.route("/orders", methods=["POST"])
    def create_order():
        data = request.get_json(silent=True) or {}
        required = ["user_name", "service_type", "sla_uptime_pct", "sla_latency_ms"]

        if not all(k in data for k in required):
            _increment_error_counter()
            return jsonify({"error": "Invalid payload"}), 400

        try:
            # Insert order
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

            # Activate service (NETCONF)
            try:
                sla_params = {
                    "latency": order.sla_latency_ms,
                    "uptime": order.sla_uptime_pct,
                    "throughput": 1000.0,
                    "jitter": 5.0
                }
                orchestrator.order_service(service_id=service_id, sla_params=sla_params)
            except Exception as e:
                print(f"[NETCONF] Activation failed (ignored): {e}")

            # Push metrics
            latency_value = order.sla_latency_ms
            uptime_value = order.sla_uptime_pct

            sla_latency.labels(service_id=service_id).set(latency_value)
            sla_latency_histogram.labels(service_id=service_id).observe(latency_value)
            sla_uptime.labels(service_id=service_id).set(uptime_value)
            service_activation_status.labels(service_id=service_id).set(1)

            # Run SLA evaluation + email alerts
            import random
            # Apply probabilistic simulation
            if random.random() < 0.40:
                latency_value = random.uniform(650, 1000)
                uptime_value = random.uniform(90, 97)

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


    # ============================================================================
    #  LIST ORDERS
    # ============================================================================
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


    # ============================================================================
    #  GET ORDER DETAILS
    # ============================================================================
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
                {"timestamp": m.timestamp.isoformat(), "uptime_pct": m.uptime_pct, "latency_ms": m.latency_ms}
                for m in metrics
            ],
            "alerts": [
                {"id": a.id, "timestamp": a.timestamp.isoformat(), "type": a.type, "details": a.details}
                for a in alerts
            ]
        })


    # ============================================================================
    #  PROMETHEUS MERGED METRICS ENDPOINT
    # ============================================================================
    @app.route("/metrics", methods=["GET"])
    def metrics():
        from prometheus_client import REGISTRY as DEFAULT_REGISTRY

        custom_metrics = generate_latest(registry)
        default_metrics = generate_latest(DEFAULT_REGISTRY)

        return Response(custom_metrics + b"\n" + default_metrics, mimetype=CONTENT_TYPE_LATEST)


    # ============================================================================
    #  HEALTH CHECK
    # ============================================================================
    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok", "time": datetime.utcnow().isoformat()})


    return app



# ============================================================================
#  ENTRYPOINT
# ============================================================================
if __name__ == "__main__":
    application = create_app()
    port = int(os.getenv("PORT", 8080))
    application.run(host="0.0.0.0", port=port)
