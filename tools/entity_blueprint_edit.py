#!/usr/bin/env python3
"""entity_blueprint_edit.py -- 改实体表「实体→组件」蓝图（块 0 尾部 u16 清单）里的一个组件值。

为什么需要它
    实体表第一块（type `0x80C1CA70`，payload 185,172 B）才是引擎侧的实体蓝图：
        4096 槽 × 32 B  `{u64 实体键, u64 组件表偏移, u64 组件数, u32}` （payload 前 131,072 B）
        + 尾部 u16 数组 = 各实体的**组件类型清单**（按槽序紧密排列，总数 27,050）
    实测：这套 u16 清单与各组件块自己的哈希图**逐实体精确同构**（272/272 个组件块都能找到一个
    u16 值，其"出现过的实体集合"与块的键集合完全相等），例如
        Interactable = 247,  WeaponMagazine = 5,  WeaponRounds = 119,  LoadoutEntry = 29
    教训（2026-10-31 实机）：只往组件块哈希图里插一条键、**不**改这份蓝图，引擎不会给实体
    实例化该组件（P-41 加了 Interactable 行仍无交互提示）；改蓝图后才可能生效。

做法
    1. 定位实体在块 0 的 32 B 记录 → 尾部 u16 切片（偏移是 payload 相对字节偏移）
    2. 把切片里的 `--old` 值换成 `--new` 值（整段重新升序排好，原表就是升序）
    3. tail 宿主保内容哈希（末块 payload += pad+8、文件尾补零、校正字 8 对齐）

用法
    # 给 P-41 把「百科条目」槽位换成「交互」组件（22 条 → 仍是 22 条）
    python tools/entity_blueprint_edit.py --plain X.plain \\
        --key 0xBDE1F2534280300D --old 77 --new 247 --out Y.plain

门禁
    G1 长度 = 原长 + pad + 8              G2 差异 ⊆ 目标切片 ∪ 末块尺寸字段 ∪ 校正字
    G3 重算 Murmur == 锚点                G4 切片读回（升序、新值在、旧值不在）
    G5 其余实体的切片逐条未动              G6 容器重解析自洽
    G7 旧值原本在切片里、新值原本不在
"""
from __future__ import annotations

import argparse
import pathlib
import struct
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from murmur64 import murmur64, padding_word_for_hash        # noqa: E402
from pod_rack_swap import parse_blocks, check_container     # noqa: E402

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:                                       # noqa: BLE001
        pass

PLAIN = r"D:\mod\refs\dlbin\plaintext-26251122\generated_entities.dl_bin"
ANCHOR = 0x8E49771B181FFAA1
TAIL = 8
HM_BYTES = 4096 * 32          # 块 0 前 131,072 B = 实体哈希图
BLOCK0_TID = 0x80C1CA70


def slots_of(plain: bytes):
    out = {}
    for s in range(4096):
        key, off, cnt, misc = struct.unpack_from("<QQQI", plain, 28 + 32 * s)
        if key:
            out[key] = (off, cnt, s)
    return out


def slice_of(plain: bytes, key: int):
    rec = slots_of(plain).get(key)
    if rec is None:
        raise SystemExit(f"✗ 实体键 0x{key:016X} 不在块 0 哈希图里")
    off, cnt, slot = rec
    start = 28 + off                       # 文件绝对偏移（off 是 payload 相对）
    if start < 28 + HM_BYTES or start + 2 * cnt > len(plain):
        raise SystemExit(f"✗ 切片越界：off={off} cnt={cnt}")
    vals = list(struct.unpack_from("<%dH" % cnt, plain, start))
    return slot, start, cnt, vals


def main() -> int:
    ap = argparse.ArgumentParser(description="实体蓝图（块0 u16 组件清单）单值替换")
    ap.add_argument("--plain", default=PLAIN)
    ap.add_argument("--key", required=True)
    ap.add_argument("--old", type=int, required=True, help="原组件类型值（u16）")
    ap.add_argument("--new", type=int, required=True, help="新组件类型值（u16）")
    ap.add_argument("--expect-anchor", action="store_true",
                    help="要求原文件哈希 == 本 build 锚点（默认只要求改完能自洽）")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    original = pathlib.Path(a.plain).read_bytes()
    blocks = parse_blocks(original)
    if not blocks or blocks[0]["type_id"] != BLOCK0_TID:
        raise SystemExit("✗ 第一块不是实体蓝图块 0x80C1CA70")
    h0 = murmur64(original)
    print(f"原始长度 {len(original):,}  哈希 0x{h0:016X}")
    if a.expect_anchor and h0 != ANCHOR:
        raise SystemExit(f"✗ 哈希 0x{h0:016X} != 锚点 0x{ANCHOR:016X}")

    key = int(str(a.key), 0)
    slot, start, cnt, vals = slice_of(original, key)
    print(f"实体 0x{key:016X}：槽 {slot}  切片 @0x{start:X}  {cnt} 个值")
    print(f"  原清单: {sorted(vals)}")
    if a.old not in vals:
        raise SystemExit(f"✗ 旧值 {a.old} 不在该实体的组件清单里")
    if a.new in vals:
        raise SystemExit(f"✗ 新值 {a.new} 已经在该实体的组件清单里")
    new_vals = sorted([a.new if v == a.old else v for v in vals])
    print(f"  新清单: {new_vals}")

    pad = (8 - len(original) % 8) % 8
    word_at = len(original) + pad
    tail_len = pad + TAIL
    last = blocks[-1]
    edited = bytearray(original)
    edited += bytes(tail_len)
    struct.pack_into("<I", edited, last["head"] + 16, last["payload"] + tail_len)
    struct.pack_into("<%dH" % cnt, edited, start, *new_vals)
    edited[word_at:word_at + TAIL] = padding_word_for_hash(bytes(edited), word_at, h0)
    print(f"校正字 @0x{word_at:X}   长度 {len(original):,} -> {len(edited):,}")

    checks = []

    def check(tag, cond, detail=""):
        checks.append((tag, bool(cond)))
        print(f"  {'PASS' if cond else 'FAIL'}  {tag}{('  ' + detail) if detail else ''}")

    allowed = set(range(start, start + 2 * cnt)) \
        | set(range(last["head"] + 16, last["head"] + 20)) \
        | set(range(word_at, word_at + TAIL))
    diff = {i for i in range(len(original)) if original[i] != edited[i]}
    check("G1 长度 = 原长 + pad + 8", len(edited) == len(original) + tail_len)
    check("G2 差异 ⊆ 目标切片 ∪ 尺寸字段 ∪ 校正字", diff <= allowed,
          f"diff={len(diff)}，越界 {sorted(diff - allowed)[:5]}")
    check("G3 重算哈希 == 原始哈希", murmur64(bytes(edited)) == h0)
    got = list(struct.unpack_from("<%dH" % cnt, bytes(edited), start))
    check("G4 切片读回（升序/新值在/旧值不在）",
          got == new_vals and a.new in got and a.old not in got, str(got))
    ok_other = True
    other = slots_of(original)
    other_edited = slots_of(bytes(edited))
    for k in other:
        if k == key:
            continue
        o1 = other[k]
        o2 = other_edited.get(k)
        if o2 is None:
            ok_other = False
            break
        s1 = list(struct.unpack_from("<%dH" % o1[1], original, 28 + o1[0]))
        s2 = list(struct.unpack_from("<%dH" % o2[1], bytes(edited), 28 + o2[0]))
        if s1 != s2:
            ok_other = False
            break
    check("G5 其余实体切片未动", ok_other, f"{len(other)-1} 个实体")
    try:
        n = check_container(bytes(edited))
        check("G6 容器重解析自洽", n == len(blocks), f"{n} 块")
    except Exception as exc:                                   # noqa: BLE001
        check("G6 容器重解析自洽", False, str(exc))
    check("G7 旧值原本在 / 新值原本不在", a.old in vals and a.new not in vals)

    if not all(c for _, c in checks):
        print("\n✗ 门禁未过，未写出")
        return 1
    out = pathlib.Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(bytes(edited))
    print(f"\n✓ 全部门禁通过 → {out}（{len(edited):,} B）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
