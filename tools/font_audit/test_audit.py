import struct
import unittest
from audit import InvalidFont, audit


def record(tag, payload):
    payload += bytes((-len(payload)) % 4)
    return struct.pack('<I4s', 8 + len(payload), tag) + payload


def fixture(kind=2, start=0x10D0, length=3, base=1, entries=3, payload=b'', wide=False):
    head = bytearray(40)
    struct.pack_into('<IHH', head, 0, 1, 3, 24)
    head[26] = int(wide)
    subtable = struct.pack('<IIHHHBB', 28, start, length, base, entries, kind, 0)
    cmap = record(b'cmap', struct.pack('<I', 1) + subtable + payload)
    offsets = struct.pack('<4I' if wide else '<4H', 8, 9, 10, 11)
    loca = record(b'loca', struct.pack('<I', 4) + offsets)
    return record(b'head', bytes(head)) + cmap + loca + record(b'glyf', b'\x00\x11\x22\x33')


class AuditTest(unittest.TestCase):
    def mappings(self, blob, text='აბგდ'):
        return audit(blob, text)['fonts'][0]['mapped_glyph_ids']

    def test_contiguous_georgian_and_missing(self):
        r = audit(fixture(), 'აბგდ')['fonts'][0]
        self.assertEqual(r['mapped_glyph_ids'], {'U+10D0': 1, 'U+10D1': 2, 'U+10D2': 3})
        self.assertEqual(r['unmapped'], ['U+10D3'])

    def test_contiguous_full_uses_explicit_ids(self):
        self.assertEqual(self.mappings(fixture(kind=0, payload=bytes([2, 0, 1]))),
                         {'U+10D0': 3, 'U+10D1': 1, 'U+10D2': 2})

    def test_sparse_tiny_does_not_fill_holes(self):
        self.assertEqual(self.mappings(fixture(kind=3, entries=2, payload=struct.pack('<HH', 0, 2))),
                         {'U+10D0': 1, 'U+10D2': 2})

    def test_sparse_full_uses_explicit_ids(self):
        self.assertEqual(self.mappings(fixture(kind=1, entries=2, payload=struct.pack('<4H', 0, 2, 2, 0))),
                         {'U+10D0': 3, 'U+10D2': 1})

    def test_glyph_zero_is_undefined(self):
        self.assertNotIn('U+10D0', self.mappings(fixture(base=0)))

    def test_wide_loca_and_supplementary_unicode(self):
        self.assertEqual(self.mappings(fixture(start=0x10000, wide=True), chr(0x10000)), {'U+10000': 1})

    def test_every_truncation_fails(self):
        blob = fixture()
        for n in range(len(blob)):
            with self.subTest(n=n), self.assertRaises(InvalidFont):
                audit(blob[:n], 'ა')

    def test_no_fonts_is_unknown_not_missing(self):
        r = audit(b'not a font', 'ა', scan=True)
        self.assertEqual(r['status'], 'no_parseable_fonts')
        self.assertEqual(r['fonts'], [])

    def test_container_reports_rejections_and_valid_offsets(self):
        prefix = b'head invalid candidate'
        r = audit(prefix + fixture() + fixture(start=65), 'Aა', scan=True)
        self.assertEqual(len(r['fonts']), 2)
        self.assertEqual(r['fonts'][0]['offset'], len(prefix))
        self.assertEqual(len(r['rejected_candidates']), 1)

    def test_trailing_data_requires_scan(self):
        with self.assertRaises(InvalidFont):
            audit(fixture() + b'trailing', 'ა')

    def test_bad_offsets_counts_and_versions_fail(self):
        for offset, fmt, value in [(0, 'I', 0xffffffff), (8, 'I', 2), (12, 'H', 65535),
                                   (34, 'B', 3), (56, 'I', 4097), (60, 'I', 0xffffffff),
                                   (74, 'B', 4)]:
            blob = bytearray(fixture(kind=0, payload=bytes([0, 1, 2])))
            struct.pack_into('<' + fmt, blob, offset, value)
            with self.subTest(offset=offset), self.assertRaises(InvalidFont):
                audit(bytes(blob), 'ა')

    def test_invalid_sparse_and_glyph_ids_fail(self):
        for blob in [fixture(kind=3, entries=2, payload=struct.pack('<HH', 2, 0)),
                     fixture(kind=3, entries=2, payload=struct.pack('<HH', 0, 0)),
                     fixture(kind=3, entries=2, payload=struct.pack('<HH', 0, 4)),
                     fixture(base=65535), fixture(start=0x10ffff)]:
            with self.assertRaises(InvalidFont):
                audit(blob, 'ა')

    def test_query_limits(self):
        for text in ['', ''.join(map(chr, range(257))), '\ud800']:
            with self.assertRaises(InvalidFont):
                audit(fixture(), text)

    def test_candidate_limit_fails_instead_of_partial_success(self):
        with self.assertRaises(InvalidFont):
            audit(fixture() + b'head' * 2049, 'ა', scan=True)


if __name__ == '__main__':
    unittest.main()
