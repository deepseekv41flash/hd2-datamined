#!/usr/bin/env python3
"""xcheck_projectile_names.py -- 把弹丸 type id 贴上 wiki 枚举名，并做批量数值交叉验证。

WHY
    `generated_projectile_settings.dl_bin` 的行只有数字 id（`+0`），没有名字；社区/wiki 的
    projectile 模块行却有枚举名（`Pistol_9x20mm_fmj`、`P-2_P`…）。两边各自都只有一半：
      * 我们这边：实体 →（默认弹种配件的 entity delta，或实体自带的 `ProjectileWeapon+0`）→ 数字 id
      * wiki 镜像 `wiki.sqlite`：武器页 → weapon 模块 `attacks[].name` → 枚举名；projectile/damage
        模块行给出 caliber / velocity / mass / pen_slow / dmg / dmg2
    按武器名 join，就能给 id 贴名，并用数值字段反向验证"delta 解出来的 id 对不对"。

WHAT IT FOUND (build 26088801, 2026-10-27)
    61 个武器精确 join；size / velocity / mass / pen_slow 61/61 全中，dmg/dmg2 49/60（其余是
    wiki 快照版本旧、伤害被后续补丁改过）。P-19 Redeemer → 296 (`Pistol_9x20mm_fmj`)，
    P-2 Peacemaker → 342 (`P-2_P`，6/6，含 damage 100/20)；P-19 的伤害差是 wiki 旧值
    （60/5）对现档（70/12）。

USAGE
    python tools/xcheck_projectile_names.py \
        --wiki D:/mod/refs/wiki/wiki.sqlite \
        --plaintext D:/mod/refs/dlbin/plaintext-26251122 \
        --csv D:/mod/refs/exports/weapon_customization_settings.csv \
        --out D:/mod/out/wiki-proj-names.json
"""
from __future__ import annotations

import argparse
import collections
import csv
import json
import pathlib
import sqlite3
import struct
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import entity_locid_scan as scan                          # noqa: E402
from table_dictionary import Dictionary, load_names        # noqa: E402


def load_entity_names(path: pathlib.Path) -> dict[int, dict]:
    """refs/entity-locid-names.json → {实体键: {name, code}}（吃掉 placeholder）。"""
    out: dict[int, dict] = {}
    if not path.is_file():
        return out
    data = json.loads(path.read_text(encoding="utf-8"))
    tables = data.get("name_tables") or []
    if isinstance(tables, dict):
        tables = list(tables.values())
    for table in tables:
        entries = table.get("entries") if isinstance(table, dict) else table
        for item in entries or []:
            if not isinstance(item, dict) or not item.get("key"):
                continue
            if item.get("quality") == "placeholder":
                continue
            try:
                key = int(item["key"], 16)
            except (TypeError, ValueError):
                continue
            out.setdefault(key, {"name": item.get("name") or item.get("name_upper"),
                                 "code": item.get("code") or ""})
    return out


def load_customization_csv(path: pathlib.Path) -> dict[int, dict]:
    """配件总表 CSV：optionId(+8) → {name, slot, addpath(+32)}。"""
    out: dict[int, dict] = {}
    if not path.is_file():
        return out
    with open(path, encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f)
        header = next(reader, None) or []
        col = {name: i for i, name in enumerate(header)}
        for row in reader:
            def num(name: str) -> int:
                i = col.get(name)
                if i is None or i >= len(row):
                    return 0
                token = row[i].split("/")[0].strip()
                return int(token, 16) if token.lower().startswith("0x") else 0
            oid = num("+8")
            if oid:
                out[oid] = {"name": row[2] if len(row) > 2 else "",
                            "slot": row[3] if len(row) > 3 else "",
                            "addpath": num("+32")}
    return out


def load_delta_projectiles(plaintext: pathlib.Path) -> dict[int, int]:
    """AddPath → 该配件 delta 写进 ProjectileWeapon+0 的弹丸 id（没有就缺省）。"""
    dd = (plaintext / "generated_entity_deltas.dl_bin").read_bytes()
    j = dd.find(b"LDLD")
    if j < 0:
        return {}
    p0 = j - 4 + 28
    o_h, n_h = struct.unpack_from("<QQ", dd, p0)
    o_s, _ = struct.unpack_from("<QQ", dd, p0 + 16)
    o_c, _ = struct.unpack_from("<QQ", dd, p0 + 32)
    o_d, _ = struct.unpack_from("<QQ", dd, p0 + 48)
    o_x, _ = struct.unpack_from("<QQ", dd, p0 + 64)

    def u32(o: int) -> int:
        return struct.unpack_from("<I", dd, p0 + o)[0]

    out: dict[int, int] = {}
    for s in range(n_h):
        key, sidx, _pad = struct.unpack_from("<QII", dd, p0 + o_h + 16 * s)
        if not key:
            continue
        n, first = u32(o_s + sidx * 8), u32(o_s + sidx * 8 + 4)
        for i in range(n):
            comp = u32(o_c + (first + i) * 12)
            fd, dc = u32(o_c + (first + i) * 12 + 4), u32(o_c + (first + i) * 12 + 8)
            if comp != 324:                       # ProjectileWeaponComponentData（本 build 实测）
                continue
            for k in range(dc):
                mo, sz, raw = (u32(o_d + (fd + k) * 12), u32(o_d + (fd + k) * 12 + 4),
                               u32(o_d + (fd + k) * 12 + 8))
                if mo == 0 and sz == 4:
                    out[key] = u32(o_x + raw)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="弹丸 id ↔ wiki 枚举名 + 批量数值交叉验证")
    ap.add_argument("--plaintext", default=r"D:\mod\refs\dlbin\plaintext-26251122")
    ap.add_argument("--wiki", default=r"D:\mod\refs\wiki\wiki.sqlite")
    ap.add_argument("--csv", default=r"D:\mod\refs\exports\weapon_customization_settings.csv")
    ap.add_argument("--names", default=r"D:\mod\dl-type-names.json",
                    help="typelib 类型名 json（解实体块几何用）")
    ap.add_argument("--entity-names", default=r"D:\mod\refs\entity-locid-names.json")
    ap.add_argument("--out", default=r"D:\mod\out\wiki-proj-names.json")
    a = ap.parse_args()

    plain = pathlib.Path(a.plaintext)
    dic = Dictionary((plain / "dl_library.dl_typelib").read_bytes(), load_names(pathlib.Path(a.names)))
    ent = (plain / "generated_entities.dl_bin").read_bytes()
    blocks = scan.parse_blocks(ent)

    def block(name: str):
        for b in blocks:
            if dic.name(b["type_id"]) == name:
                g = scan.check_geometry(ent, b, scan.geometry(dic, b))
                if g["ok"]:
                    return b, g
        return None, None

    info = load_entity_names(pathlib.Path(a.entity_names))
    opt2row = load_customization_csv(pathlib.Path(a.csv))
    delta = load_delta_projectiles(plain)

    # 默认槽：WeaponCustomizationComponentData 的 (slot, optionId) 对
    cb, cg = block("WeaponCustomizationComponentData")
    if cb is None:
        print("✗ 没找到 WeaponCustomizationComponentData")
        return 2
    for key, row in scan.hashmap(ent, cb, cg).items():
        base = cb["payload_at"] + cg["index_size"] + row * cg["stride"]
        for i in range(24):
            slot, opt = struct.unpack_from("<II", ent, base + 8 * i)
            if slot == 0:
                break
            if slot == 6 and opt in opt2row:
                v = info.setdefault(key, {})
                v["ammo_name"] = opt2row[opt]["name"]
                v["ammo_addpath"] = opt2row[opt]["addpath"]
                v["delta_proj"] = delta.get(opt2row[opt]["addpath"])

    # 实体自带弹丸（ACTIVE_DIRECT 路径）
    pb, pg = block("ProjectileWeaponComponentData")
    if pb is None:
        print("✗ 没找到 ProjectileWeaponComponentData")
        return 2
    for key, row in scan.hashmap(ent, pb, pg).items():
        base = pb["payload_at"] + pg["index_size"] + row * pg["stride"]
        info.setdefault(key, {})["base_proj"] = struct.unpack_from("<I", ent, base)[0]

    # 只留真装备（LoadoutEntry item_type 1/2/3）
    lb, lg = block("LoadoutEntryComponentData")
    loadout = {}
    if lb is not None:
        for key, row in scan.hashmap(ent, lb, lg).items():
            base = lb["payload_at"] + lg["index_size"] + row * lg["stride"]
            loadout[key] = struct.unpack_from("<I", ent, base + 4)[0]

    # 弹丸表 / 伤害表
    pr = (plain / "generated_projectile_settings.dl_bin").read_bytes()
    proj_base = 28 + 16
    ids = [struct.unpack_from("<I", pr, proj_base + i * 272)[0] for i in range(355)]
    proj = {}
    for i, tid in enumerate(ids):
        r = proj_base + i * 272
        f = lambda o: struct.unpack_from("<f", pr, r + o)[0]     # noqa: E731
        u = lambda o: struct.unpack_from("<I", pr, r + o)[0]     # noqa: E731
        proj[tid] = {"size": f(0x18), "velocity": f(0x20), "mass": f(0x24),
                     "penslow": f(0x40), "dmg_row": u(0x3C)}
    dm = (plain / "generated_damage_settings.dl_bin").read_bytes()
    dmg = {}
    for i in range(661):
        r = 100 + i * 76
        dmg[struct.unpack_from("<I", dm, r)[0]] = struct.unpack_from("<ii", dm, r + 4)

    # wiki
    db = sqlite3.connect(a.wiki)
    db.row_factory = sqlite3.Row
    pages = {r["title"]: r for r in db.execute("SELECT * FROM page WHERE kind='weapon'")}
    weapons = {}
    for r in db.execute("SELECT key,json FROM weapon"):
        try:
            weapons[r["key"].upper()] = json.loads(r["json"])
        except json.JSONDecodeError:
            pass
    projmods = collections.defaultdict(list)
    dmgmods = collections.defaultdict(list)
    for r in db.execute("SELECT section,key,json FROM entity"):
        try:
            item = json.loads(r["json"])
        except json.JSONDecodeError:
            continue
        if r["section"] == "projectile":
            projmods[r["key"]].append(item)
        elif r["section"] == "damage":
            dmgmods[r["key"]].append(item)

    # 精确标题 join："<code> <name>"；同页只留一个实体（优先有 delta 的）
    by_title = {}
    for key, v in info.items():
        if loadout.get(key) not in (1, 2, 3):
            continue
        name = v.get("name")
        if not name:
            continue
        title = f"{v.get('code') or ''} {name}".strip()
        if title not in pages:
            continue
        score = (v.get("delta_proj") is not None, bool(v.get("base_proj")), key)
        if title not in by_title or score > by_title[title][0]:
            by_title[title] = (score, key, v)

    results, id2names = [], collections.defaultdict(set)
    for title, (_s, key, v) in by_title.items():
        page = pages[title]
        module = weapons.get((page["attack_key"] or "").upper())
        if not module:
            continue
        attacks = [x for x in (module.get("attacks") or []) if x.get("type") == "projectile"]
        if len(attacks) != 1:
            continue
        pname = attacks[0].get("name")
        pid = v.get("delta_proj") if v.get("delta_proj") is not None else v.get("base_proj")
        if pid is None or pname is None or pid not in proj:
            continue
        our = proj[pid]
        row = dmg.get(our["dmg_row"])
        checks = []
        best = None
        for mod in projmods.get(pname, []):
            cand = []
            for label, ours, theirs in (
                    ("size", our["size"], mod.get("caliber")),
                    ("vel", our["velocity"], mod.get("velocity")),
                    ("mass", our["mass"], mod.get("mass")),
                    ("penslow", our["penslow"], mod.get("pen_slow") or mod.get("penslow"))):
                if theirs is None:
                    continue
                cand.append((label, abs(float(ours) - float(theirs)) < 0.051, ours, theirs))
            for d in dmgmods.get(mod.get("damageid") or mod.get("damage_id") or "", []):
                if row and "dmg" in d:
                    cand.append(("dmg", row[0] == d["dmg"], row[0], d["dmg"]))
                    if "dmg2" in d:
                        cand.append(("dmg2", row[1] == d["dmg2"], row[1], d["dmg2"]))
                    break
            if cand and (best is None or sum(c[1] for c in cand) > sum(c[1] for c in best)):
                best = cand
        if not best:
            continue
        checks = best
        id2names[pid].add(pname)
        results.append({"title": title, "pid": pid, "pname": pname,
                        "ammo": v.get("ammo_name"), "delta": v.get("delta_proj") is not None,
                        "score": sum(1 for c in checks if c[1]), "n": len(checks), "checks": checks})

    ft, fo = collections.Counter(), collections.Counter()
    for r in results:
        for label, ok, _o, _t in r["checks"]:
            ft[label] += 1
            fo[label] += ok
    full = [r for r in results if r["score"] == r["n"]]
    print(f"join 到 wiki 的武器：{len(results)}；全字段一致：{len(full)}")
    print("字段一致率：", "  ".join(f"{k} {fo[k]}/{ft[k]}" for k in sorted(ft)))
    print(f"\n{'code/name':34s} {'pid':>4} {'wiki projectile':30s} fields verdict")
    for r in sorted(results, key=lambda x: x["title"]):
        detail = " ".join(f"{l}:{o}/{t}" for l, ok, o, t in r["checks"] if not ok)
        print(f"{r['title'][:34]:34s} {r['pid']:>4} {r['pname'][:30]:30s} "
              f"{r['score']}/{r['n']:<4} {'✓' if r['score'] == r['n'] else '~ ' + detail}")
    conflicts = {pid: sorted(n) for pid, n in id2names.items() if len(n) > 1}
    print(f"\n弹丸 id -> wiki 名：{len(id2names)} 个 id；一名多 id 冲突 {len(conflicts)} 个")
    dest = pathlib.Path(a.out)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps({str(k): sorted(v) for k, v in id2names.items()},
                               ensure_ascii=False, indent=1), encoding="utf-8")
    print("wrote", dest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
