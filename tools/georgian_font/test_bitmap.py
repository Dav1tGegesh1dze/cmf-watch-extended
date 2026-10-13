import struct
import unittest
from bitmap import Bits, InvalidFont, decode, png_preview


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
                         {'advance': 8, 'x': -1, 'y': -2, 'width': 2, 'height': 1, 'pixels': [[0, 15]]})

    def test_missing_character_is_error_not_fallback(self):
        with self.assertRaises(InvalidFont):
            decode(fixture(), 'ბ')

    def test_rejects_compressed_subpixel_and_wrong_bpp(self):
        for offset, value in [(41, 1), (42, 1), (37, 2), (38, 32), (40, 32)]:
            data = bytearray(fixture())
            data[offset] = value
            with self.subTest(offset=offset), self.assertRaises(InvalidFont):
                decode(bytes(data), 'ა')

    def test_rejects_truncated_input(self):
        data = fixture()
        for end in range(len(data)):
            with self.subTest(end=end), self.assertRaises(InvalidFont):
                decode(data[:end], 'ა')

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
