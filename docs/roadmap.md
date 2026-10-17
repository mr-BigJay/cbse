# Implementation Roadmap

## Phase 0 — Design (complete in docs/)

Architecture, feature matrix, schema, protocols, permissions.

## Phase 1 — MVP (this release)

- [x] FastAPI backend: auth (JWT + TOTP hooks), enrollment, devices, commands, location, audit, settings
- [x] PostgreSQL + Alembic initial migration
- [x] Next.js dashboard: Persian RTL, dark theme, devices, commands, map stub with real coordinates
- [x] Android: enrollment, heartbeat, command poll, LOCATE/ALARM/LOCK/STATUS, SMS receiver
- [x] Docker Compose + Caddy + setup script
- [x] Backend unit/integration tests

## Phase 2 — Hardening

- WebAuthn MFA, SSE command stream, FCM server integration in backend
- Managed Device Owner DPC provisioning module
- Geo-fencing, retention cron, Prometheus metrics

## Phase 3 — Enterprise

- Multi-tenant orgs, RBAC roles beyond administrator
- Compliance export, signed audit chain
