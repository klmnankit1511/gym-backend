from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/summary")
def get_dashboard_summary(db: Session = Depends(get_db)):
    """
    Get dashboard summary with key metrics.
    Returns static zeros for now — real aggregation added once Member/Membership/Attendance/Payment models exist.
    """
    return {
        "total_members": 0,
        "active_memberships": 0,
        "today_attendance": 0,
        "monthly_revenue": 0.0,
    }
