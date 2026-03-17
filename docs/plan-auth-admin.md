# Auth & Admin Implementation Plan

## Phase A — Auth Foundation
- [x] Add `users` table + migration
- [x] Add password hash + JWT service
- [x] Add register/login/me endpoints
- [x] Add auth API tests

## Phase B — Authorization Foundation
- [x] Add `require_admin()` dependency
- [x] Restrict runtime config updates to admins
- [x] Add admin permission tests

## Phase C — Admin Data Layer
- [x] Add `symbol_configs` table
- [x] Add `audit_logs` table
- [x] Add symbol config list/create/update APIs
- [x] Add symbol admin API tests

## Phase D — Admin User Management
- [ ] Add admin list users API
- [ ] Add admin update user role/status API
- [ ] Add audit logs for user management changes
- [ ] Add tests for admin user management

## Phase E — Frontend Auth & Admin Entry
- [ ] Add login page
- [ ] Add register page
- [ ] Add auth state storage
- [ ] Add header/admin entry

## Phase F — Frontend Admin Views
- [ ] Add symbol management page
- [ ] Add user management page
- [ ] Connect admin UI to backend APIs
- [ ] Keep mobile-first responsive layout

## Verification Rule
For each phase chunk:
1. Update docs/spec or plan if scope changes
2. Implement in small verified steps
3. Run relevant tests/build
4. Commit + push
5. Deploy dev server
6. Append worklog entry
