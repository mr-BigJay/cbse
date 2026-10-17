package com.ardm.agent.work

import android.content.Context
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import com.ardm.agent.commands.CommandProcessor
import com.ardm.agent.data.SecureStore
import com.ardm.agent.network.ApiClient
import org.json.JSONObject

class HeartbeatWorker(appContext: Context, params: WorkerParameters) : CoroutineWorker(appContext, params) {
    override suspend fun doWork(): Result {
        val store = SecureStore(applicationContext)
        if (store.deviceId == null) return Result.success()
        val api = ApiClient(store)
        return try {
            val bm = applicationContext.getSystemService(Context.BATTERY_SERVICE) as android.os.BatteryManager
            val level = bm.getIntProperty(android.os.BatteryManager.BATTERY_PROPERTY_CAPACITY)
            api.heartbeat(level, JSONObject())
            CommandProcessor(applicationContext, store, api).processPending()
            Result.success()
        } catch (_: Exception) {
            Result.retry()
        }
    }
}
