import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
try:
    from .config import settings
    from .database import db_manager
    from .riot_api import riot_api
except ImportError:
    from config import settings
    from database import db_manager
    from riot_api import riot_api

logger = logging.getLogger(__name__)


class PlayerUpdater:
    """Main updater class that orchestrates player data updates"""
    
    def __init__(self):
        self.stats = {
            "total_players": 0,
            "updated_players": 0,
            "failed_updates": 0,
            "skipped_players": 0,
            "start_time": None,
            "end_time": None
        }
    
    async def update_all_players(self) -> Dict[str, Any]:
        """Update all players in the database"""
        logger.info("Starting player data update process")
        self.stats["start_time"] = datetime.utcnow()
        
        try:
            # Connect to database
            if not await db_manager.connect():
                raise Exception("Failed to connect to database")
            
            # Get all players
            players = await db_manager.get_all_puuids()
            if not players:
                logger.warning("No players found in database")
                return self._get_update_stats()
            
            self.stats["total_players"] = len(players)
            logger.info(f"Found {len(players)} players to update")
            
            # Start API session
            async with riot_api:
                await self._update_players_batch(players)
            
        except Exception as e:
            logger.error(f"Error during player update process: {e}")
            
        finally:
            self.stats["end_time"] = datetime.utcnow()
            await db_manager.disconnect()
        
        return self._get_update_stats()
    
    async def _update_players_batch(self, players: List[Dict[str, Any]]):
        """Update players in batches with rate limiting"""
        total_players = len(players)
        
        for i, player in enumerate(players, 1):
            puuid = player.get("puuid")
            name = player.get("name", "Unknown")
            tag = player.get("tag", "0000")
            
            if not puuid:
                logger.warning(f"Player {i}/{total_players}: Missing PUUID, skipping")
                self.stats["skipped_players"] += 1
                continue
            
            logger.info(f"Updating player {i}/{total_players}: {name}#{tag}")
            
            try:
                # Update single player
                success = await self._update_single_player(puuid, name, tag)
                
                if success:
                    self.stats["updated_players"] += 1
                    logger.info(f"✓ Successfully updated {name}#{tag}")
                else:
                    self.stats["failed_updates"] += 1
                    logger.error(f"✗ Failed to update {name}#{tag}")
            
            except Exception as e:
                logger.error(f"✗ Exception updating {name}#{tag}: {e}")
                self.stats["failed_updates"] += 1
            
            # Rate limiting delay (except for the last player)
            if i < total_players:
                logger.debug(f"Waiting {settings.rate_limit_delay}s before next update")
                await asyncio.sleep(settings.rate_limit_delay)
    
    async def _update_single_player(self, puuid: str, name: str, tag: str) -> bool:
        """Update a single player's data"""
        try:
            # Fetch fresh data from Riot API
            player_data = await riot_api.get_full_player_data(puuid)
            
            if not player_data:
                logger.warning(f"No data received for {name}#{tag}")
                return False
            
            # Update database
            success = await db_manager.update_player_data(puuid, player_data)
            
            if success:
                rank = player_data.get("rank_details", {}).get("currenttierpatched", "Unknown")
                elo = player_data.get("rank_details", {}).get("elo", 0)
                logger.debug(f"Updated {name}#{tag}: {rank} ({elo} ELO)")
            
            return success
            
        except Exception as e:
            logger.error(f"Error updating player {name}#{tag}: {e}")
            return False
    
    async def update_single_player_by_puuid(self, puuid: str) -> bool:
        """Update a specific player by PUUID (useful for testing)"""
        logger.info(f"Updating single player: {puuid}")
        
        try:
            if not await db_manager.connect():
                raise Exception("Failed to connect to database")
            
            # Get player info
            player = await db_manager.get_player_by_puuid(puuid)
            if not player:
                logger.error(f"Player not found in database: {puuid}")
                return False
            
            name = player.get("name", "Unknown")
            tag = player.get("tag", "0000")
            
            # Update player
            async with riot_api:
                success = await self._update_single_player(puuid, name, tag)
            
            return success
            
        except Exception as e:
            logger.error(f"Error updating single player {puuid}: {e}")
            return False
            
        finally:
            await db_manager.disconnect()
    
    def _get_update_stats(self) -> Dict[str, Any]:
        """Get update statistics"""
        stats = self.stats.copy()
        
        if stats["start_time"] and stats["end_time"]:
            duration = stats["end_time"] - stats["start_time"]
            stats["duration_seconds"] = duration.total_seconds()
            stats["duration_formatted"] = str(duration).split(".")[0]  # Remove microseconds
        
        if stats["total_players"] > 0:
            stats["success_rate"] = (stats["updated_players"] / stats["total_players"]) * 100
        else:
            stats["success_rate"] = 0
        
        return stats
    
    def log_update_summary(self, stats: Dict[str, Any]):
        """Log a summary of the update process"""
        logger.info("=" * 50)
        logger.info("UPDATE SUMMARY")
        logger.info("=" * 50)
        logger.info(f"Total Players: {stats.get('total_players', 0)}")
        logger.info(f"Successfully Updated: {stats.get('updated_players', 0)}")
        logger.info(f"Failed Updates: {stats.get('failed_updates', 0)}")
        logger.info(f"Skipped Players: {stats.get('skipped_players', 0)}")
        logger.info(f"Success Rate: {stats.get('success_rate', 0):.1f}%")
        logger.info(f"Duration: {stats.get('duration_formatted', 'Unknown')}")
        logger.info("=" * 50)


# Global updater instance
player_updater = PlayerUpdater()