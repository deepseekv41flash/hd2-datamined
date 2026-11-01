#!/usr/bin/env python3
"""gamedll_catalog_extract.py -- 从 `data/game/game.dll` 明文数据段提取三张硬编码表（只读）。

表 1：Operation Modifiers（13 条 × 0x50 B）  —— 偏移 0x2CA0168，见 opmod_scan.py
表 2：Operation 类型/impact 定义族（14 条 × 0xA8 B）—— 偏移 0x2077570
表 3：舰船升级模块（44 条 × 0x30 B）        —— 偏移 0x208A454（其后是提示文案，不再属于本表）

用法
    python tools/gamedll_catalog_extract.py --json out/gamedll-catalogs.json
"""
from __future__ import annotations

import argparse
import json
import pathlib
import struct
import sys

DLL = pathlib.Path(r"D:\SteamLibrary\steamapps\common\Helldivers 2\data\game\game.dll")
STRINGS = pathlib.Path(r"D:\mod\refs\strings-en-26088801.json")

OPMOD_BASE, OPMOD_N, OPMOD_STRIDE = 0x2CA0168, 13, 0x50
OPSET_BASE, OPSET_STRIDE = 0x2077570, 0xA8
SHIP_BASE, SHIP_N, SHIP_STRIDE = 0x208A454, 44, 0x30


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dll", default=str(DLL))
    ap.add_argument("--strings", default=str(STRINGS))
    ap.add_argument("--json", default="")
    a = ap.parse_args()
    data = pathlib.Path(a.dll).read_bytes()
    strings = json.loads(pathlib.Path(a.strings).read_text(encoding="utf-8"))
    s = lambda loc: strings.get(str(loc), "")  # noqa: E731

    def u32(off):
        return struct.unpack_from("<I", data, off)[0]

    def f32(off):
        return round(struct.unpack_from("<f", data, off)[0], 6)

    # ---- 1) operation modifiers ----
    opmods = []
    for i in range(OPMOD_N):
        off = OPMOD_BASE + i * OPMOD_STRIDE
        opmods.append({
            "idx": i, "offset": f"0x{off:07X}",
            "name": s(u32(off)), "desc": s(u32(off + 4)),
            "hash08": f"0x{u32(off + 8):08X}", "hash0c": f"0x{u32(off + 0xC):08X}",
            "value10": u32(off + 0x10), "hash18": f"0x{u32(off + 0x18):08X}",
            "value1c": u32(off + 0x1C), "hash24": f"0x{u32(off + 0x24):08X}",
            "f28": f32(off + 0x28),
        })

    # ---- 2) operation impact family ----
    opsets = []
    for k in range(40):
        off = OPSET_BASE + k * OPSET_STRIDE
        if off + OPSET_STRIDE > len(data):
            break
        impact = s(u32(off + 0x10))
        if not impact:
            break
        opsets.append({
            "idx": k, "offset": f"0x{off:07X}",
            "nums": [u32(off), u32(off + 4), u32(off + 8)],
            "impact_label": s(u32(off + 0xC)),
            "impact": impact,
            "pct_label": s(u32(off + 0x1C)),
            "op_type": s(u32(off + 0x20)),
        })

    # ---- 3) ship modules ----
    ship = []
    for i in range(SHIP_N):
        off = SHIP_BASE + i * SHIP_STRIDE
        ship.append({
            "idx": i, "offset": f"0x{off:07X}",
            "name": s(u32(off)), "desc": s(u32(off + 4)),
            "effect": s(u32(off + 8)),
            "hash1c": f"0x{u32(off + 0x1C):08X}",
            "v20": u32(off + 0x20), "f24": f32(off + 0x24),
        })
    out = {"opmods": opmods, "opsets": opsets, "ship_modules": ship}
    for m in ship:
        print(f"[{m['idx']:>2}] {m['name'][:34]:<36} | {(m['effect'] or m['desc'])[:64]}")
    print(f"\nopmods={len(opmods)} opsets={len(opsets)} ship_modules={len(ship)}")
    if a.json:
        p = pathlib.Path(a.json)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        print("wrote", p)
    return 0


if __name__ == "__main__":
    sys.exit(main())
