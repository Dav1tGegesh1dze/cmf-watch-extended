import lzma
import struct
import unittest
import zlib
from inspect_stock import directory, font_directory, inspect, unpack, word_sum


def archive():
    data = bytearray(1028)
    data[:4] = b'AOTA'
    data[1024:] = b'test'
    struct.pack_into('<16sIIII', data, 512, b'app.bin', 1024, 4, 0, zlib.crc32(b'test'))
    return data


def chunk(payload=b'test', expected=4):
    compressed = lzma.compress(payload)
    return struct.pack('<4sIII', b'LZMA', 16, len(compressed), expected) + compressed


class InspectionTests(unittest.TestCase):
    def test_directory(self):
        self.assertEqual(directory(archive())['app.bin'][0], b'test')

    def test_directory_rejections(self):
        for kind in ('crc', 'bounds', 'overlap', 'duplicate', 'magic', 'truncated'):
            data = archive()
            if kind == 'crc': data[-1] ^= 1
            if kind == 'bounds': struct.pack_into('<I', data, 532, 100)
            if kind in ('overlap', 'duplicate'):
                data[544:576] = data[512:544]
                if kind == 'overlap': data[544:552] = b'new.bin\0'
            if kind == 'magic': data[0] = 0
            if kind == 'truncated': data = data[:700]
            with self.subTest(kind=kind), self.assertRaises(ValueError): directory(data)

    def test_multiple_chunks(self):
        self.assertEqual(unpack(chunk() + chunk()), b'testtest')

    def test_chunk_rejections(self):
        cases = [b'', chunk()[:-1], chunk()[:10], chunk(expected=3), chunk(expected=5),
                 chunk(expected=2 * 1024 * 1024 + 1), b'FAIL' + chunk()[4:]]
        for data in cases:
            with self.subTest(data=data[:16]), self.assertRaises(ValueError): unpack(data)

    def test_trailing_stream(self):
        data = bytearray(chunk() + b'x')
        struct.pack_into('<I', data, 8, len(data) - 16)
        with self.assertRaises(ValueError): unpack(data)

    def test_hash_binding(self):
        with self.assertRaisesRegex(ValueError, 'pinned'): inspect(archive())

    def test_word_sum_tail_and_overflow(self):
        self.assertEqual(word_sum(b'\xff' * 4 + b'\x02\0\0\0abc'), 1)

    def test_sdfs(self):
        data = bytearray(68)
        struct.pack_into('<12sII8sI', data, 0, b'sdfs.bin', 1, 68, b'', 0)
        struct.pack_into('<12sII8sI', data, 32, b'test.font', 64, 4, b'', 1)
        data[64] = 1
        self.assertEqual(font_directory(data)['test.font'][0], b'\x01\0\0\0')
        for position, value in [(64, 2), (16, 67), (12, 255), (44, 63), (48, 5)]:
            broken = data.copy()
            broken[position] = value
            with self.subTest(position=position), self.assertRaises(ValueError): font_directory(broken)


if __name__ == '__main__':
    unittest.main()
