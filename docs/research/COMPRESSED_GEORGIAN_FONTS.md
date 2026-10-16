# Compressed Georgian font implementation

Date: 2026-10-17. The standalone builder now emits verified 2-bpp RLE/XOR Georgian fonts in addition to the existing 4-bpp raw prototypes. This addresses a format difference identified while tracing the older notification renderer. No vendor font or firmware image is modified.

## Results

| Size | 4-bpp raw bytes | 2-bpp RLE/XOR bytes | Characters verified in each file |
| --- | ---: | ---: | ---: |
| 24 px | 17,820 | 7,508 | 161 |
| 28 px | 23,740 | 9,624 | 161 |
| 32 px | 32,040 | 12,272 | 161 |

All 966 glyph instances across six files match the converter's separately emitted raster after quantization to the selected depth. Metrics/advance checks and nonblank-glyph checks passed. The existing 4-bpp outputs retain their prior hashes. The 32 px compressed preview was visually inspected and contains readable Georgian; all previews come from decoded font bytes, not phone font substitution. Generated hashes and license attribution are in `build/georgian-font/manifest.json` and the CI artifact.

The decoder handles raw and RLE pixels, short runs, long counters, run restarts and row XOR reconstruction. It bounds reads and decoded dimensions and rejects unsupported formats or runs exceeding glyph dimensions. CI exercises synthetic malformed inputs as well as building and comparing every prototype glyph. Implementation and reproducible commands are in [the tool README](../../tools/georgian_font/README.md).

## Older default-glyph check

Read-only local decoding of the previously audited `sans32.font` (SHA-256 `416fe976f3c9fa7e758ac156e4de27d82c01361d772a9a4ee88f36a91fc11e7e`) produced readable ASCII and a hollow-box bitmap for U+56D7. That glyph has a 26×27 bitmap and an advance of 32 px. It is the character configured by the [older renderer's default-glyph path](NOTIFICATION_RENDERER.md). The temporary preview is kept in ignored local research storage; vendor font bytes and that preview are not committed or included in artifacts.

This supplements character-map and static-code evidence with offline bitmap inspection. It is not a new test of the owner's watch or firmware 1.0.0.73, nor an independent raster reference for the vendor glyph.

## What still prevents installation

The prototype covers ASCII and modern Georgian only. Replacing the full system font would remove other scripts. The new format matches the older font's depth and compression but not its complete coverage, metrics, table widths, resource layout or verified loader constraints. It is not a drop-in font replacement.

Matching 1.0.0.73 resources and a coverage-preserving integration still need verification, along with installation/recovery behavior. The upstream request was rechecked on 2026-10-17 and still provides no matching image or hash. The ordinary phone UI cannot inject glyphs into the watch's notification renderer. Firmware modification/flashing remains a separately authorized operation.

Local validation: 15 bitmap tests passed; all six font builds and raster comparisons passed; original raw font hashes retained; compressed preview and the older default glyph inspected. Android/iOS builds and hardware tests were not run locally for this Python-only change. Required platform CI results are tracked in the PR.
