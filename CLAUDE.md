# Gym Manager API Backend

FastAPI backend for the Gym Member Management System.

## Project Structure

```
app/
├── main.py              # FastAPI app, CORS, routers, health check
├── core/
│   └── config.py        # Pydantic Settings (DATABASE_URL, CORS_ORIGINS)
├── db/
│   └── session.py       # SQLAlchemy engine, SessionLocal, Base, get_db() dependency
└── api/
    └── dashboard.py     # Dashboard endpoints (GET /api/dashboard/summary)
```

## Getting Started

1. **Create virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Setup environment:**
   ```bash
   cp .env.example .env
   ```

4. **Run development server:**
   ```bash
   uvicorn app.main:app --reload
   ```

Server runs on `http://localhost:8000`

## Endpoints

- `GET /health` - Health check → `{"status": "ok"}`
- `GET /api/dashboard/summary` - Dashboard summary → `{total_members, active_memberships, today_attendance, monthly_revenue}`
- `GET /docs` - Swagger UI
- `GET /redoc` - ReDoc documentation

## Database

**SQLite** (via SQLAlchemy) - configured in `.env` as `DATABASE_URL`

For production, change to PostgreSQL:
```
DATABASE_URL=postgresql://user:password@localhost/gym_db
```

No schema migration tool configured yet. Will add Alembic in Phase 2.

## API Design

### Conventions

- All endpoints return JSON
- Error responses: `{"detail": "error message"}`
- Pagination: Add `?skip=0&limit=10` params to list endpoints
- Timestamps: ISO 8601 format

### Future Endpoints (Phase 1)

**Members:**
- `GET /api/members` - List all members
- `POST /api/members` - Create member
- `GET /api/members/{id}` - Get member details
- `PUT /api/members/{id}` - Update member
- `DELETE /api/members/{id}` - Soft delete member

**Membership Plans:**
- `GET /api/plans` - List plans
- `POST /api/plans` - Create plan
- `PUT /api/plans/{id}` - Update plan

**Memberships:**
- `GET /api/memberships` - List active memberships
- `POST /api/memberships` - Purchase membership for member
- `PUT /api/memberships/{id}` - Renew/freeze membership

**Payments:**
- `GET /api/payments` - List payments
- `POST /api/payments` - Record payment

**Attendance:**
- `POST /api/attendance` - Check-in member
- `GET /api/attendance/{member_id}` - Member attendance history

## CORS

Currently allows `http://localhost:3000` (React dev server).

For production, update `.env`:
```
CORS_ORIGINS=["https://example.com"]
```

## Notes

- No authentication yet (Phase 2)
- Database models not created yet (waiting for Phase 1 feature specs)
- All business logic goes in `/api` routers; `/db` handles only DB access
- Use Pydantic models for request/response validation
