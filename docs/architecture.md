# Android Remote Device Manager — Architecture

## Overview

Self-hosted Android Remote Device Management (ARDM) for devices owned by the administrator or enrolled with explicit consent. The system comprises four runtime components and one optional push channel.

```
┌─────────────────┐     HTTPS/TLS      ┌──────────────────┐
│  Admin Browser  │◄──────────────────►│  Caddy (reverse  │
│  (Next.js UI)   │                    │  proxy + TLS)    │
└────────┬────────┘                    └────────┬─────────┘
         │                                      │
         │ /api/v1/*                            │ /api, /_next
         ▼                                      ▼
┌─────────────────┐                    ┌──────────────────┐
│  FastAPI        │◄──────SQL─────────►│  PostgreSQL      │
│  Backend        │                    │                  │
└────────┬────────┘                    └──────────────────┘
         │
         │ HTTPS (device token + mTLS-ready headers)
         ▼
┌─────────────────┐     FCM (wake only)  ┌──────────────────┐
│  Android Agent  │◄───────────────────│  Firebase Cloud  │
│  (Kotlin)       │                    │  Messaging       │
└────────┬────────┘                    └──────────────────┘
         │
         │ Optional SMS (HMAC-authenticated)
         ▼
    Authorized senders
```

## Monorepo layout

| Path | Role |
|------|------|
| `backend/` | REST API, auth, command queue, audit |
| `frontend/` | Persian RTL admin dashboard |
| `android/` | Companion agent app |
| `deploy/` | Docker Compose, Caddy, env templates |
| `docs/` | Architecture, security, API, permissions |

## Trust boundaries

1. **Administrators** authenticate via JWT (access + refresh), optional TOTP MFA. All mutating actions are authorized server-side and logged.
2. **Devices** enroll with a one-time code, receive a device ID and rotating device secret stored in Android Keystore. Commands are signed by the server; the agent verifies signature, expiry, and idempotency before execution.
3. **FCM** carries only a wake signal (`command_available`); payloads are fetched over HTTPS.
4. **SMS** uses HMAC-SHA256 over `command|nonce|expiry` with a per-device SMS secret established at enrollment (never logged server-side in plaintext after provisioning display).

## Management modes

- **Standard Mode**: User-installed app, runtime permissions, Device Admin where applicable for lock, WorkManager for periodic status.
- **Managed Device Mode**: Device Owner via Android Enterprise (QR / NFC / DPC). Extended policy via `DevicePolicyManager`; documented in `docs/permissions.md`.

## Command lifecycle

1. Admin UI → `POST /api/v1/commands` with `device_id`, `type`, optional params.
2. Backend validates capability matrix for device mode + reported capabilities → creates `Command` row (`pending`).
3. FCM wake (if configured) or agent poll `GET /api/v1/commands/pending`.
4. Agent `POST /api/v1/commands/{id}/ack` → `delivered`.
5. Agent executes with Android permission checks identical to SMS path.
6. Agent `POST /api/v1/commands/{id}/result` with structured outcome → `completed` | `failed` | `rejected`.
7. UI subscribes via polling or SSE for status updates.

## Data retention

Location points respect `settings.location_retention_days`. Audit logs retained per administrator configuration (default 90 days).

## Deployment topology (single VPS)

Docker Compose on Ubuntu 24.04: `caddy`, `frontend`, `backend`, `postgres` (internal network only). Backups: `pg_dump` documented in `docs/installation.md`.
