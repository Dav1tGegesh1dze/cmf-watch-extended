package com.giftfile.watch2proreverse.ble

import androidx.lifecycle.ViewModel

/** Discovery only. No protocol or connection abstraction until there is verified behavior. */
class WatchRepository(private val bluetooth: BluetoothController) {
    val state = bluetooth.state
    fun refresh() = bluetooth.refreshAvailability()
    fun startScan() = bluetooth.startScan()
    fun stopScan() = bluetooth.stopScan()
    fun permissionDenied() = bluetooth.permissionDenied()
    fun clearDiagnostics() = bluetooth.clearDiagnostics()
    fun close() = bluetooth.close()
}

class WatchViewModel(private val repository: WatchRepository) : ViewModel() {
    val state = repository.state
    fun refresh() = repository.refresh()
    fun startScan() = repository.startScan()
    fun stopScan() = repository.stopScan()
    fun permissionDenied() = repository.permissionDenied()
    fun clearDiagnostics() = repository.clearDiagnostics()
    override fun onCleared() = repository.close()
}
