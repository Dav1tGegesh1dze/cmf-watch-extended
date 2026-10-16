import struct
import unittest
from bitmap import Bits, InvalidFont, bitmap_pixels, decode, png_preview


def bit_stream(pattern):
    pattern = pattern.replace(' ', '')
    padded = pattern + '0' * (-len(pattern) % 8)
    return Bits(bytes(int(padded[i:i + 8], 2) for i in range(0, len(padded), 8)))


def fixture():
    def record(tag, payload):
        payload += bytes(-len(payload) % 4)
        return struct.pack('<I4s', 8 + len(payload), tag) + payload
    head = bytearray(40)
    struct.pack_into('<IHH', head, 0, 1, 3, 24)
    head[29:33] = bytes([4, 3, 3, 4])
    cmap = struct.pack('<IIIHHHBB', 1, 28, 0x10D0, 1, 1, 1, 2, 0)
    return (record(b'head', bytes(head)) + record(b'cmap', cmap)
            + record(b'loca', struct.pack('<IHH', 2, 8, 8)) + record(b'glyf', bytes.fromhex('8f910f')))


class BitmapTests(unittest.TestCase):
    def test_bit_order_and_signed_value(self):
        b = Bits(bytes.fromhex('8f91'))
        self.assertEqual(b.read(4), 8)
        self.assertEqual(b.read(3, True), -1)
        self.assertEqual(b.read(3, True), -2)
        self.assertEqual(b.read(3), 2)
        self.assertEqual(b.read(3), 1)

    def test_read_bounds(self):
        for count in (-1, 9, 33):
            with self.assertRaises(InvalidFont):
                Bits(b'\0').read(count)

    def test_decodes_synthetic_raw_bitmap(self):
        self.assertEqual(decode(fixture(), 'ა')[0x10D0],
                         {'advance': 8, 'x': -1, 'y': -2, 'width': 2, 'height': 1, 'bpp': 4, 'pixels': [[0, 15]]})

    def test_missing_character_is_error_not_fallback(self):
        with self.assertRaises(InvalidFont):
            decode(fixture(), 'ბ')

    def test_rejects_unsupported_formats(self):
        for offset, value in [(41, 3), (42, 1), (37, 3), (38, 32), (40, 32)]:
            data = bytearray(fixture())
            data[offset] = value
            with self.subTest(offset=offset), self.assertRaises(InvalidFont):
                decode(bytes(data), 'ა')

    def test_rejects_truncated_input(self):
        data = fixture()
        for end in range(len(data)):
            with self.subTest(end=end), self.assertRaises(InvalidFont):
                decode(data[:end], 'ა')

    def test_rle_literals_and_short_run(self):
        # 0, 1, 1, 1, 1, 2: equal literals introduce two unary repeats, then zero.
        self.assertEqual(bitmap_pixels(bit_stream('00 01 01 110 10'), 6, 1, 2, 2),
                         [[0, 1, 1, 1, 1, 2]])

    def test_four_bit_rle_and_two_bit_raw(self):
        self.assertEqual(bitmap_pixels(bit_stream('1111 1111 0 0111'), 3, 1, 4, 2),
                         [[15, 15, 7]])
        self.assertEqual(bitmap_pixels(bit_stream('00 01 10 11'), 2, 2, 2, 0),
                         [[0, 1], [2, 3]])

    def test_rle_counter_boundaries_and_restart(self):
        for counter in (0, 1, 63):
            count = 12 + counter
            pattern = '11 11 ' + '1' * 11 + f'{counter:06b}' + '11 11 0 01'
            self.assertEqual(bitmap_pixels(bit_stream(pattern), count + 3, 1, 2, 2),
                             [[3] * (count + 2) + [1]])

    def test_runs_cross_rows_and_xor_uses_reconstructed_row(self):
        pattern = '00 11 00 00 11110'  # [0,3,0,0,0,0,0,0]
        self.assertEqual(bitmap_pixels(bit_stream(pattern), 2, 4, 2, 2),
                         [[0, 3], [0, 0], [0, 0], [0, 0]])
        self.assertEqual(bitmap_pixels(bit_stream(pattern), 2, 4, 2, 1),
                         [[0, 3], [0, 3], [0, 3], [0, 3]])

    def test_rle_consumes_from_current_bit_position(self):
        bits = bit_stream('101 00 11 10')
        bits.read(3)
        self.assertEqual(bitmap_pixels(bits, 3, 1, 2, 1), [[0, 3, 2]])

    def test_empty_bitmap_consumes_no_bits(self):
        self.assertEqual(bitmap_pixels(Bits(b''), 0, 0, 2, 1), [])

    def test_rejects_run_overflow_truncation_and_oversized_dimensions(self):
        with self.assertRaisesRegex(InvalidFont, 'exceeds'):
            bitmap_pixels(bit_stream('11 11 10'), 2, 1, 2, 2)
        # Eleven repeat flags must be followed by all six counter bits.
        with self.assertRaisesRegex(InvalidFont, 'truncated'):
            bitmap_pixels(Bits(bytes.fromhex('ffff')), 20, 1, 2, 2)
        with self.assertRaisesRegex(InvalidFont, 'truncated'):
            bitmap_pixels(Bits(b''), 1, 1, 2, 1)
        with self.assertRaisesRegex(InvalidFont, 'oversized'):
            bitmap_pixels(Bits(b''), 257, 1, 2, 1)

    def test_two_bit_png_uses_full_opacity_range(self):
        import zlib
        glyphs = {ord('ა'): {'advance': 4, 'x': 0, 'y': 0, 'width': 4, 'height': 1,
                            'bpp': 2, 'pixels': [[0, 1, 2, 3]]}}
        png = png_preview(glyphs, ['ა'])
        position = 8
        while position < len(png):
            length = struct.unpack_from('>I', png, position)[0]
            if png[position + 4:position + 8] == b'IDAT':
                self.assertIn(bytes([0, 85, 170, 255]), zlib.decompress(png[position + 8:position + 8 + length]))
                return
            position += 12 + length
        self.fail('PNG has no image data')

    def test_png_encodes_decoded_pixels(self):
        import zlib
        png = png_preview(decode(fixture(), 'ა'), ['ა'])
        self.assertEqual(png[:8], b'\x89PNG\r\n\x1a\n')
        position = 8
        types = []
        while position < len(png):
            length = struct.unpack_from('>I', png, position)[0]
            tag = png[position + 4:position + 8]
            payload = png[position + 8:position + 8 + length]
            crc = struct.unpack_from('>I', png, position + 8 + length)[0]
            self.assertEqual(crc, zlib.crc32(tag + payload))
            types.append(tag)
            if tag == b'IDAT':
                self.assertEqual(zlib.decompress(payload).count(b'\xff'), 1)
            position += 12 + length
        self.assertEqual(types, [b'IHDR', b'IDAT', b'IEND'])


if __name__ == '__main__':
    unittest.main()
