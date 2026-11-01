#!/usr/bin/env python3
"""opmod_scan.py -- 从 `data/game/game.dll` 里提取 Operation Modifiers 硬编码表（只读）。

背景
    wiki 的 Operation Modifiers 不由服务器 API 下发（2026-11-01 抓包证明：
    Operation/Create、Mission/Start、Mission/end 响应里没有 modifier 字段）；
    客户端把 13 条定义硬编码在 game.dll 的文件偏移 0x2CA0168，每条 0x50 B：
        +0x00 显示名 locid（UPPER）
        +0x04 描述 locid
        +0x08/+0x0C 类型/类别 hash（多数条目相同，Leviathan 那条不同）
        +0x10 枚举/效果索引（⚠ 未证）
        +0x18 hash（⚠ 未证）· +0x1C / +0x20 数值 · +0x24 hash
        +0x28 f32（权重/倍率？⚠ 未证）
    locid -> 英文文案用 D:/mod/refs/strings-en-26088801.json 解。

用法
    python tools/opmod_scan.py            # 打印 13 条
    python tools/opmod_scan.py --csv out/opmod.csv --json out/opmod.json
"""
from __future__ import annotations

import argparse
import csv
import json
import pathlib
import struct
import sys

DLL = pathlib.Path(r"D:\SteamLibrary\steamapps\common\Helldivers 2\data\game\game.dll")
STRINGS = pathlib.Path(r"D:\mod\refs\strings-en-26088801.json")
TABLE_OFF = 0x2CA0168
STRIDE = 0x50
COUNT = 13


def extract(dll: pathlib.Path, strings: dict[str, str]) -> list[dict]:
    data = dll.read_bytes()
    rows = []
    for i in range(COUNT):
        off = TABLE_OFF + i * STRIDE
        w = [struct.unpack_from("<I", data, off + 4 * j)[0] for j in range(20)]
        f28 = struct.unpack_from("<f", data, off + 0x28)[0]
        rows.append({
            "idx": i,
            "file_offset": f"0x{off:08X}",
            "name": strings.get(str(w[0]), ""),
            "name_locid": w[0],
            "desc": strings.get(str(w[1]), ""),
            "desc_locid": w[1],
            "hash08": f"0x{w[2]:08X}",
            "hash0c": f"0x{w[3]:08X}",
            "value10": w[4],
            "hash18": f"0x{w[6]:08X}",
            "value1c": w[7],
            "value20": w[8],
            "hash24": f"0x{w[9]:08X}",
            "f28": round(f28, 6),
        })
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description="提取 game.dll 里的 Operation Modifiers 硬编码表")
    ap.add_argument("--dll", default=str(DLL))
    ap.add_argument("--strings", default=str(STRINGS))
    ap.add_argument("--csv", default="")
    ap.add_argument("--json", default="")
    a = ap.parse_args()
    dll = pathlib.Path(a.dll)
    if not dll.exists():
        print(f"✗ game.dll 不存在: {dll}", file=sys.stderr)
        return 1
    strings = json.loads(pathlib.Path(a.strings).read_text(encoding="utf-8"))
    rows = extract(dll, strings)
    for r in rows:
        print(f"[{r['idx']:>2}] {r['name']:<28} {r['desc'][:70]}")
        print(f"      0x08={r['hash08']} 0x0c={r['hash0c']} +0x10={r['value10']:>4} "
              f"0x18={r['hash18']} 0x1c={r['value1c']:>4} 0x24={r['hash24']} f28={r['f28']}")
    if a.csv:
        p = pathlib.Path(a.csv)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("w", encoding="utf-8-sig", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        print("wrote", p)
    if a.json:
        p = pathlib.Path(a.json)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
        print("wrote", p)
    return 0


if __name__ == "__main__":
    sys.exit(main())
