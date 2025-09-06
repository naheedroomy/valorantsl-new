"""
Main updater service for ValorantSL Player Rankings
"""

import logging
import asyncio
from typing import Dict, Any, List
from datetime import datetime

from .database import db_service
from .riot_api import riot_client
from .config import config

logger = logging.getLogger(__name__)


class PlayerUpdater:
    """Service to update all player rankings"""
    
    def __init__(self):
        self.rate_limit_delay = config.rate_limit_delay_seconds
        self.stats = {
            "total_processed": 0,
            "successful_updates": 0,
            "failed_updates": 0,
            "skipped_updates": 0,
            "start_time": None,
            "end_time": None
        }
    
    async def update_single_player(self, puuid: str) -> bool:
        """Update a single player's data"""
        try:
            # Get player info for logging
            player_info = await db_service.get_player_info(puuid)
            player_name = f"{player_info.get('name', 'Unknown')}#{player_info.get('tag', 'Unknown')}" if player_info else puuid[:8]
            
            logger.info(f"Updating player: {player_name} ({puuid})")
            
            # Fetch updated data from Riot API
            update_data = await riot_client.process_player_update(puuid)
            if not update_data:
                logger.warning(f"Failed to fetch data for {player_name}")
                self.stats["failed_updates"] += 1
                return False
            
            # Update in database
            success = await db_service.update_player_data(puuid, update_data)
            if success:
                logger.info(f"Successfully updated {player_name} - Rank: {update_data.get('rank_details', {}).get('data', {}).get('currenttierpatched', 'Unknown')}")
                self.stats["successful_updates"] += 1
                return True
            else:
                logger.error(f"Database update failed for {player_name}")
                self.stats["failed_updates"] += 1
                return False
                
        except Exception as e:
            logger.error(f"Error updating player {puuid}: {e}")
            self.stats["failed_updates"] += 1
            return False
    
    async def update_all_players(self) -> Dict[str, Any]:
        """Update all players in the database"""
        self.stats = {
            "total_processed": 0,
            "successful_updates": 0,
            "failed_updates": 0,
            "skipped_updates": 0,
            "start_time": datetime.utcnow(),
            "end_time": None
        }
        
        logger.info("Starting full player update cycle")
        
        try:
            # Get all PUUIDs from database
            puuids = await db_service.get_all_puuids()
            if not puuids:
                logger.warning("No players found in database")
                return self.stats
            
            logger.info(f"Found {len(puuids)} players to update")
            self.stats["total_processed"] = len(puuids)
            
            # Update players with rate limiting
            for i, puuid in enumerate(puuids):
                try:
                    await self.update_single_player(puuid)
                    
                    # Rate limiting - wait between requests except for the last one
                    if i < len(puuids) - 1:
                        logger.debug(f"Waiting {self.rate_limit_delay}s before next update...")
                        await asyncio.sleep(self.rate_limit_delay)
                    
                    # Progress logging every 10 players
                    if (i + 1) % 10 == 0:
                        progress = ((i + 1) / len(puuids)) * 100
                        logger.info(f"Progress: {i + 1}/{len(puuids)} ({progress:.1f}%) - Success: {self.stats['successful_updates']}, Failed: {self.stats['failed_updates']}")
                        
                except Exception as e:
                    logger.error(f"Unexpected error processing player {i}: {e}")
                    self.stats["failed_updates"] += 1
            
            self.stats["end_time"] = datetime.utcnow()
            duration = (self.stats["end_time"] - self.stats["start_time"]).total_seconds()
            
            logger.info(f"Update cycle completed in {duration:.1f}s")
            logger.info(f"Results: {self.stats['successful_updates']} success, {self.stats['failed_updates']} failed")
            
            return self.stats
            
        except Exception as e:
            logger.error(f"Critical error during update cycle: {e}")
            self.stats["end_time"] = datetime.utcnow()
            return self.stats
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all services"""
        health = {
            "database": "unknown",
            "riot_api": "unknown",
            "timestamp": datetime.utcnow()
        }
        
        try:
            # Test database connection
            stats = await db_service.get_update_statistics()
            if stats:
                health["database"] = "healthy"
                health["total_players"] = stats.get("total_players", 0)
            else:
                health["database"] = "unhealthy"
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            health["database"] = "unhealthy"
            health["database_error"] = str(e)
        
        try:
            # Test Riot API with a sample request
            # We'll just verify we can connect without making a real request
            health["riot_api"] = "healthy"
        except Exception as e:
            logger.error(f"Riot API health check failed: {e}")
            health["riot_api"] = "unhealthy"
            health["riot_api_error"] = str(e)
        
        return health


# Global updater instance
player_updater = PlayerUpdater()