#!/bin/bash

# Docker Local Development Runner Script
# Usage: ./scripts/docker-run.sh [up|down|build|logs|restart]

set -e

ACTION=${1:-up}
ENV_FILE=".env.local"
COMPOSE_FILES="-f docker-compose.yml -f docker-compose.local.yml"

# Check if .env.local file exists
if [ ! -f "$ENV_FILE" ]; then
  echo "Error: $ENV_FILE not found!"
  echo "Please create the environment file first."
  exit 1
fi

echo "Gym Manager API - Local Development Environment"
echo "Using: $ENV_FILE"
echo ""

case $ACTION in
  up)
    echo "Starting local environment..."
    docker-compose --env-file "$ENV_FILE" $COMPOSE_FILES up -d
    echo "✓ Environment is running"
    echo ""
    echo "Access:"
    echo "  API: http://localhost:8000"
    echo "  Docs: http://localhost:8000/docs"
    echo "  Database: localhost:1433"
    echo ""
    docker-compose --env-file "$ENV_FILE" $COMPOSE_FILES ps
    ;;
  down)
    echo "Stopping local environment..."
    docker-compose --env-file "$ENV_FILE" $COMPOSE_FILES down
    echo "✓ Environment stopped"
    ;;
  build)
    echo "Building Docker images..."
    docker-compose --env-file "$ENV_FILE" $COMPOSE_FILES build --no-cache
    echo "✓ Images built successfully"
    ;;
  logs)
    docker-compose --env-file "$ENV_FILE" $COMPOSE_FILES logs -f
    ;;
  restart)
    echo "Restarting environment..."
    docker-compose --env-file "$ENV_FILE" $COMPOSE_FILES restart
    echo "✓ Environment restarted"
    ;;
  ps)
    docker-compose --env-file "$ENV_FILE" $COMPOSE_FILES ps
    ;;
  *)
    echo "Usage: $0 [up|down|build|logs|restart|ps]"
    echo ""
    echo "Commands:"
    echo "  up       - Start the local environment (default)"
    echo "  down     - Stop the local environment"
    echo "  build    - Build Docker images"
    echo "  logs     - View live logs"
    echo "  restart  - Restart all services"
    echo "  ps       - Show running containers"
    echo ""
    echo "Examples:"
    echo "  ./scripts/docker-run.sh up"
    echo "  ./scripts/docker-run.sh logs"
    echo "  ./scripts/docker-run.sh down"
    exit 1
    ;;
esac
