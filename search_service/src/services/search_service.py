import time
from typing import List, Dict, Any, Optional, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from search_service.app.settings.settings import (
    SEARCH_CATEGORIES,
    SEARCH_CATEGORIES_CONFIG,
    RETURNABLE_FIELDS_CONFIG,
    ATLAS_SEARCH_CONFIG,
    ATLAS_SEARCH_INDEXES,
    FRONTEND_BACKEND_MAPPER,
    BACKEND_FRONTEND_MAPPER,
)

# Setup custom logging (same standard as workflow service)
from common.logging.custom_logger import logger

from search_service.src.models.search import (
    SearchRequest,
    SearchResult,
    SearchResponse,
)


class SearchService:
    """Optimized service for performing Atlas Search across MongoDB collections."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.categories = SEARCH_CATEGORIES
        self.categories_config = SEARCH_CATEGORIES_CONFIG
        self.returnable_fields_config = RETURNABLE_FIELDS_CONFIG
        self.atlas_config = ATLAS_SEARCH_CONFIG
    
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
            
            logger.info(f"Frontend categories: {frontend_categories} -> Backend collections: {backend_collections}")
            
            # Log the Atlas Search configuration being used
            for backend_collection in backend_collections:
                index_config = ATLAS_SEARCH_INDEXES.get(backend_collection, {})
                index_name = index_config.get("index_name", "not_configured")
                logger.info(f"Collection '{backend_collection}' will use Atlas Search index: '{index_name}'")
            
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
            
            # Sort by Atlas Search score (descending) - scores come directly from MongoDB Atlas
            sorted_results = sorted(all_results, key=lambda x: x.score, reverse=True)
            
            # Apply limit if specified
            if request.limit and len(sorted_results) > request.limit:
                sorted_results = sorted_results[:request.limit]
                total_count = min(total_count, request.limit)
            
            # Calculate search time
            search_time_ms = (time.time() - start_time) * 1000
            
            logger.info(f"Atlas Search completed in {search_time_ms:.2f}ms: {total_count} results found")
            
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
            # Re-raise the exception to maintain the specific error message
            raise e
    
    async def _search_collection(self, collection_name: str, request: SearchRequest) -> Tuple[List[SearchResult], int]:
        """Search within a specific collection using optimized Atlas Search."""
        try:
            collection = self.db[collection_name]
            searchable_columns = self.categories_config.get(collection_name, [])
            returnable_fields = self.returnable_fields_config.get(collection_name, [])
            
            if not searchable_columns:
                logger.warning(f"No searchable columns configured for collection {collection_name}")
                return [], 0
            
            # Build optimized Atlas Search query
            search_query = self._build_optimized_atlas_query(request.query, searchable_columns, collection_name)
            
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
            
            # Execute optimized Atlas Search using MongoDB aggregation pipeline
            pipeline = [
                {
                    "$search": search_query
                },
                {
                    "$match": {
                        "teamId": request.teamId
                    }
                },
                {
                    "$addFields": {
                        "searchScore": {"$meta": "searchScore"},  # Capture Atlas Search score
                        "searchHighlights": {"$meta": "searchHighlights"}  # Capture search highlights
                    }
                },
                {
                    "$project": projection
                }
            ]
            
            cursor = collection.aggregate(pipeline)
            
            results = []
            async for doc in cursor:
                result = self._convert_to_search_result(
                    doc, collection_name, returnable_fields
                )
                results.append(result)
            
            # Get total count for this collection using $count (keep same search + match)
            count_pipeline = [
                {
                    "$search": search_query
                },
                {
                    "$match": {
                        "teamId": request.teamId
                    }
                },
                {
                    "$count": "total"
                }
            ]
            
            count_result = await collection.aggregate(count_pipeline).to_list(1)
            total_count = count_result[0]["total"] if count_result else 0
            
            return results, total_count
            
        except Exception as e:
            logger.error(f"Error searching collection {collection_name}: {str(e)}")
            return [], 0
    
    def _build_optimized_atlas_query(self, query: str, searchable_columns: List[str], collection_name: str) -> Dict[str, Any]:
        """Build an optimized Atlas Search query for best performance using dynamic index names."""
        # Clean and prepare the query
        clean_query = query.strip()
        
        # Get the correct index name for this collection from settings
        index_config = ATLAS_SEARCH_INDEXES.get(collection_name, {})
        index_name = index_config.get("index_name", "default")
        
        if not index_name or index_name == "default":
            logger.error(f"No Atlas Search index configured for collection '{collection_name}'")
            raise Exception(f"Atlas Search index not configured for collection '{collection_name}'")
        
        logger.info(f"Using Atlas Search index '{index_name}' for collection '{collection_name}'")
        
        # Skip teamId as it's used for filtering, not searching
        search_fields = [field for field in searchable_columns if field != "teamId"]
        
        if not search_fields:
            return {"index": index_name}
        
        # Build optimized compound search query with correct index name
        search_query = {
            "index": index_name,  # Use the actual index name from settings
            "compound": {
                "should": [],
                "minimumShouldMatch": 1
            }
        }
        
        # Add search strategies based on the actual index definition
        for field in search_fields:
            # Get the index definition for this collection to determine available field types
            index_config = ATLAS_SEARCH_INDEXES.get(collection_name, {})
            index_definition = index_config.get("index_definition", {})
            
            # Check what field types are available in the index
            field_mapping = index_definition.get("mappings", {}).get("fields", {}).get(field, [])
            
            if isinstance(field_mapping, list):
                # Handle array of field types (like our current bots index)
                for field_type_config in field_mapping:
                    field_type = field_type_config.get("type")
                    if field_type == "autocomplete":
                        # Enhanced autocomplete search with fuzzy matching
                        search_query["compound"]["should"].append({
                            "autocomplete": {
                                "query": clean_query,
                                "path": field,
                                "tokenOrder": "any",
                                "fuzzy": {
                                    "maxEdits": 1,
                                    "prefixLength": 1,
                                    "maxExpansions": 50
                                }
                            }
                        })
                    elif field_type == "string":
                        # Text search for string fields
                        search_query["compound"]["should"].append({
                            "text": {
                                "query": clean_query,
                                "path": field
                            }
                        })
                    elif field_type == "keyword":
                        # Term search for keyword fields
                        search_query["compound"]["should"].append({
                            "term": {
                                "query": clean_query,
                                "path": field
                            }
                        })
            else:
                # Handle single field type (fallback)
                field_type = field_mapping.get("type") if isinstance(field_mapping, dict) else "string"
                if field_type == "autocomplete":
                    search_query["compound"]["should"].append({
                        "autocomplete": {
                            "query": clean_query,
                            "path": field
                        }
                    })
                else:
                    # Default to text search
                    search_query["compound"]["should"].append({
                        "text": {
                            "query": clean_query,
                            "path": field
                        }
                    })
        
        return search_query
    
    def _convert_to_search_result(self, doc: Dict[str, Any], collection_name: str, returnable_fields: List[str]) -> SearchResult:
        """Convert MongoDB document to SearchResult using Atlas Search score directly."""
        # Convert backend collection name to frontend category name
        frontend_category = BACKEND_FRONTEND_MAPPER.get(collection_name, collection_name)
        
        # Start with essential fields
        result_data = {
            "id": str(doc.get("_id")) if doc.get("_id") is not None else None,
            "category": frontend_category,  # Return frontend category instead of backend collection
            "score": 0.0,  # Will be set from Atlas Search score
            "match_type": "atlas_search"
        }
        
        # Add all returnable fields from the document
        if returnable_fields:
            for field in returnable_fields:
                if field in doc and field not in result_data:
                    value = doc.get(field)
                    # Convert ObjectId to string if needed
                    if isinstance(value, ObjectId):
                        value = str(value)
                    result_data[field] = value
        
        # Use Atlas Search score directly from MongoDB (we ensured it's in projection)
        if "searchScore" in doc and doc["searchScore"] is not None:
            try:
                result_data["score"] = float(doc["searchScore"])
            except (ValueError, TypeError):
                result_data["score"] = 0.0
        
        # Optionally include highlights if present
        if "searchHighlights" in doc and doc["searchHighlights"]:
            result_data["highlights"] = doc["searchHighlights"]
        
        # Remove None values to keep the response clean
        result_data = {k: v for k, v in result_data.items() if v is not None}
        
        return SearchResult(**result_data)
    
    def _convert_frontend_to_backend(self, frontend_categories: List[str]) -> List[str]:
        """Convert frontend category names to backend collection names using mapper.
        Allows partial success: valid mapped categories are returned and invalid ones are logged."""
        if not frontend_categories:
            return []
        
        backend_collections = []
        for cat in frontend_categories:
            if cat in FRONTEND_BACKEND_MAPPER:
                backend_collections.append(FRONTEND_BACKEND_MAPPER[cat])
            else:
                logger.warning(f"Invalid frontend category requested: {cat} (skipping)")
        
        # Deduplicate while preserving order
        seen = set()
        deduped = []
        for coll in backend_collections:
            if coll not in seen:
                seen.add(coll)
                deduped.append(coll)
        
        return deduped
    
    def _convert_backend_to_frontend(self, backend_collections: List[str]) -> List[str]:
        """Convert backend collection names to frontend category names using mapper."""
        frontend_categories = []
        for backend_coll in backend_collections:
            if backend_coll in BACKEND_FRONTEND_MAPPER:
                frontend_categories.append(BACKEND_FRONTEND_MAPPER[backend_coll])
            else:
                logger.warning(f"Backend collection '{backend_coll}' not found in mapper")
        return frontend_categories
    
    def _get_default_frontend_categories(self) -> List[str]:
        """Get default frontend categories when none specified in request."""
        return list(FRONTEND_BACKEND_MAPPER.keys())
