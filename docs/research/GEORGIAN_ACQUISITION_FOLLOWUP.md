# Georgian rendering: acquisition and font-selection follow-up

Checked 2026-10-16. Native Georgian notification rendering remains unresolved. This investigation performed public HTTP reads and offline inspection only.

## A reachable OTA object, but still the older version

The [original researcher's OTA discovery](https://www.reddit.com/r/CMFTech/comments/1eylsuo/finally_got_the_ota_url_of_wtch_pro_2/) links to [this CloudFront object](https://d2w98c7ljypqzk.cloudfront.net/otafile/1724161837605-90.bin). A request for bytes 0–3071 returned HTTP 206 with `Content-Range: bytes 0-3071/56065096`.

- The 3,072-byte prefix has SHA-256 `51f4700b085b3a1450c86ccb659c22972f6640c4927294ff967cc31f26322b51`. This is **not a complete firmware hash**.
- Both the header and embedded manifest identify `1.00_2408181820`; the manifest identifies board `jx402_01_3089c` and version code `0x10000`.
- Its font partition metadata names `fonts.bin`, resource version `0x2B`, compressed size `0x773868`, original size `0x912900`, and checksum field `0xd5aa43a2`. These fields were read, not independently validated against a full download.

The reachable object is a useful acquisition reference, but its metadata supplies no verified mapping to 1.0.0.73. An OTA API outage does not imply that every previously published CDN object is unavailable. No API credentials, guessed object names or phone traffic interception were used.

## A newly found repository is not a new stock image

Inspected [krtkygpta/cmf-watch-2-pro-custom-firmware at 8be5877](https://github.com/krtkygpta/cmf-watch-2-pro-custom-firmware/tree/8be5877eaa7c863aa6ca9a6f9e6ede1eae7cea3b). Its `extracted.bin` Git LFS pointer specifies 80,321,216 bytes and SHA-256 `a201168bc4dda50d64a248690823470f2c5b5f1012feedbc901644b615598e6b`: exactly the older dump already audited here. We compared pointer metadata, not a newly downloaded LFS payload.

The repacker changes version metadata and a bundled watchface, not Georgian glyph coverage. Its README's installation claims do not establish a successful Georgian fix. No top-level license was present in the inspected tree; no code was copied or executed. The repacked image was not downloaded or installed.

## Concrete offline font-selection leads

Rehashed the existing older decompressed dump and searched for exact ASCII byte sequences. [NOTIFICATION_FONT_LEADS.json](NOTIFICATION_FONT_LEADS.json) records reproducible offsets and the input hash. It locates four `/NAND:A/` text-font paths, `/NAND:C/emoji28.font`, `/NAND:C/sans32.font`, and two notification-view function-name strings.

These are observed strings, not a call graph. Their presence or proximity does not prove which font renders notification text. The previously audited `sans32.font` has no Georgian mappings, but neither that result nor these offsets establishes the installed 1.0.0.73 renderer's behavior.

The next offline reverse-engineering step is to establish the executable layout/load addresses, locate references to these paths, and trace font assignment from notification layout through fallback selection. That work must distinguish older-image findings from matching-version evidence. A matching stock image or notification-font export with acquisition/version provenance remains necessary before designing a device-specific font change.

## Validation and remaining boundary

Executed: GitHub commit/tree/source inspection, CDN range read, local dump SHA-256 and exact-string inventory. No new font parser or application code was introduced. Android/iOS builds and watch tests were not run for this research change. No BLE commands, firmware edits, flashing, pairing changes, upstream messages or proprietary binary commits occurred.

The protocol repository remains at `c1e5993fffe40385bdf5e3967abaa0c25293d8f3`; its firmware-request issue still supplies no stock 1.0.0.73 image or hash. Search results and the newly inspected repository do not close that gap. This report advances provenance and analysis targets; it is not a rendering fix.
