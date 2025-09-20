"""User registration router with Riot API integration"""
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
import httpx
import logging
from datetime import datetime

from ..config import settings
from ..services.database import db_service
from ..models.user import UserInDB

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/register", tags=["registration"])


class RegistrationRequest(BaseModel):
    """Registration request model"""
    discord_id: int
    discord_username: str
    puuid: str


class PlayerPreview(BaseModel):
    """Player preview data before registration"""
    puuid: str
    name: str
    tag: str
    current_rank: str
    elo: int
    peak_rank: str
    peak_season: str
    last_played: Optional[str]


async def fetch_riot_api(endpoint: str) -> Optional[Dict[str, Any]]:
    """Helper function to make Riot API requests"""
    url = f"{settings.riot_api_base_url}{endpoint}"
    headers = {"Authorization": settings.riot_api_key} if settings.riot_api_key else {}
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(url, headers=headers)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return None
            else:
                logger.error(f"Riot API error {response.status_code}: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Riot API request failed: {e}")
            return None


async def get_player_mmr(puuid: str) -> Optional[Dict[str, Any]]:
    """Get player MMR/rank information - same as updater"""
    endpoint = f"/valorant/v3/by-puuid/mmr/ap/pc/{puuid}"
    return await fetch_riot_api(endpoint)


async def get_last_played_match(puuid: str) -> Optional[str]:
    """Get the date of the last competitive match - same as updater"""
    endpoint = f"/valorant/v4/by-puuid/matches/{settings.riot_region}/{settings.riot_platform}/{puuid}?mode=competitive&size=1"
    response = await fetch_riot_api(endpoint)
    
    if response and "data" in response:
        matches = response["data"]
        if matches and len(matches) > 0:
            last_match = matches[0]
            
            # Check for started_at in metadata (v4 API)
            if "metadata" in last_match and "started_at" in last_match["metadata"]:
                return last_match["metadata"]["started_at"]
            
            # Fallback to game_start timestamp
            if "metadata" in last_match and "game_start" in last_match["metadata"]:
                timestamp_ms = last_match["metadata"]["game_start"]
                timestamp_seconds = timestamp_ms / 1000
                return datetime.fromtimestamp(timestamp_seconds).isoformat()
    
    return None


def process_mmr_data(mmr_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process MMR data into standardized format - same as updater"""
    if not mmr_data or "data" not in mmr_data:
        return {
            "currenttierpatched": "Unrated",
            "currenttier": 0,
            "elo": 0,
            "ranking_in_tier": 0,
            "mmr_change_to_last_game": 0,
            "games_needed_for_rating": 0,
            "rank_protection_shields": 0,
            "leaderboard_placement": None
        }
    
    data = mmr_data["data"]
    current_data = data.get("current", {})
    tier_info = current_data.get("tier", {})
    
    return {
        "data": {
            "currenttier": tier_info.get("id", 0),
            "currenttierpatched": tier_info.get("name", "Unrated"),
            "elo": current_data.get("elo", 0),
            "ranking_in_tier": current_data.get("rr", 0),
            "mmr_change_to_last_game": current_data.get("mmr_change_to_last_game", 0),
            "games_needed_for_rating": current_data.get("games_needed_for_rating", 0),
            "rank_protection_shields": 0,
            "leaderboard_placement": current_data.get("leaderboard", None)
        },
        "status": 200
    }


def get_peak_rank_info(mmr_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract peak rank information - same as updater"""
    if not mmr_data or "data" not in mmr_data:
        return {
            "tier_name": "Unknown",
            "season_short": "Unknown",
            "rr": 0
        }
    
    data = mmr_data["data"]
    peak_data = data.get("peak", {})
    tier_info = peak_data.get("tier", {})
    season_info = peak_data.get("season", {})
    
    return {
        "tier_name": tier_info.get("name", "Unknown"),
        "season_short": season_info.get("short", "Unknown"),
        "rr": peak_data.get("rr", 0)
    }


@router.post("/preview")
async def preview_player(puuid: str = Body(..., embed=True)):
    """Get player preview data before registration"""
    try:
        logger.info(f"Fetching preview for PUUID: {puuid}")
        
        # Check if PUUID already exists
        if await db_service.user_exists(puuid):
            raise HTTPException(status_code=409, detail="Player already registered")
        
        # Fetch MMR data (includes account info)
        mmr_data = await get_player_mmr(puuid)
        if not mmr_data or "data" not in mmr_data:
            raise HTTPException(status_code=404, detail="Player not found or has no competitive data")
        
        # Extract account info from MMR response
        mmr_response = mmr_data["data"]
        account_info = mmr_response.get("account", {})
        
        if not account_info.get("name"):
            raise HTTPException(status_code=404, detail="Player account information not found")
        
        # Get last played match
        last_played = await get_last_played_match(puuid)
        
        # Process rank data
        rank_details = process_mmr_data(mmr_data)
        peak_rank = get_peak_rank_info(mmr_data)
        
        # Build preview response
        preview = PlayerPreview(
            puuid=puuid,
            name=account_info.get("name", "Unknown"),
            tag=account_info.get("tag", "0000"),
            current_rank=rank_details["data"]["currenttierpatched"],
            elo=rank_details["data"]["elo"],
            peak_rank=peak_rank["tier_name"],
            peak_season=peak_rank["season_short"],
            last_played=last_played
        )
        
        logger.info(f"Preview fetched for {preview.name}#{preview.tag}")
        return preview
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching player preview: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch player data")


@router.post("/submit")
async def submit_registration(request: RegistrationRequest):
    """Submit final registration to add player to leaderboard"""
    try:
        logger.info(f"Processing registration for Discord user {request.discord_username} with PUUID {request.puuid}")
        
        # Check if Discord user already exists
        existing_discord = await db_service.get_user_by_discord_id(request.discord_id)
        if existing_discord:
            raise HTTPException(status_code=409, detail="Discord user already registered")
        
        # Check if PUUID already exists
        if await db_service.user_exists(request.puuid):
            raise HTTPException(status_code=409, detail="PUUID already registered")
        
        # Fetch complete player data using same logic as updater
        mmr_data = await get_player_mmr(request.puuid)
        if not mmr_data or "data" not in mmr_data:
            raise HTTPException(status_code=404, detail="Player not found")
        
        # Extract account info
        mmr_response = mmr_data["data"]
        account_info = mmr_response.get("account", {})
        
        # Get last played match
        last_played = await get_last_played_match(request.puuid)
        
        # Process all data
        rank_details = process_mmr_data(mmr_data)
        peak_rank = get_peak_rank_info(mmr_data)
        
        # Get seasonal ranks (we'll just use empty for now, updater will fill this)
        seasonal_ranks = []
        
        # Create user object matching the database model
        user_data = UserInDB(
            puuid=request.puuid,
            name=account_info.get("name", "Unknown"),
            tag=account_info.get("tag", "0000"),
            region=settings.riot_region,
            discord_id=request.discord_id,
            discord_username=request.discord_username,
            rank_details=rank_details,
            updated_at=datetime.utcnow(),
            peak_rank=peak_rank,
            seasonal_extended_at=datetime.utcnow(),
            seasonal_ranks=seasonal_ranks,
            last_played_match=last_played
        )
        
        # Save to database
        created_user = await db_service.create_user(user_data)
        
        logger.info(f"Successfully registered {created_user.name}#{created_user.tag} for Discord user {request.discord_username}")
        
        return {
            "success": True,
            "message": "Registration successful",
            "player": {
                "puuid": created_user.puuid,
                "name": created_user.name,
                "tag": created_user.tag,
                "current_rank": rank_details["data"]["currenttierpatched"],
                "elo": rank_details["data"]["elo"]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")

# -------------------------------------------------------------
# Alias routes for frontend compatibility (GET + simplified POST)
# -------------------------------------------------------------
@router.get("/preview/{puuid}")
async def preview_player_get(puuid: str):
    """Alias GET endpoint matching frontend expectation /api/v1/preview/{puuid}"""
    return await preview_player(puuid=puuid)

@router.post("")
async def submit_registration_root(request: RegistrationRequest):
    """Alias POST endpoint matching frontend expectation /api/v1/register"""
    return await submit_registration(request)
