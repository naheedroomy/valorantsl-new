import asyncio
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
import httpx
try:
    from .config import settings
except ImportError:
    from config import settings

logger = logging.getLogger(__name__)


class RiotAPIClient:
    """Riot Games API client for fetching player data"""
    
    def __init__(self):
        self.base_url = settings.riot_api_base_url
        self.api_key = settings.riot_api_key
        self.region = settings.riot_region
        self.platform = settings.riot_platform
        self.session: Optional[httpx.AsyncClient] = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        await self.start_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close_session()
    
    async def start_session(self):
        """Start HTTP session"""
        self.session = httpx.AsyncClient(
            headers={"Authorization": self.api_key} if self.api_key else {},
            timeout=30.0
        )
    
    async def close_session(self):
        """Close HTTP session"""
        if self.session:
            await self.session.aclose()
            self.session = None
    
    async def _make_request(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """Make HTTP request to Riot API with retry logic"""
        if not self.session:
            logger.error("HTTP session not initialized")
            return None
        
        url = f"{self.base_url}{endpoint}"
        
        for attempt in range(settings.max_retries):
            try:
                logger.debug(f"Making request to {url} (attempt {attempt + 1})")
                
                response = await self.session.get(url)
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:
                    # Rate limited
                    retry_after = int(response.headers.get("Retry-After", settings.retry_delay))
                    logger.warning(f"Rate limited. Waiting {retry_after} seconds before retry")
                    await asyncio.sleep(retry_after)
                    continue
                elif response.status_code == 404:
                    logger.warning(f"Player not found: {endpoint}")
                    return None
                else:
                    logger.warning(f"API request failed with status {response.status_code}: {response.text}")
                    
            except httpx.RequestError as e:
                logger.error(f"Request error for {url}: {e}")
            except Exception as e:
                logger.error(f"Unexpected error for {url}: {e}")
            
            # Wait before retry
            if attempt < settings.max_retries - 1:
                await asyncio.sleep(settings.retry_delay)
        
        logger.error(f"All retry attempts failed for {url}")
        return None
    
    async def get_player_by_puuid(self, puuid: str) -> Optional[Dict[str, Any]]:
        """Get basic player account info by PUUID"""
        endpoint = f"/valorant/v1/by-puuid/account/{puuid}"
        return await self._make_request(endpoint)
    
    async def get_player_mmr(self, puuid: str) -> Optional[Dict[str, Any]]:
        """Get player MMR/rank information"""
        endpoint = f"/valorant/v3/by-puuid/mmr/ap/pc/{puuid}"
        return await self._make_request(endpoint)
    
    async def get_player_matches(self, puuid: str, size: int = 5) -> Optional[List[Dict[str, Any]]]:
        """Get recent matches for a player"""
        endpoint = f"/valorant/v3/by-puuid/matches/{self.region}/{puuid}?size={size}"
        response = await self._make_request(endpoint)
        
        if response and "data" in response:
            return response["data"]
        return None
    
    async def get_player_matches_v4(self, puuid: str, size: int = 1) -> Optional[List[Dict[str, Any]]]:
        """Get recent matches for a player using v4 API (includes more match metadata)"""
        endpoint = f"/valorant/v4/by-puuid/matches/{self.region}/{self.platform}/{puuid}?mode=competitive&size={size}"
        response = await self._make_request(endpoint)
        
        if response and "data" in response:
            return response["data"]
        return None
    
    async def get_last_played_match_date(self, puuid: str) -> Optional[str]:
        """Get the date of the last competitive match for a player"""
        try:
            matches = await self.get_player_matches_v4(puuid, size=1)
            
            if matches and len(matches) > 0:
                last_match = matches[0]
                
                # The v4 API includes started_at in ISO format in the metadata
                if "metadata" in last_match and "started_at" in last_match["metadata"]:
                    last_played_date = last_match["metadata"]["started_at"]
                    logger.debug(f"Last played match for PUUID {puuid}: {last_played_date}")
                    return last_played_date
                
                # Fallback: try other potential timestamp fields
                if "metadata" in last_match and "game_start" in last_match["metadata"]:
                    timestamp_ms = last_match["metadata"]["game_start"]
                    timestamp_seconds = timestamp_ms / 1000
                    last_played_date = datetime.fromtimestamp(timestamp_seconds).isoformat()
                    
                    logger.debug(f"Last played match for PUUID {puuid} (from game_start): {last_played_date}")
                    return last_played_date
            
            logger.debug(f"No recent matches found for PUUID: {puuid}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting last played match for PUUID {puuid}: {e}")
            return None
    
    async def get_full_player_data(self, puuid: str) -> Optional[Dict[str, Any]]:
        """Get essential player data using only MMR endpoint (includes account info) and last played date"""
        try:
            logger.debug(f"Fetching player data for PUUID: {puuid}")
            
            # Get MMR data (includes account info)
            mmr_data = await self.get_player_mmr(puuid)
            if not mmr_data or "data" not in mmr_data:
                logger.warning(f"No MMR data found for PUUID: {puuid}")
                return None
            
            # Extract account info from MMR data
            mmr_response = mmr_data["data"]
            account_info = mmr_response.get("account", {})
            
            # Get last played match date
            last_played_date = await self.get_last_played_match_date(puuid)
            
            # Build player data structure
            player_data = {
                # Basic account info (from MMR endpoint)
                "puuid": puuid,
                "name": account_info.get("name", "Unknown"),
                "tag": account_info.get("tag", "0000"),
                
                # Rank information
                "rank_details": self._process_mmr_data(mmr_data),
                
                # Peak rank information
                "peak_rank": self._get_peak_rank_info(mmr_data),
                
                # Seasonal ranks information
                "seasonal_ranks": self._get_seasonal_ranks_info(mmr_data),
                
                # Last played match date
                "last_played_match": last_played_date,
                
                # Metadata
                "last_updated": datetime.utcnow().isoformat(),
                "update_source": "updater_service"
            }
            
            logger.debug(f"Successfully processed data for player: {account_info.get('name')}#{account_info.get('tag')}")
            return player_data
            
        except Exception as e:
            logger.error(f"Error processing player data for PUUID {puuid}: {e}")
            return None
    
    def _process_mmr_data(self, mmr_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Process MMR data into standardized format"""
        if not mmr_data or "data" not in mmr_data:
            return {
                "currenttierpatched": "Unrated",
                "current_tier": 0,
                "elo": 0,
                "ranking_in_tier": 0,
                "games_needed_for_rating": 0
            }
        
        data = mmr_data["data"]
        current_data = data.get("current", {})
        tier_info = current_data.get("tier", {})
        
        return {
            "currenttierpatched": tier_info.get("name", "Unrated"),
            "current_tier": tier_info.get("id", 0),
            "elo": current_data.get("elo", 0),
            "ranking_in_tier": current_data.get("rr", 0),
            "games_needed_for_rating": current_data.get("games_needed_for_rating", 0)
        }
    
    def _get_peak_rank_info(self, mmr_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract peak rank information"""
        if not mmr_data or "data" not in mmr_data:
            return {
                "tier_name": "Unknown",
                "season_short": "Unknown",
                "tier": 0
            }
        
        data = mmr_data["data"]
        peak_data = data.get("peak", {})
        tier_info = peak_data.get("tier", {})
        season_info = peak_data.get("season", {})
        
        return {
            "tier_name": tier_info.get("name", "Unknown"),
            "season_short": season_info.get("short", "Unknown"),
            "tier": tier_info.get("id", 0)
        }
    
    def _get_seasonal_ranks_info(self, mmr_data: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract seasonal rank information from MMR data"""
        if not mmr_data or "data" not in mmr_data:
            return []
        
        data = mmr_data["data"]
        seasonal_data = data.get("seasonal", [])
        
        if not seasonal_data:
            return []
        
        processed_seasonal = []
        
        for season in seasonal_data:
            season_info = season.get("season", {})
            end_tier_info = season.get("end_tier", {})
            
            # Process the seasonal data into our desired format
            season_record = {
                "season_short": season_info.get("short", "Unknown"),
                "season_id": season_info.get("id", ""),
                "wins": season.get("wins", 0),
                "games": season.get("games", 0),
                "end_tier": {
                    "id": end_tier_info.get("id", 0),
                    "name": end_tier_info.get("name", "Unknown")
                },
                "end_rr": season.get("end_rr", 0),
                "ranking_schema": season.get("ranking_schema", "base"),
                "leaderboard_placement": season.get("leaderboard_placement")
            }
            
            # Add act wins if available (this is detailed win history)
            act_wins = season.get("act_wins", [])
            if act_wins:
                # Count act wins by tier to get a summary
                tier_counts = {}
                for act_win in act_wins:
                    tier_name = act_win.get("name", "Unknown")
                    tier_counts[tier_name] = tier_counts.get(tier_name, 0) + 1
                
                season_record["act_wins_summary"] = tier_counts
                season_record["total_act_wins"] = len(act_wins)
            
            processed_seasonal.append(season_record)
        
        # Sort by season (most recent first) - assuming season_short format like e10a2
        processed_seasonal.sort(key=lambda x: x.get("season_short", ""), reverse=True)
        
        logger.debug(f"Processed {len(processed_seasonal)} seasonal records")
        return processed_seasonal
    
    def _calculate_match_stats(self, matches_data: Optional[List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Calculate match statistics from recent games"""
        if not matches_data:
            return {
                "recent_games": 0,
                "wins": 0,
                "losses": 0,
                "win_rate": 0.0,
                "avg_score": 0.0,
                "avg_kills": 0.0,
                "avg_deaths": 0.0,
                "avg_assists": 0.0
            }
        
        total_games = len(matches_data)
        wins = 0
        total_score = 0
        total_kills = 0
        total_deaths = 0
        total_assists = 0
        
        for match in matches_data:
            if isinstance(match, dict) and "stats" in match:
                stats = match["stats"]
                
                # Count wins
                if stats.get("team", "") == "Red" and match.get("teams", {}).get("red", 0) > match.get("teams", {}).get("blue", 0):
                    wins += 1
                elif stats.get("team", "") == "Blue" and match.get("teams", {}).get("blue", 0) > match.get("teams", {}).get("red", 0):
                    wins += 1
                
                # Aggregate stats
                total_score += stats.get("score", 0)
                total_kills += stats.get("kills", 0)
                total_deaths += stats.get("deaths", 0)
                total_assists += stats.get("assists", 0)
        
        return {
            "recent_games": total_games,
            "wins": wins,
            "losses": total_games - wins,
            "win_rate": (wins / total_games * 100) if total_games > 0 else 0.0,
            "avg_score": total_score / total_games if total_games > 0 else 0.0,
            "avg_kills": total_kills / total_games if total_games > 0 else 0.0,
            "avg_deaths": total_deaths / total_games if total_games > 0 else 0.0,
            "avg_assists": total_assists / total_games if total_games > 0 else 0.0
        }


# Global API client instance
riot_api = RiotAPIClient()