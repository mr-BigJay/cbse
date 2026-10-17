package com.ardm.agent.security

import com.ardm.agent.network.CommandEnvelope
import java.time.Instant
import javax.crypto.Mac
import javax.crypto.spec.SecretKeySpec

object CommandVerifier {
    fun isValid(envelope: CommandEnvelope, deviceId: String, verificationKey: String): Boolean {
        if (verificationKey.isBlank()) return false
        val expires = runCatching { Instant.parse(envelope.expiresAt) }.getOrNull() ?: return false
        if (Instant.now().isAfter(expires)) return false
        val canonical = "${envelope.commandId}|$deviceId|${envelope.type}|${envelope.expiresAt}"
        val expected = hmacSha256(verificationKey, canonical)
        return expected.equals(envelope.signature, ignoreCase = true)
    }

    private fun hmacSha256(key: String, message: String): String {
        val mac = Mac.getInstance("HmacSHA256")
        mac.init(SecretKeySpec(key.toByteArray(Charsets.UTF_8), "HmacSHA256"))
        return mac.doFinal(message.toByteArray(Charsets.UTF_8)).joinToString("") { "%02x".format(it) }
    }
}
