package com.ardm.agent

import android.app.admin.DevicePolicyManager
import android.content.ComponentName
import android.content.Intent
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.ardm.agent.admin.ArdmDeviceAdminReceiver
import com.ardm.agent.commands.CommandProcessor
import com.ardm.agent.data.SecureStore
import com.ardm.agent.network.ApiClient
import org.json.JSONObject

class MainActivity : ComponentActivity() {
    private lateinit var store: SecureStore

    private val adminLauncher = registerForActivityResult(ActivityResultContracts.StartActivityForResult()) {}

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        store = SecureStore(this)

        setContent {
            MaterialTheme(colorScheme = darkColorScheme()) {
                var server by remember { mutableStateOf(store.serverUrl ?: "") }
                var code by remember { mutableStateOf("") }
                var status by remember { mutableStateOf(enrollmentStatus()) }
                var smsNumbers by remember { mutableStateOf(store.smsSenders.joinToString(",")) }

                Column(
                    modifier = Modifier.fillMaxSize().padding(16.dp),
                    verticalArrangement = Arrangement.spacedBy(12.dp),
                ) {
                    Text("ARDM Agent — managed with consent")
                    Text("Server: ${store.serverUrl ?: "not set"}")
                    Text("Device: ${store.deviceId ?: "not enrolled"}")
                    Text(status)

                    if (store.deviceId == null) {
                        OutlinedTextField(server, { server = it }, label = { Text("Server URL") }, modifier = Modifier.fillMaxWidth())
                        OutlinedTextField(code, { code = it }, label = { Text("Enrollment code") }, modifier = Modifier.fillMaxWidth())
                        Button(onClick = {
                            store.serverUrl = server
                            enroll(code)
                            status = enrollmentStatus()
                        }) { Text("Enroll") }
                    } else {
                        Button(onClick = {
                            CommandProcessor(this@MainActivity, store, ApiClient(store)).processPending()
                            status = "Polled commands"
                        }) { Text("Poll commands now") }
                        Button(onClick = { requestDeviceAdmin() }) { Text("Enable lock (Device Admin)") }
                        OutlinedTextField(smsNumbers, { smsNumbers = it }, label = { Text("Authorized SMS senders") }, modifier = Modifier.fillMaxWidth())
                        Button(onClick = {
                            store.smsSenders = smsNumbers.split(",").map { it.trim() }.filter { it.isNotEmpty() }.toSet()
                        }) { Text("Save SMS senders") }
                        Button(onClick = {
                            store.clearEnrollment()
                            status = enrollmentStatus()
                        }) { Text("Revoke enrollment") }
                    }
                }
            }
        }
    }

    private fun enrollmentStatus(): String =
        if (store.deviceId != null) "Enrolled — awaiting server approval if pending" else "Not enrolled"

    private fun enroll(enrollmentCode: String) {
        val api = ApiClient(store)
        val caps = JSONObject()
            .put("LOCATE", "requires_permission")
            .put("LOCK", "requires_permission")
        val resp = api.register(
            enrollmentCode,
            name = "Android ${android.os.Build.MODEL}",
            model = android.os.Build.MODEL,
            manufacturer = android.os.Build.MANUFACTURER,
            androidVersion = android.os.Build.VERSION.RELEASE,
            capabilities = caps,
        )
        store.deviceId = resp.getString("device_id")
        store.deviceToken = resp.getString("device_token")
        store.smsSecret = resp.getString("sms_secret")
        store.commandVerificationKey = resp.getString("command_verification_key")
        store.adminLabel = store.serverUrl
    }

    private fun requestDeviceAdmin() {
        val admin = ComponentName(this, ArdmDeviceAdminReceiver::class.java)
        val intent = Intent(DevicePolicyManager.ACTION_ADD_DEVICE_ADMIN).apply {
            putExtra(DevicePolicyManager.EXTRA_DEVICE_ADMIN, admin)
            putExtra(DevicePolicyManager.EXTRA_ADD_EXPLANATION, "Required for remote lock when authorized")
        }
        adminLauncher.launch(intent)
    }
}
