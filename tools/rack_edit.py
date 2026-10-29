#!/usr/bin/env python3
"""rack_edit.py -- `HellpodRackComponentData` 任意槽位 / `spawn_payload_size` 写入（保内容哈希）。

为什么不用 `pod_rack_swap.py`
    那个工具只认 slot0 / slot1（外加 `--all-mirrors` 把 slot2/3 写成同值）。
    实验经常需要「三件不同物品」或「只改 `+556` spawn 上限」，所以这里做通用的：
    任意 `--slot N=item`（可重复）＋ `--spawn N`，一次写完。

偏移怎么来
    不写死常量：用 typelib 取 `RackAttach` 的 stride/Item 偏移，再按 rack 行几何算
    （与 `pod_rack_swap.py` 同一套推导）。`spawn_payload_size` 在行内 `+0x22C`。

门禁
    G1 长度 = 原长 + pad + 8          G2 差异 ⊆ 声明字段 ∪ 最后一块尺寸字段 ∪ 校正字
    G3 重算 Murmur64A == 锚点         G4 每个声明字段读回一致
    G5 校正字 8 对齐                  G6 容器重解析自洽
    G7 旧值 == 期望（`--expect-slot 0=0x…` / `spawn=1`）

用法
    python tools/rack_edit.py --plain r3.plain --rack 29 \
        --slot 0=0x73D84EAAE8C75342 --slot 1=0xB49756795D9B0E68 \
        --slot 2=0x88C2D09AD85A7C9F --spawn 3 --out X.plain
"""
from __future__ import annotations

import argparse
import pathlib
import struct
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from murmur64 import murmur64, padding_word_for_hash                    # noqa: E402
from pod_rack_swap import (MURMUR_ANCHOR, RackTable, TypeLib, parse_blocks,  # noqa: E402
                           TAIL, DEFAULT_PLAIN, DEFAULT_TYPELIB)

SPAWN_OFF = 0x22C          # spawn_payload_size（rack 行内）


def main() -> int:
    ap = argparse.ArgumentParser(description="投送舱 rack 任意槽位 / spawn 写入（保内容哈希）")
    ap.add_argument("--plain", default=DEFAULT_PLAIN)
    ap.add_argument("--typelib", default=DEFAULT_TYPELIB)
    ap.add_argument("--rack", type=int, required=True)
    ap.add_argument("--slot", action="append", default=[], help="N=item十六进制，可重复")
    ap.add_argument("--spawn", type=int, default=None, help="新的 spawn_payload_size（+0x22C）")
    ap.add_argument("--expect-slot", action="append", default=[],
                    help="N=旧值，可重复（G7）；写 `spawn=N` 可校验 +0x22C 的旧值")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    original = pathlib.Path(a.plain).read_bytes()
    lib = TypeLib(open(a.typelib, "rb").read())
    h0 = murmur64(original)
    if h0 != MURMUR_ANCHOR:
        raise SystemExit(f"✗ 明文哈希 0x{h0:016X} != 锚点 0x{MURMUR_ANCHOR:016X}（base 不是干净明文）")
    t = RackTable(original, lib)
    blocks = parse_blocks(original)
    last = blocks[-1]

    pad = (8 - len(original) % 8) % 8
    tail_len = pad + TAIL
    word_at = len(original) + pad
    edited = bytearray(original)
    struct.pack_into("<I", edited, last["head"] + 16, last["payload"] + tail_len)
    edited += bytes(tail_len)

    declared: dict[int, tuple[str, bytes, bytes]] = {}
    for spec in a.slot:
        if "=" not in spec:
            raise SystemExit(f"✗ --slot 需要 N=值，收到 {spec!r}")
        k, v = spec.split("=", 1)
        slot = int(k, 0)
        off = t.slot_offset(a.rack, slot)
        blob = struct.pack("<Q", int(v, 0) & 0xFFFFFFFFFFFFFFFF)
        old = original[off:off + 8]
        edited[off:off + 8] = blob
        declared[off] = (f"slot{slot}", old, blob)
    if a.spawn is not None:
        off = t.base + a.rack * t.stride + SPAWN_OFF
        blob = struct.pack("<I", a.spawn & 0xFFFFFFFF)
        old = original[off:off + 4]
        edited[off:off + 4] = blob
        declared[off] = ("spawn", old, blob)

    if not declared:
        raise SystemExit("✗ 没有要写的东西")

    want = {}
    for spec in a.expect_slot:
        k, v = spec.split("=", 1)
        key = "spawn" if k.strip().lower() == "spawn" else f"slot{int(k, 0)}"
        want[key] = int(v, 0)
    if want:
        bad = []
        for off, (label, old, _new) in declared.items():
            if label in want:
                got = struct.unpack("<Q", old)[0] if len(old) == 8 else struct.unpack("<I", old)[0]
                if got != want[label]:
                    bad.append((label, hex(got), hex(want[label])))
        print(f"  {'PASS' if not bad else 'FAIL'}  G7 旧值 == 期望{'  ' + str(bad) if bad else ''}")
        if bad:
            return 1

    edited[word_at:word_at + TAIL] = padding_word_for_hash(bytes(edited), word_at, h0)
    edited = bytes(edited)

    checks = []

    def check(tag, cond, detail=""):
        checks.append((tag, bool(cond)))
        print(f"  {'PASS' if cond else 'FAIL'}  {tag}{('  ' + detail) if detail else ''}")

    allowed = set()
    for off, (_l, _o, new) in declared.items():
        allowed |= set(range(off, off + len(new)))
    allowed |= set(range(last["head"] + 16, last["head"] + 20))   # entities 容器：payload 尺寸在 head+16
    allowed |= set(range(word_at, word_at + TAIL))

    print(f"rack {a.rack}  base 0x{t.base + a.rack * t.stride:X}  行跨度 {t.stride}")
    for off, (label, old, new) in sorted(declared.items()):
        fmt = "<Q" if len(new) == 8 else "<I"
        print(f"  {label:6s} @0x{off:X}  {struct.unpack(fmt, old)[0]:#x} -> {struct.unpack(fmt, new)[0]:#x}")

    diff = {i for i in range(len(original)) if original[i] != edited[i]}
    got = murmur64(edited)
    check("G1 长度 = 原长 + 对齐 + 8", len(edited) == len(original) + tail_len,
          f"{len(original):,} -> {len(edited):,}")
    check("G2 差异 ⊆ 声明字段 ∪ 尺寸字段 ∪ 校正字", diff <= allowed,
          f"diff={len(diff)} 越界={[hex(i) for i in sorted(diff - allowed)[:6]]}")
    check("G3 重算哈希 == 锚点", got == h0, f"0x{got:016X}")
    check("G4 声明字段读回一致", all(edited[o:o + len(n)] == n for o, (_l, _o, n) in declared.items()),
          f"{len(declared)} 处")
    check("G5 校正字 8 对齐", word_at % 8 == 0, f"@0x{word_at:X}")
    try:
        parse_blocks(edited)
        ok = True
    except Exception as exc:                                        # noqa: BLE001
        ok = False
        print(f"      解析失败：{exc}")
    check("G6 容器重解析自洽", ok)

    if not all(c[1] for c in checks):
        print("\n✗ 门禁未全过，不写输出")
        return 1
    out = pathlib.Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(edited)
    print(f"\n✓ 已写 {out}（{len(edited):,} B，哈希 0x{murmur64(edited):016X}）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
