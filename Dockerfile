# Use the official lightweight Python image
FROM python:3.10-slim

# Set working directory inside the container
WORKDIR /app

# Copy only backend folder and requirements file
COPY backend/ ./backend/
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 5000 (Flask default)
EXPOSE 5000

# Start the Flask app
CMD ["python", "backend/app.py"]
