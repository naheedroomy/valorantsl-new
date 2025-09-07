"""Discord OAuth authentication router"""
from typing import Optional, Dict, Any, Set
from fastapi import APIRouter, HTTPException, Query, Depends, Body
from fastapi.responses import JSONResponse
from fastapi_discord import DiscordOAuthClient, User, Unauthorized, RateLimited
from fastapi_discord.exceptions import ClientSessionNotInitialized
import logging
import httpx
from datetime import datetime

from ..config import settings
from ..services.database import db_service
from ..models.user import UserInDB

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])

# Cache to store used OAuth codes to prevent duplicate exchanges
_used_codes: Set[str] = set()

# Initialize Discord OAuth client
discord = DiscordOAuthClient(
    settings.discord_client_id,
    settings.discord_client_secret,
    settings.discord_redirect_uri,
    ("identify", "email")  # Only need basic user info
)


@router.get("/discord/login")
async def discord_login():
    """Get Discord OAuth login URL"""
    return {"url": discord.oauth_login_url}


@router.get("/discord/callback")
async def discord_callback(code: str = Query(...)):
    """Handle Discord OAuth callback and exchange code for user info"""
    
    # Check if this code has already been used to prevent duplicate processing
    if code in _used_codes:
        raise HTTPException(status_code=409, detail="OAuth code already used")
    
    try:
        # Mark code as being used
        _used_codes.add(code)
        
        # Exchange code for access token
        token, refresh_token = await discord.get_access_token(code)
        
        # Get user info from Discord
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {token}"}
            response = await client.get("https://discord.com/api/users/@me", headers=headers)
            
            if response.status_code != 200:
                raise HTTPException(status_code=400, detail="Failed to get Discord user info")
            
            discord_user = response.json()
        
        # Extract user data
        user_data = {
            "discord_id": int(discord_user["id"]),
            "discord_username": discord_user["username"],
            "discord_discriminator": discord_user.get("discriminator", "0"),
            "discord_avatar": discord_user.get("avatar"),
            "discord_email": discord_user.get("email"),
            "access_token": token
        }
        
        logger.info(f"Discord user authenticated: {user_data['discord_username']} (ID: {user_data['discord_id']})")
        
        # Check if user already exists in database
        existing_user = await db_service.get_user_by_discord_id(user_data["discord_id"])
        
        return {
            "user": user_data,
            "exists": existing_user is not None,
            "existing_data": {
                "puuid": existing_user.puuid,
                "name": existing_user.name,
                "tag": existing_user.tag,
                "current_rank": existing_user.rank_details.data.currenttierpatched if existing_user and existing_user.rank_details else None
            } if existing_user else None
        }
        
    except Exception as e:
        # Remove from used codes on error so it can be retried if needed
        _used_codes.discard(code)
        logger.error(f"Discord OAuth callback error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/check-discord")
async def check_discord_exists(discord_id: int = Body(..., embed=True)):
    """Check if a Discord user already exists in the database"""
    try:
        user = await db_service.get_user_by_discord_id(discord_id)
        
        if user:
            return {
                "exists": True,
                "user": {
                    "puuid": user.puuid,
                    "name": user.name,
                    "tag": user.tag,
                    "discord_username": user.discord_username,
                    "current_rank": user.rank_details.data.currenttierpatched if user.rank_details else None
                }
            }
        
        return {"exists": False}
        
    except Exception as e:
        logger.error(f"Error checking Discord user: {e}")
        raise HTTPException(status_code=500, detail="Failed to check Discord user")


@router.post("/check-puuid")
async def check_puuid_exists(puuid: str = Body(..., embed=True)):
    """Check if a PUUID already exists in the database"""
    try:
        logger.info(f"Checking PUUID existence: {puuid}")
        
        if not puuid:
            logger.error("Empty PUUID received")
            raise HTTPException(status_code=400, detail="PUUID is required")
        
        exists = await db_service.user_exists(puuid)
        
        if exists:
            user = await db_service.get_user_by_puuid(puuid)
            logger.info(f"PUUID {puuid} already exists for user {user.name}#{user.tag}" if user else f"PUUID {puuid} exists but user data not found")
            return {
                "exists": True,
                "user": {
                    "name": user.name,
                    "tag": user.tag,
                    "discord_username": user.discord_username
                } if user else None
            }
        
        logger.info(f"PUUID {puuid} does not exist in database")
        return {"exists": False}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking PUUID {puuid}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to check PUUID: {str(e)}")