"""Independent decoder for the uncompressed LVGL prototype fonts only."""
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'font_audit'))
from audit import InvalidFont, audit, number, require, table


class Bits:
    def __init__(self, data):
        self.data = data
        self.position = 0

    def read(self, count, signed=False):
        require(0 <= count <= 32 and self.position + count <= len(self.data) * 8, 'truncated bitmap field')
        value = 0
        for _ in range(count):
            value = value * 2 + ((self.data[self.position // 8] >> (7 - self.position % 8)) & 1)
            self.position += 1
        if signed and count and value & (1 << (count - 1)):
            value -= 1 << count
        return value


def decode(data, text):
    result = audit(data, text)['fonts'][0]
    require(not result['unmapped'], 'prototype has missing characters')
    _, head = table(data, 0)
    require(head[41] == 0 and head[42] == 0, 'only raw, non-subpixel fonts are supported')
    require(head[37] == 4 and head[36] in (0, 1), 'unsupported bitmap format')
    require(all(0 < head[i] <= 16 for i in (38, 39)) and head[40] <= 16, 'unsupported metric widths')
    records = {}
    offset = len(head)
    for _ in range(number(head, 12, 'H')):
        tag, record = table(data, offset)
        records[tag] = record
        offset += len(record)
    loca, glyf = records[b'loca'], records[b'glyf']
    count = number(loca, 8)
    width = 2 if head[34] == 0 else 4
    positions = [number(loca, 12 + i * width, 'H' if width == 2 else 'I') for i in range(count)] + [len(glyf)]
    glyphs = {}
    for cp in sorted(set(map(ord, text))):
        glyph_id = result['mapped_glyph_ids'][f'U+{cp:04X}']
        bits = Bits(glyf[positions[glyph_id]:positions[glyph_id + 1]])
        advance = bits.read(head[40]) if head[40] else number(head, 30, 'H')
        x, y = bits.read(head[38], True), bits.read(head[38], True)
        w, h = bits.read(head[39]), bits.read(head[39])
        require(w <= 256 and h <= 256, 'oversized prototype glyph')
        pixels = [[bits.read(4) for _ in range(w)] for _ in range(h)]
        glyphs[cp] = {'advance': advance / (16 if head[36] else 1), 'x': x, 'y': y, 'width': w, 'height': h, 'pixels': pixels}
    return glyphs


def png_preview(glyphs, lines):
    """Render the decoded binary glyphs, not a platform substitute font."""
    import zlib
    margin, gap = 16, 16
    ascent = max(g['height'] + g['y'] for g in glyphs.values())
    descent = max(-g['y'] for g in glyphs.values())
    line_height = ascent + descent + gap
    width = int(max(sum(glyphs[ord(c)]['advance'] for c in line) for line in lines)) + margin * 2 + 16
    height = line_height * len(lines) + margin * 2
    require(0 < width <= 2048 and 0 < height <= 2048, 'preview too large')
    canvas = [bytearray(width) for _ in range(height)]
    for row, line in enumerate(lines):
        pen = float(margin)
        baseline = margin + ascent + row * line_height
        for char in line:
            g = glyphs[ord(char)]
            for dy, pixels in enumerate(g['pixels']):
                for dx, pixel in enumerate(pixels):
                    x, y = round(pen) + g['x'] + dx, baseline - g['y'] - g['height'] + dy
                    require(0 <= x < width and 0 <= y < height, 'glyph outside preview')
                    canvas[y][x] = max(canvas[y][x], pixel * 17)
            pen += g['advance']
    def chunk(tag, data):
        return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data))
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 0, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(b''.join(b'\0' + row for row in canvas))) + chunk(b'IEND', b'')
