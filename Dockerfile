FROM python:3.10-slim

WORKDIR /app

# Install deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend folder INTO /app/backend
COPY backend backend

# Required for Python to detect package
ENV PYTHONPATH="/app"

EXPOSE 8080

# Run as module so imports work
CMD ["python", "-m", "backend.app"]
