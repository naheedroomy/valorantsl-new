import os
from pydantic_settings import BaseSettings
from pydantic import Field


class UpdaterSettings(BaseSettings):
    """Configuration settings for the updater service"""
    
    # MongoDB Configuration
    mongodb_uri: str = Field(default="mongodb://localhost:27017")
    mongodb_database: str = Field(default="valorantsl")
    mongodb_collection: str = Field(default="user_leaderboard_complete")
    
    # Riot API Configuration
    riot_api_base_url: str = Field(default="https://api.henrikdev.xyz")
    riot_api_key: str = Field(default="")
    riot_region: str = Field(default="ap")
    riot_platform: str = Field(default="pc")
    
    # Update Configuration
    update_interval_minutes: int = Field(default=30)
    rate_limit_delay: float = Field(default=2.5)
    batch_size: int = Field(default=50)
    max_retries: int = Field(default=3)
    retry_delay: float = Field(default=5.0)
    
    # Logging Configuration
    log_level: str = Field(default="INFO")
    log_file: str = Field(default="updater.log")
    
    class Config:
        env_file = "../.env"  # Use root-level .env file
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from the .env file


# Global settings instance
settings = UpdaterSettings()