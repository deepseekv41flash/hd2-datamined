#!/usr/bin/env python3
"""entity_dump.py -- 给一个实体键，列出它**全部组件行**（哪个块、哪一行、字段原值）。

为什么需要
    `entity_field_set.py` 要求调用方**预先知道** `--block`（组件类型 id）；
    而排查「这个实体为什么行为不对」时，第一步恰恰是「它到底挂了哪些组件」。
    本工具把「实体键 → 组件清单」这一步补上：遍历所有块，逐块查该块的哈希图。

定位方式（与 entity_field_set 完全一致，不写死任何块偏移）
    每个组件块形态 = 「哈希图（key:u64 → row:u32）+ 行数组」，块体从 head+28 起。
    行内字段顺序由 typelib 的成员描述给出（--fields 时按名字/偏移打印）。

用法
    python tools/entity_dump.py --key 0x75BE82ED8592A6B3
    python tools/entity_dump.py --key 0x75BE82ED8592A6B3 --rows 12      # 每行前 12 个 u32
    python tools/entity_dump.py --key 0x... --compare 0x...             # 两个实体组件差异
    python tools/entity_dump.py --key 0x... --json-out out/a.json

局限
    只处理「2 成员」块（哈希图 + 行数组）。别的形态（单成员 / 三成员）会跳过并计入 skipped，
    不会静默当成 0 组件。
"""
from __future__ import annotations

import argparse
import json
import pathlib
import struct
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from pod_rack_swap import parse_blocks                    # noqa: E402
from typelib import TypeLib                                # noqa: E402

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:                                      # noqa: BLE001
        pass

PLAIN = r"D:\mod\refs\dlbin\plaintext-26251122\generated_entities.dl_bin"
TYPELIB = r"D:\mod\refs\dlbin\plaintext-26251122\dl_library.dl_typelib"
BLOCK_TYPES = HERE.parent / "refs" / "entity-block-types.json"


def block_name_map() -> dict[int, str | None]:
    if not BLOCK_TYPES.exists():
        return {}
    d = json.load(open(BLOCK_TYPES, encoding="utf-8"))
    out: dict[int, str | None] = {}
    for b in d.get("blocks", []):
        out[int(b["type_id"], 16)] = b.get("component")
    return out


def find_rows(data: bytes, lib: TypeLib, key: int):
    """→ [(block_index, type_id, row_index, row_offset, stride, slots, members)]"""
    hits = []
    for bi, b in enumerate(parse_blocks(data)):
        try:
            ms = lib.members(b["type_id"])
        except Exception:                                  # noqa: BLE001
            continue
        if len(ms) != 2:
            continue
        slots = ms[0]["size64"]
        try:
            stride = lib.desc(ms[1]["type_id"])[3]
        except Exception:                                  # noqa: BLE001
            continue
        if not stride or slots % 16:
            continue
        body = b["head"] + 28
        if body + slots > len(data):
            continue
        for i in range(slots // 16):
            k, v = struct.unpack_from("<QI", data, body + 16 * i)
            if k == key:
                if v * stride + stride > ms[1]["size64"]:
                    continue
                hits.append((bi, b["type_id"], v, body + slots + v * stride, stride, slots, ms))
                break
    return hits


def fmt_row(data: bytes, off: int, stride: int, width: int) -> list[str]:
    out = []
    for o in range(0, min(width, stride), 4):
        u = struct.unpack_from("<I", data, off + o)[0]
        i = struct.unpack_from("<i", data, off + o)[0]
        f = struct.unpack_from("<f", data, off + o)[0]
        fs = f"{f:<14.6g}"
        out.append(f"+0x{o:02X} {u:<11d} {i:<11d} {fs}")
    return out


def dump(data: bytes, lib: TypeLib, names: dict[int, str | None], key: int, width: int) -> dict:
    hits = find_rows(data, lib, key)
    rows = []
    for bi, tid, ridx, roff, stride, slots, ms in hits:
        rows.append({
            "block_index": bi,
            "type_id": f"0x{tid:08X}",
            "component": names.get(tid),
            "row": ridx,
            "row_offset": roff,
            "stride": stride,
            "slots": slots,
            "cells": fmt_row(data, roff, stride, width),
            "raw": data[roff:roff + stride].hex(),
        })
    return {"key": f"0x{key:016X}", "components": rows}


def main() -> int:
    ap = argparse.ArgumentParser(description="实体键 → 全部组件行")
    ap.add_argument("--plain", default=PLAIN)
    ap.add_argument("--typelib", default=TYPELIB)
    ap.add_argument("--key", required=True, help="实体键（哈希图键）")
    ap.add_argument("--rows", type=int, default=0, help="每行打印前 N 个 u32（0 = 只列组件）")
    ap.add_argument("--json-out", default=None)
    ap.add_argument("--yaml", action="store_true", help="按 JSON 原样输出（禁用，兼容旧脚本）")
    a = ap.parse_args()

    data = pathlib.Path(a.plain).read_bytes()
    lib = TypeLib(open(a.typelib, "rb").read())
    names = block_name_map()

    keys = [int(str(k), 0) for k in ([a.key] if isinstance(a.key, str) else a.key)]
    results = []
    for key in keys:
        r = dump(data, lib, names, key, a.rows * 4)
        results.append(r)
        print(f"=== 0x{key:016X}  组件 {len(r['components'])} 个 ===")
        for c in sorted(r["components"], key=lambda x: (x["component"] or "zzz", x["type_id"])):
            nm = c["component"] or "?"
            print(f"  {nm:<44} {c['type_id']}  row {c['row']:<5} stride {c['stride']:<6} 0x{c['row_offset']:X}")
            for cell in c["cells"]:
                print(f"      {cell}")
        print()
    if a.json_out:
        pathlib.Path(a.json_out).write_text(
            json.dumps(results[0] if len(results) == 1 else results, indent=1, ensure_ascii=False),
            encoding="utf-8")
        print(f"→ {a.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
