from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Setup custom logging (same standard as workflow service)
from common.logging.custom_logger import logger

router = APIRouter()


class LogLevelUpdate(BaseModel):
    level: str


@router.put("/log-level")
async def update_log_level(log_level_update: LogLevelUpdate):
    """
    Update the logging level dynamically.
    """
    level = log_level_update.level.upper()
    
    if level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        raise HTTPException(status_code=400, detail="Invalid log level")
    
    # Update the custom logger level
    logger.setLevel(level)
    
    logger.info(f"Log level updated to {level}")
    return {"message": f"Log level updated to {level}", "level": level}
