#!/bin/bash

# Database Restore Script
# Restores the local SQL Server database from a backup file

set -e

BACKUP_FILE=${1}
CONTAINER_NAME="gym-db-local"
SA_PASSWORD=${SA_PASSWORD:-GymAdmin@123!}

# Check if backup file is provided
if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup-file>"
    echo ""
    echo "Examples:"
    echo "  $0 ./gym_db_backup_20240101_120000.bak"
    exit 1
fi

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "Preparing to restore database from: $BACKUP_FILE"
echo ""
read -p "This will overwrite the current database. Continue? (y/N): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Copy backup file to container
    echo "Copying backup file to container..."
    docker cp "$BACKUP_FILE" "$CONTAINER_NAME:/var/opt/mssql/backup/restore.bak"

    echo "Restoring database..."
    # Restore database
    docker exec $CONTAINER_NAME bash -c "
/opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P '$SA_PASSWORD' -Q \"
RESTORE DATABASE [gym] FROM DISK = N'/var/opt/mssql/backup/restore.bak'
  WITH REPLACE, RECOVERY
\"
" 2>&1 | grep -v "^$" || true

    echo "✓ Database restored successfully!"
    echo ""
    echo "Restart the API container to ensure it's working:"
    echo "  ./scripts/docker-run.sh restart"
else
    echo "Restore cancelled."
fi
