# Alembic Database Migrations Guide

This document describes all database migrations for the Gym Manager API.

## Migration Overview

The database schema is built incrementally through Alembic migrations, organized by feature domain:

| Revision | Name | Description |
|----------|------|-------------|
| `2026_07_25_0001` | Initial Schema | Core multi-tenant structure (tenants, branches, users, roles) |
| `2026_07_28_0002` | Gym Core Tables | Members, staff, trainers, and documents |
| `2026_07_28_0003` | Memberships & Payments | Plans, subscriptions, invoices, and payments |
| `2026_07_28_0004` | Attendance | Access devices and attendance records |
| `2026_07_28_0005` | Classes & Workouts | Classes, exercises, workout plans, and body measurements |
| `2026_07_28_0006` | CRM & Integrations | Leads, notifications, support tickets, and integrations |

## Running Migrations

### View Migration Status

```bash
# Check which migrations have been applied
alembic current

# View all migrations
alembic history
```

### Apply Migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Apply specific migration
alembic upgrade 2026_07_28_0003

# Apply next migration
alembic upgrade +1
```

### Rollback Migrations

```bash
# Rollback to previous migration
alembic downgrade -1

# Rollback to specific migration
alembic downgrade 2026_07_25_0001

# Rollback all migrations
alembic downgrade base
```

### Create New Migration

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "description of change"

# Create empty migration
alembic revision -m "description of change"
```

## Migration Details

### 2026_07_25_0001: Initial Schema

**Tables Created:**
- `tenants` - Multi-tenant gym organizations
- `branches` - Gym branch locations
- `users` - System users with roles
- `roles` - User roles (admin, manager, trainer, staff, member)
- `user_roles` - User-role assignments per branch

**Key Features:**
- Multi-tenant data isolation
- Branch-level role assignments
- Soft delete support (ready for future implementation)

### 2026_07_28_0002: Gym Core Tables

**Tables Created:**
- `staff` - Gym staff members (receptionists, managers)
- `trainers` - Fitness trainers with specialization
- `trainer_availability` - Weekly availability slots
- `members` - Gym members with profile information
- `member_documents` - ID proofs, waivers, certificates
- `member_consents` - Terms, privacy, medical consents

**Relationships:**
- Staff → User (1-to-1)
- Trainers → User (1-to-1)
- Members → Trainers (optional, assigned trainer)
- Members → User (optional, member portal login)

**Constraints:**
- Unique trainer code per tenant
- Unique member code per tenant
- Phone number unique per tenant (with optional alternate)

### 2026_07_28_0003: Memberships & Payments

**Tables Created:**
- `membership_plans` - Plan types with pricing and features
- `member_subscriptions` - Active/inactive memberships
- `subscription_freezes` - Freeze requests and approvals
- `invoices` - Billing invoices
- `invoice_items` - Line items in invoices
- `payments` - Payment records (cash, card, UPI, etc.)
- `refunds` - Refund requests and tracking

**Key Features:**
- Visit, class, and PT session limits per plan
- Automatic renewal support
- Cross-branch access support
- Freeze/unfreeze membership logic
- Payment gateway integration ready
- Idempotent payments (prevent duplicates)

**Relationships:**
- Subscription → Member → Trainer (optional for personal training)
- Invoice → Subscription → Member
- Payment → Invoice → Member
- Refund → Payment

### 2026_07_28_0004: Attendance

**Tables Created:**
- `access_devices` - QR, RFID, biometric, facial recognition
- `attendance_records` - Check-in/check-out logs

**Key Features:**
- Multiple check-in methods
- Attendance validation (valid, duplicate, expired membership, blocked)
- Manual override capability with reason tracking
- Device status tracking (online, offline, disabled)

**Indexes:**
- Member check-in history
- Branch-level attendance analytics
- Tenant-wide attendance status

### 2026_07_28_0005: Classes & Workouts

**Tables Created:**

**Classes & Training:**
- `class_types` - Yoga, Zumba, CrossFit, etc.
- `class_schedules` - Class sessions with capacity
- `class_bookings` - Member bookings with waitlist

**Workouts:**
- `exercises` - Exercise library (tenant-specific or global)
- `workout_templates` - Reusable workout plans
- `workout_template_exercises` - Exercises in templates
- `member_workout_plans` - Plans assigned to members
- `workout_sessions` - Individual workout sessions
- `workout_session_exercises` - Exercises logged in sessions

**Progress Tracking:**
- `body_measurements` - Weight, BMI, body fat %, etc.
- `progress_photos` - Before/after photos

**Personal Training:**
- `personal_training_sessions` - PT booking and tracking

**Key Features:**
- Multi-week workout templates
- Exercise library with video URLs
- Detailed session logging (sets, reps, weight)
- Body measurement history for progress charts
- PT session scheduling

### 2026_07_28_0006: CRM & Integrations

**Tables Created:**

**Lead Management:**
- `leads` - Prospects (NEW → TRIAL → NEGOTIATION → WON/LOST)
- `lead_follow_ups` - Calls, WhatsApp, SMS, email
- `trial_passes` - Free trial passes with visit limits

**Communications:**
- `message_templates` - SMS, Email, WhatsApp templates
- `notifications` - Queued notifications with retry logic

**Support & Audit:**
- `support_tickets` - Help desk tickets
- `audit_logs` - Entity change tracking (insert, update, delete)

**Integrations:**
- `integration_configs` - Payment gateways, SMS, email configs (encrypted)
- `webhook_events` - Incoming webhooks from payment providers

**Key Features:**
- Lead pipeline tracking
- Multi-channel messaging
- Support ticket prioritization
- Full audit trail for compliance
- Webhook signature validation
- Integration credential encryption

## Database Schema Diagram (Simplified)

```
┌─────────────────────────────────────────────────────────┐
│                      CORE / TENANCY                      │
├─────────────────────────────────────────────────────────┤
│ tenants ◄──── branches ◄──── users (with roles)         │
└─────────────────────────────────────────────────────────┘
                           ▲
         ┌─────────────────┼─────────────────┐
         │                 │                 │
    ┌────────────┐  ┌──────────────┐  ┌────────────┐
    │   MEMBERS  │  │ TRAINERS/STAFF│ │   LEADS    │
    └────────────┘  └──────────────┘  └────────────┘
         │                 │                 │
    ┌─────────────────────────────────────────────────┐
    │        MEMBERSHIPS & SUBSCRIPTIONS              │
    │ (plans, subscriptions, invoices, payments)      │
    └─────────────────────────────────────────────────┘
         │                 │                 │
    ┌─────────────────────────────────────────────────┐
    │         OPERATIONS & ENGAGEMENT                 │
    │ (attendance, classes, workouts, PT sessions)    │
    └─────────────────────────────────────────────────┘
         │                 │                 │
    ┌─────────────────────────────────────────────────┐
    │      SUPPORT & INTEGRATIONS                     │
    │ (notifications, tickets, webhooks, audit)       │
    └─────────────────────────────────────────────────┘
```

## Key Design Patterns

### 1. Soft Deletes (Prepared for future use)
Some tables have `deleted_at` columns but are not enforced in migrations yet.

### 2. Audit Trail
- `audit_logs` table tracks ALL changes to sensitive entities
- Stores old and new values as JSON
- Includes user, IP, user agent, and request ID

### 3. Versioning
- `member_subscriptions.version` supports optimistic locking
- Prevents concurrent modification conflicts

### 4. Status Enums (as VARCHAR)
- Uses VARCHAR instead of MySQL ENUM for flexibility
- Allows adding new statuses without migrations
- Examples: 'ACTIVE', 'FROZEN', 'EXPIRED', 'CANCELLED'

### 5. Multi-Tenant Isolation
- Every table (except global tables) has `tenant_id`
- Foreign key constraints enforce tenant boundaries
- Indexes on tenant_id for fast filtering

### 6. Unique Constraints
- Codes (member_code, trainer_code, etc.) are unique per tenant
- Prevents duplicates within tenant while allowing same code across tenants

## Data Types

### IDs
- All IDs are `VARCHAR(36)` to support UUIDs
- UUIDs are generated at application layer

### Timestamps
- `created_at`, `updated_at`, `deleted_at` all `DATETIME`
- Use application timezone (configured in settings)
- SQL Server automatically handles conversion

### Amounts
- Financial amounts use `NUMERIC(12, 2)` (2 decimal places)
- Examples: base_price, discount_amount, tax_amount

### Measurements
- Body measurements use `NUMERIC(6, 2)` for kg/cm
- Weight: 0-999.99 kg
- Height: 0-999.99 cm

### Status Fields
- Always `VARCHAR` with meaningful values
- Examples: 'ACTIVE', 'INACTIVE', 'PENDING', 'COMPLETED'

## Indexing Strategy

### Performance Indexes
- Foreign key columns (for joins)
- Tenant + status (for filtering)
- Tenant + date range (for reporting)
- Member ID + date (for member history)

### Search Indexes (to add in future)
- Phone numbers (for member lookup)
- Email addresses (for user lookup)
- QR codes (for attendance)

## Future Considerations

### Phase 2 (Not yet implemented)
- Audit log soft deletes enforcement
- Subscription pause/resume (in addition to freeze)
- Multi-location family plans
- Corporate bulk memberships
- Equipment booking system
- Locker assignment
- Supplement/product inventory
- Point of sale (POS) integration
- Accounting software integrations (Tally, QuickBooks)

### Migration Strategy
- Always create new migrations for schema changes
- Never modify existing migrations
- Use `alembic revision --autogenerate` when possible
- Test upgrades AND downgrades locally
- Keep migration descriptions detailed in docstrings

## Troubleshooting

### Migration Failed to Apply

```bash
# Check current state
alembic current

# Check failed migrations
alembic history --verbose

# Try rolling back
alembic downgrade -1

# Check for syntax errors in migration file
alembic upgrade --sql 2026_07_28_0005
```

### Foreign Key Constraint Errors

- Ensure parent tables are created first
- Check revision order
- Verify FK references correct table and column

### Duplicate Key Errors

- Check unique constraints in migration
- May need data cleanup before migration
- Use alembic operations to clean up data in migration

## SQL Server Specific Notes

1. **Identity columns**: Use VARCHAR(36) for UUIDs, not auto-increment
2. **JSON columns**: Supported natively in SQL Server 2016+
3. **Datetime vs DateTime2**: Using DateTime (compatible with Python datetime)
4. **String length**: VARCHAR(MAX) avoided in favor of explicit lengths
5. **Case sensitivity**: All table/column names are case-insensitive

## Related Documentation

- See `DATABASE_BACKUP.md` for backup/restore procedures
- See `DOCKER_SETUP.md` for environment configuration
- See `CLAUDE.md` for API design patterns
