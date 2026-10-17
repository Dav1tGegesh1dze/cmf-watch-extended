import struct
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest
from merge_font import POINTS, RANGES, Writer, decode, extend_cmap, integrate, pack_table, records


def bits(values):
    pattern = ''.join(f'{value & ((1 << width) - 1):0{width}b}' for value, width in values)
    pattern += '0' * (-len(pattern) % 8)
    return bytes(int(pattern[i:i + 8], 2) for i in range(0, len(pattern), 8))


def fixture(donor=False):
    head = bytearray(48)
    struct.pack_into('<I4sIHH', head, 0, 48, b'head', 1, 3 if donor else 4, 32)
    struct.pack_into('<Hh', head, 16, 43, -18)
    head[34:43] = bytes([0, 0, 0, 2, 6, 6, 7, 1, 0] if donor else [1, 1, 1, 2, 7, 7, 12, 1, 0])
    glyph = bits([(8 if donor else 128, 7 if donor else 12), (-1, 6 if donor else 7),
                  (-2, 6 if donor else 7), (2, 6 if donor else 7), (1, 6 if donor else 7), (1, 2), (3, 2)])
    ranges = RANGES if donor else [(65, 2)]
    count = 1 + sum(length for _, length in ranges)
    headers, index = [], 1
    for start, length in ranges:
        headers.append(struct.pack('<IIHHHBB', 0, start, length, index, length, 2, 0))
        index += length
    cmap = pack_table(b'cmap', struct.pack('<I', len(headers)) + b''.join(headers))
    loca = pack_table(b'loca', struct.pack('<I', count) + struct.pack('<' + ('H' if donor else 'I') * count,
                      8, *[8 + i * len(glyph) for i in range(count - 1)]))
    glyf = pack_table(b'glyf', glyph * (count - 1))
    # One synthetic pair (A,B), negative kerning.
    kern = pack_table(b'kern', b'\0' * 4 + struct.pack('<IHHb', 1, 1, 2, -3))
    return bytes(head) + cmap + loca + glyf + (b'' if donor else kern)


class IntegrationTests(unittest.TestCase):
    def test_extension_preserves_old_and_decodes_new(self):
        base, donor = fixture(), fixture(True)
        output, report = integrate(base, donor)
        self.assertEqual(report['added_glyphs'], 66)
        self.assertEqual(report['preserved_mappings'], 2)
        self.assertEqual(decode(output, 'AB'), decode(base, 'AB'))
        text = ''.join(map(chr, POINTS))
        self.assertEqual(decode(output, text), decode(donor, text))
        self.assertEqual(decode(output, 'ა')[0x10d0]['pixels'], [[1, 3]])
        self.assertEqual(records(output)[b'kern'], records(base)[b'kern'])

    def test_rejects_double_integration(self):
        output, _ = integrate(fixture(), fixture(True))
        with self.assertRaisesRegex(ValueError, 'overlaps'): integrate(output, fixture(True))

    def test_rejects_missing_donor_glyph(self):
        donor = bytearray(fixture(True))
        struct.pack_into('<I', donor, 64, 0x1100)
        with self.assertRaises(ValueError): integrate(fixture(), donor)

    def test_rejects_unsupported_encoding_and_kerning(self):
        for position, value in [(34, 0), (35, 0), (36, 0), (37, 4), (41, 0), (42, 1), (14, 28)]:
            base = bytearray(fixture());base[position] = value
            with self.subTest(position=position), self.assertRaises(ValueError): integrate(base, fixture(True))
        base = bytearray(fixture());base[-24 + 8] = 3
        with self.assertRaises(ValueError): integrate(base, fixture(True))

    def test_every_truncation_rejected(self):
        base = fixture()
        for end in range(len(base)):
            with self.subTest(end=end), self.assertRaises(ValueError): integrate(base[:end], fixture(True))

    def test_rejects_vertical_clipping(self):
        base = bytearray(fixture())
        struct.pack_into('<h', base, 18, -1)
        with self.assertRaisesRegex(ValueError, 'vertical'): integrate(base, fixture(True))

    def test_writer_rejects_metric_overflow(self):
        for value, count, signed in [(128, 7, False), (-1, 7, False), (-65, 7, True), (64, 7, True)]:
            with self.assertRaises(ValueError): Writer().write(value, count, signed)

    def test_cmap_relocates_existing_sparse_data(self):
        cmap = pack_table(b'cmap', struct.pack('<I', 1) + struct.pack('<IIHHHBB', 28, 65, 3, 1, 2, 3, 0) + struct.pack('<HH', 0, 2))
        result = extend_cmap(cmap, 3)
        self.assertEqual(struct.unpack_from('<I', result, 12)[0], 60)
        self.assertEqual(result[60:], cmap[28:])

    def test_cli_rejects_unpinned_input_without_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory);base = root / 'base';donor = root / 'donor';out = root / 'output'
            base.write_bytes(fixture());donor.write_bytes(fixture(True))
            result = subprocess.run([sys.executable, str(Path(__file__).with_name('merge_font.py')), str(base), str(donor), str(out)], capture_output=True)
            self.assertEqual(result.returncode, 2)
            self.assertFalse(out.exists())
            self.assertEqual(base.read_bytes(), fixture())


if __name__ == '__main__': unittest.main()
