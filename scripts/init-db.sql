-- Gym Manager - Initial Dummy Data
-- This script populates the database with sample data for testing

-- Insert Tenants
INSERT INTO tenants (id, name, slug, billing_email, status, created_at, updated_at)
VALUES
('tenant-001', 'FitZone Gym', 'fitzone-gym', 'billing@fitzone.com', 'active', GETDATE(), GETDATE()),
('tenant-002', 'PowerLift Studios', 'powerlift-studios', 'billing@powerlift.com', 'active', GETDATE(), GETDATE()),
('tenant-003', 'Yoga Haven', 'yoga-haven', 'billing@yogahaven.com', 'active', GETDATE(), GETDATE());

-- Insert Branches
INSERT INTO branches (id, tenant_id, name, address, created_at, updated_at)
VALUES
('branch-001', 'tenant-001', 'FitZone Downtown', '123 Main St, Downtown', GETDATE(), GETDATE()),
('branch-002', 'tenant-001', 'FitZone Uptown', '456 Park Ave, Uptown', GETDATE(), GETDATE()),
('branch-003', 'tenant-002', 'PowerLift Central', '789 Gym Blvd, Central', GETDATE(), GETDATE()),
('branch-004', 'tenant-003', 'Yoga Haven Studio', '321 Peace Ln, Peaceful', GETDATE(), GETDATE());

-- Insert Roles
INSERT INTO roles (id, name)
VALUES
(1, 'admin'),
(2, 'manager'),
(3, 'trainer'),
(4, 'staff'),
(5, 'member');

-- Insert Users
INSERT INTO users (id, tenant_id, email, full_name, password_hash, is_active, created_at, updated_at, last_login_at)
VALUES
('user-001', 'tenant-001', 'admin@fitzone.com', 'Admin User', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5YmMxSUqqqJlm', 1, GETDATE(), GETDATE(), NULL),
('user-002', 'tenant-001', 'manager@fitzone.com', 'Manager User', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5YmMxSUqqqJlm', 1, GETDATE(), GETDATE(), NULL),
('user-003', 'tenant-001', 'trainer@fitzone.com', 'John Trainer', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5YmMxSUqqqJlm', 1, GETDATE(), GETDATE(), NULL),
('user-004', 'tenant-001', 'staff@fitzone.com', 'Staff Member', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5YmMxSUqqqJlm', 1, GETDATE(), GETDATE(), NULL),
('user-005', 'tenant-002', 'admin@powerlift.com', 'Admin PowerLift', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5YmMxSUqqqJlm', 1, GETDATE(), GETDATE(), NULL),
('user-006', 'tenant-003', 'admin@yogahaven.com', 'Admin Yoga', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5YmMxSUqqqJlm', 1, GETDATE(), GETDATE(), NULL);

-- Assign Roles to Users
INSERT INTO user_roles (user_id, role_id)
VALUES
('user-001', 1),  -- admin@fitzone.com -> admin
('user-002', 2),  -- manager@fitzone.com -> manager
('user-003', 3),  -- trainer@fitzone.com -> trainer
('user-004', 4),  -- staff@fitzone.com -> staff
('user-005', 1),  -- admin@powerlift.com -> admin
('user-006', 1);  -- admin@yogahaven.com -> admin

-- Members Table (Gym members - need to create if not exists)
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'members')
BEGIN
    CREATE TABLE members (
        id NVARCHAR(36) PRIMARY KEY,
        tenant_id NVARCHAR(36) NOT NULL,
        branch_id NVARCHAR(36) NOT NULL,
        first_name NVARCHAR(100) NOT NULL,
        last_name NVARCHAR(100) NOT NULL,
        email NVARCHAR(255) UNIQUE,
        phone NVARCHAR(20),
        date_of_birth DATE,
        gender NVARCHAR(10),
        address NVARCHAR(255),
        city NVARCHAR(100),
        state NVARCHAR(100),
        postal_code NVARCHAR(10),
        emergency_contact_name NVARCHAR(100),
        emergency_contact_phone NVARCHAR(20),
        join_date DATE NOT NULL,
        status NVARCHAR(20) DEFAULT 'active',
        created_at DATETIME NOT NULL,
        updated_at DATETIME NOT NULL,
        FOREIGN KEY (tenant_id) REFERENCES tenants(id),
        FOREIGN KEY (branch_id) REFERENCES branches(id)
    );
    CREATE INDEX ix_members_tenant_id ON members(tenant_id);
    CREATE INDEX ix_members_branch_id ON members(branch_id);
    CREATE INDEX ix_members_email ON members(email);
    CREATE INDEX ix_members_status ON members(status);
END

-- Insert Members
INSERT INTO members (id, tenant_id, branch_id, first_name, last_name, email, phone, date_of_birth, gender, address, city, state, postal_code, emergency_contact_name, emergency_contact_phone, join_date, status, created_at, updated_at)
VALUES
('member-001', 'tenant-001', 'branch-001', 'John', 'Doe', 'john@example.com', '555-0101', '1990-01-15', 'M', '123 Oak St', 'Springfield', 'IL', '62701', 'Jane Doe', '555-0102', '2024-01-01', 'active', GETDATE(), GETDATE()),
('member-002', 'tenant-001', 'branch-001', 'Alice', 'Smith', 'alice@example.com', '555-0201', '1992-05-20', 'F', '456 Elm St', 'Springfield', 'IL', '62701', 'Bob Smith', '555-0202', '2024-01-15', 'active', GETDATE(), GETDATE()),
('member-003', 'tenant-001', 'branch-001', 'Bob', 'Johnson', 'bob@example.com', '555-0301', '1988-03-10', 'M', '789 Pine St', 'Springfield', 'IL', '62701', 'Carol Johnson', '555-0302', '2024-02-01', 'active', GETDATE(), GETDATE()),
('member-004', 'tenant-001', 'branch-002', 'Carol', 'Williams', 'carol@example.com', '555-0401', '1995-07-25', 'F', '321 Maple St', 'Springfield', 'IL', '62702', 'David Williams', '555-0402', '2024-02-10', 'active', GETDATE(), GETDATE()),
('member-005', 'tenant-001', 'branch-002', 'David', 'Brown', 'david@example.com', '555-0501', '1991-11-30', 'M', '654 Cedar St', 'Springfield', 'IL', '62702', 'Emma Brown', '555-0502', '2024-03-01', 'inactive', GETDATE(), GETDATE()),
('member-006', 'tenant-002', 'branch-003', 'Emma', 'Davis', 'emma@example.com', '555-0601', '1993-09-12', 'F', '987 Birch St', 'Chicago', 'IL', '60601', 'Frank Davis', '555-0602', '2024-01-20', 'active', GETDATE(), GETDATE()),
('member-007', 'tenant-002', 'branch-003', 'Frank', 'Miller', 'frank@example.com', '555-0701', '1989-04-08', 'M', '147 Oak Ave', 'Chicago', 'IL', '60601', 'Grace Miller', '555-0702', '2024-02-15', 'active', GETDATE(), GETDATE()),
('member-008', 'tenant-003', 'branch-004', 'Grace', 'Wilson', 'grace@example.com', '555-0801', '1994-12-05', 'F', '258 Elm Ave', 'Madison', 'WI', '53701', 'Henry Wilson', '555-0802', '2024-03-01', 'active', GETDATE(), GETDATE());

-- Membership Plans Table
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'membership_plans')
BEGIN
    CREATE TABLE membership_plans (
        id NVARCHAR(36) PRIMARY KEY,
        tenant_id NVARCHAR(36) NOT NULL,
        name NVARCHAR(100) NOT NULL,
        description NVARCHAR(500),
        price DECIMAL(10, 2) NOT NULL,
        duration_days INT NOT NULL,
        features NVARCHAR(MAX),
        is_active BIT DEFAULT 1,
        created_at DATETIME NOT NULL,
        updated_at DATETIME NOT NULL,
        FOREIGN KEY (tenant_id) REFERENCES tenants(id)
    );
    CREATE INDEX ix_membership_plans_tenant_id ON membership_plans(tenant_id);
END

-- Insert Membership Plans
INSERT INTO membership_plans (id, tenant_id, name, description, price, duration_days, features, is_active, created_at, updated_at)
VALUES
('plan-001', 'tenant-001', 'Basic Monthly', 'Access to gym equipment during business hours', 49.99, 30, 'Gym access,Locker,Wi-Fi', 1, GETDATE(), GETDATE()),
('plan-002', 'tenant-001', 'Premium Monthly', 'Full access including all classes and pool', 79.99, 30, 'Gym access,Classes,Pool,Personal training (1/month),Locker,Wi-Fi', 1, GETDATE(), GETDATE()),
('plan-003', 'tenant-001', 'Annual', 'Best value annual membership', 699.99, 365, 'Gym access,Classes,Pool,Personal training (2/month),Locker,Wi-Fi,Guest passes', 1, GETDATE(), GETDATE()),
('plan-004', 'tenant-002', 'PowerLift Pro', 'Heavy lifting and strength training focus', 89.99, 30, 'Gym access,Strength training,Spotters,Equipment reservation', 1, GETDATE(), GETDATE()),
('plan-005', 'tenant-003', 'Yoga Unlimited', 'Unlimited yoga classes', 59.99, 30, 'All yoga classes,Meditation,Workshops', 1, GETDATE(), GETDATE());

-- Memberships Table
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'memberships')
BEGIN
    CREATE TABLE memberships (
        id NVARCHAR(36) PRIMARY KEY,
        member_id NVARCHAR(36) NOT NULL,
        plan_id NVARCHAR(36) NOT NULL,
        start_date DATE NOT NULL,
        end_date DATE NOT NULL,
        status NVARCHAR(20) DEFAULT 'active',
        is_frozen BIT DEFAULT 0,
        frozen_start_date DATE,
        frozen_end_date DATE,
        created_at DATETIME NOT NULL,
        updated_at DATETIME NOT NULL,
        FOREIGN KEY (member_id) REFERENCES members(id),
        FOREIGN KEY (plan_id) REFERENCES membership_plans(id)
    );
    CREATE INDEX ix_memberships_member_id ON memberships(member_id);
    CREATE INDEX ix_memberships_plan_id ON memberships(plan_id);
    CREATE INDEX ix_memberships_status ON memberships(status);
END

-- Insert Memberships
INSERT INTO memberships (id, member_id, plan_id, start_date, end_date, status, is_frozen, frozen_start_date, frozen_end_date, created_at, updated_at)
VALUES
('mem-001', 'member-001', 'plan-001', '2024-01-01', '2024-01-31', 'active', 0, NULL, NULL, GETDATE(), GETDATE()),
('mem-002', 'member-002', 'plan-002', '2024-01-15', '2024-02-14', 'active', 0, NULL, NULL, GETDATE(), GETDATE()),
('mem-003', 'member-003', 'plan-003', '2024-02-01', '2025-01-31', 'active', 0, NULL, NULL, GETDATE(), GETDATE()),
('mem-004', 'member-004', 'plan-001', '2024-02-10', '2024-03-10', 'active', 0, NULL, NULL, GETDATE(), GETDATE()),
('mem-005', 'member-005', 'plan-002', '2024-01-01', '2024-01-31', 'expired', 0, NULL, NULL, GETDATE(), GETDATE()),
('mem-006', 'member-006', 'plan-004', '2024-01-20', '2024-02-19', 'active', 0, NULL, NULL, GETDATE(), GETDATE()),
('mem-007', 'member-007', 'plan-004', '2024-02-15', '2024-03-15', 'active', 1, '2024-03-01', '2024-03-15', GETDATE(), GETDATE()),
('mem-008', 'member-008', 'plan-005', '2024-03-01', '2024-03-31', 'active', 0, NULL, NULL, GETDATE(), GETDATE());

-- Payments Table
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'payments')
BEGIN
    CREATE TABLE payments (
        id NVARCHAR(36) PRIMARY KEY,
        member_id NVARCHAR(36) NOT NULL,
        membership_id NVARCHAR(36),
        amount DECIMAL(10, 2) NOT NULL,
        payment_method NVARCHAR(50) NOT NULL,
        payment_date DATE NOT NULL,
        transaction_id NVARCHAR(100),
        status NVARCHAR(20) DEFAULT 'completed',
        notes NVARCHAR(500),
        created_at DATETIME NOT NULL,
        updated_at DATETIME NOT NULL,
        FOREIGN KEY (member_id) REFERENCES members(id),
        FOREIGN KEY (membership_id) REFERENCES memberships(id)
    );
    CREATE INDEX ix_payments_member_id ON payments(member_id);
    CREATE INDEX ix_payments_payment_date ON payments(payment_date);
    CREATE INDEX ix_payments_status ON payments(status);
END

-- Insert Payments
INSERT INTO payments (id, member_id, membership_id, amount, payment_method, payment_date, transaction_id, status, notes, created_at, updated_at)
VALUES
('pay-001', 'member-001', 'mem-001', 49.99, 'credit_card', '2024-01-01', 'TXN001', 'completed', 'Monthly membership', GETDATE(), GETDATE()),
('pay-002', 'member-002', 'mem-002', 79.99, 'credit_card', '2024-01-15', 'TXN002', 'completed', 'Premium monthly', GETDATE(), GETDATE()),
('pay-003', 'member-003', 'mem-003', 699.99, 'bank_transfer', '2024-02-01', 'TXN003', 'completed', 'Annual membership', GETDATE(), GETDATE()),
('pay-004', 'member-004', 'mem-004', 49.99, 'credit_card', '2024-02-10', 'TXN004', 'completed', 'Basic monthly', GETDATE(), GETDATE()),
('pay-005', 'member-005', 'mem-005', 79.99, 'credit_card', '2024-01-01', 'TXN005', 'completed', 'Premium monthly', GETDATE(), GETDATE()),
('pay-006', 'member-006', 'mem-006', 89.99, 'credit_card', '2024-01-20', 'TXN006', 'completed', 'PowerLift Pro', GETDATE(), GETDATE()),
('pay-007', 'member-007', 'mem-007', 89.99, 'credit_card', '2024-02-15', 'TXN007', 'completed', 'PowerLift Pro', GETDATE(), GETDATE()),
('pay-008', 'member-008', 'mem-008', 59.99, 'credit_card', '2024-03-01', 'TXN008', 'completed', 'Yoga Unlimited', GETDATE(), GETDATE());

-- Attendance Table
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'attendance')
BEGIN
    CREATE TABLE attendance (
        id NVARCHAR(36) PRIMARY KEY,
        member_id NVARCHAR(36) NOT NULL,
        check_in_time DATETIME NOT NULL,
        check_out_time DATETIME,
        duration_minutes INT,
        notes NVARCHAR(500),
        created_at DATETIME NOT NULL,
        FOREIGN KEY (member_id) REFERENCES members(id)
    );
    CREATE INDEX ix_attendance_member_id ON attendance(member_id);
    CREATE INDEX ix_attendance_check_in_time ON attendance(check_in_time);
END

-- Insert Attendance Records
INSERT INTO attendance (id, member_id, check_in_time, check_out_time, duration_minutes, notes, created_at)
VALUES
('att-001', 'member-001', DATEADD(day, -3, GETDATE()) + CAST('06:00:00' AS TIME), DATEADD(day, -3, GETDATE()) + CAST('07:30:00' AS TIME), 90, 'Morning workout', GETDATE()),
('att-002', 'member-001', DATEADD(day, -2, GETDATE()) + CAST('06:00:00' AS TIME), DATEADD(day, -2, GETDATE()) + CAST('07:00:00' AS TIME), 60, 'Morning run', GETDATE()),
('att-003', 'member-001', DATEADD(day, -1, GETDATE()) + CAST('18:00:00' AS TIME), DATEADD(day, -1, GETDATE()) + CAST('19:30:00' AS TIME), 90, 'Evening class', GETDATE()),
('att-004', 'member-002', DATEADD(day, -3, GETDATE()) + CAST('07:00:00' AS TIME), DATEADD(day, -3, GETDATE()) + CAST('08:00:00' AS TIME), 60, 'Morning session', GETDATE()),
('att-005', 'member-002', DATEADD(day, -1, GETDATE()) + CAST('17:30:00' AS TIME), DATEADD(day, -1, GETDATE()) + CAST('19:00:00' AS TIME), 90, 'Evening training', GETDATE()),
('att-006', 'member-003', DATEADD(day, -4, GETDATE()) + CAST('05:30:00' AS TIME), DATEADD(day, -4, GETDATE()) + CAST('07:00:00' AS TIME), 90, 'Strength training', GETDATE()),
('att-007', 'member-004', DATEADD(day, -2, GETDATE()) + CAST('18:00:00' AS TIME), DATEADD(day, -2, GETDATE()) + CAST('19:15:00' AS TIME), 75, 'Yoga class', GETDATE()),
('att-008', 'member-006', DATEADD(day, -3, GETDATE()) + CAST('06:30:00' AS TIME), DATEADD(day, -3, GETDATE()) + CAST('08:00:00' AS TIME), 90, 'Heavy lifting', GETDATE());

PRINT 'Dummy data initialization completed successfully!';
