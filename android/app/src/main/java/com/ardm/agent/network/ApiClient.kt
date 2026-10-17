package com.ardm.agent.network

import com.ardm.agent.data.SecureStore
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONArray
import org.json.JSONObject

class ApiClient(private val store: SecureStore) {
    private val client = OkHttpClient.Builder().build()
    private val jsonType = "application/json".toMediaType()

    private fun baseUrl(): String = store.serverUrl?.trimEnd('/') ?: error("Server URL not set")

    private fun deviceAuth(): String {
        val id = store.deviceId ?: error("Not enrolled")
        val token = store.deviceToken ?: error("Not enrolled")
        return "Device $id:$token"
    }

    fun register(
        enrollmentCode: String,
        name: String,
        model: String?,
        manufacturer: String?,
        androidVersion: String?,
        capabilities: JSONObject,
    ): JSONObject {
        val body = JSONObject()
            .put("enrollment_code", enrollmentCode)
            .put("name", name)
            .put("model", model)
            .put("manufacturer", manufacturer)
            .put("android_version", androidVersion)
            .put("mode", "standard")
            .put("capabilities", capabilities)
        return post("/api/v1/enrollment/register", body, auth = false)
    }

    fun heartbeat(battery: Int?, capabilities: JSONObject?) {
        val body = JSONObject().put("battery_level", battery)
        if (capabilities != null) body.put("capabilities", capabilities)
        post("/api/v1/devices/me/heartbeat", body, auth = true)
    }

    fun pendingCommands(): List<CommandEnvelope> {
        val req = Request.Builder()
            .url("${baseUrl()}/api/v1/commands/pending")
            .header("Authorization", deviceAuth())
            .get()
            .build()
        client.newCall(req).execute().use { resp ->
            if (!resp.isSuccessful) return emptyList()
            val arr = JSONArray(resp.body?.string() ?: "[]")
            return (0 until arr.length()).map { i ->
                val o = arr.getJSONObject(i)
                CommandEnvelope(
                    commandId = o.getString("command_id"),
                    type = o.getString("type"),
                    payload = o.optJSONObject("payload") ?: JSONObject(),
                    expiresAt = o.getString("expires_at"),
                    signature = o.getString("signature"),
                )
            }
        }
    }

    fun ack(commandId: String) {
        post("/api/v1/commands/$commandId/ack", JSONObject().put("status", "delivered"), auth = true)
    }

    fun result(commandId: String, status: String, result: JSONObject, error: String? = null) {
        val body = JSONObject().put("status", status).put("result", result)
        if (error != null) body.put("error", error)
        post("/api/v1/commands/$commandId/result", body, auth = true)
    }

    fun reportLocation(lat: Double, lng: Double, accuracy: Float?) {
        val body = JSONObject().put("latitude", lat).put("longitude", lng)
        if (accuracy != null) body.put("accuracy", accuracy.toDouble())
        post("/api/v1/devices/me/location", body, auth = true)
    }

    fun revoke() {
        store.clearEnrollment()
    }

    private fun post(path: String, body: JSONObject, auth: Boolean): JSONObject {
        val builder = Request.Builder()
            .url("${baseUrl()}$path")
            .post(body.toString().toRequestBody(jsonType))
        if (auth) builder.header("Authorization", deviceAuth())
        client.newCall(builder.build()).execute().use { resp ->
            val text = resp.body?.string() ?: "{}"
            if (!resp.isSuccessful) error("HTTP ${resp.code}: $text")
            return if (text.isBlank()) JSONObject() else JSONObject(text)
        }
    }
}

data class CommandEnvelope(
    val commandId: String,
    val type: String,
    val payload: JSONObject,
    val expiresAt: String,
    val signature: String,
)
