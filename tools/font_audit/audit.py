#!/usr/bin/env python3
"""Read-only LVGL character-map audit. No BLE, extraction or firmware writes.

Format references and limitations: tools/font_audit/README.md.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

MAX_BYTES = 128 * 1024 * 1024
MAX_CANDIDATES = 2048
DEFAULT_TEXT = 'ABC 123 სალამი გამარჯობა საქართველო როგორ ხარ? შეტყობინება ᲒᲐᲛᲐᲠᲯᲝᲑᲐ'


class InvalidFont(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise InvalidFont(message)


def number(data, offset, fmt='I'):
    size = struct.calcsize('<' + fmt)
    require(0 <= offset <= len(data) - size, 'truncated field')
    return struct.unpack_from('<' + fmt, data, offset)[0]


def table(data, offset):
    length = number(data, offset)
    require(length >= 8 and length % 4 == 0, 'invalid table size')
    require(offset + length <= len(data), 'truncated table')
    return bytes(data[offset + 4:offset + 8]), data[offset:offset + length]


def parse_font(data, offset, codepoints):
    """Return mappings to nonzero glyph IDs, not a visual-rendering verdict."""
    tag, head = table(data, offset)
    require(tag == b'head' and len(head) >= 48, 'invalid head')
    require(number(head, 8) == 1, 'unsupported font version')
    count = number(head, 12, 'H')
    require(3 <= count <= 4, 'unsupported table count')
    require(head[34] in (0, 1), 'unsupported loca format')
    tables = {}
    end = offset + len(head)
    for _ in range(count):
        tag, record = table(data, end)
        require(tag in (b'cmap', b'loca', b'glyf', b'kern'), 'unknown table')
        require(tag not in tables, 'duplicate table')
        tables[tag] = record
        end += len(record)
    require(all(t in tables for t in (b'cmap', b'loca', b'glyf')), 'missing required table')
    loca, glyf = tables[b'loca'], tables[b'glyf']
    glyph_count = number(loca, 8)
    require(1 <= glyph_count <= 65536, 'invalid glyph count')
    width = 2 if head[34] == 0 else 4
    require(12 + glyph_count * width <= len(loca), 'truncated loca')
    positions = [number(loca, 12 + i * width, 'H' if width == 2 else 'I') for i in range(glyph_count)]
    require(all(8 <= p <= len(glyf) for p in positions), 'glyph offset outside glyf')
    require(positions == sorted(positions), 'unordered glyph offsets')

    cmap = tables[b'cmap']
    n = number(cmap, 8)
    require(1 <= n <= 4096 and 12 + n * 16 <= len(cmap), 'invalid cmap count')
    matches = {}
    previous_end = 0
    for i in range(n):
        pos = 12 + i * 16
        data_offset, start, length, base, entries, kind, reserved = struct.unpack_from('<IIHHHBB', cmap, pos)
        require(reserved == 0 and kind in (0, 1, 2, 3), 'unsupported cmap format')
        require(length > 0 and start >= previous_end and start + length <= 0x110000, 'invalid or overlapping Unicode range')
        previous_end = start + length
        if kind == 2:
            require(base + length - 1 < glyph_count, 'glyph ID outside loca')
            relative = None
        else:
            size = length if kind == 0 else entries * (4 if kind == 1 else 2)
            require(size > 0 and 12 + n * 16 <= data_offset <= len(cmap) - size, 'cmap data outside table')
            if kind == 0:
                relative = None
                require(all(base + cmap[data_offset + j] < glyph_count for j in range(length)), 'glyph ID outside loca')
            else:
                require(0 < entries <= length, 'invalid sparse count')
                relative = [number(cmap, data_offset + j * 2, 'H') for j in range(entries)]
                require(all(r < length for r in relative) and all(a < b for a, b in zip(relative, relative[1:])), 'invalid sparse codepoints')
                ids = [base + (number(cmap, data_offset + entries * 2 + j * 2, 'H') if kind == 1 else j) for j in range(entries)]
                require(all(g < glyph_count for g in ids), 'glyph ID outside loca')
                sparse = dict(zip(relative, ids))
        for cp in codepoints:
            r = cp - start
            if not 0 <= r < length:
                continue
            if kind == 2:
                glyph = base + r
            elif kind == 0:
                glyph = base + cmap[data_offset + r]
            else:
                glyph = sparse.get(r, 0)
            if glyph:
                matches[f'U+{cp:04X}'] = glyph
    return {
        'offset': offset, 'byte_length': end - offset,
        'sha256': hashlib.sha256(data[offset:end]).hexdigest(),
        'font_size_px': number(head, 14, 'H'), 'glyph_count': glyph_count,
        'mapped_glyph_ids': matches,
        'unmapped': [f'U+{cp:04X}' for cp in codepoints if f'U+{cp:04X}' not in matches],
    }


def audit(data, text, scan=False):
    require(len(data) <= MAX_BYTES, 'input exceeds 128 MiB limit')
    points = sorted(set(map(ord, text)))
    require(0 < len(points) <= 256, 'request must contain 1 to 256 distinct codepoints')
    require(all(not 0xD800 <= cp <= 0xDFFF for cp in points), 'invalid Unicode scalar')
    view = memoryview(data)
    fonts, rejected = [], []
    candidates = 0
    cursor = 0
    while True:
        marker = data.find(b'head', cursor) if scan else 4
        if marker < 0:
            break
        candidates += 1
        require(candidates <= MAX_CANDIDATES, 'too many candidates; audit aborted')
        offset = marker - 4
        try:
            font = parse_font(view, offset, points)
            if not scan:
                require(font['byte_length'] == len(data), 'trailing data; use --scan for containers')
            fonts.append(font)
        except InvalidFont as error:
            if not scan:
                raise
            rejected.append({'offset': offset, 'reason': str(error)})
        if not scan:
            break
        cursor = marker + 4
    return {
        'schema_version': 1, 'input_sha256': hashlib.sha256(data).hexdigest(),
        'input_bytes': len(data), 'mode': 'scan' if scan else 'font',
        'status': 'parsed_candidates' if fonts else 'no_parseable_fonts',
        'scope': 'Character maps only. Firmware version, completeness, notification font selection and visual rendering are unverified.',
        'requested_codepoints': [f'U+{cp:04X}' for cp in points],
        'fonts': fonts, 'rejected_candidates': rejected,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--scan', action='store_true', help='search an already decompressed container for LVGL fonts; not a completeness guarantee')
    parser.add_argument('--text', default=DEFAULT_TEXT)
    parser.add_argument('--georgian-blocks', action='store_true', help='also inspect U+10A0–U+10FF and U+1C90–U+1CBF')
    args = parser.parse_args()
    try:
        with args.input.open('rb') as source:
            data = source.read(MAX_BYTES + 1)
        text = args.text
        if args.georgian_blocks:
            text += ''.join(map(chr, range(0x10A0, 0x1100))) + ''.join(map(chr, range(0x1C90, 0x1CC0)))
        result = audit(data, text, args.scan)
    except (OSError, InvalidFont) as error:
        print(str(error), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['fonts'] else 1


if __name__ == '__main__':
    sys.exit(main())
