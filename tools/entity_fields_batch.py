#!/usr/bin/env python3
"""entity_fields_batch.py -- set MULTIPLE fields of one entity component row in one shot,
still preserving the whole-file Murmur "content hash" with a single 8-byte tail correction word.

Why this exists
    `entity_field_set.py` writes one field per run: each run appends pad+8 bytes and solves its own
    correction word, so a 15-field preset grows the file by 12 + 14*8 = 124 B.  Third-party file-mods
    (e.g. Slidedivers - Tribes) instead append **12 bytes total** (4 pad + one 8-byte word) for all
    edits at once -- byte-identical plaintexts are achievable with that scheme, which this tool does.

Scheme (same as entity_field_set.py / plain_edit.py)
    last block payload += pad + 8 ; append pad+8 zero bytes ; write 8-byte correction word at len+pad
    so that MurmurHash64A(whole file) == ANCHOR (untouched content id).

usage
    python tools/entity_fields_batch.py set --block 0x40EF204C --key 0x4D1C334D294DFA97 \\
        --field 0x5C=f32:0.0175 --field 0xB0=f32:0.25 --field 0xD0=f32:2.0 --out X.plain
    # exact bits (byte-exact reproduction):
        --field 0x5C=bits:0x3C8F5C29
    # read back a row:
    python tools/entity_fields_batch.py show --block ... --key ... --field 0x5C --width 32
"""
from __future__ import annotations

import argparse
import pathlib
import struct
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from murmur64 import murmur64, padding_word_for_hash      # noqa: E402
from pod_rack_swap import parse_blocks, check_container  # noqa: E402
from typelib import TypeLib                              # noqa: E402

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:                                              # noqa: BLE001
        pass

PLAIN = r"D:\mod\refs\dlbin\plaintext-26251122\generated_entities.dl_bin"
TYPELIB = r"D:\mod\refs\dlbin\plaintext-26251122\dl_library.dl_typelib"
ANCHOR = 0x8E49771B181FFAA1
TAIL = 8


def row_of(data, lib, block_tid, key):
    bl = [b for b in parse_blocks(data) if b["type_id"] == block_tid]
    if len(bl) != 1:
        raise SystemExit(f"✗ 期望恰好 1 个块 0x{block_tid:08X}，实际 {len(bl)}")
    b = bl[0]
    ms = lib.members(block_tid)
    if len(ms) < 2 or ms[0]["size64"] % 16:
        raise SystemExit(f"✗ 块 0x{block_tid:08X} 不是「哈希图 + 行数组」形态")
    slots = ms[0]["size64"]
    stride = lib.desc(ms[1]["type_id"])[3]
    body = b["head"] + 28
    r = None
    for i in range(slots // 16):
        k, v = struct.unpack_from("<QI", data, body + 16 * i)
        if k == key:
            r = v
            break
    if r is None:
        raise SystemExit(f"✗ 键 0x{key:016X} 不在块 0x{block_tid:08X} 的哈希图里")
    rows = (b["payload"] - slots) // stride
    if r >= rows:
        raise SystemExit(f"✗ 行号 {r} 越界（共 {rows} 行）")
    return body + slots + r * stride, stride, r


def parse_value(text):
    """'f32:0.25' -> 4 bytes ; 'bits:0x3E800000' -> 4 bytes ; 'u32:7' / 'i32:-1' -> 4 bytes"""
    kind, _, val = text.partition(":")
    if kind == "f32":
        return struct.pack("<f", float(val))
    if kind == "bits":
        return struct.pack("<I", int(val, 0))
    if kind == "u32":
        return struct.pack("<I", int(val, 0))
    if kind == "i32":
        return struct.pack("<i", int(val, 0))
    raise SystemExit(f"✗ 无法解析值 {text!r}（用 f32:… / bits:0x… / u32:… / i32:…）")


def main() -> int:
    ap = argparse.ArgumentParser(description="一次写同一行多个字段（tail-host 保内容哈希）")
    ap.add_argument("command", choices=["set", "show"])
    ap.add_argument("--plain", default=PLAIN)
    ap.add_argument("--typelib", default=TYPELIB)
    ap.add_argument("--block", required=True)
    ap.add_argument("--key", required=True)
    ap.add_argument("--field", action="append", default=[], help="set: 0xOFF=f32:… / show: 0xOFF")
    ap.add_argument("--width", type=int, default=32, help="show 时显示多少字节")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    original = pathlib.Path(a.plain).read_bytes()
    lib = TypeLib(open(a.typelib, "rb").read())
    h0 = murmur64(original)
    if h0 != ANCHOR:
        raise SystemExit(f"✗ 明文哈希 0x{h0:016X} != 锚点 0x{ANCHOR:016X}（base 不干净）")
    block = int(str(a.block), 0)
    key = int(str(a.key), 0)
    row_off, stride, r = row_of(original, lib, block, key)

    if a.command == "show":
        start = int(str(a.field[0]), 0) if a.field else 0
        w = min(a.width, stride - start)
        print(f"块 0x{block:08X} 键 0x{key:016X} → 行 {r} 行基址 0x{row_off:X} stride {stride}")
        for off in range(start, start + w, 4):
            u = struct.unpack_from("<I", original, row_off + off)[0]
            i = struct.unpack_from("<i", original, row_off + off)[0]
            f = struct.unpack_from("<f", original, row_off + off)[0]
            print(f"  +0x{off:03X}  u32={u:<12d} i32={i:<12d} f32={f:<14g} bits=0x{u:08X}")
        return 0

    if not a.field or not a.out:
        raise SystemExit("✗ set 需要 --field / --out")

    edits = []
    for spec in a.field:
        off_s, sep, val_s = spec.partition("=")
        if not sep:
            raise SystemExit(f"✗ --field 需形如 0x5C=f32:0.25，收到 {spec!r}")
        off = int(off_s, 0)
        blob = parse_value(val_s)
        if off + len(blob) > stride:
            raise SystemExit(f"✗ 字段 +0x{off:X}+{len(blob)} 超出 stride {stride}")
        old = original[row_off + off:row_off + off + len(blob)]
        edits.append((off, blob, old))

    pad = (8 - len(original) % 8) % 8
    tail_len = pad + TAIL
    word_at = len(original) + pad
    edited = bytearray(original)
    last = parse_blocks(original)[-1]
    struct.pack_into("<I", edited, last["head"] + 16, last["payload"] + tail_len)
    edited += bytes(tail_len)
    for off, blob, _old in edits:
        edited[row_off + off:row_off + off + len(blob)] = blob
    edited[word_at:word_at + TAIL] = padding_word_for_hash(bytes(edited), word_at, h0)

    print(f"块 0x{block:08X} 行 {r} 行基址 0x{row_off:X}")
    for off, blob, old in edits:
        if len(blob) == 4:
            oi = struct.unpack("<I", old)[0]
            ni = struct.unpack("<I", blob)[0]
            print(f"  +0x{off:03X}  0x{oi:08X} ({struct.unpack('<f', old)[0]:g})"
                  f" -> 0x{ni:08X} ({struct.unpack('<f', blob)[0]:g})")
        else:
            print(f"  +0x{off:03X}  {old.hex()} -> {blob.hex()}")
    print(f"校正字 @0x{word_at:X}  长度 {len(original):,} -> {len(edited):,}")

    checks = []

    def check(tag, cond, detail=""):
        checks.append(bool(cond))
        print(f"  {'PASS' if cond else 'FAIL'}  {tag}{('  ' + detail) if detail else ''}")

    allowed = set(range(last["head"] + 16, last["head"] + 20)) | set(range(word_at, word_at + TAIL))
    for off, blob, _ in edits:
        allowed |= set(range(row_off + off, row_off + off + len(blob)))
    diff = {i for i in range(len(original)) if original[i] != edited[i]}
    got = murmur64(bytes(edited))
    check("G1 长度 = 原长 + pad + 8", len(edited) == len(original) + tail_len)
    check("G2 差异 ⊆ 字段 ∪ payload 尺寸 ∪ 校正字", diff <= allowed,
          f"diff={len(diff)}，越界 {[hex(i) for i in sorted(diff - allowed)[:6]]}")
    check("G3 重算哈希 == 原始哈希", got == h0, f"0x{got:016X}")
    check("G4 字段读回 == 目标", all(edited[row_off + off:row_off + off + len(blob)] == blob
                                     for off, blob, _ in edits))
    check("G7 字段确实改变了", any(old != blob for _off, blob, old in edits))
    check("G8 校正字 8 对齐且不与目标重叠",
          word_at % 8 == 0 and all(not (row_off + off < word_at + TAIL and word_at < row_off + off + len(blob))
                                   for off, blob, _ in edits), f"@0x{word_at:X}")
    try:
        n = check_container(bytes(edited))
        check("G6 容器重解析自洽", n == len(parse_blocks(original)), f"{n} 块")
    except Exception as exc:                                       # noqa: BLE001
        check("G6 容器重解析自洽", False, str(exc))

    if not all(checks):
        print("\n✗ 门禁未全过，不写输出")
        return 1
    out = pathlib.Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(bytes(edited))
    print(f"\n✓ 全部门禁通过 → {out}（{len(edited):,} B）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
