#!/usr/bin/env python3
"""gamedll_data_survey.py -- 盘点 `data/game/game.dll` **明文数据段**里有什么（只读）。

背景
    新 build（25988413+，49 MB）的 game.dll 段表恢复正常：`.text` 熵 8.0000（代码仍加密），
    但 `.rdata`（熵 7.67）与 `.data`（熵 6.43）里的**静态数据是明文**。本工具用「locid 字扫描」
    找出数据段里所有「本地化字符串引用」，按邻近聚成数据簇，给出每簇的样例文案，用于发现
    硬编码表（Operation Modifiers 就是这么找到的）。

用法
    python tools/gamedll_data_survey.py                    # 打印数据簇摘要
    python tools/gamedll_data_survey.py --json out/gamedll-clusters.json
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import struct
import sys

import pefile

DLL = pathlib.Path(r"D:\SteamLibrary\steamapps\common\Helldivers 2\data\game\game.dll")
STRINGS = pathlib.Path(r"D:\mod\refs\strings-en-26088801.json")
SECTIONS = (".rdata", ".data")
GAP = 0x400  # 相邻 locid 字间距超过该值即视为新簇


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dll", default=str(DLL))
    ap.add_argument("--strings", default=str(STRINGS))
    ap.add_argument("--json", default="")
    a = ap.parse_args()
    dll = pathlib.Path(a.dll)
    if not dll.exists():
        print(f"✗ game.dll 不存在: {dll}", file=sys.stderr)
        return 1
    data = dll.read_bytes()
    strings = json.loads(pathlib.Path(a.strings).read_text(encoding="utf-8"))
    ids = {int(k) for k in strings}
    pe = pefile.PE(data=data, fast_load=True)
    parts = {}
    for s in pe.sections:
        nm = s.Name.rstrip(b"\x00").decode("latin1")
        if nm in SECTIONS:
            parts[nm] = (s.PointerToRawData, s.SizeOfRawData)
    hits = []
    for nm, (off, size) in parts.items():
        for i in range(0, size - 3, 4):
            v = struct.unpack_from("<I", data, off + i)[0]
            if v in ids:
                hits.append((nm, off + i, v))
    clusters, cur = [], []
    for h in hits:
        if not cur or h[1] - cur[-1][1] <= GAP:
            cur.append(h)
        else:
            clusters.append(cur)
            cur = [h]
    if cur:
        clusters.append(cur)
    out = []
    for c in sorted((c for c in clusters if len(c) >= 3), key=lambda c: -len(c)):
        offs = [x[1] for x in c]
        deltas = collections.Counter(b - a for a, b in zip(offs, offs[1:]))
        samples, seen = [], set()
        for _nm, _o, v in c:
            t = strings.get(str(v), "")
            if t and t not in seen:
                seen.add(t)
                samples.append(t[:48].replace("\n", " "))
            if len(samples) >= 12:
                break
        out.append({
            "section": c[0][0],
            "start": f"0x{offs[0]:07X}",
            "end": f"0x{offs[-1]:07X}",
            "hits": len(c),
            "common_deltas": deltas.most_common(3),
            "samples": samples,
        })
    print(f"sections={ {k: (hex(v[0]), hex(v[1])) for k, v in parts.items()} }  locid 字命中={len(hits)}  "
          f"簇(>=3)={len(out)}")
    for r in out[:25]:
        print(f"  {r['section']} {r['start']}-{r['end']} n={r['hits']} deltas={r['common_deltas']}")
        print("     ", " | ".join(r["samples"][:8]))
    if a.json:
        p = pathlib.Path(a.json)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        print("wrote", p)
    return 0


if __name__ == "__main__":
    sys.exit(main())
