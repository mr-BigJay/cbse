#!/usr/bin/env bash
# End-to-end HTTP validation against a live uvicorn process + PostgreSQL.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export DATABASE_URL="${DATABASE_URL:-postgresql+asyncpg://ardm:ardmtest@127.0.0.1:5432/ardm_test}"
export JWT_SECRET="${JWT_SECRET:-e2e-jwt-secret-minimum-32-characters-long}"
export COMMAND_HMAC_SECRET="${COMMAND_HMAC_SECRET:-e2e-command-hmac-secret-key}"
export ADMIN_EMAIL="${ADMIN_EMAIL:-e2e@example.com}"
export ADMIN_PASSWORD="${ADMIN_PASSWORD:-e2e-admin-pass}"
export TESTING=1

cd "$ROOT/backend"
python3 - <<'PY'
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from app.db.base import Base
from app.models import AuditLog, Command, Device, DeviceLocation, EnrollmentCode, RefreshToken, User  # noqa: F401
import os
async def main():
    engine = create_async_engine(os.environ["DATABASE_URL"])
    async with engine.begin() as conn:
        await conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
asyncio.run(main())
PY

. .venv/bin/activate 2>/dev/null || python3 -m venv .venv && . .venv/bin/activate && pip install -q -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8765 &
PID=$!
trap "kill $PID" EXIT
sleep 2

BASE=http://127.0.0.1:8765
TOKEN=$(curl -sf -X POST "$BASE/api/v1/auth/login" -H 'Content-Type: application/json' \
  -d "{\"email\":\"$ADMIN_EMAIL\",\"password\":\"$ADMIN_PASSWORD\"}" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
AUTH="Authorization: Bearer $TOKEN"

CODE=$(curl -sf -X POST "$BASE/api/v1/enrollment/codes" -H "$AUTH" -H 'Content-Type: application/json' -d '{}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['code'])")

REG=$(curl -sf -X POST "$BASE/api/v1/enrollment/register" -H 'Content-Type: application/json' \
  -d "{\"enrollment_code\":\"$CODE\",\"name\":\"E2E Device\"}")
DEVICE_ID=$(echo "$REG" | python3 -c "import sys,json; print(json.load(sys.stdin)['device_id'])")
DEVICE_TOKEN=$(echo "$REG" | python3 -c "import sys,json; print(json.load(sys.stdin)['device_token'])")
CMD_KEY=$(echo "$REG" | python3 -c "import sys,json; print(json.load(sys.stdin)['command_verification_key'])")
DEV_AUTH="Authorization: Device ${DEVICE_ID}:${DEVICE_TOKEN}"

curl -sf -X POST "$BASE/api/v1/devices/$DEVICE_ID/approve" -H "$AUTH" >/dev/null

CMD=$(curl -sf -X POST "$BASE/api/v1/commands" -H "$AUTH" -H 'Content-Type: application/json' \
  -d "{\"device_id\":\"$DEVICE_ID\",\"type\":\"STATUS\",\"payload\":{}}")
CMD_ID=$(echo "$CMD" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

PENDING=$(curl -sf "$BASE/api/v1/commands/pending" -H "$DEV_AUTH")
echo "$PENDING" | grep -q "$CMD_ID"

curl -sf -X POST "$BASE/api/v1/commands/$CMD_ID/ack" -H "$DEV_AUTH" -H 'Content-Type: application/json' -d '{"status":"delivered"}' >/dev/null
curl -sf -X POST "$BASE/api/v1/commands/$CMD_ID/result" -H "$DEV_AUTH" -H 'Content-Type: application/json' \
  -d '{"status":"completed","result":{"battery":42}}' >/dev/null

STATUS=$(curl -sf "$BASE/api/v1/commands?device_id=$DEVICE_ID" -H "$AUTH" | python3 -c "import sys,json; print(json.load(sys.stdin)[0]['status'])")
test "$STATUS" = "completed"

echo "E2E backend flow OK (device_id=$DEVICE_ID, cmd_key_len=${#CMD_KEY})"
