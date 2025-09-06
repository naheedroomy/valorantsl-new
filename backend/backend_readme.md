# ValorantSL Backend API Documentation

## 🎯 Overview

The ValorantSL Backend is a FastAPI-based REST API that powers a Valorant player leaderboard system. It integrates with the unofficial Riot Games API to fetch player data and stores it in MongoDB Atlas for efficient querying and ranking.

## 🏗️ Architecture

### Tech Stack
- **Framework**: FastAPI 0.115.12
- **Database**: MongoDB Atlas (Motor async driver)
- **HTTP Client**: HTTPX for Riot API integration
- **Configuration**: Pydantic Settings
- **Containerization**: Docker + Docker Compose
- **Authentication**: External Riot API with API key

### Project Structure
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py               # Environment configuration with Pydantic
│   ├── models/
│   │   ├── __init__.py
│   │   └── user.py             # Pydantic models for API requests/responses
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── registration.py     # User registration endpoints
│   │   └── leaderboard.py      # Leaderboard and stats endpoints
│   ├── services/
│   │   ├── __init__.py
│   │   ├── database.py         # MongoDB async operations
│   │   └── riot_api.py         # Riot Games API integration
│   └── utils/
│       └── __init__.py
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Container configuration
├── .env                        # Environment variables
└── backend_readme.md           # This documentation
```

## 🗄️ Database Configuration

### MongoDB Atlas Connection
- **URI**: Configured via `MONGODB_URI` environment variable
- **Database**: Configured via `MONGODB_DATABASE` environment variable
- **Collection**: `user_leaderboard_complete`
- **Current Records**: 247+ players

### Database Schema
Each user document contains:
```json
{
  "puuid": "unique-player-id",
  "name": "PlayerName",
  "tag": "TAG",
  "region": "ap",
  "discord_id": 123456789,
  "discord_username": "discord_user",
  "rank_details": {
    "data": {
      "currenttier": 20,
      "currenttierpatched": "Diamond 3",
      "elo": 1729,
      "ranking_in_tier": 29,
      "mmr_change_to_last_game": -11,
      "games_needed_for_rating": 0,
      "rank_protection_shields": 2,
      "leaderboard_placement": null
    },
    "status": 200
  },
  "peak_rank": {
    "season_short": "e10a2",
    "tier_name": "Ascendant 3",
    "rr": 10
  },
  "seasonal_ranks": [
    {
      "season_short": "e10a5",
      "end_tier_name": "Diamond 3",
      "wins": 18,
      "games": 26,
      "end_rr": 29
    }
  ],
  "updated_at": "2025-09-06T03:53:58.860168Z",
  "seasonal_extended_at": "2025-09-06T03:53:58.860168Z"
}
```

## 🔌 External API Integration

### Riot Games API (Unofficial)
- **Base URL**: `https://api.henrikdev.xyz`
- **API Key**: Configured via `RIOT_API_KEY` environment variable
- **Endpoint Used**: `GET /valorant/v3/by-puuid/mmr/{region}/{platform}/{puuid}`
- **Region**: `ap` (Asia Pacific)
- **Platform**: `pc`

### Data Transformation
The API response is transformed and mapped to our database schema:
- Account information (name, tag, PUUID)
- Current rank details (tier, ELO, RR)
- Peak rank across all seasons
- Historical seasonal performance data

## 📡 API Endpoints

### Core Endpoints

#### Health Check
```http
GET /health
```
**Response:**
```json
{
  "status": "healthy",
  "database": "healthy", 
  "version": "1.0.0",
  "timestamp": "2025-09-06T03:53:50.024931Z"
}
```

#### API Information
```http
GET /
GET /api/v1/info
```

### Registration Endpoints

#### Register New User
```http
POST /api/v1/register
Content-Type: application/json

{
  "puuid": "b7e20365-9977-51c2-858e-20275d45ddb9",
  "discord_id": 123456789,
  "discord_username": "testuser"
}
```

**Response:** Complete user profile with rank data, peak rank, and seasonal history.

#### Get User by PUUID
```http
GET /api/v1/user/{puuid}
```

#### Refresh User Data
```http
PUT /api/v1/user/{puuid}/refresh
```
Fetches fresh data from Riot API and updates the database.

### Leaderboard Endpoints

#### Get Paginated Leaderboard
```http
GET /api/v1/leaderboard?page=1&per_page=10
```

**Parameters:**
- `page`: Page number (1-based, default: 1)
- `per_page`: Results per page (1-200, default: 50)

**Response:**
```json
{
  "entries": [
    {
      "puuid": "22c8d906-22f7-5f26-9ee8-f9a22f1b53d9",
      "name": "Protoxype",
      "tag": "PRTXY",
      "discord_username": "protoxype",
      "current_tier": "Immortal 2",
      "elo": 2212,
      "rank_in_tier": 112,
      "peak_rank": "Immortal 3",
      "peak_season": "e7a3"
    }
  ],
  "total": 247,
  "page": 1,
  "per_page": 10,
  "total_pages": 25
}
```

#### Get Top N Players
```http
GET /api/v1/leaderboard/top/{count}
```
**Parameters:** `count` (1-100)

#### Search User by Discord Username
```http
GET /api/v1/leaderboard/search/{discord_username}
```

#### Get Leaderboard Statistics
```http
GET /api/v1/leaderboard/stats
```

**Response:**
```json
{
  "total_users": 247,
  "highest_elo": 2212,
  "lowest_elo": 0,
  "average_elo": 1249.91,
  "rank_distribution": {
    "Diamond 1": 25,
    "Platinum 1": 22,
    "Immortal 2": 2
  }
}
```

## 🔧 Configuration & Environment Variables

### Environment Variables (.env)
Create a `.env` file based on the `.env.example` template:

```bash
# MongoDB Configuration
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/database
MONGODB_DATABASE=your_database_name
MONGODB_COLLECTION=user_leaderboard_complete

# Riot API Configuration
RIOT_API_BASE_URL=https://api.henrikdev.xyz
RIOT_API_KEY=your_riot_api_key_here
RIOT_REGION=ap
RIOT_PLATFORM=pc

# Application Configuration
APP_NAME=ValorantSL Backend
APP_VERSION=1.0.0
DEBUG=true

# CORS Configuration
CORS_ORIGINS=["http://localhost:3000","http://localhost:8080"]
```

**⚠️ Important**: Never commit the `.env` file to version control. Use `.env.example` as a template.

### Pydantic Settings
Configuration is managed through `app/config.py` using Pydantic Settings for type safety and validation.

## 🐳 Docker Deployment

### Docker Compose Configuration
```yaml
services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: valorantsl-backend
    restart: unless-stopped
    environment:
      - MONGODB_URI=${MONGODB_URI}
      - MONGODB_DATABASE=${MONGODB_DATABASE}
      - MONGODB_COLLECTION=${MONGODB_COLLECTION}
      - RIOT_API_BASE_URL=${RIOT_API_BASE_URL}
      - RIOT_API_KEY=${RIOT_API_KEY}
      - RIOT_REGION=${RIOT_REGION}
      - RIOT_PLATFORM=${RIOT_PLATFORM}
      - APP_NAME=${APP_NAME}
      - APP_VERSION=${APP_VERSION}
      - DEBUG=${DEBUG}
      - CORS_ORIGINS=${CORS_ORIGINS}
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app:ro
    healthcheck:
      test: curl -f http://localhost:8000/health || exit 1
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s
```

### Deployment Commands
```bash
# Start the backend
cd valorantsl-new
docker compose up -d

# View logs
docker compose logs backend -f

# Stop the backend
docker compose down

# Rebuild and restart
docker compose down
docker compose build --no-cache
docker compose up -d
```

## 🚀 Getting Started

### Prerequisites
- Docker & Docker Compose
- MongoDB Atlas account (configured)
- Riot API access key

### Quick Start
1. **Clone the repository** (if applicable)
2. **Configure environment variables:**
   ```bash
   cp backend/.env.example backend/.env
   # Edit backend/.env file with your actual credentials:
   # - MongoDB Atlas connection string
   # - Riot API key
   # - Other configuration values
   ```
3. **Start the backend:**
   ```bash
   cd valorantsl-new
   docker compose up -d
   ```

### ⚠️ Security Setup
**IMPORTANT**: Before deployment, ensure:
- [ ] `.env` file is created from `.env.example`
- [ ] All placeholder values replaced with actual credentials
- [ ] `.env` file is added to `.gitignore` (already included)
- [ ] Never commit actual credentials to version control
4. **Test the API:**
   ```bash
   curl http://localhost:8000/health
   ```
5. **View documentation:** http://localhost:8000/docs

### Development Setup
```bash
# Create virtual environment
cd backend
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 📊 Performance & Monitoring

### Database Indexing
- Unique index on `puuid` field for fast lookups
- Compound index on `rank_details.data.elo` for leaderboard sorting

### Logging
- Structured logging with timestamps
- Debug level logging for development
- Request/response logging for API calls

### Health Checks
- Database connectivity monitoring
- API endpoint health verification
- Docker container health checks

## 🔒 Security Considerations

### API Key Management
- Riot API key stored as environment variable
- Never committed to version control
- Use `.env.example` as template, keep actual `.env` private

### Database Security
- MongoDB Atlas provides built-in security
- Connection string includes authentication credentials
- Network access restrictions via Atlas
- Sensitive connection details stored in environment variables

### CORS Configuration
- Configurable allowed origins
- Supports multiple frontend domains

## 🧪 Testing

### Manual Testing Examples

**Register User:**
```bash
curl -X POST "http://localhost:8000/api/v1/register" \
  -H "Content-Type: application/json" \
  -d '{"puuid": "b7e20365-9977-51c2-858e-20275d45ddb9", "discord_id": 123456789, "discord_username": "testuser"}'
```

**Get Leaderboard:**
```bash
curl "http://localhost:8000/api/v1/leaderboard?page=1&per_page=5"
```

**Search User:**
```bash
curl "http://localhost:8000/api/v1/leaderboard/search/protoxype"
```

## 📈 Current Statistics
- **Total Users**: 247+ registered players
- **Top Player**: Protoxype (Immortal 2, 2212 ELO)
- **Rank Distribution**: Diverse player base from Bronze to Immortal
- **API Response Time**: <2 seconds average
- **Database**: MongoDB Atlas (cloud-hosted)

## 🔄 Data Flow

1. **User Registration:**
   - Client sends PUUID + Discord info
   - Backend fetches data from Riot API
   - Data transformed to internal schema
   - User saved to MongoDB Atlas
   
2. **Leaderboard Generation:**
   - MongoDB aggregation pipeline
   - Sorted by ELO (descending)
   - Paginated results
   - Cached rankings

3. **Data Updates:**
   - Manual refresh via API endpoint
   - Fetches latest Riot API data
   - Updates existing user records

## 🛠️ Future Enhancements

- Automated data refresh scheduling
- Player statistics tracking
- Match history integration
- Real-time leaderboard updates
- Discord bot integration
- Advanced filtering options

## 📝 API Documentation

Interactive API documentation is available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

**Version**: 1.0.0  
**Last Updated**: September 6, 2025  
**Author**: ValorantSL Development Team