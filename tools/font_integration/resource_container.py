"""Rebuild the pinned decompressed font SDFS locally; never create an OTA image."""
import argparse
import json
from pathlib import Path
import struct
import sys
from merge_font import BASE_SHA, digest, require
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'firmware_audit'))
from inspect_stock import font_directory, word_sum

STOCK_SHA = 'f36c502dc0d35be63be0aa5037a5f53d5ca85f44da57efe86859790efa14b01f'
CANDIDATE_SHA = '89865ff6a1dea8463779a026e8aaedf0b661492e1d780fe14fcce0982c37db8b'
LIMIT = 16 * 1024 * 1024


def align64(value):
    return (value + 63) // 64 * 64


def validate(data):
    require(len(data) <= LIMIT, 'container size limit')
    files = font_directory(data)
    start = align64(32 * (len(files) + 1))
    require(data[20:24] == b'\0' * 4, 'unknown header field')
    require(word_sum(data[32:start]) == struct.unpack_from('<I', data, 24)[0], 'directory word sum mismatch')
    require(word_sum(data[start:]) == struct.unpack_from('<I', data, 28)[0], 'data word sum mismatch')
    cursor = start
    for index, (_, meta) in enumerate(files.values()):
        require(data[32 + index * 32 + 20:32 + index * 32 + 28] == b'\0' * 8, 'unknown entry fields')
        require(meta['offset'] == cursor, 'unexpected file alignment/order')
        end = cursor + meta['bytes']
        cursor = align64(end)
        require(not any(data[end:cursor]), 'nonzero padding')
    require(cursor == len(data), 'unexpected tail')
    return files


def rebuild(data, replacements):
    files = validate(data)
    require(set(replacements) <= set(files), 'unknown replacement name')
    start = align64(32 * (len(files) + 1))
    output = bytearray(data[:start])
    for index, (name, (blob, _)) in enumerate(files.items()):
        content = replacements.get(name, blob)
        require(0 < len(content) <= LIMIT - len(output), 'replacement size limit')
        offset = len(output)
        output.extend(content)
        output.extend(b'\0' * (-len(output) % 64))
        struct.pack_into('<II', output, 32 + index * 32 + 12, offset, len(content))
        struct.pack_into('<I', output, 32 + index * 32 + 28, word_sum(content))
    struct.pack_into('<I', output, 16, len(output))
    struct.pack_into('<II', output, 24, word_sum(output[32:start]), word_sum(output[start:]))
    require(len(output) <= LIMIT, 'container size limit')
    checked = validate(output)
    for name, (blob, _) in files.items():
        require(checked[name][0] == replacements.get(name, blob), 'resource preservation failed')
    return bytes(output)


def read(path):
    with path.open('rb') as stream: data = stream.read(LIMIT + 1)
    require(len(data) <= LIMIT, 'input limit')
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stock_container', type=Path)
    parser.add_argument('extended_font', type=Path)
    parser.add_argument('output_directory', type=Path)
    args = parser.parse_args()
    try:
        original, font = read(args.stock_container), read(args.extended_font)
        require(digest(original) == STOCK_SHA and digest(font) == CANDIDATE_SHA, 'input hash mismatch')
        files = validate(original)
        require(digest(files['sans32.font'][0]) == BASE_SHA, 'unexpected base font')
        require(rebuild(original, {}) == original, 'stock round trip mismatch')
        result = rebuild(original, {'sans32.font': font})
        report = dict(stock_sha256=STOCK_SHA, font_sha256=CANDIDATE_SHA, output_sha256=digest(result),
                      stock_bytes=len(original), output_bytes=len(result), added_bytes=len(result) - len(original),
                      preserved_other_files=len(files) - 1, stock_round_trip_identical=True,
                      all_observed_word_sums_valid=True,
                      scope='Decompressed font resource candidate only. No OTA packaging, transfer or hardware validation.')
        args.output_directory.mkdir(parents=True, exist_ok=False)
        (args.output_directory / 'fonts-georgian.sdfs').write_bytes(result)
        (args.output_directory / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(report, indent=2))
    except (ValueError, OSError) as error:
        parser.exit(2, f'{error}\n')


if __name__ == '__main__': main()
