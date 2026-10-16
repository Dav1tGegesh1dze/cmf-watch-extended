# Georgian LVGL font prototype

This builds **standalone font assets**, not a firmware patch. It has no Bluetooth support, never opens a vendor firmware image, and cannot install anything on a watch. The generated fonts are not drop-in replacements for `sans32.font`: they contain a small research character set and would discard other scripts if used that way. Notification font selection, fallback, available resource space, the matching firmware and a safe installation/recovery method remain unverified.

## Build and verify

Requires Node.js 22+ and Python 3.10+. From the repository root:

```sh
npm ci --prefix tools/georgian_font --ignore-scripts --no-audit --no-fund
python3 -m unittest discover -s tools/font_audit -v
python3 -m unittest discover -s tools/georgian_font -v
python3 tools/georgian_font/build.py
```

The build fetches a pinned, SHA-256-verified Noto Sans Georgian TTF into ignored `build/georgian-font/` if it is absent. A cached checksum mismatch aborts instead of silently replacing the file. It invokes a lockfile-pinned `lv_font_conv@1.5.3` with lifecycle scripts disabled during installation.

Outputs: `georgian24.font`, `georgian28.font`, `georgian32.font`, plus `georgian24-2bpp-rle.font`, `georgian28-2bpp-rle.font` and `georgian32-2bpp-rle.font`, corresponding PNG previews, `manifest.json` and `OFL.txt`. The original files remain **uncompressed 4-bpp**; the new variants use **2-bpp RLE with row XOR prefiltering**, as observed in the older `sans32.font`. All omit kerning. Matching these two format fields does not establish compatibility with the watch's loader, memory limits or font metrics. The manifest records depth, compression, exact hashes and sizes. Fonts and previews are also saved as the `georgian-font-prototype` CI artifact.

Each font contains 161 requested characters: 95 printable ASCII, 33 modern Mkhedruli (U+10D0–U+10F0), and 33 corresponding Mtavruli (U+1C90–U+1CB0). This is not every historical Georgian character or punctuation mark. Other scripts, emoji and fallback behavior are not provided.

The independent Python decoder reads the actual binary's cmap, loca, metrics and packed pixels, including RLE and reversal of row XOR filtering. For every requested glyph, the build compares decoded pixels at the selected depth and metrics with the converter's separately emitted raster dump, and checks for unexpected blank glyphs. Preview PNGs use the decoded depth's full opacity range, without a platform font fallback. This checks serialization and coverage, not execution on the watch's renderer. Tests include RLE counter boundaries/restarts, runs crossing rows, truncation, overlong runs, missing characters and PNG integrity. Decoding supports 2/4-bpp, compression IDs 0/1/2 and no subpixel rendering; glyphs are bounded to 256×256 and a request to four million pixels. Existing character-map query limits also apply.

## Source and license attribution

- [lv_font_conv 1.5.3](https://www.npmjs.com/package/lv_font_conv/v/1.5.3), [upstream source](https://github.com/lvgl/lv_font_conv): MIT. Used as a dependency, not copied into application code. Its bundled dependencies retain their own notices in the installed package. The npm integrity hash is pinned in `package-lock.json`.
- [Noto Sans Georgian source at 8b0a1d0](https://github.com/google/fonts/tree/8b0a1d0f5983c89bc2b93f1b5fb55f9e252744b5/ofl/notosansgeorgian): Copyright 2022 The Noto Project Authors, SIL OFL 1.1. Full notice/license is in [OFL.txt](OFL.txt) and accompanies generated artifacts. The font source hash is `dc591156f36842d38996c4a7a17fee9bb58e45da3e2cac7a31b7d33de700adb9`. Generated font derivatives remain under OFL 1.1; no license for unrelated project code is implied.
- Binary format references and the character-map parser are documented in [font_audit](../font_audit/README.md). The bitmap reader is independently implemented from those field definitions and checked against the converter output.
- RLE semantics and row filtering were checked against the [pinned binary specification](https://github.com/lvgl/lv_font_conv/blob/2107ab79b615a6ff7051796fa9f7ae52f042437b/doc/font_spec.md#compression), the installed 1.5.3 converter, and [LVGL v8.3.11's decoder](https://github.com/lvgl/lvgl/blob/v8.3.11/src/font/lv_font_fmt_txt.c). These upstream projects use MIT licensing. The Python decoder was independently written; no upstream C/JavaScript implementation was copied.

## What this proves

Local validation produced readable previews of `სალამი`, `გამარჯობა`, `საქართველო`, `როგორ ხარ?` and `შეტყობინება`. The three fonts are 17,820 / 23,740 / 32,040 bytes. This demonstrates that licensed Georgian glyphs can be encoded in LVGL binary format. It does **not** demonstrate that the CMF notification renderer can load these files or that a safe font-upload command exists. No firmware was modified or uploaded.

The compressed 2-bpp variants are 7,508 / 9,624 / 12,272 bytes. Their 483 glyphs (161 per size) match the converter raster after 2-bit quantization. The three existing raw fonts still have their original hashes. Size differences combine lower bit depth with compression; they are not a measurement of compression alone. [Validation and remaining integration requirements](../../docs/research/COMPRESSED_GEORGIAN_FONTS.md) distinguish this result from watch compatibility.
