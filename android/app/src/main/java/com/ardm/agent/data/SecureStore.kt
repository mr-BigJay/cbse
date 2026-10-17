package com.ardm.agent.data

import android.content.Context
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey

class SecureStore(context: Context) {
    private val prefs = EncryptedSharedPreferences.create(
        context,
        "ardm_secure",
        MasterKey.Builder(context).setKeyScheme(MasterKey.KeyScheme.AES256_GCM).build(),
        EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
        EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM,
    )

    var serverUrl: String?
        get() = prefs.getString("server_url", null)
        set(value) = prefs.edit().putString("server_url", value).apply()

    var deviceId: String?
        get() = prefs.getString("device_id", null)
        set(value) = prefs.edit().putString("device_id", value).apply()

    var deviceToken: String?
        get() = prefs.getString("device_token", null)
        set(value) = prefs.edit().putString("device_token", value).apply()

    var smsSecret: String?
        get() = prefs.getString("sms_secret", null)
        set(value) = prefs.edit().putString("sms_secret", value).apply()

    var adminLabel: String?
        get() = prefs.getString("admin_label", null)
        set(value) = prefs.edit().putString("admin_label", value).apply()

    var smsSenders: Set<String>
        get() = prefs.getStringSet("sms_senders", emptySet()) ?: emptySet()
        set(value) = prefs.edit().putStringSet("sms_senders", value).apply()

    fun addSmsNonce(nonce: String) {
        val current = prefs.getStringSet("sms_nonces", mutableSetOf())?.toMutableSet() ?: mutableSetOf()
        current.add(nonce)
        while (current.size > 200) {
            current.remove(current.first())
        }
        prefs.edit().putStringSet("sms_nonces", current).apply()
    }

    fun hasSmsNonce(nonce: String): Boolean =
        prefs.getStringSet("sms_nonces", emptySet())?.contains(nonce) == true

    fun clearEnrollment() {
        prefs.edit()
            .remove("device_id")
            .remove("device_token")
            .remove("sms_secret")
            .apply()
    }
}
