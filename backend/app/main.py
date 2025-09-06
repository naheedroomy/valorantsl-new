from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from contextlib import asynccontextmanager
from datetime import datetime

from .config import settings
from .services.database import db_service
from .routers import registration, leaderboard, auth
from .routers.auth import discord

# Import Discord exceptions
from fastapi_discord import RateLimited, Unauthorized
from fastapi_discord.exceptions import ClientSessionNotInitialized

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events
    """
    # Startup
    logger.info("Starting ValorantSL Backend API")
    try:
        await db_service.connect()
        logger.info("Database connection established")
        await discord.init()
        logger.info("Discord OAuth client initialized")
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down ValorantSL Backend API")
    await db_service.disconnect()
    logger.info("Database connection closed")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Backend API for ValorantSL - A Valorant leaderboard system",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(registration.router)
app.include_router(leaderboard.router)
app.include_router(auth.router)


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "Internal server error",
            "status_code": 500
        }
    )


# Discord exception handlers
@app.exception_handler(Unauthorized)
async def unauthorized_error_handler(request, exc):
    return JSONResponse({"error": "Unauthorized"}, status_code=401)


@app.exception_handler(RateLimited)
async def rate_limit_error_handler(request, exc: RateLimited):
    return JSONResponse(
        {"error": "RateLimited", "retry": exc.retry_after, "message": exc.message}, 
        status_code=429
    )


@app.exception_handler(ClientSessionNotInitialized)
async def client_session_error_handler(request, exc: ClientSessionNotInitialized):
    logger.error(f"Discord client session not initialized: {exc}")
    return JSONResponse({"error": "Internal Error"}, status_code=500)


# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint - API health check
    """
    return {
        "message": "ValorantSL Backend API",
        "version": settings.app_version,
        "status": "running",
        "docs_url": "/docs" if settings.debug else "disabled"
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    try:
        # Test database connection
        await db_service.client.admin.command('ping')
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "unhealthy"
    
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "database": db_status,
        "version": settings.app_version,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


# API info endpoint
@app.get("/api/v1/info")
async def api_info():
    """
    API information endpoint
    """
    return {
        "api_name": settings.app_name,
        "version": settings.app_version,
        "endpoints": {
            "registration": "/api/v1/register",
            "user_lookup": "/api/v1/user/{puuid}",
            "user_refresh": "/api/v1/user/{puuid}/refresh",
            "leaderboard": "/api/v1/leaderboard",
            "top_players": "/api/v1/leaderboard/top/{count}",
            "search_user": "/api/v1/leaderboard/search/{discord_username}",
            "leaderboard_stats": "/api/v1/leaderboard/stats"
        },
        "documentation": "/docs" if settings.debug else "disabled",
        "status": "operational"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info"
    )