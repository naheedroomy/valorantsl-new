# ValorantSL Discord Bot Service

A dual-bot Discord service that automatically updates user roles and nicknames based on their Valorant competitive ranks. The service directly queries MongoDB for player data and manages Discord server members accordingly.

## Features

- **Dual Bot Architecture**: Two bots work in parallel to handle large Discord servers efficiently
- **Automatic Role Assignment**: Assigns Alpha/Omega team roles and rank-specific roles
- **Nickname Updates**: Updates Discord nicknames with current rank abbreviations
- **Database Sync**: Bot 1 syncs Discord IDs and usernames back to the database
- **New Member Handling**: Automatically processes new members joining the server
- **Manual Role Override**: Respects "Manual" role for users with custom role management
- **Rate Limiting**: Built-in delays to respect Discord API rate limits
- **Comprehensive Logging**: Detailed logging for debugging and monitoring

## Architecture

The service uses two Discord bots to distribute the workload:
- **Bot 1**: Processes first half of members, handles new joins, syncs Discord data to database
- **Bot 2**: Processes second half of members

Both bots run concurrently and update every 15 minutes.

## Rank System

### Team Assignment
- **Alpha Team**: Diamond, Ascendant, Radiant, Immortal
- **Omega Team**: Iron, Bronze, Silver, Gold, Platinum

### Rank Abbreviations
- Iron → Iron
- Bronze → Brz
- Silver → Slv
- Gold → Gld
- Platinum → Plt
- Diamond → Dia
- Ascendant → Asc
- Immortal → Imm
- Radiant → Radiant

## Prerequisites

- Python 3.11+
- MongoDB database with player data
- Discord server with appropriate roles created
- Two Discord bot applications created

## Required Discord Roles

Ensure these roles exist in your Discord server:
- `Alpha` - For high-tier players
- `Omega` - For standard-tier players
- `Verified` - For registered players
- `Unverified` - For non-registered members
- `Manual` - For users with custom role management
- Individual rank roles: `Iron`, `Bronze`, `Silver`, `Gold`, `Platinum`, `Diamond`, `Ascendant`, `Immortal`, `Radiant`

## Installation

### Local Development

1. Clone the repository and navigate to the discord-bot directory:
```bash
cd discord-bot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables in the **root project `.env` file** (not in discord-bot directory):
```bash
# Edit the .env file in the project root
nano ../.env
```

Add these Discord Bot variables to the root `.env`:
```env
# Discord Bot Configuration
DISCORD_TOKEN_1=your_first_bot_token
DISCORD_TOKEN_2=your_second_bot_token
DISCORD_GUILD_ID=your_discord_server_id

# Bot Settings (optional - these have defaults)
UPDATE_INTERVAL_MINUTES=15
RATE_LIMIT_DELAY=0.5
LOG_LEVEL=INFO
```

Note: MongoDB configuration is already in the root `.env` and is shared with backend/updater services.

4. Run the service:
```bash
python main.py
```

### Docker Deployment

1. Build the Docker image:
```bash
docker build -t valorantsl-discord-bot .
```

2. Run with Docker (from project root):
```bash
docker run -d \
  --name valorantsl-discord-bot \
  --env-file .env \
  --restart unless-stopped \
  -v $(pwd)/discord-bot/logs:/app/logs \
  valorantsl-discord-bot
```

### Docker Compose (Recommended)

Add to your `docker-compose.yml` in the project root:

```yaml
discord-bot:
  build: ./discord-bot
  container_name: valorantsl-discord-bot
  restart: unless-stopped
  env_file:
    - ./.env  # Use root .env file
  volumes:
    - ./discord-bot/logs:/app/logs
  networks:
    - valorantsl-network
```

## Database Schema

The service supports both new and legacy database schemas:

### New Schema
```json
{
  "discord_id": 123456789,
  "discord_username": "username",
  "rank_details": {
    "currenttierpatched": "Diamond 3",
    "current_tier": 20,
    "elo": 1750
  }
}
```

### Legacy Schema
```json
{
  "discord_id": 123456789,
  "discord_username": "username",
  "rank_details": {
    "data": {
      "currenttierpatched": "Diamond 3",
      "currenttier": 20,
      "elo": 1750
    }
  }
}
```

## Bot Permissions

Ensure both bots have the following Discord permissions:
- View Channels
- Manage Nicknames
- Manage Roles
- View Server Members
- Read Messages

## Monitoring

### Logs
Logs are stored in the `logs/` directory:
- `bot1_discord.log` - Bot 1 activity
- `bot2_discord.log` - Bot 2 activity

### Health Check
The Docker container includes a health check that verifies Python is running correctly.

## Troubleshooting

### Bot not updating roles
1. Check bot has "Manage Roles" permission
2. Ensure bot's role is higher than roles it needs to manage
3. Verify role names match exactly (case-sensitive)

### Database connection issues
1. Verify MongoDB URI is correct
2. Check network connectivity to MongoDB
3. Ensure database and collection names are correct

### Rate limiting
- Default delay is 0.5 seconds between operations
- Increase `RATE_LIMIT_DELAY` if hitting Discord rate limits

## Development

### Project Structure
```
discord-bot/
├── app/
│   ├── __init__.py
│   ├── config.py           # Configuration management
│   └── discord_bots.py     # Main bot logic
├── logs/                   # Log files (created at runtime)
├── main.py                # Entry point
├── requirements.txt       # Python dependencies
├── Dockerfile            # Container configuration
├── .env.example          # Environment variables template
└── README.md            # This file
```

### Adding New Features
1. Modify `app/discord_bots.py` for bot logic
2. Update `app/config.py` for new configuration options
3. Test locally before deploying

## Support

For issues or questions, please check the logs first, then create an issue in the repository with:
- Log excerpts showing the error
- Your configuration (without sensitive data)
- Steps to reproduce the issue