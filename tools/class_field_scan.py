#!/usr/bin/env python3
"""class_field_scan.py -- 按「武器类别」扫描组件行字段，找只由类别决定的字段。

背景
    捡拾问题要回答「副武器不能被捡起，是不是某个字段/槽位类型决定的」。
    单看 4 把武器只能看到一堆差异，无法区分
        「这把枪特有的值（哈希、模型 id、数值）」
        「类别决定的枚举（primary/support/sidearm 槽位类型）」
    所以要用**带类别标签的语料**做统计：同一类别里取值恒定、不同类别取值互斥的字段，
    才是「类别开关」的候选。

语料
    refs/weapon-customization-l0-26251122.json 的 rows[].kind
    （primary_weapon 59 / support_weapon 45 / sidearm 28 / unit 20 / throwable 6 / interactable 7）

判据（每个 4 字节槽）
    对每个偏移 off，取每类里出现过该组件的实体的 u32 值集合 S_c：
      · 每类基数小（≤3）且至少两类互斥（S_a ∩ S_b = ∅） → 候选
      · 排序：类别覆盖率（含该组件的类数）高、类内基数小、类间重叠小

用法
    python tools/class_field_scan.py [--min-classes 3] [--top 40]
    python tools/class_field_scan.py --only Interactable,Equipment
    python tools/class_field_scan.py --json-out out/class-fields.json
"""
from __future__ import annotations

import argparse
import json
import pathlib
import struct
import sys
from collections import defaultdict

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from entity_dump import block_name_map, PLAIN, TYPELIB          # noqa: E402
from pod_rack_swap import parse_blocks                          # noqa: E402
from typelib import TypeLib                                     # noqa: E402

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:                                           # noqa: BLE001
        pass

CENSUS = HERE.parent / "refs" / "weapon-customization-l0-26251122.json"
CLASS_ORDER = ["sidearm", "primary_weapon", "support_weapon", "throwable", "unit"]


def load_census() -> dict[str, list[tuple[str, str]]]:
    d = json.load(open(CENSUS, encoding="utf-8"))
    out: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for rid, r in d["rows"].items():
        kind = r.get("kind")
        name = r.get("name") or f"row{rid}"
        for k in r.get("keys") or []:
            out[kind].append((name, k))
    return out


def build_index(data: bytes, lib: TypeLib, names: dict[int, str | None]):
    """预解析所有 2 成员块 → [(tid, name, slots, stride, rowtype, body)]，并缓存成员名。"""
    idx = []
    for bi, b in enumerate(parse_blocks(data)):
        try:
            ms = lib.members(b["type_id"])
        except Exception:                                       # noqa: BLE001
            continue
        if len(ms) != 2:
            continue
        slots = ms[0]["size64"]
        try:
            stride = lib.desc(ms[1]["type_id"])[3]
        except Exception:                                       # noqa: BLE001
            continue
        if not stride or slots % 16:
            continue
        body = b["head"] + 28
        if body + slots > len(data):
            continue
        idx.append((b["type_id"], names.get(b["type_id"]) or f"<0x{b['type_id']:08X}>",
                    slots, stride, ms[1]["type_id"], body))
    return idx


def rows_for_key(data: bytes, idx, key: int) -> dict[int, tuple[int, int, bytes, list]]:
    out = {}
    for tid, name, slots, stride, rowtype, body in idx:
        for i in range(slots // 16):
            k, v = struct.unpack_from("<QI", data, body + 16 * i)
            if k == key:
                off = body + slots + v * stride
                if off + stride <= len(data):
                    out[tid] = (v, stride, data[off:off + stride], [name, rowtype])
                break
    return out


def f32(b: bytes, off: int) -> float:
    return struct.unpack_from("<f", b, off)[0]


def scan(component_rows: dict[str, dict[int, bytes]], classes: list[str],
         min_classes: int, top: int, only: list[str], json_out: str | None) -> None:
    # 组件 → 类 → [值数组]
    tids = set()
    for c in classes:
        for comps in component_rows[c].values():
            tids.update(comps)
    names = block_name_map()
    results = []
    for tid in sorted(tids):
        cname = names.get(tid) or f"<0x{tid:08X}>"
        if only and not any(s.lower() in cname.lower() for s in only):
            continue
        per_class = {}
        strides = set()
        for c in classes:
            rows = [comps[tid] for comps in component_rows[c].values() if tid in comps]
            if not rows:
                continue
            per_class[c] = rows
            strides.update(r[1] for r in rows)
        if len(per_class) < min_classes or len(strides) != 1:
            continue
        stride = strides.pop()
        total = sum(len(v) for v in per_class.values())
        cand = []
        for off in range(0, stride, 4):
            sets = {}
            for c, rows in per_class.items():
                sets[c] = {struct.unpack_from("<I", r[2], off)[0] for r in rows}
            # 互斥：存在两类集合不相交
            disjoint_pairs = 0
            cs = [c for c in CLASS_ORDER if c in sets]
            for i in range(len(cs)):
                for j in range(i + 1, len(cs)):
                    if sets[cs[i]] and sets[cs[j]] and not (sets[cs[i]] & sets[cs[j]]):
                        disjoint_pairs += 1
            small = sum(1 for c in cs if len(sets[c]) <= 3)
            if disjoint_pairs == 0 or small < len(cs):
                continue
            fvals = {c: {f32(next(r[2] for r in per_class[c] if struct.unpack_from("<I", r[2], off)[0] == v), off)
                         for v in sets[c]} for c in cs}
            cand.append({
                "offset": off,
                "classes": {c: sorted(sets[c]) for c in cs},
                "f32": {c: sorted(round(x, 6) for x in fvals[c]) for c in cs},
                "disjoint_pairs": disjoint_pairs,
                "small": small,
            })
        if not cand:
            continue
        cand.sort(key=lambda x: (-x["disjoint_pairs"], -x["small"], x["offset"]))
        results.append({"component": cname, "type_id": f"0x{tid:08X}", "stride": stride,
                        "coverage": {c: len(per_class[c]) for c in per_class},
                        "candidates": cand})

    print(f"语料: " + "  ".join(f"{c}={len(v)}" for c, v in ((c, component_rows[c]) for c in classes)))
    print(f"扫描组件 {len(results)} 个（含候选字段）\n")
    for r in results:
        print("=" * 78)
        print(f"{r['component']}  {r['type_id']} stride {r['stride']}  "
              f"覆盖 {r['coverage']}")
        for cand in r["candidates"][:top]:
            cls_s = "  ".join(
                f"{c}={cand['classes'][c] if len(str(cand['classes'][c])) < 40 else str(cand['classes'][c])[:40]}"
                for c in cand["classes"])
            print(f"  +0x{cand['offset']:03X}  disjoint={cand['disjoint_pairs']} small={cand['small']}  {cls_s}")
        if len(r["candidates"]) > top:
            print(f"  … 还有 {len(r['candidates']) - top} 个候选槽")
        print()

    if json_out:
        pathlib.Path(json_out).write_text(
            json.dumps({"classes": classes, "results": results}, indent=1, ensure_ascii=False),
            encoding="utf-8")
        print(f"→ {json_out}")


def main() -> int:
    ap = argparse.ArgumentParser(description="按武器类别扫描类别决定字段")
    ap.add_argument("--plain", default=PLAIN)
    ap.add_argument("--typelib", default=TYPELIB)
    ap.add_argument("--classes", default="sidearm,primary_weapon,support_weapon")
    ap.add_argument("--min-classes", type=int, default=3)
    ap.add_argument("--top", type=int, default=25)
    ap.add_argument("--only", default="")
    ap.add_argument("--json-out", default=None)
    a = ap.parse_args()

    census = load_census()
    classes = [c.strip() for c in a.classes.split(",") if c.strip()]
    data = pathlib.Path(a.plain).read_bytes()
    lib = TypeLib(open(a.typelib, "rb").read())
    names = block_name_map()
    idx = build_index(data, lib, names)
    print(f"2 成员组件块 {len(idx)} 个")
    comp_rows: dict[str, dict[str, dict[int, tuple]]] = {}
    for c in classes:
        ents = census.get(c, [])
        comp_rows[c] = {}
        for name, k in ents:
            comp_rows[c][name + "@" + k] = rows_for_key(data, idx, int(k, 16))
    only = [s for s in a.only.split(",") if s.strip()]
    scan(comp_rows, classes, a.min_classes, a.top, only, a.json_out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
