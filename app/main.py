from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime
import time
from sqlalchemy import text
from app.core.config import settings
from app.api.v1 import api_router
from app.db.session import SessionLocal
from app.db.cosmos import close_cosmos_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""
    yield
    # Cleanup on shutdown
    close_cosmos_client()


app = FastAPI(
    title="Gym Manager API",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include v1 API routes (includes /api/v1/auth, /api/v1/dashboard, etc.)
app.include_router(api_router)


@app.get("/health")
def health_check():
    """Basic health check endpoint"""
    return {"status": "ok", "version": "1.0.0", "timestamp": datetime.utcnow().isoformat()}


@app.get("/health/detailed")
def detailed_health_check(response: Response):
    """Detailed health check with database connectivity test"""
    health_status = {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "api": {"status": "up"},
            "database": {"status": "unknown", "latency_ms": 0},
        }
    }

    # Test database connectivity
    try:
        start = time.time()
        db = SessionLocal()
        result = db.execute(text("SELECT 1"))
        latency = (time.time() - start) * 1000
        db.close()

        health_status["components"]["database"]["status"] = "up"
        health_status["components"]["database"]["latency_ms"] = round(latency, 2)
    except Exception as e:
        health_status["components"]["database"]["status"] = "down"
        health_status["components"]["database"]["error"] = str(e)
        health_status["status"] = "degraded"
        response.status_code = 503  # Service Unavailable

    return health_status


@app.get("/health/ready")
def readiness_check(response: Response):
    """Kubernetes-style readiness probe - checks if API is ready to serve requests"""
    try:
        # Quick database connectivity check
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()

        return {
            "ready": True,
            "version": "1.0.0",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        response.status_code = 503
        return {
            "ready": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@app.get("/health/live")
def liveness_check():
    """Kubernetes-style liveness probe - checks if API process is alive"""
    return {
        "alive": True,
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }
