# Use official Python image as base
FROM python:3.12-slim

# Install system dependencies required by psycopg2-binary, Chromium and others
RUN apt-get update && \
    apt-get install -y \
        build-essential \
        libpq-dev \
        chromium \
        wget \
        unzip \
        libnss3 \
        libgconf-2-4 \
        libatk-bridge2.0-0 \
        libgtk-3-0 \
        libxss1 \
        libasound2 \
        libx11-xcb1 \
        libxtst6 \
        libxrandr2 \
        libpangocairo-1.0-0 \
        fonts-liberation \
        libappindicator3-1 \
        xdg-utils && \
    rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy requirements first for caching
COPY requirements.txt .

# Install Python dependencies with verbose logging
RUN pip install --no-cache-dir -r requirements.txt --verbose

# Copy app source code
COPY . .

# Expose port Railway expects
EXPOSE 8000

# Set environment variable for Chromium path so Selenium can find it
ENV CHROMIUM_PATH=/usr/bin/chromium

# Start the app with gunicorn
CMD ["gunicorn", "FlaskAPI:app", "--bind", "0.0.0.0:8000"]
