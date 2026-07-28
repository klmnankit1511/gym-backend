#!/usr/bin/env python3
"""
Seed script to create initial roles, tenant, branch, and owner account for testing.
Run this once after initial setup and database migrations: python scripts/seed_owner.py
"""
import sys
import uuid
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import SessionLocal, engine, Base
from app.models.user import User, Role
from app.models.tenant import Tenant, Branch
from app.core.security import hash_password

# Create tables (normally done via Alembic migrations)
Base.metadata.create_all(bind=engine)

db = SessionLocal()

# Seed roles (global catalog)
ROLES = ["SUPER_ADMIN", "OWNER", "MANAGER", "RECEPTIONIST", "TRAINER", "ACCOUNTANT", "MEMBER"]

for role_name in ROLES:
    existing_role = db.query(Role).filter(Role.name == role_name).first()
    if not existing_role:
        role = Role(name=role_name)
        db.add(role)
        print(f"✓ Created role: {role_name}")
    else:
        print(f"✓ Role already exists: {role_name}")

db.commit()

# Create demo tenant
demo_tenant = db.query(Tenant).filter(Tenant.slug == "demo-gym").first()

if not demo_tenant:
    demo_tenant = Tenant(
        id=str(uuid.uuid4()),
        name="Demo Gym",
        slug="demo-gym",
        billing_email="demo@gym.example.com",
        status="active"
    )
    db.add(demo_tenant)
    db.commit()
    db.refresh(demo_tenant)
    print(f"\n✓ Created tenant:")
    print(f"  Name: {demo_tenant.name}")
    print(f"  Slug: {demo_tenant.slug}")
    print(f"  Tenant ID: {demo_tenant.id}")
else:
    print(f"\n✓ Tenant already exists: {demo_tenant.slug}")

# Create main branch for the demo tenant
main_branch = db.query(Branch).filter(
    Branch.tenant_id == demo_tenant.id,
    Branch.name == "Main Branch"
).first()

if not main_branch:
    main_branch = Branch(
        id=str(uuid.uuid4()),
        tenant_id=demo_tenant.id,
        name="Main Branch",
        address="123 Main Street, City, State 12345"
    )
    db.add(main_branch)
    db.commit()
    db.refresh(main_branch)
    print(f"✓ Created branch:")
    print(f"  Name: {main_branch.name}")
    print(f"  Branch ID: {main_branch.id}")
else:
    print(f"✓ Branch already exists: {main_branch.name}")

# Create demo owner user
owner_email = "owner@example.com"
existing_owner = db.query(User).filter(
    User.email == owner_email,
    User.tenant_id == demo_tenant.id
).first()

if not existing_owner:
    owner_role = db.query(Role).filter(Role.name == "OWNER").first()
    owner = User(
        id=f"usr_{uuid.uuid4().hex[:8]}",
        tenant_id=demo_tenant.id,
        email=owner_email,
        full_name="Demo Owner",
        password_hash=hash_password("owner123"),
    )
    owner.roles.append(owner_role)
    db.add(owner)
    db.commit()
    db.refresh(owner)
    print(f"\n✓ Created owner account:")
    print(f"  Email: {owner_email}")
    print(f"  Password: owner123")
    print(f"  Tenant: {demo_tenant.slug}")
    print(f"  User ID: {owner.id}")
else:
    print(f"\n✓ Owner account already exists: {owner_email}")

db.close()
print("\n✓ Database seeding complete!")
print("\nYou can now login with:")
print(f"  Email: {owner_email}")
print(f"  Password: owner123")
