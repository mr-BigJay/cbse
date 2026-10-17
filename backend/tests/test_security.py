from datetime import datetime, timezone
from uuid import uuid4

from app.core.security import sign_command, verify_command_signature, verify_password, hash_password


def test_password_hash_roundtrip():
    hashed = hash_password("secret-pass")
    assert verify_password("secret-pass", hashed)
    assert not verify_password("wrong", hashed)


def test_command_signature():
    cid = uuid4()
    did = uuid4()
    exp = datetime.now(timezone.utc)
    sig = sign_command(cid, did, "STATUS", exp)
    assert verify_command_signature(cid, did, "STATUS", exp, sig)
    assert not verify_command_signature(cid, did, "LOCK", exp, sig)
