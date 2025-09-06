import asyncio
import logging
import os
from datetime import datetime
from typing import Optional, List, Dict, Any

import discord
from discord.ext import commands
import motor.motor_asyncio
from motor.motor_asyncio import AsyncIOMotorClient


# Define intents
intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.message_content = True


class ScriptFilter(logging.Filter):
    """Filter to only log messages from this script"""
    def filter(self, record):
        return record.pathname == __file__


def setup_logging(bot_name: str) -> logging.Logger:
    """Setup logging configuration for each bot"""
    logger = logging.getLogger(bot_name)
    logger.setLevel(logging.INFO)
    
    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)
    
    handler = logging.FileHandler(f'logs/{bot_name}_discord.log')
    handler.setLevel(logging.INFO)
    
    # Create a logging format
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%d/%m/%Y %H:%M:%S'
    )
    handler.setFormatter(formatter)
    
    handler.addFilter(ScriptFilter())
    logger.addHandler(handler)
    
    # Also add console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger


# Rank configuration
ALPHA_RANKS = ['Diamond', 'Ascendant', 'Radiant', 'Immortal']
OMEGA_RANKS = ['Bronze', 'Silver', 'Gold', 'Platinum', 'Iron']
RANK_NAMES_MAPPER = {
    'Iron': 'Iron',
    'Bronze': 'Brz',
    'Silver': 'Slv',
    'Gold': 'Gld',
    'Platinum': 'Plt',
    'Ascendant': 'Asc',
    'Diamond': 'Dia',
    'Immortal': 'Imm',
    'Radiant': 'Radiant'
}


class DiscordBotRunner:
    """Discord bot for updating user roles and nicknames based on Valorant ranks"""
    
    def __init__(self, bot_id: int, config: dict):
        """
        Initialize the Discord bot
        
        Args:
            bot_id: Bot identifier (1 or 2)
            config: Configuration dictionary with tokens and settings
        """
        self.bot_id = bot_id
        self.config = config
        self.logger = setup_logging(f'bot{bot_id}')
        
        # Create bot instance with command prefix
        self.bot = commands.Bot(command_prefix='!', intents=intents)
        
        # MongoDB connection
        self.db_client = None
        self.db = None
        self.collection = None
        
        # Register events
        self._register_events()
        
    def _register_events(self):
        """Register bot events"""
        
        @self.bot.event
        async def on_ready():
            self.logger.info(f'{self.bot.user} has connected to Discord!')
            # Initialize database connection
            await self._init_database()
            # Start the main update loop
            self.bot.loop.create_task(self.main_loop())
        
        # Only bot 1 handles new member joins
        if self.bot_id == 1:
            @self.bot.event
            async def on_member_join(member):
                guild = self.bot.get_guild(self.config['discord_guild_id'])
                if guild:
                    self.logger.info(f'New member joined: {member.name} (ID: {member.id})')
                    db_response = await self.get_all_players_from_db()
                    if db_response:
                        await self.update_discord_roles(member, db_response)
    
    async def _init_database(self):
        """Initialize MongoDB connection"""
        try:
            self.db_client = AsyncIOMotorClient(self.config['mongodb_uri'])
            self.db = self.db_client[self.config['mongodb_database']]
            self.collection = self.db[self.config['mongodb_collection']]
            
            # Test connection
            await self.db_client.admin.command('ping')
            self.logger.info("Successfully connected to MongoDB")
        except Exception as e:
            self.logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    async def get_all_players_from_db(self) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch all players from the database
        
        Returns:
            List of player documents or None if error
        """
        try:
            cursor = self.collection.find({})
            players = await cursor.to_list(length=None)
            self.logger.info(f"Successfully retrieved {len(players)} players from database")
            return players
        except Exception as e:
            self.logger.error(f"Failed to get players from database: {e}")
            return None
    
    async def update_database_discord_data(self, member: discord.Member, db_response: List[Dict[str, Any]]):
        """
        Update Discord ID and username in database if they've changed slightly
        
        Args:
            member: Discord member object
            db_response: List of player documents from database
        """
        discord_id = int(member.id)
        discord_username = member.name
        
        match_found = False
        
        for database_user in db_response:
            db_discord_id = database_user.get('discord_id')
            if not db_discord_id:
                continue
                
            db_discord_id = int(db_discord_id)
            db_username = database_user.get('discord_username', '')
            
            # Check if Discord ID is within range (handles slight ID changes)
            if abs(discord_id - db_discord_id) <= 200:
                match_found = True
                
                # Update if ID or username changed
                if db_discord_id != discord_id or db_username != discord_username:
                    try:
                        await self.collection.update_one(
                            {'_id': database_user['_id']},
                            {'$set': {
                                'discord_id': discord_id,
                                'discord_username': discord_username,
                                'updated_at': datetime.utcnow().isoformat() + 'Z'
                            }}
                        )
                        self.logger.info(
                            f"Updated database discord_id | {db_discord_id} --> {discord_id}, "
                            f"discord_username | {db_username} --> {discord_username}"
                        )
                    except Exception as e:
                        self.logger.error(f"Failed to update Discord data: {e}")
                break
        
        if not match_found:
            self.logger.info(f"Discord ID {discord_id} not found in database. Username: {discord_username}")
    
    async def update_nickname(self, member: discord.Member, global_name: str, rank_tier: str):
        """
        Update member's nickname with their rank
        
        Args:
            member: Discord member object
            global_name: Member's global display name
            rank_tier: Current rank tier
        """
        mapped_rank = RANK_NAMES_MAPPER.get(rank_tier, rank_tier)
        new_nickname = f"{global_name} ({mapped_rank})"
        
        # Limit nickname length to Discord's 32 character limit
        if len(new_nickname) > 32:
            # Truncate the name part, keeping the rank
            max_name_length = 32 - len(f" ({mapped_rank})")
            global_name = global_name[:max_name_length]
            new_nickname = f"{global_name} ({mapped_rank})"
        
        try:
            await member.edit(nick=new_nickname)
            self.logger.info(f"Updated display name for discord username: {member.name} -> {new_nickname}")
        except discord.errors.Forbidden:
            self.logger.warning(f"Bot does not have permissions to update display name for discord username: {member.name}")
        except Exception as e:
            self.logger.error(f"Error updating nickname for {member.name}: {e}")
    
    async def update_roles(self, member: discord.Member, new_roles: List[discord.Role]):
        """
        Update member's roles
        
        Args:
            member: Discord member object
            new_roles: List of new roles to assign
        """
        try:
            # Get all current roles except @everyone
            roles_to_remove = [role for role in member.roles if role.name != "@everyone"]
            
            if roles_to_remove:
                await member.remove_roles(*roles_to_remove)
                self.logger.info(f"{member.name} : Removed roles: {', '.join(role.name for role in roles_to_remove)}")
            else:
                self.logger.info(f"{member.name} : No roles to remove")
            
            if new_roles:
                # Filter out None values
                new_roles = [role for role in new_roles if role is not None]
                if new_roles:
                    await member.add_roles(*new_roles)
                    self.logger.info(f"{member.name} : Added roles: {', '.join(role.name for role in new_roles)}")
        
        except discord.errors.Forbidden:
            self.logger.warning(f"Bot does not have permissions to update roles for discord username: {member.name}")
        except discord.errors.NotFound as e:
            self.logger.error(f"Role not found in the server: {e}")
        except Exception as e:
            self.logger.error(f"Error updating roles for {member.name}: {e}")
    
    async def get_new_roles(self, member: discord.Member, rank_tier: str) -> List[discord.Role]:
        """
        Get the new roles for a member based on their rank
        
        Args:
            member: Discord member object
            rank_tier: Current rank tier
            
        Returns:
            List of Discord role objects
        """
        new_roles = []
        
        if rank_tier in ALPHA_RANKS:
            alpha_role = discord.utils.get(member.guild.roles, name="Alpha")
            rank_role = discord.utils.get(member.guild.roles, name=rank_tier)
            verified_role = discord.utils.get(member.guild.roles, name="Verified")
            new_roles = [alpha_role, rank_role, verified_role]
        elif rank_tier in OMEGA_RANKS:
            omega_role = discord.utils.get(member.guild.roles, name="Omega")
            rank_role = discord.utils.get(member.guild.roles, name=rank_tier)
            verified_role = discord.utils.get(member.guild.roles, name="Verified")
            new_roles = [omega_role, rank_role, verified_role]
        
        # Filter out None values
        new_roles = [role for role in new_roles if role is not None]
        return new_roles
    
    async def update_discord_roles(self, member: discord.Member, db_response: List[Dict[str, Any]]):
        """
        Update a member's Discord roles and nickname based on their Valorant rank
        
        Args:
            member: Discord member object
            db_response: List of player documents from database
        """
        global_name = member.global_name or member.name
        discord_id = int(member.id)
        discord_username = member.name
        
        # Find the user in db_response
        user_data = None
        for user in db_response:
            if user.get('discord_id') and int(user['discord_id']) == discord_id:
                user_data = user
                break
        
        if user_data:
            # Handle both new and legacy database schemas
            rank_details = user_data.get('rank_details', {})
            
            # Check if it's the legacy format (has 'data' field) or new format
            if 'data' in rank_details:
                # Legacy format: rank_details.data.currenttierpatched
                rank = rank_details.get('data', {}).get('currenttierpatched', 'Unknown')
            else:
                # New format: rank_details.currenttierpatched
                rank = rank_details.get('currenttierpatched', 'Unknown')
            
            # Extract tier name (e.g., "Diamond 3" -> "Diamond")
            rank_tier = rank.split(' ')[0] if rank != 'Unknown' else 'Unknown'
            
            # Update nickname
            await self.update_nickname(member, global_name, rank_tier)
            
            # Check for "Manual" role - skip role updates if present
            manual_role = discord.utils.get(member.guild.roles, name="Manual")
            if manual_role in member.roles:
                self.logger.info(f"Skipping role update for {discord_username} as they have 'Manual' role.")
                return
            
            # Get and update roles
            new_roles = await self.get_new_roles(member, rank_tier)
            await self.update_roles(member, new_roles)
        
        else:
            # User not found in database - mark as unverified
            unverified_role = discord.utils.get(member.guild.roles, name="Unverified")
            new_roles = [unverified_role] if unverified_role else []
            await self.update_roles(member, new_roles)
            await self.update_nickname(member, global_name, "Unverified")
    
    async def main_loop(self):
        """Main update loop that runs every 15 minutes"""
        await self.bot.wait_until_ready()
        
        while not self.bot.is_closed():
            try:
                guild = self.bot.get_guild(self.config['discord_guild_id'])
                if guild:
                    # Get all players from database
                    db_response = await self.get_all_players_from_db()
                    
                    if db_response:
                        # Sort members by ID for consistent splitting
                        members = sorted(guild.members, key=lambda member: member.id)
                        half_members = len(members) // 2
                        
                        # Split work between bots
                        if self.bot_id == 1:
                            target_members = members[:half_members]  # First half
                        else:
                            target_members = members[half_members:]  # Second half
                        
                        self.logger.info(f"Bot {self.bot_id} processing {len(target_members)} members")
                        
                        # Update roles for assigned members
                        for member in target_members:
                            if not member.bot:  # Skip bot accounts
                                await self.update_discord_roles(member, db_response)
                                await asyncio.sleep(0.5)  # Rate limiting
                        
                        # Bot 1 also updates database discord data for all members
                        if self.bot_id == 1:
                            self.logger.info("Bot 1 updating database Discord data for all members")
                            for member in members:
                                if not member.bot:
                                    await self.update_database_discord_data(member, db_response)
                                    await asyncio.sleep(0.5)  # Rate limiting
                    else:
                        self.logger.error("Failed to retrieve database response")
                
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}", exc_info=True)
            
            finally:
                self.logger.info("Sleeping for 15 minutes before next iteration.")
                await asyncio.sleep(15 * 60)  # 15 minutes
    
    async def run(self):
        """Run the bot"""
        token = self.config[f'discord_token_{self.bot_id}']
        await self.bot.start(token)
    
    async def close(self):
        """Close database connection and bot"""
        if self.db_client:
            self.db_client.close()
        await self.bot.close()