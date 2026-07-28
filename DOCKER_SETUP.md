# Docker Local Development Setup

This project uses Docker for **local development only**. For production deployment, update credentials in `.env` and deploy separately.

## Quick Start

### Start Local Environment

```bash
./scripts/docker-run.sh up
```

This starts:
- **FastAPI server** on `http://localhost:8000`
- **SQL Server 2022** on `localhost:1433`
- **Automatic migrations** and dummy data loading

### Access the API

```
API: http://localhost:8000
Docs: http://localhost:8000/docs
ReDoc: http://localhost:8000/redoc
Database: localhost:1433 (user: sa, password: GymAdmin@123!)
```

## File Structure

```
gym-backend/
├── Dockerfile                  # Multi-stage build
├── docker-compose.yml          # Base services (API + Database)
├── docker-compose.local.yml    # Local overrides
├── .env.local                  # Local configuration
└── scripts/
    └── docker-run.sh           # Helper script
```

## Helper Script Usage

```bash
# Start environment
./scripts/docker-run.sh up

# Stop environment
./scripts/docker-run.sh down

# View logs
./scripts/docker-run.sh logs

# Build images
./scripts/docker-run.sh build

# Restart services
./scripts/docker-run.sh restart

# Show running containers
./scripts/docker-run.sh ps
```

## Local Environment

- **Database**: SQL Server 2022 (Docker container)
- **API Server**: FastAPI with auto-reload
- **Migrations**: Run automatically on startup
- **Dummy Data**: Loads automatically (70+ test records)
- **Logging**: DEBUG level
- **CORS**: Allows `localhost:3000` for React frontend

## Database Migrations

Migrations run **automatically** when you start the environment. To run manually:

```bash
# Inside the API container
./scripts/docker-run.sh ps
docker exec gym-api-local alembic upgrade head

# Or if running locally without Docker
alembic upgrade head
uvicorn app.main:app --reload
```

## Health Checks

```bash
# View running services
./scripts/docker-run.sh ps

# Check API health
curl http://localhost:8000/health

# Check SQL Server health
docker exec gym-db-local /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P GymAdmin@123! -Q "SELECT 1"
```

## Production Deployment (Later)

When ready to deploy to production:

1. Create Azure resources:
   - Azure SQL Database
   - Azure Cosmos DB (if needed)
   - Azure Container Registry (optional)

2. Create `.env.prod` with:
   ```bash
   DATABASE_URL=mssql+pyodbc://username:password@server.database.windows.net:1433/gym?driver=ODBC+Driver+18+for+SQL+Server
   COSMOS_ENDPOINT=https://your-cosmos.documents.azure.com:443/
   COSMOS_KEY=your-key
   SECRET_KEY=<generate-strong-random-key>
   CORS_ORIGINS=["https://yourdomain.com"]
   ```

3. Deploy using Docker, Kubernetes, or Azure App Service

4. **Never commit `.env.prod` to git** - use CI/CD secrets instead

## Troubleshooting

### Database Connection Timeout

Wait 30 seconds for SQL Server to start:
```bash
./scripts/docker-run.sh logs
```

### Port Already in Use

Change the port mapping in `docker-compose.local.yml`:
```yaml
ports:
  - "8001:8000"  # Map to 8001 instead of 8000
```

### ODBC Driver Not Found

The Dockerfile includes the ODBC driver. If running locally without Docker:

```bash
# macOS
brew install freetds

# Ubuntu/Debian
sudo apt-get install freetds-dev
```

### Permission Denied on Scripts

```bash
chmod +x scripts/docker-run.sh
```

## View Logs

```bash
# All services
./scripts/docker-run.sh logs

# Specific service
docker logs gym-api-local
docker logs gym-db-local

# Follow logs in real-time
./scripts/docker-run.sh logs
# Press Ctrl+C to exit
```

## Next Steps

1. **Start**: `./scripts/docker-run.sh up`
2. **Check**: `curl http://localhost:8000/docs`
3. **Develop**: Edit `app/` files - auto-reload enabled
4. **Test**: Create API routes and test with Swagger UI
5. **Backup**: Use `./scripts/backup-db.sh local ./backups`
6. **Deploy**: Add `.env.prod` when ready for production

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Azure SQL Documentation](https://docs.microsoft.com/en-us/azure/azure-sql/)
- [Azure Cosmos DB Documentation](https://docs.microsoft.com/en-us/azure/cosmos-db/)
