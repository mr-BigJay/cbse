import os
from datetime import datetime, timezone
from uuid import UUID

import pytest
from httpx import AsyncClient

from app.core.security import derive_device_command_key, sign_command, verify_command_signature

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_INTEGRATION") != "1",
    reason="Integration tests require RUN_INTEGRATION=1 and PostgreSQL on TEST_DATABASE_URL",
)


@pytest.mark.asyncio
async def test_admin_login_and_me(client: AsyncClient, seeded_admin):
    email, password = seeded_admin
    login = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200
    token = login.json()["access_token"]
    me = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == email


@pytest.mark.asyncio
async def test_enrollment_approve_and_device_auth(client: AsyncClient, seeded_admin):
    email, password = seeded_admin
    login = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    admin_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    code_resp = await client.post("/api/v1/enrollment/codes", json={}, headers=admin_headers)
    assert code_resp.status_code == 200
    code = code_resp.json()["code"]

    reg = await client.post(
        "/api/v1/enrollment/register",
        json={
            "enrollment_code": code,
            "name": "Test Phone",
            "model": "TestModel",
            "capabilities": {"LOCATE": "requires_permission"},
        },
    )
    assert reg.status_code == 200
    body = reg.json()
    device_id = body["device_id"]
    device_token = body["device_token"]
    cmd_key = body["command_verification_key"]
    assert cmd_key == derive_device_command_key(UUID(device_id))

    device_headers = {"Authorization": f"Device {device_id}:{device_token}"}
    hb = await client.post("/api/v1/devices/me/heartbeat", json={"battery_level": 88}, headers=device_headers)
    assert hb.status_code == 200

    approve = await client.post(f"/api/v1/devices/{device_id}/approve", headers=admin_headers)
    assert approve.status_code == 200

    bad = await client.post("/api/v1/devices/me/heartbeat", json={}, headers={"Authorization": f"Device {device_id}:wrong"})
    assert bad.status_code == 401


@pytest.mark.asyncio
async def test_command_lifecycle(client: AsyncClient, seeded_admin):
    email, password = seeded_admin
    login = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    admin_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    code_resp = await client.post("/api/v1/enrollment/codes", json={}, headers=admin_headers)
    code = code_resp.json()["code"]
    reg = await client.post(
        "/api/v1/enrollment/register",
        json={"enrollment_code": code, "name": "Cmd Device"},
    )
    device_id = reg.json()["device_id"]
    device_token = reg.json()["device_token"]
    await client.post(f"/api/v1/devices/{device_id}/approve", headers=admin_headers)

    device_headers = {"Authorization": f"Device {device_id}:{device_token}"}
    create = await client.post(
        "/api/v1/commands",
        json={"device_id": device_id, "type": "STATUS", "payload": {}},
        headers=admin_headers,
    )
    assert create.status_code == 200
    cmd = create.json()
    assert cmd["status"] == "pending"
    cmd_id = cmd["id"]

    pending = await client.get("/api/v1/commands/pending", headers=device_headers)
    assert pending.status_code == 200
    envelopes = pending.json()
    assert len(envelopes) == 1
    assert envelopes[0]["command_id"] == cmd_id

    ack = await client.post(
        f"/api/v1/commands/{cmd_id}/ack",
        json={"status": "delivered"},
        headers=device_headers,
    )
    assert ack.status_code == 200
    assert ack.json()["status"] == "delivered"

    result = await client.post(
        f"/api/v1/commands/{cmd_id}/result",
        json={"status": "completed", "result": {"battery": 50}},
        headers=device_headers,
    )
    assert result.status_code == 200
    assert result.json()["status"] == "completed"
    assert result.json()["result"]["battery"] == 50


@pytest.mark.asyncio
async def test_command_signature_and_expiry(client: AsyncClient, seeded_admin):
    email, password = seeded_admin
    login = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    admin_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    code = (await client.post("/api/v1/enrollment/codes", json={}, headers=admin_headers)).json()["code"]
    reg = await client.post("/api/v1/enrollment/register", json={"enrollment_code": code, "name": "Sig"})
    device_id = UUID(reg.json()["device_id"])
    device_token = reg.json()["device_token"]
    await client.post(f"/api/v1/devices/{reg.json()['device_id']}/approve", headers=admin_headers)
    device_headers = {"Authorization": f"Device {device_id}:{device_token}"}

    created = await client.post(
        "/api/v1/commands",
        json={"device_id": str(device_id), "type": "ALARM", "payload": {}},
        headers=admin_headers,
    )
    cmd = created.json()
    exp = datetime.fromisoformat(cmd["expires_at"].replace("Z", "+00:00"))
    assert verify_command_signature(UUID(cmd["id"]), device_id, "ALARM", exp, cmd["signature"])

    tampered = await client.get("/api/v1/commands/pending", headers=device_headers)
    assert tampered.status_code == 200


@pytest.mark.asyncio
async def test_inactive_device_cannot_receive_commands(client: AsyncClient, seeded_admin):
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": seeded_admin[0], "password": seeded_admin[1]},
    )
    admin_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    code = (await client.post("/api/v1/enrollment/codes", json={}, headers=admin_headers)).json()["code"]
    reg = await client.post("/api/v1/enrollment/register", json={"enrollment_code": code, "name": "Pending"})
    device_id = reg.json()["device_id"]

    denied = await client.post(
        "/api/v1/commands",
        json={"device_id": device_id, "type": "STATUS", "payload": {}},
        headers=admin_headers,
    )
    assert denied.status_code == 400


@pytest.mark.asyncio
async def test_per_device_command_key_signing():
    device_id = UUID("12345678-1234-5678-1234-567812345678")
    exp = datetime.now(timezone.utc)
    cmd_id = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
    sig = sign_command(cmd_id, device_id, "STATUS", exp)
    assert verify_command_signature(cmd_id, device_id, "STATUS", exp, sig)
    assert not verify_command_signature(cmd_id, device_id, "LOCK", exp, sig)
