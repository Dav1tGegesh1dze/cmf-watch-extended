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

Outputs: `georgian24.font`, `georgian28.font`, `georgian32.font`, corresponding PNG previews, `manifest.json` and `OFL.txt`. These are **uncompressed 4-bpp, no-kerning** prototypes for transparent verification; they are not tuned to watch firmware memory/performance requirements. The manifest records exact generated hashes and sizes. Fonts and previews are also saved as the `georgian-font-prototype` CI artifact.

Each font contains 161 requested characters: 95 printable ASCII, 33 modern Mkhedruli (U+10D0–U+10F0), and 33 corresponding Mtavruli (U+1C90–U+1CB0). This is not every historical Georgian character or punctuation mark. Other scripts, emoji and fallback behavior are not provided.

The independent Python decoder reads the actual binary's cmap, loca, metrics and packed pixels. For every requested glyph, the build compares the decoded bitmap and metrics with the converter's separately emitted raster dump and checks for unexpected blank glyphs. Preview PNGs are drawn from the decoded binary, without a platform font fallback. This checks serialization and coverage, not execution on the watch's renderer. The unit tests also cover signed/cross-byte fields, unsupported compression, missing glyphs, truncation and PNG integrity.

## Source and license attribution

- [lv_font_conv 1.5.3](https://www.npmjs.com/package/lv_font_conv/v/1.5.3), [upstream source](https://github.com/lvgl/lv_font_conv): MIT. Used as a dependency, not copied into application code. Its bundled dependencies retain their own notices in the installed package. The npm integrity hash is pinned in `package-lock.json`.
- [Noto Sans Georgian source at 8b0a1d0](https://github.com/google/fonts/tree/8b0a1d0f5983c89bc2b93f1b5fb55f9e252744b5/ofl/notosansgeorgian): Copyright 2022 The Noto Project Authors, SIL OFL 1.1. Full notice/license is in [OFL.txt](OFL.txt) and accompanies generated artifacts. The font source hash is `dc591156f36842d38996c4a7a17fee9bb58e45da3e2cac7a31b7d33de700adb9`. Generated font derivatives remain under OFL 1.1; no license for unrelated project code is implied.
- Binary format references and the character-map parser are documented in [font_audit](../font_audit/README.md). The bitmap reader is independently implemented from those field definitions and checked against the converter output.

## What this proves

Local validation produced readable previews of `სალამი`, `გამარჯობა`, `საქართველო`, `როგორ ხარ?` and `შეტყობინება`. The three fonts are 17,820 / 23,740 / 32,040 bytes. This demonstrates that licensed Georgian glyphs can be encoded in LVGL binary format. It does **not** demonstrate that the CMF notification renderer can load these files or that a safe font-upload command exists. No firmware was modified or uploaded.
