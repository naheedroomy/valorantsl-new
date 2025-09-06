import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Configuration settings for Discord Bot Service"""
    
    # Discord Configuration
    discord_token_1: str = Field(..., env='DISCORD_TOKEN_1')
    discord_token_2: str = Field(..., env='DISCORD_TOKEN_2')
    discord_guild_id: int = Field(..., env='DISCORD_GUILD_ID')
    
    # MongoDB Configuration
    mongodb_uri: str = Field(..., env='MONGODB_URI')
    mongodb_database: str = Field(default='live', env='MONGODB_DATABASE')
    mongodb_collection: str = Field(default='user_leaderboard_complete', env='MONGODB_COLLECTION')
    
    # Bot Configuration
    update_interval_minutes: int = Field(default=15, env='UPDATE_INTERVAL_MINUTES')
    rate_limit_delay: float = Field(default=0.5, env='RATE_LIMIT_DELAY')
    
    # Logging
    log_level: str = Field(default='INFO', env='LOG_LEVEL')
    
    class Config:
        # Use the .env file from the project root (parent directory)
        env_file = Path(__file__).parent.parent.parent / '.env'
        env_file_encoding = 'utf-8'
        case_sensitive = False


# Create settings instance
settings = Settings()