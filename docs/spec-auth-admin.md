# Auth & Admin Spec

## Scope

This spec defines the user/auth/admin management layer for AlphaPilot.
It also sits inside the broader product direction now adopted in PRD: AI Trader / Program Trader separation, multi-agent responsibilities, attribution analytics, factor intelligence, and web + messaging collaboration.

### Included
- User registration
- User login
- JWT-based authentication
- Roles: `user`, `admin`
- User status: `active`, `disabled`
- Admin-only runtime config writes
- Admin symbol configuration management
- Audit logs for admin actions
- Admin user management APIs and frontend entry points

### Excluded for now
- Password reset
- 2FA
- Invite-only onboarding
- Multi-tenant organization model

## Security Constraints

1. Passwords are stored only as hashes.
2. Sensitive runtime config stays encrypted in DB.
3. Admins may overwrite secrets but may not read plaintext API keys/secrets.
4. Admin actions must create audit logs.
5. UI must not expose admin mutation controls to normal users.

## Backend Acceptance Criteria

### Authentication
- `POST /api/auth/register` creates a user with default role `user`
- `POST /api/auth/login` returns bearer token + user payload
- `GET /api/auth/me` returns current user when token is valid

### Authorization
- Admin-only endpoints reject anonymous/non-admin callers
- Runtime config update endpoint is admin-only

### Symbol Management
- Admin can list symbol configs
- Admin can create symbol configs
- Admin can update symbol configs
- Create/update actions write audit logs

### User Management
- Admin can list users
- Admin can update role/status of users
- User admin changes write audit logs

## Frontend Acceptance Criteria

### Auth UI
- Login page exists
- Register page exists
- Token is stored client-side for dev flow
- Header/dashboard shows login state

### Admin UI
- Admin-only entry point exists
- Admin can access symbol management UI
- Non-admin users do not see admin mutation entry points

## Mobile UX Constraints
- Auth pages must be mobile-first
- Admin pages must avoid wide tables on small screens
- Forms must stay usable with one-handed touch targets
