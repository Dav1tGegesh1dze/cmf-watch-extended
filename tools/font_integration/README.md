# Offline Georgian font integration

This tool adds 66 modern Georgian letters (Mkhedruli U+10D0–U+10F0 and Mtavruli U+1C90–U+1CB0) to the audited `sans32.font`. Historical Georgian letters outside these ranges are not added. It preserves original glyph IDs, glyph data, mappings, header metrics and pair kerning. It does not create an OTA image, install anything or change phone-app behavior.

The command requires exact SHA-256 matches for the stock font and the reproducible 32 px, 2 bpp RLE prototype. Run the existing [prototype builder](../georgian_font/README.md) first. Inputs and generated vendor-derived outputs must stay under ignored `build/`, never in Git or public CI artifacts.

```sh
python3 -m unittest discover -s tools/font_integration -v
python3 tools/font_integration/merge_font.py \
  build/firmware-1.0.0.73/sans32.font \
  build/georgian-font/georgian32-2bpp-rle.font \
  build/font-integration/candidate
```

The output directory must not exist. It receives `sans32-georgian.font`, a JSON validation report and a PNG decoded from the resulting binary. The original input is never written. Input files are limited to 8 MiB. Unsupported encodings, overlapping ranges, truncated data, missing donor characters, metric overflow and vertical line-metric overflow are rejected. Exit 2 indicates an error.

The structural worker is independently implemented from the [pinned LVGL binary font specification](https://github.com/lvgl/lv_font_conv/blob/2107ab79b615a6ff7051796fa9f7ae52f042437b/doc/font_spec.md). The MIT-licensed specification/converter and OFL donor attribution are retained in the Georgian font tooling. Original pair-kerning bytes remain unchanged; no kerning pairs are added for the new letters. No vendor code or glyph bytes are included in the tests.

The public CLI deliberately rejects other font revisions. A successful run verifies offline structure, preservation and decoded pixels; it does not establish loader compatibility, memory capacity, resource-partition capacity, signature validity, or installation/recovery safety. The resulting font is larger than the original and cannot be copied over the old resource in place.

Vendor redistribution/modification licensing is unresolved. Generated derivatives remain local and are not published; the OFL donor license does not license the vendor's existing glyphs. See [the integration evidence](../../docs/research/GEORGIAN_FONT_INTEGRATION.md) for the exact boundary and pending device work.

## Local decompressed resource candidate

After generating the extended font, the companion tool can rebuild the exact pinned font filesystem locally:

```sh
python3 tools/font_integration/resource_container.py \
  build/firmware-1.0.0.73/fonts-unpacked.bin \
  build/font-integration/candidate/sans32-georgian.font \
  build/font-integration/resource
```

It first requires a byte-identical stock round trip. It preserves all other files, aligns entries to 64 bytes and updates observed word-sum fields. Both inputs are hash-bound; output must be a new directory. Inputs/outputs are bounded to 16 MiB. The resulting `fonts-georgian.sdfs` is an uncompressed local resource, not an installable OTA file. The on-watch partition size and update acceptance remain unknown.
