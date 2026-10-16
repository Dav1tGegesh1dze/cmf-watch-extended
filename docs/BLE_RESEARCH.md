# BLE research and evidence

Reviewed 2026-10-12. Phase 1 scans advertisements through public platform APIs; it implements no device-specific UUID, opcode, packet format, checksum, cryptography, GATT access or pairing operation.

## Source register

| Source | Pinned revision reviewed | Relevance / license |
| --- | --- | --- |
| [joshuapassos/CMF-Watch-Pro-2-BLE-Protocol](https://github.com/joshuapassos/CMF-Watch-Pro-2-BLE-Protocol/tree/c1e5993fffe40385bdf5e3967abaa0c25293d8f3) | `c1e5993fffe40385bdf5e3967abaa0c25293d8f3` | Reverse-engineering notes covering advertising, GATT, framing, authentication, encryption and watchface formats. No top-level license was present when inspected; treat as a reference, not permission to copy code/assets. |
| [Bendy3192/reCMF](https://github.com/Bendy3192/reCMF/tree/7e1c13959922bafd7a7659c8829685383cb290a6) | `7e1c13959922bafd7a7659c8829685383cb290a6` | Android companion implementation and firmware-specific observations. AGPL-3.0; do not transplant implementation without assessing obligations. |
| [freethinkel/fmc](https://github.com/freethinkel/fmc/tree/fe83ffc3a5d71230fe530d1f574647f4cabd70f6) | `fe83ffc3a5d71230fe530d1f574647f4cabd70f6` | Watchface editor and transfer research. AGPL-3.0, with separately licensed fonts. No source, font, watchface or artwork copied. |

These projects report results on their own hardware. They are not evidence that this application has successfully used the user's watch. Authentication details in the sources need reconciliation before implementation; this phase does not adopt either description or reproduce any secrets.

## Discovery decisions

- Discover all advertising BLE peripherals without filtering on an assumed watch UUID or name. The primary notes describe a CMF-style local name, but a name can change, be absent or be spoofed.
- Show the local name when available; otherwise show an explicit unnamed-device label. Update RSSI for repeat advertisements and deduplicate by platform identifier.
- Display iOS UUIDs and Android addresses as identifiers, without claiming equivalence or permanent identity.
- Discovery does not establish a connection. No GATT services are enumerated and no notification characteristics are subscribed to.
- The official CMF app may keep the watch connected, and the watch may not advertise. An empty scan is not proof of incompatibility. Keep the existing pairing; do not reset/unpair to make discovery pass.
- OS scanning may exchange link-layer scan requests, but this app sends no application commands or GATT writes.

## Platform references

- [Android Bluetooth permissions](https://developer.android.com/develop/connectivity/bluetooth/bt-permissions): API 31+ SCAN/CONNECT runtime permissions; legacy fine-location permissions; `neverForLocation` may filter beacons.
- [Android BLE discovery](https://developer.android.com/develop/connectivity/bluetooth/ble/find-ble-devices): bounded scan duration and stopping scans when no longer needed.
- [Apple CBCentralManager](https://developer.apple.com/documentation/corebluetooth/cbcentralmanager): central state, peripheral discovery and delegate lifecycle.
- [Apple Bluetooth background processing](https://developer.apple.com/library/archive/documentation/NetworkingInternetWeb/Conceptual/CoreBluetooth_concepts/CoreBluetoothBackgroundProcessingForIOSApps/PerformingTasksWhileYourAppIsInTheBackground.html): foreground and background behavior differ. This phase declares no background Bluetooth capability.

## Gate for every later protocol feature

Record the source revision and license, exact command and framing, byte order, length limits, checksum, authentication and encryption requirements, error behavior and firmware version. Add independently authored encoding/decoding tests with non-secret fixtures. Reconcile conflicting references. Obtain approval for operations that change pairing or firmware. Only label a hardware feature verified after an actual device test with redacted results. Never commit authentication keys or private captures.

## Font evidence

See [the read-only audit tool](../tools/font_audit/README.md) for pinned LVGL format references, parser limitations and the older public-dump inventory. This analysis uses no BLE operations. It does not establish a system-font upload command or compatibility with firmware 1.0.0.73.

[Branch investigation](research/BRANCH_AND_FONT_PROTOTYPE.md) found an upstream flashing branch, but successful modified firmware installation is explicitly unresolved there. Its code was not executed. The new standalone font prototype introduces no BLE behavior.

The [acquisition follow-up](research/GEORGIAN_ACQUISITION_FOLLOWUP.md) adds a pinned source review and read-only CDN/header evidence. No device protocol or firmware installation behavior was added.

The [notification-renderer analysis](research/NOTIFICATION_RENDERER.md) is static and offline. Its inferred code addresses apply only to the hashed older dump and are never BLE commands, write targets or firmware patch offsets.

## Matching-version stock resource audit

The [1.0.0.73 package audit](research/STOCK_1.0.0.73_AUDIT.md) now verifies a matching-version public resource package, its internal version and partition checksums. Its named `sans32.font` is identical to the older font and lacks Georgian character mappings. This supersedes earlier missing-resource blockers; full glyph-miss tracing, font integration and a supported installation/recovery route remain pending. The audit is offline and read-only; the phone app remains discovery-only and watch rendering is not fixed.
