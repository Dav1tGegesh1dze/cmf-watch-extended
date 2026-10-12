package com.giftfile.watch2proreverse.ble

import android.Manifest
import android.annotation.SuppressLint
import android.bluetooth.BluetoothAdapter
import android.bluetooth.BluetoothManager
import android.bluetooth.le.BluetoothLeScanner
import android.bluetooth.le.ScanCallback
import android.bluetooth.le.ScanResult
import android.bluetooth.le.ScanSettings
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.content.pm.PackageManager
import android.location.LocationManager
import android.os.Build
import android.os.Handler
import android.os.Looper
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob

class AndroidBleController(context: Context) : BaseBluetoothController(
    CoroutineScope(SupervisorJob() + Dispatchers.Main.immediate)
) {
    private val context = context.applicationContext
    private val handler = Handler(Looper.getMainLooper())
    private val adapter get() = this.context.getSystemService(BluetoothManager::class.java)?.adapter
    private var scanner: BluetoothLeScanner? = null
    private var callback: ScanCallback? = null
    private val receiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context?, intent: Intent?) { refreshAvailability() }
    }

    init {
        val filter = IntentFilter(BluetoothAdapter.ACTION_STATE_CHANGED).apply {
            addAction(LocationManager.MODE_CHANGED_ACTION)
        }
        // These broadcasts originate from the system Bluetooth/location components.
        if (Build.VERSION.SDK_INT >= 33) this.context.registerReceiver(receiver, filter, Context.RECEIVER_EXPORTED)
        else this.context.registerReceiver(receiver, filter)
        refreshAvailability()
    }

    private fun hasPermissions() = requiredPermissions().all {
        context.checkSelfPermission(it) == PackageManager.PERMISSION_GRANTED
    }

    @SuppressLint("MissingPermission") // Checked immediately before accessing protected adapter APIs.
    override fun refreshAvailability() {
        if (closed) return
        val status = try {
            when {
                !context.packageManager.hasSystemFeature(PackageManager.FEATURE_BLUETOOTH_LE) || adapter == null -> BluetoothAvailability.UNSUPPORTED
                !hasPermissions() -> if (state.value.availability == BluetoothAvailability.PERMISSION_DENIED)
                    BluetoothAvailability.PERMISSION_DENIED else BluetoothAvailability.PERMISSION_REQUIRED
                adapter?.isEnabled != true -> BluetoothAvailability.POWERED_OFF
                Build.VERSION.SDK_INT <= 30 && !locationEnabled() -> BluetoothAvailability.LOCATION_DISABLED
                else -> BluetoothAvailability.READY
            }
        } catch (_: SecurityException) { BluetoothAvailability.PERMISSION_REQUIRED }
        availability(status)
    }

    private fun locationEnabled(): Boolean {
        val manager = context.getSystemService(LocationManager::class.java) ?: return false
        return if (Build.VERSION.SDK_INT >= 28) manager.isLocationEnabled
        else manager.isProviderEnabled(LocationManager.GPS_PROVIDER) || manager.isProviderEnabled(LocationManager.NETWORK_PROVIDER)
    }

    @SuppressLint("MissingPermission")
    override fun startScan() {
        refreshAvailability()
        val session = beginScan() ?: return
        try {
            val nativeScanner = adapter?.bluetoothLeScanner
            if (nativeScanner == null) {
                failScan(session, ScanProblem.SCANNER_UNAVAILABLE)
                return
            }
            val nativeCallback = object : ScanCallback() {
                override fun onScanResult(callbackType: Int, result: ScanResult) { accept(result) }
                override fun onBatchScanResults(results: MutableList<ScanResult>) { results.forEach(::accept) }
                private fun accept(result: ScanResult) {
                    handler.post {
                        if (!isCurrent(session)) return@post
                        try {
                            discovered(session, WatchDevice(result.device.address,
                                result.scanRecord?.deviceName ?: result.device.name, result.rssi))
                        } catch (_: SecurityException) { permissionDenied() }
                    }
                }
                override fun onScanFailed(errorCode: Int) {
                    handler.post { failScan(session, ScanProblem.START_FAILED, errorCode) }
                }
            }
            scanner = nativeScanner
            callback = nativeCallback
            nativeScanner.startScan(null, ScanSettings.Builder()
                .setScanMode(ScanSettings.SCAN_MODE_LOW_LATENCY).build(), nativeCallback)
        } catch (_: SecurityException) { permissionDenied() }
        catch (_: IllegalStateException) {
            failScan(session, ScanProblem.START_FAILED)
            refreshAvailability()
        }
    }

    @SuppressLint("MissingPermission")
    override fun stopNativeScan() {
        val oldCallback = callback
        callback = null
        try {
            if (oldCallback != null) scanner?.stopScan(oldCallback)
        } catch (_: SecurityException) { reportProblem(ScanProblem.STOP_FAILED) }
        catch (_: IllegalStateException) { reportProblem(ScanProblem.STOP_FAILED) }
        finally { scanner = null }
    }

    override fun close() {
        if (closed) return
        super.close()
        context.unregisterReceiver(receiver)
        handler.removeCallbacksAndMessages(null)
    }

    companion object {
        fun requiredPermissions(): Array<String> = if (Build.VERSION.SDK_INT >= 31)
            arrayOf(Manifest.permission.BLUETOOTH_SCAN, Manifest.permission.BLUETOOTH_CONNECT)
        else arrayOf(Manifest.permission.ACCESS_FINE_LOCATION)
    }
}
