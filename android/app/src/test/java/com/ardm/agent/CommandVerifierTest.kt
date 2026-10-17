package com.ardm.agent

import com.ardm.agent.network.CommandEnvelope
import com.ardm.agent.security.CommandVerifier
import org.json.JSONObject
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test
import java.time.Instant
import javax.crypto.Mac
import javax.crypto.spec.SecretKeySpec

class CommandVerifierTest {
    @Test
    fun validSignatureAccepted() {
        val deviceId = "12345678-1234-5678-1234-567812345678"
        val cmdId = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        val exp = Instant.now().plusSeconds(600).toString()
        val key = "test-key"
        val canonical = "$cmdId|$deviceId|STATUS|$exp"
        val sig = hmac(key, canonical)
        val envelope = CommandEnvelope(cmdId, "STATUS", JSONObject(), exp, sig)
        assertTrue(CommandVerifier.isValid(envelope, deviceId, key))
    }

    @Test
    fun expiredRejected() {
        val deviceId = "12345678-1234-5678-1234-567812345678"
        val exp = Instant.now().minusSeconds(10).toString()
        val envelope = CommandEnvelope("id", "STATUS", JSONObject(), exp, "00")
        assertFalse(CommandVerifier.isValid(envelope, deviceId, "key"))
    }

    private fun hmac(key: String, message: String): String {
        val mac = Mac.getInstance("HmacSHA256")
        mac.init(SecretKeySpec(key.toByteArray(), "HmacSHA256"))
        return mac.doFinal(message.toByteArray()).joinToString("") { "%02x".format(it) }
    }
}
