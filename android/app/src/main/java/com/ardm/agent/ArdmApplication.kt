package com.ardm.agent

import android.app.Application
import androidx.work.ExistingPeriodicWorkPolicy
import androidx.work.PeriodicWorkRequestBuilder
import androidx.work.WorkManager
import com.ardm.agent.work.HeartbeatWorker
import java.util.concurrent.TimeUnit

class ArdmApplication : Application() {
    override fun onCreate() {
        super.onCreate()
        val request = PeriodicWorkRequestBuilder<HeartbeatWorker>(15, TimeUnit.MINUTES).build()
        WorkManager.getInstance(this).enqueueUniquePeriodicWork(
            "ardm-heartbeat",
            ExistingPeriodicWorkPolicy.KEEP,
            request,
        )
    }
}
