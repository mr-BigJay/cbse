# Database Schema (PostgreSQL)

## users

- `id` UUID PK
- `email` unique
- `password_hash`
- `role` enum (`administrator`)
- `totp_secret` nullable (encrypted)
- `totp_enabled` bool
- `created_at`, `updated_at`

## enrollment_codes

- `id` UUID PK
- `code` hashed
- `expires_at`
- `created_by` FK users
- `used_at`, `device_id` nullable

## devices

- `id` UUID PK
- `name`, `model`, `manufacturer`, `android_version`
- `mode` enum (`standard`, `managed`)
- `capabilities` JSONB
- `status` enum (`pending_approval`, `active`, `revoked`)
- `last_seen_at`, `battery_level`
- `fcm_token` nullable
- `public_key` PEM for command verification optional
- `device_secret_hash` for bearer token validation
- `sms_secret_hash` for HMAC verification
- `enrolled_at`, `approved_at`

## device_locations

- `id`, `device_id`, `latitude`, `longitude`, `accuracy`, `recorded_at`

## commands

- `id` UUID PK
- `device_id`, `type`, `payload` JSONB
- `status` enum (`pending`, `delivered`, `completed`, `failed`, `rejected`, `expired`)
- `idempotency_key` unique per device
- `expires_at`, `created_by`, `result` JSONB, timestamps

## audit_logs

- `id`, `user_id` nullable, `device_id` nullable, `action`, `details` JSONB, `ip`, `created_at`

## settings

- `key` PK, `value` JSONB (e.g. `location_retention_days`)

## refresh_tokens / device_tokens

- Hashed tokens, expiry, revocation

Alembic migrations live in `backend/alembic/versions/`.
