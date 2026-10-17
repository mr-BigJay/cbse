# Installation (Ubuntu 24.04 VPS)

## Prerequisites

- Docker Engine 24+ and Docker Compose v2
- Domain pointing to VPS (for TLS via Caddy)
- Optional: Firebase project for FCM (google-services.json in Android)

## Quick start

```bash
cd deploy
cp .env.example .env
# Edit .env: POSTGRES_PASSWORD, JWT_SECRET, ADMIN_EMAIL, ADMIN_PASSWORD, DOMAIN

./setup.sh
docker compose up -d
```

Open `https://YOUR_DOMAIN` and sign in with admin credentials from `.env`.

## First device

1. Dashboard → Enrollment → Create code.
2. Install APK from `android/` build output (see `android/README.md`).
3. Enroll with server URL and code.
4. Approve device in dashboard.

## Managed Device Owner

Requires Android Enterprise managed provisioning (QR). Generate QR payload from Android Management API or use afw#setup with your DPC component `com.ardm.agent/.AdminReceiver` — see Android README. Factory reset is typically required.

## Backup

```bash
docker compose exec postgres pg_dump -U ardm ardm > backup.sql
```

## Restore

```bash
cat backup.sql | docker compose exec -T postgres psql -U ardm ardm
```

PostgreSQL is not published to the host by default; only the internal Docker network exposes port 5432.
