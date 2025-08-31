"""
Atlas Search Index Manager
Handles creation/upsert of Atlas Search indexes for all configured collections.
Called once on application startup.
"""

from typing import Dict, Any, List
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection
from pymongo.operations import SearchIndexModel
from common.logging.custom_logger import logger
from search_service.app.settings.settings import ATLAS_SEARCH_INDEXES


class AtlasIndexManager:
    """Manages Atlas Search index upsert (create or update) for configured collections."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def create_all_indexes(self):
        """Create or update Atlas Search indexes for all configured collections."""
        logger.info("Starting Atlas Search index upsert (create/update)...")

        enabled_indexes = [name for name, cfg in ATLAS_SEARCH_INDEXES.items() if cfg.get("enabled", False)]
        if not enabled_indexes:
            logger.warning("No enabled Atlas Search indexes found in configuration")
            return

        logger.info(f"Found {len(enabled_indexes)} enabled collections for index upsert: {enabled_indexes}")

        success_count = 0
        total_count = 0

        for collection_name, index_config in ATLAS_SEARCH_INDEXES.items():
            if not index_config.get("enabled", False):
                logger.info(f"Skipping disabled collection: {collection_name}")
                continue

            total_count += 1
            try:
                await self._upsert_collection_index(collection_name, index_config)
                success_count += 1
            except Exception as e:
                logger.error(f"Failed to upsert index for {collection_name}: {str(e)}")

        if success_count == total_count and total_count > 0:
            logger.info(f"Atlas Search index upsert completed successfully - {success_count}/{total_count}")
        elif success_count > 0:
            logger.warning(f"Atlas Search index upsert partially completed - {success_count}/{total_count}")
        else:
            logger.error(f"Atlas Search index upsert failed - 0/{total_count}")
            raise Exception("No Atlas Search indexes were created or updated successfully")

    async def _upsert_collection_index(self, collection_name: str, index_config: Dict[str, Any]):
        """Create or update Atlas Search index for a specific collection."""
        logger.info(f"Upserting Atlas Search index for collection: {collection_name}")

        if "index_name" not in index_config:
            raise ValueError(f"Missing 'index_name' in index configuration for '{collection_name}'")
        if "searchable_fields" not in index_config:
            raise ValueError(f"Missing 'searchable_fields' in index configuration for '{collection_name}'")

        index_name = index_config["index_name"]
        index_definition = self._build_index_definition(index_config)

        collection: AsyncIOMotorCollection = self.db[collection_name]

        # 1) Check existing search indexes on the collection
        try:
            existing_indexes = await collection.aggregate([{"$listSearchIndexes": {}}]).to_list(length=None)
        except Exception as e:
            logger.error(f"Could not list search indexes for collection '{collection_name}': {str(e)}")
            raise

        existing_names = [idx.get("name") for idx in existing_indexes if isinstance(idx, dict) and idx.get("name")]
        logger.debug(f"Existing search indexes for '{collection_name}': {existing_names}")

        # 2) If index exists -> update it. Otherwise -> create it.
        if index_name in existing_names:
            logger.info(f"Index '{index_name}' already exists on '{collection_name}', attempting update...")
            try:
                # Create SearchIndexModel for update
                search_index_model = SearchIndexModel(
                    definition=index_definition,
                    name=index_name
                )
                await collection.update_search_index(
                    name=index_name,
                    definition=index_definition
                )
                logger.info(f"Atlas Search index '{index_name}' updated successfully for collection '{collection_name}'")
                return
            except Exception as update_err:
                logger.error(f"Failed to update search index '{index_name}' on '{collection_name}': {str(update_err)}")
                raise

        # Index doesn't exist -> create it
        logger.info(f"Index '{index_name}' not found on '{collection_name}', attempting create...")
        try:
            # Create SearchIndexModel and use it to create the index
            search_index_model = SearchIndexModel(
                definition=index_definition,
                name=index_name
            )
            await collection.create_search_index(search_index_model)
            logger.info(f"Atlas Search index '{index_name}' created successfully for collection '{collection_name}'")
        except Exception as create_err:
            logger.error(f"Failed to create search index '{index_name}' on '{collection_name}': {str(create_err)}")
            raise


    def _build_index_definition(self, index_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get the static index definition from configuration.
        
        The index definition is now statically defined in settings for each collection.
        """
        # Check if static index definition is provided in config
        if "index_definition" in index_config:
            logger.info(f"Using static index definition for '{index_config.get('index_name')}'")
            return index_config["index_definition"]
        
        # Fallback to dynamic definition if no static one is provided
        logger.warning(f"No static index definition found for '{index_config.get('index_name')}', using fallback")
        
        searchable_fields: List[str] = index_config.get("searchable_fields", [])
        if not searchable_fields:
            raise ValueError("No searchable fields configured for Atlas Search index")

        mappings_fields: Dict[str, Any] = {}

        for field in searchable_fields:
            # Skip teamId as your code uses it purely for filtering
            if field == "teamId":
                continue

            # define subfields as documented by Atlas Search mapping model
            mappings_fields[field] = {
                "type": "string"
            }

        if not mappings_fields:
            raise ValueError("No valid searchable fields found after filtering (all fields may have been filtered out)")

        index_definition = {
            "mappings": {
                "dynamic": False,
                "fields": mappings_fields
            }
        }

        # Allow index-specific settings if provided (e.g., other root-level keys)
        if isinstance(index_config.get("index_settings"), dict):
            # Merge shallow settings (do not overwrite mappings)
            for k, v in index_config["index_settings"].items():
                if k == "mappings":
                    continue
                # Only add if not present
                if k not in index_definition:
                    index_definition[k] = v

        logger.info(f"Built fallback index definition for '{index_config.get('index_name')}' with {len(mappings_fields)} fields")
        return index_definition


async def initialize_atlas_indexes(db: AsyncIOMotorDatabase):
    """Initialize (upsert) all Atlas Search indexes on application startup."""
    manager = AtlasIndexManager(db)
    await manager.create_all_indexes()
