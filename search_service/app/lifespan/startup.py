from common.logging.custom_logger import logger
from search_service.app.settings.settings import MONGODB_URL
from search_service.src.db.connection import DatabaseManager
from search_service.src.models import Bot
from search_service.utils.atlas_index_manager import initialize_atlas_indexes

# Initialize database manager for search service
mongo_db = DatabaseManager(document_models=[Bot])


async def connect_db():
    """Initialize database connection for search service."""
    if not MONGODB_URL:
        logger.error("MONGODB_URL environment variable not set.")
        raise ValueError("MONGODB_URL environment variable must be set.")
    
    # Check if it's MongoDB Atlas (required for Atlas Search)
    if not MONGODB_URL.startswith("mongodb+srv://"):
        logger.error("MongoDB Atlas connection required for Atlas Search!")
        logger.error("Your connection string starts with 'mongodb://' which is regular MongoDB")
        logger.error("Atlas Search requires 'mongodb+srv://' connection to MongoDB Atlas")
        raise ValueError("MongoDB Atlas connection required for Atlas Search. Use 'mongodb+srv://' URL.")
    
    logger.info(f"Initializing database connection with MongoDB Atlas URL: {MONGODB_URL}")
    await mongo_db.init(MONGODB_URL)
    logger.info("Search service database connection established successfully.")
    
    # Try to initialize Atlas Search indexes using our manager
    try:
        logger.info("Attempting to create/update Atlas Search indexes using AtlasIndexManager...")
        
        # Ensure database is initialized before creating indexes
        if mongo_db.is_initialized and mongo_db.db is not None:
            await initialize_atlas_indexes(mongo_db.db)
            logger.info("Atlas Search indexes created/updated successfully.")
        else:
            logger.warning("Database not initialized yet, skipping Atlas Search index creation")
            
    except Exception as e:
        logger.error(f"Failed to create/update Atlas Search indexes: {str(e)}")
        logger.error("Service cannot start without Atlas Search indexes (per configuration)")
        logger.error("Please check your Atlas Search permissions and configuration")
        raise e  # Re-raise to prevent service from starting without Atlas Search
    
    logger.info("Bot model registered - Atlas Search indexes created/updated successfully.")
