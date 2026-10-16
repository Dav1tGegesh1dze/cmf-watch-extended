# Static trace of the older notification renderer

Date: 2026-10-16. This closes part of the **older-image font-selection** gap. It does not establish the renderer of the owner's installed 1.0.0.73 firmware or implement a watch-font fix.

## Reproducible evidence

Input: the same 80,321,216-byte decompressed dump with SHA-256 `a201168bc4dda50d64a248690823470f2c5b5f1012feedbc901644b615598e6b`. Its nested AOTA directory contains `app.bin` at file offset `0x800`, length 2,445,440, CRC32 `0x78ae6370`. The actual bytes match that CRC.

The app header and vector table contain the Thumb entry `0x10102ec9`. Mapping the app to `0x10000000` makes independent literal references resolve exactly to the known font paths and notification strings. Addresses below are inferred runtime addresses, **not file offsets**: `file_offset = address - 0x10000000 + 0x800`. Capstone 5.0.7 in ARM Thumb/M-class mode was used for static inspection.

The [read-only verifier](../../tools/notification_font/README.md) checks selected instructions and generates [NOTIFICATION_RENDERER_TRACE.json](NOTIFICATION_RENDERER_TRACE.json). It refuses an image with a different hash.

| Observation | Static evidence | Confidence / limitation |
| --- | --- | --- |
| Message-popup handler opens `sans32.font` | Handler at `0x10068040`; load at `0x1006813c`, call to wrapper at `0x1006813e` | Direct path load and call verified. The same function references the `message_msgbox view inflated` log string. |
| Popup opens emoji support | Load at `0x1006814a`, call at `0x1006814c` to `0x10181b60` | Callee refers to emoji-specific diagnostics and stores the opened resource separately. This is not proof of arbitrary Unicode font fallback. |
| Popup also opens `font34R.font` | Load at `0x1006815c`, wrapper call at `0x10068168` | Separate font object. Do not conclude that every popup field uses the same font. |
| The `sans32` font object is attached to a style used by two text objects | Object at context `+0x28` passed at `0x100681b0`; style later attached at `0x1006820a` and `0x10068286` | Manually traced register/object flow. Semantic field names and live rendering remain unverified; these steps are not a full automated data-flow proof. |
| Common wrapper configures a default character for `sans32` | Wrapper `0x100dd1dc` compares the path, opens emoji support, loads `r1 = 0x56d7` at `0x100dd1f8`, and calls `0x10181ce4` | Selected path/call/immediate checks are automated. The default setter's diagnostics identify its purpose; it ultimately stores the code at font object `+0xb4`. |

Re-running the existing character-map audit on the named `sans32.font` (SHA-256 `416fe976f3c9fa7e758ac156e4de27d82c01361d772a9a4ee88f36a91fc11e7e`) with `ABC სალამი囗` finds Latin A/B/C, space, and U+56D7 (glyph ID 4470). It finds no mappings for U+10D0, U+10D8, U+10DA, U+10DB or U+10E1, the distinct Georgian letters in the sample.

```sh
python3 tools/font_audit/audit.py build/font-audit/sans32.font --text 'ABC სალამი囗'
```

The glyph-metrics path calls `0x1017ff60`. Its first lookup (`0x1017ffa2`) is followed by a zero-result check; on a miss it loads the configured default at `0x1017ffaa` and repeats the lookup at `0x1017ffda`. The bitmap path has the analogous lookup/default/retry sequence at `0x1017f99c`, `0x1017f9a2`, and `0x1017f9e8`. Selected call targets and default-field reads are checked by the verifier; the branch/register flow was manually inspected.

Both glyph callbacks compare the code point with `0x1f2ff` before the emoji route. Georgian Mkhedruli and Mtavruli are below that threshold and take the normal-font route in this code. Adding Georgian to `emoji28.font` alone would therefore not provide a fallback for those characters. This is a code-path finding, not a runtime test.

**Inference:** missing Georgian glyphs plus a configured U+56D7 default and a lookup retry using that default explain box-like substitution in this older renderer. We have not executed the renderer. The owner's 1.0.0.73 observation is consistent with this finding, but is not proof that the firmware versions share code or fonts.

## Consequences for implementation

Changing phone localization or UTF-8 encoding cannot add these missing font mappings. The standalone Georgian prototype demonstrates glyph serialization, but replacing `sans32.font` with that small subset would discard existing coverage. A candidate solution would need to preserve the original character set, metrics and emoji behavior, either by a verified additional fallback or by a compatible expanded font resource. Neither integration path is established yet.

The remaining prerequisites are a version-provenanced 1.0.0.73 image/font export, matching renderer analysis, resource-size and loader constraints, and a verified installation/recovery route. No font-upload API was discovered by this analysis. Offline firmware modification and flashing remain subject to the repository's separate approval requirement; no such operation was performed.

## Validation

- Executed the verifier on the exact old dump: complete hash, partition CRC and all selected instruction checks passed.
- Executed four synthetic tests covering address bounds, Thumb PC alignment, wrong input size/hash, and direct API rejection of unknown images: passed.
- Re-ran the named-font character-map audit for ASCII, Georgian and the configured default character: results above.
- Android/iOS builds and hardware rendering tests were not run locally for this offline tool. CI's platform checks are reported separately in the PR.

No vendor bytes, fonts, full disassembly or upstream implementation code are committed. The evidence report contains only selected addresses, paths and call relationships.
