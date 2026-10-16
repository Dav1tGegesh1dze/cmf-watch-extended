# Branch investigation and Georgian font prototype

Date: 2026-10-13. Goal: a native Georgian notification fix on Watch Pro 2 firmware 1.0.0.73. The owner's observed ASCII/Georgian difference is recorded in GEORGIAN_SUPPORT.md. The goal remains unfinished.

## Branch findings

- `joshuapassos/CMF-Watch-Pro-2-BLE-Protocol`, `claude/fmc-repo-coverage-8on4vf`: behind main with no additional files in the GitHub comparison. No forks were returned by the fork query.
- `whatotter/cmf-watch-firmware`, **flashing** at [`e823ab513c92f3bdc07ffc25309444d943adffd2`](https://github.com/whatotter/cmf-watch-firmware/tree/e823ab513c92f3bdc07ffc25309444d943adffd2): ahead of main, includes named fonts, unpack/repack tools and an OTA flasher. Its README explicitly lists successful flashing of modified/repacked firmware as missing. Its manifest still identifies the August 2024 image. No flasher/repacker was run or copied; no license permitting code reuse was found in the tree.
- The `vladyud/cmf-watch-firmware` fork's main compared identical to upstream main.
- `Bendy3192/reCMF`, `claude/cmf-watch-pro-poisonfit-apdhqr`: identical to main in the comparison. Reviewed release assets are app APKs and release notes, not a matching stock firmware image. It is AGPL-3.0; no code was copied.
- `freethinkel/fmc`, `fmc(glyph-metrics)` and `fmc(font-numbers)`: behind main in the comparisons. Watchface glyph work is not a global notification-font installer. Its AGPL code was not copied.
- `tirodz/CMF-Ringtone-Tool`: branch list contains CI, audio and CLI fixes, with no font-specific branch. The prior version-provenance gap remains.
- `ambraglow/cmfparser`: main only in the branch query; an unpacker is not evidence of a safe modified-font install.

These are observations of the branches checked, not a claim to have exhausted every repository or unpublished implementation. The recent [Gen 1 custom-firmware report](https://www.reddit.com/r/Gadgetbridge/comments/1wqoke9/i_got_a_custom_firmware_running_on_a_cmf_watch/) concerns a different model and withholds its acquisition method/binary. It cannot establish Pro 2 update acceptance or recovery safety.

## Named font inspection

Downloaded the flashing branch's named font resources into ignored local research storage. `sans32.font` is 5,320,508 bytes, SHA-256 `416fe976f3c9fa7e758ac156e4de27d82c01361d772a9a4ee88f36a91fc11e7e`; it contains 36,021 glyph entries but no mappings in the Georgian blocks checked. Its hash already appears in our older-dump inventory, so this is identification of an existing audited blob, **not independent evidence from 1.0.0.73**.

`emoji28.font` and `test.font` do not have the LVGL header expected by our parser. No coverage conclusions are drawn from their names. No vendor font bytes are committed or distributed.

## Reused licensed tools and concrete output

The [Georgian font prototype](../../tools/georgian_font/README.md) uses the MIT-licensed LVGL converter and an OFL-licensed Noto source. It generates standalone 24/28/32 px fonts, verifies all 161 selected glyphs by decoding the binary and comparing pixels to the converter raster, and renders PNG previews without phone-font fallback. These assets are not integrated into vendor firmware or the phone application.

Remaining requirements: verify matching stock firmware, identify notification font selection/fallback, retain all existing scripts when designing a future change, establish resource/checksum/space constraints and a safe installation/recovery path. Firmware modification/upload still requires separate explicit approval. Generating an independent font file does not satisfy those requirements.

## Upstream request

With the owner's authorization, posted a request for an original 1.0.0.73 OTA URL/hash or notification-font inventory: [issue comment](https://github.com/joshuapassos/CMF-Watch-Pro-2-BLE-Protocol/issues/2#issuecomment-6141536559). No response had been received at the time this report was written. No account material, device identifiers or private notification contents were shared.

### Follow-up checked 2026-10-16

[Vertexsss's comment on 2026-10-15](https://github.com/joshuapassos/CMF-Watch-Pro-2-BLE-Protocol/issues/2#issuecomment-6201236344) is another request for the stock 1.0.0.73 image, not a maintainer answer supplying it. It contains no OTA URL, SHA-256, font inventory or attached verification scripts.

The commenter reports a byte-identical stock unpack/repack flow, a version check that rejects the August 2024 public image as a downgrade, and HTTP 503 responses from `iota.nothing.tech`. These are third-party reports, not independently reproduced findings. The comment does not establish current server availability, safe modified-image installation, or a recovery mechanism. Their reported device version check was not executed by this project.

The next actionable input remains a provenance-backed stock 1.0.0.73 image or notification-font export, preferably accompanied by its SHA-256 and acquisition/version evidence. Once available, run the existing read-only font audit, identify the actual notification font and fallback behavior, and compare coverage with the standalone Georgian prototype. A successful stock round trip alone would not establish that a modified image is accepted or safe; changing version metadata is not an approved workaround.

This follow-up changes research status only. No firmware was modified or transferred, no device commands were issued, and no new upstream message was posted. Android/iOS builds and hardware tests were not run locally for this documentation update.
