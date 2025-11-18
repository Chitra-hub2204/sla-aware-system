FROM python:3.10-slim
WORKDIR /app

COPY backend ./backend
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8080

# Run the package as a module so "backend" package imports resolve
CMD ["python", "-m", "backend.app"]
