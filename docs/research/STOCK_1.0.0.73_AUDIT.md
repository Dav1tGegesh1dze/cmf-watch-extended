# Stock 1.0.0.73 read-only audit

## Acquisition and identity

The [pinned Nothing Archive metadata](https://github.com/spike0en/nothing_archive/blob/b6ae0397ae66bf0387d804e0939fced0abd25e80/website/src/data/accessories_updates.json) lists Watch Pro 2 / D398 / Buizel version 1.0.0.73 with a September 19, 2025 update date and [this OTA object](https://dmen2t88o28qi.cloudfront.net/ota/1758271254329JX402_01_ATS3089C_V1.0.0.73_GPS_V10_20250913.bin). Downloaded for offline inspection on October 17, 2026 (Tbilisi).

The 56,903,752-byte object has SHA-256 `30903fc8ce6db4f8860bb554366635db3d2bcbb2d43827b3b50fbbac22b59353`. Its manifest identifies board `jx402_01_3089c` and build `1.00_2509131556`; the contained application includes the null-terminated version string `1.0.0.73`. These are mutually consistent identity observations, not independent signature verification or proof of equivalence to the owner's installed bytes. The digest was computed locally, not obtained from a signed vendor manifest.

## Reproducible results

[The report](STOCK_1.0.0.73_AUDIT.json) contains metadata only. The [audit tool](../../tools/firmware_audit/inspect_stock.py) requires the exact package hash, validates AOTA entry bounds/non-overlap and CRC32, decompresses bounded LZMA chunks, and checks every manifest partition size and checksum. TEMP's manifest describes its compressed container; the DATA entries describe decompressed bytes. The inner app directory CRC is also checked.

The decompressed font SDFS has nine named entries. Its trailing per-entry field matches the sum of complete little-endian 32-bit words modulo 2^32, ignoring final partial words, in all nine entries. This is an observed algorithm for this input, not a signature, documented general SDFS contract, or authorization to rebuild/install resources. Unknown fields remain uninterpreted.

`sans32.font` is 5,320,508 bytes with SHA-256 `416fe976f3c9fa7e758ac156e4de27d82c01361d772a9a4ee88f36a91fc11e7e`, identical to the named font in the older dump. None of the 144 code points in U+10A0–U+10FF and U+1C90–U+1CBF maps to a glyph. This is a named-font coverage result, not a firmware-wide claim.

Exploratory disassembly also found the message popup loading sans32 and its wrapper configuring U+56D7. A hash-bound automated trace for this newer app is still needed; the committed renderer verifier targets the older image only. Do not treat exploratory addresses as a patch recipe.

## Boundaries and next steps

The missing matching-version resource blocker is resolved for this publicly available package. The remaining work is to verify the newer renderer path reproducibly, establish a glyph-preserving integration design, and determine a supported installation/recovery route. Standalone Georgian subsets must not replace this full system font. Hardware loading, rendering, notification transport and recovery are untested. No firmware modification, flashing, connections or pairing changes occurred.

The tool is independently implemented from observed container bytes and Python's standard library, reusing our existing independently implemented LVGL character-map parser. No archive code, vendor binaries or glyph artwork are redistributed. Public availability does not establish a redistribution or modification license for vendor assets; that review remains necessary before distribution.

## Validation

Executed locally: eight synthetic parser tests, complete read-only inspection of the pinned stock package, and the existing font-audit test suite. CI runs synthetic fixtures only and never downloads proprietary firmware. Android/iOS checks are recorded by the associated PR; local firmware inspection is not a hardware test.
