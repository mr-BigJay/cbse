import hmac
import hashlib
import time

from app.core.security import verify_sms_hmac


def test_sms_hmac_valid():
    secret = "sms-test-secret"
    exp = int(time.time()) + 300
    nonce = "nonce-1"
    canonical = f"ARDM v1:STATUS:{exp}:{nonce}"
    mac = hmac.new(secret.encode(), canonical.encode(), hashlib.sha256).hexdigest()
    assert verify_sms_hmac(secret, canonical, mac)


def test_sms_hmac_rejects_wrong_secret():
    secret = "sms-test-secret"
    canonical = "ARDM v1:LOCK:9999999999:abc"
    mac = hmac.new(b"other", canonical.encode(), hashlib.sha256).hexdigest()
    assert not verify_sms_hmac(secret, canonical, mac)
