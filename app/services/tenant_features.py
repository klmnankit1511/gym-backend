from typing import Any, Dict

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.gym import TenantFeature
from app.models.user import User


FEATURE_CATALOG: Dict[str, Dict[str, Any]] = {
    "dashboard": {"label": "Business dashboard", "category": "Core", "default": True},
    "members": {"label": "Member management", "category": "Core", "default": True},
    "member_medical_notes": {"label": "Medical and injury notes", "category": "Members", "default": True},
    "member_documents": {"label": "Documents and waivers", "category": "Members", "default": True},
    "member_progress": {"label": "Measurements and progress photos", "category": "Members", "default": True},
    "family_memberships": {"label": "Family memberships", "category": "Members", "default": True},
    "corporate_memberships": {"label": "Corporate memberships", "category": "Members", "default": True},
    "membership_plans": {"label": "Membership plans", "category": "Core", "default": True},
    "attendance": {"label": "Attendance", "category": "Operations", "default": True},
    "payments": {"label": "Billing and payments", "category": "Operations", "default": True},
    "leads": {"label": "Leads and CRM", "category": "Growth", "default": True},
    "trainers": {"label": "Trainer management", "category": "Operations", "default": True},
    "classes": {"label": "Classes and scheduling", "category": "Operations", "default": True},
    "workouts": {"label": "Workout plans", "category": "Members", "default": True},
    "communications": {"label": "Member communication", "category": "Growth", "default": True},
    "online_signup": {"label": "Online signup", "category": "Growth", "default": True},
}


def feature_map(db: Session, tenant_id: str) -> Dict[str, Dict[str, Any]]:
    overrides = {
        row.feature_key: row
        for row in db.query(TenantFeature).filter(TenantFeature.tenant_id == tenant_id).all()
    }
    result: Dict[str, Dict[str, Any]] = {}
    for key, metadata in FEATURE_CATALOG.items():
        override = overrides.get(key)
        result[key] = {
            "feature_key": key,
            "label": metadata["label"],
            "category": metadata["category"],
            "enabled": override.enabled if override else metadata["default"],
            "config": (override.config_json or {}) if override else {},
        }
    return result


def feature_enabled(db: Session, tenant_id: str, feature_key: str) -> bool:
    row = (
        db.query(TenantFeature)
        .filter(TenantFeature.tenant_id == tenant_id, TenantFeature.feature_key == feature_key)
        .first()
    )
    if row is not None:
        return bool(row.enabled)
    return bool(FEATURE_CATALOG.get(feature_key, {}).get("default", False))


def require_feature(feature_key: str):
    async def dependency(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> User:
        if not feature_enabled(db, current_user.tenant_id, feature_key):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"The {feature_key} module is disabled for this gym",
            )
        return current_user

    return dependency
