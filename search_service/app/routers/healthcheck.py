from fastapi import APIRouter
from fastapi.responses import JSONResponse

from common.models.response_models import IResponseModel

router = APIRouter()


@router.get("/", response_model=IResponseModel)
async def welcome():
    """
    Welcome endpoint to check if the service is running.
    """
    return JSONResponse(
        status_code=200,
        content={"message": "Welcome to Search Service!"},
    )


@router.get("/healthcheck", response_model=IResponseModel)
async def health_check():
    """
    Health check endpoint to verify the service is operational.
    """
    return JSONResponse(
        status_code=200,
        content={"message": "Search Service is healthy!"},
    )
