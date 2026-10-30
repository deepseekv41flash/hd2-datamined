#!/usr/bin/env python3
"""entity_field_set.py -- 改 `generated_entities.dl_bin` 里**任意组件行的任意字段**，保内容哈希。

为什么需要
    `pod_rack_swap.py` 只会改投送舱槽位，`entities_modeb.py` 只认几个写死的格子。
    真正做数值实验时，目标经常是「某组件某实体键那一行的某个偏移」——
    这个工具就是那条通用原语，偏移由调用方给，其余（块定位、行定位、宿主、门禁）全部自动。

定位方式（全部现算，不写死块偏移）
    --block  组件的容器类型 id（如 0x66081072 = WeaponRoundsComponentData）
    --key    该块哈希图里的键（实体键，如 0x11C27D3BABB38956）
    行号来自哈希图，行内偏移由 --field 给（如 +0x50）。

tail 宿主（与 `plain_edit.py` / `pod_rack_swap.py` 同一套，设置表上已多次实机）
    末块 payload 尺寸 += pad+8；文件尾追加 pad+8 零字节；校正字落在 len+pad（8 对齐）。

门禁
    G1 长度 = 原长 + pad + 8      G2 差异 ⊆ 声明字段 ∪ 末块 payload 尺寸字段 ∪ 校正字
    G3 重算 Murmur == 原值        G4 字段读回 == 目标
    G6 容器重解析自洽             G7 旧值 == 期望（--expect-old；省略则只要求真的变了）
    G8 校正字 8 对齐且不与目标重叠 G9 追加区除校正字外全 0

用法
    python tools/entity_field_set.py set --block 0x66081072 --key 0x... --field 0x50 \\
        --type u32 --value 40 --expect-old 0 --out X.plain
    # 需要写多个字段时，把上一次的输出当 --plain 再跑一次（哈希已保住，可安全链式）
"""
from __future__ import annotations

import argparse
import pathlib
import struct
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from murmur64 import murmur64, padding_word_for_hash    # noqa: E402
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
FMT = {"u32": ("<I", 4), "i32": ("<i", 4), "f32": ("<f", 4), "u64": ("<Q", 8)}


def row_of(data, lib, block_tid, key):
    bl = [b for b in parse_blocks(data) if b["type_id"] == block_tid]
    if len(bl) != 1:
        raise SystemExit(f"✗ 期望恰好 1 个块 0x{block_tid:08X}，实际 {len(bl)}")
    b = bl[0]
    ms = lib.members(block_tid)
    # 允许三成员形态（哈希图 + 行数组 + 尾部平行数组），例如 0x4F2CF417 LoadoutEntry：
    # 成员2（796 B/199 槽）是行号平行的 u32 数组，不参与定位；只要求前两个成员是
    # 「16 字节槽哈希图 + 行数组」，其余成员按原样保留。
    if len(ms) < 2:
        raise SystemExit(f"✗ 块 0x{block_tid:08X} 不是「哈希图 + 行数组」形态（成员数 {len(ms)}）")
    if ms[0]["size64"] % 16:
        raise SystemExit(f"✗ 块 0x{block_tid:08X} 成员0 不是 16 字节槽哈希图（{ms[0]['size64']} B）")
    slots, stride = ms[0]["size64"], lib.desc(ms[1]["type_id"])[3]
    if len(ms) > 2:
        print(f"  注意：块 0x{block_tid:08X} 是三成员形态，尾部成员2 = {ms[2]['size64']} B（原样保留）")
    body = b["head"] + 28
    r = None
    for i in range(slots // 16):
        k, v = struct.unpack_from("<QI", data, body + 16 * i)
        if k == key:
            r = v
            break
    if r is None:
        raise SystemExit(f"✗ 键 0x{key:016X} 不在块 0x{block_tid:08X} 的哈希图里")
    rows = ms[1]["size64"] // stride
    if r >= rows:
        raise SystemExit(f"✗ 行号 {r} 越界（共 {rows} 行）")
    return body + slots + r * stride, stride, r


def main() -> int:
    ap = argparse.ArgumentParser(description="实体组件行字段写入（tail 宿主保哈希）")
    ap.add_argument("command", choices=["set", "show"])
    ap.add_argument("--plain", default=PLAIN)
    ap.add_argument("--typelib", default=TYPELIB)
    ap.add_argument("--block", required=True, help="容器类型 id，如 0x66081072")
    ap.add_argument("--key", required=True, help="实体键（哈希图键），如 0x...")
    ap.add_argument("--field", default=None, help="行内偏移（show 用；如 0x50）")
    ap.add_argument("--width", type=int, default=16, help="show 时显示多少字节")
    ap.add_argument("--type", default="u32", choices=sorted(FMT))
    ap.add_argument("--value", default=None)
    ap.add_argument("--expect-old", default=None)
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
        start = int(str(a.field), 0) if a.field else 0
        if start >= stride:
            raise SystemExit(f"✗ --field +0x{start:X} 超出 stride {stride}")
        w = min(a.width, stride - start)
        print(f"块 0x{block:08X}  键 0x{key:016X} → 行 {r}  行基址 0x{row_off:X}  stride {stride}")
        for off in range(start, start + w, 4):
            u = struct.unpack_from("<I", original, row_off + off)[0]
            i = struct.unpack_from("<i", original, row_off + off)[0]
            f = struct.unpack_from("<f", original, row_off + off)[0]
            print(f"  +0x{off:02X}  u32={u:<12d} i32={i:<12d} f32={f:g}")
        return 0

    if not (a.field and a.value is not None and a.out):
        raise SystemExit("✗ set 需要 --field / --value / --out")
    field = int(str(a.field), 0)
    fmt, width = FMT[a.type]
    if field + width > stride:
        raise SystemExit(f"✗ 字段 +0x{field:X}+{width} 超出 stride {stride}")
    new = struct.unpack(fmt, struct.pack(fmt, float(a.value) if a.type == "f32" else int(a.value, 0)))[0]
    blob = struct.pack(fmt, new)
    old = struct.unpack_from(fmt, original, row_off + field)[0]
    target = row_off + field
    print(f"块 0x{block:08X} 行 {r}  +0x{field:X} ({a.type})  0x{target:X}: {old} -> {new}")

    pad = (8 - len(original) % 8) % 8
    tail_len = pad + TAIL
    word_at = len(original) + pad
    blocks = parse_blocks(original)
    last = blocks[-1]
    edited = bytearray(original)
    struct.pack_into("<I", edited, last["head"] + 16, last["payload"] + tail_len)
    edited += bytes(tail_len)
    edited[target:target + width] = blob
    edited[word_at:word_at + TAIL] = padding_word_for_hash(bytes(edited), word_at, h0)
    print(f"校正字 @0x{word_at:X}   长度 {len(original):,} -> {len(edited):,}")

    checks = []

    def check(tag, cond, detail=""):
        checks.append((tag, bool(cond)))
        print(f"  {'PASS' if cond else 'FAIL'}  {tag}{('  ' + detail) if detail else ''}")

    allowed = set(range(target, target + width)) | set(range(last["head"] + 16, last["head"] + 20)) \
        | set(range(word_at, word_at + TAIL))
    diff = {i for i in range(len(original)) if original[i] != edited[i]}
    got = murmur64(bytes(edited))
    check("G1 长度 = 原长 + pad + 8", len(edited) == len(original) + tail_len)
    check("G2 差异 ⊆ 字段 ∪ payload 尺寸 ∪ 校正字", diff <= allowed,
          f"diff={len(diff)}，越界 {[hex(i) for i in sorted(diff - allowed)[:6]]}")
    check("G3 重算哈希 == 原始哈希", got == h0, f"0x{got:016X}")
    check("G4 字段读回 == 目标", struct.unpack_from(fmt, edited, target)[0] == new)
    if a.expect_old is not None:
        want = struct.unpack(fmt, struct.pack(fmt, float(a.expect_old) if a.type == "f32"
                                              else int(a.expect_old, 0)))[0]
        check("G7 旧值 == 期望", abs(old - want) < 1e-9 if a.type == "f32" else old == want,
              f"实际 {old} 期望 {want}")
    else:
        check("G7 字段确实改变了", old != new)
    check("G8 校正字 8 对齐且不与目标重叠",
          word_at % 8 == 0 and not (target < word_at + TAIL and word_at < target + width), f"@0x{word_at:X}")
    try:
        n = check_container(bytes(edited))
        check("G6 容器重解析自洽", n == len(blocks), f"{n} 块")
    except Exception as exc:                                       # noqa: BLE001
        check("G6 容器重解析自洽", False, str(exc))

    if not all(c[1] for c in checks):
        print("\n✗ 门禁未全过，不写输出")
        return 1
    out = pathlib.Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(bytes(edited))
    print(f"\n✓ 全部门禁通过 → {out}（{len(edited):,} B）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
