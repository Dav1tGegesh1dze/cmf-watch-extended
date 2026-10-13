# Georgian notifications: firmware 1.0.0.73 investigation

Research date: 2026-10-12. Target: CMF Watch Pro 2, paired with the official CMF app on an iPhone 16 Pro. The owner confirmed firmware **1.0.0.73**, discovery in our app, and Georgian rendering in our phone UI. Watch notification rendering has not yet been measured with the controlled samples below.

## Finding and decision

Owner reports support a Georgian notification-rendering problem. Missing font glyphs are a strong hypothesis, not yet a verified character-table finding for this watch. Phone localization cannot install watch fonts. No safe, documented system-font installation command or confirmed Georgian notification fix was found in the sources reviewed.

Proceed with a controlled notification baseline and offline font inspection. Do not implement speculative BLE writes, authentication, or firmware updates as a font fix. Nothing has been transmitted to the watch during this investigation.

## Evidence and its limits

| Evidence | What it establishes | What it does not establish |
| --- | --- | --- |
| [Nothing community: Georgian on Watch Pro 2](https://nothing.community/d/25500-cmf-watch-pro-2-georgian-language-support) | Owners report unreadable Georgian notifications, including square placeholders. | Exact font coverage on every firmware; a working remedy. Some replies discuss other models. |
| [Additional Watch Pro 2 report](https://nothing.community/en/d/50669-cmf-watch-georgian-language-support) | Another owner requests Mkhedruli notification support. | Independent inspection of the firmware. |
| [Official system-language list](https://support.cmf.tech/hc/en-us/articles/26428716785297-Which-system-languages-are-available-on-Watch-Pro-2) | Georgian is absent from the published UI-language list. | Notification fonts can cover languages absent from the UI; this is not a glyph inventory. |
| [Protocol research, pinned revision](https://github.com/joshuapassos/CMF-Watch-Pro-2-BLE-Protocol/blob/c1e5993fffe40385bdf5e3967abaa0c25293d8f3/README.md), sections 9 and 11 | Research targets 1.0.0.73, describes UTF-8 notification fields, and reports decoding LVGL system fonts. | Georgian coverage, permission to redistribute fonts, or a supported global font-upload command. Its hardware claims are the author's, not our validation. |
| [Public firmware manifest](https://github.com/whatotter/cmf-watch-firmware/blob/fd8c7081c2e36355fdfc65391878fe57e528c456/info.xml) | A firmware package identifies a separate font resource named `fonts.bin`. Its internal version is `1.00_2408181820`. | A verified mapping to the owner's 1.0.0.73 firmware or permission to rewrite that resource. |
| [Request for the matching stock firmware](https://github.com/joshuapassos/CMF-Watch-Pro-2-BLE-Protocol/issues/2) | Another researcher has requested the 1.0.0.73 OTA image, hash or URL. No response supplying it was visible during this review. | Availability or authenticity of a matching image. |

Also reviewed [reCMF](https://github.com/Bendy3192/reCMF) and [fmc](https://github.com/freethinkel/fmc). Android notification relaying and watchface font sprites do not establish an iOS notification-font fix. No third-party code, firmware or fonts have been copied into this project. These repositories' license requirements must be assessed before any reuse; public availability alone is insufficient.

## Reproducible test on the owner's watch

This test uses the **official CMF app and the existing pairing**, not our discovery app. No laptop or USB connection is needed. Do not change firmware, unpair, or reset anything.

1. Stop scanning in CMF Watch Extended. Confirm the official app shows the watch connected.
2. Use a messaging app whose incoming notifications already reach the watch. Keep its existing notification settings. Have a second person or account send the samples below as separate messages while the iPhone is locked. Self-messages may not generate equivalent notifications.
3. First verify the ASCII control reaches both phone and watch. If it does not, stop: delivery must work before interpreting a font test.
4. Compare the phone notification with the watch's expanded notification, not only its brief preview. Record whether each line is correct, blank, boxes, question marks, or truncated. Record title and body separately if they differ.
5. Use only these synthetic samples. Record the messaging app, firmware and results; exclude sender identifiers and private messages from diagnostic material.

| Sample | Purpose | Result |
| --- | --- | --- |
| `ABC 123` | Delivery and Latin control | Not executed |
| `გამარჯობა` | Short Mkhedruli sample | Not executed |
| `ABC გამარჯობა 123` | Mixed script and intact surrounding Latin | Not executed |
| `საქართველო` | Additional Georgian letters | Not executed |
| `როგორ ხარ?` | Space and punctuation | Not executed |
| `შეტყობინება` | Notification example | Not executed |
| `ᲒᲐᲛᲐᲠᲯᲝᲑᲐ` | Mtavruli separately from Mkhedruli | Not executed |

Boxes only for Georgian with intact Latin strengthen the missing-glyph/fallback hypothesis. They do not by themselves distinguish font coverage from a watch renderer or transport bug. A short sample failing throughout is different from a long sample losing only its final character; UTF-8 boundary truncation must be investigated separately. Do not apply documented custom-command byte limits to Apple's notification path without evidence.

## Next engineering milestone: verify font coverage offline

### Follow-up source search

The [official community 1.0.0.73 announcement](https://nothing.community/en/d/42725-cmf-watch-pro-2-10073-changelog) dates the release announcement to September 2025. The public dump's internal manifest date is August 2024; a later firmware could reuse resources, but this does not establish identical font contents.

An additional lead, [CMF-Ringtone-Tool](https://github.com/tirodz/CMF-Ringtone-Tool/tree/6e867e18f7984df694a2a0e75a08c78c5c06603c), labels a firmware registry entry 1.0.0.73 while directing readers to the same whatotter dump for `original.bin`. Its registry is not independent proof of the dump's version or font coverage. The project explicitly marks BLE installation as untested on hardware. No scripts from it were executed, no code was copied, and no debug-shell operations were attempted. Its GPL-3.0 license would need consideration before code reuse.

Searches for the exact version with firmware download, binary and CDN terms did not locate an authenticated matching image or published checksum. The protocol repository's firmware-request issue still had no comments when checked. This is a search result, not a claim that the image does not exist. The immediate missing research input remains a provenance-backed matching image or font export; the owner does not need to reset or update the watch to continue the notification baseline.

Required input is an authentic stock 1.0.0.73 OTA image or extracted fonts with provenance, ideally the original download URL and a published checksum. Do not trigger an update or intercept private account traffic merely to obtain it. A public older dump may help understand formats but cannot prove this firmware's coverage.

Once a matching artifact is available:

1. Record source, acquisition date, SHA-256, manifest and firmware mapping. Keep proprietary binaries out of Git.
2. Identify the font container from its actual bytes and published format documentation. Extract read-only with bounded lengths and resource limits. Never execute downloaded extraction scripts without review.
3. Decode character maps and glyph presence, including U+10D0–U+10FF and U+1C90–U+1CBF. Test each sample's code points. Glyph counts or searching binary strings cannot establish coverage.
4. Identify which fonts the notification renderer selects and its fallback behavior. Finding a Georgian glyph in an unrelated font would not prove notification support.
5. Publish a reproducible inventory and test the parser against synthetic valid, truncated and malformed fixtures. Mark actual glyph rendering separately from character-map presence.
6. If glyphs exist, investigate encoding and renderer selection. If absent, look for a documented resource installation mechanism. Without one, a vendor firmware update or separately authorized firmware research is needed; no safe native fix can yet be promised.

## Candidate outcomes

| Approach | Status and limitation |
| --- | --- |
| Native Georgian notifications | Desired outcome; no verified fix yet. Missing global glyphs would need a watch-side remedy. |
| Georgian rendered into a watchface image | Plausible static-display workaround. Does not repair notification text. Transfer and actual display remain untested here. |
| Latin transliteration | Loses Georgian script. Our iOS app cannot generally intercept and rewrite other apps' notifications. Not implemented as a substitute. |
| Firmware/font resource modification | Feasibility and recovery unknown. Requires separate explicit approval before modifying or uploading firmware. |

[Apple ANCS](https://developer.apple.com/library/archive/documentation/CoreBluetooth/Reference/AppleNotificationCenterServiceSpecification/Introduction/Introduction.html) provides notifications to authorized accessories. It does not grant our phone app blanket access to other apps' notifications. A future own-app notification test can exercise delivery if allowed by the official companion's settings, but cannot supply missing watch glyphs.

## Delivery and validation

This is a documentation-only research change, branched from main. No application behavior changed; no builds or unit tests were run for this change. Source links and firmware metadata were inspected, and `git diff --check` was run. The notification matrix and font inventory remain unexecuted.

The discovery implementation is in [PR #1](https://github.com/Dav1tGegesh1dze/cmf-watch-extended/pull/1), still unmerged at research time. Review that PR first. This branch intentionally does not duplicate its application or CI files. Required CI checks cannot run on this branch until that workflow is present; after PR #1 merges, update this branch from main and let CI run. Do not weaken branch protection or merge automatically.

## Follow-up, 2026-10-13

The owner reports normal `ABC 123` notifications and six empty boxes for `სალამი` on firmware 1.0.0.73. The original matrix above remains unexecuted except for the ASCII control; the owner used a different Georgian sample. The messaging app and expanded-versus-preview view were not specified.

An independently implemented [offline character-map audit](../../tools/font_audit/README.md) now exists, with tests and [older-dump inventory](PUBLIC_FONT_AUDIT.json). It found no Georgian mappings in 56 distinct parseable font blobs. The earlier statement that font inspection is unexecuted is superseded only for that older dump, not for a matching 1.0.0.73 image. Both preceding research/discovery PRs are now merged.
