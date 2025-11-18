FROM python:3.10-slim

WORKDIR /app

# Copy backend folder into the image
COPY backend backend

# Copy and install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Required for Python to detect package
ENV PYTHONPATH="/app"

EXPOSE 8080

# Run as module so imports work
CMD ["python", "-m", "backend.app"]
