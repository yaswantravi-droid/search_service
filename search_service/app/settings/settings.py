import os
from typing import List, Dict, Any

# MongoDB Configuration
MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017/interactly")

# Search Configuration
SEARCH_CATEGORIES: List[str] = [
    "bots"  # Add more collections here as needed
]

# Searchable columns for each category (backend configuration)
SEARCH_CATEGORIES_CONFIG: Dict[str, List[str]] = {
    "bots": ["name", "teamId"],  # Search bots collection on name and teamId
}

# Returnable fields for each category (what gets returned in search results)
RETURNABLE_FIELDS_CONFIG: Dict[str, List[str]] = {
    "bots": [
        "_id", "name", "teamId"  # Return essential fields for bots
    ]
}

# Atlas Search Configuration
ATLAS_SEARCH_CONFIG = {
    "enabled": True,
    "max_results": 100,
    "min_score_threshold": 10.0,  # Minimum score to include in results
    "wildcard_search": True,  # Enable wildcard search for partial matches
    "compound_scoring": True,  # Enable compound scoring for multiple field matches
}

# Atlas Search Index Configuration
ATLAS_SEARCH_INDEXES = {
    "bots": {
        "enabled": True,  # Enable index creation from code
        "index_name": "bots_search_index",  # Use original index name for upsert logic
        "searchable_fields": ["name"],  # Only index the 'name' field for search
        "index_definition": {
            "mappings": {
                "dynamic": False,
                "fields": {
                    "name": [
                        {
                            "type": "autocomplete",
                            "tokenization": "nGram",
                            "minGrams": 2,
                            "maxGrams": 15,
                            "foldDiacritics": True
                        }
                    ]
                }
            }
        }
    }
}

# Frontend-Backend Category Mapper
FRONTEND_BACKEND_MAPPER: Dict[str, str] = {
    "assistant": "bots",
}

# Reverse mapper for converting backend names to frontend names (for responses)
BACKEND_FRONTEND_MAPPER: Dict[str, str] = {
    "bots": "assistant",
}
