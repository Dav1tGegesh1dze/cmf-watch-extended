# Roadmap

1. **BLE discovery (this PR):** availability, permissions, foreground scan start/stop/timeout, names, identifiers, RSSI, bounded diagnostics, English/Georgian phone UI, shared tests and CI. Hardware acceptance is pending.
2. **Read-only connection diagnostics:** after Phase 1 is reviewed and physically tested, explicitly assess interaction with the official iPhone app, connect/disconnect without pairing changes, enumerate GATT services, and compare observed UUIDs with pinned research. No writes or authentication until separately reviewed.
3. **Protocol research and offline codecs:** reconcile documented framing/authentication/encryption differences, use synthetic non-secret test fixtures, document licenses, and test encoding/decoding without hardware writes.
4. **Authenticated read operations:** secure Keychain/Keystore storage, explicit permission for any pairing change, verified device/battery information and time synchronization only after command-by-command review (time synchronization is a write).
5. **Customization research:** local watchface preview and Georgian raster text first; transfer only after documented formats, checksums, bounds and recovery behavior are verified.
6. **Notifications and diagnostics:** controlled notifications where supported, clear iOS limitations, connection health, locally collected battery history, redacted log export and experimental feature flags.

Firmware modification, flashing, reset and unpairing are never implied by this roadmap. Each feature gets a separate branch and pull request. The owner authorized merging implementation PRs after required checks pass on 2026-10-13; no protection bypasses.

Georgian work now includes a read-only [font audit tool](../tools/font_audit/README.md). It found no Georgian character mappings in 56 distinct parseable fonts from an older public dump. Matching 1.0.0.73 resources and a verified installation mechanism are still required before a native notification fix can be implemented.

A standalone [Georgian font prototype](../tools/georgian_font/README.md) now verifies glyph serialization and produces previews. Integrating it into notification rendering is still blocked on version-specific font selection and a verified resource installation/recovery mechanism.

The next Georgian research step is tracing notification font assignment and fallback from the [recorded offline leads](research/GEORGIAN_ACQUISITION_FOLLOWUP.md), while obtaining matching-version resources. A duplicate older dump or changed version label cannot satisfy that requirement.

The [older-image notification trace](research/NOTIFICATION_RENDERER.md) now establishes explicit font loading and default-character configuration. Next: obtain matching 1.0.0.73 resources, verify the same renderer path, and assess a coverage-preserving integration plus installation/recovery route before any firmware change.

The [compressed font implementation](research/COMPRESSED_GEORGIAN_FONTS.md) closes the prototype depth/compression gap with the older notification font. The remaining work is matching-version analysis and coverage-preserving integration with a verified installation/recovery route.

## Matching-version stock resource audit

The [1.0.0.73 package audit](research/STOCK_1.0.0.73_AUDIT.md) now verifies a matching-version public resource package, its internal version and partition checksums. Its named `sans32.font` is identical to the older font and lacks Georgian character mappings. This supersedes earlier missing-resource blockers; full glyph-miss tracing, font integration and a supported installation/recovery route remain pending. The audit is offline and read-only; the phone app remains discovery-only and watch rendering is not fixed.
