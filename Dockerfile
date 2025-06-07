# Use official Python image as base
FROM python:3.12-slim

# Install system dependencies required by psycopg2-binary and others
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy requirements first for caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy app source code
COPY . .

# Expose port Railway expects
EXPOSE 8000

# Start the app with gunicorn
CMD ["gunicorn", "FlaskAPI:app", "--bind", "0.0.0.0:8000"]
