#!/usr/bin/env python3
"""Seed a complete, idempotent demo dataset across every application table."""

from datetime import date, datetime, time, timedelta
from decimal import Decimal
import json
import sys
import uuid
from pathlib import Path

from sqlalchemy import JSON, MetaData, and_, func, insert, select

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.security import hash_password
from app.db.session import engine


NAMESPACE = uuid.UUID("42b6e021-d42e-4e40-aab9-53bed44ce101")
NOW = datetime.utcnow().replace(microsecond=0)
TODAY = NOW.date()


def demo_id(key: str) -> str:
    return str(uuid.uuid5(NAMESPACE, key))


metadata = MetaData()
metadata.reflect(bind=engine)


def table(name: str):
    return metadata.tables[name]


def existing(connection, table_name: str, **criteria):
    target = table(table_name)
    conditions = [target.c[key] == value for key, value in criteria.items()]
    return connection.execute(select(target).where(and_(*conditions))).mappings().first()


def ensure(connection, table_name: str, key: str, **values):
    target = table(table_name)
    row_id = values.get("id", demo_id(f"{table_name}:{key}"))
    if "id" in target.c and existing(connection, table_name, id=row_id):
        return row_id
    usable_values = {}
    for name, value in values.items():
        if name not in target.c:
            continue
        if isinstance(value, (dict, list)) and not isinstance(target.c[name].type, JSON):
            value = json.dumps(value)
        usable_values[name] = value
    if "id" in target.c:
        usable_values["id"] = row_id
    connection.execute(insert(target).values(**usable_values))
    return row_id


with engine.begin() as connection:
    tenant = existing(connection, "tenants", slug="demo-gym")
    if not tenant:
        tenant_id = ensure(
            connection,
            "tenants",
            "demo-gym",
            name="Demo Gym",
            slug="demo-gym",
            billing_email="demo@gym.example.com",
            status="active",
            created_at=NOW,
            updated_at=NOW,
        )
    else:
        tenant_id = tenant["id"]

    owner = existing(connection, "users", tenant_id=tenant_id, email="owner@example.com")
    if not owner:
        owner_id = ensure(
            connection,
            "users",
            "owner",
            tenant_id=tenant_id,
            email="owner@example.com",
            full_name="Demo Owner",
            password_hash=hash_password("owner123"),
            is_active=1,
            created_at=NOW,
            updated_at=NOW,
        )
    else:
        owner_id = owner["id"]

    branch = existing(connection, "branches", tenant_id=tenant_id, name="Main Branch")
    branch_id = branch["id"] if branch else ensure(
        connection,
        "branches",
        "main",
        tenant_id=tenant_id,
        name="Main Branch",
        address="123 Fitness Street, Bengaluru, Karnataka 560001",
        created_at=NOW,
        updated_at=NOW,
    )
    second_branch_id = ensure(
        connection,
        "branches",
        "indiranagar",
        tenant_id=tenant_id,
        name="Indiranagar Branch",
        address="100 Feet Road, Indiranagar, Bengaluru 560038",
        created_at=NOW,
        updated_at=NOW,
    )

    role_ids = {}
    for index, role_name in enumerate(
        ["SUPER_ADMIN", "OWNER", "MANAGER", "RECEPTIONIST", "TRAINER", "ACCOUNTANT", "MEMBER"],
        start=1,
    ):
        role = existing(connection, "roles", name=role_name)
        if role:
            role_ids[role_name] = role["id"]
        else:
            connection.execute(insert(table("roles")).values(name=role_name))
            role_ids[role_name] = existing(connection, "roles", name=role_name)["id"]

    def ensure_user(key, email, full_name, role_name):
        user = existing(connection, "users", tenant_id=tenant_id, email=email)
        user_id = user["id"] if user else ensure(
            connection,
            "users",
            key,
            tenant_id=tenant_id,
            email=email,
            full_name=full_name,
            password_hash=hash_password("Demo@123"),
            is_active=1,
            created_at=NOW,
            updated_at=NOW,
        )
        if not existing(connection, "user_roles", user_id=user_id, role_id=role_ids[role_name]):
            connection.execute(
                insert(table("user_roles")).values(user_id=user_id, role_id=role_ids[role_name])
            )
        return user_id

    if not existing(connection, "user_roles", user_id=owner_id, role_id=role_ids["OWNER"]):
        connection.execute(
            insert(table("user_roles")).values(user_id=owner_id, role_id=role_ids["OWNER"])
        )

    manager_id = ensure_user("manager", "manager@demo-gym.com", "Priya Sharma", "MANAGER")
    trainer_user_id = ensure_user("trainer", "trainer@demo-gym.com", "Arjun Mehta", "TRAINER")
    receptionist_id = ensure_user(
        "receptionist", "reception@demo-gym.com", "Neha Kapoor", "RECEPTIONIST"
    )
    accountant_id = ensure_user(
        "accountant", "accounts@demo-gym.com", "Rohan Iyer", "ACCOUNTANT"
    )

    staff_id = ensure(
        connection,
        "staff",
        "manager",
        tenant_id=tenant_id,
        branch_id=branch_id,
        user_id=manager_id,
        employee_code="EMP-001",
        designation="Branch Manager",
        joining_date=TODAY - timedelta(days=730),
        employment_type="FULL_TIME",
        monthly_salary=Decimal("65000.00"),
        commission_percent=Decimal("2.50"),
        status="ACTIVE",
        created_at=NOW,
        updated_at=NOW,
    )
    trainer_id = ensure(
        connection,
        "trainers",
        "arjun",
        tenant_id=tenant_id,
        branch_id=branch_id,
        user_id=trainer_user_id,
        trainer_code="TRN-001",
        specialization="Strength and functional training",
        experience_years=Decimal("7.5"),
        bio="Certified strength coach focused on sustainable progress.",
        hourly_rate=Decimal("1200.00"),
        commission_percent=Decimal("20.00"),
        status="ACTIVE",
        created_at=NOW,
        updated_at=NOW,
    )
    for weekday in range(1, 7):
        ensure(
            connection,
            "trainer_availability",
            f"arjun-{weekday}",
            trainer_id=trainer_id,
            day_of_week=weekday,
            start_time=time(6, 0),
            end_time=time(14, 0),
            is_available=True,
        )

    feature_defaults = {
        "dashboard": {"widgets": ["members", "revenue", "attendance", "leads"]},
        "members": {"medical_notes_restricted": True},
        "billing": {"currency": "INR"},
        "attendance": {"allow_manual_check_in": True},
        "classes": {"waiting_list_enabled": True},
        "workouts": {"progress_photos_enabled": True},
        "crm": {"follow_up_reminders": True},
        "communications": {"channels": ["EMAIL", "SMS"]},
    }
    for feature_key, config in feature_defaults.items():
        ensure(
            connection,
            "tenant_features",
            feature_key,
            tenant_id=tenant_id,
            feature_key=feature_key,
            enabled=True,
            config_json=config,
            updated_by=owner_id,
            created_at=NOW,
            updated_at=NOW,
        )

    plan_specs = [
        ("MONTHLY", "Monthly Unlimited", "MONTHLY", 1, "MONTH", "2499.00", 8, 2),
        ("QUARTERLY", "Quarterly Fitness", "QUARTERLY", 3, "MONTH", "6499.00", 24, 6),
        ("ANNUAL", "Annual Elite", "ANNUAL", 12, "MONTH", "19999.00", 120, 24),
        ("PT12", "Personal Training 12", "PT_PACKAGE", 3, "MONTH", "14999.00", 12, 12),
        ("TRIAL7", "Seven Day Trial", "TRIAL", 7, "DAY", "499.00", 3, 0),
    ]
    plan_ids = {}
    for code, name, plan_type, duration, unit, price, class_limit, pt_limit in plan_specs:
        plan_ids[code] = ensure(
            connection,
            "membership_plans",
            code,
            tenant_id=tenant_id,
            branch_id=None,
            plan_code=code,
            name=name,
            description=f"Configurable {name.lower()} package.",
            plan_type=plan_type,
            duration_value=duration,
            duration_unit=unit,
            visit_limit=None,
            class_limit=class_limit,
            pt_session_limit=pt_limit,
            base_price=Decimal(price),
            joining_fee=Decimal("500.00"),
            tax_percent=Decimal("18.00"),
            freeze_allowed=duration > 1,
            max_freeze_days=30 if duration > 1 else 7,
            grace_period_days=5,
            auto_renew_allowed=True,
            cross_branch_access=code == "ANNUAL",
            security_deposit=Decimal("0.00"),
            default_discount=Decimal("0.00"),
            terms_and_conditions="Membership is subject to configured cancellation and freeze rules.",
            rules_json={"renewal_reminder_days": [30, 15, 7], "transfer_allowed": True},
            status="ACTIVE",
            created_at=NOW,
            updated_at=NOW,
        )

    member_specs = [
        ("001", "Aarav", "Patel", "ACTIVE", -80, 45, "ANNUAL"),
        ("002", "Meera", "Nair", "ACTIVE", -50, 7, "QUARTERLY"),
        ("003", "Kabir", "Singh", "ACTIVE", -20, 15, "MONTHLY"),
        ("004", "Ananya", "Rao", "EXPIRED", -420, -30, "ANNUAL"),
        ("005", "Vikram", "Joshi", "FROZEN", -120, 90, "QUARTERLY"),
        ("006", "Ishita", "Desai", "ACTIVE", -10, 30, "PT12"),
        ("007", "Rahul", "Verma", "BLOCKED", -200, -5, "MONTHLY"),
        ("008", "Sanya", "Gupta", "INACTIVE", -300, -120, "QUARTERLY"),
    ]
    member_ids = {}
    subscription_ids = {}
    invoice_ids = {}
    payment_ids = {}
    for index, (code, first, last, status, joined_offset, expiry_offset, plan_code) in enumerate(
        member_specs, start=1
    ):
        member_user_id = ensure_user(
            f"member-{code}",
            f"{first.lower()}.{last.lower()}@example.com",
            f"{first} {last}",
            "MEMBER",
        )
        member_id = ensure(
            connection,
            "members",
            code,
            tenant_id=tenant_id,
            home_branch_id=branch_id if index < 7 else second_branch_id,
            user_id=member_user_id,
            assigned_trainer_id=trainer_id,
            member_code=f"MEM-{code}",
            first_name=first,
            last_name=last,
            email=f"{first.lower()}.{last.lower()}@example.com",
            phone=f"+91980000{index:04d}",
            alternate_phone=f"+91970000{index:04d}",
            date_of_birth=date(1990 + index, (index % 12) + 1, min(index + 5, 28)),
            gender="FEMALE" if index % 2 == 0 else "MALE",
            blood_group=["O+", "A+", "B+", "AB+"][index % 4],
            address_line1=f"{10 + index}, Demo Layout",
            city="Bengaluru",
            state="Karnataka",
            postal_code="560001",
            emergency_contact_name=f"Emergency Contact {index}",
            emergency_contact_phone=f"+91960000{index:04d}",
            occupation="Professional",
            source=["Instagram", "Referral", "Walk-in"][index % 3],
            joining_date=TODAY + timedelta(days=joined_offset),
            profile_photo_url=f"https://example.com/demo/members/{code}.jpg",
            medical_notes="No known restrictions." if index != 3 else "Avoid heavy impact exercises.",
            fitness_goal=["Weight loss", "Strength", "Mobility"][index % 3],
            internal_notes="Demo member generated for product evaluation.",
            custom_fields_json={"preferred_language": "English", "tshirt_size": "M"},
            family_group_id="FAMILY-DEMO-01" if index in (1, 2) else None,
            corporate_account="Demo Technologies Pvt Ltd" if index in (6, 8) else None,
            blocked_reason="Payment overdue" if status == "BLOCKED" else None,
            status=status,
            created_at=NOW + timedelta(days=joined_offset),
            updated_at=NOW,
        )
        member_ids[code] = member_id
        ensure(
            connection,
            "member_documents",
            code,
            tenant_id=tenant_id,
            member_id=member_id,
            document_type="ID_PROOF",
            file_name=f"member-{code}-id.pdf",
            file_url=f"https://example.com/demo/documents/member-{code}-id.pdf",
            uploaded_by=owner_id,
            created_at=NOW,
        )
        ensure(
            connection,
            "member_consents",
            code,
            tenant_id=tenant_id,
            member_id=member_id,
            consent_type="LIABILITY_WAIVER",
            document_version="1.0",
            accepted=True,
            accepted_at=NOW + timedelta(days=joined_offset),
            ip_address="127.0.0.1",
            created_at=NOW + timedelta(days=joined_offset),
        )
        start_date = TODAY + timedelta(days=joined_offset)
        end_date = TODAY + timedelta(days=expiry_offset)
        subscription_status = (
            "ACTIVE" if status == "ACTIVE" else "FROZEN" if status == "FROZEN" else "EXPIRED"
        )
        price = Decimal(next(spec[5] for spec in plan_specs if spec[0] == plan_code))
        tax = (price * Decimal("0.18")).quantize(Decimal("0.01"))
        subscription_id = ensure(
            connection,
            "member_subscriptions",
            code,
            tenant_id=tenant_id,
            branch_id=branch_id if index < 7 else second_branch_id,
            member_id=member_id,
            membership_plan_id=plan_ids[plan_code],
            subscription_number=f"SUB-2026-{code}",
            start_date=start_date,
            end_date=end_date,
            original_end_date=end_date,
            sale_price=price,
            discount_amount=Decimal("0.00"),
            tax_amount=tax,
            final_amount=price + tax,
            auto_renew=index % 2 == 0,
            remaining_visits=None,
            remaining_classes=max(0, 20 - index),
            remaining_pt_sessions=max(0, 8 - index),
            status=subscription_status,
            created_by=owner_id,
            created_at=NOW + timedelta(days=joined_offset),
            updated_at=NOW,
            version=0,
        )
        subscription_ids[code] = subscription_id
        is_paid = index not in (3, 7)
        total = price + tax
        invoice_id = ensure(
            connection,
            "invoices",
            code,
            tenant_id=tenant_id,
            branch_id=branch_id if index < 7 else second_branch_id,
            member_id=member_id,
            subscription_id=subscription_id,
            invoice_number=f"INV-2026-{code}",
            invoice_date=start_date,
            due_date=start_date + timedelta(days=7),
            subtotal_amount=price,
            discount_amount=Decimal("0.00"),
            tax_amount=tax,
            total_amount=total,
            paid_amount=total if is_paid else Decimal("0.00"),
            balance_amount=Decimal("0.00") if is_paid else total,
            status="PAID" if is_paid else "OVERDUE",
            notes="Demo membership invoice.",
            created_by=owner_id,
            created_at=NOW + timedelta(days=joined_offset),
            updated_at=NOW,
        )
        invoice_ids[code] = invoice_id
        ensure(
            connection,
            "invoice_items",
            code,
            invoice_id=invoice_id,
            item_type="MEMBERSHIP",
            description=f"{plan_code} membership package",
            quantity=Decimal("1.00"),
            unit_price=price,
            discount_amount=Decimal("0.00"),
            tax_percent=Decimal("18.00"),
            tax_amount=tax,
            line_total=total,
        )
        if is_paid:
            payment_ids[code] = ensure(
                connection,
                "payments",
                code,
                tenant_id=tenant_id,
                branch_id=branch_id if index < 7 else second_branch_id,
                member_id=member_id,
                invoice_id=invoice_id,
                payment_number=f"PAY-2026-{code}",
                payment_method=["UPI", "CARD", "CASH"][index % 3],
                gateway_name="DemoPay" if index % 3 != 0 else None,
                gateway_transaction_id=f"DEMO-TXN-{code}" if index % 3 != 0 else None,
                amount=total,
                payment_date=NOW + timedelta(days=joined_offset),
                status="SUCCESS",
                reference_number=f"REF-{code}",
                notes="Demo payment.",
                collected_by=receptionist_id,
                idempotency_key=f"demo-payment-{code}",
                created_at=NOW + timedelta(days=joined_offset),
                updated_at=NOW,
            )
        ensure(
            connection,
            "body_measurements",
            code,
            tenant_id=tenant_id,
            member_id=member_id,
            measured_by=trainer_user_id,
            measurement_date=TODAY - timedelta(days=index * 3),
            weight_kg=Decimal(str(58 + index * 3)),
            height_cm=Decimal(str(160 + index * 2)),
            bmi=Decimal("23.40"),
            body_fat_percent=Decimal(str(18 + index)),
            muscle_mass_kg=Decimal(str(40 + index)),
            chest_cm=Decimal(str(84 + index)),
            waist_cm=Decimal(str(72 + index)),
            hips_cm=Decimal(str(88 + index)),
            arm_cm=Decimal(str(28 + index / 2)),
            thigh_cm=Decimal(str(48 + index / 2)),
            notes="Baseline demo measurement.",
            created_at=NOW,
        )
        ensure(
            connection,
            "progress_photos",
            code,
            tenant_id=tenant_id,
            member_id=member_id,
            photo_date=TODAY - timedelta(days=index * 3),
            photo_type="FRONT",
            file_url=f"https://example.com/demo/progress/{code}-front.jpg",
            notes="Baseline progress photo.",
            created_at=NOW,
        )
        ensure(
            connection,
            "member_timeline_events",
            code,
            tenant_id=tenant_id,
            member_id=member_id,
            actor_user_id=owner_id,
            event_type="MEMBERSHIP_CREATED",
            title=f"{plan_code} membership activated",
            details_json={"subscription_number": f"SUB-2026-{code}"},
            created_at=NOW + timedelta(days=joined_offset),
        )

    ensure(
        connection,
        "subscription_freezes",
        "member-005",
        tenant_id=tenant_id,
        subscription_id=subscription_ids["005"],
        freeze_start_date=TODAY - timedelta(days=5),
        freeze_end_date=TODAY + timedelta(days=10),
        total_days=16,
        reason="Travel",
        status="APPROVED",
        requested_by=owner_id,
        approved_by=owner_id,
        approved_at=NOW - timedelta(days=6),
        created_at=NOW - timedelta(days=7),
    )
    ensure(
        connection,
        "refunds",
        "member-002",
        tenant_id=tenant_id,
        payment_id=payment_ids["002"],
        refund_number="REFUND-2026-001",
        amount=Decimal("500.00"),
        reason="Duplicate add-on charge",
        gateway_refund_id="DEMO-RFD-001",
        status="COMPLETED",
        requested_by=accountant_id,
        approved_by=owner_id,
        created_at=NOW - timedelta(days=2),
        updated_at=NOW - timedelta(days=1),
    )

    access_device_id = ensure(
        connection,
        "access_devices",
        "main-gate",
        tenant_id=tenant_id,
        branch_id=branch_id,
        device_code="GATE-MAIN-01",
        device_type="QR_SCANNER",
        name="Main entrance scanner",
        ip_address="10.0.0.25",
        status="ONLINE",
        last_seen_at=NOW,
        created_at=NOW - timedelta(days=180),
    )
    for day_offset in range(0, 14):
        for member_index, code in enumerate(["001", "002", "003", "005", "006"], start=1):
            if (day_offset + member_index) % 3:
                check_in = NOW - timedelta(days=day_offset, hours=member_index)
                ensure(
                    connection,
                    "attendance_records",
                    f"{code}-{day_offset}",
                    tenant_id=tenant_id,
                    branch_id=branch_id,
                    member_id=member_ids[code],
                    subscription_id=subscription_ids[code],
                    access_device_id=access_device_id,
                    check_in_at=check_in,
                    check_out_at=check_in + timedelta(hours=1, minutes=10),
                    check_in_method="QR",
                    attendance_status="VALID",
                    created_at=check_in,
                )

    class_type_id = ensure(
        connection,
        "class_types",
        "yoga",
        tenant_id=tenant_id,
        name="Power Yoga",
        description="Instructor-led flexibility and strength class.",
        default_duration_min=60,
        status="ACTIVE",
        created_at=NOW,
    )
    schedule_id = ensure(
        connection,
        "class_schedules",
        "yoga-tomorrow",
        tenant_id=tenant_id,
        branch_id=branch_id,
        class_type_id=class_type_id,
        trainer_id=trainer_id,
        title="Morning Power Yoga",
        room_name="Studio A",
        start_at=(NOW + timedelta(days=1)).replace(hour=7, minute=0),
        end_at=(NOW + timedelta(days=1)).replace(hour=8, minute=0),
        capacity=20,
        waiting_list_limit=5,
        booking_opens_at=NOW - timedelta(days=7),
        booking_closes_at=NOW + timedelta(hours=20),
        cancellation_cutoff_min=120,
        status="SCHEDULED",
        created_at=NOW,
        updated_at=NOW,
    )
    ensure(
        connection,
        "class_bookings",
        "yoga-member-001",
        tenant_id=tenant_id,
        class_schedule_id=schedule_id,
        member_id=member_ids["001"],
        subscription_id=subscription_ids["001"],
        booking_status="BOOKED",
        booked_at=NOW,
    )

    exercise_ids = {}
    for key, name, muscle, equipment in [
        ("squat", "Goblet Squat", "Legs", "Dumbbell"),
        ("pushup", "Push-up", "Chest", "Bodyweight"),
        ("row", "Seated Cable Row", "Back", "Cable machine"),
    ]:
        exercise_ids[key] = ensure(
            connection,
            "exercises",
            key,
            tenant_id=tenant_id,
            name=name,
            muscle_group=muscle,
            equipment=equipment,
            instructions="Use controlled form and stop if discomfort occurs.",
            video_url=f"https://example.com/demo/exercises/{key}",
            is_global=False,
            status="ACTIVE",
            created_at=NOW,
        )
    workout_template_id = ensure(
        connection,
        "workout_templates",
        "beginner-strength",
        tenant_id=tenant_id,
        created_by_trainer_id=trainer_id,
        name="Beginner Full Body Strength",
        description="Three foundational movements.",
        difficulty_level="BEGINNER",
        goal_type="STRENGTH",
        status="ACTIVE",
        created_at=NOW,
        updated_at=NOW,
    )
    for sequence, exercise_key in enumerate(["squat", "pushup", "row"], start=1):
        ensure(
            connection,
            "workout_template_exercises",
            exercise_key,
            workout_template_id=workout_template_id,
            exercise_id=exercise_ids[exercise_key],
            day_number=1,
            sequence_number=sequence,
            target_sets=3,
            target_reps="10-12",
            target_weight=Decimal("10.00") if exercise_key != "pushup" else None,
            rest_seconds=60,
            notes="Focus on technique.",
        )
    workout_plan_id = ensure(
        connection,
        "member_workout_plans",
        "member-001",
        tenant_id=tenant_id,
        member_id=member_ids["001"],
        trainer_id=trainer_id,
        workout_template_id=workout_template_id,
        name="Aarav's Strength Foundation",
        start_date=TODAY - timedelta(days=14),
        end_date=TODAY + timedelta(days=76),
        status="ACTIVE",
        created_at=NOW - timedelta(days=14),
        updated_at=NOW,
    )
    workout_session_id = ensure(
        connection,
        "workout_sessions",
        "member-001-session",
        tenant_id=tenant_id,
        member_id=member_ids["001"],
        workout_plan_id=workout_plan_id,
        trainer_id=trainer_id,
        started_at=NOW - timedelta(days=1, hours=1),
        completed_at=NOW - timedelta(days=1),
        duration_minutes=60,
        notes="Good technique and steady pacing.",
        status="COMPLETED",
    )
    for sequence, exercise_key in enumerate(["squat", "pushup", "row"], start=1):
        ensure(
            connection,
            "workout_session_exercises",
            exercise_key,
            workout_session_id=workout_session_id,
            exercise_id=exercise_ids[exercise_key],
            sequence_number=sequence,
            sets_completed=3,
            reps_completed="12,12,10",
            weight_used=Decimal("12.50") if exercise_key != "pushup" else None,
            calories_burned=Decimal("45.00"),
            notes="Completed as planned.",
        )
    ensure(
        connection,
        "personal_training_sessions",
        "member-006",
        tenant_id=tenant_id,
        branch_id=branch_id,
        member_id=member_ids["006"],
        trainer_id=trainer_id,
        subscription_id=subscription_ids["006"],
        scheduled_start_at=NOW + timedelta(days=2),
        scheduled_end_at=NOW + timedelta(days=2, hours=1),
        status="SCHEDULED",
        notes="Lower-body strength assessment.",
        created_at=NOW,
        updated_at=NOW,
    )

    lead_ids = {}
    lead_specs = [
        ("001", "Riya", "Malhotra", "NEW", "Instagram"),
        ("002", "Dev", "Khanna", "CONTACTED", "Website"),
        ("003", "Nikhil", "Bose", "TRIAL", "Referral"),
        ("004", "Tanya", "Menon", "CONVERTED", "Walk-in"),
        ("005", "Aditya", "Kulkarni", "LOST", "Google"),
    ]
    for index, (code, first, last, stage, source) in enumerate(lead_specs, start=1):
        lead_ids[code] = ensure(
            connection,
            "leads",
            code,
            tenant_id=tenant_id,
            branch_id=branch_id,
            assigned_to=receptionist_id,
            first_name=first,
            last_name=last,
            phone=f"+91950000{index:04d}",
            email=f"{first.lower()}.{last.lower()}@lead.example.com",
            source=source,
            interested_plan_id=plan_ids["QUARTERLY"],
            preferred_time="Evening",
            stage=stage,
            next_follow_up_at=NOW + timedelta(days=index),
            lost_reason="Budget constraints" if stage == "LOST" else None,
            notes="Demo CRM lead.",
            converted_member_id=member_ids["006"] if stage == "CONVERTED" else None,
            created_at=NOW - timedelta(days=index * 2),
            updated_at=NOW,
        )
        ensure(
            connection,
            "lead_follow_ups",
            code,
            tenant_id=tenant_id,
            lead_id=lead_ids[code],
            performed_by=receptionist_id,
            follow_up_type="CALL",
            outcome="Shared plan details and scheduled next contact.",
            next_follow_up_at=NOW + timedelta(days=index),
            created_at=NOW - timedelta(days=index),
        )
    ensure(
        connection,
        "trial_passes",
        "lead-003",
        tenant_id=tenant_id,
        branch_id=branch_id,
        lead_id=lead_ids["003"],
        pass_code="TRIAL-DEMO-003",
        valid_from=NOW - timedelta(days=1),
        valid_until=NOW + timedelta(days=6),
        max_visits=3,
        used_visits=1,
        status="ACTIVE",
        created_at=NOW - timedelta(days=1),
    )

    message_template_id = ensure(
        connection,
        "message_templates",
        "expiry-reminder",
        tenant_id=tenant_id,
        template_code="MEMBERSHIP_EXPIRY",
        name="Membership expiry reminder",
        channel="EMAIL",
        subject_template="Your membership expires soon",
        body_template="Hi {{member_name}}, your membership expires on {{expiry_date}}.",
        status="ACTIVE",
        created_at=NOW,
        updated_at=NOW,
    )
    ensure(
        connection,
        "notifications",
        "member-002-expiry",
        tenant_id=tenant_id,
        user_id=None,
        member_id=member_ids["002"],
        channel="EMAIL",
        recipient="meera.nair@example.com",
        subject="Your membership expires in 7 days",
        message_body="Renew now to continue without interruption.",
        notification_type="MEMBERSHIP_EXPIRY",
        reference_type="SUBSCRIPTION",
        reference_id=subscription_ids["002"],
        scheduled_at=NOW,
        sent_at=NOW,
        status="SENT",
        provider_message_id="DEMO-MSG-001",
        retry_count=0,
        created_at=NOW,
    )
    ensure(
        connection,
        "support_tickets",
        "ticket-001",
        tenant_id=tenant_id,
        raised_by=manager_id,
        assigned_to=owner_id,
        ticket_number="TKT-2026-001",
        category="BILLING",
        subject="Demo invoice reconciliation question",
        description="Example support ticket for testing the support workflow.",
        priority="MEDIUM",
        status="OPEN",
        created_at=NOW,
        updated_at=NOW,
    )
    ensure(
        connection,
        "audit_logs",
        "seed-complete",
        tenant_id=tenant_id,
        user_id=owner_id,
        branch_id=branch_id,
        action="DEMO_DATA_SEEDED",
        entity_type="TENANT",
        entity_id=tenant_id,
        new_values_json={"dataset": "complete-demo-v1"},
        reason="Populate demonstration environment",
        ip_address="127.0.0.1",
        user_agent="seed_demo_data.py",
        request_id="demo-seed-v1",
        created_at=NOW,
    )
    ensure(
        connection,
        "integration_configs",
        "email-demo",
        tenant_id=tenant_id,
        integration_type="EMAIL",
        provider_name="DEMO",
        config_encrypted="DEMO_ONLY_NOT_A_REAL_CREDENTIAL",
        status="INACTIVE",
        last_tested_at=NOW,
        created_at=NOW,
        updated_at=NOW,
    )
    ensure(
        connection,
        "webhook_events",
        "payment-demo",
        tenant_id=tenant_id,
        provider_name="DemoPay",
        event_id="evt_demo_payment_001",
        event_type="payment.success",
        payload_json={"payment_number": "PAY-2026-001", "demo": True},
        signature_valid=True,
        processing_status="PROCESSED",
        retry_count=0,
        processed_at=NOW,
        created_at=NOW,
    )

    application_tables = sorted(
        name for name in metadata.tables if name != "alembic_version"
    )
    counts = {
        name: connection.execute(select(func.count()).select_from(table(name))).scalar_one()
        for name in application_tables
    }

print("Demo data seeding complete.")
print(f"Tenant: demo-gym ({tenant_id})")
print(f"Application tables covered: {len(counts)}")
for table_name in sorted(counts):
    print(f"  {table_name}: {counts[table_name]}")
