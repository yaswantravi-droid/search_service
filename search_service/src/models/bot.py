from beanie import Document


class Bot(Document):
    """Simple model for bots collection - Atlas Search handles all search functionality."""
    
    class Settings:
        name = "bots"
        # No special indexes needed - Atlas Search handles everything
        # Return fields are managed in settings.py via RETURNABLE_FIELDS_CONFIG
