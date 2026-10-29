#!/usr/bin/env python3
"""stratagem_payload_check.py -- 战备行的「载荷实体」在本 build 到底存不存在。

为什么需要这个
    `+0xC8` 额外战备链能把任意一行带进任务，但「带得进去」不等于「叫得出来」。
    2026-10-28 实机测 id 106 / 135 / 127 得到三种不同症状：

        id 106 Carpet Bomb   → 能按，投出瞬间**崩溃**
        id 135 Nuke          → 能按，投出后**什么都不会发生**
        id 127 Reinforce     → 有图标但**按不动**

    离线查下来，前两条的载荷实体引用是**悬空**的（本 build 的 `generated_entities.dl_bin`
    里一次都没出现），第三条的载荷**存在**、缺的是呼叫前置。所以「崩 / 静默 / 按不动」
    分属三层，不是一件事。

判据
    战备行 `+0x98` = `{u64 payload 相对偏移, u32 数量}` → 指向一段 8 字节**实体哈希数组**
    （见 docs/tables/STRATAGEM-FIELDS-26088801.md）。对每个哈希，去
    `generated_entities.dl_bin` 里数它的 u64 小端出现次数：0 次 = 悬空。

用法
    python tools/stratagem_payload_check.py                 # 只列悬空行
    python tools/stratagem_payload_check.py --all           # 全表 153 行
    python tools/stratagem_payload_check.py --id 106 135 127
"""
from __future__ import annotations

import argparse
import json
import pathlib
import struct
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
MOD = REPO.parent.parent
BASE = MOD / "refs/dlbin/plaintext-26251122"
STRAT = BASE / "generated_stratagem_settings.dl_bin"
ENT = BASE / "generated_entities.dl_bin"

sys.path.insert(0, str(REPO / "tools"))
from stratagem_extra import load, u32, names_map, label          # noqa: E402

DEPLOY = {0: "飞鹰空投", 1: "轨道", 2: "投掷/空投", 3: "载具空投", 4: "信标",
          5: "行走弹幕", 6: "SEAF 专用", 7: "Eagle Rearm"}


def payload_hashes(row: bytes, payload: bytes):
    off = struct.unpack_from("<Q", row, 0x98)[0]
    cnt = struct.unpack_from("<I", row, 0xA0)[0]
    if not (0 < cnt <= 64) or not (0 <= off < len(payload) - 8):
        return []
    if off + cnt * 8 > len(payload):
        return []
    return [struct.unpack_from("<Q", payload, off + i * 8)[0] for i in range(cnt)]


def main() -> int:
    ap = argparse.ArgumentParser(description="战备行载荷实体是否存在")
    ap.add_argument("--all", action="store_true", help="列出全表")
    ap.add_argument("--id", nargs="*", type=int, default=[], help="只看这些 id")
    a = ap.parse_args()

    data, gs, rows = load(str(STRAT))
    nm = names_map()
    payloads = {gi: g["payload"] for gi, g in enumerate(gs)}
    ent = ENT.read_bytes()
    known = json.loads((MOD / "refs/entity-locid-names.json").read_text(encoding="utf-8"))
    by_key = {e["key"].upper(): e for e in known["entity_index"] if e.get("key")}
    srkit = {}
    for it in json.loads((MOD / "refs/srkit-names.json").read_text(encoding="utf-8")):
        h = (it.get("file_id_hex") or "").upper()
        if h:
            srkit.setdefault(h, it)

    out = []
    for k, r in enumerate(rows):
        row = r["row"]
        sid = u32(row, 0)
        if a.id and sid not in a.id:
            continue
        mode = u32(row, 0x3C)
        hs = payload_hashes(row, payloads[r["group"]])
        missing = [h for h in hs if ent.count(struct.pack("<Q", h)) == 0]
        rec = {"id": sid, "row": k, "name": label(k, nm), "mode": mode,
               "mode_name": DEPLOY.get(mode, "?"), "hashes": [f"0x{h:016X}" for h in hs],
               "missing": [f"0x{h:016X}" for h in missing],
               "verdict": ("dangling" if missing else
                           "ok" if hs else "no-payload-array")}
        out.append(rec)

    print(f"{'id':>4} {'row':>4} {'投放':<10} {'载荷数':>5}  状态      名字 / 悬空哈希")
    print("-" * 96)
    for rec in out:
        if not a.all and a.id == [] and rec["verdict"] != "dangling":
            continue
        extra = ""
        if rec["verdict"] == "dangling":
            res = []
            for h in rec["missing"]:
                it = srkit.get(h.upper())
                res.append(f"{h}({it['type'] + ':' + it['name'] if it else '无资源名'})")
            extra = "  " + " ".join(res)
        print(f"{rec['id']:>4} {rec['row']:>4} {rec['mode']}({rec['mode_name']})"
              f"{'':<2} {len(rec['hashes']):>5}  {rec['verdict']:<10}{rec['name'][:26]:26}{extra}")

    dangling = [r for r in out if r["verdict"] == "dangling"]
    print()
    print(f"共 {len(out)} 行；悬空 {len(dangling)} 行"
          + ("：" + ", ".join(f"id {r['id']} ({r['name']})" for r in dangling) if dangling else ""))
    if a.all or a.id:
        (MOD / "out/stratagem-extra/payload-check.json").write_text(
            json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"-> {MOD / 'out/stratagem-extra/payload-check.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
