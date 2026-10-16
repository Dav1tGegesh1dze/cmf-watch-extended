# Architecture

Phase 1 uses the existing `shared`, `androidApp`, and `iosApp` wizard structure. No extra Gradle modules or DI framework are needed.

```text
Compose UI → WatchViewModel → WatchRepository → BluetoothController
                                               ├─ AndroidBleController
                                               └─ IosBleController
```

`BluetoothController` exposes an immutable `StateFlow<DiscoveryState>` and discovery lifecycle methods. Its API deliberately has no connect, pairing, GATT read/write, authentication, or firmware methods. `WatchDevice` represents any discovered BLE peripheral, not verified CMF hardware. A local name is untrusted display text, not proof of identity.

`BaseBluetoothController` owns the 15-second timeout, availability state, scan errors, identifier-based deduplication, generation checks for asynchronous results, and bounded storage (200 devices / 80 diagnostic events). A new scan clears results; stopping preserves them. Missing later names retain a previously seen name. RSSI 127 and values outside the accepted range are shown as unavailable. No devices or logs are persisted or uploaded. Diagnostic entries contain event codes, sequence numbers, availability states and optional numeric platform error codes, never identifiers, names, advertising payloads or notification contents.

All controller calls and mutations run on the platform main thread. Android marshals callbacks through a main `Handler`; CoreBluetooth uses its main dispatch queue. A lifecycle-owned `WatchViewModel` constructs the repository via constructor injection, survives Android configuration recreation, and closes its controller on clearing. Shared Compose lifecycle events refresh availability on start and stop discovery on stop. A canceled timeout cannot stop a later scan.

Android uses `BluetoothLeScanner`, checks BLE capability and adapter state, requests Nearby Devices permissions on API 31+, and fine location on API 24–30. Older Android also needs Location services enabled. CONNECT permission is needed for protected adapter/device metadata APIs; this app never establishes a connection. System broadcasts update availability. Receivers and callbacks are cleaned up with the controller. `neverForLocation` asserts that discovery is not used to infer location; Android may filter some beacon advertisements as a consequence.

On iOS, `CBCentralManager` is constructed on the first explicit scan request, so the Bluetooth privacy prompt has context. The delegate is retained strongly; permission/power changes update shared state. No background Bluetooth mode is declared. Explicit UIKit observers stop scans on background entry and resume a pending permission request only while active. Pending initialization requests are canceled on stop, and scans start only while the application is active. iOS identifiers are CoreBluetooth UUIDs, not MAC addresses, and cannot be compared directly to Android identifiers. Simulator compilation does not verify Bluetooth hardware behavior.

The Material 3 interface follows system light/dark appearance and supports an explicit English/Georgian toggle (retained across ordinary UI recreation). Georgian text uses the platform font stack; physical-device glyph inspection remains part of acceptance testing. Dependencies remain in the version catalog. The wizard's Material 3 alpha was replaced with the latest published stable Material 3 release available during implementation; existing stable compiler/Compose/AGP versions are preserved.

Tests exercise controller state transitions and repository/ViewModel behavior with a fake transport and virtual time. Actual OS permission sheets, radio state, lifecycle integration and real advertisement reception require device tests; see [TESTING.md](TESTING.md).

## Offline research tools

`tools/font_audit` is a standalone Python standard-library character-map parser with synthetic tests. It is not linked into the KMP app and has no BLE or firmware-write APIs. CI runs its tests in the Gradle configuration job. Vendor binaries remain outside Git; reports retain hashes and offsets for reproducibility.

`tools/georgian_font` invokes a pinned MIT-licensed converter and verifies generated binary glyphs with an independent Python decoder. It remains outside the KMP runtime; it contains no firmware patching or device transport.

`tools/notification_font` verifies selected static font-selection evidence against one exact older decompressed image. Its optional Capstone dependency stays outside the phone app. Hash and address guards reject other images; there are no device or firmware-write APIs.

The standalone bitmap decoder now supports bounded 2/4-bpp raw and RLE data, with or without row XOR filtering. The builder verifies both raw 4-bpp and compressed 2-bpp variants against converter rasters. This code remains outside the KMP runtime.

## Matching-version stock resource audit

The [1.0.0.73 package audit](research/STOCK_1.0.0.73_AUDIT.md) now verifies a matching-version public resource package, its internal version and partition checksums. Its named `sans32.font` is identical to the older font and lacks Georgian character mappings. This supersedes earlier missing-resource blockers; full glyph-miss tracing, font integration and a supported installation/recovery route remain pending. The audit is offline and read-only; the phone app remains discovery-only and watch rendering is not fixed.
