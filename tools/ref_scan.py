#!/usr/bin/env python3
"""ref_scan.py -- 反查「谁引用了某张表的行 id」，命中归因到（文件 / 块 / 行 / 行内偏移 / 实体键）。

为什么要它
    想知道"某个弹丸 type id 在整个档案里有哪些引用点"，逐个组件猜字段偏移会漏；而只查
    `ProjectileWeaponComponentData+0x000` 又会把"另有一套引用写法"误判成"没有引用"。本工具
    换成数据驱动，两种判据都跑：

      columns  扫"值域整列落在目标表 id 集合里"的槽位。真正的引用列必然整列都是目标 id
               （外加 0 = 无），所以这条判据能把引用面**找全**，不需要预先知道偏移。
      exact    扫"精确等于某个 id 的 4 字节窗口"（任意字节对齐）。一个随机 u32 恰好等于
               355 分之一的概率是 1/4.3e9，本档 4 字节窗口约 1,180 万个 ⇒ 期望误报 0.003 次，
               所以命中即证据。命中再按块 / 行 / 槽归因。

读的是明文缓存（`refs/dlbin/plaintext-<build>/`），只读，不碰游戏目录。

用法
    python tools/ref_scan.py columns --names D:/mod/dl-type-names.json --for-projectile
    python tools/ref_scan.py exact 296 --names D:/mod/dl-type-names.json
    python tools/ref_scan.py entity 0x3575AABC5F1F9326 --names D:/mod/dl-type-names.json
"""
from __future__ import annotations

import argparse
import collections
import csv
import json
import pathlib
import struct
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from table_dictionary import Dictionary, load_names                 # noqa: E402
import entity_locid_scan as scan                                     # noqa: E402

PLAIN = pathlib.Path(r"D:\mod\refs\dlbin\plaintext-26251122")
NAMES = pathlib.Path(r"D:\mod\dl-type-names.json")


# ---------------------------------------------------------------- 几何
def table_geometry(plain: bytes, block: dict) -> dict | None:
    """非实体表：payload = [16 B 描述符: u64 0x10, u64 行数][行数组][尾垫]。"""
    p0 = block["payload_at"]
    if p0 + 16 > len(plain):
        return None
    marker, count = struct.unpack_from("<QQ", plain, p0)
    if marker != 16 or count <= 0 or count > 5_000_000:
        return None
    rest = block["payload"] - 16
    if rest % count:
        return None
    stride = rest // count
    if stride < 4:
        return None
    return {"rows": count, "stride": stride, "base": p0 + 16, "layout": "descriptor"}


def entity_geometries(plain: bytes, dic: Dictionary) -> list[tuple[int, dict, dict]]:
    out = []
    for i, block in enumerate(scan.parse_blocks(plain)):
        g = scan.geometry(dic, block)
        if g is None:
            continue
        g = scan.check_geometry(plain, block, g)
        if g["ok"] and g["stride"] >= 4 and g["rows"] > 0:
            out.append((i, block, g))
    return out


def row_keys(plain: bytes, block: dict, geo: dict) -> dict[int, list[int]]:
    """行号 -> 实体键列表（用 scan.hashmap，含 index_offset）。"""
    out: dict[int, list[int]] = {}
    for key, row in scan.hashmap(plain, block, geo).items():
        out.setdefault(row, []).append(key)
    return out


def entity_names(path: pathlib.Path) -> dict[int, str]:
    """`refs/entity-locid-names.json` 里的 实体键 -> 游戏内名字（只取 ok 条目）。"""
    out: dict[int, str] = {}
    if not path.is_file():
        return out
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return out
    tables = data.get("name_tables") or []
    if isinstance(tables, dict):
        tables = list(tables.values())
    for table in tables:
        entries = table.get("entries") if isinstance(table, dict) else None
        if entries is None and isinstance(table, list):
            entries = table
        for item in entries or []:
            if not isinstance(item, dict):
                continue
            key, name = item.get("key"), item.get("name") or item.get("name_upper")
            if not key or not name or item.get("quality") == "placeholder":
                continue
            try:
                out[int(key, 16)] = name
            except (TypeError, ValueError):
                continue
    return out


# ---------------------------------------------------------------- 扫描
def column_scan(rows: list[bytes], stride: int, ids: set[int], max_id: int,
                min_hits: int) -> list[dict]:
    """找出值域落在 ids 里的 4 字节槽（0 视为"无"）。"""
    found = []
    for slot in range(0, stride - 3, 4):
        hits, distinct, seen, outside = 0, set(), 0, 0
        for row in rows:
            v = struct.unpack_from("<I", row, slot)[0]
            if v == 0:
                continue
            seen += 1
            if v in ids:
                hits += 1
                distinct.add(v)
            elif v > max_id:
                outside += 1
        if hits >= min_hits and len(distinct) >= 3 and outside == 0:
            found.append({"slot": slot, "hits": hits, "distinct": len(distinct),
                          "nonzero": seen})
    return found


def exact_hits(plain: bytes, needle: int) -> list[dict]:
    """扫 u32 == needle 的全部字节窗口（任意对齐）。"""
    pat = struct.pack("<I", needle)
    hits, at = [], plain.find(pat)
    while at >= 0:
        hits.append({"at": at, "rel": 0})
        at = plain.find(pat, at + 1)
    return hits


def locate(plain: bytes, blocks: list[dict], geos: dict[int, dict],
           pos: int) -> dict | None:
    """把绝对偏移归因到 (块, 行, 行内偏移)。"""
    for i, block in enumerate(blocks):
        p0 = block["payload_at"]
        if not (p0 <= pos < p0 + block["payload"]):
            continue
        g = geos.get(i)
        if not g:
            return {"block": block, "row": None, "slot": None, "geo": None}
        row_start = p0 + g["index_size"]
        if not (row_start <= pos < row_start + g["rows"] * g["stride"]):
            return {"block": block, "row": None, "slot": None, "geo": g}
        delta = pos - row_start
        return {"block": block, "row": delta // g["stride"],
                "slot": delta % g["stride"], "geo": g}
    return None


def key_of_row(plain: bytes, block: dict, geo: dict, row: int) -> list[int]:
    out = []
    for s in range(geo["index_size"] // 16):
        key, value, _pad = struct.unpack_from(
            "<QII", plain, block["payload_at"] + 16 * s)
        if key and value == row:
            out.append(key)
    return out


def fmt_key(key: int, names: dict[int, str]) -> str:
    name = names.get(key)
    return f"0x{key:016X}" + (f" ({name})" if name else "")


# ---------------------------------------------------------------- 子命令
def cmd_exact(a) -> int:
    names = entity_names(pathlib.Path(a.entity_names)) if a.entity_names else {}
    for path in sorted(pathlib.Path(a.plaintext).glob("generated_*.dl_bin")):
        print(f"\n### {path.name}")
        plain = path.read_bytes()
        blocks = scan.parse_blocks(plain)
        is_entities = path.name == "generated_entities.dl_bin"
        dic = _dic(a)
        if is_entities:
            geos = {i: g for i, _b, g in entity_geometries(plain, dic)}
        else:
            geos = {}
            for i, block in enumerate(blocks):
                g = table_geometry(plain, block)
                if g:
                    geos[i] = g
        hits = exact_hits(plain, a.value)
        print(f"  u32 == {a.value} 命中 {len(hits)} 处")
        shown = 0
        for h in hits:
            loc = locate(plain, blocks, geos, h["at"])
            if loc is None:
                print(f"  @0x{h['at']:X} 不在任何块内")
                continue
            block, geo = loc["block"], loc["geo"]
            tname = dic.name(block["type_id"])
            if loc["row"] is None:
                if a.row_only:
                    continue
                print(f"  @0x{h['at']:X} 块 {tname} 非行数组区（+{h['at'] - block['payload_at']}）")
                continue
            keys = sorted(row_keys(plain, block, geo).get(loc["row"], [])) if is_entities else []
            ktxt = " keys=" + ",".join(fmt_key(k, names) for k in keys[:4]) if keys else ""
            row_base = block["payload_at"] + geo["index_size"] + loc["row"] * geo["stride"]
            aligned = loc["slot"] - loc["slot"] % 4
            neighbour = struct.unpack_from("<I", plain, row_base + aligned)[0] \
                if row_base + aligned + 4 <= len(plain) else -1
            ctx = plain[h["at"] - 4: h["at"] + 8].hex()
            print(f"  {tname} row {loc['row']} +{loc['slot']}"
                  f"{'' if loc['slot'] == aligned else f' (对齐槽 +{aligned} 值 {neighbour})'}"
                  f" (stride {geo['stride']}){ktxt}  ctx {ctx}")
            shown += 1
            if shown >= a.max_show:
                print(f"  … 只显示前 {a.max_show} 处")
                break
    return 0


_DIC_CACHE: dict[str, Dictionary] = {}


def _dic(a) -> Dictionary:
    key = str(pathlib.Path(a.names).resolve())
    if key not in _DIC_CACHE:
        plain = pathlib.Path(a.plaintext) / "dl_library.dl_typelib"
        _DIC_CACHE[key] = Dictionary(plain.read_bytes(), load_names(pathlib.Path(a.names)))
    return _DIC_CACHE[key]


def cmd_columns(a) -> int:
    plain = pathlib.Path(a.plaintext)
    dic = _dic(a)
    names = None
    ids = set(range(1, a.max_id + 1)) if a.for_projectile else {int(x, 0) for x in a.ids.split(",")}
    print(f"目标 id 集合：{len(ids)} 个（0 视为无引用）")

    ent = plain / "generated_entities.dl_bin"
    if ent.is_file():
        data = ent.read_bytes()
        geos = entity_geometries(data, dic)
        print(f"\n== generated_entities.dl_bin：{len(geos)} 个可拆组件块 ==")
        total = 0
        for _i, block, g in geos:
            rows = [data[block["payload_at"] + g["index_size"] + r * g["stride"]:
                         block["payload_at"] + g["index_size"] + (r + 1) * g["stride"]]
                    for r in range(g["rows"])]
            hits = column_scan(rows, g["stride"], ids, a.max_id, a.min_hits)
            if not hits:
                continue
            total += 1
            block_name = dic.name(block["type_id"])
            detail = "  ".join(f"+{h['slot']}({h['hits']}/{g['rows']},dist{h['distinct']})"
                               for h in hits[:8])
            print(f"  {block_name:<40} rows {g['rows']:>4} stride {g['stride']:>6}  {detail}")
        print(f"  ⇒ 含候选引用列的组件块：{total} 个")

    for path in sorted(plain.glob("generated_*.dl_bin")):
        if path.name == "generated_entities.dl_bin":
            continue
        data = path.read_bytes()
        blocks = scan.parse_blocks(data)
        printed = False
        for i, block in enumerate(blocks):
            g = table_geometry(data, block)
            if not g:
                continue
            rows = [data[g["base"] + r * g["stride"]: g["base"] + (r + 1) * g["stride"]]
                    for r in range(g["rows"])]
            hits = column_scan(rows, g["stride"], ids, a.max_id, a.min_hits)
            if not hits:
                continue
            if not printed:
                print(f"\n== {path.name} ==")
                printed = True
            print(f"  块{dic.name(block['type_id'])} rows {g['rows']} stride {g['stride']}: "
                  + "  ".join(f"+{h['slot']}({h['hits']}/{g['rows']},dist{h['distinct']})"
                              for h in hits[:10]))
    return 0


def cmd_entity(a) -> int:
    plain = pathlib.Path(a.plaintext)
    dic = _dic(a)
    names = entity_names(pathlib.Path(a.entity_names)) if a.entity_names else {}
    data = (plain / "generated_entities.dl_bin").read_bytes()
    target = a.key
    ids = set(range(1, a.max_id + 1))
    geos = {i: g for i, _b, g in entity_geometries(data, dic)}
    print(f"实体 {fmt_key(target, names)}")
    for i, block in enumerate(scan.parse_blocks(data)):
        g = geos.get(i)
        if not g:
            continue
        row = scan.hashmap(data, block, g).get(target)
        if row is None:
            continue
        base = block["payload_at"] + g["index_size"] + row * g["stride"]
        row_bytes = data[base: base + g["stride"]]
        tname = dic.name(block["type_id"])
        slots = []
        for off in range(0, g["stride"] - 3, 4):
            v = struct.unpack_from("<I", row_bytes, off)[0]
            if v:
                mark = "  <-- 目标 id" if v in ids else ""
                slots.append(f"+{off}:{v}{mark}")
        print(f"\n  [{tname}] row {row} stride {g['stride']}")
        if a.raw:
            print("   raw:", data[base:base + a.raw].hex())
        print("   " + "  ".join(slots))
    return 0


# ---------------------------------------------------------------- entity delta 存储
# `generated_entity_deltas.dl_bin` 只有一个块（type 0x683E604F = ComponentEntityDeltaStorage）：
#   payload = [80 B 头：5 组 (u64 offset, u64 count)][hashmap 16 B/条][settings 8 B][component 12 B]
#             [delta 12 B][data 字节流]
#   hashmap 条 = {u64 AddPath(=配件/弹种资源哈希), u32 settingsIndex, u32 pad}
#   settings  = {u32 componentCount, u32 firstComponent}
#   component = {u32 组件索引, u32 firstDelta, u32 deltaCount}
#   delta     = {u32 成员偏移, u32 宽度, u32 data 偏移}
# 这是「武器在建造时把配件 delta 打进组件记录」的那张表：弹种（slot 6）就是靠它写
# ProjectileWeapon+0，所以实体记录里的 +0 才是 0（dormant）。
# 组件索引是本 build 实测映射（换 build 必须重测，社区文档里 0.28.1 的索引就不同）。
DELTA_STORE_TYPE = 0x683E604F
DELTA_COMPONENTS = {
    5: "WeaponMagazineComponentData",
    114: "WeaponReloadComponentData",
    119: "WeaponRoundsComponentData",
    239: "WeaponDataComponentData",
    274: "WeaponCustomizationComponentData",
    324: "ProjectileWeaponComponentData",
}


def load_delta_store(path: pathlib.Path) -> dict | None:
    data = path.read_bytes()
    block = next((b for b in scan.parse_blocks(data) if b["type_id"] == DELTA_STORE_TYPE), None)
    if block is None:
        return None
    p0 = block["payload_at"]
    names = ("hashmap", "settings", "component", "delta", "data")
    store = {"data": data, "p0": p0, "off": {}, "count": {}, "size": len(data)}
    for i, name in enumerate(names):
        store["off"][name], store["count"][name] = struct.unpack_from("<QQ", data, p0 + 16 * i)
    hm = {}
    for s in range(store["count"]["hashmap"]):
        key, sidx, _pad = struct.unpack_from(
            "<QII", data, p0 + store["off"]["hashmap"] + 16 * s)
        if key:
            hm.setdefault(key, sidx)
    store["hashmap"] = hm
    return store


def delta_patches(store: dict, key: int) -> list[dict]:
    data, p0 = store["data"], store["p0"]
    off, cnt = store["off"], store["count"]
    sidx = store["hashmap"][key]
    n_comp, first_comp = struct.unpack_from("<II", data, p0 + off["settings"] + 8 * sidx)
    out = []
    for i in range(n_comp):
        comp, first_delta, n_delta = struct.unpack_from(
            "<III", data, p0 + off["component"] + 12 * (first_comp + i))
        for k in range(n_delta):
            member, size, raw = struct.unpack_from(
                "<III", data, p0 + off["delta"] + 12 * (first_delta + k))
            payload = data[p0 + off["data"] + raw: p0 + off["data"] + raw + size]
            out.append({"component": comp, "member": member, "size": size,
                        "data_off": raw, "abs_off": p0 + off["data"] + raw,
                        "bytes": payload,
                        "u32": struct.unpack("<I", payload[:4])[0] if size >= 4 else None})
    return out


def load_customization_csv(path: str) -> dict[int, dict]:
    """`weapon_customization_settings` 导出 CSV：AddPath(+32) -> {name, slot, option_id(+8)}。"""
    out: dict[int, dict] = {}
    if not path or not pathlib.Path(path).is_file():
        return out
    with open(path, encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if not header:
            return out
        col = {name: i for i, name in enumerate(header)}
        for row in reader:
            def num(name: str) -> int:
                i = col.get(name)
                if i is None or i >= len(row):
                    return 0
                token = row[i].split("/")[0].strip()
                return int(token, 16) if token.lower().startswith("0x") else 0
            add_path = num("+32")
            if add_path:
                out.setdefault(add_path, {"name": row[2] if len(row) > 2 else "",
                                          "slot": row[3] if len(row) > 3 else "",
                                          "option_id": num("+8")})
    return out


def cmd_delta_info(a) -> int:
    store = load_delta_store(pathlib.Path(a.plaintext) / "generated_entity_deltas.dl_bin")
    if store is None:
        print("✗ 没找到 ComponentEntityDeltaStorage 块")
        return 2
    print(f"文件 {store['size']:,} B；hashmap {len(store['hashmap'])} 条")
    for name in ("hashmap", "settings", "component", "delta", "data"):
        unit = {"hashmap": 16, "settings": 8, "component": 12, "delta": 12, "data": 1}[name]
        print(f"  {name:9s} off 0x{store['off'][name]:06X} count {store['count'][name]:>7}"
              f"  ({store['count'][name] * unit:,} B)")
    hist = collections.Counter()
    combos = collections.Counter()
    for key in store["hashmap"]:
        for patch in delta_patches(store, key):
            hist[patch["component"]] += 1
            combos[(patch["component"], patch["member"], patch["size"])] += 1
    print("\n组件索引 -> 被打补丁的次数（本 build 实测名）:")
    for comp, n in hist.most_common():
        print(f"  {comp:>4}  {DELTA_COMPONENTS.get(comp, '?'):<32} {n:>5} 次")
    print("\n最常见的 (组件, 成员偏移, 宽度) 组合:")
    for (comp, member, size), n in combos.most_common(20):
        print(f"  comp {comp:>4} +{member:<6} size {size:<3} x{n}")
    return 0


def cmd_delta_show(a) -> int:
    store = load_delta_store(pathlib.Path(a.plaintext) / "generated_entity_deltas.dl_bin")
    if store is None or a.addpath not in store["hashmap"]:
        print(f"✗ delta store 里没有 AddPath 0x{a.addpath:016X}")
        return 2
    print(f"AddPath 0x{a.addpath:016X} 的 delta 补丁：")
    for p in delta_patches(store, a.addpath):
        name = DELTA_COMPONENTS.get(p["component"], "?")
        print(f"  comp {p['component']:>4} {name:<32} +{p['member']:<7} size {p['size']:<3}"
              f" data 0x{p['data_off']:06X} (abs 0x{p['abs_off']:06X})"
              f"  hex {p['bytes'].hex()}"
              + (f"  u32 {p['u32']}" if p["size"] == 4 else ""))
    return 0


def cmd_delta_ammo(a) -> int:
    store = load_delta_store(pathlib.Path(a.plaintext) / "generated_entity_deltas.dl_bin")
    if store is None:
        print("✗ 没找到 delta store")
        return 2
    names = load_customization_csv(a.csv)
    rows = []
    for key in store["hashmap"]:
        info = names.get(key, {})
        slot = info.get("slot", "")
        if a.slot and slot != a.slot:
            continue
        for p in delta_patches(store, key):
            if a.component is not None and p["component"] != a.component:
                continue
            if a.member is not None and p["member"] != a.member:
                continue
            rows.append((slot, info.get("name", ""), key, p))
    rows.sort(key=lambda r: (r[0], r[1], r[3]["member"]))
    print(f"{'slot':<10} {'item':<46} {'component':<32} {'+off':>5} size  value")
    for slot, name, key, p in rows:
        comp = f"{p['component']} {DELTA_COMPONENTS.get(p['component'], '?')}"
        print(f"{slot:<10} {name:<46} {comp:<32} {p['member']:>5} {p['size']:>4}  {p['u32']}")
    print(f"\n共 {len(rows)} 条补丁；带名字的 AddPath {sum(1 for r in rows if r[1])} 条")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="反查表行 id 的引用点")
    ap.add_argument("--plaintext", default=str(PLAIN))
    ap.add_argument("--names", default=str(NAMES), help="type_id -> 类型名 json")
    ap.add_argument("--entity-names", default=r"D:\mod\refs\entity-locid-names.json")
    ap.add_argument("--max-id", type=int, default=355)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("exact", help="扫精确等于某值的 u32 窗口")
    p.add_argument("value", type=lambda s: int(s, 0))
    p.add_argument("--max-show", type=int, default=60)
    p.add_argument("--row-only", action="store_true", help="只看落在行数组里的命中")
    p.set_defaults(func=cmd_exact)

    p = sub.add_parser("columns", help="扫值域落在目标 id 集合里的槽位")
    p.add_argument("--for-projectile", action="store_true",
                   help="目标集合 = 弹丸表 id（1..355）")
    p.add_argument("--ids", default="", help="显式 id 列表（逗号分隔，可写 0x..）")
    p.add_argument("--min-hits", type=int, default=3)
    p.set_defaults(func=cmd_columns)

    p = sub.add_parser("entity", help="打印某实体的全部组件行")
    p.add_argument("key", type=lambda s: int(s, 0))
    p.add_argument("--raw", type=int, default=0, help="额外打印前 N 字节 hex")
    p.set_defaults(func=cmd_entity)

    p = sub.add_parser("delta-info", help="entity delta 存储的几何与组件索引直方图")
    p.set_defaults(func=cmd_delta_info)

    p = sub.add_parser("delta-show", help="打印某个 AddPath（配件/弹种）的 delta 补丁")
    p.add_argument("addpath", type=lambda s: int(s, 0))
    p.set_defaults(func=cmd_delta_show)

    p = sub.add_parser("delta-ammo", help="列出所有配件 delta 补丁（可 join 配件总表 CSV）")
    p.add_argument("--csv", default=r"D:\mod\refs\exports\weapon_customization_settings.csv",
                   help="weapon_customization_settings 导出 CSV（可选，用来带名字）")
    p.add_argument("--component", type=int, default=None, help="只看某个组件索引")
    p.add_argument("--member", type=int, default=None, help="只看某个成员偏移")
    p.add_argument("--slot", default="", help="只看某个槽位名，如 AmmoType / AmmoTypeAlt")
    p.set_defaults(func=cmd_delta_ammo)

    a = ap.parse_args()
    return a.func(a)


if __name__ == "__main__":
    raise SystemExit(main())
