"""Middleware for request correlation tracking."""

import uuid
from contextvars import ContextVar
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# Context variable to store the request ID for the current async task
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="")


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """
    Middleware that ensures every request has a unique correlation ID.
    If the client sends X-Request-ID, we use it; otherwise, we generate one.
    The ID is added to response headers for debugging.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check if X-Request-ID is already present (e.g., from Ingress or CDN)
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        
        # Set the context variable for logging
        token = request_id_ctx.set(request_id)
        
        # Add to request state for access in routes
        request.state.request_id = request_id
        
        try:
            # Process the request
            response: Response = await call_next(request)
            
            # Propagate the ID back to the client/caller
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            # Reset the context variable
            request_id_ctx.reset(token)
