package com.ardm.agent.commands

import android.content.Context
import android.content.Intent
import android.os.Build
import com.ardm.agent.alarm.FindDeviceService
import com.ardm.agent.data.SecureStore
import com.ardm.agent.location.LocationHelper
import com.ardm.agent.network.ApiClient
import com.ardm.agent.network.CommandEnvelope
import com.ardm.agent.policy.LockHelper
import com.ardm.agent.security.CommandVerifier
import org.json.JSONObject

class CommandProcessor(
    private val context: Context,
    private val store: SecureStore,
    private val api: ApiClient,
) {
    fun processPending() {
        val deviceId = store.deviceId ?: return
        val verifyKey = store.commandVerificationKey ?: return
        for (cmd in api.pendingCommands()) {
            if (!CommandVerifier.isValid(cmd, deviceId, verifyKey)) {
                continue
            }
            api.ack(cmd.commandId)
            execute(cmd)
        }
    }

    /** SMS fallback executes the same logic without a server command id (results not reported to dashboard). */
    fun executeLocal(type: String): LocalResult {
        return try {
            when (type) {
                "STATUS" -> LocalResult.Ok("battery=${readBattery()}")
                "LOCATE" -> {
                    val loc = LocationHelper(context).getLastLocation()
                        ?: return LocalResult.Rejected("Location unavailable")
                    api.reportLocation(loc.latitude, loc.longitude, loc.accuracy)
                    LocalResult.Ok("ok")
                }
                "ALARM" -> {
                    val intent = Intent(context, FindDeviceService::class.java)
                    if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.O) {
                        context.startForegroundService(intent)
                    } else {
                        context.startService(intent)
                    }
                    LocalResult.Ok("alarm")
                }
                "LOCK" -> if (LockHelper(context).lockDevice()) LocalResult.Ok("locked") else LocalResult.Failed("Lock not authorized")
                else -> LocalResult.Rejected("Unsupported")
            }
        } catch (e: Exception) {
            LocalResult.Failed(e.message ?: "error")
        }
    }

    private fun execute(cmd: CommandEnvelope) {
        try {
            when (cmd.type) {
                "STATUS" -> {
                    val info = JSONObject()
                        .put("battery", readBattery())
                        .put("model", Build.MODEL)
                        .put("manufacturer", Build.MANUFACTURER)
                        .put("android", Build.VERSION.RELEASE)
                    api.result(cmd.commandId, "completed", info)
                }
                "LOCATE" -> {
                    val loc = LocationHelper(context).getLastLocation()
                    if (loc == null) {
                        api.result(cmd.commandId, "rejected", JSONObject(), "Location permission or fix unavailable")
                        return
                    }
                    api.reportLocation(loc.latitude, loc.longitude, loc.accuracy)
                    api.result(
                        cmd.commandId,
                        "completed",
                        JSONObject()
                            .put("latitude", loc.latitude)
                            .put("longitude", loc.longitude)
                            .put("accuracy", loc.accuracy),
                    )
                }
                "ALARM" -> {
                    startAlarmService()
                    api.result(cmd.commandId, "completed", JSONObject().put("alarm", true))
                }
                "LOCK" -> {
                    val locked = LockHelper(context).lockDevice()
                    if (locked) {
                        api.result(cmd.commandId, "completed", JSONObject().put("locked", true))
                    } else {
                        api.result(cmd.commandId, "failed", JSONObject(), "Lock not authorized — enable Device Admin")
                    }
                }
                "APP_LIST" -> {
                    val apps = AppInventory.listLaunchable(context)
                    api.result(cmd.commandId, "completed", JSONObject().put("apps", apps))
                }
                "SYNC_STATUS" -> {
                    api.result(
                        cmd.commandId,
                        "rejected",
                        JSONObject(),
                        "Open system account settings — user confirmation required",
                    )
                }
                else -> api.result(cmd.commandId, "rejected", JSONObject(), "Unsupported command")
            }
        } catch (e: Exception) {
            api.result(cmd.commandId, "failed", JSONObject(), e.message ?: "error")
        }
    }

    private fun startAlarmService() {
        val intent = Intent(context, FindDeviceService::class.java)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            context.startForegroundService(intent)
        } else {
            context.startService(intent)
        }
    }

    private fun readBattery(): Int {
        val bm = context.getSystemService(Context.BATTERY_SERVICE) as android.os.BatteryManager
        return bm.getIntProperty(android.os.BatteryManager.BATTERY_PROPERTY_CAPACITY)
    }
}
