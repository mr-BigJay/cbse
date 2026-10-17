# HTTP API (v1)

OpenAPI is served at `/docs` on the backend.

## Auth

- `POST /api/v1/auth/login` — email, password, optional `totp_code`
- `POST /api/v1/auth/refresh`
- `GET /api/v1/auth/me`
- `POST /api/v1/auth/mfa/setup` · `POST /api/v1/auth/mfa/enable`

## Enrollment

- `POST /api/v1/enrollment/codes` (admin)
- `POST /api/v1/enrollment/register` (device, no auth)

## Devices

- `GET /api/v1/devices` · `GET /api/v1/devices/{id}`
- `POST /api/v1/devices/{id}/approve` · `POST /api/v1/devices/{id}/revoke`
- Device auth: `POST /api/v1/devices/me/heartbeat`, `/me/location`, `/me/rotate-token`
- `GET /api/v1/devices/{id}/locations`
- `PUT /api/v1/devices/{id}/sms-senders`

## Commands

- `POST /api/v1/commands` (admin, optional `Idempotency-Key`)
- `GET /api/v1/commands?device_id=`
- Device: `GET /api/v1/commands/pending`, `POST .../ack`, `POST .../result`

## Audit & settings

- `GET /api/v1/audit`
- `GET|PUT /api/v1/settings`

Device header: `Authorization: Device <uuid>:<token>`
