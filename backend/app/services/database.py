from typing import List, Optional
import logging
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from pymongo.errors import DuplicateKeyError
from datetime import datetime

from ..config import settings
from ..models.user import UserInDB, LeaderboardEntry

logger = logging.getLogger(__name__)


class DatabaseService:
    """Service for MongoDB operations"""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.database: Optional[AsyncIOMotorDatabase] = None
        self.collection: Optional[AsyncIOMotorCollection] = None

    async def connect(self):
        """Connect to MongoDB"""
        try:
            self.client = AsyncIOMotorClient(settings.mongodb_uri)
            self.database = self.client[settings.mongodb_database]
            self.collection = self.database[settings.mongodb_collection]
            
            # Test connection
            await self.client.admin.command('ping')
            logger.info(f"Connected to MongoDB: {settings.mongodb_database}")
            
            # Create index on puuid for faster queries
            await self.collection.create_index("puuid", unique=True)
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    async def disconnect(self):
        """Disconnect from MongoDB"""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")

    async def create_user(self, user_data: UserInDB) -> UserInDB:
        """Create a new user in the database"""
        try:
            user_dict = user_data.model_dump()
            user_dict["_id"] = user_data.puuid  # Use PUUID as MongoDB _id
            
            result = await self.collection.insert_one(user_dict)
            logger.info(f"Created user with PUUID: {user_data.puuid}")
            return user_data
            
        except DuplicateKeyError:
            logger.warning(f"User with PUUID {user_data.puuid} already exists")
            raise ValueError(f"User with PUUID {user_data.puuid} already exists")
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            raise

    async def get_user_by_puuid(self, puuid: str) -> Optional[UserInDB]:
        """Get user by PUUID"""
        try:
            user_doc = await self.collection.find_one({"puuid": puuid})
            if user_doc:
                # Remove MongoDB _id field and convert to UserInDB
                user_doc.pop("_id", None)
                return UserInDB(**user_doc)
            return None
        except Exception as e:
            logger.error(f"Failed to get user by PUUID {puuid}: {e}")
            raise

    async def update_user(self, puuid: str, user_data: UserInDB) -> Optional[UserInDB]:
        """Update existing user data"""
        try:
            user_dict = user_data.model_dump()
            user_dict["updated_at"] = datetime.utcnow()
            
            result = await self.collection.replace_one(
                {"puuid": puuid}, 
                user_dict
            )
            
            if result.modified_count > 0:
                logger.info(f"Updated user with PUUID: {puuid}")
                return user_data
            return None
            
        except Exception as e:
            logger.error(f"Failed to update user {puuid}: {e}")
            raise

    async def get_leaderboard(
        self, 
        page: int = 1, 
        per_page: int = 50
    ) -> tuple[List[LeaderboardEntry], int]:
        """Get leaderboard data with pagination - filtering null data and inactive users"""
        try:
            from datetime import datetime, timedelta
            
            skip = (page - 1) * per_page
            
            # Calculate the cutoff date (2 weeks ago)
            two_weeks_ago = datetime.utcnow() - timedelta(weeks=2)
            
            # Pipeline for aggregating leaderboard data
            pipeline = [
                {
                    "$match": {
                        "$and": [
                            # Must have ELO data
                            {
                                "$or": [
                                    {"rank_details.data.elo": {"$exists": True, "$ne": None}},
                                    {"rank_details.elo": {"$exists": True, "$ne": None}}
                                ]
                            },
                            # Must have played within last 2 weeks OR have no last_played_match field (backward compatibility)
                            {
                                "$or": [
                                    {"last_played_match": {"$gte": two_weeks_ago.isoformat()}},
                                    {"last_played_match": {"$exists": False}}  # Include users without this field for backward compatibility
                                ]
                            }
                        ]
                    }
                },
                {
                    "$project": {
                        "puuid": 1,
                        "name": 1,
                        "tag": 1,
                        "discord_username": 1,
                        "current_tier": {
                            "$ifNull": ["$rank_details.data.currenttierpatched", "$rank_details.currenttierpatched"]
                        },
                        "elo": {
                            "$ifNull": ["$rank_details.data.elo", "$rank_details.elo"]
                        },
                        "rank_in_tier": {
                            "$ifNull": ["$rank_details.data.ranking_in_tier", "$rank_details.ranking_in_tier"]
                        },
                        "peak_rank": "$peak_rank.tier_name",
                        "peak_season": "$peak_rank.season_short",
                        "last_played_match": 1
                    }
                },
                {
                    "$sort": {
                        "elo": -1  # Sort by ELO descending
                    }
                },
                {
                    "$skip": skip
                },
                {
                    "$limit": per_page
                }
            ]
            
            # Get leaderboard entries
            cursor = self.collection.aggregate(pipeline)
            entries_data = await cursor.to_list(length=per_page)
            
            # Convert to LeaderboardEntry objects with error handling
            entries = []
            for i, entry in enumerate(entries_data):
                try:
                    entries.append(LeaderboardEntry(**entry))
                except Exception as e:
                    logger.error(f"Failed to create LeaderboardEntry for record {i+skip+1}: {entry}")
                    logger.error(f"Validation error: {e}")
                    # Skip this entry instead of failing the entire request
                    continue
            
            # Get total count of active users with ELO (both structures)
            total = await self.collection.count_documents({
                "$and": [
                    # Must have ELO data
                    {
                        "$or": [
                            {"rank_details.data.elo": {"$exists": True, "$ne": None}},
                            {"rank_details.elo": {"$exists": True, "$ne": None}}
                        ]
                    },
                    # Must have played within last 2 weeks
                    {
                        "$or": [
                            {"last_played_match": {"$gte": two_weeks_ago.isoformat()}},
                            {"last_played_match": {"$exists": False}},  # Include users without this field for backward compatibility
                            {"last_played_match": None}  # Include null values for backward compatibility
                        ]
                    }
                ]
            })
            
            logger.info(f"Retrieved leaderboard page {page} with {len(entries)} entries")
            return entries, total
            
        except Exception as e:
            logger.error(f"Failed to get leaderboard: {e}")
            raise

    async def get_user_by_discord_id(self, discord_id: int) -> Optional[UserInDB]:
        """Get user by Discord ID"""
        try:
            user_doc = await self.collection.find_one({"discord_id": discord_id})
            if user_doc:
                # Remove MongoDB _id field
                user_doc.pop("_id", None)
                try:
                    return UserInDB(**user_doc)
                except Exception as validation_error:
                    logger.warning(f"User {discord_id} exists in DB but failed UserInDB validation: {validation_error}")
                    # Return a simplified object that indicates the user exists
                    # This allows the auth flow to detect existing users even with incomplete data
                    from types import SimpleNamespace
                    simple_user = SimpleNamespace()
                    simple_user.puuid = user_doc.get("puuid", "")
                    simple_user.name = user_doc.get("name", "")
                    simple_user.tag = user_doc.get("tag", "")
                    simple_user.discord_id = user_doc.get("discord_id")
                    simple_user.discord_username = user_doc.get("discord_username", "")

                    # Handle different rank_details structures
                    rank_details = user_doc.get("rank_details", {})
                    if isinstance(rank_details, dict):
                        if "data" in rank_details:
                            # Legacy structure: rank_details.data.currenttierpatched
                            current_rank = rank_details.get("data", {}).get("currenttierpatched")
                        else:
                            # New structure: rank_details.currenttierpatched
                            current_rank = rank_details.get("currenttierpatched")
                    else:
                        current_rank = None

                    simple_user.rank_details = SimpleNamespace()
                    simple_user.rank_details.data = SimpleNamespace()
                    simple_user.rank_details.data.currenttierpatched = current_rank

                    return simple_user
            return None
        except Exception as e:
            logger.error(f"Failed to get user by Discord ID {discord_id}: {e}")
            raise

    async def user_exists(self, puuid: str) -> bool:
        """Check if user exists by PUUID"""
        try:
            count = await self.collection.count_documents({"puuid": puuid})
            return count > 0
        except Exception as e:
            logger.error(f"Failed to check user existence {puuid}: {e}")
            raise


# Global database service instance
db_service = DatabaseService()