# Device Enrollment and Command Protocol

## Enrollment

1. Administrator creates enrollment code: `POST /api/v1/enrollment/codes` → `{ code, expires_at }` (plaintext code shown once).
2. User opens Android app → enters server URL + code + optional device label.
3. App generates Ed25519 key pair; private key in Android Keystore.
4. App `POST /api/v1/enrollment/register`:
   - `enrollment_code`, `public_key`, `device_info`, `mode`
5. Server validates code → creates `device` (`pending_approval`), returns:
   - `device_id`, `device_token` (long-lived, rotatable), `sms_secret` (shown once for SMS HMAC setup), `command_verification_key` (per-device HMAC key for verifying signed commands)
6. Administrator approves: `POST /api/v1/devices/{id}/approve`
7. App polls or receives push; begins heartbeat and command poll.

## Device authentication

`Authorization: Device <device_id>:<token>`

Token rotated via `POST /api/v1/devices/me/rotate-token` with current valid token.

## Command envelope (HTTPS)

Server creates command with:

```json
{
  "command_id": "uuid",
  "type": "LOCATE|ALARM|LOCK|STATUS|...",
  "payload": {},
  "expires_at": "ISO8601",
  "signature": "HMAC-SHA256(server_command_key, canonical_json)"
}
```

Agent verifies expiry, device_id binding, and signature before execution.

## SMS command format

```
ARDM v1:<COMMAND>:<exp_unix>:<nonce>:<hmac_hex>
```

HMAC key = per-device SMS secret. Agent rejects expired or reused `nonce` (stored in encrypted prefs, bounded set).

## Idempotency

Admin/API sends `Idempotency-Key` header; duplicate within 24h returns same command record.

## FCM wake payload (non-sensitive)

```json
{ "t": "cmd", "d": "<device_id_prefix>" }
```

Full command fetched from API only.
