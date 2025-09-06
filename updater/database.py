import logging
from typing import List, Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection
from pymongo.errors import ConnectionFailure
try:
    from .config import settings
except ImportError:
    from config import settings

logger = logging.getLogger(__name__)


class DatabaseManager:
    """MongoDB database manager for the updater service"""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.collection: Optional[AsyncIOMotorCollection] = None
        
    async def connect(self) -> bool:
        """Connect to MongoDB database"""
        try:
            self.client = AsyncIOMotorClient(settings.mongodb_uri)
            
            # Test the connection
            await self.client.admin.command('ping')
            
            # Get the collection
            database = self.client[settings.mongodb_database]
            self.collection = database[settings.mongodb_collection]
            
            logger.info(f"Successfully connected to MongoDB: {settings.mongodb_database}")
            return True
            
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error connecting to MongoDB: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from MongoDB"""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")
    
    async def get_all_puuids(self) -> List[Dict[str, Any]]:
        """Get all PUUIDs and basic player info from the database"""
        try:
            cursor = self.collection.find(
                {},  # No filter - get all documents
                {
                    "puuid": 1,
                    "name": 1,
                    "tag": 1,
                    "_id": 0
                }
            )
            
            players = await cursor.to_list(length=None)
            logger.info(f"Retrieved {len(players)} players from database")
            return players
            
        except Exception as e:
            logger.error(f"Failed to retrieve PUUIDs from database: {e}")
            return []
    
    async def update_player_data(self, puuid: str, update_data: Dict[str, Any]) -> bool:
        """Update player data in the database"""
        try:
            # Remove region from update data since we don't update it
            update_data.pop('region', None)
            
            result = await self.collection.update_one(
                {"puuid": puuid},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                logger.debug(f"Successfully updated player {puuid}")
                return True
            else:
                logger.warning(f"No changes made to player {puuid} - data might be identical")
                return True  # Still consider it successful
                
        except Exception as e:
            logger.error(f"Failed to update player {puuid}: {e}")
            return False
    
    async def get_player_count(self) -> int:
        """Get total number of players in the database"""
        try:
            count = await self.collection.count_documents({})
            return count
        except Exception as e:
            logger.error(f"Failed to get player count: {e}")
            return 0
    
    async def get_player_by_puuid(self, puuid: str) -> Optional[Dict[str, Any]]:
        """Get a specific player by PUUID"""
        try:
            player = await self.collection.find_one({"puuid": puuid})
            return player
        except Exception as e:
            logger.error(f"Failed to get player {puuid}: {e}")
            return None


# Global database manager instance
db_manager = DatabaseManager()