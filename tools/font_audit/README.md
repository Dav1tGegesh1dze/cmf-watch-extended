# Offline LVGL font audit

Python 3.10+; standard library only. Reads an individual LVGL binary font or scans an already decompressed container. It never connects to a device, decompresses archives, patches firmware or writes its input. JSON is printed to stdout. Exit codes: 0 = at least one parsed font; 1 = no parseable font candidates; 2 = invalid input or resource limit. A zero exit code does **not** mean Georgian is supported.

```sh
python3 tools/font_audit/audit.py /path/to/font.font --text 'ABC სალამი'
python3 tools/font_audit/audit.py /path/to/decompressed.bin --scan --georgian-blocks > /tmp/font-audit.json
python3 -m unittest discover -s tools/font_audit -v
```

Firmware images and fonts are not bundled. Obtain an authorized input separately and preserve its provenance. Keep binaries under ignored `build/font-audit/`, never in Git. Verify the firmware version independently; the tool cannot infer it from a font.

## Interpretation

- `mapped_glyph_ids` reports mappings to nonzero glyph IDs, with IDs bounded by the location table. It does not decode glyph bitmaps, prove that the glyph depicts the intended character, or identify the font used by notifications.
- `unmapped` means no nonzero mapping for that requested code point **in that parsed font**. It is not a firmware-wide claim.
- `--scan` can find multiple copies of the same font. Compare per-font SHA-256 values; candidates are not filenames or a complete filesystem inventory.
- Rejected candidates are reported. Unsupported, compressed, XOR-encoded or absent fonts may be missed. `no_parseable_fonts` is an unknown result, never evidence of missing Georgian.
- Format-0 zero deltas follow LVGL v8.3's lookup behavior, including aliases to the first glyph. Such a mapping must not be interpreted as correct visual coverage.
- Size (128 MiB), candidate (2048), subtable (4096) and query (256 distinct code points) limits prevent unbounded parsing. Invalid offsets, overlaps between Unicode ranges, out-of-range IDs, unordered sparse maps and truncation are rejected. Bitmap and kerning validation are outside this tool's scope.

## Sources and independent implementation

The parser is independently written from the [LVGL binary font specification](https://github.com/lvgl/lv_font_conv/blob/2107ab79b615a6ff7051796fa9f7ae52f042437b/doc/font_spec.md) and checked against its header/table definitions. Lookup semantics were checked against [LVGL v8.3.11](https://github.com/lvgl/lvgl/blob/v8.3.11/src/font/lv_font_fmt_txt.c). Both upstream projects use MIT licensing; no upstream implementation code or font assets are copied here. Test fonts are tiny synthetic structures authored for the tests, not extracted vendor fonts. No licensing grant for vendor firmware is inferred from its publication.

## Public-dump result, 2026-10-13

Input: [whatotter decompressed dump at fd8c708](https://github.com/whatotter/cmf-watch-firmware/blob/fd8c7081c2e36355fdfc65391878fe57e528c456/bins/extracted.bin), 80,321,216 bytes, SHA-256 `a201168bc4dda50d64a248690823470f2c5b5f1012feedbc901644b615598e6b`.

The audit parsed 58 candidates representing 56 distinct font hashes; 45 other `head` matches were rejected. No parsed candidate maps a character in U+10A0–U+10FF or U+1C90–U+1CBF. 28 candidates map Latin A. Metadata and offsets are recorded in [PUBLIC_FONT_AUDIT.json](../../docs/research/PUBLIC_FONT_AUDIT.json). To reproduce these counts, run the container command above on the exact input and group `fonts` by SHA-256; the checked-in inventory omits per-character mappings and contains no font bytes.

**This older dump has not been established as firmware 1.0.0.73.** The result supports investigating missing glyphs; it is not proof about all fonts on the owner's watch and is not a Georgian notification fix. Matching-version resources, notification font selection and a supported installation route remain unresolved.
