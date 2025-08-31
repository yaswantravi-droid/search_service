from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from search_service.app.settings.settings import (
    FRONTEND_BACKEND_MAPPER,
    BACKEND_FRONTEND_MAPPER,
)
from search_service.src.models.search import SearchRequest, SearchResponse
from search_service.src.services.search_service import SearchService
from search_service.app.lifespan.startup import mongo_db
from common.logging.custom_logger import logger


router = APIRouter()


def get_search_service() -> SearchService:
    """Dependency to get search service instance."""
    if not mongo_db.is_initialized:
        raise HTTPException(status_code=503, detail="Search service not ready")
    return SearchService(mongo_db.db)


@router.get("/", response_model=Dict[str, str])
async def welcome():
    """Welcome endpoint for the search service."""
    return {
        "message": "Search Service API",
        "description": "Enhanced search service using Atlas Search for optimal performance and relevance",
        "version": "2.0.0",
        "endpoints": {
            "search": "POST /searches - Perform search across collections",
            "categories": "GET /categories - View available frontend categories",
            "health": "GET /healthcheck - Service health status",
            "welcome": "GET / - This information"
        },
        "features": [
            "Atlas Search integration",
            "Centralized index management",
            "Multi-collection search",
            "Configurable search fields",
            "Team-based filtering",
            "Relevance scoring",
            "Frontend-backend category mapping",
            "Google-like search"
        ]
    }


@router.post("/", response_model=SearchResponse)
async def search(
    request: SearchRequest,
    search_service: SearchService = Depends(get_search_service)
):
    """
    Perform an Atlas Search across MongoDB collections with enhanced scoring.
    
    This endpoint provides Google-like search capabilities using MongoDB Atlas Search:
    - Exact matches (highest priority)
    - Prefix matches (high priority)
    - Fuzzy matches with typo tolerance (medium priority)
    - Wildcard search for partial matches (lower priority)
    - Compound scoring across multiple fields
    - Enhanced relevance scoring
    
    Features:
    - Atlas Search enabled by default
    - Configurable result limits
    - Cross-collection search
    - Team-based data isolation
    - Smart relevance scoring
    - Dynamic index creation
    """
    try:
        logger.info(f"Processing Atlas Search request for teamId: {request.teamId}, query: '{request.query}'")
        result = await search_service.search(request)
        logger.info(f"Atlas Search completed: {len(result.results)} results found in {result.search_time_ms:.2f}ms")
        return result
    except Exception as e:
        logger.error(f"Atlas Search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/categories", response_model=Dict[str, Any])
async def get_available_categories():
    """
    Get available search categories.
    
    This endpoint shows frontend developers what category names they can use
    in their search requests.
    """
    try:
        # Only return categories - backend collections are internal
        categories = list(FRONTEND_BACKEND_MAPPER.keys())
        
        return {
            "message": "Available search categories",
            "categories": categories,
            "example_usage": {
                "search_request": {
                    "teamId": "team123",
                    "query": "assistant",
                    "categories": categories,  # Use actual available categories
                    "limit": 10
                },
                "note": "Use these category names in your search requests. They will be automatically mapped to backend collections."
            }
        }
    except Exception as e:
        logger.error(f"Failed to get categories: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get categories: {str(e)}")
