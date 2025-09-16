from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends

from search_service.app.settings.settings import (
    FRONTEND_BACKEND_MAPPER,
)
from search_service.src.models.search import SearchRequest, SearchResponse
from search_service.src.services.search_service import SearchService
from search_service.app.lifespan.startup import mongo_db
from common.logging.custom_logger import logger


router = APIRouter(prefix="/v1")


def get_search_service() -> SearchService:
    """Dependency to get search service instance."""
    if not mongo_db.is_initialized:
        raise HTTPException(status_code=503, detail="Search service not ready")
    return SearchService(mongo_db.db)


@router.get("/schema")
async def get_search_schema():
    """
    Endpoint to retrieve the schema for search
    """
    return {
        "search_request_schema": SearchRequest.model_json_schema(mode="serialization"),
        "search_response_schema": SearchResponse.model_json_schema(mode="serialization"),
        "available_categories": list(FRONTEND_BACKEND_MAPPER.keys()),
    }


@router.post("/query", response_model=SearchResponse)
async def search(
    request: SearchRequest,
    search_service: SearchService = Depends(get_search_service)
):
    """
    Endpoint to perform search across collections.
    """
    try:
        logger.info(f"Processing search request for teamId: {request.teamId}, query: '{request.query}'")
        result = await search_service.search(request)
        logger.info(f"Search completed: {len(result.results)} results found in {result.search_time_ms:.2f}ms")
        return result
    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/categories")
async def get_available_categories():
    """
    Endpoint to get available search categories.
    """
    try:
        categories = list(FRONTEND_BACKEND_MAPPER.keys())
        
        return {
            "message": "Available search categories",
            "categories": categories,
        }
    except Exception as e:
        logger.error(f"Failed to get categories: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get categories: {str(e)}")
