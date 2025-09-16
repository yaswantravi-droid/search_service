from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    """Request model for search queries."""
    teamId: str = Field(..., description="Team ID for the search")
    query: str = Field(..., description="Search query string", min_length=1)
    categories: Optional[List[str]] = Field(
        default=None, 
        description="Specific categories (collections) to search in. If not provided, searches all configured categories."
    )
    limit: Optional[int] = Field(
        default=50,
        description="Maximum number of results to return",
        ge=1,
        le=100
    )


class SearchResult(BaseModel):
    """Dynamic model for individual search results - accepts any fields from MongoDB documents."""
    id: str = Field(..., description="Unique identifier for the result")
    category: str = Field(..., description="Frontend category name (e.g., 'assistant' instead of 'bots')")
    score: float = Field(..., description="Relevance score from MongoDB")
    match_type: str = Field(..., description="Type of match: atlas_search")
    
    # Allow any additional fields from MongoDB documents
    class Config:
        extra = "allow"


class SearchResponse(BaseModel):
    """Response model for search queries."""
    teamId: str = Field(..., description="Team ID that was searched")
    query: str = Field(..., description="The original search query")
    results: List[SearchResult] = Field(
        default_factory=list, 
        description="List of search results"
    )
    total: int = Field(..., description="Total number of results found")
    categories_searched: List[str] = Field(
        ..., 
        description="Categories (collections) that were searched"
    )
    search_time_ms: float = Field(..., description="Time taken for the search in milliseconds")
