from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.db.session import get_db
from app.models.gym import TenantFeature, Trainer
from app.models.tenant import Branch
from app.models.user import User
from app.schemas.gym import BranchOut, FeatureBulkUpdate
from app.services.tenant_features import FEATURE_CATALOG, feature_map


router = APIRouter(prefix="/settings", tags=["Tenant settings"])


@router.get("/features")
def get_features(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return {"features": list(feature_map(db, current_user.tenant_id).values())}


@router.put("/features")
def update_features(
    payload: FeatureBulkUpdate,
    current_user: User = Depends(require_roles("SUPER_ADMIN", "OWNER")),
    db: Session = Depends(get_db),
):
    unknown = set(payload.features) - set(FEATURE_CATALOG)
    if unknown:
        raise HTTPException(status_code=400, detail=f"Unknown features: {', '.join(sorted(unknown))}")

    for key, setting in payload.features.items():
        row = (
            db.query(TenantFeature)
            .filter(
                TenantFeature.tenant_id == current_user.tenant_id,
                TenantFeature.feature_key == key,
            )
            .first()
        )
        if row is None:
            row = TenantFeature(
                tenant_id=current_user.tenant_id,
                feature_key=key,
                created_at=datetime.utcnow(),
            )
            db.add(row)
        row.enabled = setting.enabled
        row.config_json = setting.config
        row.updated_by = current_user.id
        row.updated_at = datetime.utcnow()
    db.commit()
    return {"features": list(feature_map(db, current_user.tenant_id).values())}


@router.get("/branches", response_model=list[BranchOut])
def list_branches(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(Branch)
        .filter(Branch.tenant_id == current_user.tenant_id)
        .order_by(Branch.name)
        .all()
    )


@router.get("/trainers")
def list_trainers(
    branch_id: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Trainer).filter(
        Trainer.tenant_id == current_user.tenant_id,
        Trainer.status == "ACTIVE",
    )
    if branch_id:
        query = query.filter(Trainer.branch_id == branch_id)
    return [
        {
            "id": trainer.id,
            "branch_id": trainer.branch_id,
            "trainer_code": trainer.trainer_code,
            "specialization": trainer.specialization,
            "status": trainer.status,
        }
        for trainer in query.order_by(Trainer.trainer_code).all()
    ]
