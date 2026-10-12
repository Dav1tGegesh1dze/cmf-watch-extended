# Georgian support

The phone UI includes an English/Georgian toggle and these examples:

- გამარჯობა
- საქართველო
- როგორ ხარ?
- შეტყობინება

Kotlin strings preserve these characters and tests verify UTF-8 round trips. Compose renders the phone UI through the platform font stack. Verify glyphs visually on the intended Android phone and iPhone; successful compilation/UTF-8 tests do not establish rendering quality. No Georgian text is sent to the watch in Phase 1.

## Confirmed in this implementation

Localized phone UI strings and Unicode data handling exist. This is a phone-side implementation claim, not confirmation of real-watch glyph support. Hardware validation remains pending in [TESTING.md](TESTING.md).

## Technically plausible, unverified

- **Notification text:** UTF-8 transport could preserve Georgian code points if the documented command uses that encoding and accepts sufficient byte lengths. Correct encoding alone cannot supply missing firmware glyphs. Confirm field encoding, byte limits, truncation boundaries and firmware fonts before sending controlled test messages.
- **Watchface images:** rasterizing Georgian into an image on the phone could avoid watch text-font limitations for static watchface content. It does not fix dynamic notification text. Rendering format, dimensions, pixel encoding, container structure and safe transfer must be verified first.
- **Firmware fonts:** the primary research discusses decoded system font resources, but that does not establish Georgian glyph coverage, shaping support or a supported font installation mechanism. Inspect licensed/authorized resources offline for U+10D0–U+10FF and, where needed, U+1C90–U+1CBF; record the exact firmware and font tables. No resources have been extracted here.

## May require firmware modification

Adding missing glyphs to a fixed system font could require modifying firmware or signed resources if there is no supported font-loading command. Whether that is feasible is unknown. Do not flash or upload firmware without separate explicit approval; this project has no such implementation.

## Unsupported / platform constraints

This app currently supports neither custom watch fonts nor notification forwarding. No supported device API for arbitrary font installation has been verified; absence of evidence is not proof of a permanent hardware limitation.

An ordinary iOS application has no Android-style notification listener for reading all other apps' notification contents. [Apple UserNotifications](https://developer.apple.com/documentation/usernotifications) concerns an app's own notifications. [Apple Notification Center Service (ANCS)](https://developer.apple.com/library/archive/documentation/CoreBluetooth/Reference/AppleNotificationCenterServiceSpecification/Introduction/Introduction.html) is a separate accessory protocol with user authorization; it is not blanket access for a companion app. Any watch ANCS capability or interaction with the official app must be investigated separately. Phone localization does not change iOS notification restrictions or the watch's fonts.

Research sources and attribution are in [BLE_RESEARCH.md](BLE_RESEARCH.md). No third-party fonts or proprietary artwork are bundled.
