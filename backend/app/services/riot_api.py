import httpx
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from ..config import settings
from ..models.user import UserInDB, RankDetails, RankData, PeakRank, SeasonalRank

logger = logging.getLogger(__name__)


class RiotAPIService:
    """Service for interacting with Riot API"""
    
    def __init__(self):
        self.base_url = settings.riot_api_base_url
        self.api_key = settings.riot_api_key
        self.region = settings.riot_region
        self.platform = settings.riot_platform

    async def get_player_mmr_data(self, puuid: str) -> Dict[str, Any]:
        """
        Fetch player MMR data from Riot API
        Endpoint: GET /valorant/v3/by-puuid/mmr/{region}/{platform}/{puuid}
        """
        url = f"{self.base_url}/valorant/v3/by-puuid/mmr/{self.region}/{self.platform}/{puuid}"
        
        headers = {
            "Authorization": self.api_key,
            "Content-Type": "application/json"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, timeout=30.0)
                response.raise_for_status()
                
                data = response.json()
                logger.info(f"Successfully fetched MMR data for PUUID: {puuid}")
                return data
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching MMR data for {puuid}: {e.response.status_code} - {e.response.text}")
            raise ValueError(f"Failed to fetch player data: HTTP {e.response.status_code}")
        except httpx.TimeoutException:
            logger.error(f"Timeout fetching MMR data for {puuid}")
            raise ValueError("Request timeout while fetching player data")
        except Exception as e:
            logger.error(f"Unexpected error fetching MMR data for {puuid}: {e}")
            raise ValueError(f"Failed to fetch player data: {str(e)}")

    async def get_last_competitive_match_date(self, puuid: str) -> Optional[str]:
        """
        Fetch the date of the last competitive match for a player
        Endpoint: GET /valorant/v4/by-puuid/matches/{region}/{platform}/{puuid}?mode=competitive&size=1
        """
        url = f"{self.base_url}/valorant/v4/by-puuid/matches/{self.region}/{self.platform}/{puuid}?mode=competitive&size=1"
        
        headers = {
            "Authorization": self.api_key,
            "Content-Type": "application/json"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, timeout=30.0)
                response.raise_for_status()
                
                data = response.json()
                
                # Extract the last competitive match date
                if data["status"] == 200 and data["data"] and len(data["data"]) > 0:
                    last_match = data["data"][0]
                    if "metadata" in last_match and "started_at" in last_match["metadata"]:
                        last_played_date = last_match["metadata"]["started_at"]
                        logger.debug(f"Last competitive match for PUUID {puuid}: {last_played_date}")
                        return last_played_date
                
                logger.debug(f"No recent competitive matches found for PUUID: {puuid}")
                return None
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"No competitive matches found for {puuid}")
                return None
            logger.error(f"HTTP error fetching last competitive match for {puuid}: {e.response.status_code}")
            return None
        except httpx.TimeoutException:
            logger.warning(f"Timeout fetching last competitive match for {puuid}")
            return None
        except Exception as e:
            logger.warning(f"Error fetching last competitive match for {puuid}: {e}")
            return None

    def _parse_rank_details(self, mmr_data: Dict[str, Any]) -> RankDetails:
        """Parse rank details from MMR API response"""
        current_data = mmr_data["data"]["current"]
        
        rank_data = RankData(
            currenttier=current_data["tier"]["id"],
            currenttierpatched=current_data["tier"]["name"],
            elo=current_data["elo"],
            ranking_in_tier=current_data["rr"],
            mmr_change_to_last_game=current_data["last_change"],
            games_needed_for_rating=current_data["games_needed_for_rating"],
            rank_protection_shields=current_data["rank_protection_shields"],
            leaderboard_placement=current_data.get("leaderboard_placement")
        )
        
        return RankDetails(
            data=rank_data,
            status=mmr_data["status"]
        )

    def _parse_peak_rank(self, mmr_data: Dict[str, Any]) -> PeakRank:
        """Parse peak rank from MMR API response"""
        peak_data = mmr_data["data"]["peak"]
        
        return PeakRank(
            season_short=peak_data["season"]["short"],
            tier_name=peak_data["tier"]["name"],
            rr=peak_data["rr"]
        )

    def _parse_seasonal_ranks(self, mmr_data: Dict[str, Any]) -> List[SeasonalRank]:
        """Parse seasonal ranks from MMR API response"""
        seasonal_data = mmr_data["data"]["seasonal"]
        seasonal_ranks = []
        
        for season in seasonal_data:
            seasonal_rank = SeasonalRank(
                season_short=season["season"]["short"],
                end_tier_name=season["end_tier"]["name"],
                wins=season["wins"],
                games=season["games"],
                end_rr=season["end_rr"]
            )
            seasonal_ranks.append(seasonal_rank)
        
        return seasonal_ranks

    async def create_user_from_puuid(
        self, 
        puuid: str, 
        discord_id: int, 
        discord_username: str
    ) -> UserInDB:
        """
        Create a complete UserInDB object from PUUID and Discord info
        """
        try:
            # Fetch MMR data from Riot API
            mmr_data = await self.get_player_mmr_data(puuid)
            
            # Fetch last competitive match date
            last_competitive_match = await self.get_last_competitive_match_date(puuid)
            
            # Extract account info
            account_data = mmr_data["data"]["account"]
            
            # Parse components
            rank_details = self._parse_rank_details(mmr_data)
            peak_rank = self._parse_peak_rank(mmr_data)
            seasonal_ranks = self._parse_seasonal_ranks(mmr_data)
            
            # Create UserInDB object
            user = UserInDB(
                puuid=puuid,
                name=account_data["name"],
                tag=account_data["tag"],
                region=self.region,
                discord_id=discord_id,
                discord_username=discord_username,
                rank_details=rank_details,
                updated_at=datetime.utcnow(),
                peak_rank=peak_rank,
                seasonal_extended_at=datetime.utcnow(),
                seasonal_ranks=seasonal_ranks,
                last_played_match=last_competitive_match
            )
            
            logger.info(f"Created user object for {account_data['name']}#{account_data['tag']} ({puuid}) - Last competitive match: {last_competitive_match}")
            return user
            
        except Exception as e:
            logger.error(f"Failed to create user from PUUID {puuid}: {e}")
            raise


# Global Riot API service instance
riot_api_service = RiotAPIService()