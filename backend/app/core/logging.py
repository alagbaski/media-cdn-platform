"""Logging configuration utilities."""
import logging
import sys

from pythonjsonlogger import jsonlogger

from .middleware import request_id_ctx


class RequestCorrelationFilter(logging.Filter):
    """Logging filter to inject the current request ID into log records."""

    def filter(self, record):
        record.request_id = request_id_ctx.get()
        return True


def configure_logging(level: str = "INFO", json_format: bool = False) -> None:
    """Configure root logging once for the application."""
    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(RequestCorrelationFilter())

    if json_format:
        formatter = jsonlogger.JsonFormatter(
            "%(asctime)s %(levelname)s %(name)s %(message)s %(request_id)s"
        )
    else:
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(request_id)s | %(message)s"
        )

    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # Remove existing handlers to avoid duplicates
    for h in root_logger.handlers[:]:
        root_logger.removeHandler(h)
    
    root_logger.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """Return a module-level logger."""
    return logging.getLogger(name)
