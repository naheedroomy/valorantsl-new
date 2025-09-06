# Use Python 3.11 slim image for minimal footprint
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for Python packages
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        libc6-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy the updater source code
COPY . .

# Create logs directory first
RUN mkdir -p logs

# Create non-root user for security
RUN groupadd -r updater && useradd -r -g updater updater \
    && chown -R updater:updater /app

# Switch to non-root user
USER updater

# Set Python path and Docker flag
ENV PYTHONPATH=/app
ENV DOCKER_CONTAINER=true

# Health check to ensure the updater is running
HEALTHCHECK --interval=5m --timeout=30s --start-period=30s --retries=3 \
    CMD python -c "import os; print('Updater is running')" || exit 1

# Default command - run the updater service
CMD ["python", "main.py"]