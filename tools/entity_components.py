#!/usr/bin/env python3
"""entity_components.py -- 实体 → 组件清单，并顺带找"谁引用了某个爆炸类型"。

为什么要它
    ① `refs/entity-locid-names.json` 只回答"哪些实体有名字"。要判断**没有名字的实体是不是
       占位/废案**，最直接的证据是它们的组件组成：只有 Transform/Renderable 的实体基本是空壳，
       挂着 LoadoutEntry / WeaponData / AI 的才是真内容。
    ② 块 0 尾部那 27,050 个 u16 不是块序号（值域到 52942、去重 324，直方图与各组件键数对不上），
       所以"实体→组件"不用它，改用**每个组件块自己的哈希图**（一份隶属表）反查。

用法
    python tools/entity_components.py --plaintext refs/dlbin/plaintext-26251122 \\
        --typelib refs/dlbin/plaintext-26251122/dl_library.dl_typelib \\
        --out refs/entity-components.json [--scan-refs VALUE ...]
"""
from __future__ import annotations

import argparse
import json
import pathlib
import struct
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from table_dictionary import Dictionary                          # noqa: E402
import entity_locid_scan as scan                                  # noqa: E402

# 类型名必须来自 json：typelib 被剥离过、没有名字，`geometry()` 靠 `ComponentIndexData`
# 这个名字认哈希图成员，没有名字表就一个块都拆不开（第一次跑就是这么空转的）。
NAMES_JSON = pathlib.Path("dl-type-names.json")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plaintext", default="refs/dlbin/plaintext-26251122")
    ap.add_argument("--typelib", default="refs/dlbin/plaintext-26251122/dl_library.dl_typelib")
    ap.add_argument("--out", default="refs/entity-components.json")
    ap.add_argument("--scan-refs", action="append", default=[],
                    help="在这些值里找'谁引用了它'（例如爆炸类型 68）")
    ap.add_argument("--targets", default="refs/dlbin/plaintext-26251122/generated_explosion_settings.dl_bin",
                    help="被引用值的候选集合来源（默认 explosion 表的 +0 类型 id）")
    a = ap.parse_args()

    base = pathlib.Path(a.plaintext)
    plain = (base / "generated_entities.dl_bin").read_bytes()
    dic = Dictionary(pathlib.Path(a.typelib).read_bytes(),
                     scan.load_names(NAMES_JSON) if NAMES_JSON.is_file() else {})

    blocks = scan.parse_blocks(plain)
    geos, membership = {}, {}
    for i, block in enumerate(blocks):
        g = scan.geometry(dic, block)
        if g is None:
            continue
        g = scan.check_geometry(plain, block, g)
        if not g["ok"]:
            continue
        geos[i] = g
        if not g["keys"]:
            continue
        name = scan.name_of(dic, block["type_id"])
        membership.setdefault(name, set()).update(scan.hashmap(plain, block, g))

    # 反查：实体键 -> 组件名
    comps: dict[int, list[str]] = {}
    for name, keys in membership.items():
        for key in keys:
            comps.setdefault(key, []).append(name)

    census = {}
    for key, names in comps.items():
        census[len(names)] = census.get(len(names), 0) + 1
    print(f"实体 {len(comps)} 个；组件块 {len(membership)} 个，几何通过 {len(geos)}")
    print("组件数分布（组件数:实体数）:",
          "  ".join(f"{k}:{v}" for k, v in sorted(census.items())[:12]))

    out = {"entities": len(comps),
           "blocks_used": len(geos),
           "components": {f"0x{k:016X}": sorted(v) for k, v in comps.items()}}

    # ---- 选做：找"哪个组件的哪一列引用了给定值" ----------------------------------
    if a.scan_refs:
        cand = set()
        tp = pathlib.Path(a.targets)
        if tp.is_file():
            tplain = tp.read_bytes()
            # explosion 表 +0 是类型 id；用字符串表定位方式太绕，这里直接取所有 < 4096 的 u32
            for off in range(0, len(tplain) - 4, 4):
                v = struct.unpack_from("<I", tplain, off)[0]
                if 0 < v < 4096:
                    cand.add(v)
        print(f"\n候选值集合（来自 {tp.name}）：{len(cand)} 个")
        targets = {int(x, 0) for x in a.scan_refs}
        found = {}
        for i, block in enumerate(blocks):
            g = geos.get(i)
            if not g:
                continue
            name = scan.name_of(dic, block["type_id"])
            row0 = block["payload_at"] + g["index_size"]
            for off in range(0, max(1, g["stride"] - 3), 4):
                hits, values = 0, set()
                for r in range(g["rows"]):
                    at = row0 + r * g["stride"] + off
                    if at + 4 > len(plain):
                        break
                    v = struct.unpack_from("<I", plain, at)[0]
                    if v in targets:
                        hits += 1
                        values.add(v)
                if hits:
                    found.setdefault(f"{name}+{off}", (hits, sorted(values)))
        print(f"命中 {len(found)} 个列：")
        for k, (hits, values) in sorted(found.items(), key=lambda kv: -kv[1][0])[:20]:
            print(f"  {k:52s} 命中 {hits:4d}  值 {values[:5]}")
        out["entity_refs"] = {k: {"hits": v[0], "values": v[1]} for k, v in found.items()}

    # ---- 选做：把没有名字的实体按组件组合归类 --------------------------------------
    dest = pathlib.Path(a.out)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n写入 {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
