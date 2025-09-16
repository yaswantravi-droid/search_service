from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from common.logging.utils import update_dynamic_log_level

router = APIRouter()


@router.get("/update_log_level")
async def update_log_level(request: Request):
    """
    Update the logging level dynamically.
    """
    query = request.query_params
    level = query.get("level", "").lower()
    response = update_dynamic_log_level(level)
    return JSONResponse(status_code=200, content=response)
