package com.giftfile.watch2proreverse.ble

import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Job
import kotlinx.coroutines.cancel
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

enum class BluetoothAvailability { UNKNOWN, READY, PERMISSION_REQUIRED, PERMISSION_DENIED, POWERED_OFF, UNSUPPORTED, LOCATION_DISABLED }
enum class ScanProblem { PERMISSION_DENIED, START_FAILED, SCANNER_UNAVAILABLE, STOP_FAILED }
enum class DiagnosticEvent { AVAILABILITY_CHANGED, SCAN_STARTED, SCAN_STOPPED, SCAN_TIMED_OUT, SCAN_FAILED, PERMISSION_DENIED }

/** Identifiers are platform-local: Android addresses and iOS UUIDs are not interchangeable. */
data class WatchDevice(val identifier: String, val name: String?, val rssi: Int?)
data class DiagnosticEntry(
    val sequence: Long,
    val event: DiagnosticEvent,
    val code: Int? = null,
    val availability: BluetoothAvailability? = null,
)
data class DiscoveryState(
    val availability: BluetoothAvailability = BluetoothAvailability.UNKNOWN,
    val isScanning: Boolean = false,
    val devices: List<WatchDevice> = emptyList(),
    val problem: ScanProblem? = null,
    val diagnostics: List<DiagnosticEntry> = emptyList(),
)

/** All calls and state mutations are confined to the platform main thread. No connection API. */
interface BluetoothController {
    val state: StateFlow<DiscoveryState>
    fun refreshAvailability()
    fun startScan()
    fun stopScan()
    fun permissionDenied()
    fun clearDiagnostics()
    fun close()
}

/** Shared scan lifetime, bounded memory, deduplication and stale callback protection. */
abstract class BaseBluetoothController(private val scope: CoroutineScope) : BluetoothController {
    private val mutableState = MutableStateFlow(DiscoveryState())
    final override val state = mutableState.asStateFlow()
    private var generation = 0L
    private var logSequence = 0L
    private var timeout: Job? = null
    protected var closed = false
        private set

    protected fun availability(value: BluetoothAvailability) {
        if (closed || state.value.availability == value) return
        if (value != BluetoothAvailability.READY) stopScan()
        mutableState.value = state.value.copy(availability = value, problem = null)
        log(DiagnosticEvent.AVAILABILITY_CHANGED, availability = value)
    }

    protected fun beginScan(): Long? {
        if (closed || state.value.isScanning || state.value.availability != BluetoothAvailability.READY) return null
        val session = ++generation
        mutableState.value = state.value.copy(isScanning = true, devices = emptyList(), problem = null)
        log(DiagnosticEvent.SCAN_STARTED)
        timeout = scope.launch {
            delay(SCAN_DURATION_MS)
            if (isCurrent(session)) {
                stopScan()
                log(DiagnosticEvent.SCAN_TIMED_OUT)
            }
        }
        return session
    }

    protected fun isCurrent(session: Long) = !closed && state.value.isScanning && generation == session

    protected fun discovered(session: Long, device: WatchDevice) {
        if (!isCurrent(session)) return
        val devices = state.value.devices.toMutableList()
        val index = devices.indexOfFirst { it.identifier == device.identifier }
        // Do not discard a previously advertised name when a later packet omits it.
        val normalized = device.copy(name = device.name?.takeIf { it.isNotBlank() }?.take(160),
            rssi = device.rssi?.takeIf { it in -127..20 })
        if (index >= 0) devices[index] = normalized.copy(name = normalized.name ?: devices[index].name)
        else if (devices.size < MAX_DEVICES) devices.add(normalized)
        mutableState.value = state.value.copy(devices = devices)
    }

    protected fun failScan(session: Long, problem: ScanProblem, code: Int? = null) {
        if (!isCurrent(session)) return
        stopScan()
        reportProblem(problem, code)
    }

    protected fun reportProblem(problem: ScanProblem, code: Int? = null) {
        if (closed) return
        mutableState.value = state.value.copy(problem = problem)
        log(DiagnosticEvent.SCAN_FAILED, code)
    }

    override fun stopScan() {
        timeout?.cancel()
        timeout = null
        if (!state.value.isScanning) return
        ++generation
        mutableState.value = state.value.copy(isScanning = false)
        stopNativeScan()
        log(DiagnosticEvent.SCAN_STOPPED)
    }

    protected abstract fun stopNativeScan()

    override fun permissionDenied() {
        if (closed) return
        availability(BluetoothAvailability.PERMISSION_DENIED)
        mutableState.value = state.value.copy(problem = ScanProblem.PERMISSION_DENIED)
        log(DiagnosticEvent.PERMISSION_DENIED)
    }

    private fun log(event: DiagnosticEvent, code: Int? = null, availability: BluetoothAvailability? = null) {
        mutableState.value = state.value.copy(diagnostics =
            (state.value.diagnostics + DiagnosticEntry(++logSequence, event, code, availability)).takeLast(MAX_LOGS))
    }

    override fun clearDiagnostics() { mutableState.value = state.value.copy(diagnostics = emptyList()) }
    override fun close() {
        if (closed) return
        stopScan()
        closed = true
        scope.cancel()
    }

    companion object {
        const val SCAN_DURATION_MS = 15_000L
        const val MAX_DEVICES = 200
        const val MAX_LOGS = 80
    }
}
