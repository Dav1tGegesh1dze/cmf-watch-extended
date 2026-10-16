"""Read-only, hash-bound CMF 1.0.0.73 container inspection. No extraction."""
import argparse
import hashlib
import json
import lzma
from pathlib import Path
import struct
import sys
import xml.etree.ElementTree as ET
import zlib

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'font_audit'))
from audit import parse_font

STOCK_SHA256 = '30903fc8ce6db4f8860bb554366635db3d2bcbb2d43827b3b50fbbac22b59353'
STOCK_SIZE = 56903752
LIMIT = 64 * 1024 * 1024


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def metadata(blob):
    return dict(bytes=len(blob), sha256=hashlib.sha256(blob).hexdigest(),
                crc32=f'{zlib.crc32(blob):08x}')


def name_of(raw):
    name = raw.split(b'\0', 1)[0].decode('ascii')
    require(bool(name) and all(c.isalnum() or c in '._' for c in name), 'invalid name')
    return name


def directory(data):
    require(len(data) >= 1024 and data[:4] == b'AOTA', 'invalid AOTA header')
    result, spans = {}, []
    for offset in range(512, 1024, 32):
        raw, start, size, _, crc = struct.unpack_from('<16sIIII', data, offset)
        if not raw.strip(b'\0'):
            break
        name = name_of(raw)
        require(name not in result, 'duplicate entry')
        require(start >= 1024 and 0 < size <= len(data) - start, 'entry bounds')
        require(all(start + size <= a or start >= b for a, b in spans), 'entry overlap')
        blob = data[start:start + size]
        require(zlib.crc32(blob) == crc, 'entry CRC mismatch')
        result[name] = (blob, dict(offset=start, **metadata(blob)))
        spans.append((start, start + size))
    require(bool(result), 'empty directory')
    return result


def unpack(data):
    out, pos = bytearray(), 0
    while pos < len(data):
        require(len(data) - pos >= 16, 'truncated chunk')
        magic, header, size, expected = struct.unpack_from('<4sIII', data, pos)
        require(magic == b'LZMA' and header == 16, 'invalid chunk header')
        require(0 < size <= len(data) - pos - 16, 'compressed bounds')
        require(0 < expected <= 2 * 1024 * 1024 and len(out) + expected <= LIMIT, 'output limit')
        decoder = lzma.LZMADecompressor(memlimit=LIMIT)
        chunk = decoder.decompress(data[pos + 16:pos + 16 + size], max_length=expected + 1)
        require(len(chunk) == expected and decoder.eof and not decoder.unused_data, 'chunk length/stream mismatch')
        out.extend(chunk)
        pos += 16 + size
    require(bool(out), 'empty compressed input')
    return bytes(out)


def word_sum(blob):
    """Observed field: sum complete little-endian words, ignoring tail bytes."""
    return sum(x[0] for x in struct.iter_unpack('<I', blob[:len(blob) // 4 * 4])) & 0xffffffff


def font_directory(data):
    require(len(data) >= 32, 'truncated SDFS header')
    raw, count, length, _, _ = struct.unpack_from('<12sII8sI', data)
    require(name_of(raw) == 'sdfs.bin' and length == len(data), 'invalid SDFS header')
    require(0 < count <= 256 and 32 + count * 32 <= len(data), 'SDFS count')
    result, spans = {}, []
    for i in range(count):
        raw, start, size, _, checksum = struct.unpack_from('<12sII8sI', data, 32 + i * 32)
        name = name_of(raw)
        require(name not in result, 'duplicate SDFS entry')
        require(start >= 32 + count * 32 and 0 < size <= len(data) - start, 'SDFS bounds')
        require(all(start + size <= a or start >= b for a, b in spans), 'SDFS overlap')
        blob = data[start:start + size]
        require(word_sum(blob) == checksum, 'observed SDFS word sum mismatch')
        result[name] = (blob, dict(offset=start, **metadata(blob), observed_word_sum=f'{checksum:08x}'))
        spans.append((start, start + size))
    return result


def inspect(data):
    require(len(data) == STOCK_SIZE and hashlib.sha256(data).hexdigest() == STOCK_SHA256,
            'input is not the pinned stock package')
    parts = directory(data)
    report = dict(stock=metadata(data), partitions={k: v[1] for k, v in parts.items()})
    manifest = ET.fromstring(parts['ota.xml'][0])
    report['manifest_version'] = manifest.findtext('firmware_version/version_name')
    report['board'] = manifest.findtext('firmware_version/board_name')
    require(report['manifest_version'] == '1.00_2509131556' and report['board'] == 'jx402_01_3089c', 'manifest identity')
    for entry in manifest.findall('partitions/partition'):
        name = entry.findtext('file_name')
        compressed = parts[name][0]
        require(len(compressed) == int(entry.findtext('file_size'), 0), 'manifest compressed size')
        decoded = unpack(compressed)
        report['partitions'][name]['unpacked'] = metadata(decoded)
        # TEMP manifest describes the compressed container; DATA describes unpacked bytes.
        checked = compressed if name == 'TEMP.bin' else decoded
        require(len(checked) == int(entry.findtext('orig_size'), 0), 'manifest original size')
        require(zlib.crc32(checked) == int(entry.findtext('checksum'), 0), 'manifest checksum')
        if name == 'TEMP.bin':
            app, report['app'] = directory(decoded)['app.bin']
            require(b'1.0.0.73\0' in app, 'missing internal version')
            report['internal_version'] = '1.0.0.73'
        elif name == 'fonts.bin':
            fonts = font_directory(decoded)
            report['font_files'] = {k: v[1] for k, v in fonts.items()}
            points = list(range(0x10a0, 0x1100)) + list(range(0x1c90, 0x1cc0))
            report['sans32_georgian'] = parse_font(fonts['sans32.font'][0], 0, points)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    args = parser.parse_args()
    try:
        with args.input.open('rb') as source:
            data = source.read(LIMIT + 1)
        require(len(data) <= LIMIT, 'input limit')
        print(json.dumps(inspect(data), indent=2))
    except (ValueError, OSError, lzma.LZMAError, ET.ParseError) as error:
        print(str(error), file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
