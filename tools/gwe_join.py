#!/usr/bin/env python3
"""gwe_join.py -- 把 `GalacticWarEffects`（约 300 条 effect）对到本地对象空间，产出能力边界报告。

WHY
    「让引擎相信服务器说了什么」这条通道能做什么，取决于那张 effect 菜单：每条 effect 的
    `effectType` 决定引擎用哪个**解释器**，`values` 决定它指向哪个**本地对象**。
    这个工具就是那张表的对表器：effect → presence / 战备 / 未知，并统计覆盖率与未对上的值。

SCHEMA TOLERANCE (by design)
    我们还没见过真实 dump 的字段名。工具会在任何层级的数组里找「像 effect 的 dict」，
    依次尝试 `id/effectId/effect_id/Id`、`effectType/effect_type/type/kind`、`values/value/params/args`，
    并把**实际看到的键名**打印出来。第一次跑的输出就用来把 schema 钉死。

JOINS
    1. `effectType=71` 与 presence：`values[0]` 是 presence 身份键（两个 u32 = lo/hi，
       u64 = hi<<32|lo）。本地表 137 行，身份键见 `tools/planet_tables.py`。
    2. `effectType=32` 与战备：`variant_mod/stratagem_catalog.json` 的 `native_hash`/`effect_hash`
       是 8 位十六进制（u32），与 values 的 32 位截断比。
    3. 任意 effect 的 **id** 与 `variant_catalog.json` 的变种 id（1243/1245…）比 —— 那是 effect id，
       不是 values。
    4. 32/40/71 之外的类型 → 「新解释器候选」，说明引擎还有别的分派分支。

USAGE
    python tools/gwe_join.py report --gwe out/gwe --out out/planet/gwe-report.json
    python tools/gwe_join.py selftest       # 合成 effect 表，验三类匹配 + 一个能失败的对照
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

PLAIN = pathlib.Path(r"D:/mod/refs/dlbin/plaintext-26088801")
CASE = pathlib.Path(r"D:/Downloads/variant_mod")

ID_KEYS = ("id", "effectId", "effect_id", "Id", "effectID")
TYPE_KEYS = ("effectType", "effect_type", "type", "kind", "EffectType")
VAL_KEYS = ("values", "value", "params", "args", "valuesList")


# ----------------------------------------------------------------------------- inputs
def load_presence(path: pathlib.Path | None = None) -> list[dict]:
    """137 条 presence：名字 / RaceType / 身份键 (lo,hi) / 类别键。"""
    p = path or (PLAIN / "generated_galactic_presence_settings.dl_bin")
    if not p.exists():
        return []
    import struct
    import re as _re
    d = p.read_bytes()
    pos, rows = 4, []
    while pos + 24 <= len(d) and d[pos:pos + 4] == b"LDLD":
        ver, tid, size, wide, flags = struct.unpack_from("<IIIII", d, pos + 4)
        payload = d[pos + 24: pos + 24 + size]
        strs = [m.group().decode("latin1") for m in _re.finditer(rb"[ -~]{3,}", payload[1000:])]
        name = next((x for x in strs if x != "None" and not x.startswith("content/")), "(unnamed)")
        b = payload[:1000]
        lo = struct.unpack_from("<I", b, 0x20)[0]
        hi = struct.unpack_from("<I", b, 0x24)[0]
        rows.append({"index": len(rows), "name": name, "race": struct.unpack_from("<I", b, 0x1C)[0],
                     "kind": struct.unpack_from("<I", b, 0x14)[0],
                     "key_lo": lo, "key_hi": hi, "key64": (hi << 32) | lo,
                     "category": struct.unpack_from("<Q", b, 0x28)[0]})
        pos += 24 + size
    return rows


def load_stratagem(path: pathlib.Path) -> list[dict]:
    if not path.exists():
        return []
    doc = json.loads(path.read_text(encoding="utf-8"))
    return doc.get("items") or []


def load_variants(path: pathlib.Path) -> dict[int, str]:
    if not path.exists():
        return {}
    doc = json.loads(path.read_text(encoding="utf-8"))
    out: dict[int, str] = {}
    for name, ids in (doc.get("variants") or {}).items():
        for i in ids:
            out[int(i)] = name
    return out


def find_effect_items(doc) -> tuple[list[dict], str]:
    """在任何层级找「像 effect 的 dict 数组」，返回 (items, 来源路径)。"""
    best: tuple[list[dict], str] = ([], "")
    stack = [("$", doc)]
    while stack:
        where, node = stack.pop()
        if isinstance(node, dict):
            for k, v in node.items():
                stack.append((f"{where}.{k}", v))
        elif isinstance(node, list) and node:
            dicts = [x for x in node if isinstance(x, dict)]
            if dicts and any(any(k in x for k in ID_KEYS) for x in dicts[:5]):
                if len(dicts) > len(best[0]):
                    best = (dicts, where)
    return best


def norm(item: dict) -> dict:
    def pick(keys):
        for k in keys:
            if k in item:
                return item[k], k
        return None, ""
    eid, idk = pick(ID_KEYS)
    etype, typek = pick(TYPE_KEYS)
    vals, valk = pick(VAL_KEYS)
    if isinstance(vals, dict):
        vals = list(vals.values())
    if not isinstance(vals, list):
        vals = [] if vals is None else [vals]
    ints = []
    for v in vals:
        if isinstance(v, bool):
            continue
        if isinstance(v, int):
            ints.append(v)
        elif isinstance(v, float) and v.is_integer():
            ints.append(int(v))
        elif isinstance(v, str):
            try:
                ints.append(int(v, 0))
            except ValueError:
                pass
        elif isinstance(v, dict):
            for k in ("value", "Value", "id", "hash"):
                if isinstance(v.get(k), int):
                    ints.append(v[k])
                    break
    return {"id": eid if isinstance(eid, int) else None, "id_key": idk,
            "type": etype if isinstance(etype, int) else None, "type_key": typek,
            "values": ints, "val_key": valk, "arity": len(ints)}


# ----------------------------------------------------------------------------- report
def build_report(gwe_paths: list[pathlib.Path], presence: list[dict],
                 stratagems: list[dict], variants: dict[int, str]) -> dict:
    by_key = {r["key64"]: r for r in presence if r["key64"]}
    by_lo: dict[int, list[dict]] = {}
    for r in presence:
        if r["key_lo"]:
            by_lo.setdefault(r["key_lo"], []).append(r)
    strat_index: dict[int, dict] = {}
    for it in stratagems:
        for f in ("native_hash", "effect_hash"):
            h = str(it.get(f) or "")
            if h:
                try:
                    strat_index.setdefault(int(h, 16), it)
                except ValueError:
                    pass

    files = []
    all_items: list[dict] = []
    seen_keys: set[str] = set()
    for p in gwe_paths:
        raw = p.read_bytes()
        rec = {"file": p.name, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()[:16]}
        try:
            doc = json.loads(raw.decode("utf-8", "replace"))
        except Exception as e:
            rec["error"] = f"not json: {e!r}"
            files.append(rec)
            continue
        items, where = find_effect_items(doc)
        rec.update({"items": len(items), "found_at": where,
                    "top_level": type(doc).__name__,
                    "item_keys": sorted({k for x in items[:5] for k in x})[:14]})
        files.append(rec)
        for it in items:
            n = norm(it)
            if n["id"] is None:
                continue
            key = f'{n["id"]}:{n["type"]}'
            if key in seen_keys:
                continue
            seen_keys.add(key)
            all_items.append(n)

    types: dict[str, list[dict]] = {}
    unmatched: dict[int, int] = {}
    used_presence: set[int] = set()
    rows = []
    for n in all_items:
        hits = []
        for v in n["values"]:
            if v in by_key:
                r = by_key[v]
                hits.append({"kind": "presence", "value": v, "row": r["index"], "name": r["name"],
                             "race": r["race"], "strength": "exact64"})
                used_presence.add(r["index"])
            elif v in by_lo and v > 0xFFFF:
                cands = by_lo[v]
                hits.append({"kind": "presence_lo", "value": v,
                             "rows": [c["index"] for c in cands][:4],
                             "names": [c["name"] for c in cands][:4], "strength": "weak32"})
            if (v & 0xFFFFFFFF) in strat_index:
                st = strat_index[v & 0xFFFFFFFF]
                hits.append({"kind": "stratagem", "value": v, "id": v & 0xFFFFFFFF,
                             "name": st.get("name") or st.get("key"), "strength": "u32"})
        label = variants.get(n["id"])
        row = {"id": n["id"], "type": n["type"], "arity": n["arity"],
               "values": n["values"][:6], "hits": hits, "variant": label}
        rows.append(row)
        types.setdefault(str(n["type"]), []).append(row)
        if not hits:
            for v in n["values"]:
                unmatched[v] = unmatched.get(v, 0) + 1

    # 40(tag) 与 71(mechanic) 的邻接配对（案例里是 1:1 成对注入；这里只做启发式）
    pairs = []
    by_id = {r["id"]: r for r in rows}
    for r in rows:
        if r["type"] == 71:
            for d in (1, -1, 2, -2):
                other = by_id.get((r["id"] or 0) + d)
                if other and other["type"] == 40:
                    pairs.append({"tag": other["id"], "mechanic": r["id"],
                                  "variant": r["variant"] or other["variant"],
                                  "presence": [h.get("name") for h in r["hits"] if h.get("kind") == "presence"]})
                    break

    return {
        "files": files,
        "schema": {"id_keys_seen": sorted({n['id_key'] for n in all_items}),
                   "type_keys_seen": sorted({n['type_key'] for n in all_items}),
                   "value_keys_seen": sorted({n['val_key'] for n in all_items})},
        "effects": len(all_items),
        "types": {t: {"count": len(v),
                      "arities": sorted({r['arity'] for r in v}),
                      "ids": [r["id"] for r in v][:40],
                      "sample_values": [r["values"] for r in v][:5]}
                  for t, v in sorted(types.items(), key=lambda kv: -len(kv[1]))},
        "coverage": {"presence_rows": len(presence),
                     "presence_rows_referenced": len(used_presence),
                     "presence_unreferenced": len(presence) - len(used_presence),
                     "stratagem_items": len(stratagems)},
        "pairs": pairs,
        "unmatched_values": sorted(unmatched.items(), key=lambda kv: -kv[1])[:40],
        "rows": rows,
    }


def render_md(rep: dict) -> str:
    L = ["# GalacticWarEffects 对表报告", ""]
    L.append("| 文件 | 字节 | items | 位置 | 顶层 | 前几个键 |")
    L.append("|---|---:|---:|---|---|---|")
    for f in rep["files"]:
        L.append(f'| {f["file"]} | {f["bytes"]} | {f.get("items", "-")} | `{f.get("found_at", "")}` '
                 f'| {f.get("top_level", "")} | {", ".join(f.get("item_keys", [])[:8])} |')
    L += ["", f'实际字段名：id={rep["schema"]["id_keys_seen"]} · type={rep["schema"]["type_keys_seen"]} '
              f'· values={rep["schema"]["value_keys_seen"]}', "",
          "## 解释器分布（effectType）", "", "| type | 条数 | 元数(arity) | 前几个 id |", "|---:|---:|---|---|"]
    for t, v in rep["types"].items():
        L.append(f'| **{t}** | {v["count"]} | {v["arities"]} | {v["ids"][:10]} |')
    L += ["", "## 覆盖率", "",
          f'* effect 总数：**{rep["effects"]}**',
          f'* 本地 presence 被引用：**{rep["coverage"]["presence_rows_referenced"]}/{rep["coverage"]["presence_rows"]}**'
          f'（未引用 {rep["coverage"]["presence_unreferenced"]}）',
          f'* 战备目录：{rep["coverage"]["stratagem_items"]} 条', "",
          "## tag / mechanic 配对（邻接启发式，⚠ 需用 Status 共现复核）", ""]
    if rep["pairs"]:
        L += ["| tag id | mechanic id | 变种 | presence |", "|---:|---:|---|---|"]
        for p in rep["pairs"][:30]:
            L.append(f'| {p["tag"]} | {p["mechanic"]} | {p["variant"] or ""} | {", ".join(x for x in p["presence"] if x)} |')
    else:
        L.append("（没有邻接对；说明配对不是按 id 相邻，需要用 Status 的共现次数推）")
    L += ["", "## 没对上的 values（前 40）", ""]
    L.append("这些值不属于任何本地 presence / 战备 —— 可能是别类对象（修饰符、实体、或纯数字参数），"
             "也可能指向我们还没加载的表。")
    for v, c in rep["unmatched_values"]:
        L.append(f"* `0x{v:016X}` ({v}) ×{c}")
    return "\n".join(L) + "\n"


def cmd_report(a) -> int:
    gwe = pathlib.Path(a.gwe)
    paths = sorted(gwe.glob("*.json")) if gwe.is_dir() else [gwe]
    if not paths:
        print(f"FAIL 没找到 dump（{gwe}）")
        return 2
    rep = build_report(paths, load_presence(a.presence and pathlib.Path(a.presence)),
                       load_stratagem(pathlib.Path(a.stratagem)),
                       load_variants(pathlib.Path(a.variants)))
    out = pathlib.Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    md = out.with_suffix(".md")
    md.write_text(render_md(rep), encoding="utf-8")
    print(f"wrote {out} + {md}")
    print(f"effects={rep['effects']} types={[(t, v['count']) for t, v in rep['types'].items()]}")
    print(f"presence 覆盖 {rep['coverage']['presence_rows_referenced']}/{rep['coverage']['presence_rows']}")
    return 0


def cmd_selftest(a) -> int:
    presence = load_presence()
    if not presence:
        print("SKIP 没有本地 presence 明文（先跑 tools/build_cache.py）")
        return 0
    strat = load_stratagem(CASE / "stratagem_catalog.json")
    variants = load_variants(CASE / "variant_catalog.json")
    target = next(r for r in presence if r["name"] == "bugs_super_predator")
    mech = next(iter(strat), None)

    fake = [
        {"id": 1243, "effectType": 40, "values": []},
        {"id": 1245, "effectType": 71, "values": [target["key64"]]},
        {"id": 1227, "effectType": 32, "values": [int(str(mech["native_hash"]), 16)] if mech else []},
        {"id": 9999, "effectType": 99, "values": [0xDEADBEEFCAFE]},
    ]
    d = pathlib.Path(a.workdir)
    d.mkdir(parents=True, exist_ok=True)
    f = d / "selftest_gwe.json"
    f.write_text(json.dumps({"effects": fake}, ensure_ascii=False), encoding="utf-8")

    rep = build_report([f], presence, strat, variants)
    rows = {r["id"]: r for r in rep["rows"]}
    checks = []

    checks.append(("找到 effect 数组", rep["effects"] == 4, rep["effects"]))
    hit = rows[1245]["hits"]
    checks.append(("type71 values[0] 命中 presence（bugs_super_predator）",
                   any(h.get("name") == "bugs_super_predator" for h in hit), hit))
    checks.append(("effect id 认出变种名（掠食变种）", rows[1245]["variant"] == "掠食变种", rows[1245]["variant"]))
    if mech:
        s_hit = [h for h in rows[1227]["hits"] if h.get("kind") == "stratagem"]
        checks.append((f"type32 命中战备（{mech.get('name')}）", bool(s_hit), s_hit))
    checks.append(("未知类型进「新解释器候选」", "99" in rep["types"], list(rep["types"])))
    checks.append(("未对上的值被记账", any(v == 0xDEADBEEFCAFE for v, _ in rep["unmatched_values"]), rep["unmatched_values"][:2]))
    checks.append(("tag/mechanic 邻接配对成立", any(p["tag"] == 1243 and p["mechanic"] == 1245 for p in rep["pairs"]), rep["pairs"]))

    # 能失败的对照：把 presence 键改坏，必须不再命中
    bad = [dict(x) for x in fake]
    bad[1]["values"] = [target["key64"] ^ 0xFFFFFFFFFFFFFFFF]
    f2 = d / "selftest_negative.json"
    f2.write_text(json.dumps(bad, ensure_ascii=False), encoding="utf-8")
    rep2 = build_report([f2], presence, strat, variants)
    r2 = {r["id"]: r for r in rep2["rows"]}
    checks.append(("对照：键被改坏后不再命中 presence",
                   not any(h.get("kind") == "presence" for h in r2[1245]["hits"]), r2[1245]["hits"]))

    ok = True
    for name, good, detail in checks:
        print(f"[{'PASS' if good else 'FAIL'}] {name}" + ("" if good else f"  <- {detail}"))
        ok &= good
    print("RESULT=" + ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("report", help="对表并产出 JSON + Markdown")
    s.add_argument("--gwe", required=True, help="dump 目录或单个 json")
    s.add_argument("--out", default="out/planet/gwe-report.json")
    s.add_argument("--presence", default="", help="presence 明文（缺省用本 build 缓存）")
    s.add_argument("--stratagem", default=str(CASE / "stratagem_catalog.json"))
    s.add_argument("--variants", default=str(CASE / "variant_catalog.json"))
    s.set_defaults(func=cmd_report)
    s = sub.add_parser("selftest", help="合成 effect 表，验三类匹配 + 一个能失败的对照")
    s.add_argument("--workdir", default="out/gwe/selftest")
    s.set_defaults(func=cmd_selftest)
    a = ap.parse_args()
    return a.func(a)


if __name__ == "__main__":
    sys.exit(main())
