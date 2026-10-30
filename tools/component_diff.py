#!/usr/bin/env python3
"""component_diff.py -- 多个实体键的**组件行逐字段 diff**（捡拾问题排查用）。

为什么需要
    `entity_dump.py` 只做「一个实体 → 它的组件行」；判断两把武器为什么行为不同
    （例：副武器为什么不能被捡起）需要把**同名组件**的行并排 diff，
    并把差异字段翻译成 typelib 里的成员名，而不是一串裸 u32。

做法
    复用 entity_dump 的哈希图定位（2 成员块：key:u64 → row:u32 + 行数组），
    对每个组件：先按 4 字节槽比较原始字节，再对每个差异槽给出
    u32 / i32 / f32 三种读法 + 最内层覆盖该偏移的 typelib 成员名。
    完全相同的组件只记一行「同」，不刷屏。

用法
    python tools/component_diff.py --key 副=0x05E4E5C2DB6E44A2 --key 主=0x03E67A19B07C6523
    python tools/component_diff.py --key A=0x.. --key B=0x.. --key C=0x.. --json-out out/x.json
    python tools/component_diff.py --key A=0x.. --key B=0x.. --only Wieldable,LoadoutEntry

退出码
    0 = 跑完（有差异也是 0）；2 = 参数/读表错误。
"""
from __future__ import annotations

import argparse
import json
import pathlib
import struct
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from entity_dump import (find_rows, block_name_map, PLAIN, TYPELIB)   # noqa: E402
from pod_rack_swap import parse_blocks                                # noqa: E402
from typelib import TypeLib                                           # noqa: E402

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:                                                  # noqa: BLE001
        pass

MAX_FIELDS = 400


def member_ranges(lib: TypeLib, tid: int, depth: int = 0, base: int = 0,
                  out: list | None = None) -> list[tuple[int, int, str, int]]:
    """(offset, size, name, depth) 展平，深度 ≤ 3，带 base 偏移。"""
    if out is None:
        out = []
    if depth > 3:
        return out
    try:
        members = lib.members(tid)
    except Exception:                                                  # noqa: BLE001
        return out
    for m in members:
        off = base + m["offset32"]
        size = m["size32"]
        out.append((off, size, m["name"] or "?", depth))
        if size > 4 and depth < 3 and m["type_flags"] in (0, 1, 2):
            member_ranges(lib, m["type_id"], depth + 1, off, out)
    return out


def build_namer(lib: TypeLib, row_tid: int):
    rng = member_ranges(lib, row_tid)
    rng.sort(key=lambda x: (x[0], -x[3]))

    def name_at(off: int) -> str:
        best = None
        for o, size, nm, depth in rng:
            if o <= off < o + size:
                cand = (depth, o, nm)
                if best is None or cand > best:
                    best = cand
        if best is None:
            return ""
        depth, o, nm = best
        return nm if o == off else f"{nm}+0x{off - o:X}"

    return name_at


def load_entity(data: bytes, lib: TypeLib, names: dict[int, str | None], key: int) -> dict:
    comps = {}
    for bi, tid, ridx, roff, stride, slots, ms in find_rows(data, lib, key):
        raw = data[roff:roff + stride]
        comps[tid] = {
            "name": names.get(tid) or f"<0x{tid:08X}>",
            "type_id": tid,
            "row": ridx,
            "stride": stride,
            "row_type": ms[1]["type_id"],
            "raw": raw,
        }
    return comps


def f32(raw: bytes, off: int) -> float:
    return struct.unpack_from("<f", raw, off)[0]


def fmt_f32(v: float) -> str:
    return f"{v:.7g}"


def diff_rows(lib: TypeLib, a: dict, b: dict) -> list[dict]:
    ra, rb = a["raw"], b["raw"]
    if len(ra) != len(rb):
        return [{"offset": -1, "note": f"stride 不同 {len(ra)} vs {len(rb)}"}]
    namer = build_namer(lib, a["row_type"])
    diffs = []
    for off in range(0, len(ra), 4):
        if ra[off:off + 4] == rb[off:off + 4]:
            continue
        ua, ub = struct.unpack_from("<I", ra, off)[0], struct.unpack_from("<I", rb, off)[0]
        fa, fb = f32(ra, off), f32(rb, off)
        diffs.append({
            "offset": off,
            "field": namer(off),
            "hex": [ra[off:off + 4].hex(), rb[off:off + 4].hex()],
            "u32": [ua, ub],
            "i32": [struct.unpack_from("<i", ra, off)[0], struct.unpack_from("<i", rb, off)[0]],
            "f32": [fa, fb],
            "f32_fmt": [fmt_f32(fa), fmt_f32(fb)],
        })
    return diffs


def main() -> int:
    ap = argparse.ArgumentParser(description="多实体组件行逐字段 diff")
    ap.add_argument("--key", action="append", required=True,
                    help="标签=0x实体键，至少两个；第一个为基准")
    ap.add_argument("--plain", default=PLAIN)
    ap.add_argument("--typelib", default=TYPELIB)
    ap.add_argument("--only", default="", help="只比较名字含这些子串的组件（逗号分隔）")
    ap.add_argument("--json-out", default=None)
    a = ap.parse_args()

    named = []
    for spec in a.key:
        if "=" not in spec:
            ap.error(f"--key 需要 标签=0x键 形式：{spec}")
        label, k = spec.split("=", 1)
        named.append((label.strip(), int(k.strip(), 0)))
    if len(named) < 2:
        ap.error("至少给两个 --key")

    data = pathlib.Path(a.plain).read_bytes()
    lib = TypeLib(open(a.typelib, "rb").read())
    names = block_name_map()
    forces = [s.strip().lower() for s in a.only.split(",") if s.strip()]

    ents = {label: load_entity(data, lib, names, key) for label, key in named}
    base_label = named[0][0]
    base = ents[base_label]

    print(f"明文: {a.plain}")
    for label, key in named:
        print(f"  {label:<10} 0x{key:016X}  组件 {len(ents[label])} 个")
    print()

    report = {"keys": {l: f"0x{k:016X}" for l, k in named}, "pairs": []}

    for label, key in named[1:]:
        other = ents[label]
        print("=" * 78)
        print(f"### {label} 相对 {base_label}（{base_label} 为基准）")
        set_a, set_b = set(base), set(other)
        extra = sorted(set_b - set_a, key=lambda t: (names.get(t) or "", t))
        missing = sorted(set_a - set_b, key=lambda t: (names.get(t) or "", t))
        pair = {"other": label, "component_diff": [], "extra": [], "missing": []}
        if extra:
            print(f"  {label} 多出的组件:")
            for t in extra:
                nm = other[t]["name"]
                print(f"    + {nm:<42} 0x{t:08X} stride {other[t]['stride']}")
                pair["extra"].append({"name": nm, "type_id": f"0x{t:08X}"})
        if missing:
            print(f"  {label} 缺少的组件:")
            for t in missing:
                nm = base[t]["name"]
                print(f"    - {nm:<42} 0x{t:08X} stride {base[t]['stride']}")
                pair["missing"].append({"name": nm, "type_id": f"0x{t:08X}"})
        if not extra and not missing:
            print("  组件集合: 完全相同")

        common = [t for t in sorted(set_a & set_b, key=lambda t: (names.get(t) or "", t))]
        shown = same = 0
        for t in common:
            nm = base[t]["name"]
            if forces and not any(f in nm.lower() for f in forces):
                continue
            diffs = diff_rows(lib, base[t], other[t])
            if not diffs:
                same += 1
                continue
            shown += 1
            print(f"\n  ~ {nm}  (0x{t:08X}, stride {base[t]['stride']}, "
                  f"{len(diffs)} 处差异)")
            for d in diffs[:MAX_FIELDS]:
                print(f"      +0x{d['offset']:03X} {d['field']:<34} "
                      f"{d['hex'][0]} → {d['hex'][1]}   "
                      f"u32 {d['u32'][0]}→{d['u32'][1]}   "
                      f"f32 {d['f32_fmt'][0]}→{d['f32_fmt'][1]}")
            if len(diffs) > MAX_FIELDS:
                print(f"      … 还有 {len(diffs) - MAX_FIELDS} 处（--json-out 看全量）")
            pair["component_diff"].append({
                "name": nm, "type_id": f"0x{t:08X}", "stride": base[t]["stride"],
                "diff_count": len(diffs), "fields": diffs,
            })
        print(f"\n  同名组件: {len(common)} 个，有差异 {shown} 个，完全相同 {same} 个")
        report["pairs"].append(pair)

    if a.json_out:
        pathlib.Path(a.json_out).write_text(
            json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"\n→ {a.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
