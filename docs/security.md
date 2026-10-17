# Security

- TLS termination at Caddy; HSTS recommended in production.
- Passwords: bcrypt. JWT access 15m, refresh 7d, rotation on use.
- TOTP: RFC 6238, optional per administrator.
- Rate limiting on auth and enrollment endpoints (slowapi).
- Commands: max TTL 15 minutes, server-side authorization per device status and capabilities.
- No sensitive payloads in FCM notification bodies.
- SMS: HMAC + expiry + nonce replay table; no destructive SMS commands in v1.
- Secrets: `.env` not committed; device tokens stored hashed (SHA-256).
- Logging: redact tokens, SMS secrets, precise location in debug logs.
- Location retention configurable; default purge job in backend startup hook (daily).

Unauthorized enrollment attempts increment audit log and rate limit counter.
