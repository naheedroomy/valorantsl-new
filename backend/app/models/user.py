from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class UserRegistration(BaseModel):
    """Input model for user registration"""
    puuid: str = Field(..., description="Player Unique User ID")
    discord_id: int = Field(..., description="Discord user ID")
    discord_username: str = Field(..., description="Discord username")


class SeasonalRank(BaseModel):
    """Model for seasonal rank information"""
    season_short: str = Field(..., description="Season short name (e.g., e10a2)")
    end_tier_name: str = Field(..., description="End tier name (e.g., Diamond 3)")
    wins: int = Field(..., description="Number of wins in this season")
    games: int = Field(..., description="Total games played in this season")
    end_rr: int = Field(..., description="Rank rating at end of season")


class PeakRank(BaseModel):
    """Model for peak rank information"""
    season_short: str = Field(..., description="Season when peak was achieved")
    tier_name: str = Field(..., description="Peak rank tier name")
    rr: int = Field(..., description="Rank rating at peak")


class RankData(BaseModel):
    """Current rank details data"""
    currenttier: int = Field(..., description="Current tier ID")
    currenttierpatched: str = Field(..., description="Current tier name")
    elo: int = Field(..., description="Current ELO rating")
    ranking_in_tier: int = Field(..., description="RR within current tier")
    mmr_change_to_last_game: int = Field(..., description="MMR change from last game")
    games_needed_for_rating: int = Field(..., description="Games needed for rating")
    rank_protection_shields: int = Field(..., description="Rank protection shields")
    leaderboard_placement: Optional[int] = Field(None, description="Leaderboard placement if applicable")


class RankDetails(BaseModel):
    """Model for rank details with status"""
    data: RankData = Field(..., description="Rank data")
    status: int = Field(..., description="API response status code")


class UserInDB(BaseModel):
    """Complete user model as stored in database"""
    puuid: str = Field(..., description="Player Unique User ID")
    name: str = Field(..., description="Player in-game name")
    tag: str = Field(..., description="Player tag/discriminator")
    region: str = Field(..., description="Player region")
    discord_id: int = Field(..., description="Discord user ID")
    discord_username: str = Field(..., description="Discord username")
    rank_details: RankDetails = Field(..., description="Current rank information")
    updated_at: datetime = Field(..., description="Last update timestamp")
    peak_rank: PeakRank = Field(..., description="Peak rank achieved")
    seasonal_extended_at: datetime = Field(..., description="Seasonal data last updated")
    seasonal_ranks: List[SeasonalRank] = Field(..., description="Historical seasonal ranks")
    last_played_match: Optional[str] = Field(None, description="Last competitive match date (ISO format)")


class UserResponse(BaseModel):
    """Response model for user data (excludes sensitive info)"""
    puuid: str
    name: str
    tag: str
    region: str
    discord_username: str
    rank_details: RankDetails
    peak_rank: PeakRank
    seasonal_ranks: List[SeasonalRank]
    updated_at: datetime
    last_played_match: Optional[str] = None


class LeaderboardEntry(BaseModel):
    """Model for leaderboard entries"""
    puuid: str
    name: str
    tag: str
    discord_username: str
    current_tier: Optional[str] = None
    elo: Optional[int] = None
    rank_in_tier: Optional[int] = None
    peak_rank: Optional[str] = None
    peak_season: Optional[str] = None
    last_played_match: Optional[str] = None


class LeaderboardResponse(BaseModel):
    """Response model for leaderboard with pagination"""
    entries: List[LeaderboardEntry]
    total: int
    page: int
    per_page: int
    total_pages: int


class RegistrationResponse(BaseModel):
    """Response model for successful registration"""
    message: str
    user: UserResponse