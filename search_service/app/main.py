import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from common.configs.services import SEARCH_SERVICE_NAME
from common.logging.custom_logger import logger
from search_service.app.lifespan.shutdown import disconnect_db
from search_service.app.lifespan.startup import connect_db
from search_service.app.routers import healthcheck, log_level, search

prefix = f"/{SEARCH_SERVICE_NAME.split('_')[0]}"
health_check_interface = None


# ----------------------------
# App Init
# ----------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up the database connection...")
    await connect_db()

    yield
    logger.info("Shutting down the database connection...")
    await disconnect_db()


# ----------------------------
# App
# ----------------------------
app = FastAPI(
    title="Search Service API",
    lifespan=lifespan,
    root_path=f"{prefix}",
    version="1.0.0",
    description="API documentation for the Search Service",
)

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
app.include_router(search.router, tags=["Search"])


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
