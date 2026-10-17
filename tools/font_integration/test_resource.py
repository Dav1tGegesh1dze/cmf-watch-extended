import struct
import unittest
from resource_container import rebuild, validate
from inspect_stock import word_sum


def fixture():
    data = bytearray(256)
    struct.pack_into('<12sII8sI', data, 0, b'sdfs.bin', 2, len(data), b'', 0)
    for i, (name, start, content) in enumerate([(b'one.font', 128, b'abcd1'), (b'two.font', 192, b'xyz')]):
        struct.pack_into('<12sII8sI', data, 32 + i * 32, name, start, len(content), b'', word_sum(content))
        data[start:start + len(content)] = content
    struct.pack_into('<II', data, 24, word_sum(data[32:128]), word_sum(data[128:]))
    return bytes(data)


class ResourceTests(unittest.TestCase):
    def test_stock_round_trip(self):
        self.assertEqual(rebuild(fixture(), {}), fixture())

    def test_growing_resource_relocates_and_preserves(self):
        changed = rebuild(fixture(), {'one.font': b'g' * 70})
        files = validate(changed)
        self.assertEqual(files['one.font'][0], b'g' * 70)
        self.assertEqual(files['two.font'][0], b'xyz')
        self.assertEqual(files['two.font'][1]['offset'], 256)
        self.assertEqual(len(changed), 320)

    def test_rejects_corrupt_checksums_padding_and_unknown_fields(self):
        for position in (24, 28, 20, 52, 128, 133):
            data = bytearray(fixture());data[position] ^= 1
            with self.subTest(position=position), self.assertRaises(ValueError): validate(data)

    def test_rejects_truncated_input(self):
        for end in range(len(fixture())):
            with self.subTest(end=end), self.assertRaises(ValueError): rebuild(fixture()[:end], {})

    def test_rejects_unknown_and_empty_replacements(self):
        for replacements in ({'missing.font': b'a'}, {'one.font': b''}):
            with self.assertRaises(ValueError): rebuild(fixture(), replacements)


if __name__ == '__main__': unittest.main()
