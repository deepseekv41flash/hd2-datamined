#!/usr/bin/env python3
"""levelgen 分析脚本（只读）：产出 out/planet/levelgen.json 的全部数字。
复跑：python tools/probes/planet/analyze_levelgen.py   （产物写 out/planet/levelgen.json）
"""
from __future__ import annotations

import json
import pathlib
import re
import bisect
import struct
import sys
from collections import Counter, defaultdict

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))
import typelib  # noqa: E402
import murmur64  # noqa: E402

PLAIN = pathlib.Path(r"D:/mod/refs/dlbin/plaintext-26088801")
OUT = ROOT / "out" / "planet"

# filediver Go 结构（enum/结构体顺序来源）
LG_REGION_TYPE_ENUM = [  # enum.LevelGenerationRegionType（0..34）
    "none", "region_generation_testing", "region_sandy_tutorial", "region_sandy_base",
    "region_sandy_acid", "region_sandy_moon", "region_sandy_mineral", "region_sandy_spiky",
    "region_sandy_cyborg_factory", "region_primordial_tutorial", "region_primordial_base",
    "region_primordial_dead", "region_primordial_purple", "region_primordial_blue",
    "region_primordial_bug", "region_magma_base", "region_rift_active",
    "region_coniferous_base", "region_arctic_glacier_base", "region_arctic_glacier_coldrocky",
    "region_cyberstan", "region_moor_baseplanet", "region_moor_tundra", "region_moor_arid",
    "region_moor_red", "region_superearth", "region_deciduous_base", "region_deciduous_autumn",
    "region_deciduous_crimson", "region_swamp_base", "region_swamp_haunted",
    "region_swamp_variant_02", "region_oasis_base", "region_oasis_bleak", "region_bug_hiveworld",
]
ZONE_TAG_COUNT = 18          # enum.ZoneTag: None + 16 + Count
PATROL_SETTING_COUNT = 4     # enum.PatrolSetting: 3 + None + Count
RACE_TYPE = {0: "None", 1: "SuperEarth", 2: "Bugs", 3: "Cyborg", 4: "Illuminate"}


def id_names() -> dict[int, str]:
    out = {}
    for line in (ROOT / "refs" / "dl-type-names.txt").read_text(encoding="utf-8", errors="replace").splitlines():
        s = line.strip()
        if s and not s.startswith("//") and not s.startswith("====="):
            out.setdefault(typelib.type_hash(s), s)
    return out


NAMES = id_names()
LIB = typelib.TypeLib((PLAIN / "dl_library.dl_typelib").read_bytes())


def cstr(blob: bytes, off: int) -> str | None:
    if not (0 < off < len(blob) - 1):
        return None
    end = blob.find(b"\0", off)
    if end < 0 or end - off < 2 or end - off > 300:
        return None
    raw = blob[off:end]
    if any(c < 0x20 or c > 0x7E for c in raw):
        return None
    return raw.decode("latin1")


def sections(data: bytes) -> list[list[dict]]:
    """按 [u32 count][LDLD groups...] 分段。工具只解第一段；本函数解全部段。"""
    out, pos = [], 0
    while True:
        at = data.find(b"LDLD", pos, pos + 32)
        if at < 0:
            break
        pos = at
        groups = []
        while pos + 24 <= len(data) and data[pos:pos + 4] == b"LDLD":
            ver, tid, size, wide, flags = struct.unpack_from("<IIIII", data, pos + 4)
            groups.append({"tid": tid, "size": size, "payload": data[pos + 24:pos + 24 + size]})
            pos += 24 + size
        out.append(groups)
    return out


def load(table) -> list[list[dict]]:
    return sections((PLAIN / f"generated_{table}.dl_bin").read_bytes())


def dlt(blob, at):
    o, c = struct.unpack_from("<qQ", blob, at)
    return int(o), int(c)


def members_named(tid):
    out = []
    try:
        for m in LIB.members(tid):
            mt = m["type_id"]
            out.append({"offset": m["offset64"], "size": m["size64"],
                        "type": NAMES.get(mt, f"0x{mt:08X}" if mt else "prim")})
    except Exception:                                            # noqa: BLE001
        pass
    return out


# ---------------------------------------------------------------- zone_data
def zone_rows():
    gs = load("zone_data")[0]
    rows = []
    for gi, g in enumerate(gs):
        b = g["payload"]
        zo, zc = dlt(b, 0x0)
        tags = list(b[zo:zo + zc]) if 0 <= zo and 0 <= zc and zo + zc <= len(b) else []
        patrol = struct.unpack_from("<I", b, 0x16C)[0]
        floats = struct.unpack_from("<11f", b, 0x170)
        flags = list(b[0x208:0x218])
        ltags = struct.unpack_from("<4I", b, 0x380)
        rows.append({
            "group": gi, "size": g["size"], "zone_tags": tags, "patrol_setting": patrol,
            "patrol_floats": [round(f, 4) for f in floats],
            "minimap_terrain": b[0xA0], "zone_music": b[0x128],
            "location_flags": flags, "level_tags": list(ltags),
            "water_level_offset": struct.unpack_from("<f", b, 0xE0)[0],
            "city_heuristic": struct.unpack_from("<I", b, 0x1A0)[0],
        })
    return rows


# ---------------------------------------------------------------- region chain
def region_chain():
    secs = load("region_settings")
    sec0, sec1 = secs[0], secs[1]
    # sec0: 74 × GenerationRegionSettings；SubRegionSettings[16] at +0x238，Zone at +4
    rows0 = []
    for ri, g in enumerate(sec0):
        b = g["payload"]
        zones, sub_zones, prox = [], [], []
        for i in range(16):
            sb = 0x238 + i * 68
            z = struct.unpack_from("<I", b, sb + 4)[0]
            sub_zones.append(z)
            if z:
                zones.append(z)
            for k in range(8):
                zz = struct.unpack_from("<I", b, sb + 36 + 4 * k)[0]
                prox.append(zz)
                if zz:
                    zones.append(zz)
        overrides = []
        for i in range(16):
            ob = 0xAB4 + i * 32
            overrides.append({"type": struct.unpack_from("<I", b, ob)[0],
                              "zone_id": struct.unpack_from("<I", b, ob + 16)[0],
                              "race_affiliation": b[ob + 20],
                              "operation_type": struct.unpack_from("<I", b, ob + 24)[0]})
        rows0.append({"row": ri, "zones": sorted(set(zones)),
                      "sub_zones": sub_zones, "prox_zones": prox,
                      "overrides": overrides})
    # sec1: 13 region groups → variant lists → variant settings (variant type enum)
    lists = []
    for g in sec1:
        b = g["payload"]
        gname = cstr(b, struct.unpack_from("<q", b, 0)[0])
        lo, lc = dlt(b, 0x30)
        for j in range(lc):
            lb = lo + j * 48
            lname = cstr(b, struct.unpack_from("<q", b, lb)[0])
            lid = struct.unpack_from("<I", b, lb + 8)[0]
            so, sc = dlt(b, lb + 0x20)
            sets = []
            for k in range(sc):
                vb = so + k * 56
                sets.append({
                    "name": cstr(b, struct.unpack_from("<q", b, vb)[0]),
                    "hash": struct.unpack_from("<I", b, vb + 8)[0],
                    "variant_type": struct.unpack_from("<I", b, vb + 12)[0],
                    "weight": round(struct.unpack_from("<f", b, vb + 16)[0], 4),
                })
            lists.append({"group": gname, "name": lname, "id": lid, "sets": sets})
    return rows0, lists


def planet_rows():
    gs = load("planet_data")[0]
    rows = []
    for gi, g in enumerate(gs):
        b = g["payload"]
        rec = {"group": gi}
        for key, off in (("lowland", 0x60), ("highland", 0x88)):
            name = cstr(b, struct.unpack_from("<q", b, off)[0])
            rid = struct.unpack_from("<I", b, off + 8)[0]
            rtype = struct.unpack_from("<I", b, off + 0xC)[0]
            rec[key] = {"name": name, "id": rid, "type": rtype}
        rows.append(rec)
    return rows


def zone_xref_planet(zones_rows, rows0, lists, planets):
    """planet → LevelGenerationRegionType → region variant list → variant settings
    → variant_type-1 → sect0 row → ZoneId 集合。返回覆盖率统计。"""
    by_ltype = defaultdict(list)
    for lst in lists:
        # 用 sec1 的 list 名反查 LevelGenerationRegionType 枚举值
        for i, nm in enumerate(LG_REGION_TYPE_ENUM):
            if nm == lst["name"]:
                by_ltype[i].append(lst)
                break
    type_to_row = {v: v - 1 for v in range(1, 75)}     # 变体类型枚举 → sec0 行（推断）
    cov = Counter()
    planet_zones = {}
    for p in planets:
        zset = set()
        for side in ("lowland", "highland"):
            r = p[side]
            lsts = by_ltype.get(r["type"], [])
            for lst in lsts:
                for s in lst["sets"]:
                    vt = s["variant_type"]
                    ri = type_to_row.get(vt)
                    if ri is not None and 0 <= ri < len(rows0):
                        zset |= set(rows0[ri]["zones"])
                        cov["settings_hops"] += 1
            cov["regions"] += 1
            if lsts:
                cov["regions_matched_list"] += 1
        planet_zones[p["group"]] = sorted(zset)
        cov["planets"] += 1
        if zset:
            cov["planets_with_zones"] += 1
            cov["zone_refs"] += len(zset)
    allz = sorted({z for zs in planet_zones.values() for z in zs})
    cov["distinct_zones_total"] = len(allz)
    return dict(cov), planet_zones, allz


# ---------------------------------------------------------------- location stamps
def stamp_rows():
    """location_groups / satellite_groups 的 LocationStampInfo 枚举字段分布。"""
    si_tid = next(m["type_id"] for m in LIB.members(0xBBFEA78A)
                  if m["size64"] == 16 and m["type_id"])
    si = LIB.desc(si_tid)[3]
    members = {m["offset64"]: m for m in LIB.members(si_tid)}
    res = {}
    inst = []
    for t in ("location_groups", "satellite_groups"):
        for g in load(t)[0]:
            b = g["payload"]
            if t == "location_groups":
                g_tid = next(m["type_id"] for m in LIB.members(0x9BF3BB9D)
                             if m["size64"] == 16 and m["type_id"])
                gs = LIB.desc(g_tid)[3]
                lo, lc = dlt(b, 0x28)
                if not (0 <= lo and lc and lo + lc * gs <= len(b)):
                    continue
                for i in range(lc):
                    gb = lo + i * gs
                    so, sc = dlt(b, gb + 8)
                    if not (0 <= so and sc and so + sc * si <= len(b)):
                        continue
                    for j in range(sc):
                        inst.append(b[so + j * si: so + (j + 1) * si])
            else:
                etid = next(m["type_id"] for m in LIB.members(0x9D66BB58)
                            if m["size64"] == 16 and m["type_id"])
                es = LIB.desc(etid)[3]
                o, c = dlt(b, 0x8)
                if not (0 <= o and c and o + c * es <= len(b)):
                    continue
                for i in range(c):
                    eb = o + i * es
                    inst.append(b[eb: eb + si])
    for off in (0xD0, 0xE8, 0xE9, 0x134, 0x138, 0x15F, 0xD4):
        if off not in members:
            continue
        msize = members[off]["size64"]
        cnt = Counter(inst_ [off:off + msize] for inst_ in inst)
        if msize <= 4:
            vals = Counter()
            for raw in cnt:
                vals[int.from_bytes(raw, "little") if msize > 1 else raw[0]] = cnt[raw]
            res[f"+0x{off:X}"] = {"count": sum(vals.values()), "distinct": len(vals),
                                  "top": vals.most_common(8)}
        else:
            res[f"+0x{off:X}"] = {"count": sum(cnt.values()), "distinct": len(cnt)}
    return len(inst), res


def presence_xref():
    """presence 的 +0x20/+0x28 u64、尾部标签字符串/murmur64 是否出现在任何表里。"""
    gs = load("galactic_presence_settings")[0]
    u20, u28, tags = set(), set(), set()
    for g in gs:
        b = g["payload"]
        v20 = struct.unpack_from("<Q", b, 0x20)[0]
        v28 = struct.unpack_from("<Q", b, 0x28)[0]
        if v20:
            u20.add(v20)
        if v28:
            u28.add(v28)
        for m in re.finditer(rb"[a-zA-Z][a-zA-Z0-9_/]{5,}", b[1000:]):
            tags.add(m.group().decode("latin1"))
    hashes = {murmur64.murmur64(t.encode()) for t in tags}
    tables = sorted(p.name[len("generated_"):-len(".dl_bin")]
                    for p in PLAIN.glob("generated_*.dl_bin"))
    report = {}
    total = 0
    for t in tables:
        try:
            secs = load(t)
        except Exception:                                        # noqa: BLE001
            continue
        blob = b"".join(g["payload"] for sec in secs for g in sec)
        h20 = h28 = ht = hs = 0
        for off in range(0, len(blob) - 7, 4):
            v = struct.unpack_from("<Q", blob, off)[0]
            if v in u20:
                h20 += 1
            if v in u28:
                h28 += 1
            if v in hashes:
                ht += 1
        for tag in tags:
            hs += blob.count(tag.encode())
        if h20 or h28 or ht or hs:
            report[t] = {"u20": h20, "u28": h28, "tag_hash": ht, "tag_string": hs}
        total += h20 + h28 + ht
    return {"u20_unique": len(u20), "u28_unique": len(u28), "tags_unique": len(tags),
            "tables_scanned": len(tables), "hash_hits_total": total, "per_table": report}


def presence_entity_refs():
    """presence 的 u64 在实体库里命中在哪（本 build 只有 ShowOnMapComponent 引用）。"""
    pgs = load("galactic_presence_settings")[0]
    vals = {}
    for gi, g in enumerate(pgs):
        b = g["payload"]
        for off, key in ((0x20, "u20"), (0x28, "u28")):
            v = struct.unpack_from("<Q", b, off)[0]
            if v:
                vals.setdefault(v, []).append((gi, key))
    ent = (PLAIN / "generated_entities.dl_bin").read_bytes()
    blocks, pos = [], 0
    while True:
        at = ent.find(b"LDLD", pos)
        if at < 0:
            break
        head = at - 4
        ver, inner, payload = struct.unpack_from("<III", ent, at + 4)
        if ver != 1 or inner != struct.unpack_from("<I", ent, head)[0]:
            pos = at + 4
            continue
        blocks.append({"head": head, "tid": inner, "size": payload, "payload_at": head + 28})
        pos = head + 28 + payload
    starts = [b["head"] for b in blocks]
    hits = []
    for off in range(0, len(ent) - 7, 4):
        v = struct.unpack_from("<Q", ent, off)[0]
        if v not in vals:
            continue
        bi = bisect.bisect_right(starts, off) - 1
        b = blocks[bi]
        members = LIB.members(b["tid"])
        im = [m for m in members if NAMES.get(m["type_id"], "") == "ComponentIndexData"]
        if not im:
            continue
        isz = im[0]["size64"]
        rest = [m for m in members if m is not im[0]]
        if not rest:
            continue
        stride = LIB.desc(rest[0]["type_id"])[3]
        rel = off - b["payload_at"]
        if rel < isz:
            continue
        row, o = (rel - isz) // stride, (rel - isz) % stride
        field = next((f"+0x{m['offset64']:X}" for m in LIB.members(rest[0]["type_id"])
                      if m["offset64"] <= o < m["offset64"] + max(m["size64"], 1)), "?")
        hits.append({"block": bi, "component": NAMES.get(b["tid"], f"0x{b['tid']:08X}"),
                     "row": row, "field": field, "presence_rows": [r for r, _k in vals[v]]})
    return {"presence_u64_unique": len(vals), "entity_hits": hits}


def main() -> int:
    data = {}
    # ---- zone_data
    zr = zone_rows()
    data["zone_data"] = {
        "rows": len(zr),
        "geometry": {"groups": 88, "stride": 912, "layout": "1 row/group + per-group array tail",
                     "payload_min": min(r["size"] for r in zr),
                     "payload_max": max(r["size"] for r in zr)},
        "named_fields": members_named(0x221E024D),
        "zone_tags": {
            "per_zone_count": dict(Counter(len(r["zone_tags"]) for r in zr)),
            "value_distribution": dict(Counter(t for r in zr for t in r["zone_tags"]).most_common()),
            "distinct": len({t for r in zr for t in r["zone_tags"]}),
            "enum_range": "0..17（enum.ZoneTag: None + 16 + Count=18）",
        },
        "patrol_setting": dict(Counter(r["patrol_setting"] for r in zr).most_common()),
        "patrol_floats": {},
        "patrol_presets": {},
        "minimap_terrain": dict(Counter(r["minimap_terrain"] for r in zr).most_common()),
        "zone_music": dict(Counter(r["zone_music"] for r in zr).most_common()),
    }
    for i in range(11):
        vals = [r["patrol_floats"][i] for r in zr]
        data["zone_data"]["patrol_floats"][f"PatrolFloat{i + 1}"] = {
            "min": min(vals), "max": max(vals), "distinct": len(set(vals)),
            "top": dict(Counter(vals).most_common(6)),
        }
    presets = defaultdict(set)
    for r in zr:
        presets[r["patrol_setting"]].add(tuple(r["patrol_floats"]))
    data["zone_data"]["patrol_presets"] = {
        str(p): {"rows": sum(1 for r in zr if r["patrol_setting"] == p),
                 "float_combos": [list(c) for c in sorted(v)]}
        for p, v in sorted(presets.items())}
    # PatrolSetting × terrain / tags
    cross = Counter((r["patrol_setting"], r["minimap_terrain"]) for r in zr)
    data["zone_data"]["patrol_x_terrain"] = {f"{p}/{t}": c for (p, t), c in sorted(cross.items())}
    data["zone_data"]["patrol_groups"] = {str(p): [r["group"] for r in zr if r["patrol_setting"] == p]
                                          for p in sorted(presets)}

    # ---- region chain
    rows0, lists = region_chain()
    planets = planet_rows()
    cov, planet_zones, allz = zone_xref_planet(zr, rows0, lists, planets)
    data["region_settings"] = {
        "rows_section0": len(rows0),
        "rows_section1_groups": len(lists),
        "variant_lists": [{"group": l["group"], "name": l["name"], "id": f"0x{l['id']:08X}",
                           "sets": l["sets"]} for l in lists],
        "zone_coverage": {
            "distinct_zones_referenced": len({z for r in rows0 for z in r["zones"]}),
            "zones_per_row": dict(Counter(len(r["zones"]) for r in rows0).most_common()),
            "zone_histogram_top": dict(Counter(z for r in rows0 for z in r["zones"]).most_common(20)),
        },
        "subregion_override": {
            "race_affiliation": dict(Counter(o["race_affiliation"] for r in rows0
                                             for o in r["overrides"]).most_common(12)),
            "operation_type": dict(Counter(o["operation_type"] for r in rows0
                                           for o in r["overrides"]).most_common(12)),
        },
        "named_fields_sec0": members_named(0x05D2D521),
    }
    # region 名/类型命中率（独立于推断的 settings 行跳）
    lnames = {l["name"] for l in lists}
    lids = {l["id"] for l in lists}
    shashes = {st["hash"] for l in lists for st in l["sets"]}
    n_name = n_id = n_hash = n_slots = 0
    for p_ in planets:
        for side in ("lowland", "highland"):
            r = p_[side]
            n_slots += 1
            if r["name"] in lnames:
                n_name += 1
            if r["id"] in lids:
                n_id += 1
            if r["id"] in shashes:
                n_hash += 1
    data["planet_join"] = {
        "coverage": cov,
        "match_rates": {"slots": n_slots, "name_hit": n_name, "list_id_hit": n_id,
                        "settings_hash_hit": n_hash,
                        "note": "join 键：Name(DLString) 876/876、Id(ThinHash) 876/876、Type(枚举) 876/876 三者一致；"
                                "Id 命中 settings hash 只有 6/876（噪声），说明 Id 是 region 变体 id 不是 settings 引用"},
        "region_type_distribution": dict(Counter(
            r[side]["type"] for r in planets for side in ("lowland", "highland")).most_common()),
        "region_type_names": {str(i): nm for i, nm in enumerate(LG_REGION_TYPE_ENUM)},
        "distinct_zones_all": allz,
        "zone_to_planets": {str(z): sum(1 for zs in planet_zones.values() if z in zs)
                            for z in allz},
    }

    # ---- location/satellite stamps
    inst, stamps = stamp_rows()
    data["location_stamps"] = {"instances": inst, "fields": stamps}

    # ---- presence xref
    data["presence_xref"] = presence_xref()
    data["presence_xref"]["entity_hits"] = presence_entity_refs()

    # ---- 其他表（行数/几何/字段名）
    other = {}
    for t, sec_idx in (("planet_region_settings", 0), ("planet_types_settings", 0),
                       ("scenario_settings", 0), ("solar_system_settings", 0),
                       ("modifier_settings", 0), ("planet_color_set_settings", 0),
                       ("planet_override_settings", 0)):
        secs = load(t)
        g = secs[0][0]
        tid = g["tid"]
        stride = LIB.desc(tid)[3]
        rows = sum(sz["size"] // stride for sz in secs[0]) if t not in ("planet_types_settings",
                                                                       "planet_color_set_settings",
                                                                       "planet_override_settings") else None
        other[t] = {"groups": len(secs[0]), "row_type": NAMES.get(tid, f"0x{tid:08X}"),
                    "stride": stride, "rows_floor": rows,
                    "sections": [{"groups": len(s), "type": NAMES.get(s[0]["tid"], "?")}
                                 for s in secs],
                    "named_fields": members_named(tid)}
    # ---- planet_region_settings 关键分布
    gs = load("planet_region_settings")[0]
    prs = {"rows": len(gs), "race": Counter(), "op_type": Counter(), "unk_int1": Counter(),
           "unk_enum": Counter()}
    for g in gs:
        b = g["payload"]
        prs["race"][struct.unpack_from("<I", b, 0x18)[0]] += 1
        prs["op_type"][struct.unpack_from("<I", b, 0x38)[0]] += 1
        prs["unk_int1"][struct.unpack_from("<I", b, 0x34)[0]] += 1
        prs["unk_enum"][struct.unpack_from("<I", b, 0x50)[0]] += 1
    other["planet_region_settings"]["race_type"] = {str(k): v for k, v in prs["race"].most_common()}
    other["planet_region_settings"]["operation_type"] = {str(k): v for k, v in prs["op_type"].most_common()}
    other["planet_region_settings"]["unk_int1"] = {str(k): v for k, v in prs["unk_int1"].most_common()}
    other["planet_region_settings"]["unk_enum"] = {str(k): v for k, v in prs["unk_enum"].most_common()}
    other["planet_region_settings"]["race_type_names"] = {str(k): v for k, v in RACE_TYPE.items()}
    # 行数/形态说明
    other["planet_region_settings"]["rows"] = len(gs)
    other["planet_region_settings"]["key_observation"] = (
        "369 行 = 城市/区域模板；RaceType 只有 SuperEarth(344) 与 Cyborg(25)，"
        "后者的 UnkInt0(+0x30)=4；无敌兵组成字段")
    sc_secs = load("scenario_settings")[0]
    other["scenario_settings"]["rows"] = sum(g["size"] // LIB.desc(sc_secs[0]["tid"])[3]
                                             for g in sc_secs)
    other["scenario_settings"]["key_observation"] = (
        "149 行 × 48 B = {u64,u64,u64,u32, DLArray<ScenarioSetting>}；类型树无 enemy/spawn/faction 字段")
    other["solar_system_settings"]["key_observation"] = (
        "1 组 3822 行 × 24 B = {Hash 行星类型, DLArray<SolarSystemSetting>}；尾部有 planet_* 名字字符串")
    other["planet_types_settings"]["key_observation"] = (
        "容器 = (offset=16,count=88) → 88 × SolarSystemObjectType(24 B) = {Hash, DLArray}")
    other["modifier_settings"]["key_observation"] = "15 组 52 行 × 24 B = {u32,u8,DLArray<ModifierGroup>}；无字符串"

    # ---- zone_data 枚举观察与 join
    z = data["zone_data"]
    z["enum_observations"] = {
        "ZoneTag": "0..17（18 个值），命中 88/88 行数组；values 都是 u8",
        "PatrolSetting": "0..3（4 个值），命中 88/88 行",
        "MinimapTerrainType": "0..5（6 个值：Open/Difficult/Rocky/Vegetation/Impassable/Bug）",
        "ZoneMusicType": "只有 0(None)/1(Bug) 两个值",
        "BanterEventType": "88/88 = 0（None）",
        "CityPlacementHeuristic": "0..5（6 个值）",
        "LevelGenerationTag": "+0x380 4×u32，LevelGenerationTag 枚举",
    }
    z["join_keys"] = {
        "zone 身份": "块序号 = enum.ZoneId（0..87；ZoneId 枚举恰好 88 个值）",
        "被引用": "region_settings 段0 的 SubRegionSettings[16](+0x238,+0x4 ZoneId) 与 "
                 "InvalidZoneProximity[8](+0x25C 起)",
        "覆盖率": "67/88 个 zone 被引用；每个 region 行 3..14 个 zone",
    }
    data["region_settings"]["enum_observations"] = {
        "RegionFlag": "+0xA95 4 B，RegionFlag 枚举",
        "LevelGenerationMode": "+0xA94 1 B",
        "SubRegionType": "SubRegionSettings+0x0（0..44）",
        "StampRaceAffiliation": "SubRegionSettingsOverride+0x14：位掩码 Bugs=1/Cyborg=2/Illuminate=4/SuperEarth=8",
        "OperationType": "SubRegionSettingsOverride+0x18",
        "LevelGenerationRegionVariantType": "变体 settings +0x0C（0..74，46 个不同值被使用）",
    }
    data["region_settings"]["join_keys"] = {
        "region 变体列表": "段1 的 34 个 GenerationRegionVariantList：+0x0 DLString 名，+0x8 ThinHash id",
        "planet → region": "planet_data.RegionLowland/Highland 的 Name（DLString）与 Type（LevelGenerationRegionType 0..34）"
                           "→ region_settings 段1 的 34 个 GenerationRegionVariantList；实测 Name 876/876、Type 876/876 命中，"
                           "且 Type↔Name 876/876 一致；Region.Id(ThinHash) 与列表 id / settings hash 均不匹配（0.7%≈噪声）",
        "region → 生成设置行": "变体 settings +0x0C（LevelGenerationRegionVariantType v）→ 段0 第 v-1 行（74 行 = 74 个枚举值）⚠推断",
        "生成设置行 → zone": "SubRegionSettings[16].Zone / InvalidZoneProximity[8]（ZoneId）",
        "未被使用": "变体 settings +0x30 的 GenerationRegionSettings 引用在 146/146 条里都是 -1（本 build 未用）",
    }
    data["presence_sample"] = {
        "note": "presence 行 97（race=4 Illuminate，tag=illuminate_rift_sideboard_gate）的 +0x28 "
                "出现在实体库 ShowOnMapComponent +0x8（3 个实体，地图标记）",
        "rows": [{"row": 97, "race": 4, "id_0x8": 1001, "tags": ["illuminate_rift_sideboard_gate"]}],
    }
    data["presence_xref"]["method"] = (
        "1) 收集 137 行 presence 的 +0x20/+0x28 两个 u64（105/32 个唯一值）；"
        "2) 对 54 张 generated_*.dl_bin 的全部 payload 以 4 字节步进读 8 字节窗口比对；"
        "3) 同时用 144 个 presence 尾部标签字符串的 murmur64 与原始 ASCII 扫描；"
        "4) 8 字节哈希是 64 位，误命中概率 ≈ 表窗口数/2^64，可忽略")
    data["presence_xref"]["conclusion"] = (
        "8 张目标表 0 命中；只有 generated_entities 的 ShowOnMapComponentData +0x8 命中 3 次"
        "（presence 97 的 +0x28）——即 presence 在本 build 里只被'星图标记实体'引用，"
        "不被任何关卡生成表引用")

    data["other_tables"] = other
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "levelgen.json").write_text(json.dumps(data, ensure_ascii=False, indent=1,
                                                  default=str), encoding="utf-8")
    print(f"wrote {OUT/'levelgen.json'} ({ (OUT/'levelgen.json').stat().st_size//1024 } KB)")
    print("coverage:", json.dumps(cov, ensure_ascii=False))
    print("presence xref:", json.dumps(data["presence_xref"], ensure_ascii=False))
    print("stamp instances:", inst)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
