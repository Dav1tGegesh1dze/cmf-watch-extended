# Georgian support

The phone UI includes an English/Georgian toggle and these examples:

- გამარჯობა
- საქართველო
- როგორ ხარ?
- შეტყობინება

Kotlin strings preserve these characters and tests verify UTF-8 round trips. Compose renders the phone UI through the platform font stack. Verify glyphs visually on the intended Android phone and iPhone; successful compilation/UTF-8 tests do not establish rendering quality. No Georgian text is sent to the watch in Phase 1.

## Confirmed in this implementation

Owner observation on 2026-10-13: on Watch Pro 2 firmware 1.0.0.73, `ABC 123` appeared normally and `სალამი` appeared as six empty boxes. This is an owner-reported hardware result, not an automated test or a confirmed cause. Phone Georgian rendering and discovery were also confirmed by the owner. Other hardware acceptance items remain pending.

The [offline font audit](../tools/font_audit/README.md) found no mappings in U+10A0–U+10FF or U+1C90–U+1CBF in 56 distinct parseable font blobs from an older public dump. That dump has not been matched to 1.0.0.73. Character-map inspection does not establish notification-font selection or bitmap rendering. See the [inventory](research/PUBLIC_FONT_AUDIT.json); no firmware binaries are committed.

Localized phone UI strings and Unicode data handling exist. This is a phone-side implementation claim, not confirmation of real-watch glyph support. Remaining hardware checks are listed in [TESTING.md](TESTING.md); owner confirmations are recorded above.

## Technically plausible, unverified

- **Notification text:** UTF-8 transport could preserve Georgian code points if the documented command uses that encoding and accepts sufficient byte lengths. Correct encoding alone cannot supply missing firmware glyphs. Confirm field encoding, byte limits, truncation boundaries and firmware fonts before sending controlled test messages.
- **Watchface images:** rasterizing Georgian into an image on the phone could avoid watch text-font limitations for static watchface content. It does not fix dynamic notification text. Rendering format, dimensions, pixel encoding, container structure and safe transfer must be verified first.
- **Firmware fonts:** an older public dump has now been inspected offline as described above. Matching 1.0.0.73 resources, actual notification-font selection and a supported font installation mechanism remain unverified.

## May require firmware modification

Adding missing glyphs to a fixed system font could require modifying firmware or signed resources if there is no supported font-loading command. Whether that is feasible is unknown. Do not flash or upload firmware without separate explicit approval; this project has no such implementation.

## Unsupported / platform constraints

This app currently supports neither custom watch fonts nor notification forwarding. No supported device API for arbitrary font installation has been verified; absence of evidence is not proof of a permanent hardware limitation.

An ordinary iOS application has no Android-style notification listener for reading all other apps' notification contents. [Apple UserNotifications](https://developer.apple.com/documentation/usernotifications) concerns an app's own notifications. [Apple Notification Center Service (ANCS)](https://developer.apple.com/library/archive/documentation/CoreBluetooth/Reference/AppleNotificationCenterServiceSpecification/Introduction/Introduction.html) is a separate accessory protocol with user authorization; it is not blanket access for a companion app. Any watch ANCS capability or interaction with the official app must be investigated separately. Phone localization does not change iOS notification restrictions or the watch's fonts.

Research sources and attribution are in [BLE_RESEARCH.md](BLE_RESEARCH.md). No third-party fonts or proprietary artwork are bundled.

## Standalone font prototype

[Licensed Georgian LVGL fonts](../tools/georgian_font/README.md) can now be generated at 24, 28 and 32 px. Their decoded bitmaps match the converter raster for 161 characters per size. Laptop previews are readable; watch loading and rendering remain untested. These small font subsets must not replace full system fonts. See [branch findings and remaining requirements](research/BRANCH_AND_FONT_PROTOTYPE.md).
