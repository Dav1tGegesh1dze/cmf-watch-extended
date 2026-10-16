# Notification font evidence verifier

Read-only analysis of the **older public image only**. This tool rejects every input except the exact decompressed dump previously audited by this project. It does not connect to a watch, extract secrets, modify firmware or install fonts.

```sh
python3 -m venv build/re-analysis-venv
build/re-analysis-venv/bin/pip install -r tools/notification_font/requirements.txt
python3 -m unittest discover -s tools/notification_font -v
build/re-analysis-venv/bin/python tools/notification_font/trace.py build/font-audit/public-extracted.bin
```

The input is not bundled; its provenance and hash are in [the font audit](../font_audit/README.md). JSON goes to stdout. Exit code 2 means invalid input, a missing dependency, or evidence that does not match. No output file is written by the tool.

The verifier checks the complete input hash and size, the `app.bin` partition and CRC, selected Thumb direct calls and PC-relative path loads, and the default-character immediate. Address arithmetic is bounded to the application partition. The runtime base is inferred from the image's vector/header values and consistent string references, not from a vendor linker map. Selected instructions do not constitute a complete call graph or dynamic execution proof.

Capstone 5.0.7 is an optional offline analysis dependency under its [BSD license](https://github.com/capstone-engine/capstone/blob/5.0.7/LICENSE.TXT). Its [Python API documentation](https://www.capstone-engine.org/lang_python) describes instruction and operand decoding. We invoke it as an installed dependency; no upstream implementation is copied. It is not linked into Android or iOS. CI runs the synthetic bounds/hash tests without proprietary inputs; reproduction against the actual image is a separate local check.

See [findings and limits](../../docs/research/NOTIFICATION_RENDERER.md) and the [generated evidence](../../docs/research/NOTIFICATION_RENDERER_TRACE.json). The tool intentionally does not accept an arbitrary load-address override or a different firmware version: applying these addresses to 1.0.0.73 without re-analysis would be unsafe and misleading.
