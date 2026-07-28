#!/bin/bash
set -e

echo "Starting Gym Manager API..."

# The local SQL Server container needs its application database created.
# Azure SQL databases are provisioned separately and should leave this disabled.
if [ "${CREATE_DATABASE:-false}" = "true" ]; then
    echo "Ensuring application database exists..."
    python -m scripts.create_database
fi

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Optional: Load dummy data if flag is set
# Note: Dummy data is loaded via alembic migrations or manually via SQL scripts
if [ "${LOAD_DUMMY_DATA}" = "true" ]; then
    echo "Note: Dummy data can be loaded via: scripts/init-db.sql"
fi

# Start the application
echo "Starting FastAPI application..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
