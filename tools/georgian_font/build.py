#!/usr/bin/env python3
"""Build and verify standalone Georgian fonts; never opens firmware or BLE."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import urllib.request
from bitmap import decode, png_preview

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / 'tools/georgian_font'
OUTPUT = ROOT / 'build/georgian-font'
SOURCE_REVISION = '8b0a1d0f5983c89bc2b93f1b5fb55f9e252744b5'
SOURCE_URL = f'https://raw.githubusercontent.com/google/fonts/{SOURCE_REVISION}/ofl/notosansgeorgian/NotoSansGeorgian%5Bwdth%2Cwght%5D.ttf'
SOURCE_SHA256 = 'dc591156f36842d38996c4a7a17fee9bb58e45da3e2cac7a31b7d33de700adb9'
CONVERTER_VERSION = '1.5.3'
RANGES = '0x20-0x7e,0x10d0-0x10f0,0x1c90-0x1cb0'
TEXT = ''.join(map(chr, range(32, 127))) + ''.join(map(chr, range(0x10D0, 0x10F1))) + ''.join(map(chr, range(0x1C90, 0x1CB1)))
LINES = ['ABC 123', 'სალამი', 'გამარჯობა', 'საქართველო', 'როგორ ხარ?', 'შეტყობინება', 'ᲒᲐᲛᲐᲠᲯᲝᲑᲐ']


def main():
    converter = TOOL / 'node_modules/lv_font_conv'
    if not (converter / 'package.json').is_file():
        raise RuntimeError('Run npm ci --prefix tools/georgian_font --ignore-scripts first')
    if json.loads((converter / 'package.json').read_text())['version'] != CONVERTER_VERSION:
        raise RuntimeError('Unexpected converter version')
    OUTPUT.mkdir(parents=True, exist_ok=True)
    source = OUTPUT / 'source.ttf'
    if not source.exists():
        with urllib.request.urlopen(SOURCE_URL, timeout=30) as response:
            data = response.read(2 * 1024 * 1024 + 1)
        if len(data) > 2 * 1024 * 1024 or hashlib.sha256(data).hexdigest() != SOURCE_SHA256:
            raise RuntimeError('Source font checksum/size mismatch')
        source.write_bytes(data)
    if hashlib.sha256(source.read_bytes()).hexdigest() != SOURCE_SHA256:
        raise RuntimeError('Cached source font checksum mismatch; refusing to use it')
    results = []
    for size, bpp, compressed in [(size, bpp, compressed) for size in (24, 28, 32)
                                  for bpp, compressed in ((4, False), (2, True))]:
        suffix = '-2bpp-rle' if compressed else ''
        common = ['node', str(converter / 'lv_font_conv.js'), '--font', str(source), '--range', RANGES,
                  '--size', str(size), '--bpp', str(bpp), '--no-kerning']
        if not compressed:
            common.append('--no-compress')
        target = OUTPUT / f'georgian{size}{suffix}.font'
        dump = OUTPUT / f'dump{size}{suffix}'
        subprocess.run(common + ['--format', 'bin', '-o', str(target)], check=True, timeout=60)
        subprocess.run(common + ['--format', 'dump', '--full-info', '-o', str(dump)], check=True, timeout=60)
        data = target.read_bytes()
        if data[37] != bpp or data[41] != (1 if compressed else 0):
            raise RuntimeError('Converter did not produce the requested bitmap format')
        glyphs = decode(data, TEXT)
        reference = json.loads((dump / 'font_info.json').read_text())['glyphs']
        if {g['code'] for g in reference} != set(map(ord, TEXT)):
            raise RuntimeError('Converter did not produce the full required character set')
        for expected in reference:
            actual = glyphs[expected['code']]
            bbox = expected['bbox']
            if any(actual[key] != bbox[key] for key in ('x', 'y', 'width', 'height')):
                raise RuntimeError('Decoded glyph metrics differ from the converter raster')
            if actual['pixels'] != [[p >> (8 - bpp) for p in row] for row in expected['pixels']]:
                raise RuntimeError('Decoded glyph pixels differ from the converter raster')
            if abs(actual['advance'] - expected['advanceWidth']) > 0.51:
                raise RuntimeError('Decoded advance differs from converter raster')
            if expected['code'] != 32 and not any(p for row in actual['pixels'] for p in row):
                raise RuntimeError('Unexpected blank glyph')
        preview = OUTPUT / f'preview{size}{suffix}.png'
        preview.write_bytes(png_preview(glyphs, LINES))
        results.append({'size_px': size, 'bpp': bpp, 'compression': 'rle-xor' if compressed else 'raw',
                        'file': target.name, 'sha256': hashlib.sha256(data).hexdigest(),
                        'bytes': len(data), 'verified_glyphs': len(glyphs), 'preview': preview.name})
    shutil.copyfile(TOOL / 'OFL.txt', OUTPUT / 'OFL.txt')
    report = {'source_revision': SOURCE_REVISION, 'source_url': SOURCE_URL, 'source_sha256': SOURCE_SHA256,
              'converter': f'lv_font_conv@{CONVERTER_VERSION}', 'fonts': results,
              'scope': 'Standalone prototypes only. No vendor fonts replaced, no firmware modified, no device transfer or compatibility claim.'}
    (OUTPUT / 'manifest.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
