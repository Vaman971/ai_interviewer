"""FastAPI application entrypoint.

Configures middleware, mounts routers, and manages the application lifecycle.
"""

import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.config import get_settings
from backend.app.db.database import create_tables
from backend.app.api.auth import router as auth_router
from backend.app.api.interviews import router as interviews_router
from backend.app.api.media import router as media_router
from backend.app.api.code_execution import router as code_execution_router

logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application startup and shutdown.

    Creates database tables in development and logs lifecycle events.

    Args:
        app: The FastAPI application instance.

    Yields:
        Control back to the framework while the application runs.
    """
    logger.info("Starting %s (env=%s)", settings.app_name, settings.app_env)

    if not settings.is_production:
        await create_tables()
        logger.info("Development tables created")

    yield

    logger.info("Shutting down %s", settings.app_name)


app = FastAPI(
    title=settings.app_name,
    description="AI-powered interview practice platform",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth_router)
app.include_router(interviews_router)
app.include_router(media_router)
app.include_router(code_execution_router)


@app.get("/health")
async def health_check() -> dict:
    """Health-check endpoint for monitoring and load balancing.

    Returns:
        JSON with status, application name, and environment.
    """
    return {
        "status": "healthy",
        "app": settings.app_name,
        "env": settings.app_env,
    }
