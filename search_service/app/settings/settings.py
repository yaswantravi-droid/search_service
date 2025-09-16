import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

# MongoDB Configuration
MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017/interactly")

# Search Configuration
SEARCH_CATEGORIES: List[str] = [
    "bots",
    "knowledgebase", 
    "tools",
    "wf_workflows"
]

@dataclass
class FieldConfig:
    """Configuration for a searchable field."""
    path: str  # Field path (e.g., "name", "function.name")
    field_type: str  # Atlas Search field type (autocomplete, string, keyword, etc.)
    boost: Optional[float] = None  # Optional boost value for scoring
    fuzzy: Optional[Dict[str, Any]] = None  # Optional fuzzy matching config

@dataclass
class CollectionSearchConfig:
    """Configuration for searching a collection."""
    searchable_fields: List[FieldConfig]
    returnable_fields: List[str]
    team_id_field: str = "teamId"  # Field used for team filtering
    display_name_field: str = "name"  # Standardized field name for display

# Improved searchable fields configuration with proper nested field support
SEARCH_CATEGORIES_CONFIG: Dict[str, CollectionSearchConfig] = {
    "bots": CollectionSearchConfig(
        searchable_fields=[
            FieldConfig(
                path="name",
                field_type="autocomplete",
                boost=5.0,
                fuzzy={"maxEdits": 1, "prefixLength": 1, "maxExpansions": 50}
            ),
            FieldConfig(
                path="name",
                field_type="string",
                boost=2.0,
                fuzzy={"maxEdits": 1, "prefixLength": 1}
            )
        ],
        returnable_fields=["_id", "name", "teamId"],
        display_name_field="name"
    ),
    "knowledgebase": CollectionSearchConfig(
        searchable_fields=[
            FieldConfig(
                path="title",
                field_type="autocomplete",
                boost=5.0,
                fuzzy={"maxEdits": 1, "prefixLength": 1, "maxExpansions": 50}
            ),
            FieldConfig(
                path="title",
                field_type="string",
                boost=2.0,
                fuzzy={"maxEdits": 1, "prefixLength": 1}
            )
        ],
        returnable_fields=["_id", "title", "teamId"],
        display_name_field="title"
    ),
    "tools": CollectionSearchConfig(
        searchable_fields=[
            FieldConfig(
                path="function.name",
                field_type="autocomplete",
                boost=5.0,
                fuzzy={"maxEdits": 1, "prefixLength": 1, "maxExpansions": 50}
            ),
            FieldConfig(
                path="function.name",
                field_type="string",
                boost=2.0,
                fuzzy={"maxEdits": 1, "prefixLength": 1}
            )
        ],
        returnable_fields=["_id", "function.name", "teamId"],
        display_name_field="function.name"
    ),
    "wf_workflows": CollectionSearchConfig(
        searchable_fields=[
            FieldConfig(
                path="workflow_config.name",
                field_type="autocomplete",
                boost=5.0,
                fuzzy={"maxEdits": 1, "prefixLength": 1, "maxExpansions": 50}
            ),
            FieldConfig(
                path="workflow_config.name",
                field_type="string",
                boost=2.0,
                fuzzy={"maxEdits": 1, "prefixLength": 1}
            )
        ],
        returnable_fields=["_id", "workflow_config.name", "team_id"],
        team_id_field="team_id",  # Different team ID field name
        display_name_field="workflow_config.name"
    )
}

# Legacy compatibility - kept for backward compatibility only
RETURNABLE_FIELDS_CONFIG: Dict[str, List[str]] = {
    "bots": ["_id", "name", "teamId"],
    "knowledgebase": ["_id", "title", "teamId"],
    "tools": ["_id", "function.name", "teamId"],
    "wf_workflows": ["_id", "workflow_config.name", "teamId"]
}

# Atlas Search Index Configuration
ATLAS_SEARCH_INDEXES = {
    "bots": {
        "enabled": True,
        "index_name": "bots_search_index",
        "searchable_fields": ["name"],
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
                        },
                        {"type": "string"}
                    ],
                    "teamId": {"type": "token"}
                }
            }
        }
    },
    "knowledgebase": {
        "enabled": True,
        "index_name": "knowledgebase_search_index",
        "searchable_fields": ["title"],
        "index_definition": {
            "mappings": {
                "dynamic": False,
                "fields": {
                    "title": [
                        {
                            "type": "autocomplete",
                            "tokenization": "nGram",
                            "minGrams": 2,
                            "maxGrams": 15,
                            "foldDiacritics": True
                        },
                        {"type": "string"}
                    ],
                    "teamId": {"type": "token"}
                }
            }
        }
    },
    "tools": {
        "enabled": True,
        "index_name": "tools_search_index",
        "searchable_fields": ["function.name"],
        "index_definition": {
            "mappings": {
                "dynamic": False,
                "fields": {
                    "function": {
                        "type": "document",
                        "fields": {
                            "name": [
                                {
                                    "type": "autocomplete",
                                    "tokenization": "nGram",
                                    "minGrams": 2,
                                    "maxGrams": 15,
                                    "foldDiacritics": True
                                },
                                {"type": "string"}
                            ]
                        }
                    },
                    "teamId": {"type": "token"}
                }
            }
        }
    },
    "wf_workflows": {
        "enabled": True,
        "index_name": "wf_workflows_search_index",
        "searchable_fields": ["workflow_config.name"],
        "index_definition": {
            "mappings": {
                "dynamic": False,
                "fields": {
                    "workflow_config": {
                        "type": "document",
                        "fields": {
                            "name": [
                                {
                                    "type": "autocomplete",
                                    "tokenization": "nGram",
                                    "minGrams": 2,
                                    "maxGrams": 15,
                                    "foldDiacritics": True
                                },
                                {"type": "string"}
                            ]
                        }
                    },
                    "team_id": {"type": "objectId"}  # ObjectId type for team_id field
                }
            }
        }
    }
}

# Frontend-Backend Category Mapper
FRONTEND_BACKEND_MAPPER: Dict[str, str] = {
    "assistant": "bots",
    "knowledge": "knowledgebase",
    "tools": "tools",
    "workflows": "wf_workflows",
}

# Reverse mapper for converting backend names to frontend names (for responses)
BACKEND_FRONTEND_MAPPER: Dict[str, str] = {
    "bots": "assistant",
    "knowledgebase": "knowledge",
    "tools": "tools",
    "wf_workflows": "workflows",
}


