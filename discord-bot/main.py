#!/usr/bin/env python3
"""
ValorantSL Discord Bot Service
Main entry point for running the Discord bots
"""

import asyncio
import signal
import sys
import logging
from typing import Optional

from app.discord_bots import DiscordBotRunner
from app.config import settings


# Setup main logger
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class BotManager:
    """Manages both Discord bot instances"""
    
    def __init__(self):
        self.bot1: Optional[DiscordBotRunner] = None
        self.bot2: Optional[DiscordBotRunner] = None
        self.running = False
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.running = False
        
        # Schedule shutdown
        asyncio.create_task(self.shutdown())
    
    async def shutdown(self):
        """Gracefully shutdown both bots"""
        logger.info("Shutting down Discord bots...")
        
        tasks = []
        if self.bot1:
            tasks.append(self.bot1.close())
        if self.bot2:
            tasks.append(self.bot2.close())
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        logger.info("Discord bots shut down successfully")
    
    async def run(self):
        """Run both Discord bots concurrently"""
        self.running = True
        
        # Create configuration for bots
        config = {
            'discord_token_1': settings.discord_token_1,
            'discord_token_2': settings.discord_token_2,
            'discord_guild_id': settings.discord_guild_id,
            'mongodb_uri': settings.mongodb_uri,
            'mongodb_database': settings.mongodb_database,
            'mongodb_collection': settings.mongodb_collection,
            'update_interval_minutes': settings.update_interval_minutes,
            'rate_limit_delay': settings.rate_limit_delay
        }
        
        # Initialize bots
        self.bot1 = DiscordBotRunner(bot_id=1, config=config)
        self.bot2 = DiscordBotRunner(bot_id=2, config=config)
        
        logger.info("Starting Discord Bot Service...")
        logger.info(f"Guild ID: {settings.discord_guild_id}")
        logger.info(f"MongoDB Database: {settings.mongodb_database}")
        logger.info(f"MongoDB Collection: {settings.mongodb_collection}")
        logger.info(f"Update Interval: {settings.update_interval_minutes} minutes")
        
        # Run both bots concurrently
        try:
            await asyncio.gather(
                self.bot1.run(),
                self.bot2.run()
            )
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        except Exception as e:
            logger.error(f"Error running bots: {e}", exc_info=True)
        finally:
            await self.shutdown()


async def main():
    """Main entry point"""
    manager = BotManager()
    await manager.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application terminated by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)