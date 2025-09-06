"""
Configuration management for the ValorantSL Player Updater Service
"""

import os
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class UpdaterConfig(BaseSettings):
    """Configuration settings for the updater service"""
    
    # MongoDB Configuration
    mongodb_uri: str = Field(description="MongoDB connection string")
    mongodb_database: str = Field(default="live", description="Database name")
    mongodb_collection: str = Field(default="user_leaderboard_complete", description="Collection name")
    
    # Riot API Configuration
    riot_api_base_url: str = Field(default="https://api.henrikdev.xyz", description="Henrik API base URL")
    riot_api_key: str = Field(description="Henrik API key")
    riot_region: str = Field(default="ap", description="Riot region (hardcoded to AP)")
    riot_platform: str = Field(default="pc", description="Riot platform")
    
    # Update Configuration
    update_interval_minutes: int = Field(default=30, description="Update interval in minutes")
    rate_limit_delay_seconds: float = Field(default=2.5, description="Delay between API calls")
    max_retries: int = Field(default=3, description="Maximum retries for API calls")
    
    # Logging Configuration
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="json", description="Log format (json|text)")
    
    class Config:
        env_file = "../backend/.env"  # Use the same .env as backend
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global configuration instance
config = UpdaterConfig()