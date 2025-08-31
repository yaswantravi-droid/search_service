# 🔍 **Search Service - Atlas Search Edition**

A high-performance, scalable search service built with **FastAPI** and **MongoDB Atlas Search** that provides Google-like search capabilities with autocomplete and fuzzy matching.

## 🚀 **What This Service Does**

- **Atlas Search Integration**: Uses MongoDB Atlas Search directly with pymongo for lightning-fast, relevant search results
- **Centralized Index Management**: Indexes created once on startup, not during search operations
- **Autocomplete Search**: Google-like search suggestions with fuzzy matching and typo tolerance
- **Team-Based Isolation**: Automatically filters results by team ID for security
- **Configurable Fields**: Easily configure which fields to search and return for each collection
- **Direct Score Usage**: Uses Atlas Search scores directly from MongoDB - no manual calculation

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

### **2. Centralized Configuration**
- **No Code Changes**: Add new collections and fields via configuration
- **Startup Index Creation**: Indexes created once when application starts
- **Flexible Fields**: Configure which fields to search and return
- **Team Isolation**: Automatic filtering by team ID

### **3. Performance & Scalability**
- **O(log n) Performance**: Logarithmic search time regardless of collection size
- **Startup Indexing**: Indexes created once, not during search operations
- **Memory Efficient**: Minimal overhead with Atlas Search
- **Horizontal Scaling**: Scales with your MongoDB Atlas cluster

### **4. Field Management**
- **Searchable Fields**: Configure which fields to index for search
- **Returnable Fields**: Control what data gets returned in search results
- **Dynamic Configuration**: Change field sets without code modifications
- **Team Filtering**: Automatic teamId filtering for all searches

### **5. Frontend-Backend Category Mapping**
- **User-Friendly Names**: Frontend uses "assistant" instead of "bots"
- **Backend Collections**: Backend uses actual collection names like "bots"
- **Automatic Translation**: API automatically maps "assistant" to "bots"
- **Transparent to Frontend**: No changes needed in frontend code when adding collections

## 📡 **API Endpoints**

### **Main Search Endpoint**
```bash
POST /searches
```

**Request Body:**
```json
{
  "teamId": "6511868aa28b1404f6a629cb",
  "query": "Kt",
  "categories": ["assistant"],
  "limit": 10
}
```

**Response:**
```json
{
  "teamId": "6511868aa28b1404f6a629cb",
  "query": "Kt",
  "results": [
    {
      "id": "507f1f77bcf86cd799439011",
      "category": "assistant",
      "name": "Kt Assistant Bot",
      "teamId": "6511868aa28b1404f6a629cb",
      "score": 95.5,
      "match_type": "atlas_search"
    }
  ],
  "total": 1,
  "categories_searched": ["assistant"],
  "search_time_ms": 45.2
}
```

### **Other Endpoints:**
- **Health Check**: `GET /healthcheck` - Check if service is running
- **Welcome**: `GET /` - Basic service information
- **Categories**: `GET /categories` - View available frontend categories for search

## ⚙️ **Configuration**

### **Single Source of Truth**
All search configuration is centralized in `app/settings/settings.py` - no environment variables needed for search behavior.

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
    "bots"  # Add more collections here as needed
]

# Searchable columns for each category
SEARCH_CATEGORIES_CONFIG = {
    "bots": ["name", "teamId"],  # Search bots collection on name and teamId
}

# Returnable fields for each category
RETURNABLE_FIELDS_CONFIG = {
    "bots": [
        "_id", "name", "teamId"  # Return essential fields for bots
    ]
}

# Atlas Search Index Configuration
ATLAS_SEARCH_INDEXES = {
    "bots": {
        "enabled": True,  # Enable index creation from code
        "index_name": "bots_search_index",  # Index name for the collection
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
FRONTEND_BACKEND_MAPPER = {
    "assistant": "bots"  # Frontend: "assistant" -> Backend: "bots"
}

# Reverse mapper for responses
BACKEND_FRONTEND_MAPPER = {
    "bots": "assistant"  # Backend: "bots" -> Frontend: "assistant"
}
```

### **How Field Management Works**

#### **Searchable Fields (`SEARCH_CATEGORIES_CONFIG`)**
- **Purpose**: Fields that will be used for search operations
- **Example**: `["name", "teamId"]` for bots
- **Note**: `teamId` is included for team filtering but not indexed for search

#### **Returnable Fields (`RETURNABLE_FIELDS_CONFIG`)**
- **Purpose**: Fields that will be returned in search results
- **Example**: `["_id", "name", "teamId"]` for bots
- **Automatic**: `id`, `category`, `score`, and `match_type` are always included
- **Dynamic**: You control exactly what data users see in results

#### **Index Fields (`ATLAS_SEARCH_INDEXES`)**
- **Purpose**: Fields that will have Atlas Search indexes created
- **Example**: `["name"]` for bots (excludes `teamId`)
- **Performance**: Only searchable fields get indexes for optimal performance

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

### **Autocomplete Search**
- **nGram Tokenization**: Breaks text into 2-15 character chunks
- **Fuzzy Matching**: Handles typos with 1 character edit distance
- **Token Order**: Matches tokens in any order for flexible searching
- **Diacritic Folding**: Handles accented characters automatically

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

### **Index Performance**
- **Creation Time**: Indexes created once on startup (5-10 seconds)
- **Storage**: Minimal additional storage for search indexes
- **Maintenance**: Automatic index optimization by Atlas Search

## 🔧 **Adding New Collections**

### **Step 1: Update Configuration**
```python
# In app/settings/settings.py

# Add to SEARCH_CATEGORIES
SEARCH_CATEGORIES = ["bots", "users", "workflows"]

# Add searchable fields
SEARCH_CATEGORIES_CONFIG = {
    "bots": ["name", "teamId"],
    "users": ["name", "email", "teamId"],
    "workflows": ["name", "title", "teamId"]
}

# Add returnable fields
RETURNABLE_FIELDS_CONFIG = {
    "bots": ["_id", "name", "teamId"],
    "users": ["_id", "name", "email", "teamId"],
    "workflows": ["_id", "name", "title", "teamId"]
}

# Add index configuration
ATLAS_SEARCH_INDEXES = {
    "bots": { /* existing config */ },
    "users": {
        "enabled": True,
        "index_name": "users_search_index",
        "searchable_fields": ["name", "email"],
        "index_definition": { /* similar to bots */ }
    },
    "workflows": { /* similar config */ }
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
- **WARNING**: Configuration issues and non-critical errors
- **ERROR**: Search failures and critical issues
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
- **Elasticsearch Integration**: Alternative search engine for high-scale deployments
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
    score: float                   # Relevance score from Atlas Search
    match_type: str                # Type of match (always "atlas_search")
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