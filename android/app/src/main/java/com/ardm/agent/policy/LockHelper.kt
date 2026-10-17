package com.ardm.agent.policy

import android.app.admin.DevicePolicyManager
import android.content.ComponentName
import android.content.Context
import com.ardm.agent.admin.ArdmDeviceAdminReceiver

class LockHelper(private val context: Context) {
    fun lockDevice(): Boolean {
        val dpm = context.getSystemService(Context.DEVICE_POLICY_SERVICE) as DevicePolicyManager
        val admin = ComponentName(context, ArdmDeviceAdminReceiver::class.java)
        if (!dpm.isAdminActive(admin)) return false
        dpm.lockNow()
        return true
    }
}
