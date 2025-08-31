"""Database connection manager using Beanie and Motor."""

# Standard library imports
import asyncio
import traceback

# Third-party imports
from typing import Optional, Sequence, Union

from beanie import Document, UnionDoc, View, init_beanie
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.database import Database as PyMongoDatabase

# Local application imports
import logging

# Setup basic logging
logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Manages the connection to MongoDB and handles initialization of Beanie models.
    Provides an easy-to-use interface for connecting, interacting with, and closing the MongoDB connection.
    """

    def __init__(
        self,
        document_models: Sequence[type[Document] | type[UnionDoc] | type[View] | str] | None = None,
    ):
        """
        Initialize the database manager with optional document models for Beanie ORM.
        """
        self._client: Optional[AsyncIOMotorClient] = None
        self._db: Optional[AsyncIOMotorDatabase] = None
        self._initialized: bool = False
        self._document_models = document_models or []

    async def init(self, connection_string: str):
        """
        Initialize the MongoDB connection using the provided connection string.
        The connection string will contain all necessary details for connecting.
        """
        if self._initialized:
            logger.warning("DatabaseManager is already initialized.")
            return

        if not connection_string:
            logger.error("Connection string is required for database initialization.")
            raise ValueError("Connection string must be provided to initialize the database.")

        try:
            # Initialize the MongoDB client and get the default database
            self._client = AsyncIOMotorClient(connection_string)
            self._client.get_io_loop = asyncio.get_event_loop
            self._db = self._client.get_default_database()

            # Initialize Beanie with the provided database and models
            await init_beanie(database=self._db, document_models=self._document_models)
            self._initialized = True
            logger.info("Database initialized successfully.")

        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")

    async def close(self):
        """
        Cleanly closes the MongoDB client connection.
        """
        if self._client:
            self._client.close()
            self._client = None
            self._initialized = False
            logger.info("MongoDB client closed.")

    @property
    def db(self) -> Optional[Union[AsyncIOMotorDatabase, PyMongoDatabase]]:
        """
        Get the current MongoDB database connection.

        Returns:
            Union[AsyncIOMotorDatabase, PyMongoDatabase]: The database instance connected to MongoDB.
            Returns None if the database has not been initialized.
        """
        return self._db

    @property
    def is_initialized(self) -> bool:
        """
        Check if the database has been initialized.

        Returns:
            True if the database connection has been established and models are registered.
        """
        return self._initialized
