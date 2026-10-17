package com.ardm.agent.commands

import android.content.Context
import org.json.JSONArray

object AppInventory {
    fun listLaunchable(context: Context): JSONArray {
        val pm = context.packageManager
        val intents = pm.queryIntentActivities(
            android.content.Intent(android.content.Intent.ACTION_MAIN).addCategory(android.content.Intent.CATEGORY_LAUNCHER),
            0,
        )
        val arr = JSONArray()
        intents.take(100).forEach { ri ->
            arr.put(ri.activityInfo.packageName)
        }
        return arr
    }
}
