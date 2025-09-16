# 🔍 **Search Service - Atlas Search Edition**

A high-performance, scalable search service built with **FastAPI** and **MongoDB Atlas Search** that provides Google-like search capabilities with autocomplete and fuzzy matching.

## 🚀 **What This Service Does**

- **Atlas Search Integration**: Uses MongoDB Atlas Search directly with pymongo for lightning-fast, relevant search results
- **Centralized Index Management**: Indexes created once on startup, not during search operations
- **Autocomplete Search**: Google-like search suggestions with fuzzy matching and typo tolerance
- **Team-Based Isolation**: Automatically filters results by team ID for security (using filter clause)
- **Configurable Fields**: Easily configure which fields to search and return for each collection
- **Direct Score Usage**: Uses Atlas Search scores directly from MongoDB - no manual calculation
- **Performance Optimized**: Single-query execution with $facet for results and count
- **Empty Query Protection**: Automatically handles empty queries without errors

## 🏗️ **Architecture Overview**

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   FastAPI App   │───▶│  Atlas Search    │───▶│  MongoDB Atlas  │
│                 │    │  Service         │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Search API    │    │ Centralized      │    │   Collections   │
│   Endpoints     │    │ Index Manager    │    │   (bots, etc.)  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

**Key Components:**
- **FastAPI App**: Web framework and API endpoints
- **Atlas Search Service**: Optimized search logic using MongoDB Atlas Search
- **Centralized Index Manager**: Creates indexes once on startup
- **MongoDB Atlas**: Database with built-in Atlas Search capabilities

## 🔧 **Key Features**

### **1. Atlas Search Engine**
- **Autocomplete**: Real-time search suggestions with nGram tokenization
- **Fuzzy Matching**: Handles typos with configurable edit distance
- **Token Order Flexibility**: Matches tokens in any order for better results
- **Performance Optimized**: Uses Atlas Search's built-in scoring

### **2. Advanced Configuration System**
- **Type-Safe Configuration**: Uses dataclasses for compile-time type checking
- **Nested Field Support**: Handles complex nested fields like `function.name` and `workflow_config.name`
- **Multiple Search Strategies**: Same field can have both autocomplete and string search
- **Dynamic Team ID Mapping**: Different collections can use different team ID field names
- **ObjectId Support**: Automatic conversion between string and ObjectId team IDs

### **3. Performance & Scalability**
- **O(log n) Performance**: Logarithmic search time regardless of collection size
- **Startup Indexing**: Indexes created once, not during search operations
- **Memory Efficient**: Minimal overhead with Atlas Search
- **Horizontal Scaling**: Scales with your MongoDB Atlas cluster
- **Single Query Execution**: Results and count fetched in one database query per collection
- **Optimized Lookups**: Index definitions cached to avoid repeated database lookups

### **4. Standardized API Response**
- **Consistent Field Names**: All results include a standardized `name` field
- **Frontend Simplicity**: Frontend can use `result.name` for all categories
- **Backward Compatibility**: Original fields are preserved in response
- **Multiple Field Types**: Same field can have different search strategies with different boost values

### **5. Dynamic Field Management**
- **Configurable Boost Values**: Fine-tune relevance scoring per field type
- **Per-Field Fuzzy Matching**: Different fuzzy settings for different field types
- **Nested Field Extraction**: Properly extracts values from nested document structures
- **Team ID Flexibility**: Each collection can use different team ID field names and types

### **6. Frontend-Backend Category Mapping**
- **User-Friendly Names**: Frontend uses "assistant" instead of "bots"
- **Backend Collections**: Backend uses actual collection names like "bots"
- **Automatic Translation**: API automatically maps "assistant" to "bots"
- **Transparent to Frontend**: No changes needed in frontend code when adding collections

## 📡 **API Endpoints**

The Search Service follows the same standard as other Interactly services with clean, essential endpoints:

### **Base URL Structure**
- **Service Name**: `search_service` (from common configs)
- **Prefix**: `/search` (from `SEARCH_SERVICE_NAME.split('_')[0]`)
- **Root Path**: `/search` (singular, following service naming)
- **Version**: `/v1` (API versioning)
- **Final Base URL**: `/search/v1`

### **Available Endpoints**

#### **1. API Schema**
```bash
GET /search/v1/schema
```
**Description**: Get API schemas and available categories (follows workflow service pattern)  
**Response**: Request/response schemas and search categories

#### **2. Search Operations**
```bash
POST /search/v1/query
```
**Description**: Perform search across MongoDB collections  
**Request Body**:
```json
{
  "teamId": "6511868aa28b1404f6a629cb",
  "query": "assistant",
  "categories": ["assistant"],
  "limit": 10
}
```

**Response**:
```json
{
  "teamId": "6511868aa28b1404f6a629cb",
  "query": "assistant",
  "results": [
    {
      "id": "507f1f77bcf86cd799439011",
      "category": "assistant",
      "name": "Kt Assistant Bot",
      "teamId": "6511868aa28b1404f6a629cb",
      "score": 5.2,
      "match_type": "atlas_search",
      "highlights": [
        {
          "path": "name",
          "texts": [
            {
              "value": "Kt ",
              "type": "text"
            },
            {
              "value": "Assistant",
              "type": "hit"
            },
            {
              "value": " Bot",
              "type": "text"
            }
          ]
        }
      ]
    }
  ],
  "total": 1,
  "categories_searched": ["assistant"],
  "search_time_ms": 45.2
}
```

#### **3. Available Categories**
```bash
GET /search/v1/categories
```
**Description**: View available frontend categories for search  
**Response**: List of available search categories

#### **4. Health Check**
```bash
GET /search/healthcheck
```
**Description**: Check if service is running

#### **5. Log Level Management**
```bash
GET /search/update_log_level?level=info
```
**Description**: Update service log level dynamically (supports: debug, info, warning, error, critical)

### **Frontend Integration Example**
```typescript
const SEARCH_SERVICE_BASE = '/search/v1';

// Perform search
const searchResults = await fetch(`${SEARCH_SERVICE_BASE}/query`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    teamId: '6511868aa28b1404f6a629cb',
    query: 'assistant',
    categories: ['assistant'],
    limit: 10
  })
});

// Get available categories
const categories = await fetch(`${SEARCH_SERVICE_BASE}/categories`);

// Get service schema
const schema = await fetch(`${SEARCH_SERVICE_BASE}/schema`);
```

## ⚙️ **Configuration**

### **Single Source of Truth**
All search configuration is centralized in `app/settings/settings.py` - no environment variables needed for search behavior. The service uses raw MongoDB collections directly, so no Beanie models are required.

### **Environment Variables**
```bash
# MongoDB Connection
MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/interactly
```

### **Search Configuration**
```python
# app/settings/settings.py

# Define which collections to search (single source of truth)
SEARCH_CATEGORIES = [
    "bots", "knowledgebase", "tools", "wf_workflows"
]

# Advanced field configuration with type safety
@dataclass
class FieldConfig:
    path: str  # Field path (e.g., "name", "function.name")
    field_type: str  # Atlas Search field type (autocomplete, string, keyword, etc.)
    boost: Optional[float] = None  # Optional boost value for scoring
    fuzzy: Optional[Dict[str, Any]] = None  # Optional fuzzy matching config

@dataclass
class CollectionSearchConfig:
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
        team_id_field="teamId",
        display_name_field="name"
    ),
    "tools": CollectionSearchConfig(
        searchable_fields=[
            FieldConfig(
                path="function.name",
                field_type="autocomplete",
                boost=5.0,
                fuzzy={"maxEdits": 1, "prefixLength": 1, "maxExpansions": 50}
            )
        ],
        returnable_fields=["_id", "function.name", "teamId"],
        team_id_field="teamId",
        display_name_field="function.name"
    ),
    "wf_workflows": CollectionSearchConfig(
        searchable_fields=[
            FieldConfig(
                path="workflow_config.name",
                field_type="autocomplete",
                boost=5.0,
                fuzzy={"maxEdits": 1, "prefixLength": 1, "maxExpansions": 50}
            )
        ],
        returnable_fields=["_id", "workflow_config.name", "team_id"],
        team_id_field="team_id",  # Different team ID field name
        display_name_field="workflow_config.name"
    )
}

# Atlas Search Index Configuration
ATLAS_SEARCH_INDEXES = {
    "bots": {
        "enabled": True,
        "index_name": "bots_search_index",
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
    "wf_workflows": {
        "enabled": True,
        "index_name": "wf_workflows_search_index",
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
FRONTEND_BACKEND_MAPPER = {
    "assistant": "bots",
    "knowledge": "knowledgebase",
    "tools": "tools",
    "workflows": "wf_workflows"
}

# Reverse mapper for responses
BACKEND_FRONTEND_MAPPER = {
    "bots": "assistant",
    "knowledgebase": "knowledge",
    "tools": "tools",
    "wf_workflows": "workflows"
}
```

### **How Field Management Works**

#### **Advanced Field Configuration**
- **Type Safety**: Uses dataclasses for compile-time type checking
- **Nested Field Support**: Handles nested fields like `function.name` and `workflow_config.name`
- **Multiple Field Types**: Same field can have multiple search strategies (autocomplete + string)
- **Boost Values**: Configurable relevance scoring per field type
- **Fuzzy Matching**: Per-field fuzzy matching configuration

#### **Searchable Fields (`FieldConfig`)**
- **Purpose**: Fields that will be used for search operations with type-specific configuration
- **Example**: `FieldConfig(path="name", field_type="autocomplete", boost=5.0)`
- **Multiple Types**: Same field can have both autocomplete and string search strategies
- **Nested Fields**: Supports dot notation like `function.name` and `workflow_config.name`

#### **Returnable Fields (`returnable_fields`)**
- **Purpose**: Fields that will be returned in search results
- **Example**: `["_id", "name", "teamId"]` for bots
- **Automatic**: `id`, `category`, `score`, and `match_type` are always included
- **Standardized**: All results include a consistent `name` field for frontend simplicity

#### **Team ID Field Mapping (`team_id_field`)**
- **Purpose**: Configurable team ID field name per collection
- **Example**: `"teamId"` for bots, `"team_id"` for workflows
- **ObjectId Support**: Automatically converts string teamId to ObjectId when needed
- **Dynamic**: Each collection can use different team ID field names and types

#### **Display Name Field (`display_name_field`)**
- **Purpose**: Standardized field name for consistent frontend display
- **Example**: `"name"` for bots, `"function.name"` for tools
- **Frontend Consistency**: All results have a `name` field regardless of collection
- **Backward Compatibility**: Original fields are preserved in response

### **How Category Mapping Works**

#### **Frontend Names (What Users See)**
- **assistant** → Maps to backend collection **bots**

#### **API Usage Examples**
```json
# Frontend sends "assistant" category
{
  "teamId": "team123",
  "query": "bot",
  "categories": ["assistant"]
}

# Backend searches "bots" collection
# Response shows "assistant" in categories_searched
```

## 🔍 **Search Capabilities**

### **Atlas Search Query Structure**
- **Compound Query**: Uses MongoDB Atlas Search compound queries for optimal performance
- **Filter Clause**: `teamId` filtering handled in `filter` clause (not affecting relevance scoring)
- **Should Clause**: Search conditions in `should` clause with `minimumShouldMatch: 1`
- **Empty Query Protection**: Automatically returns no results for empty queries

### **Autocomplete Search**
- **nGram Tokenization**: Breaks text into 2-15 character chunks
- **Fuzzy Matching**: Handles typos with 1 character edit distance
- **Token Order**: Matches tokens in any order for flexible searching
- **Diacritic Folding**: Handles accented characters automatically

### **Search Highlights**
- **Automatic Highlighting**: Shows exactly which parts of the text matched your query
- **Field-Specific**: Highlights are provided for each searchable field
- **Text Fragments**: Returns both matched and unmatched text portions
- **Visual Indicators**: Use `type: "hit"` to highlight matched portions in your UI

### **Search Examples**
```bash
# Search for "Kt" (partial match)
POST /searches
{
  "teamId": "team123",
  "query": "Kt",
  "categories": ["assistant"]
}

# Search for "assistant" (full word)
POST /searches
{
  "teamId": "team123",
  "query": "assistant",
  "categories": ["assistant"]
}

# Search with typo "assistant" (fuzzy match)
POST /searches
{
  "teamId": "team123",
  "query": "assistant",
  "categories": ["assistant"]
}

# Empty query protection (returns no results)
POST /searches
{
  "teamId": "team123",
  "query": "",
  "categories": ["assistant"]
}
```

## 🚀 **Setup and Installation**

### **Prerequisites**
- MongoDB Atlas cluster with Atlas Search enabled
- Python 3.10+
- Docker (for containerized deployment)

### **Environment Setup**
```bash
# Copy environment template
cp sample_envs.txt .env

# Edit .env with your MongoDB Atlas connection string
MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/interactly
```

### **Docker Deployment**
```bash
# Build and run with Docker
make dockerize_search_service VERSION=1.0.0
make start_search_service VERSION=1.0.0

# Or manually
docker build -t search_service:latest -f dockerfile .
docker run -d --name search_service -p 8000:8000 --env-file .env search_service:latest
```

### **Local Development**
```bash
# Install dependencies
pipenv install

# Run locally
pipenv run uvicorn search_service.app.main:app --reload --host 0.0.0.0 --port 8000
```

## 📊 **Performance Characteristics**

### **Search Performance**
- **Response Time**: Typically 50-150ms for most queries
- **Throughput**: Handles multiple concurrent searches efficiently
- **Memory Usage**: Minimal overhead with Atlas Search
- **Scalability**: Scales with MongoDB Atlas cluster size
- **Single Query Execution**: Uses `$facet` to fetch results and count in one database query
- **Collection-Level Sorting**: Results sorted by relevance score within each collection
- **Global Result Merging**: Python-based sorting across collections (efficient for typical result counts)

### **Index Performance**
- **Creation Time**: Indexes created once on startup (5-10 seconds)
- **Storage**: Minimal additional storage for search indexes
- **Maintenance**: Automatic index optimization by Atlas Search
- **Optimized Lookups**: Index definitions fetched once per collection to avoid repeated lookups

## 🔧 **Adding New Collections**

### **Step 1: Update Configuration**
```python
# In app/settings/settings.py

# Add to SEARCH_CATEGORIES
SEARCH_CATEGORIES = ["bots", "users", "workflows"]

# Add new collection configuration
SEARCH_CATEGORIES_CONFIG: Dict[str, CollectionSearchConfig] = {
    "bots": { /* existing config */ },
    "users": CollectionSearchConfig(
        searchable_fields=[
            FieldConfig(
                path="name",
                field_type="autocomplete",
                boost=5.0,
                fuzzy={"maxEdits": 1, "prefixLength": 1, "maxExpansions": 50}
            ),
            FieldConfig(
                path="email",
                field_type="string",
                boost=2.0,
                fuzzy={"maxEdits": 1, "prefixLength": 1}
            )
        ],
        returnable_fields=["_id", "name", "email", "teamId"],
        team_id_field="teamId",  # or "team_id" if different
        display_name_field="name"
    ),
    "workflows": CollectionSearchConfig(
        searchable_fields=[
            FieldConfig(
                path="workflow_config.name",
                field_type="autocomplete",
                boost=5.0,
                fuzzy={"maxEdits": 1, "prefixLength": 1, "maxExpansions": 50}
            )
        ],
        returnable_fields=["_id", "workflow_config.name", "team_id"],
        team_id_field="team_id",  # Different team ID field
        display_name_field="workflow_config.name"
    )
}

# Add index configuration
ATLAS_SEARCH_INDEXES = {
    "bots": { /* existing config */ },
    "users": {
        "enabled": True,
        "index_name": "users_search_index",
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
                    "email": {"type": "string"},
                    "teamId": {"type": "token"}
                }
            }
        }
    },
    "workflows": {
        "enabled": True,
        "index_name": "workflows_search_index",
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
                    "team_id": {"type": "objectId"}  # ObjectId if needed
                }
            }
        }
    }
}

# Add category mapping
FRONTEND_BACKEND_MAPPER = {
    "assistant": "bots",
    "user": "users",
    "workflow": "workflows"
}
```

### **Step 2: Restart Service**
```bash
# Restart to create new indexes
docker restart search_service
```

### **Step 3: Test New Collection**
```bash
# Search in new collection
POST /searches
{
  "teamId": "team123",
  "query": "john",
  "categories": ["user"]
}
```

## 🐛 **Troubleshooting**

### **Common Issues**

#### **Index Creation Failed**
```bash
# Check logs for index creation errors
docker logs search_service | grep "index"

# Verify Atlas Search permissions
# Ensure user has "Atlas Search Editor" role
```

#### **Empty Query Handling**
```bash
# Empty queries automatically return no results
# This is expected behavior - add validation in frontend if needed
# Check logs for "Empty query provided" warnings
```

#### **Search Returns No Results**
```bash
# Check if index exists
# Verify searchable fields configuration
# Ensure teamId filtering is correct
```

#### **Connection Issues**
```bash
# Verify MONGODB_URL format
# Check network connectivity to Atlas
# Ensure cluster is running
```

### **Debug Mode**
```bash
# Enable debug logging
PUT /log-level
{
  "level": "DEBUG"
}
```

## 📈 **Monitoring and Logging**

### **Log Levels**
- **INFO**: Normal operation and search results
- **WARNING**: Configuration issues, non-critical errors, and empty query warnings
- **ERROR**: Search failures and critical issues (wrapped in SearchException)
- **DEBUG**: Detailed search query and response information

### **Key Metrics**
- **Search Response Time**: Tracked in `search_time_ms`
- **Result Counts**: Total results and per-collection counts
- **Index Status**: Index creation and update status
- **Error Rates**: Failed searches and connection issues

## 🔮 **Future Enhancements**

### **Planned Features**
- **Multi-language Support**: Internationalization for search queries
- **Advanced Filtering**: Date ranges, numeric filters, and complex queries
- **Search Analytics**: Query patterns and result click-through rates
- **Real-time Updates**: Live index updates without service restart

### **Scalability Improvements**
- **$unionWith Optimization**: MongoDB-based global sorting for large result sets across collections
- **Caching Layer**: Redis-based result caching for popular queries
- **Load Balancing**: Multiple search service instances
- **CDN Integration**: Global search service distribution

## 📚 **API Reference**

### **Search Request Model**
```python
class SearchRequest(BaseModel):
    teamId: str                    # Required: Team ID for filtering
    query: str                     # Required: Search query string
    categories: Optional[List[str]] # Optional: Specific categories to search
    limit: Optional[int]           # Optional: Maximum results (1-100, default 50)
```

### **Search Response Model**
```python
class SearchResponse(BaseModel):
    teamId: str                    # Team ID that was searched
    query: str                     # Original search query
    results: List[SearchResult]    # List of search results
    total: int                     # Total number of results found
    categories_searched: List[str] # Categories that were searched
    search_time_ms: float          # Search execution time
```

### **Search Result Model**
```python
class SearchResult(BaseModel):
    id: str                        # Unique identifier
    category: str                  # Frontend category name (e.g., 'assistant')
    score: float                   # Relevance score from Atlas Search (direct from MongoDB)
    match_type: str                # Type of match (always "atlas_search")
    highlights: Optional[List]     # Search highlights showing matched text fragments
    # Additional fields based on RETURNABLE_FIELDS_CONFIG
```

## 🤝 **Contributing**

### **Development Guidelines**
- Follow existing code structure and patterns
- Add comprehensive logging for new features
- Update configuration documentation
- Test with multiple collections and field types

### **Testing**
```bash
# Run tests
pipenv run pytest

# Test specific functionality
pipenv run pytest tests/test_search.py
```

---

**Built with ❤️ using FastAPI, MongoDB Atlas Search, and modern Python practices.**