from datetime import datetime
import uuid

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, JSON, Numeric, String, Text

from app.db.session import Base


def new_id() -> str:
    return str(uuid.uuid4())


class TenantFeature(Base):
    __tablename__ = "tenant_features"
    id = Column(String(36), primary_key=True, default=new_id)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    feature_key = Column(String(100), nullable=False)
    enabled = Column(Boolean, nullable=False, default=True)
    config_json = Column(JSON, nullable=True)
    updated_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class Trainer(Base):
    __tablename__ = "trainers"
    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    branch_id = Column(String(36), ForeignKey("branches.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    trainer_code = Column(String(50), nullable=False)
    specialization = Column(String(255), nullable=True)
    experience_years = Column(Numeric(4, 1), nullable=True)
    bio = Column(Text, nullable=True)
    hourly_rate = Column(Numeric(12, 2), nullable=True)
    commission_percent = Column(Numeric(5, 2), nullable=True)
    status = Column(String(20), nullable=False, default="ACTIVE")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class Member(Base):
    __tablename__ = "members"
    id = Column(String(36), primary_key=True, default=new_id)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    home_branch_id = Column(String(36), ForeignKey("branches.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    assigned_trainer_id = Column(String(36), ForeignKey("trainers.id"), nullable=True)
    member_code = Column(String(50), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=True)
    email = Column(String(150), nullable=True)
    phone = Column(String(30), nullable=False)
    alternate_phone = Column(String(30), nullable=True)
    date_of_birth = Column(Date, nullable=True)
    gender = Column(String(20), nullable=True)
    blood_group = Column(String(10), nullable=True)
    address_line1 = Column(String(200), nullable=True)
    address_line2 = Column(String(200), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    emergency_contact_name = Column(String(150), nullable=True)
    emergency_contact_phone = Column(String(30), nullable=True)
    occupation = Column(String(100), nullable=True)
    source = Column(String(100), nullable=True)
    joining_date = Column(Date, nullable=False)
    profile_photo_url = Column(String(500), nullable=True)
    medical_notes = Column(Text, nullable=True)
    fitness_goal = Column(String(500), nullable=True)
    internal_notes = Column(Text, nullable=True)
    custom_fields_json = Column(JSON, nullable=True)
    family_group_id = Column(String(100), nullable=True)
    corporate_account = Column(String(200), nullable=True)
    blocked_reason = Column(String(500), nullable=True)
    status = Column(String(20), nullable=False, default="ACTIVE")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class MemberDocument(Base):
    __tablename__ = "member_documents"
    id = Column(String(36), primary_key=True, default=new_id)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    member_id = Column(String(36), ForeignKey("members.id"), nullable=False)
    document_type = Column(String(50), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_url = Column(String(500), nullable=False)
    uploaded_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class MemberConsent(Base):
    __tablename__ = "member_consents"
    id = Column(String(36), primary_key=True, default=new_id)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    member_id = Column(String(36), ForeignKey("members.id"), nullable=False)
    consent_type = Column(String(50), nullable=False)
    document_version = Column(String(50), nullable=False)
    accepted = Column(Boolean, nullable=False)
    accepted_at = Column(DateTime, nullable=True)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class MembershipPlan(Base):
    __tablename__ = "membership_plans"
    id = Column(String(36), primary_key=True, default=new_id)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    branch_id = Column(String(36), ForeignKey("branches.id"), nullable=True)
    plan_code = Column(String(50), nullable=False)
    name = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    plan_type = Column(String(30), nullable=False)
    duration_value = Column(Integer, nullable=True)
    duration_unit = Column(String(10), nullable=True)
    visit_limit = Column(Integer, nullable=True)
    class_limit = Column(Integer, nullable=True)
    pt_session_limit = Column(Integer, nullable=True)
    base_price = Column(Numeric(12, 2), nullable=False)
    joining_fee = Column(Numeric(12, 2), nullable=False, default=0)
    tax_percent = Column(Numeric(5, 2), nullable=False, default=0)
    freeze_allowed = Column(Boolean, nullable=False, default=False)
    max_freeze_days = Column(Integer, nullable=True)
    grace_period_days = Column(Integer, nullable=False, default=0)
    auto_renew_allowed = Column(Boolean, nullable=False, default=False)
    cross_branch_access = Column(Boolean, nullable=False, default=False)
    security_deposit = Column(Numeric(12, 2), nullable=False, default=0)
    default_discount = Column(Numeric(12, 2), nullable=False, default=0)
    terms_and_conditions = Column(Text, nullable=True)
    rules_json = Column(JSON, nullable=True)
    status = Column(String(20), nullable=False, default="ACTIVE")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class MemberSubscription(Base):
    __tablename__ = "member_subscriptions"
    id = Column(String(36), primary_key=True, default=new_id)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    branch_id = Column(String(36), ForeignKey("branches.id"), nullable=False)
    member_id = Column(String(36), ForeignKey("members.id"), nullable=False)
    membership_plan_id = Column(String(36), ForeignKey("membership_plans.id"), nullable=False)
    subscription_number = Column(String(60), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    original_end_date = Column(Date, nullable=False)
    sale_price = Column(Numeric(12, 2), nullable=False)
    discount_amount = Column(Numeric(12, 2), nullable=False, default=0)
    tax_amount = Column(Numeric(12, 2), nullable=False, default=0)
    final_amount = Column(Numeric(12, 2), nullable=False)
    auto_renew = Column(Boolean, nullable=False, default=False)
    remaining_visits = Column(Integer, nullable=True)
    remaining_classes = Column(Integer, nullable=True)
    remaining_pt_sessions = Column(Integer, nullable=True)
    status = Column(String(20), nullable=False, default="PENDING")
    cancellation_reason = Column(String(500), nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    version = Column(Integer, nullable=False, default=0)


class Invoice(Base):
    __tablename__ = "invoices"
    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    branch_id = Column(String(36), ForeignKey("branches.id"), nullable=False)
    member_id = Column(String(36), ForeignKey("members.id"), nullable=False)
    subscription_id = Column(String(36), ForeignKey("member_subscriptions.id"), nullable=True)
    invoice_number = Column(String(60), nullable=False)
    invoice_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=True)
    subtotal_amount = Column(Numeric(12, 2), nullable=False)
    discount_amount = Column(Numeric(12, 2), nullable=False)
    tax_amount = Column(Numeric(12, 2), nullable=False)
    total_amount = Column(Numeric(12, 2), nullable=False)
    paid_amount = Column(Numeric(12, 2), nullable=False)
    balance_amount = Column(Numeric(12, 2), nullable=False)
    status = Column(String(20), nullable=False)
    notes = Column(String(1000), nullable=True)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)


class Payment(Base):
    __tablename__ = "payments"
    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    branch_id = Column(String(36), ForeignKey("branches.id"), nullable=False)
    member_id = Column(String(36), ForeignKey("members.id"), nullable=False)
    invoice_id = Column(String(36), ForeignKey("invoices.id"), nullable=True)
    payment_number = Column(String(60), nullable=False)
    payment_method = Column(String(50), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    payment_date = Column(DateTime, nullable=False)
    status = Column(String(30), nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)


class AttendanceRecord(Base):
    __tablename__ = "attendance_records"
    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    branch_id = Column(String(36), ForeignKey("branches.id"), nullable=False)
    member_id = Column(String(36), ForeignKey("members.id"), nullable=False)
    subscription_id = Column(String(36), ForeignKey("member_subscriptions.id"), nullable=True)
    access_device_id = Column(String(36), nullable=True)
    check_in_at = Column(DateTime, nullable=False)
    check_out_at = Column(DateTime, nullable=True)
    check_in_method = Column(String(20), nullable=False)
    attendance_status = Column(String(30), nullable=False)
    override_reason = Column(String(500), nullable=True)
    override_by = Column(String(36), nullable=True)
    created_at = Column(DateTime, nullable=False)


class Lead(Base):
    __tablename__ = "leads"
    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    branch_id = Column(String(36), ForeignKey("branches.id"), nullable=False)
    assigned_to = Column(String(36), nullable=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=True)
    phone = Column(String(30), nullable=False)
    email = Column(String(150), nullable=True)
    source = Column(String(100), nullable=True)
    interested_plan_id = Column(String(36), nullable=True)
    stage = Column(String(30), nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)


class MemberMeasurement(Base):
    __tablename__ = "body_measurements"
    id = Column(String(36), primary_key=True, default=new_id)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    member_id = Column(String(36), ForeignKey("members.id"), nullable=False)
    measured_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    measurement_date = Column(Date, nullable=False, default=lambda: datetime.utcnow().date())
    weight_kg = Column(Numeric(6, 2), nullable=True)
    height_cm = Column(Numeric(6, 2), nullable=True)
    bmi = Column(Numeric(5, 2), nullable=True)
    body_fat_percent = Column(Numeric(5, 2), nullable=True)
    muscle_mass_kg = Column(Numeric(6, 2), nullable=True)
    chest_cm = Column(Numeric(6, 2), nullable=True)
    waist_cm = Column(Numeric(6, 2), nullable=True)
    hips_cm = Column(Numeric(6, 2), nullable=True)
    arm_cm = Column(Numeric(6, 2), nullable=True)
    thigh_cm = Column(Numeric(6, 2), nullable=True)
    notes = Column(String(1000), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class MemberProgressPhoto(Base):
    __tablename__ = "progress_photos"
    id = Column(String(36), primary_key=True, default=new_id)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    member_id = Column(String(36), ForeignKey("members.id"), nullable=False)
    photo_date = Column(Date, nullable=False, default=lambda: datetime.utcnow().date())
    photo_type = Column(String(20), nullable=False)
    file_url = Column(String(500), nullable=False)
    notes = Column(String(500), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class MemberTimelineEvent(Base):
    __tablename__ = "member_timeline_events"
    id = Column(String(36), primary_key=True, default=new_id)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False)
    member_id = Column(String(36), ForeignKey("members.id"), nullable=False)
    actor_user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    event_type = Column(String(100), nullable=False)
    title = Column(String(255), nullable=False)
    details_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
