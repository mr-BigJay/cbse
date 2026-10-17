# Pre-release validation — PR #1

Validation run on branch `cursor/android-remote-device-manager-af9a` (2026-10-17).

## Android

| Check | Result |
|-------|--------|
| `./gradlew assembleDebug` | **PASS** — `android/app/build/outputs/apk/debug/app-debug.apk` (~11 MB) |
| `./gradlew test` | **PASS** — `SmsHmacTest`, `CommandVerifierTest` |
| Manifest / FGS | **FIXED** — find-alarm uses `foregroundServiceType=mediaPlayback` (not location); SMS receiver `exported` + `BROADCAST_SMS` permission |
| WorkManager | 15-minute periodic heartbeat (Android minimum interval) |

**Not tested in this environment:** physical device or emulator install, FCM wake, live SMS over radio.

## Backend

| Check | Result |
|-------|--------|
| Unit tests | **PASS** (4) — security, SMS HMAC helpers |
| Integration tests (PostgreSQL) | **PASS** (7) — auth, enrollment, device auth, command lifecycle, inactive device rejection |
| Live HTTP E2E (`scripts/e2e_backend.sh`) | **PASS** — login → enrollment → approve → STATUS command pending → ack → completed |

## Frontend

| Check | Result |
|-------|--------|
| `npm run build` | **PASS** |

## Docker Compose

| Check | Result |
|-------|--------|
| Full stack on VPS | **NOT RUN** — Docker unavailable in validation VM; compose files reviewed statically |

## CI

GitHub Actions workflow `.github/workflows/ci.yml`: backend (unit + integration + Postgres service), frontend build, Android `assembleDebug` + `test`.

## Security fixes applied during review

- Per-device `command_verification_key` at enrollment; agent verifies signature + expiry before ack
- Rate limits: login `10/minute`, enrollment register `30/minute`
- `TESTING=1` disables location purge background task; asyncpg `statement_cache_size=0` for schema resets in tests
