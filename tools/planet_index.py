#!/usr/bin/env python3
"""planet_index.py -- 行星编号 ↔ 名称 ↔ 生态 的一张表（build 26088801）。

WHY
    `planet_data` 的行号就是游戏里的行星索引（`planetActiveEffects.index` / `planetStatus.index`
    用的就是它），但那个数字本身没有任何可读信息。这个工具把已解出的字段拼成一张可以直接查的表，
    并且把「服务器侧当前生效的 presence」并进来（那一列来自抓包，属于网络层，输出到仓库外）。

NAMES
    名称取自 `locid-names.json` 的 `tables.planet_data`（`+0x008` 的 locid → 英文字符串），
    **英文本就是本 build 数据里唯一的语料**（本机 `.strings` 只有英文 blob）。39 行没有名字，
    都是模板行（`Inherits` 为空），`debug_name` 里有生态提示。

USAGE
    python tools/planet_index.py                      # 生成 docs/tables/PLANET-INDEX-26088801.md + out/planet/planet-index.json
    python tools/planet_index.py --live-dir <dir>     # 额外把抓包里的 owner / 当前 presence 并进来（写仓库外的 CSV）
"""
from __future__ import annotations

import argparse
import csv
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

PLANET_JSON = ROOT / "out" / "planet" / "planet-data.json"
DEFAULT_LIVE = pathlib.Path(r"D:/mod/out/gwe")

BIOME = {2: "arctic", 3: "sandy", 6: "swamp", 8: "primordial", 9: "moor", 10: "superearth",
         11: "bug_hiveworld", 12: "magma", 13: "oasis", 14: "deciduous", 15: "coniferous",
         16: "rift"}
OWNER = {1: "superearth", 2: "terminid", 3: "automaton", 4: "illuminate"}



MASK64 = 2 ** 64 - 1


def murmur64_seed0(data: bytes) -> int:
    """Stingray 名字哈希（seed 0），与 srkit/util/hashing.py 同算法。"""
    m, r = 0xC6A4A7935BD1E995, 47
    h = (m * len(data)) & MASK64
    off = (len(data) // 8) * 8
    for pos in range(0, off, 8):
        k = int.from_bytes(data[pos:pos + 8], "little")
        k = (k * m) & MASK64
        k ^= k >> r
        k = (k * m) & MASK64
        h = ((h ^ k) * m) & MASK64
    tail = len(data) & 7
    for i in range(tail, 0, -1):
        h ^= data[off + i - 1] << (8 * (i - 1))
    if tail:
        h = (h * m) & MASK64
    h ^= h >> r
    h = (h * m) & MASK64
    h ^= h >> r
    return h


def murmur32(name: str) -> int:
    """引擎 32 位名字哈希 = murmur64(seed=0) >> 32。

    服务器的 `GalacticWarEffects`（effectType=71）用这个值指向 presence：
    `values[0] == murmur32(presence 名)`，见 docs/tables/PLANET-TABLES-26088801.md §3.6。
    """
    return murmur64_seed0(name.encode("utf-8")) >> 32


def presence_names() -> list[str]:
    """本地 presence 表的 137 个名字（读明文缓存；不在就返回空）。"""
    import struct
    from planet_tables import PLAIN, parse_groups
    path = PLAIN / "generated_galactic_presence_settings.dl_bin"
    if not path.exists():
        return []
    names = []
    for g in parse_groups(path.read_bytes()):
        tail = g.payload[1000:]
        got = [m.group().decode("latin1") for m in __import__("re").finditer(rb"[ -~]{3,}", tail)]
        names.append(next((x for x in got if x != "None" and not x.startswith("content/")), "(unnamed)"))
    return names


def load_planets() -> list[dict]:
    if not PLANET_JSON.exists():
        raise SystemExit(f"缺少 {PLANET_JSON}（先跑 planet-data 解码）")
    rows = json.loads(PLANET_JSON.read_text(encoding="utf-8"))
    out = []
    for r in rows:
        setup = ""
        inh = r.get("inherits") or ""
        if inh:
            setup = inh.rsplit("/", 1)[-1].replace("planet_", "")
        reg = r.get("region_lowland") or {}
        out.append({
            "index": r["index"],
            "name": r.get("planet_name") or "",
            "biome": BIOME.get(r.get("planet_type"), str(r.get("planet_type"))),
            "planet_type": r.get("planet_type"),
            "setup": setup,
            "region": reg.get("family") or reg.get("name") or "",
            "region_type": reg.get("type"),
            "debug_name": r.get("debug_name") or "",
            "locid": (r.get("locids") or {}).get("name"),
            "samples": r.get("samples") or [],
        })
    return out


def load_live(directory: pathlib.Path) -> dict:
    """从抓包目录里取 Status → {planet_index: {owner, effects:[id]}}；缺就返回空。"""
    if not directory.exists():
        return {}
    status, effects = None, {}
    for p in sorted(directory.glob("*.json")):
        try:
            doc = json.loads(p.read_text(encoding="utf-8", errors="replace"))
        except Exception:
            continue
        if isinstance(doc, dict) and "planetActiveEffects" in doc:
            status = doc
        if isinstance(doc, list) and doc and isinstance(doc[0], dict) and "effectType" in doc[0]:
            for e in doc:
                if isinstance(e.get("values"), list) and e["values"]:
                    effects[e["id"]] = (e.get("effectType"), e["values"][0])
    if not status:
        return {}
    # 用 murmur32(presence 名) 反查 presence 名（自包含实现，不依赖仓库外的工具）
    by_m32 = {murmur32(n): n for n in presence_names() }
    live: dict[int, dict] = {}
    for e in status.get("planetActiveEffects") or []:
        idx, eid = e.get("index"), e.get("galacticEffectId")
        rec = live.setdefault(idx, {"owner": None, "effects": [], "presences": []})
        rec["effects"].append(eid)
        hit = by_m32.get((effects.get(eid) or (None, None))[1])
        if hit:
            rec["presences"].append(hit)
    for r in status.get("planetStatus") or []:
        idx = r.get("index")
        if isinstance(idx, int) and idx in live:
            live[idx]["owner"] = OWNER.get(r.get("owner"), r.get("owner"))
    return live


def render_md(rows: list[dict], live: dict) -> str:
    L = ["# 行星索引表（build 26088801）", "",
         "> 行号 = 游戏里的行星索引（`planetActiveEffects.index` / `planetStatus.index` 用的就是它）。",
         "> 名称取自 `planet_data.+0x008` 的 locid（**本 build 数据里只有英文语料**），生态取自 `+0x1B8 PlanetType`，",
         "> region 取自 `+0x060 RegionLowland`（指向 `region_settings` 段 1）。",
         "> 39 行没有名字：都是模板行（`Inherits` 为空），`debug_name` 保留生态提示。",
         "> 「当前 presence」列只有抓到 Status 时才有（网络层，不入库）。", ""]
    named = sum(1 for r in rows if r["name"])
    L += [f"共 **{len(rows)}** 行，其中 **{named}** 行有显示名。", "",
          "| # | 名称 | 生态 | setup | region | 当前 presence | debug_name |",
          "|---:|---|---|---|---|---|---|"]
    for r in rows:
        p = live.get(r["index"]) or {}
        pres = ", ".join(dict.fromkeys(p.get("presences") or [])) or ""
        L.append(f'| {r["index"]} | {r["name"] or "—"} | {r["biome"]} | {r["setup"] or "—"} | '
                 f'{r["region"] or "—"} | {pres} | `{r["debug_name"]}` |')
    return "\n".join(L) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--live-dir", default=str(DEFAULT_LIVE), help="抓包目录（含 Status json），缺省 D:/mod/out/gwe")
    ap.add_argument("--no-md", action="store_true", help="只写 json/csv，不写 markdown")
    a = ap.parse_args()

    rows = load_planets()
    live = load_live(pathlib.Path(a.live_dir))

    md = ROOT / "docs" / "tables" / "PLANET-INDEX-26088801.md"
    if not a.no_md:
        md.write_text(render_md(rows, live), encoding="utf-8")
        print(f"wrote {md} ({len(rows)} rows, {sum(1 for r in rows if r['name'])} named)")

    js = ROOT / "out" / "planet" / "planet-index.json"
    payload = [dict(r, **({"live": live[r["index"]]} if r["index"] in live else {})) for r in rows]
    js.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"wrote {js}")

    if live:
        out = pathlib.Path(r"D:/mod/work/variant-net/out")
        out.mkdir(parents=True, exist_ok=True)
        csv_path = out / "planet-live.csv"
        with csv_path.open("w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["index", "name", "biome", "owner", "effects", "presences"])
            for r in rows:
                p = live.get(r["index"])
                if not p:
                    continue
                w.writerow([r["index"], r["name"], r["biome"], p.get("owner") or "",
                            " ".join(str(x) for x in p.get("effects") or []),
                            ";".join(dict.fromkeys(p.get("presences") or []))])
        print(f"wrote {csv_path}（{len(live)} 颗有生效效果的星球）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
