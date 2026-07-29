import csv
import io
from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.session import get_db
from app.models.gym import (
    AttendanceRecord,
    Invoice,
    Member,
    MemberConsent,
    MemberDocument,
    MemberMeasurement,
    MemberProgressPhoto,
    MemberSubscription,
    MemberTimelineEvent,
    Payment,
)
from app.models.tenant import Branch
from app.models.user import User
from app.schemas.gym import (
    MeasurementCreate,
    ConsentCreate,
    DocumentCreate,
    MemberCreate,
    MemberOperation,
    MemberUpdate,
    ProgressPhotoCreate,
)
from app.services.tenant_features import require_feature


router = APIRouter(prefix="/members", tags=["Members"])
STAFF_ROLES = ("SUPER_ADMIN", "OWNER", "MANAGER", "RECEPTIONIST", "TRAINER", "ACCOUNTANT")
SENSITIVE_ROLES = {"SUPER_ADMIN", "OWNER", "MANAGER"}


def user_roles(user: User) -> set[str]:
    return {role.name for role in user.roles}


def ensure_branch(db: Session, tenant_id: str, branch_id: str) -> None:
    exists = db.query(Branch.id).filter(Branch.id == branch_id, Branch.tenant_id == tenant_id).first()
    if not exists:
        raise HTTPException(status_code=400, detail="Branch does not belong to this gym")


def generate_member_code(db: Session, tenant_id: str) -> str:
    sequence = db.query(Member).filter(Member.tenant_id == tenant_id).count() + 1
    return f"MEM-{datetime.utcnow():%y%m}-{sequence:05d}"


def add_timeline(
    db: Session,
    member: Member,
    user: User,
    event_type: str,
    title: str,
    details: Optional[dict] = None,
) -> None:
    db.add(
        MemberTimelineEvent(
            tenant_id=member.tenant_id,
            member_id=member.id,
            actor_user_id=user.id,
            event_type=event_type,
            title=title,
            details_json=details or {},
        )
    )


def member_dict(member: Member, viewer: User) -> dict:
    can_view_sensitive = bool(user_roles(viewer) & SENSITIVE_ROLES)
    return {
        "id": member.id,
        "home_branch_id": member.home_branch_id,
        "assigned_trainer_id": member.assigned_trainer_id,
        "member_code": member.member_code,
        "first_name": member.first_name,
        "last_name": member.last_name,
        "full_name": " ".join(filter(None, [member.first_name, member.last_name])),
        "email": member.email,
        "phone": member.phone,
        "alternate_phone": member.alternate_phone,
        "date_of_birth": member.date_of_birth,
        "gender": member.gender,
        "blood_group": member.blood_group,
        "address_line1": member.address_line1,
        "address_line2": member.address_line2,
        "city": member.city,
        "state": member.state,
        "postal_code": member.postal_code,
        "emergency_contact_name": member.emergency_contact_name,
        "emergency_contact_phone": member.emergency_contact_phone,
        "occupation": member.occupation,
        "source": member.source,
        "joining_date": member.joining_date,
        "profile_photo_url": member.profile_photo_url,
        "medical_notes": member.medical_notes if can_view_sensitive else None,
        "fitness_goal": member.fitness_goal,
        "internal_notes": member.internal_notes if can_view_sensitive else None,
        "custom_fields": member.custom_fields_json or {},
        "family_group_id": member.family_group_id,
        "corporate_account": member.corporate_account,
        "blocked_reason": member.blocked_reason if can_view_sensitive else None,
        "status": member.status,
        "created_at": member.created_at,
        "updated_at": member.updated_at,
    }


@router.get("")
def list_members(
    search: Optional[str] = None,
    branch_id: Optional[str] = None,
    trainer_id: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=25, ge=1, le=200),
    current_user: User = Depends(require_feature("members")),
    db: Session = Depends(get_db),
):
    query = db.query(Member).filter(Member.tenant_id == current_user.tenant_id)
    if search:
        pattern = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Member.member_code.ilike(pattern),
                Member.first_name.ilike(pattern),
                Member.last_name.ilike(pattern),
                Member.email.ilike(pattern),
                Member.phone.ilike(pattern),
            )
        )
    if branch_id:
        query = query.filter(Member.home_branch_id == branch_id)
    if trainer_id:
        query = query.filter(Member.assigned_trainer_id == trainer_id)
    if status:
        query = query.filter(Member.status == status.upper())
    total = query.count()
    rows = query.order_by(Member.created_at.desc()).offset(skip).limit(limit).all()
    return {"items": [member_dict(row, current_user) for row in rows], "total": total, "skip": skip, "limit": limit}


@router.post("", status_code=201)
def create_member(
    payload: MemberCreate,
    _feature: User = Depends(require_feature("members")),
    current_user: User = Depends(require_roles(*STAFF_ROLES)),
    db: Session = Depends(get_db),
):
    ensure_branch(db, current_user.tenant_id, payload.home_branch_id)
    duplicate = (
        db.query(Member)
        .filter(Member.tenant_id == current_user.tenant_id, Member.phone == payload.phone)
        .first()
    )
    if duplicate:
        raise HTTPException(status_code=409, detail="A member with this phone number already exists")
    values = payload.model_dump(exclude={"custom_fields", "member_code"})
    member = Member(
        **values,
        tenant_id=current_user.tenant_id,
        member_code=payload.member_code or generate_member_code(db, current_user.tenant_id),
        custom_fields_json=payload.custom_fields,
    )
    db.add(member)
    db.flush()
    add_timeline(db, member, current_user, "MEMBER_CREATED", "Member profile created")
    db.commit()
    db.refresh(member)
    return member_dict(member, current_user)


@router.get("/export")
def export_members(
    branch_id: Optional[str] = None,
    status: Optional[str] = None,
    _feature: User = Depends(require_feature("members")),
    current_user: User = Depends(require_roles("SUPER_ADMIN", "OWNER", "MANAGER")),
    db: Session = Depends(get_db),
):
    query = db.query(Member).filter(Member.tenant_id == current_user.tenant_id)
    if branch_id:
        query = query.filter(Member.home_branch_id == branch_id)
    if status:
        query = query.filter(Member.status == status.upper())
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["member_code", "first_name", "last_name", "phone", "email", "joining_date", "status", "branch_id"])
    for member in query.order_by(Member.member_code).all():
        writer.writerow([
            member.member_code, member.first_name, member.last_name or "", member.phone,
            member.email or "", member.joining_date.isoformat(), member.status, member.home_branch_id,
        ])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=members.csv"},
    )


@router.post("/import")
async def import_members(
    branch_id: str,
    file: UploadFile = File(...),
    _feature: User = Depends(require_feature("members")),
    current_user: User = Depends(require_roles("SUPER_ADMIN", "OWNER", "MANAGER")),
    db: Session = Depends(get_db),
):
    ensure_branch(db, current_user.tenant_id, branch_id)
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Upload a CSV file")
    raw = (await file.read()).decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(raw))
    required = {"first_name", "phone"}
    if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
        raise HTTPException(status_code=400, detail="CSV must include first_name and phone columns")
    created = 0
    errors = []
    for line_number, row in enumerate(reader, start=2):
        try:
            phone = (row.get("phone") or "").strip()
            first_name = (row.get("first_name") or "").strip()
            if not phone or not first_name:
                raise ValueError("first_name and phone are required")
            exists = db.query(Member.id).filter(Member.tenant_id == current_user.tenant_id, Member.phone == phone).first()
            if exists:
                raise ValueError("phone already exists")
            member = Member(
                tenant_id=current_user.tenant_id,
                home_branch_id=branch_id,
                member_code=(row.get("member_code") or "").strip() or generate_member_code(db, current_user.tenant_id),
                first_name=first_name,
                last_name=(row.get("last_name") or "").strip() or None,
                phone=phone,
                email=(row.get("email") or "").strip().lower() or None,
                joining_date=date.fromisoformat(row["joining_date"]) if row.get("joining_date") else date.today(),
                status=(row.get("status") or "ACTIVE").upper(),
                source="CSV_IMPORT",
            )
            db.add(member)
            db.flush()
            add_timeline(db, member, current_user, "MEMBER_IMPORTED", "Member imported from CSV")
            created += 1
        except Exception as exc:
            db.rollback()
            errors.append({"line": line_number, "error": str(exc)})
    db.commit()
    return {"created": created, "errors": errors}


@router.get("/{member_id}")
def get_member(
    member_id: str,
    current_user: User = Depends(require_feature("members")),
    db: Session = Depends(get_db),
):
    member = (
        db.query(Member)
        .filter(Member.id == member_id, Member.tenant_id == current_user.tenant_id)
        .first()
    )
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    data = member_dict(member, current_user)
    data["memberships"] = db.query(MemberSubscription).filter(
        MemberSubscription.member_id == member.id,
        MemberSubscription.tenant_id == current_user.tenant_id,
    ).order_by(MemberSubscription.created_at.desc()).all()
    data["payments"] = db.query(Payment).filter(
        Payment.member_id == member.id,
        Payment.tenant_id == current_user.tenant_id,
    ).order_by(Payment.payment_date.desc()).limit(100).all()
    data["attendance"] = db.query(AttendanceRecord).filter(
        AttendanceRecord.member_id == member.id,
        AttendanceRecord.tenant_id == current_user.tenant_id,
    ).order_by(AttendanceRecord.check_in_at.desc()).limit(100).all()
    data["invoices"] = db.query(Invoice).filter(
        Invoice.member_id == member.id,
        Invoice.tenant_id == current_user.tenant_id,
    ).order_by(Invoice.invoice_date.desc()).limit(100).all()
    data["measurements"] = [
        {
            "id": item.id,
            "recorded_at": item.created_at,
            "weight_kg": item.weight_kg,
            "height_cm": item.height_cm,
            "body_fat_percent": item.body_fat_percent,
            "measurements": {
                "bmi": item.bmi,
                "muscle_mass_kg": item.muscle_mass_kg,
                "chest_cm": item.chest_cm,
                "waist_cm": item.waist_cm,
                "hips_cm": item.hips_cm,
                "arm_cm": item.arm_cm,
                "thigh_cm": item.thigh_cm,
            },
            "notes": item.notes,
        }
        for item in db.query(MemberMeasurement).filter(
            MemberMeasurement.member_id == member.id,
            MemberMeasurement.tenant_id == current_user.tenant_id,
        ).order_by(MemberMeasurement.measurement_date.desc()).all()
    ]
    data["documents"] = [
        {
            "id": item.id,
            "document_type": item.document_type,
            "file_name": item.file_name,
            "file_url": item.file_url,
            "created_at": item.created_at,
        }
        for item in db.query(MemberDocument).filter(
            MemberDocument.member_id == member.id,
            MemberDocument.tenant_id == current_user.tenant_id,
        ).order_by(MemberDocument.created_at.desc()).all()
    ]
    data["consents"] = [
        {
            "id": item.id,
            "consent_type": item.consent_type,
            "document_version": item.document_version,
            "accepted": item.accepted,
            "accepted_at": item.accepted_at,
        }
        for item in db.query(MemberConsent).filter(
            MemberConsent.member_id == member.id,
            MemberConsent.tenant_id == current_user.tenant_id,
        ).order_by(MemberConsent.created_at.desc()).all()
    ]
    data["progress_photos"] = [
        {
            "id": item.id,
            "photo_date": item.photo_date,
            "photo_type": item.photo_type,
            "file_url": item.file_url,
            "notes": item.notes,
        }
        for item in db.query(MemberProgressPhoto).filter(
            MemberProgressPhoto.member_id == member.id,
            MemberProgressPhoto.tenant_id == current_user.tenant_id,
        ).order_by(MemberProgressPhoto.photo_date.desc()).all()
    ]
    data["timeline"] = [
        {
            "id": item.id,
            "event_type": item.event_type,
            "title": item.title,
            "details": item.details_json or {},
            "created_at": item.created_at,
        }
        for item in db.query(MemberTimelineEvent).filter(
            MemberTimelineEvent.member_id == member.id,
            MemberTimelineEvent.tenant_id == current_user.tenant_id,
        ).order_by(MemberTimelineEvent.created_at.desc()).limit(100).all()
    ]
    return data


@router.put("/{member_id}")
def update_member(
    member_id: str,
    payload: MemberUpdate,
    _feature: User = Depends(require_feature("members")),
    current_user: User = Depends(require_roles(*STAFF_ROLES)),
    db: Session = Depends(get_db),
):
    member = db.query(Member).filter(Member.id == member_id, Member.tenant_id == current_user.tenant_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    values = payload.model_dump(exclude_unset=True, exclude={"custom_fields"})
    if "home_branch_id" in values:
        ensure_branch(db, current_user.tenant_id, values["home_branch_id"])
    if not (user_roles(current_user) & SENSITIVE_ROLES):
        for field in ("medical_notes", "internal_notes", "blocked_reason"):
            values.pop(field, None)
    for field, value in values.items():
        setattr(member, field, value)
    if payload.custom_fields is not None:
        member.custom_fields_json = payload.custom_fields
    member.updated_at = datetime.utcnow()
    add_timeline(db, member, current_user, "MEMBER_UPDATED", "Member profile updated", {"fields": sorted(values)})
    db.commit()
    db.refresh(member)
    return member_dict(member, current_user)


@router.post("/{member_id}/operations")
def member_operation(
    member_id: str,
    payload: MemberOperation,
    _feature: User = Depends(require_feature("members")),
    current_user: User = Depends(require_roles("SUPER_ADMIN", "OWNER", "MANAGER")),
    db: Session = Depends(get_db),
):
    member = db.query(Member).filter(Member.id == member_id, Member.tenant_id == current_user.tenant_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    if payload.action == "TRANSFER":
        if not payload.branch_id:
            raise HTTPException(status_code=400, detail="branch_id is required for transfer")
        ensure_branch(db, current_user.tenant_id, payload.branch_id)
        previous = member.home_branch_id
        member.home_branch_id = payload.branch_id
        details = {"from_branch_id": previous, "to_branch_id": payload.branch_id, "reason": payload.reason}
    else:
        statuses = {
            "FREEZE": "FROZEN", "UNFREEZE": "ACTIVE", "BLOCK": "BLOCKED",
            "UNBLOCK": "ACTIVE", "DEACTIVATE": "INACTIVE",
        }
        member.status = statuses[payload.action]
        if payload.action == "BLOCK":
            member.blocked_reason = payload.reason
        details = {"status": member.status, "reason": payload.reason}
    add_timeline(db, member, current_user, payload.action, payload.action.replace("_", " ").title(), details)
    db.commit()
    return member_dict(member, current_user)


@router.post("/{member_id}/measurements", status_code=201)
def add_measurement(
    member_id: str,
    payload: MeasurementCreate,
    _feature: User = Depends(require_feature("member_progress")),
    current_user: User = Depends(require_roles("SUPER_ADMIN", "OWNER", "MANAGER", "TRAINER")),
    db: Session = Depends(get_db),
):
    member = db.query(Member).filter(Member.id == member_id, Member.tenant_id == current_user.tenant_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    extra = payload.measurements
    measurement = MemberMeasurement(
        tenant_id=current_user.tenant_id,
        member_id=member.id,
        measured_by=current_user.id,
        weight_kg=payload.weight_kg,
        height_cm=payload.height_cm,
        body_fat_percent=payload.body_fat_percent,
        bmi=extra.get("bmi"),
        muscle_mass_kg=extra.get("muscle_mass_kg"),
        chest_cm=extra.get("chest_cm"),
        waist_cm=extra.get("waist_cm"),
        hips_cm=extra.get("hips_cm"),
        arm_cm=extra.get("arm_cm"),
        thigh_cm=extra.get("thigh_cm"),
        notes=payload.notes,
    )
    db.add(measurement)
    add_timeline(db, member, current_user, "MEASUREMENT_RECORDED", "Body measurements recorded")
    db.commit()
    db.refresh(measurement)
    return {
        "id": measurement.id,
        "recorded_at": measurement.created_at,
        "weight_kg": measurement.weight_kg,
        "height_cm": measurement.height_cm,
        "body_fat_percent": measurement.body_fat_percent,
        "measurements": {
            "bmi": measurement.bmi,
            "muscle_mass_kg": measurement.muscle_mass_kg,
            "chest_cm": measurement.chest_cm,
            "waist_cm": measurement.waist_cm,
            "hips_cm": measurement.hips_cm,
            "arm_cm": measurement.arm_cm,
            "thigh_cm": measurement.thigh_cm,
        },
        "notes": measurement.notes,
    }


@router.post("/{member_id}/documents", status_code=201)
def add_document(
    member_id: str,
    payload: DocumentCreate,
    _feature: User = Depends(require_feature("member_documents")),
    current_user: User = Depends(require_roles(*STAFF_ROLES)),
    db: Session = Depends(get_db),
):
    member = db.query(Member).filter(Member.id == member_id, Member.tenant_id == current_user.tenant_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    document = MemberDocument(
        tenant_id=current_user.tenant_id,
        member_id=member.id,
        uploaded_by=current_user.id,
        **payload.model_dump(),
    )
    db.add(document)
    add_timeline(db, member, current_user, "DOCUMENT_ADDED", f"{payload.document_type} document added")
    db.commit()
    db.refresh(document)
    return document


@router.post("/{member_id}/consents", status_code=201)
def record_consent(
    member_id: str,
    payload: ConsentCreate,
    _feature: User = Depends(require_feature("member_documents")),
    current_user: User = Depends(require_roles(*STAFF_ROLES)),
    db: Session = Depends(get_db),
):
    member = db.query(Member).filter(Member.id == member_id, Member.tenant_id == current_user.tenant_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    consent = MemberConsent(
        tenant_id=current_user.tenant_id,
        member_id=member.id,
        accepted_at=datetime.utcnow() if payload.accepted else None,
        **payload.model_dump(),
    )
    db.add(consent)
    add_timeline(db, member, current_user, "CONSENT_RECORDED", f"{payload.consent_type} consent recorded", {"accepted": payload.accepted})
    db.commit()
    db.refresh(consent)
    return consent


@router.post("/{member_id}/progress-photos", status_code=201)
def add_progress_photo(
    member_id: str,
    payload: ProgressPhotoCreate,
    _feature: User = Depends(require_feature("member_progress")),
    current_user: User = Depends(require_roles("SUPER_ADMIN", "OWNER", "MANAGER", "TRAINER")),
    db: Session = Depends(get_db),
):
    member = db.query(Member).filter(Member.id == member_id, Member.tenant_id == current_user.tenant_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    photo = MemberProgressPhoto(
        tenant_id=current_user.tenant_id,
        member_id=member.id,
        **payload.model_dump(),
    )
    db.add(photo)
    add_timeline(db, member, current_user, "PROGRESS_PHOTO_ADDED", "Progress photograph added")
    db.commit()
    db.refresh(photo)
    return photo


@router.get("/{member_id}/digital-card")
def digital_membership_card(
    member_id: str,
    current_user: User = Depends(require_feature("members")),
    db: Session = Depends(get_db),
):
    member = db.query(Member).filter(Member.id == member_id, Member.tenant_id == current_user.tenant_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    subscription = db.query(MemberSubscription).filter(
        MemberSubscription.member_id == member.id,
        MemberSubscription.tenant_id == current_user.tenant_id,
        MemberSubscription.status == "ACTIVE",
    ).order_by(MemberSubscription.end_date.desc()).first()
    return {
        "member_id": member.id,
        "member_code": member.member_code,
        "full_name": " ".join(filter(None, [member.first_name, member.last_name])),
        "profile_photo_url": member.profile_photo_url,
        "status": member.status,
        "branch_id": member.home_branch_id,
        "valid_until": subscription.end_date if subscription else None,
        "card_payload": f"GYM:{current_user.tenant_id}:{member.id}:{member.member_code}",
    }
