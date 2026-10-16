"""Verify selected renderer instructions in the pinned stock package, read-only."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
from inspect_stock import STOCK_SHA256, STOCK_SIZE, directory, unpack, require


def trace(data):
    require(len(data) == STOCK_SIZE and hashlib.sha256(data).hexdigest() == STOCK_SHA256,
            'input is not the pinned stock package')
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_MCLASS
    from capstone.arm import ARM_OP_IMM, ARM_OP_MEM, ARM_REG_PC
    app = directory(unpack(directory(data)['TEMP.bin'][0]))['app.bin'][0]
    engine = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_MCLASS)
    engine.detail = True

    def read(address, size):
        offset = address - 0x10000000
        require(0 <= offset <= len(app) - size, 'address outside app')
        return app[offset:offset + size]

    def instruction(address):
        result = next(engine.disasm(read(address, 4), address, count=1), None)
        require(result is not None, 'invalid instruction')
        return result

    paths = []
    for address, path in [(0x1006a8a0, '/NAND:C/sans32.font'),
                          (0x1006a8ae, '/NAND:C/emoji28.font'),
                          (0x1006a8c0, '/NAND:A/font34R.font'),
                          (0x100df9ae, '/NAND:C/sans32.font'),
                          (0x100df9b4, '/NAND:C/emoji28.font')]:
        insn = instruction(address)
        require(insn.mnemonic.startswith('ldr') and len(insn.operands) == 2, 'literal load')
        operand = insn.operands[1]
        require(operand.type == ARM_OP_MEM and operand.mem.base == ARM_REG_PC, 'PC literal')
        pool = ((address + 4) & ~3) + operand.mem.disp
        pointer = struct.unpack('<I', read(pool, 4))[0]
        require(read(pointer, len(path) + 1) == path.encode() + b'\0', 'path mismatch')
        paths.append(dict(address=hex(address), path=path, string_address=hex(pointer)))
    calls = []
    for address, target in [(0x1006a8a2, 0x100df9a0), (0x1006a8b0, 0x10185a38),
                            (0x1006a8cc, 0x100df9a0), (0x100df9a6, 0x10185c30),
                            (0x100df9b8, 0x10185a38), (0x100df9c4, 0x10185bbc),
                            (0x10185c06, 0x101d73ee)]:
        insn = instruction(address)
        require(insn.mnemonic == 'bl' and insn.operands[0].type == ARM_OP_IMM
                and insn.operands[0].imm == target, 'call mismatch')
        calls.append(dict(address=hex(address), target=hex(target)))
    insn = instruction(0x100df9bc)
    require(insn.mnemonic == 'movw' and insn.reg_name(insn.operands[0].reg) == 'r1'
            and insn.operands[1].type == ARM_OP_IMM and insn.operands[1].imm == 0x56d7,
            'default codepoint mismatch')
    store = instruction(0x101d73f0)
    require(store.mnemonic == 'str.w' and store.reg_name(store.operands[0].reg) == 'r1'
            and store.operands[1].type == ARM_OP_MEM
            and store.reg_name(store.operands[1].mem.base) == 'r0'
            and store.operands[1].mem.disp == 0xb4, 'default storage mismatch')
    return dict(stock_sha256=STOCK_SHA256, app_sha256=hashlib.sha256(app).hexdigest(),
                inferred_runtime_base='0x10000000', path_loads=paths, direct_calls=calls,
                default_codepoint='U+56D7', default_load='0x100df9bc', default_store='0x101d73f0',
                limitations='Selected instructions only, not a full control-flow proof or hardware verification.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    args = parser.parse_args()
    try:
        with args.input.open('rb') as source:
            data = source.read(STOCK_SIZE + 1)
        print(json.dumps(trace(data), indent=2))
    except (ValueError, OSError, ImportError) as error:
        parser.exit(2, f'{error}\n')
