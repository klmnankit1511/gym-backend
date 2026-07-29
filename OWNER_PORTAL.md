# Configurable Multi-Tenant Owner Portal

The owner portal is tenant-scoped: the authenticated user's `tenant_id` is
always taken from the JWT-backed user record. Client requests cannot select a
different tenant.

## Feature configuration

Owners can enable or disable optional modules independently for each gym:

```http
GET /api/v1/settings/features
PUT /api/v1/settings/features
```

Disabled modules are removed from the frontend navigation and return HTTP 403
from protected backend routes. Feature configuration is stored in
`tenant_features`; a missing override uses the feature catalog default.

## Dashboard

`GET /api/v1/dashboard/summary` supports:

- `branch_id`
- `date_from` and `date_to`
- `trainer_id`
- `membership_type`
- `payment_status`

It returns active members, 7/15/30-day expiries, attendance, new members,
revenue, collections, failed/overdue items, leads and conversion, trainer
utilisation, popular plan, retention, churn, and previous-period comparisons.

## Members

The member API supports tenant-scoped listing, search, filtering, creation,
editing, CSV import/export, branch transfer, freezing, blocking, deactivation,
measurements, documents, waivers/consents, progress photographs, membership
history, payment and attendance history, a timeline, and digital-card payloads.

Medical notes, internal notes and block reasons are only returned to
`SUPER_ADMIN`, `OWNER`, and `MANAGER`.

CSV imports require `first_name` and `phone`; `member_code`, `last_name`,
`email`, `joining_date`, and `status` are optional.

## Configurable package engine

Membership plans store common limits as indexed columns and client-specific
policy in `rules_json`. This allows each gym to configure cancellation,
renewal, access windows, eligibility, family/corporate rules, or future policy
without adding hardcoded plan types.

Membership lifecycle operations include assignment, renewal, freeze/unfreeze,
extension, cancellation, and plan changes.

## Database

Apply the new migration:

```bash
alembic upgrade head
```

The expected head is `2026_07_28_0007`.
