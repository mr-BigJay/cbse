# Android Remote Device Manager (ARDM)

Self-hosted remote device management for **Android devices you own or that were enrolled with explicit consent**. Monorepo with FastAPI backend, Persian RTL Next.js admin panel, Kotlin Android agent, and Docker Compose deployment.

## Structure

| Directory | Description |
|-----------|-------------|
| [backend/](backend/) | FastAPI + PostgreSQL API |
| [frontend/](frontend/) | Next.js admin dashboard (fa-IR, RTL, dark) |
| [android/](android/) | Android companion app |
| [deploy/](deploy/) | Caddy + Compose stack |
| [docs/](docs/) | Architecture, security, API, installation |

## Quick start (development)

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL=postgresql+asyncpg://ardm:ardm@localhost:5432/ardm
alembic upgrade head
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
```

### Production (VPS)

See [docs/installation.md](docs/installation.md) and [deploy/](deploy/).

## MVP capabilities

- Admin login (MFA-ready TOTP)
- Enrollment codes and device approval
- Device status, battery, online/offline
- Signed command queue (STATUS, LOCATE, ALARM, LOCK, APP_LIST, SYNC_STATUS)
- Real completion status from the agent (no fake success)
- Location retention settings
- SMS fallback (HMAC + expiry + nonce)
- Audit logging

## Tests

```bash
cd backend && pytest
cd frontend && npm run build
cd android && ./gradlew test
```

## License

Use responsibly and only on devices you are authorized to manage.
