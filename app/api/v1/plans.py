import calendar
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.session import get_db
from app.models.gym import Member, MemberSubscription, MembershipPlan, MemberTimelineEvent
from app.models.tenant import Branch
from app.models.user import User
from app.schemas.gym import PlanCreate, PlanUpdate, SubscriptionCreate, SubscriptionOperation
from app.services.tenant_features import require_feature


router = APIRouter(tags=["Membership plans"])
MANAGE_ROLES = ("SUPER_ADMIN", "OWNER", "MANAGER")


def plan_dict(plan: MembershipPlan) -> dict:
    return {
        "id": plan.id,
        "branch_id": plan.branch_id,
        "plan_code": plan.plan_code,
        "name": plan.name,
        "description": plan.description,
        "plan_type": plan.plan_type,
        "duration_value": plan.duration_value,
        "duration_unit": plan.duration_unit,
        "visit_limit": plan.visit_limit,
        "class_limit": plan.class_limit,
        "pt_session_limit": plan.pt_session_limit,
        "base_price": plan.base_price,
        "joining_fee": plan.joining_fee,
        "tax_percent": plan.tax_percent,
        "security_deposit": plan.security_deposit,
        "default_discount": plan.default_discount,
        "freeze_allowed": plan.freeze_allowed,
        "max_freeze_days": plan.max_freeze_days,
        "grace_period_days": plan.grace_period_days,
        "auto_renew_allowed": plan.auto_renew_allowed,
        "cross_branch_access": plan.cross_branch_access,
        "terms_and_conditions": plan.terms_and_conditions,
        "rules": plan.rules_json or {},
        "status": plan.status,
        "created_at": plan.created_at,
        "updated_at": plan.updated_at,
    }


def add_months(value: date, months: int) -> date:
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def calculate_end_date(start: date, plan: MembershipPlan) -> date:
    amount = plan.duration_value or 1
    unit = (plan.duration_unit or "MONTH").upper()
    if unit == "DAY":
        return start + timedelta(days=amount)
    if unit == "WEEK":
        return start + timedelta(weeks=amount)
    if unit == "YEAR":
        return add_months(start, amount * 12)
    return add_months(start, amount)


@router.get("/plans")
def list_plans(
    branch_id: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(require_feature("membership_plans")),
    db: Session = Depends(get_db),
):
    query = db.query(MembershipPlan).filter(MembershipPlan.tenant_id == current_user.tenant_id)
    if branch_id:
        query = query.filter(
            (MembershipPlan.branch_id == branch_id) | (MembershipPlan.branch_id.is_(None))
        )
    if status:
        query = query.filter(MembershipPlan.status == status.upper())
    return [plan_dict(plan) for plan in query.order_by(MembershipPlan.name).all()]


@router.post("/plans", status_code=201)
def create_plan(
    payload: PlanCreate,
    _feature: User = Depends(require_feature("membership_plans")),
    current_user: User = Depends(require_roles(*MANAGE_ROLES)),
    db: Session = Depends(get_db),
):
    if payload.branch_id:
        branch = db.query(Branch.id).filter(
            Branch.id == payload.branch_id, Branch.tenant_id == current_user.tenant_id
        ).first()
        if not branch:
            raise HTTPException(status_code=400, detail="Branch does not belong to this gym")
    exists = db.query(MembershipPlan.id).filter(
        MembershipPlan.tenant_id == current_user.tenant_id,
        MembershipPlan.plan_code == payload.plan_code,
    ).first()
    if exists:
        raise HTTPException(status_code=409, detail="Plan code already exists")
    values = payload.model_dump(exclude={"rules"})
    plan = MembershipPlan(**values, tenant_id=current_user.tenant_id, rules_json=payload.rules)
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan_dict(plan)


@router.get("/plans/{plan_id}")
def get_plan(
    plan_id: str,
    current_user: User = Depends(require_feature("membership_plans")),
    db: Session = Depends(get_db),
):
    plan = db.query(MembershipPlan).filter(
        MembershipPlan.id == plan_id, MembershipPlan.tenant_id == current_user.tenant_id
    ).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan_dict(plan)


@router.put("/plans/{plan_id}")
def update_plan(
    plan_id: str,
    payload: PlanUpdate,
    _feature: User = Depends(require_feature("membership_plans")),
    current_user: User = Depends(require_roles(*MANAGE_ROLES)),
    db: Session = Depends(get_db),
):
    plan = db.query(MembershipPlan).filter(
        MembershipPlan.id == plan_id, MembershipPlan.tenant_id == current_user.tenant_id
    ).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    values = payload.model_dump(exclude_unset=True, exclude={"rules"})
    for field, value in values.items():
        setattr(plan, field, value)
    if payload.rules is not None:
        plan.rules_json = payload.rules
    plan.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(plan)
    return plan_dict(plan)


@router.post("/memberships", status_code=201)
def assign_membership(
    payload: SubscriptionCreate,
    _feature: User = Depends(require_feature("membership_plans")),
    current_user: User = Depends(require_roles("SUPER_ADMIN", "OWNER", "MANAGER", "RECEPTIONIST")),
    db: Session = Depends(get_db),
):
    member = db.query(Member).filter(
        Member.id == payload.member_id, Member.tenant_id == current_user.tenant_id
    ).first()
    plan = db.query(MembershipPlan).filter(
        MembershipPlan.id == payload.membership_plan_id,
        MembershipPlan.tenant_id == current_user.tenant_id,
        MembershipPlan.status == "ACTIVE",
    ).first()
    if not member or not plan:
        raise HTTPException(status_code=404, detail="Member or active plan not found")
    if plan.branch_id and plan.branch_id != payload.branch_id and not plan.cross_branch_access:
        raise HTTPException(status_code=400, detail="This plan is not available at the selected branch")
    end_date = calculate_end_date(payload.start_date, plan)
    sale_price = payload.sale_price if payload.sale_price is not None else Decimal(plan.base_price)
    taxable = max(Decimal("0"), sale_price - payload.discount_amount)
    tax_amount = taxable * Decimal(plan.tax_percent) / Decimal("100")
    final_amount = taxable + tax_amount + Decimal(plan.joining_fee) + Decimal(plan.security_deposit)
    count = db.query(MemberSubscription).filter(
        MemberSubscription.tenant_id == current_user.tenant_id
    ).count() + 1
    subscription = MemberSubscription(
        tenant_id=current_user.tenant_id,
        branch_id=payload.branch_id,
        member_id=member.id,
        membership_plan_id=plan.id,
        subscription_number=f"SUB-{datetime.utcnow():%y%m}-{count:06d}",
        start_date=payload.start_date,
        end_date=end_date,
        original_end_date=end_date,
        sale_price=sale_price,
        discount_amount=payload.discount_amount,
        tax_amount=tax_amount,
        final_amount=final_amount,
        auto_renew=payload.auto_renew and plan.auto_renew_allowed,
        remaining_visits=plan.visit_limit,
        remaining_classes=plan.class_limit,
        remaining_pt_sessions=plan.pt_session_limit,
        status="ACTIVE",
        created_by=current_user.id,
    )
    db.add(subscription)
    db.flush()
    db.add(MemberTimelineEvent(
        tenant_id=current_user.tenant_id,
        member_id=member.id,
        actor_user_id=current_user.id,
        event_type="MEMBERSHIP_ASSIGNED",
        title=f"{plan.name} membership assigned",
        details_json={"subscription_id": subscription.id, "end_date": end_date.isoformat()},
    ))
    db.commit()
    db.refresh(subscription)
    return subscription


@router.post("/memberships/{subscription_id}/operations")
def membership_operation(
    subscription_id: str,
    payload: SubscriptionOperation,
    _feature: User = Depends(require_feature("membership_plans")),
    current_user: User = Depends(require_roles(*MANAGE_ROLES)),
    db: Session = Depends(get_db),
):
    subscription = db.query(MemberSubscription).filter(
        MemberSubscription.id == subscription_id,
        MemberSubscription.tenant_id == current_user.tenant_id,
    ).first()
    if not subscription:
        raise HTTPException(status_code=404, detail="Membership not found")
    details = {"reason": payload.reason}
    if payload.action == "CANCEL":
        subscription.status = "CANCELLED"
        subscription.cancellation_reason = payload.reason
        subscription.cancelled_at = datetime.utcnow()
    elif payload.action == "FREEZE":
        plan = db.query(MembershipPlan).filter(MembershipPlan.id == subscription.membership_plan_id).first()
        if not plan or not plan.freeze_allowed:
            raise HTTPException(status_code=400, detail="This plan does not allow freezing")
        subscription.status = "FROZEN"
    elif payload.action == "UNFREEZE":
        subscription.status = "ACTIVE"
    elif payload.action in {"EXTEND", "RENEW"}:
        if payload.action == "EXTEND":
            if not payload.days:
                raise HTTPException(status_code=400, detail="days is required")
            subscription.end_date += timedelta(days=payload.days)
        else:
            plan = db.query(MembershipPlan).filter(MembershipPlan.id == subscription.membership_plan_id).first()
            subscription.start_date = max(date.today(), subscription.end_date)
            subscription.end_date = calculate_end_date(subscription.start_date, plan)
            subscription.original_end_date = subscription.end_date
            subscription.status = "ACTIVE"
        details["end_date"] = subscription.end_date.isoformat()
    elif payload.action == "CHANGE_PLAN":
        if not payload.membership_plan_id:
            raise HTTPException(status_code=400, detail="membership_plan_id is required")
        plan = db.query(MembershipPlan).filter(
            MembershipPlan.id == payload.membership_plan_id,
            MembershipPlan.tenant_id == current_user.tenant_id,
            MembershipPlan.status == "ACTIVE",
        ).first()
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        subscription.membership_plan_id = plan.id
        subscription.end_date = calculate_end_date(date.today(), plan)
        details["plan_id"] = plan.id
    subscription.updated_at = datetime.utcnow()
    subscription.version += 1
    db.add(MemberTimelineEvent(
        tenant_id=current_user.tenant_id,
        member_id=subscription.member_id,
        actor_user_id=current_user.id,
        event_type=f"MEMBERSHIP_{payload.action}",
        title=f"Membership {payload.action.lower().replace('_', ' ')}",
        details_json=details,
    ))
    db.commit()
    db.refresh(subscription)
    return subscription
