package com.ardm.agent.sms

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.provider.Telephony
import com.ardm.agent.commands.CommandProcessor
import com.ardm.agent.commands.LocalResult
import com.ardm.agent.data.SecureStore
import com.ardm.agent.network.ApiClient
import javax.crypto.Mac
import javax.crypto.spec.SecretKeySpec

class SmsCommandReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        if (Telephony.Sms.Intents.SMS_RECEIVED_ACTION != intent.action) return
        val store = SecureStore(context)
        val secret = store.smsSecret ?: return

        for (msg in Telephony.Sms.Intents.getMessagesFromIntent(intent)) {
            val sender = msg.originatingAddress ?: continue
            if (sender !in store.smsSenders) continue
            parseAndRun(context, store, secret, sender, msg.messageBody ?: continue)
        }
    }

    private fun parseAndRun(context: Context, store: SecureStore, secret: String, sender: String, body: String) {
        // ARDM v1:STATUS:exp:nonce:hmac
        val parts = body.trim().split(":")
        if (parts.size != 5 || parts[0] != "ARDM v1") return
        val command = parts[1]
        val exp = parts[2].toLongOrNull() ?: return
        val nonce = parts[3]
        val hmac = parts[4]
        if (System.currentTimeMillis() / 1000 > exp) return
        if (store.hasSmsNonce(nonce)) return
        val canonical = "${parts[0]}:$command:$exp:$nonce"
        if (!verifyHmac(secret, canonical, hmac)) return
        store.addSmsNonce(nonce)

        val api = ApiClient(store)
        val processor = CommandProcessor(context, store, api)
        val outcome = processor.executeLocal(command.uppercase())
        when (outcome) {
            is LocalResult.Ok -> if (outcome.message != "ok") sendSmsReply(sender, outcome.message)
            is LocalResult.Failed -> sendSmsReply(sender, "ERR")
            is LocalResult.Rejected -> sendSmsReply(sender, "DENY")
        }
    }

    private fun sendSmsReply(to: String, text: String) {
        runCatching {
            android.telephony.SmsManager.getDefault().sendTextMessage(to, null, "ARDM:$text", null, null)
        }
    }

    private fun verifyHmac(secret: String, message: String, provided: String): Boolean {
        val mac = Mac.getInstance("HmacSHA256")
        mac.init(SecretKeySpec(secret.toByteArray(), "HmacSHA256"))
        val hex = mac.doFinal(message.toByteArray()).joinToString("") { "%02x".format(it) }
        return hex.equals(provided, ignoreCase = true)
    }
}
