from datetime import date, datetime, time, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.gym import (
    AttendanceRecord,
    Invoice,
    Lead,
    Member,
    MemberSubscription,
    MembershipPlan,
    Payment,
)
from app.models.user import User
from app.services.tenant_features import require_feature


router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def percent_change(current: float, previous: float) -> Optional[float]:
    if previous == 0:
        return None if current == 0 else 100.0
    return round(((current - previous) / previous) * 100, 1)


def metric(current: float, previous: float) -> dict:
    return {
        "value": round(float(current), 2),
        "previous_value": round(float(previous), 2),
        "change_percent": percent_change(float(current), float(previous)),
    }


@router.get("/summary")
def get_dashboard_summary(
    branch_id: Optional[str] = None,
    date_from: Optional[date] = Query(default=None),
    date_to: Optional[date] = Query(default=None),
    trainer_id: Optional[str] = None,
    membership_type: Optional[str] = None,
    payment_status: Optional[str] = None,
    current_user: User = Depends(require_feature("dashboard")),
    db: Session = Depends(get_db),
):
    today = date.today()
    start = date_from or today.replace(day=1)
    end = date_to or today
    if start > end:
        start, end = end, start
    start_dt = datetime.combine(start, time.min)
    end_dt = datetime.combine(end, time.max)
    days = (end - start).days + 1
    previous_end = start - timedelta(days=1)
    previous_start = previous_end - timedelta(days=days - 1)
    previous_start_dt = datetime.combine(previous_start, time.min)
    previous_end_dt = datetime.combine(previous_end, time.max)
    tenant_id = current_user.tenant_id

    members = db.query(Member).filter(Member.tenant_id == tenant_id)
    previous_members = db.query(Member).filter(Member.tenant_id == tenant_id)
    if branch_id:
        members = members.filter(Member.home_branch_id == branch_id)
        previous_members = previous_members.filter(Member.home_branch_id == branch_id)
    if trainer_id:
        members = members.filter(Member.assigned_trainer_id == trainer_id)
        previous_members = previous_members.filter(Member.assigned_trainer_id == trainer_id)
    active_members = members.filter(Member.status == "ACTIVE").count()
    previous_active = previous_members.filter(
        Member.status == "ACTIVE", Member.created_at <= previous_end_dt
    ).count()
    new_members = members.filter(Member.created_at.between(start_dt, end_dt)).count()
    previous_new_members = previous_members.filter(
        Member.created_at.between(previous_start_dt, previous_end_dt)
    ).count()

    subscriptions = db.query(MemberSubscription).filter(MemberSubscription.tenant_id == tenant_id)
    if branch_id:
        subscriptions = subscriptions.filter(MemberSubscription.branch_id == branch_id)
    if trainer_id:
        subscriptions = subscriptions.join(Member, Member.id == MemberSubscription.member_id).filter(
            Member.assigned_trainer_id == trainer_id
        )
    if membership_type:
        subscriptions = subscriptions.join(
            MembershipPlan, MembershipPlan.id == MemberSubscription.membership_plan_id
        ).filter(MembershipPlan.plan_type == membership_type)
    active_subscriptions = subscriptions.filter(MemberSubscription.status == "ACTIVE")
    expiring_7 = active_subscriptions.filter(
        MemberSubscription.end_date.between(today, today + timedelta(days=7))
    ).count()
    expiring_15 = active_subscriptions.filter(
        MemberSubscription.end_date.between(today, today + timedelta(days=15))
    ).count()
    expiring_30 = active_subscriptions.filter(
        MemberSubscription.end_date.between(today, today + timedelta(days=30))
    ).count()

    attendance = db.query(AttendanceRecord).filter(AttendanceRecord.tenant_id == tenant_id)
    if branch_id:
        attendance = attendance.filter(AttendanceRecord.branch_id == branch_id)
    if trainer_id:
        attendance = attendance.join(Member, Member.id == AttendanceRecord.member_id).filter(
            Member.assigned_trainer_id == trainer_id
        )
    today_start = datetime.combine(today, time.min)
    today_end = datetime.combine(today, time.max)
    today_attendance = attendance.filter(AttendanceRecord.check_in_at.between(today_start, today_end)).count()
    previous_day_attendance = attendance.filter(
        AttendanceRecord.check_in_at.between(
            datetime.combine(today - timedelta(days=1), time.min),
            datetime.combine(today - timedelta(days=1), time.max),
        )
    ).count()

    payments = db.query(Payment).filter(Payment.tenant_id == tenant_id)
    if branch_id:
        payments = payments.filter(Payment.branch_id == branch_id)
    if payment_status:
        payments = payments.filter(Payment.status == payment_status.upper())
    revenue_statuses = ["SUCCESS", "COMPLETED", "PAID", "CAPTURED"]
    revenue = payments.filter(
        Payment.payment_date.between(start_dt, end_dt),
        Payment.status.in_(revenue_statuses),
    ).with_entities(func.coalesce(func.sum(Payment.amount), 0)).scalar() or 0
    previous_revenue = payments.filter(
        Payment.payment_date.between(previous_start_dt, previous_end_dt),
        Payment.status.in_(revenue_statuses),
    ).with_entities(func.coalesce(func.sum(Payment.amount), 0)).scalar() or 0

    invoices = db.query(Invoice).filter(Invoice.tenant_id == tenant_id)
    if branch_id:
        invoices = invoices.filter(Invoice.branch_id == branch_id)
    pending_payments = invoices.filter(
        Invoice.status.in_(["ISSUED", "PARTIALLY_PAID", "OVERDUE"])
    ).with_entities(func.coalesce(func.sum(Invoice.balance_amount), 0)).scalar() or 0
    overdue_count = invoices.filter(
        (Invoice.status == "OVERDUE")
        | ((Invoice.due_date < today) & (Invoice.balance_amount > 0))
    ).count()
    failed_count = payments.filter(Payment.status.in_(["FAILED", "DECLINED"])).count()

    leads = db.query(Lead).filter(Lead.tenant_id == tenant_id)
    if branch_id:
        leads = leads.filter(Lead.branch_id == branch_id)
    new_leads = leads.filter(Lead.created_at.between(start_dt, end_dt)).count()
    previous_leads = leads.filter(Lead.created_at.between(previous_start_dt, previous_end_dt)).count()
    converted = leads.filter(Lead.created_at.between(start_dt, end_dt), Lead.stage == "CONVERTED").count()
    conversion = round((converted / new_leads * 100), 1) if new_leads else 0

    plan_popularity = (
        subscriptions.join(MembershipPlan, MembershipPlan.id == MemberSubscription.membership_plan_id)
        .filter(MemberSubscription.created_at.between(start_dt, end_dt))
        .with_entities(MembershipPlan.name, func.count(MemberSubscription.id).label("count"))
        .group_by(MembershipPlan.name)
        .order_by(func.count(MemberSubscription.id).desc())
        .first()
    )
    expired_or_cancelled = subscriptions.filter(
        MemberSubscription.status.in_(["EXPIRED", "CANCELLED"])
    ).count()
    current_active_subscriptions = active_subscriptions.count()
    membership_base = current_active_subscriptions + expired_or_cancelled
    retention = round(current_active_subscriptions / membership_base * 100, 1) if membership_base else 0
    churn = round(expired_or_cancelled / membership_base * 100, 1) if membership_base else 0
    assigned_active = members.filter(
        Member.status == "ACTIVE", Member.assigned_trainer_id.isnot(None)
    ).count()
    utilisation = round(assigned_active / active_members * 100, 1) if active_members else 0

    result = {
        "active_members": metric(active_members, previous_active),
        "expiring_7_days": expiring_7,
        "expiring_15_days": expiring_15,
        "expiring_30_days": expiring_30,
        "today_attendance": metric(today_attendance, previous_day_attendance),
        "new_members": metric(new_members, previous_new_members),
        "monthly_revenue": metric(revenue, previous_revenue),
        "pending_payments": float(pending_payments),
        "failed_or_overdue_payments": failed_count + overdue_count,
        "new_leads": metric(new_leads, previous_leads),
        "lead_conversion_rate": conversion,
        "trainer_utilisation": utilisation,
        "popular_plan": plan_popularity[0] if plan_popularity else None,
        "retention_rate": retention,
        "churn_rate": churn,
        "filters_applied": {
            "branch_id": branch_id,
            "date_from": start,
            "date_to": end,
            "trainer_id": trainer_id,
            "membership_type": membership_type,
            "payment_status": payment_status,
        },
        # Backward-compatible keys for older clients.
        "total_members": active_members,
        "active_memberships": current_active_subscriptions,
        "today_attendance_count": today_attendance,
        "monthly_revenue_value": float(revenue),
    }
    return result
