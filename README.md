# Gym Manager API — Multi-Tenant SaaS Backend

FastAPI backend for the multi-tenant Gym Member Management System.

**Current Status**: Phase 1 Infrastructure Foundation
- ✅ Multi-tenant schema with Tenants, Branches, Users, Roles
- ✅ JWT authentication with refresh tokens and audit logging
- ✅ SQL Server support (Azure SQL production, local Docker dev)
- ✅ Cosmos DB audit logs (Azure Cosmos production, local emulator dev)
- ✅ Alembic database migrations
- ✅ API versioning (/api/v1/)
- ⏳ Member management (next)
- ⏳ Membership plans & renewals (next)
- ⏳ Attendance & QR check-in (next)

---

## Tech Stack

- **Framework**: FastAPI 0.104.1
- **ORM**: SQLAlchemy 2.0
- **Database**: Azure SQL / SQL Server 2022
- **NoSQL**: Azure Cosmos DB / Cosmos Emulator
- **Migrations**: Alembic 1.13
- **Auth**: JWT + Refresh Tokens (httpOnly cookies)
- **Audit Logs**: Async write to Cosmos DB

---

## Prerequisites

### System Requirements

- Python 3.9+
- Docker & Docker Compose
- **macOS only**: ODBC driver for SQL Server
  ```bash
  brew install unixodbc
  brew tap microsoft/mssql-release
  brew install msodbcsql18 mssql-tools18
  ```

---

## Local Setup (Docker)

### 1. Clone & Navigate

```bash
cd gym-backend
```

### 2. Install Python Dependencies

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Create `.env` File

```bash
cp .env.example .env
```

Edit `.env` if needed (defaults are already set for local Docker):
- `DATABASE_URL`: Points to `localhost:1433` (SQL Server container)
- `COSMOS_ENDPOINT`: Points to `https://localhost:8081/` (Cosmos Emulator container)
- `COSMOS_KEY`: Well-known emulator key (do not change)

### 4. Start Docker Containers

```bash
docker compose up -d
```

Verify containers are healthy:
```bash
docker compose ps
```

Both services should show `healthy` status. Wait 30-60 seconds for SQL Server to fully initialize.

### 5. Run Database Migrations

```bash
alembic upgrade head
```

This creates:
- `tenants` table (multi-tenant isolation)
- `branches` table
- `roles` table (global: OWNER, MANAGER, RECEPTIONIST, etc.)
- `users` table (with `tenant_id` foreign key)
- `user_roles` junction table

### 6. Seed Initial Data

```bash
python scripts/seed_owner.py
```

Output:
```
✓ Created role: SUPER_ADMIN
✓ Created role: OWNER
✓ Created role: MANAGER
✓ Created role: RECEPTIONIST
✓ Created role: TRAINER
✓ Created role: ACCOUNTANT
✓ Created role: MEMBER

✓ Created tenant:
  Name: Demo Gym
  Slug: demo-gym
  Tenant ID: <uuid>

✓ Created branch:
  Name: Main Branch
  Branch ID: <uuid>

✓ Created owner account:
  Email: owner@example.com
  Password: owner123
  Tenant: demo-gym
  User ID: usr_<hex>
```

### 7. Start the API Server

```bash
uvicorn app.main:app --reload
```

Server runs on `http://localhost:8000`

---

## API Documentation

### Health Check (Unversioned)

```bash
curl http://localhost:8000/health
```

Response:
```json
{"status": "ok", "version": "1.0.0"}
```

### Authentication

#### Register

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "member@example.com",
    "password": "SecurePass123!",
    "full_name": "John Doe",
    "tenant_slug": "demo-gym"
  }'
```

Response:
```json
{
  "id": "usr_<hex>",
  "tenant_id": "<uuid>",
  "email": "member@example.com",
  "full_name": "John Doe",
  "roles": ["MEMBER"]
}
```

#### Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "owner@example.com",
    "password": "owner123"
  }' \
  -c cookies.txt
```

Response includes:
- `access_token`: Use in Authorization header
- `refresh_token`: Set as httpOnly cookie automatically
- `user`: User object with `tenant_id`

#### Get Current User

```bash
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer <access_token>"
```

#### Logout

```bash
curl -X POST http://localhost:8000/api/v1/auth/logout \
  -H "Authorization: Bearer <access_token>" \
  -b cookies.txt
```

### Dashboard (Requires Auth)

```bash
curl http://localhost:8000/api/v1/dashboard/summary \
  -H "Authorization: Bearer <access_token>"
```

Response:
```json
{
  "tenant_id": "<uuid>",
  "total_members": 0,
  "active_memberships": 0,
  "today_attendance": 0,
  "monthly_revenue": 0.0
}
```

---

## Interactive API Docs

When the server is running:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## Database Migrations (Alembic)

### View Migration Status

```bash
alembic current
alembic history
```

### Create a New Migration

After updating models in `app/models/`, generate a migration:

```bash
alembic revision --autogenerate -m "Add payment table"
```

Review the generated file in `alembic/versions/2026_07_25_<seq>_<message>.py`, then apply:

```bash
alembic upgrade head
```

### Downgrade

```bash
alembic downgrade -1  # Revert one migration
alembic downgrade base  # Revert all
```

---

## Cosmos DB Audit Logs

Audit logs are automatically written on:
- User registration
- User login
- User logout
- Member create/update/delete (once Member module is built)
- Payment operations
- Other sensitive actions

### Query Audit Logs (Local Emulator)

**Option 1: Azure Cosmos Emulator Data Explorer**
```
https://localhost:8081/_explorer/index.html
```
- Database: `gym_audit`
- Container: `audit_logs`
- Partition key: `/tenant_id`

**Option 2: Via API (future)**
Once the audit endpoint is created:
```bash
curl http://localhost:8000/api/v1/audit-logs \
  -H "Authorization: Bearer <access_token>"
```

---

## Multi-Tenant Model

### Tenant Isolation

- Each `Tenant` is a separate gym (or gym organization)
- Each `User` belongs to **exactly one** `Tenant` (`user.tenant_id` foreign key)
- Each `Branch` belongs to a `Tenant` (e.g., main location, satellite location)
- Queries automatically filter by `current_user.tenant_id` to prevent cross-tenant data access

### Example Query Pattern

```python
# In any module:
from app.api.deps import get_current_user
from app.models.member import Member

@router.get("/members")
async def list_members(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Only fetch members for this user's tenant
    members = db.query(Member).filter(
        Member.tenant_id == current_user.tenant_id
    ).all()
    return members
```

### Roles (Global Catalog)

Roles are defined globally and reused across all tenants:
- `SUPER_ADMIN`: Platform administrator
- `OWNER`: Gym owner (can see all branches & staff)
- `MANAGER`: Branch manager
- `RECEPTIONIST`: Check-in & registration
- `TRAINER`: Assigned members
- `ACCOUNTANT`: Payments & reports
- `MEMBER`: Gym member

---

## Environment Variables

| Variable | Default | Notes |
|----------|---------|-------|
| `DATABASE_URL` | `mssql+pyodbc://sa:GymAdmin@123!@localhost:1433/gym_db?driver=ODBC+Driver+18+for+SQL+Server` | SQL Server connection string |
| `COSMOS_ENDPOINT` | `https://localhost:8081/` | Cosmos DB endpoint (local emulator) |
| `COSMOS_KEY` | Emulator well-known key | Do not change for emulator |
| `COSMOS_DATABASE` | `gym_audit` | Cosmos DB database name |
| `CORS_ORIGINS` | `["http://localhost:3000"]` | React frontend URL |
| `SECRET_KEY` | `dev-secret-key-...` | **Change in production!** |
| `ALGORITHM` | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Access token lifetime |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token lifetime |
| `API_VERSION` | `v1` | Current API version |

---

## Troubleshooting

### SQL Server Container Won't Start

```bash
docker compose logs sqlserver
```

If still initializing: wait 60 seconds and retry. First startup can take a minute.

### `pyodbc` Installation Fails (macOS)

```bash
brew install unixodbc
pip install --no-cache-dir pyodbc
```

If still failing, install the ODBC driver first:
```bash
brew tap microsoft/mssql-release
brew install msodbcsql18
```

### Cosmos Emulator Connection Issues

The Cosmos Emulator has known stability issues on Apple Silicon Macs. **Fallback**:
1. Create a free-tier Azure Cosmos DB account in the Azure Portal
2. Update `.env`:
   ```
   COSMOS_ENDPOINT=https://<account-name>.documents.azure.com:443/
   COSMOS_KEY=<primary-key-from-azure-portal>
   ```
3. Restart the app — app code doesn't change, only the connection string

### Alembic Migration Fails

Ensure:
1. Docker containers are running and healthy: `docker compose ps`
2. SQL Server has fully initialized: wait 60 seconds after `up`
3. All models are imported in `alembic/env.py` so autogenerate sees them

---

## Development Workflow

### Make a Code Change

```bash
# Edit app/models/member.py (new Member model)

# Generate migration
alembic revision --autogenerate -m "Add member table"

# Review the migration file
cat alembic/versions/2026_07_25_<seq>_add_member_table.py

# Apply it
alembic upgrade head

# Restart the server (auto-reload will pick up changes)
```

### Run Tests (Future)

```bash
pytest tests/
```

### Format Code

```bash
black app/
isort app/
```

---

## Production Deployment

### Prerequisites

- Azure SQL Database instance
- Azure Cosmos DB account
- Environment variables set via Azure Key Vault or CI/CD secrets

### Connection Strings

**Azure SQL**:
```
mssql+pyodbc://username:password@server.database.windows.net:1433/gym_db?driver=ODBC+Driver+18+for+SQL+Server&Connection+Timeout=30
```

**Azure Cosmos DB**:
```
COSMOS_ENDPOINT=https://<account-name>.documents.azure.com:443/
COSMOS_KEY=<primary-key>
```

### Deployment (Azure App Service Example)

```bash
# Build & push Docker image
docker build -t gym-api:1.0.0 .
docker tag gym-api:1.0.0 <registry>.azurecr.io/gym-api:1.0.0
docker push <registry>.azurecr.io/gym-api:1.0.0

# Deploy to App Service (via Azure CLI or Portal)
az webapp create --resource-group <group> \
  --name <app-name> \
  --plan <plan-name> \
  --deployment-container-image-name <registry>.azurecr.io/gym-api:1.0.0
```

### Security Checklist

- [ ] Change `SECRET_KEY` to a long random string
- [ ] Set `CORS_ORIGINS` to your frontend domain only
- [ ] Use Azure Key Vault for database credentials
- [ ] Enable HTTPS (`secure=True` in JWT cookies)
- [ ] Set `pool_recycle` for connection pooling
- [ ] Enable audit logging for all sensitive operations
- [ ] Monitor Cosmos DB costs (can be high in production)
- [ ] Use database-level firewall rules (Azure SQL)
- [ ] Enable encryption at rest and in transit

---

## Phase 1 Roadmap

✅ **Infrastructure (Done)**
- Docker Compose with SQL Server + Cosmos Emulator
- Alembic migrations with date-based naming
- Multi-tenant schema
- JWT authentication
- Audit logging to Cosmos DB
- API versioning (/api/v1/)

⏳ **Member Management (Next)**
- Member CRUD (Create, Read, Update, Deactivate)
- Member profiles (name, contact, DOB, emergency contact, etc.)
- Member documents (waiver, ID proof)
- Member search & filtering
- Bulk import (CSV/Excel)
- Member export (CSV/PDF)

⏳ **Membership & Billing**
- Membership plans (monthly, quarterly, annual, custom)
- Purchase membership (assign plan to member)
- Renewal reminders (email, SMS, WhatsApp)
- Plan freezes & extensions
- Simple invoice generation
- Payment recording (cash, UPI, card)

⏳ **Attendance**
- QR code generation for members
- Check-in via QR (web + mobile)
- Attendance history
- Daily attendance reports

⏳ **Reports & Analytics**
- Expiring memberships
- Revenue by month
- Member retention
- Trainer performance
- Payment status dashboard

---

## Support & Contribution

For issues, questions, or contributions:
- Report bugs: [GitHub Issues](https://github.com/yourusername/gym)
- Discussions: [GitHub Discussions](https://github.com/yourusername/gym/discussions)
- Documentation: Refer to `CLAUDE.md` for project decisions

---

**Last Updated**: 2026-07-25
**API Version**: v1
**Status**: Production-Ready Infrastructure (Member Modules Coming Soon)
