# Read-only stock package audit

Python 3.10+, standard library. Obtain the exact authorized input documented in [the evidence report](../../docs/research/STOCK_1.0.0.73_AUDIT.md), keep it under ignored `build/`, and run:

```sh
python3 tools/firmware_audit/inspect_stock.py build/firmware-1.0.0.73/stock.bin
python3 -m unittest discover -s tools/firmware_audit -v
```

Prints JSON metadata to stdout; does not extract or modify files, download anything, or contact a device. Exit 2 means invalid input or failed validation. Only the pinned 1.0.0.73 package is accepted. A successful audit establishes internal consistency, not cryptographic authenticity or safe installation. Limits: 64 MiB input/output per partition and decompressor memory, 2 MiB output per compressed chunk, 256 SDFS entries. CRC and additive sums are not security checks.

Optional static renderer verification uses Capstone 5.0.7 from `tools/notification_font/requirements.txt`:

```sh
python3 tools/firmware_audit/trace_renderer.py build/firmware-1.0.0.73/stock.bin
```

This separately verifies selected instructions and emits metadata only. It does not prove the entire renderer control flow.
