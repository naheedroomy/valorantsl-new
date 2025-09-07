#!/bin/bash

# ValorantSL Production Deployment Script
# This script handles the deployment of all services in production

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

print_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

# Check if running as root (recommended for production)
if [[ $EUID -ne 0 ]]; then
   print_warning "This script is not running as root. Some operations might fail."
fi

# Parse command line arguments
OPERATION=${1:-deploy}
SERVICES=${2:-all}

case $OPERATION in
    deploy)
        print_status "Starting production deployment..."
        
        # Check if .env.production exists
        if [ ! -f .env.production ]; then
            print_error ".env.production file not found!"
            echo "Please create .env.production from .env.production.example"
            exit 1
        fi
        
        print_status "Building and starting services..."
        
        if [ "$SERVICES" == "all" ]; then
            docker compose -f docker-compose.prod.yml up -d --build
        else
            docker compose -f docker-compose.prod.yml up -d --build $SERVICES
        fi
        
        print_status "Waiting for services to be healthy..."
        sleep 10
        
        # Check service health
        docker compose -f docker-compose.prod.yml ps
        
        print_status "Deployment completed successfully!"
        print_status "Frontend: https://valorantsl.com"
        print_status "API: https://api.valorantsl.com"
        ;;
        
    stop)
        print_status "Stopping services..."
        docker compose -f docker-compose.prod.yml stop
        print_status "Services stopped."
        ;;
        
    restart)
        print_status "Restarting services..."
        if [ "$SERVICES" == "all" ]; then
            docker compose -f docker-compose.prod.yml restart
        else
            docker compose -f docker-compose.prod.yml restart $SERVICES
        fi
        print_status "Services restarted."
        ;;
        
    logs)
        if [ "$SERVICES" == "all" ]; then
            docker compose -f docker-compose.prod.yml logs -f --tail=100
        else
            docker compose -f docker-compose.prod.yml logs -f --tail=100 $SERVICES
        fi
        ;;
        
    status)
        print_status "Service Status:"
        docker compose -f docker-compose.prod.yml ps
        echo ""
        print_status "Resource Usage:"
        docker stats --no-stream
        ;;
        
    update)
        print_status "Pulling latest changes..."
        git pull origin master
        
        print_status "Rebuilding and redeploying services..."
        if [ "$SERVICES" == "all" ]; then
            docker compose -f docker-compose.prod.yml up -d --build
        else
            docker compose -f docker-compose.prod.yml up -d --build $SERVICES
        fi
        
        print_status "Cleaning up old images..."
        docker image prune -f
        
        print_status "Update completed!"
        ;;
        
    backup)
        print_status "Creating backup..."
        BACKUP_DIR="backups/$(date +'%Y%m%d_%H%M%S')"
        mkdir -p $BACKUP_DIR
        
        # Backup environment files
        cp .env.production $BACKUP_DIR/
        
        # Backup Docker volumes (if any)
        docker compose -f docker-compose.prod.yml exec -T updater tar czf - /app/logs 2>/dev/null > $BACKUP_DIR/updater_logs.tar.gz || true
        
        print_status "Backup created in $BACKUP_DIR"
        ;;
        
    clean)
        print_warning "This will remove all stopped containers, unused networks, and dangling images."
        read -p "Are you sure? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            docker system prune -f
            docker image prune -a -f
            print_status "Cleanup completed."
        fi
        ;;
        
    *)
        echo "Usage: $0 {deploy|stop|restart|logs|status|update|backup|clean} [service_name|all]"
        echo ""
        echo "Operations:"
        echo "  deploy  - Build and deploy services"
        echo "  stop    - Stop services"
        echo "  restart - Restart services"
        echo "  logs    - View service logs"
        echo "  status  - Check service status"
        echo "  update  - Pull latest code and redeploy"
        echo "  backup  - Create backup of configuration"
        echo "  clean   - Clean up Docker resources"
        echo ""
        echo "Services: nginx, backend, frontend, updater, discord-bot, all"
        echo ""
        echo "Examples:"
        echo "  $0 deploy             # Deploy all services"
        echo "  $0 restart backend    # Restart only backend"
        echo "  $0 logs discord-bot   # View discord-bot logs"
        exit 1
        ;;
esac