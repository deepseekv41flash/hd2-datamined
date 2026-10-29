#!/usr/bin/env python3
"""entity_batch_set.py -- 一次 tail 宿主写入**多个组件 / 多行 / 多字段**，保内容哈希。

为什么需要
    `entity_field_set.py` 一次只写一格。给「四把武器 + 四条 rack」这种批量改造，
    逐格链式调用会让文件每次都追加一段（12 次 ≈ +100 B），而**一次写完只追加 12 B**。
    宿主越少、越接近原版形状，加载期风险越低。

定位方式（同 entity_field_set，全部现算）
    BLOCK = 容器类型 id；KEY = 该块哈希图里的键；OFF = 行内偏移。
    行号由哈希图查得，不需要知道块在文件里的位置。

用法
    python tools/entity_batch_set.py \\
        --edit "0xA98BB156:0xDDEE9646723E09D3:0x22C:2:1" \\
        --edit "0xFB8D88A3:0x9F80D67A12A7E40F:0x8C:0:5" \\
        --edit "0xFB8D88A3:0x9F80D67A12A7E40F:0x94:0:5" \\
        --out entities.plain
    每段 = BLOCK:KEY:OFF:期望旧值:新值（u32，十六进制或十进制均可）

门禁
    G1 长度 = 原长 + pad + 8      G2 差异 ⊆ 声明字段 ∪ 末块 payload 尺寸字段 ∪ 校正字
    G3 重算 Murmur == 原值        G4 全部字段读回 == 目标
    G6 容器重解析自洽             G7 全部旧值 == 期望
    G8 校正字 8 对齐且不与目标重叠 G9 追加区除校正字外全 0
"""
from __future__ import annotations

import argparse
import pathlib
import struct
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from murmur64 import murmur64, padding_word_for_hash       # noqa: E402
from pod_rack_swap import parse_blocks, check_container    # noqa: E402
from entity_field_set import row_of                        # noqa: E402
from typelib import TypeLib                                # noqa: E402

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:                                          # noqa: BLE001
        pass

PLAIN = r"D:\mod\refs\dlbin\plaintext-26251122\generated_entities.dl_bin"
TYPELIB = r"D:\mod\refs\dlbin\plaintext-26251122\dl_library.dl_typelib"
ANCHOR = 0x8E49771B181FFAA1
TAIL = 8


def main() -> int:
    ap = argparse.ArgumentParser(description="实体库批量字段写入（单次 tail 宿主保哈希）")
    ap.add_argument("--plain", default=PLAIN)
    ap.add_argument("--typelib", default=TYPELIB)
    ap.add_argument("--edit", action="append", default=[], required=True,
                    help="BLOCK:KEY:OFF:期望旧值:新值，可重复")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    original = pathlib.Path(a.plain).read_bytes()
    lib = TypeLib(open(a.typelib, "rb").read())
    h0 = murmur64(original)
    if h0 != ANCHOR:
        raise SystemExit(f"✗ 明文哈希 0x{h0:016X} != 锚点 0x{ANCHOR:016X}（base 不干净）")

    plan = []
    for spec in a.edit:
        parts = spec.split(":")
        if len(parts) != 5:
            raise SystemExit(f"✗ --edit 需要 5 段 BLOCK:KEY:OFF:OLD:NEW，收到 {spec!r}")
        blk, key, off, exp, new = (int(x, 0) for x in parts)
        row_off, stride, _r = row_of(original, lib, blk, key)
        if off + 4 > stride:
            raise SystemExit(f"✗ {spec}: 偏移 0x{off:X} 超出 stride {stride}")
        t = row_off + off
        old = struct.unpack_from("<I", original, t)[0]
        plan.append((t, blk, key, off, exp, new, old))
        flag = "" if old == exp else "   ⚠ 旧值与期望不符"
        print(f"  0x{t:07X} (块0x{blk:08X} 键0x{key:016X} +0x{off:X}): {old} -> {new}{flag}")

    pad = (8 - len(original) % 8) % 8
    tail_len = pad + TAIL
    word_at = len(original) + pad
    blocks = parse_blocks(original)
    last = blocks[-1]
    edited = bytearray(original)
    struct.pack_into("<I", edited, last["head"] + 16, last["payload"] + tail_len)
    edited += bytes(tail_len)
    for t, _b, _k, _o, _e, new, _old in plan:
        struct.pack_into("<I", edited, t, new)
    edited[word_at:word_at + TAIL] = padding_word_for_hash(bytes(edited), word_at, h0)
    print(f"校正字 @0x{word_at:X}   长度 {len(original):,} -> {len(edited):,}（+{tail_len}）")

    checks = []

    def check(tag, ok, detail=""):
        checks.append(ok)
        print(f"  {'PASS' if ok else 'FAIL'}  {tag}{('  ' + detail) if detail else ''}")

    allowed = set(range(last["head"] + 16, last["head"] + 20)) | set(range(word_at, word_at + TAIL))
    for t, *_ in plan:
        allowed |= set(range(t, t + 4))
    diff = {i for i in range(len(original)) if original[i] != edited[i]}
    appended = bytes(edited[len(original):])
    check("G1 长度 = 原长 + pad + 8", len(edited) == len(original) + tail_len)
    check("G2 差异 ⊆ 声明 ∪ payload 尺寸 ∪ 校正字", diff <= allowed,
          f"diff={len(diff)}，越界 {[hex(i) for i in sorted(diff - allowed)[:6]]}")
    got = murmur64(bytes(edited))
    check("G3 重算哈希 == 原始哈希", got == h0, f"0x{got:016X}")
    check("G4 全部字段读回 == 目标",
          all(struct.unpack_from("<I", edited, t)[0] == n for t, _b, _k, _o, _e, n, _a in plan),
          f"{len(plan)} 处")
    check("G6 容器重解析自洽", check_container(bytes(edited)) == len(blocks), f"{len(blocks)} 块")
    bad = [hex(t) for t, _b, _k, _o, e, _n, o in plan if o != e]
    check("G7 全部旧值 == 期望", not bad, f"{len(plan)} 处" + (f"，不符 {bad}" if bad else ""))
    overlap = any(t < word_at + TAIL and word_at < t + 4 for t, *_ in plan)
    check("G8 校正字 8 对齐且不与目标重叠", word_at % 8 == 0 and not overlap, f"@0x{word_at:X}")
    check("G9 追加区除校正字外全 0",
          all(b == 0 for i, b in enumerate(appended)
              if not (word_at - len(original) <= i < word_at - len(original) + TAIL)))

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
