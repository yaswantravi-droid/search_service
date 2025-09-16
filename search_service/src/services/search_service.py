import time
from typing import List, Dict, Any, Optional, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from search_service.app.settings.settings import (
    SEARCH_CATEGORIES,
    SEARCH_CATEGORIES_CONFIG,
    RETURNABLE_FIELDS_CONFIG,
    ATLAS_SEARCH_INDEXES,
    FRONTEND_BACKEND_MAPPER,
    BACKEND_FRONTEND_MAPPER,
    FieldConfig,
    CollectionSearchConfig,
)

# Setup custom logging (same standard as workflow service)
from common.logging.custom_logger import logger

from search_service.src.models.search import (
    SearchRequest,
    SearchResult,
    SearchResponse,
)


class SearchException(Exception):
    """Custom exception for search service errors that masks internal details."""
    
    def __init__(self, message: str, internal_error: str = None):
        super().__init__(message)
        self.internal_error = internal_error
        if internal_error:
            logger.error(f"Search error: {message} (Internal: {internal_error})")
        else:
            logger.error(f"Search error: {message}")


class SearchService:
    """High-performance service for performing Atlas Search across MongoDB collections."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.categories = SEARCH_CATEGORIES
        self.categories_config = SEARCH_CATEGORIES_CONFIG
        self.returnable_fields_config = RETURNABLE_FIELDS_CONFIG
    
    async def search(self, request: SearchRequest) -> SearchResponse:
        """
        Perform an optimized Atlas Search across configured categories.
        """
        start_time = time.time()
        
        try:
            # Check if database is available
            if self.db is None:
                logger.error("Database connection not available")
                raise Exception("Database connection not available")
            
            # Validate that at least one category is required
            if not request.categories or len(request.categories) == 0:
                logger.error("No categories provided in search request. At least one category is required.")
                raise Exception("At least one category is required for search")
            
            # Convert frontend categories to backend collections using mapper
            frontend_categories = request.categories
            backend_collections = self._convert_frontend_to_backend(frontend_categories)
            
            if not backend_collections:
                logger.error(f"No valid backend collections found for frontend categories: {frontend_categories}")
                raise Exception(f"Invalid categories provided: {frontend_categories}. Please use valid category names.")
            
            # Minimal logging for performance
            logger.debug(f"Searching collections: {backend_collections}")
            
            # Search across specified backend collections
            all_results = []
            total_count = 0
            
            for backend_collection in backend_collections:
                if backend_collection not in self.categories:
                    logger.warning(f"Backend collection {backend_collection} not in allowed search categories")
                    continue
                    
                collection_results, collection_count = await self._search_collection(
                    backend_collection, request
                )
                all_results.extend(collection_results)
                total_count += collection_count
            
            # Results are already sorted by score within each collection from the $facet pipeline
            # For global sorting across collections, we sort in Python (this is efficient for typical result counts)
            # 
            # FUTURE OPTIMIZATION: If you expect thousands of results across collections, consider using $unionWith:
            # 1. Collect all results with collection metadata
            # 2. Use $unionWith to combine all collections
            # 3. Let MongoDB handle global sort + limit in one query
            # 4. This would eliminate Python sorting but requires more complex pipeline design
            sorted_results = sorted(all_results, key=lambda x: x.score, reverse=True)
            
            # Apply limit if specified
            if request.limit and len(sorted_results) > request.limit:
                sorted_results = sorted_results[:request.limit]
                total_count = min(total_count, request.limit)
            
            # Calculate search time
            search_time_ms = (time.time() - start_time) * 1000
            
            # Only log if search takes longer than 100ms
            if search_time_ms > 100:
                logger.warning(f"Slow search: {search_time_ms:.2f}ms for {total_count} results")
            
            # Convert backend collection names back to frontend categories for response
            frontend_categories_searched = self._convert_backend_to_frontend(backend_collections)
            
            # Create response
            response = SearchResponse(
                teamId=request.teamId,
                query=request.query,
                results=sorted_results,
                total=total_count,
                categories_searched=frontend_categories_searched,
                search_time_ms=search_time_ms
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            # Wrap with custom exception to mask internal details in API responses
            raise SearchException("Search operation failed", str(e))
    
    async def _search_collection(self, collection_name: str, request: SearchRequest) -> Tuple[List[SearchResult], int]:
        """Search within a specific collection using optimized Atlas Search."""
        try:
            collection = self.db[collection_name]
            
            # Direct configuration access for maximum performance
            collection_config = self.categories_config.get(collection_name)
            if not isinstance(collection_config, CollectionSearchConfig):
                logger.warning(f"No valid configuration for collection {collection_name}")
                return [], 0
            
            searchable_fields = collection_config.searchable_fields
            returnable_fields = collection_config.returnable_fields
            team_id_field = collection_config.team_id_field
            
            if not searchable_fields:
                return [], 0
            
            # Build optimized Atlas Search query
            search_query = self._build_optimized_atlas_query(request.query, searchable_fields, collection_name, request, team_id_field)
            
            # Build projection based on returnable fields and ensure we include search meta fields
            projection = {}
            if returnable_fields:
                for field in returnable_fields:
                    projection[field] = 1

            # Always include searchScore and searchHighlights so we can surface scoring & highlights
            projection["searchScore"] = 1
            projection["searchHighlights"] = 1
            # Include _id by default if not present in returnable fields
            if "_id" not in projection:
                projection["_id"] = 1
            
            # Execute optimized Atlas Search using MongoDB aggregation pipeline with $facet
            # This fetches both results and count in a single query for better performance
            pipeline = [
                {
                    "$search": search_query
                },
                {
                    "$facet": {
                        "results": [
                            {
                                "$addFields": {
                                    "searchScore": {"$meta": "searchScore"},  # Capture Atlas Search score
                                    "searchHighlights": {"$meta": "searchHighlights"}  # Capture search highlights
                                }
                            },
                            {
                                "$sort": {"searchScore": -1}  # Sort by score descending
                            },
                            {
                                "$limit": request.limit or 50
                            },
                            {
                                "$project": projection
                            }
                        ],
                        "totalCount": [
                            {
                                "$count": "total"
                            }
                        ]
                    }
                }
            ]
            
            facet_result = await collection.aggregate(pipeline).to_list(1)
            
            if not facet_result or not facet_result[0]:
                return [], 0
            
            facet_data = facet_result[0]
            results = []
            
            # Process results
            for doc in facet_data.get("results", []):
                result = self._convert_to_search_result(
                    doc, collection_name, returnable_fields
                )
                results.append(result)
            
            # Get total count from facet
            total_count_data = facet_data.get("totalCount", [])
            total_count = total_count_data[0].get("total", 0) if total_count_data else 0
            
            return results, total_count
            
        except Exception as e:
            logger.error(f"Error searching collection {collection_name}: {str(e)}")
            return [], 0
    
    def _build_optimized_atlas_query(self, query: str, searchable_fields: List[FieldConfig], collection_name: str, request: SearchRequest, team_id_field: str = "teamId") -> Dict[str, Any]:
        """Build an optimized Atlas Search query for maximum performance."""
        clean_query = query.strip()
        if not clean_query or not searchable_fields:
            return {"index": ATLAS_SEARCH_INDEXES[collection_name]["index_name"]}
        
        # Pre-compute index name for performance
        index_name = ATLAS_SEARCH_INDEXES[collection_name]["index_name"]
        
        # Handle team ID conversion for ObjectId fields
        team_id_value = request.teamId
        if team_id_field == "team_id":
            # Convert string teamId to ObjectId for collections that store team_id as ObjectId
            try:
                team_id_value = ObjectId(request.teamId)
            except Exception as e:
                logger.warning(f"Failed to convert teamId to ObjectId for collection {collection_name}: {e}")
                team_id_value = request.teamId
        
        # Build optimized compound search query
        search_query = {
            "index": index_name,
            "compound": {
                "filter": [{"equals": {"path": team_id_field, "value": team_id_value}}],
                "should": [],
                "minimumShouldMatch": 1
            },
            "highlight": {
                "path": [field.path for field in searchable_fields],
                "maxNumPassages": 3  # Reduced for performance
            }
        }
        
        # Add search strategies - optimized for speed
        for field_config in searchable_fields:
            field_query = self._build_field_query(clean_query, field_config)
            if field_query:
                search_query["compound"]["should"].append(field_query)
        
        return search_query
    
    def _build_field_query(self, query: str, field_config: FieldConfig) -> Optional[Dict[str, Any]]:
        """Build a search query for a specific field configuration - optimized for speed."""
        base_query = {"query": query, "path": field_config.path}
        
        # Add boost if specified
        if field_config.boost:
            base_query["score"] = {"boost": {"value": field_config.boost}}
        
        # Optimized field type handling
        field_type = field_config.field_type
        if field_type == "autocomplete":
            autocomplete_query = {"autocomplete": base_query}
            # Only add fuzzy matching, not index configuration fields
            if field_config.fuzzy:
                autocomplete_query["autocomplete"]["fuzzy"] = field_config.fuzzy
            return autocomplete_query
            
        elif field_type == "string":
            text_query = {"text": base_query}
            if field_config.fuzzy:
                text_query["text"]["fuzzy"] = field_config.fuzzy
            return text_query
            
        elif field_type in ("keyword", "token"):
            return {"term": base_query}
            
        else:
            # Default to text search
            return {"text": base_query}
    
    def _convert_to_search_result(self, doc: Dict[str, Any], collection_name: str, returnable_fields: List[str]) -> SearchResult:
        """Convert MongoDB document to SearchResult - optimized for speed."""
        # Convert backend collection name to frontend category name
        frontend_category = BACKEND_FRONTEND_MAPPER.get(collection_name, collection_name)
        
        # Get collection configuration for display name field
        collection_config = self.categories_config.get(collection_name)
        display_name_field = collection_config.display_name_field if collection_config else "name"
        
        # Start with essential fields
        result_data = {
            "id": str(doc.get("_id")) if doc.get("_id") is not None else None,
            "category": frontend_category,
            "score": float(doc.get("searchScore", 0.0)),
            "match_type": "atlas_search"
        }
        
        # Add standardized name field for frontend consistency
        display_name_value = self._get_nested_field_value(doc, display_name_field)
        if display_name_value is not None:
            result_data["name"] = str(display_name_value)
        
        # Add returnable fields efficiently
        for field in returnable_fields:
            if field not in result_data:
                value = self._get_nested_field_value(doc, field)
                if value is not None:
                    if isinstance(value, ObjectId):
                        value = str(value)
                    result_data[field] = value
        
        # Add highlights if present
        if "searchHighlights" in doc and doc["searchHighlights"]:
            result_data["highlights"] = doc["searchHighlights"]

        # Remove None values
        result_data = {k: v for k, v in result_data.items() if v is not None}
        
        return SearchResult(**result_data)
    
    def _get_nested_field_value(self, doc: Dict[str, Any], field_path: str) -> Any:
        """Get value from nested field path (e.g., 'function.name')."""
        if "." not in field_path:
            return doc.get(field_path)
        
        # Handle nested fields like "function.name"
        parts = field_path.split(".")
        current = doc
        
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        
        return current
    
    def _convert_frontend_to_backend(self, frontend_categories: List[str]) -> List[str]:
        """Convert frontend category names to backend collection names - optimized."""
        if not frontend_categories:
            return []
        
        backend_collections = []
        for cat in frontend_categories:
            if cat in FRONTEND_BACKEND_MAPPER:
                backend_collections.append(FRONTEND_BACKEND_MAPPER[cat])
        
        # Return unique collections while preserving order
        return list(dict.fromkeys(backend_collections))
    
    def _convert_backend_to_frontend(self, backend_collections: List[str]) -> List[str]:
        """Convert backend collection names to frontend category names - optimized."""
        return [BACKEND_FRONTEND_MAPPER[coll] for coll in backend_collections if coll in BACKEND_FRONTEND_MAPPER]
