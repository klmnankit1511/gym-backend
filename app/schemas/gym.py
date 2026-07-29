from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


MemberStatus = Literal["ACTIVE", "INACTIVE", "FROZEN", "EXPIRED", "BLOCKED"]


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class FeatureSetting(ORMModel):
    feature_key: str
    enabled: bool = True
    config: Dict[str, Any] = Field(default_factory=dict)


class FeatureUpdate(BaseModel):
    enabled: bool
    config: Dict[str, Any] = Field(default_factory=dict)


class FeatureBulkUpdate(BaseModel):
    features: Dict[str, FeatureUpdate]


class BranchOut(ORMModel):
    id: str
    name: str
    address: Optional[str] = None


class TrainerOut(ORMModel):
    id: str
    branch_id: str
    trainer_code: str
    specialization: Optional[str] = None
    status: str


class MemberBase(BaseModel):
    home_branch_id: str
    assigned_trainer_id: Optional[str] = None
    member_code: Optional[str] = None
    first_name: str = Field(min_length=1, max_length=100)
    last_name: Optional[str] = Field(default=None, max_length=100)
    email: Optional[str] = Field(default=None, max_length=150)
    phone: str = Field(min_length=5, max_length=30)
    alternate_phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    occupation: Optional[str] = None
    source: Optional[str] = None
    joining_date: date = Field(default_factory=date.today)
    profile_photo_url: Optional[str] = None
    medical_notes: Optional[str] = None
    fitness_goal: Optional[str] = None
    internal_notes: Optional[str] = None
    custom_fields: Dict[str, Any] = Field(default_factory=dict)
    family_group_id: Optional[str] = None
    corporate_account: Optional[str] = None
    blocked_reason: Optional[str] = None
    status: MemberStatus = "ACTIVE"

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: Optional[str]) -> Optional[str]:
        return value.strip().lower() if value else None


class MemberCreate(MemberBase):
    pass


class MemberUpdate(BaseModel):
    home_branch_id: Optional[str] = None
    assigned_trainer_id: Optional[str] = None
    first_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = Field(default=None, min_length=5, max_length=30)
    alternate_phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    occupation: Optional[str] = None
    source: Optional[str] = None
    joining_date: Optional[date] = None
    profile_photo_url: Optional[str] = None
    medical_notes: Optional[str] = None
    fitness_goal: Optional[str] = None
    internal_notes: Optional[str] = None
    custom_fields: Optional[Dict[str, Any]] = None
    family_group_id: Optional[str] = None
    corporate_account: Optional[str] = None
    blocked_reason: Optional[str] = None
    status: Optional[MemberStatus] = None


class MemberOut(ORMModel):
    id: str
    home_branch_id: str
    assigned_trainer_id: Optional[str] = None
    member_code: str
    first_name: str
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: str
    alternate_phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    occupation: Optional[str] = None
    source: Optional[str] = None
    joining_date: date
    profile_photo_url: Optional[str] = None
    medical_notes: Optional[str] = None
    fitness_goal: Optional[str] = None
    internal_notes: Optional[str] = None
    custom_fields: Dict[str, Any] = Field(default_factory=dict)
    family_group_id: Optional[str] = None
    corporate_account: Optional[str] = None
    blocked_reason: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime


class MemberList(BaseModel):
    items: List[MemberOut]
    total: int
    skip: int
    limit: int


class MemberOperation(BaseModel):
    action: Literal["TRANSFER", "FREEZE", "UNFREEZE", "BLOCK", "UNBLOCK", "DEACTIVATE"]
    branch_id: Optional[str] = None
    reason: Optional[str] = Field(default=None, max_length=500)


class MeasurementCreate(BaseModel):
    weight_kg: Optional[Decimal] = None
    height_cm: Optional[Decimal] = None
    body_fat_percent: Optional[Decimal] = None
    measurements: Dict[str, Any] = Field(default_factory=dict)
    notes: Optional[str] = None


class MeasurementOut(ORMModel):
    id: str
    recorded_at: datetime
    weight_kg: Optional[Decimal] = None
    height_cm: Optional[Decimal] = None
    body_fat_percent: Optional[Decimal] = None
    measurements: Dict[str, Any] = Field(default_factory=dict)
    notes: Optional[str] = None


class DocumentCreate(BaseModel):
    document_type: str = Field(min_length=1, max_length=50)
    file_name: str = Field(min_length=1, max_length=255)
    file_url: str = Field(min_length=1, max_length=500)


class ConsentCreate(BaseModel):
    consent_type: str = Field(min_length=1, max_length=50)
    document_version: str = Field(min_length=1, max_length=50)
    accepted: bool
    ip_address: Optional[str] = None


class ProgressPhotoCreate(BaseModel):
    photo_date: date = Field(default_factory=date.today)
    photo_type: Literal["FRONT", "SIDE", "BACK", "OTHER"] = "FRONT"
    file_url: str = Field(min_length=1, max_length=500)
    notes: Optional[str] = Field(default=None, max_length=500)


class TimelineOut(ORMModel):
    id: str
    event_type: str
    title: str
    details: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class PlanBase(BaseModel):
    branch_id: Optional[str] = None
    plan_code: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=150)
    description: Optional[str] = None
    plan_type: str = Field(min_length=1, max_length=30)
    duration_value: Optional[int] = Field(default=None, ge=1)
    duration_unit: Optional[Literal["DAY", "WEEK", "MONTH", "YEAR"]] = None
    visit_limit: Optional[int] = Field(default=None, ge=0)
    class_limit: Optional[int] = Field(default=None, ge=0)
    pt_session_limit: Optional[int] = Field(default=None, ge=0)
    base_price: Decimal = Field(ge=0)
    joining_fee: Decimal = Field(default=Decimal("0"), ge=0)
    tax_percent: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    security_deposit: Decimal = Field(default=Decimal("0"), ge=0)
    default_discount: Decimal = Field(default=Decimal("0"), ge=0)
    freeze_allowed: bool = False
    max_freeze_days: Optional[int] = Field(default=None, ge=0)
    grace_period_days: int = Field(default=0, ge=0)
    auto_renew_allowed: bool = False
    cross_branch_access: bool = False
    terms_and_conditions: Optional[str] = None
    rules: Dict[str, Any] = Field(default_factory=dict)
    status: Literal["ACTIVE", "INACTIVE", "ARCHIVED"] = "ACTIVE"


class PlanCreate(PlanBase):
    pass


class PlanUpdate(BaseModel):
    branch_id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    plan_type: Optional[str] = None
    duration_value: Optional[int] = Field(default=None, ge=1)
    duration_unit: Optional[Literal["DAY", "WEEK", "MONTH", "YEAR"]] = None
    visit_limit: Optional[int] = Field(default=None, ge=0)
    class_limit: Optional[int] = Field(default=None, ge=0)
    pt_session_limit: Optional[int] = Field(default=None, ge=0)
    base_price: Optional[Decimal] = Field(default=None, ge=0)
    joining_fee: Optional[Decimal] = Field(default=None, ge=0)
    tax_percent: Optional[Decimal] = Field(default=None, ge=0, le=100)
    security_deposit: Optional[Decimal] = Field(default=None, ge=0)
    default_discount: Optional[Decimal] = Field(default=None, ge=0)
    freeze_allowed: Optional[bool] = None
    max_freeze_days: Optional[int] = Field(default=None, ge=0)
    grace_period_days: Optional[int] = Field(default=None, ge=0)
    auto_renew_allowed: Optional[bool] = None
    cross_branch_access: Optional[bool] = None
    terms_and_conditions: Optional[str] = None
    rules: Optional[Dict[str, Any]] = None
    status: Optional[Literal["ACTIVE", "INACTIVE", "ARCHIVED"]] = None


class PlanOut(ORMModel):
    id: str
    branch_id: Optional[str] = None
    plan_code: str
    name: str
    description: Optional[str] = None
    plan_type: str
    duration_value: Optional[int] = None
    duration_unit: Optional[str] = None
    visit_limit: Optional[int] = None
    class_limit: Optional[int] = None
    pt_session_limit: Optional[int] = None
    base_price: Decimal
    joining_fee: Decimal
    tax_percent: Decimal
    security_deposit: Decimal
    default_discount: Decimal
    freeze_allowed: bool
    max_freeze_days: Optional[int] = None
    grace_period_days: int
    auto_renew_allowed: bool
    cross_branch_access: bool
    terms_and_conditions: Optional[str] = None
    rules: Dict[str, Any] = Field(default_factory=dict)
    status: str
    created_at: datetime
    updated_at: datetime


class SubscriptionCreate(BaseModel):
    member_id: str
    membership_plan_id: str
    branch_id: str
    start_date: date = Field(default_factory=date.today)
    sale_price: Optional[Decimal] = Field(default=None, ge=0)
    discount_amount: Decimal = Field(default=Decimal("0"), ge=0)
    auto_renew: bool = False


class SubscriptionOperation(BaseModel):
    action: Literal["RENEW", "FREEZE", "UNFREEZE", "EXTEND", "CANCEL", "CHANGE_PLAN"]
    days: Optional[int] = Field(default=None, ge=1)
    reason: Optional[str] = Field(default=None, max_length=500)
    membership_plan_id: Optional[str] = None


class DashboardMetric(BaseModel):
    value: float
    previous_value: float = 0
    change_percent: Optional[float] = None


class DashboardSummary(BaseModel):
    active_members: DashboardMetric
    expiring_7_days: int
    expiring_15_days: int
    expiring_30_days: int
    today_attendance: DashboardMetric
    new_members: DashboardMetric
    monthly_revenue: DashboardMetric
    pending_payments: float
    failed_or_overdue_payments: int
    new_leads: DashboardMetric
    lead_conversion_rate: float
    trainer_utilisation: float
    popular_plan: Optional[str] = None
    retention_rate: float
    churn_rate: float
    filters_applied: Dict[str, Any]
