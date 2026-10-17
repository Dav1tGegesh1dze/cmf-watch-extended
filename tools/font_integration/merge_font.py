"""Offline Georgian font extension; no firmware packaging or device operations."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'georgian_font'))
from bitmap import Bits, bitmap_pixels, decode, png_preview
from audit import number, parse_font, require, table

BASE_SHA = '416fe976f3c9fa7e758ac156e4de27d82c01361d772a9a4ee88f36a91fc11e7e'
DONOR_SHA = '101a4038f12828f280a0c46fccc70c5250d0bf2c384dde94acd85aafa96942f6'
RANGES = [(0x10d0, 33), (0x1c90, 33)]
POINTS = [cp for start, length in RANGES for cp in range(start, start + length)]
LIMIT = 8 * 1024 * 1024


def digest(data):
    return hashlib.sha256(data).hexdigest()


def records(data):
    require(len(data) <= LIMIT, 'font size limit')
    parse_font(data, 0, [])
    result, offset = {}, 0
    for _ in range(number(data, 12, 'H') + 1):
        tag, record = table(data, offset)
        result[tag] = bytes(record)
        offset += len(record)
    require(offset == len(data), 'trailing font data')
    return result


def pack_table(tag, payload):
    payload += b'\0' * (-len(payload) % 4)
    return struct.pack('<I4s', len(payload) + 8, tag) + payload


class Writer:
    def __init__(self):
        self.bits = []

    def write(self, value, count, signed=False):
        minimum = -(1 << (count - 1)) if signed else 0
        maximum = (1 << (count - (1 if signed else 0))) - 1
        require(count > 0 and minimum <= value <= maximum, 'metric overflow')
        value &= (1 << count) - 1
        self.bits.extend((value >> i) & 1 for i in range(count - 1, -1, -1))

    def finish(self):
        self.bits.extend([0] * (-len(self.bits) % 8))
        return bytes(sum(bit << (7 - i) for i, bit in enumerate(self.bits[p:p + 8]))
                     for p in range(0, len(self.bits), 8))


def recode(blob, source, target):
    require(source[37] == target[37] and source[41:43] == target[41:43], 'bitmap format mismatch')
    bits = Bits(blob)
    advance = bits.read(source[40]) if source[40] else number(source, 30, 'H')
    scale = 16 if source[36] else 1
    target_scale = 16 if target[36] else 1
    require(advance * target_scale % scale == 0, 'advance precision loss')
    x, y = bits.read(source[38], True), bits.read(source[38], True)
    width, height = bits.read(source[39]), bits.read(source[39])
    start = bits.position
    bitmap_pixels(bits, width, height, source[37], source[41])
    end = bits.position
    writer = Writer()
    writer.write(advance * target_scale // scale, target[40])
    for value in (x, y): writer.write(value, target[38], True)
    for value in (width, height): writer.write(value, target[39])
    bits.position = start
    for _ in range(end - start): writer.write(bits.read(1), 1)
    return writer.finish()


def extend_cmap(cmap, first_id):
    count = number(cmap, 8)
    headers = [list(struct.unpack_from('<IIHHHBB', cmap, 12 + 16 * i)) for i in range(count)]
    shift = 16 * len(RANGES)
    for header in headers:
        for start, length in RANGES:
            require(header[1] + header[2] <= start or header[1] >= start + length,
                    'Georgian range overlaps existing cmap')
        if header[0]: header[0] += shift
    for start, length in RANGES:
        headers.append([0, start, length, first_id, length, 2, 0])
        first_id += length
    headers.sort(key=lambda h: h[1])
    return pack_table(b'cmap', struct.pack('<I', len(headers)) +
                      b''.join(struct.pack('<IIHHHBB', *h) for h in headers) + cmap[12 + 16 * count:])


def integrate(base, donor):
    """Structural worker for synthetic tests; CLI additionally pins both inputs."""
    original, extra = records(base), records(donor)
    head, source = original[b'head'], extra[b'head']
    require(head[34:38] == bytes([1, 1, 1, 2]) and head[40] > 0 and head[41:43] == b'\x01\0', 'unsupported base encoding')
    require(source[36] in (0, 1) and number(head, 14, 'H') == number(source, 14, 'H'), 'font size/advance mismatch')
    require(b'kern' in original and original[b'kern'][8] == 0, 'only pair kerning supported')
    count = number(original[b'loca'], 8)
    require(count + len(POINTS) <= 65536, 'glyph ID overflow')
    mapping = parse_font(donor, 0, POINTS)
    require(not mapping['unmapped'], 'donor missing Georgian')
    glyf = bytearray(original[b'glyf'])
    positions = [number(original[b'loca'], 12 + i * 4) for i in range(count)]
    donor_count = number(extra[b'loca'], 8)
    fmt, size = ('H', 2) if source[34] == 0 else ('I', 4)
    offsets = [number(extra[b'loca'], 12 + i * size, fmt) for i in range(donor_count)] + [len(extra[b'glyf'])]
    for cp in POINTS:
        glyph = mapping['mapped_glyph_ids'][f'U+{cp:04X}']
        positions.append(len(glyf))
        glyf.extend(recode(extra[b'glyf'][offsets[glyph]:offsets[glyph + 1]], source, head))
    glyf.extend(b'\0' * (-len(glyf) % 4))
    struct.pack_into('<I', glyf, 0, len(glyf))
    output = (head + extend_cmap(original[b'cmap'], count) +
              pack_table(b'loca', struct.pack('<I', len(positions)) + struct.pack('<' + 'I' * len(positions), *positions)) +
              glyf + original[b'kern'])
    updated = records(output)
    require(updated[b'head'] == head and updated[b'kern'] == original[b'kern'], 'header/kerning changed')
    require(updated[b'glyf'][4:len(original[b'glyf'])] == original[b'glyf'][4:], 'old glyph bytes changed')
    require(updated[b'loca'][12:12 + count * 4] == original[b'loca'][12:12 + count * 4], 'old glyph offsets changed')
    old_points = []
    cmap = original[b'cmap']
    for i in range(number(cmap, 8)):
        _, start, length, *_ = struct.unpack_from('<IIHHHBB', cmap, 12 + i * 16)
        old_points.extend(range(start, start + length))
    before = parse_font(base, 0, old_points)
    after = parse_font(output, 0, old_points)
    require(before['mapped_glyph_ids'] == after['mapped_glyph_ids'] and before['unmapped'] == after['unmapped'], 'old mappings changed')
    text = ''.join(map(chr, POINTS))
    added = decode(output, text)
    require(added == decode(donor, text), 'new glyph pixels/metrics changed')
    ascent, descent = number(head, 16, 'H'), number(head, 18, 'h')
    require(all(g['y'] >= descent and g['y'] + g['height'] <= ascent for g in added.values()),
            'new glyph exceeds original vertical line metrics')
    report = dict(base_sha256=digest(base), donor_sha256=digest(donor), output_sha256=digest(output),
                  base_bytes=len(base), output_bytes=len(output), added_bytes=len(output) - len(base),
                  preserved_glyphs=count, preserved_mappings=len(before['mapped_glyph_ids']), added_glyphs=len(POINTS),
                  preserved_header=True, preserved_kerning=True, preserved_original_glyph_bytes=True,
                  new_glyph_pixels_and_metrics_match=True, ranges=['U+10D0–U+10F0', 'U+1C90–U+1CB0'],
                  scope='Offline font candidate only; not a flashable package or hardware-verified fix.')
    return bytes(output), report


def read(path):
    with path.open('rb') as source: data = source.read(LIMIT + 1)
    require(len(data) <= LIMIT, 'input limit')
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('base', type=Path)
    parser.add_argument('donor', type=Path)
    parser.add_argument('output_directory', type=Path)
    args = parser.parse_args()
    try:
        base, donor = read(args.base), read(args.donor)
        require(digest(base) == BASE_SHA and digest(donor) == DONOR_SHA, 'input hash mismatch')
        output, report = integrate(base, donor)
        lines = ['ABC 123', 'სალამი', 'გამარჯობა', 'საქართველო', 'როგორ ხარ?', 'შეტყობინება', 'ᲒᲐᲛᲐᲠᲯᲝᲑᲐ']
        preview = png_preview(decode(output, ''.join(lines)), lines)
        # A new directory prevents accidental overwrite of inputs or previous results.
        args.output_directory.mkdir(parents=True, exist_ok=False)
        (args.output_directory / 'sans32-georgian.font').write_bytes(output)
        (args.output_directory / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
        (args.output_directory / 'preview.png').write_bytes(preview)
        print(json.dumps(report, indent=2))
    except (ValueError, OSError) as error:
        parser.exit(2, f'{error}\n')


if __name__ == '__main__': main()
