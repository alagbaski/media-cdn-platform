# Use a specific version for reproducibility
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Refresh base OS packages to pull in security fixes.
RUN apt-get update && \
    apt-get upgrade -y && \
    rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create a non-root user for security
RUN useradd -m -r appuser && \
    mkdir -p /app/storage/uploads && \
    chown -R appuser:appuser /app

# Copy application code
COPY . .
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose the API port
EXPOSE 8000

# Runtime health probe for container orchestrators and scanners.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import sys,urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health/ready', timeout=3); sys.exit(0)" || exit 1

# Use Gunicorn as the production process manager
CMD ["gunicorn", "-c", "gunicorn_conf.py", "app.main:app"]
