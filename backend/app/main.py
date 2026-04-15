from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, ORJSONResponse
from fastapi.staticfiles import StaticFiles

from .api.router import api_router
from .core.config import settings
from .core.logging import configure_logging, get_logger
from .core.middleware import CorrelationIdMiddleware
from .services.storage import ensure_storage_dir


def _build_lifespan(*, initialize_storage: bool):
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Application startup/shutdown lifecycle hooks."""
        logger = get_logger(__name__)

        if initialize_storage:
            try:
                ensure_storage_dir()
                logger.info("Local storage service initialized")
            except Exception as exc:
                logger.warning("Local storage unavailable: %s", exc)

        logger.info("Application startup complete")
        yield
        logger.info("Application shutdown complete")

    return lifespan


def create_app(*, initialize_storage: bool = True) -> FastAPI:
    """Application factory."""
    log_level = "DEBUG" if settings.debug or settings.environment == "development" else "INFO"
    configure_logging(level=log_level)

    # Disable docs in production/staging for security
    is_prod = settings.environment in ("production", "staging")
    
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        docs_url=None if is_prod else settings.docs_url,
        redoc_url=None if is_prod else settings.redoc_url,
        openapi_url=None if is_prod else settings.openapi_url,
        default_response_class=ORJSONResponse,
        lifespan=_build_lifespan(initialize_storage=initialize_storage),
    )

    # Global Exception Handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger = get_logger(__name__)
        logger.exception("Unhandled error on %s %s: %s", request.method, request.url.path, str(exc))
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An internal server error occurred."},
        )

    @app.middleware("http")
    async def media_cache_headers_middleware(request: Request, call_next):
        response: Response = await call_next(request)
        if request.url.path.startswith("/media/"):
            response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        return response

    app.add_middleware(CorrelationIdMiddleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    uploads_dir = ensure_storage_dir()
    app.mount("/media", StaticFiles(directory=str(uploads_dir)), name="media")
    app.include_router(api_router, prefix=settings.api_prefix)
    return app


app = create_app()
