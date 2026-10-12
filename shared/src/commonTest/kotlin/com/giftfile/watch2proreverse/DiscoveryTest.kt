package com.giftfile.watch2proreverse

import com.giftfile.watch2proreverse.ble.*
import com.giftfile.watch2proreverse.ui.Strings
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.advanceTimeBy
import kotlinx.coroutines.test.runCurrent
import kotlinx.coroutines.test.runTest
import kotlin.test.*

@OptIn(ExperimentalCoroutinesApi::class)
class DiscoveryTest {
    private class FakeBluetooth(scope: CoroutineScope) : BaseBluetoothController(scope) {
        var nativeStarts = 0
        var nativeStops = 0
        var latestSession = 0L
        override fun refreshAvailability() = Unit
        fun status(value: BluetoothAvailability) = availability(value)
        override fun startScan() { beginScan()?.let { latestSession = it; nativeStarts++ } }
        override fun stopNativeScan() { nativeStops++ }
        fun emit(id: String = "test-device", name: String? = "Watch", rssi: Int? = -50, session: Long = latestSession) =
            discovered(session, WatchDevice(id, name, rssi))
        fun fail(session: Long = latestSession) = failScan(session, ScanProblem.START_FAILED, 2)
    }

    @Test fun scanningRequiresReadyBluetooth() = runTest {
        val controller = FakeBluetooth(backgroundScope)
        BluetoothAvailability.entries.filter { it != BluetoothAvailability.READY }.forEach {
            controller.status(it)
            controller.startScan()
            assertFalse(controller.state.value.isScanning)
        }
        assertEquals(0, controller.nativeStarts)
    }

    @Test fun duplicateStartsDoNotRestartOrClearResults() = runTest {
        val controller = FakeBluetooth(backgroundScope)
        controller.status(BluetoothAvailability.READY)
        controller.startScan()
        controller.emit()
        controller.startScan()
        assertEquals(1, controller.nativeStarts)
        assertEquals(1, controller.state.value.devices.size)
        controller.stopScan()
    }

    @Test fun repeatedAdvertisementsUpdateRssiAndPreserveKnownName() = runTest {
        val controller = FakeBluetooth(backgroundScope)
        controller.status(BluetoothAvailability.READY)
        controller.startScan()
        controller.emit(name = "გამარჯობა", rssi = -80)
        controller.emit(name = null, rssi = -42)
        assertEquals(listOf(WatchDevice("test-device", "გამარჯობა", -42)), controller.state.value.devices)
        controller.emit(rssi = 127)
        assertNull(controller.state.value.devices.single().rssi)
        controller.stopScan()
    }

    @Test fun stopAndRestartRejectLateResultsAndErrors() = runTest {
        val controller = FakeBluetooth(backgroundScope)
        controller.status(BluetoothAvailability.READY)
        controller.startScan()
        val oldSession = controller.latestSession
        controller.emit()
        controller.stopScan()
        controller.emit(id = "late")
        assertEquals(1, controller.state.value.devices.size)
        controller.startScan()
        assertTrue(controller.state.value.devices.isEmpty())
        controller.emit(session = oldSession)
        controller.fail(oldSession)
        assertTrue(controller.state.value.devices.isEmpty())
        assertTrue(controller.state.value.isScanning)
        assertNull(controller.state.value.problem)
        controller.stopScan()
    }

    @Test fun scanAutomaticallyStopsAfterFifteenSeconds() = runTest {
        val controller = FakeBluetooth(backgroundScope)
        controller.status(BluetoothAvailability.READY)
        controller.startScan()
        runCurrent()
        advanceTimeBy(14_999)
        assertTrue(controller.state.value.isScanning)
        advanceTimeBy(1)
        runCurrent()
        assertFalse(controller.state.value.isScanning)
        assertEquals(1, controller.nativeStops)
        assertEquals(DiagnosticEvent.SCAN_TIMED_OUT, controller.state.value.diagnostics.last().event)
    }

    @Test fun oldTimeoutDoesNotStopNewSession() = runTest {
        val controller = FakeBluetooth(backgroundScope)
        controller.status(BluetoothAvailability.READY)
        controller.startScan()
        runCurrent()
        advanceTimeBy(10_000)
        controller.stopScan()
        controller.startScan()
        runCurrent()
        advanceTimeBy(5_001)
        runCurrent()
        assertTrue(controller.state.value.isScanning)
        controller.stopScan()
    }

    @Test fun powerLossStopsScanAndRetainsResults() = runTest {
        val controller = FakeBluetooth(backgroundScope)
        controller.status(BluetoothAvailability.READY)
        controller.startScan()
        controller.emit()
        controller.status(BluetoothAvailability.POWERED_OFF)
        assertFalse(controller.state.value.isScanning)
        assertEquals(1, controller.nativeStops)
        assertEquals(1, controller.state.value.devices.size)
    }

    @Test fun denialAndNativeFailureAreRecoverable() = runTest {
        val controller = FakeBluetooth(backgroundScope)
        controller.status(BluetoothAvailability.READY)
        controller.startScan()
        controller.permissionDenied()
        assertEquals(ScanProblem.PERMISSION_DENIED, controller.state.value.problem)
        assertFalse(controller.state.value.isScanning)
        controller.status(BluetoothAvailability.READY)
        controller.startScan()
        assertNull(controller.state.value.problem)
        controller.fail()
        assertFalse(controller.state.value.isScanning)
        assertEquals(ScanProblem.START_FAILED, controller.state.value.problem)
        assertEquals(2, controller.state.value.diagnostics.last().code)
        controller.startScan()
        assertNull(controller.state.value.problem)
        controller.stopScan()
    }

    @Test fun memoryIsBoundedAndDiagnosticsContainNoDeviceData() = runTest {
        val controller = FakeBluetooth(backgroundScope)
        controller.status(BluetoothAvailability.READY)
        repeat(100) { controller.startScan(); controller.stopScan() }
        controller.startScan()
        repeat(250) { controller.emit(id = "private-id-$it", name = "private-name") }
        assertEquals(BaseBluetoothController.MAX_DEVICES, controller.state.value.devices.size)
        assertEquals(BaseBluetoothController.MAX_LOGS, controller.state.value.diagnostics.size)
        assertFalse(controller.state.value.diagnostics.toString().contains("private-"))
        controller.clearDiagnostics()
        assertTrue(controller.state.value.diagnostics.isEmpty())
        controller.stopScan()
    }

    @Test fun repositoryAndViewModelForwardStateAndActions() = runTest {
        val controller = FakeBluetooth(backgroundScope)
        val repository = WatchRepository(controller)
        val model = WatchViewModel(repository)
        controller.status(BluetoothAvailability.READY)
        model.refresh()
        model.startScan()
        controller.emit()
        assertEquals(controller.state.value, model.state.value)
        model.stopScan()
        assertFalse(model.state.value.isScanning)
        model.clearDiagnostics()
        assertTrue(model.state.value.diagnostics.isEmpty())
        repository.close()
        model.startScan()
        assertEquals(1, controller.nativeStarts)
    }

    @Test fun georgianExamplesRoundTripThroughUtf8WithoutChangingText() {
        listOf("გამარჯობა", "საქართველო", "როგორ ხარ?", "შეტყობინება").forEach {
            assertEquals(it, it.encodeToByteArray().decodeToString())
            assertTrue(Strings(true).georgianSample.contains(it))
        }
    }
}
