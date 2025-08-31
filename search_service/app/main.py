import asyncio
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

# Setup custom logging (same standard as workflow service)
from common.logging.custom_logger import logger

from search_service.app.lifespan.shutdown import disconnect_db
from search_service.app.lifespan.startup import connect_db
from search_service.app.routers import (
    healthcheck,
    log_level,
    search,
)

prefix = "search"
health_check_interface = None  # Simplified - no external health check interface


# ----------------------------
# App Init
# ----------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up the database connection...")
    await connect_db()

    # Simplified lifespan without external health checks
    yield
    logger.info("Shutting down the database connection...")
    await disconnect_db()


# ----------------------------
# App
# ----------------------------
app = FastAPI(
    title="Search Service API",
    lifespan=lifespan,
    version="1.0.0",
    description="API documentation for the Search Service - Multi-collection MongoDB search capabilities",
)

# Add CORS middleware
# Allow all origins for development (you can restrict this later)
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",") if os.getenv("CORS_ORIGINS") != "*" else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False if "*" in CORS_ORIGINS else True,  # Disable credentials when allowing all origins
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# We follow the convention of using plural nouns like `/searches` in the API endpoints.

# ----------------------------
# Healthcheck
# ----------------------------
app.include_router(healthcheck.router, tags=["Health"])

# ----------------------------
# Log Level Update
# ----------------------------
app.include_router(log_level.router, tags=["Logging"])

# -----------------------------
# Endpoints for Search
# -----------------------------
app.include_router(search.router, prefix="/searches", tags=["Search"])


# ----------------------------
# Exception Handlers
# ----------------------------
@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        return JSONResponse(
            status_code=404,
            content={"message": "Sorry! We haven't found this route or not implemented yet!"},
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail},
    )
