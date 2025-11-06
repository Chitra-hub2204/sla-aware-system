import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATABASE_URL = os.environ.get("DATABASE_URL") or \
               f"sqlite:///{os.path.join(BASE_DIR, 'sla_demo.db')}"
SCHEDULER_INTERVAL_SECONDS = int(os.environ.get("SCHEDULER_INTERVAL_SECONDS", "8"))
# scheduler interval 8s for demo; change to 30+ for real
