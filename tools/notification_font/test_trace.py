import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from trace import APP_BASE, APP_OFFSET, APP_SIZE, file_offset, literal_address, read_input, trace


class EvidenceBoundsTest(unittest.TestCase):
    def test_addresses_cannot_escape_app_partition(self):
        self.assertEqual(APP_OFFSET, file_offset(APP_BASE, 4))
        self.assertEqual(APP_OFFSET + APP_SIZE - 4, file_offset(APP_BASE + APP_SIZE - 4, 4))
        for address, size in [(APP_BASE - 1, 1), (APP_BASE + APP_SIZE - 3, 4),
                              (APP_BASE, 0), (APP_BASE, -1)]:
            with self.assertRaises(ValueError):
                file_offset(address, size)

    def test_thumb_pc_alignment(self):
        self.assertEqual(0x1008, literal_address(0x1000, 4))
        self.assertEqual(0x1008, literal_address(0x1002, 4))
        self.assertEqual(0x100c, literal_address(0x1004, 4))

    def test_rejects_wrong_size_and_same_size_wrong_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'synthetic.bin'
            path.write_bytes(b'not firmware')
            with self.assertRaisesRegex(ValueError, 'size'):
                read_input(path)
            with patch('trace.EXPECTED_SIZE', len(b'not firmware')):
                with self.assertRaisesRegex(ValueError, 'unsupported image'):
                    read_input(path)

    def test_direct_api_rejects_unknown_image_before_disassembly(self):
        with self.assertRaisesRegex(ValueError, 'unsupported image'):
            trace(b'not firmware')


if __name__ == '__main__':
    unittest.main()
