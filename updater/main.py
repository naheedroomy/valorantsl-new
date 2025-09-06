#!/usr/bin/env python3
"""
ValorantSL Player Updater Service

A comprehensive service that automatically updates player ranks and statistics
from the Riot Games API every 30 minutes with proper rate limiting.

Usage:
    python -m updater.main                    # Run scheduled updates
    python -m updater.main --once            # Run update once and exit
    python -m updater.main --test PUUID      # Test update for specific player
"""

import asyncio
import logging
import argparse
import signal
import sys
from datetime import datetime
from pathlib import Path
import schedule
import time

try:
    from .config import settings
    from .updater import player_updater
except ImportError:
    from config import settings
    from updater import player_updater


class UpdaterService:
    """Main service orchestrator"""
    
    def __init__(self):
        self.running = False
        self.setup_logging()
        self.setup_signal_handlers()
    
    def setup_logging(self):
        """Configure comprehensive logging"""
        import os
        
        # Configure logging
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        # Console handler (always available)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(log_format)
        console_handler.setFormatter(console_formatter)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, settings.log_level.upper()))
        root_logger.addHandler(console_handler)
        
        # Only add file handler if not in Docker or if logs directory is writable
        try:
            if not os.environ.get('DOCKER_CONTAINER'):
                # Create logs directory
                log_dir = Path(__file__).parent / "logs"
                log_dir.mkdir(exist_ok=True)
                
                # File handler
                log_file = log_dir / settings.log_file
                file_handler = logging.FileHandler(log_file, encoding='utf-8')
                file_handler.setLevel(logging.DEBUG)
                file_formatter = logging.Formatter(log_format)
                file_handler.setFormatter(file_formatter)
                root_logger.addHandler(file_handler)
        except (OSError, PermissionError):
            # If file logging fails, continue with console logging only
            pass
        
        # Reduce noise from external libraries
        logging.getLogger('httpx').setLevel(logging.WARNING)
        logging.getLogger('httpcore').setLevel(logging.WARNING)
        
        logging.info(f"Logging configured - Level: {settings.log_level}")
    
    def setup_signal_handlers(self):
        """Setup graceful shutdown handlers"""
        def signal_handler(signum, frame):
            logging.info(f"Received signal {signum}, shutting down gracefully...")
            self.running = False
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def scheduled_update(self):
        """Wrapper for scheduled updates"""
        try:
            logging.info("🚀 Starting scheduled player update")
            stats = asyncio.run(player_updater.update_all_players())
            player_updater.log_update_summary(stats)
            
            # Log next scheduled update
            next_run = schedule.next_run()
            if next_run:
                logging.info(f"⏰ Next update scheduled for: {next_run}")
            
        except Exception as e:
            logging.error(f"Error during scheduled update: {e}")
    
    async def run_once(self) -> bool:
        """Run update once and return success status"""
        try:
            logging.info("🚀 Running single update")
            stats = await player_updater.update_all_players()
            player_updater.log_update_summary(stats)
            
            return stats.get('success_rate', 0) > 0
            
        except Exception as e:
            logging.error(f"Error during single update: {e}")
            return False
    
    async def test_single_player(self, puuid: str) -> bool:
        """Test update for a single player"""
        try:
            logging.info(f"🧪 Testing update for player: {puuid}")
            success = await player_updater.update_single_player_by_puuid(puuid)
            
            if success:
                logging.info("✅ Test update completed successfully")
            else:
                logging.error("❌ Test update failed")
            
            return success
            
        except Exception as e:
            logging.error(f"Error during test update: {e}")
            return False
    
    def run_scheduler(self):
        """Run the scheduled service"""
        logging.info("🎯 ValorantSL Player Updater Service Starting")
        logging.info(f"📅 Update interval: {settings.update_interval_minutes} minutes")
        logging.info(f"⏱️ Rate limit delay: {settings.rate_limit_delay} seconds")
        logging.info(f"🔄 Max retries: {settings.max_retries}")
        logging.info(f"🌍 Region: {settings.riot_region.upper()}")
        
        # Schedule the update job
        schedule.every(settings.update_interval_minutes).minutes.do(self.scheduled_update)
        
        # Run initial update
        logging.info("🏁 Running initial update...")
        self.scheduled_update()
        
        # Main scheduler loop
        self.running = True
        logging.info("✅ Scheduler started, waiting for next update...")
        
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(1)  # Check every second
                
            except KeyboardInterrupt:
                logging.info("Keyboard interrupt received")
                break
            except Exception as e:
                logging.error(f"Error in scheduler loop: {e}")
                time.sleep(5)  # Wait before retry
        
        logging.info("🛑 ValorantSL Player Updater Service Stopped")
    
    def print_service_info(self):
        """Print service information"""
        print("=" * 60)
        print("🎮 ValorantSL Player Updater Service")
        print("=" * 60)
        print(f"📊 Database: {settings.mongodb_database}")
        print(f"📁 Collection: {settings.mongodb_collection}")
        print(f"🌐 API Base URL: {settings.riot_api_base_url}")
        print(f"🌍 Region: {settings.riot_region.upper()}")
        print(f"⏰ Update Interval: {settings.update_interval_minutes} minutes")
        print(f"⏱️ Rate Limit: {settings.rate_limit_delay}s between players")
        print(f"🔄 Max Retries: {settings.max_retries}")
        print(f"📝 Log Level: {settings.log_level}")
        print("=" * 60)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="ValorantSL Player Updater Service",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m updater.main                    # Run scheduled updates
  python -m updater.main --once            # Run update once and exit
  python -m updater.main --test PUUID      # Test update for specific player
  python -m updater.main --info            # Show service information
        """
    )
    
    parser.add_argument(
        '--once',
        action='store_true',
        help='Run update once and exit'
    )
    
    parser.add_argument(
        '--test',
        type=str,
        metavar='PUUID',
        help='Test update for a specific player PUUID'
    )
    
    parser.add_argument(
        '--info',
        action='store_true',
        help='Show service configuration and exit'
    )
    
    args = parser.parse_args()
    
    service = UpdaterService()
    
    if args.info:
        service.print_service_info()
        return
    
    if args.test:
        success = asyncio.run(service.test_single_player(args.test))
        sys.exit(0 if success else 1)
    
    if args.once:
        success = asyncio.run(service.run_once())
        sys.exit(0 if success else 1)
    
    # Default: run scheduler
    service.run_scheduler()


if __name__ == "__main__":
    main()