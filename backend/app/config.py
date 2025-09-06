from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings
import json


class Settings(BaseSettings):
    # MongoDB Configuration
    mongodb_uri: str = Field(default="mongodb://localhost:27017/")
    mongodb_database: str = Field(default="valorantsl")
    mongodb_collection: str = Field(default="user_leaderboard_complete")
    
    # Riot API Configuration
    riot_api_base_url: str = Field(default="https://api.henrikdev.xyz")
    riot_api_key: str = Field(default="")
    riot_region: str = Field(default="ap")
    riot_platform: str = Field(default="pc")
    
    # Application Configuration
    app_name: str = Field(default="ValorantSL Backend")
    app_version: str = Field(default="1.0.0")
    debug: bool = Field(default=True)
    
    # CORS Configuration
    cors_origins: str = Field(default='["http://localhost:3000","http://localhost:8080"]')
    
    # Discord OAuth Configuration
    discord_client_id: str = Field(default="")
    discord_client_secret: str = Field(default="")
    discord_redirect_uri: str = Field(default="http://localhost:3000/register")
    discord_oauth_url: str = Field(default="https://discord.com/api/oauth2/authorize")
    discord_api_endpoint: str = Field(default="https://discord.com/api/v10")
    
    class Config:
        env_file = "../.env"  # Use root-level .env file
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from consolidated .env

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins string to list"""
        try:
            return json.loads(self.cors_origins)
        except json.JSONDecodeError:
            return ["http://localhost:3000"]


def get_settings() -> Settings:
    return Settings()


settings = get_settings()