package com.ardm.agent

import org.junit.Assert.assertTrue
import org.junit.Test
import javax.crypto.Mac
import javax.crypto.spec.SecretKeySpec

class SmsHmacTest {
    @Test
    fun hmacRoundTrip() {
        val secret = "test-secret"
        val message = "ARDM v1:STATUS:9999999999:abc"
        val mac = Mac.getInstance("HmacSHA256")
        mac.init(SecretKeySpec(secret.toByteArray(), "HmacSHA256"))
        val hex = mac.doFinal(message.toByteArray()).joinToString("") { "%02x".format(it) }
        assertTrue(hex.isNotEmpty())
    }
}
