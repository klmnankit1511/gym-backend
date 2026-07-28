#!/bin/bash

# Database Volume Backup Script
# Creates a backup of the local SQL Server database

set -e

BACKUP_DIR=${1:-.}
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/gym_db_backup_${TIMESTAMP}.bak"
CONTAINER_NAME="gym-db-local"
SA_PASSWORD=${SA_PASSWORD:-GymAdmin@123!}

# Check if container is running
if ! docker ps | grep -q "$CONTAINER_NAME"; then
    echo "Error: Container $CONTAINER_NAME is not running"
    echo "Start it with: ./scripts/docker-run.sh $ENVIRONMENT up"
    exit 1
fi

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

echo "Creating database backup..."
echo "Backup file: $BACKUP_FILE"

# Create backup inside the container
docker exec $CONTAINER_NAME bash -c "
/opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P '$SA_PASSWORD' -Q \"
BACKUP DATABASE [gym] TO DISK = N'/var/opt/mssql/backup/gym_backup.bak'
  WITH NOFORMAT, NOINIT, NAME = N'Gym Backup', SKIP, NOREWIND, NOUNLOAD, STATS = 10
\"
" 2>&1 | grep -v "^$" || true

# Copy backup file from container to host
docker cp "$CONTAINER_NAME:/var/opt/mssql/backup/gym_backup.bak" "$BACKUP_FILE"

# Verify backup file exists and has content
if [ -f "$BACKUP_FILE" ] && [ -s "$BACKUP_FILE" ]; then
    SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo "✓ Database backup created successfully!"
    echo "✓ File: $BACKUP_FILE"
    echo "✓ Size: $SIZE"
    echo ""
    echo "To restore this backup:"
    echo "  ./scripts/restore-db.sh $ENVIRONMENT $BACKUP_FILE"
else
    echo "✗ Backup file not created or is empty"
    exit 1
fi
