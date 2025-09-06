"""
Database connection and operations for the ValorantSL Player Updater Service
"""

import logging
from typing import List, Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from datetime import datetime

from .config import config

logger = logging.getLogger(__name__)


class DatabaseService:
    """Service for MongoDB database operations"""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.database: Optional[AsyncIOMotorDatabase] = None
        self.collection: Optional[AsyncIOMotorCollection] = None
    
    async def connect(self) -> None:
        """Connect to MongoDB"""
        try:
            logger.info(f"Connecting to MongoDB: {config.mongodb_database}")
            self.client = AsyncIOMotorClient(config.mongodb_uri)
            self.database = self.client[config.mongodb_database]
            self.collection = self.database[config.mongodb_collection]
            
            # Test connection
            await self.client.admin.command('ping')
            logger.info(f"Successfully connected to MongoDB: {config.mongodb_database}")
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")
    
    async def get_all_puuids(self) -> List[str]:
        """Get all PUUIDs from the database"""
        try:
            cursor = self.collection.find({}, {"puuid": 1, "_id": 0})
            puuids = []
            async for doc in cursor:
                puuids.append(doc["puuid"])
            
            logger.info(f"Retrieved {len(puuids)} PUUIDs from database")
            return puuids
            
        except Exception as e:
            logger.error(f"Failed to get PUUIDs: {e}")
            raise
    
    async def get_player_info(self, puuid: str) -> Optional[Dict[str, Any]]:
        """Get basic player info for logging"""
        try:
            player = await self.collection.find_one(
                {"puuid": puuid}, 
                {"name": 1, "tag": 1, "discord_username": 1, "_id": 0}
            )
            return player
        except Exception as e:
            logger.error(f"Failed to get player info for {puuid}: {e}")
            return None
    
    async def update_player_data(self, puuid: str, update_data: Dict[str, Any]) -> bool:
        """Update player data in the database"""
        try:
            # Add updated timestamp
            update_data["updated_at"] = datetime.utcnow()
            
            result = await self.collection.update_one(
                {"puuid": puuid},
                {"$set": update_data}
            )
            
            if result.matched_count == 0:
                logger.warning(f"No player found with PUUID: {puuid}")
                return False
            elif result.modified_count == 0:
                logger.debug(f"No changes needed for player: {puuid}")
                return True
            else:
                logger.debug(f"Updated player data for PUUID: {puuid}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to update player {puuid}: {e}")
            return False
    
    async def get_update_statistics(self) -> Dict[str, Any]:
        """Get database statistics for monitoring"""
        try:
            total_players = await self.collection.count_documents({})
            
            # Get players updated in last hour
            one_hour_ago = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
            recently_updated = await self.collection.count_documents({
                "updated_at": {"$gte": one_hour_ago}
            })
            
            return {
                "total_players": total_players,
                "recently_updated": recently_updated,
                "last_check": datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Failed to get update statistics: {e}")
            return {}


# Global database service instance
db_service = DatabaseService()