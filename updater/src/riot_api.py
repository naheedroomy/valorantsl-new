"""
Riot API client for the ValorantSL Player Updater Service
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
import httpx

from .config import config

logger = logging.getLogger(__name__)


class RiotAPIClient:
    """Client for interacting with Henrik's Valorant API"""
    
    def __init__(self):
        self.base_url = config.riot_api_base_url
        self.api_key = config.riot_api_key
        self.region = config.riot_region
        self.platform = config.riot_platform
        self.max_retries = config.max_retries
        
    async def get_player_mmr_data(self, puuid: str) -> Optional[Dict[str, Any]]:
        """
        Fetch player MMR data from Henrik's API
        Endpoint: GET /valorant/v3/by-puuid/mmr/{region}/{platform}/{puuid}
        """
        url = f"{self.base_url}/valorant/v3/by-puuid/mmr/{self.region}/{self.platform}/{puuid}"
        
        headers = {
            "Authorization": self.api_key,
            "User-Agent": "ValorantSL-Updater/1.0"
        }
        
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(url, headers=headers, timeout=30.0)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("status") == 200 and "data" in data:
                            logger.debug(f"Successfully fetched data for PUUID: {puuid}")
                            return data
                        else:
                            logger.warning(f"API returned error for {puuid}: {data}")
                            return None
                            
                    elif response.status_code == 429:
                        # Rate limited - wait longer
                        wait_time = (attempt + 1) * 10
                        logger.warning(f"Rate limited for {puuid}, waiting {wait_time}s (attempt {attempt + 1})")
                        await asyncio.sleep(wait_time)
                        continue
                        
                    elif response.status_code == 404:
                        logger.warning(f"Player not found: {puuid}")
                        return None
                        
                    else:
                        logger.error(f"API error for {puuid}: {response.status_code} - {response.text}")
                        if attempt < self.max_retries - 1:
                            await asyncio.sleep((attempt + 1) * 2)
                            continue
                        return None
                        
            except httpx.TimeoutException:
                logger.warning(f"Timeout for {puuid} (attempt {attempt + 1})")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep((attempt + 1) * 2)
                    continue
                return None
                
            except Exception as e:
                logger.error(f"Unexpected error for {puuid}: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep((attempt + 1) * 2)
                    continue
                return None
        
        logger.error(f"Failed to fetch data for {puuid} after {self.max_retries} attempts")
        return None
    
    def _parse_rank_details(self, mmr_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse rank details from MMR data"""
        try:
            data = mmr_data["data"]
            return {
                "currenttierpatched": data.get("currenttierpatched", "Unknown"),
                "currenttier": data.get("currenttier", 0),
                "ranking_in_tier": data.get("ranking_in_tier", 0),
                "mmr_change_to_last_game": data.get("mmr_change_to_last_game", 0),
                "elo": data.get("elo", 0),
                "account": data.get("account", {}),
                "by_season": data.get("by_season", {})
            }
        except KeyError as e:
            logger.error(f"Missing required field in MMR data: {e}")
            return None
    
    def _parse_peak_rank(self, mmr_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse peak rank from MMR data"""
        try:
            data = mmr_data["data"]
            highest_rank = data.get("highest_rank", {})
            
            if highest_rank:
                return {
                    "tier": highest_rank.get("tier", 0),
                    "tier_name": highest_rank.get("patched_tier", "Unknown"),
                    "season_short": highest_rank.get("season_short", "Unknown"),
                    "converted": highest_rank.get("converted", 0)
                }
            return None
        except KeyError:
            return None
    
    def _parse_seasonal_ranks(self, mmr_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse seasonal rank history from MMR data"""
        try:
            data = mmr_data["data"]
            by_season = data.get("by_season", {})
            seasonal_ranks = []
            
            for season_id, season_data in by_season.items():
                if isinstance(season_data, dict):
                    seasonal_ranks.append({
                        "season_id": season_id,
                        "season_short": season_data.get("season_short", "Unknown"),
                        "tier": season_data.get("final_rank", 0),
                        "tier_name": season_data.get("final_rank_patched", "Unknown"),
                        "act_rank_wins": season_data.get("act_rank_wins", []),
                        "old": season_data.get("old", False)
                    })
            
            return seasonal_ranks
        except KeyError:
            return []
    
    async def process_player_update(self, puuid: str) -> Optional[Dict[str, Any]]:
        """
        Process a complete player update - fetch data and parse all components
        Returns update data ready for database insertion
        """
        mmr_data = await self.get_player_mmr_data(puuid)
        if not mmr_data:
            return None
        
        try:
            # Parse all components
            rank_details = self._parse_rank_details(mmr_data)
            peak_rank = self._parse_peak_rank(mmr_data)
            seasonal_ranks = self._parse_seasonal_ranks(mmr_data)
            
            # Extract account info for name/tag updates
            account_data = mmr_data["data"].get("account", {})
            
            update_data = {
                "name": account_data.get("name", "Unknown"),
                "tag": account_data.get("tag", "Unknown"),
                "rank_details": {
                    "data": rank_details
                } if rank_details else None,
                "peak_rank": peak_rank,
                "seasonal_ranks": seasonal_ranks,
                "seasonal_extended_at": datetime.utcnow()
            }
            
            return update_data
            
        except Exception as e:
            logger.error(f"Failed to process update data for {puuid}: {e}")
            return None


# Global Riot API client instance
riot_client = RiotAPIClient()