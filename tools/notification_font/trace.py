"""Read-only, hash-bound evidence for the older public CMF message renderer.

This is an evidence verifier, not a general firmware analyzer or patcher.
It emits selected call/literal metadata, never binary bytes or a patched image.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path

EXPECTED_SIZE = 80_321_216
EXPECTED_SHA256 = 'a201168bc4dda50d64a248690823470f2c5b5f1012feedbc901644b615598e6b'
APP_OFFSET = 0x800
APP_SIZE = 2_445_440
APP_BASE = 0x10000000


def require(condition, message):
    if not condition:
        raise ValueError(message)


def file_offset(address, size=1):
    offset = address - APP_BASE
    require(size > 0 and 0 <= offset <= APP_SIZE - size, 'address outside app.bin')
    return APP_OFFSET + offset


def literal_address(instruction_address, displacement):
    return ((instruction_address + 4) & ~3) + displacement


def read_input(path):
    with path.open('rb') as stream:
        require(stream.seek(0, 2) == EXPECTED_SIZE, 'unexpected input size')
        stream.seek(0)
        data = stream.read(EXPECTED_SIZE + 1)
    require(len(data) == EXPECTED_SIZE, 'input changed while reading')
    require(hashlib.sha256(data).hexdigest() == EXPECTED_SHA256,
            'unsupported image: expected the audited older decompressed dump')
    return data


def trace(data):
    # Check before interpreting any fixed addresses, even when called directly.
    require(len(data) == EXPECTED_SIZE and hashlib.sha256(data).hexdigest() == EXPECTED_SHA256,
            'unsupported image')
    import zlib
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_MCLASS
    from capstone.arm import ARM_OP_IMM, ARM_OP_MEM, ARM_REG_PC

    name, offset, size, _, crc = struct.unpack_from('<16sIIII', data, 0x220)
    require(name.rstrip(b'\0') == b'app.bin' and offset == APP_OFFSET and size == APP_SIZE,
            'unexpected app partition')
    require(zlib.crc32(data[offset:offset + size]) == crc, 'app partition CRC mismatch')
    engine = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_MCLASS)
    engine.detail = True

    def instruction(address):
        offset = file_offset(address, 4)
        decoded = next(engine.disasm(data[offset:offset + 4], address, count=1), None)
        require(decoded is not None, 'cannot decode selected instruction')
        return decoded

    def call(address, expected):
        insn = instruction(address)
        require(insn.mnemonic == 'bl' and insn.operands[0].type == ARM_OP_IMM
                and insn.operands[0].imm == expected, 'unexpected call target')
        return {'address': hex(address), 'target': hex(expected)}

    def path_load(address, expected):
        insn = instruction(address)
        require(insn.mnemonic.startswith('ldr') and len(insn.operands) == 2,
                'expected literal load')
        operand = insn.operands[1]
        require(operand.type == ARM_OP_MEM and operand.mem.base == ARM_REG_PC,
                'expected PC-relative load')
        pool = literal_address(address, operand.mem.disp)
        pointer = struct.unpack_from('<I', data, file_offset(pool, 4))[0]
        start = file_offset(pointer, len(expected) + 1)
        require(data[start:start + len(expected) + 1] == expected.encode('ascii') + b'\0',
                'unexpected path literal')
        return {'address': hex(address), 'literal_pool': hex(pool),
                'string_address': hex(pointer), 'path': expected}

    paths = [path_load(*item) for item in [
        (0x1006813c, '/NAND:C/sans32.font'),
        (0x1006814a, '/NAND:C/emoji28.font'),
        (0x1006815c, '/NAND:A/font34R.font'),
        (0x100dd1ea, '/NAND:C/sans32.font'),
        (0x100dd1f0, '/NAND:C/emoji28.font'),
    ]]
    calls = [call(*item) for item in [
        (0x1006813e, 0x100dd1dc), (0x1006814c, 0x10181b60),
        (0x10068168, 0x100dd1dc), (0x100dd1e2, 0x10181d58),
        (0x100dd1f4, 0x10181b60), (0x100dd200, 0x10181ce4),
        (0x10181d2e, 0x101d3446),
        (0x10181af2, 0x1017ff60),
        (0x1017ffa2, 0x1017f418), (0x1017ffda, 0x1017f418),
        (0x1017f99c, 0x1017f418), (0x1017f9e8, 0x1017f418),
    ]]
    thresholds = []
    for address in (0x10181a3a, 0x10181ada):
        insn = instruction(address)
        require(insn.mnemonic == 'ldr' and insn.operands[1].type == ARM_OP_MEM
                and insn.operands[1].mem.base == ARM_REG_PC, 'expected threshold literal')
        pool = literal_address(address, insn.operands[1].mem.disp)
        value = struct.unpack_from('<I', data, file_offset(pool, 4))[0]
        require(value == 0x1f2ff, 'unexpected emoji threshold')
        thresholds.append({'load_address': hex(address), 'last_normal_codepoint': 'U+1F2FF'})
    default_reads = []
    for address, base in ((0x1017f9a2, 'r4'), (0x1017ffaa, 'r5')):
        insn = instruction(address)
        require(insn.mnemonic == 'ldr.w' and insn.operands[1].type == ARM_OP_MEM
                and insn.reg_name(insn.operands[1].mem.base) == base
                and insn.operands[1].mem.disp == 0xb4, 'expected default-character read')
        default_reads.append(hex(address))
    default = instruction(0x100dd1f8)
    require(default.mnemonic == 'movw' and default.reg_name(default.operands[0].reg) == 'r1'
            and default.operands[1].type == ARM_OP_IMM and default.operands[1].imm == 0x56d7,
            'unexpected default character')
    return {
        'input_sha256': EXPECTED_SHA256, 'input_bytes': len(data),
        'scope': 'Static evidence from the older image only; not verified on firmware 1.0.0.73.',
        'address_mapping': {'app_file_offset': hex(APP_OFFSET), 'app_bytes': APP_SIZE,
                            'inferred_runtime_base': hex(APP_BASE), 'app_crc32': hex(crc)},
        'path_loads': paths, 'direct_calls': calls,
        'emoji_thresholds': thresholds, 'default_character_reads': default_reads,
        'default_character': {'load_address': hex(default.address), 'codepoint': 'U+56D7'},
        'limitations': 'Selected instructions are verified, not a complete control-flow proof. '
                        'Emoji loading is not evidence of arbitrary Unicode font fallback. '
                        'No installation mechanism or safe replacement is established.',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    args = parser.parse_args()
    try:
        report = trace(read_input(args.input))
    except (OSError, ValueError, ImportError) as error:
        parser.exit(2, f'Error: {error}\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
