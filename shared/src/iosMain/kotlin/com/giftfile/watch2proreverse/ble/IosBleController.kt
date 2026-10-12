@file:OptIn(kotlinx.cinterop.ExperimentalForeignApi::class)

package com.giftfile.watch2proreverse.ble

import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import platform.CoreBluetooth.*
import platform.Foundation.NSNumber
import platform.Foundation.NSNotificationCenter
import platform.Foundation.NSOperationQueue
import platform.darwin.NSObject
import platform.UIKit.UIApplication
import platform.UIKit.UIApplicationDidBecomeActiveNotification
import platform.UIKit.UIApplicationDidEnterBackgroundNotification
import platform.UIKit.UIApplicationState.UIApplicationStateActive

class IosBleController : BaseBluetoothController(CoroutineScope(SupervisorJob() + Dispatchers.Main.immediate)) {
    private var manager: CBCentralManager? = null
    private var pendingStart = false
    private var session: Long? = null
    // CBCentralManager's delegate is weak; keep a strong reference for its entire lifetime.
    private val delegate = object : NSObject(), CBCentralManagerDelegateProtocol {
        override fun centralManagerDidUpdateState(central: CBCentralManager) {
            if (closed) return
            refreshAvailability()
            if (pendingStart && central.state == CBManagerStatePoweredOn &&
                UIApplication.sharedApplication.applicationState == UIApplicationStateActive) {
                pendingStart = false
                startScan()
            }
        }

        override fun centralManager(
            central: CBCentralManager,
            didDiscoverPeripheral: CBPeripheral,
            advertisementData: Map<Any?, *>,
            RSSI: NSNumber,
        ) {
            val activeSession = session ?: return
            if (UIApplication.sharedApplication.applicationState != UIApplicationStateActive) return
            discovered(activeSession, WatchDevice(
                didDiscoverPeripheral.identifier.UUIDString,
                advertisementData[CBAdvertisementDataLocalNameKey] as? String ?: didDiscoverPeripheral.name,
                RSSI.intValue.takeUnless { it == 127 },
            ))
        }
    }

    // Explicit OS observers also cover backgrounding while the permission request is pending.
    private val backgroundObserver = NSNotificationCenter.defaultCenter.addObserverForName(
        UIApplicationDidEnterBackgroundNotification, null, NSOperationQueue.mainQueue,
    ) { stopScan() }
    private val foregroundObserver = NSNotificationCenter.defaultCenter.addObserverForName(
        UIApplicationDidBecomeActiveNotification, null, NSOperationQueue.mainQueue,
    ) {
        refreshAvailability()
        if (pendingStart && state.value.availability == BluetoothAvailability.READY) {
            pendingStart = false
            startScan()
        }
    }

    override fun refreshAvailability() {
        if (closed) return
        val authorization = CBManager.authorization
        val status = when (authorization) {
            CBManagerAuthorizationDenied, CBManagerAuthorizationRestricted -> BluetoothAvailability.PERMISSION_DENIED
            CBManagerAuthorizationNotDetermined -> BluetoothAvailability.PERMISSION_REQUIRED
            else -> when (manager?.state) {
                CBManagerStatePoweredOn -> BluetoothAvailability.READY
                CBManagerStatePoweredOff -> BluetoothAvailability.POWERED_OFF
                CBManagerStateUnsupported -> BluetoothAvailability.UNSUPPORTED
                CBManagerStateUnauthorized -> BluetoothAvailability.PERMISSION_DENIED
                else -> BluetoothAvailability.UNKNOWN
            }
        }
        // Preserve an explicit request only while CoreBluetooth initializes / asks permission.
        val requested = pendingStart
        availability(status)
        pendingStart = requested && status in listOf(BluetoothAvailability.UNKNOWN, BluetoothAvailability.PERMISSION_REQUIRED, BluetoothAvailability.READY)
    }

    override fun startScan() {
        if (closed || UIApplication.sharedApplication.applicationState != UIApplicationStateActive) return
        if (manager == null) {
            pendingStart = true
            // nil queue means main queue. Creation is user initiated so the privacy prompt is contextual.
            manager = CBCentralManager(delegate, null, mapOf(CBCentralManagerOptionShowPowerAlertKey to false))
            return
        }
        refreshAvailability()
        if (state.value.availability == BluetoothAvailability.UNKNOWN) {
            pendingStart = true
            return
        }
        val newSession = beginScan() ?: return
        session = newSession
        // No guessed service UUID filters: discover all advertising BLE peripherals.
        manager?.scanForPeripheralsWithServices(null, mapOf(CBCentralManagerScanOptionAllowDuplicatesKey to true))
    }

    override fun stopScan() {
        pendingStart = false
        super.stopScan()
    }

    override fun stopNativeScan() {
        session = null
        manager?.stopScan()
    }

    override fun close() {
        if (closed) return
        super.close()
        NSNotificationCenter.defaultCenter.removeObserver(backgroundObserver)
        NSNotificationCenter.defaultCenter.removeObserver(foregroundObserver)
        manager?.delegate = null
        manager = null
    }
}
