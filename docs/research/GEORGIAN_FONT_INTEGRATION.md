# Georgian font integration candidate

On 2026-10-17, after an explicit question requesting permission for offline font modification only, the owner instructed “Carry on and let's finish this implementation.” This was interpreted as authorizing the described local font-resource modification. It does not authorize uploading, flashing or unpairing.

## Implemented and executed

The [integration tool](../../tools/font_integration/README.md) produced a local extended copy of the named `sans32.font` from the audited stock 1.0.0.73 package. It adds 33 modern Georgian lowercase letters and 33 Mtavruli uppercase letters from the licensed 32 px prototype. It adapts the donor's metric widths and integer advances to the stock font's widths and fractional advances, while retaining the donor's compressed bitmap bitstream.

The original header, 36,021 glyph records (including reserved ID zero), 36,033 nonzero character mappings and pair-kerning table are preserved. New glyph IDs are appended, the location table grows, and two ordered, non-overlapping character-map ranges are inserted. Existing character-map payload offsets are relocated. Every original mapping is compared before/after; original glyph data, offsets and kerning are checked for byte equality. All added glyphs decode to exactly the donor pixels and metrics and fit the original ascent/descent. The donor font's Latin glyphs are not substituted for stock Latin glyphs.

The result grows from 5,320,508 to 5,327,000 bytes (+6,492), with SHA-256 `89865ff6a1dea8463779a026e8aaedf0b661492e1d780fe14fcce0982c37db8b`. Two independently executed runs produced identical output bytes. The [metadata report](GEORGIAN_FONT_INTEGRATION.json) is committed; vendor-derived output bytes and previews remain local in ignored `build/font-integration/`.

The locally viewed preview renders Latin alongside `სალამი`, `გამარჯობა`, `საქართველო`, `როგორ ხარ?`, `შეტყობინება` and Mtavruli. This is a binary-font decode on the development machine, not a screenshot from the watch.

## Validation and limits

Nine font tests cover original/new glyph decoding, kerning preservation, sparse cmap relocation, duplicate integration, missing characters, every truncation of a fixture, unsupported formats, metric overflow, vertical overflow and CLI hash rejection without output. Existing bitmap, font audit, firmware audit and older renderer tests are also run. Android and iOS builds/shared tests run through required PR checks. No hardware rendering or notification-forwarding test was run.

Five additional synthetic tests cover resource round trips, relocation, preservation, malformed containers and replacement rejection. The local SDFS builder exactly reproduces the unchanged stock input before replacing the font.

This finishes the offline font/resource-integration implementation. It does not finish watch support. The extended font cannot simply overwrite the original because it is larger. Before a device experiment, partition limits, loader assumptions, authenticity checks and a supported installation/recovery route must be established. OTA packaging/uploading and notification transport are not implemented here. The phone app remains discovery-only and official-app pairing is unchanged.

No vendor binary assets are redistributed. The donor's OFL and the converter/specification's MIT licenses have been reviewed; they provide no grant over proprietary base assets. Distribution of a derivative remains out of scope pending vendor licensing review. Flashing and unpairing still require separate explicit approval and documented hardware verification.

## Decompressed resource container

The local builder preserves all eight other files exactly, retains 64-byte alignment and zero padding, and updates the named font’s size/word sum, later offsets, container length, directory word sum and data-region word sum. Header offsets 24 and 28 match sums of complete little-endian words over the directory (bytes 32–319) and data (bytes 320–end), respectively. These observed checks are not cryptographic signatures. The unchanged stock rebuild is byte-identical, including padding.

The candidate grows from 9,513,344 to 9,519,872 bytes (+6,528 including alignment), SHA-256 `36908595dc832cc40db262d8edcabb27c423eb558ba0e401900df4850fcbbfec`. [Resource metadata](GEORGIAN_RESOURCE_INTEGRATION.json) is committed; the proprietary derivative remains ignored locally. No compressed OTA, manifest-version alteration or update transmission is produced. Device partition capacity and acceptance remain unverified.
