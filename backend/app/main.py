from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, ORJSONResponse

from .api.router import api_router
from .core.config import settings
from .core.logging import configure_logging, get_logger
from .core.middleware import CorrelationIdMiddleware


def _build_lifespan(*, initialize_storage: bool):
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Application startup/shutdown lifecycle hooks."""
        logger = get_logger(__name__)

        if initialize_storage:
            try:
                from .services.storage import StorageService

                storage = StorageService.from_settings(settings)
                storage.create_bucket_if_missing()
                app.state.storage = storage
                logger.info("MinIO storage service initialized (bucket=%s)", storage.bucket_name)
            except Exception as exc:
                app.state.storage = None
                logger.warning("MinIO storage unavailable, running without storage: %s", exc)
        else:
            app.state.storage = None
            logger.info("Storage bootstrap disabled for this app instance")

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

    app.add_middleware(CorrelationIdMiddleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix=settings.api_prefix)
    return app


app = create_app()
