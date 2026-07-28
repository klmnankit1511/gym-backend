from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
def get_dashboard_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get dashboard summary with key metrics for the current tenant.
    Returns static zeros for now — real aggregation added when Member/Attendance/Payment models exist.
    """
    return {
        "tenant_id": current_user.tenant_id,
        "total_members": 0,
        "active_memberships": 0,
        "today_attendance": 0,
        "monthly_revenue": 0.0,
    }
