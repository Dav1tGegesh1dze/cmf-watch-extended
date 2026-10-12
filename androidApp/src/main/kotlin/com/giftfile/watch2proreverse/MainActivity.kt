package com.giftfile.watch2proreverse

import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Bundle
import android.provider.Settings
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.result.contract.ActivityResultContracts
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import com.giftfile.watch2proreverse.ble.AndroidBleController
import com.giftfile.watch2proreverse.ble.BluetoothAvailability
import com.giftfile.watch2proreverse.ble.WatchRepository
import com.giftfile.watch2proreverse.ble.WatchViewModel

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            val model = viewModel { WatchViewModel(WatchRepository(AndroidBleController(applicationContext))) }
            val permissions = rememberLauncherForActivityResult(ActivityResultContracts.RequestMultiplePermissions()) { result ->
                if (result.isNotEmpty() && result.values.all { it }) {
                    model.refresh()
                    if (lifecycle.currentState.isAtLeast(Lifecycle.State.STARTED)) model.startScan()
                } else model.permissionDenied()
            }
            App(model, onStartScan = {
                val required = AndroidBleController.requiredPermissions()
                if (required.all { checkSelfPermission(it) == PackageManager.PERMISSION_GRANTED }) model.startScan()
                else permissions.launch(required)
            }, onOpenSettings = {
                val intent = when (model.state.value.availability) {
                    BluetoothAvailability.POWERED_OFF -> Intent(Settings.ACTION_BLUETOOTH_SETTINGS)
                    BluetoothAvailability.LOCATION_DISABLED -> Intent(Settings.ACTION_LOCATION_SOURCE_SETTINGS)
                    else -> Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS, Uri.parse("package:$packageName"))
                }
                startActivity(intent)
            })
        }
    }
}
