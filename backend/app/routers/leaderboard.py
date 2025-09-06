from fastapi import APIRouter, HTTPException, Query, Path
from typing import Optional, List
import logging
import math

from ..models.user import LeaderboardResponse, LeaderboardEntry
from ..services.database import db_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["leaderboard"])


@router.get("/leaderboard", response_model=LeaderboardResponse)
async def get_leaderboard(
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    per_page: int = Query(50, ge=1, le=200, description="Number of entries per page (1-200)")
):
    """
    Get the leaderboard with pagination.
    
    Returns users sorted by ELO in descending order.
    
    Parameters:
    - page: Page number (starts from 1)
    - per_page: Number of entries per page (max 200)
    
    Returns:
    - entries: List of leaderboard entries
    - total: Total number of users in leaderboard
    - page: Current page number
    - per_page: Entries per page
    - total_pages: Total number of pages
    """
    try:
        logger.info(f"Fetching leaderboard page {page} with {per_page} entries per page")
        
        # Get leaderboard data from database
        entries, total = await db_service.get_leaderboard(page=page, per_page=per_page)
        
        # Calculate total pages
        total_pages = math.ceil(total / per_page) if total > 0 else 1
        
        # Validate page number
        if page > total_pages:
            raise HTTPException(
                status_code=404,
                detail=f"Page {page} not found. Total pages: {total_pages}"
            )
        
        response = LeaderboardResponse(
            entries=entries,
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages
        )
        
        logger.info(f"Successfully fetched leaderboard: {len(entries)} entries, page {page}/{total_pages}")
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Error fetching leaderboard: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while fetching leaderboard")


@router.get("/leaderboard/top/{count}", response_model=List[LeaderboardEntry])
async def get_top_players(
    count: int = Path(..., ge=1, le=100, description="Number of top players to retrieve (1-100)")
):
    """
    Get the top N players from the leaderboard.
    
    Parameters:
    - count: Number of top players to retrieve (max 100)
    
    Returns:
    - List of top leaderboard entries sorted by ELO
    """
    try:
        logger.info(f"Fetching top {count} players")
        
        # Get top players (always page 1 with count as per_page)
        entries, _ = await db_service.get_leaderboard(page=1, per_page=count)
        
        logger.info(f"Successfully fetched top {len(entries)} players")
        return entries
        
    except Exception as e:
        logger.error(f"Error fetching top {count} players: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while fetching top players")


@router.get("/leaderboard/search/{discord_username}", response_model=Optional[LeaderboardEntry])
async def find_user_in_leaderboard(discord_username: str):
    """
    Find a specific user in the leaderboard by Discord username.
    
    Parameters:
    - discord_username: The Discord username to search for
    
    Returns:
    - LeaderboardEntry if found, null otherwise
    """
    try:
        logger.info(f"Searching for user: {discord_username}")
        
        # Use aggregation pipeline to find specific user
        pipeline = [
            {
                "$match": {"discord_username": {"$regex": f"^{discord_username}$", "$options": "i"}}
            },
            {
                "$project": {
                    "puuid": 1,
                    "name": 1,
                    "tag": 1,
                    "discord_username": 1,
                    "current_tier": "$rank_details.data.currenttierpatched",
                    "elo": "$rank_details.data.elo",
                    "rank_in_tier": "$rank_details.data.ranking_in_tier",
                    "peak_rank": "$peak_rank.tier_name",
                    "peak_season": "$peak_rank.season_short"
                }
            }
        ]
        
        cursor = db_service.collection.aggregate(pipeline)
        users = await cursor.to_list(length=1)
        
        if users:
            user_data = users[0]
            entry = LeaderboardEntry(**user_data)
            logger.info(f"Found user {discord_username}: {entry.name}#{entry.tag}")
            return entry
        
        logger.info(f"User {discord_username} not found in leaderboard")
        return None
        
    except Exception as e:
        logger.error(f"Error searching for user {discord_username}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while searching for user")


@router.get("/leaderboard/stats")
async def get_leaderboard_stats():
    """
    Get leaderboard statistics.
    
    Returns:
    - total_users: Total number of registered users
    - highest_elo: Highest ELO in the leaderboard
    - average_elo: Average ELO of all users
    - rank_distribution: Distribution of users by rank tiers
    """
    try:
        logger.info("Fetching leaderboard statistics")
        
        # Aggregation pipeline for statistics
        pipeline = [
            {
                "$match": {
                    "$or": [
                        {"rank_details.data.elo": {"$exists": True, "$ne": None}},
                        {"rank_details.elo": {"$exists": True, "$ne": None}}
                    ]
                }
            },
            {
                "$project": {
                    "elo": {
                        "$ifNull": ["$rank_details.data.elo", "$rank_details.elo"]
                    }
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total_users": {"$sum": 1},
                    "highest_elo": {"$max": "$elo"},
                    "lowest_elo": {"$min": "$elo"},
                    "average_elo": {"$avg": "$elo"}
                }
            }
        ]
        
        cursor = db_service.collection.aggregate(pipeline)
        stats_result = await cursor.to_list(length=1)
        
        if not stats_result:
            return {
                "total_users": 0,
                "highest_elo": 0,
                "lowest_elo": 0,
                "average_elo": 0,
                "rank_distribution": {}
            }
        
        stats = stats_result[0]
        
        # Get rank distribution
        rank_pipeline = [
            {
                "$match": {
                    "$or": [
                        {"rank_details.data.currenttierpatched": {"$exists": True, "$ne": None}},
                        {"rank_details.currenttierpatched": {"$exists": True, "$ne": None}}
                    ]
                }
            },
            {
                "$project": {
                    "tier": {
                        "$ifNull": ["$rank_details.data.currenttierpatched", "$rank_details.currenttierpatched"]
                    }
                }
            },
            {
                "$group": {
                    "_id": "$tier",
                    "count": {"$sum": 1}
                }
            },
            {
                "$sort": {"count": -1}
            }
        ]
        
        cursor = db_service.collection.aggregate(rank_pipeline)
        rank_distribution_result = await cursor.to_list(length=None)
        
        rank_distribution = {
            item["_id"]: item["count"] 
            for item in rank_distribution_result
        }
        
        response = {
            "total_users": stats["total_users"],
            "highest_elo": stats["highest_elo"],
            "lowest_elo": stats["lowest_elo"],
            "average_elo": round(stats["average_elo"], 2),
            "rank_distribution": rank_distribution
        }
        
        logger.info("Successfully fetched leaderboard statistics")
        return response
        
    except Exception as e:
        logger.error(f"Error fetching leaderboard statistics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while fetching statistics")