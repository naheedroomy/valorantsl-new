#!/bin/bash

# Script to force rebuild frontend with correct API URL

echo "Stopping frontend and nginx containers..."
docker compose -f docker-compose.prod.yml stop frontend nginx

echo "Removing old frontend container and image..."
docker compose -f docker-compose.prod.yml rm -f frontend
docker rmi valorantsl-new_frontend 2>/dev/null || true

echo "Rebuilding frontend with production API URL..."
docker compose -f docker-compose.prod.yml build --no-cache frontend

echo "Starting frontend and nginx..."
docker compose -f docker-compose.prod.yml up -d frontend nginx

echo "Checking container status..."
docker compose -f docker-compose.prod.yml ps frontend nginx

echo ""
echo "Rebuild complete! The frontend should now use https://api.valorantsl.com"
echo "Clear your browser cache and try accessing https://valorantsl.com"