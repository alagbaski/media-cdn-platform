import multiprocessing
import os

# Gunicorn configuration for production FastAPI

# IP/Port to bind
host = os.getenv("HOST", "0.0.0.0")
port = os.getenv("PORT", "8000")
bind = f"{host}:{port}"

# Performance tuning: 2 x cores + 1 is the standard formula
cores = multiprocessing.cpu_count()
workers_per_core = float(os.getenv("WORKERS_PER_CORE", "2"))
default_web_concurrency = cores * workers_per_core + 1
workers = int(os.getenv("WEB_CONCURRENCY", default_web_concurrency))

# Worker class must be UvicornWorker for FastAPI
worker_class = "uvicorn.workers.UvicornWorker"

# Timeout and keepalive
timeout = int(os.getenv("TIMEOUT", "120"))
keepalive = int(os.getenv("KEEPALIVE", "5"))

# Logging
accesslog = "-"  # Log to stdout
errorlog = "-"   # Log to stdout
loglevel = os.getenv("LOG_LEVEL", "info")

# Load application before workers forks
# This saves memory by sharing the same address space for read-only data
preload_app = True
