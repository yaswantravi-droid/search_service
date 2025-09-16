from common.logging.custom_logger import logger
from search_service.app.lifespan.startup import mongo_db


async def disconnect_db():
    """Cleanly close the database connection."""
    await mongo_db.close()
    logger.info("Search service database connection closed.")
