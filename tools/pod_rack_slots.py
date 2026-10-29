#!/usr/bin/env python3
"""pod_rack_slots.py -- 投送舱「每条 rack 能吐几个槽」普查（只读）。

要回答的问题
    同是战备空投舱，为什么有的舱掉 1 件、有的掉 4 件、有的掉 6 件？
    答案不在战备行、也不在载荷实体里，而在 `HellpodRackComponentData` 的**行内一个 u32**：
    `+556` `spawn_payload_size` —— 只有**前 N 个槽**会生成。

三个数字（每次跑都按 typelib 现算，不写死偏移）
    物理槽  8       每行 512 B = 8 × `RackAttach`(64 B)
    authored       槽里的 `Item`(u64)≠0 的个数（原版最多 6）
    spawn   1/2/4/6 `+556`，**这才是「能吐几个」**
    random  `+552`，≠0 时从 authored 里随机抽（原版只有 2 条：rack 39 / 71）

槽内 `+52`（`+0x34`）是 `RackSide` 枚举（0 未 authore / 1 右 / 2 左），**不是数量** —— 早期
把 1/2/1/2 读成"数量 1/2/1/2"是误读，本工具用 SDK `PodPayloadCapabilities.json` 的
`rackSide` 逐槽对齐来钉住它。

用法
    python tools/pod_rack_slots.py                     # 分布 + 高容量舱
    python tools/pod_rack_slots.py --table             # 73 行 markdown 全表
    python tools/pod_rack_slots.py --rack 47           # 单条详情
    python tools/pod_rack_slots.py --json refs/pod-rack-slots-26251122.json
    python tools/pod_rack_slots.py --compare <另一份明文目录>   # 跨 build 对 spawn/载荷
    python tools/pod_rack_slots.py --sdk <PodPayloadCapabilities.json>   # 用 SDK 名字补标

只读：不改任何文件（除非给 `--json`/`--out`）。
"""
from __future__ import annotations

import argparse
import json
import pathlib
import struct
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from typelib import TypeLib                                        # noqa: E402

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:                                              # noqa: BLE001
        pass

DEFAULT_PLAIN = r"D:\mod\refs\dlbin\plaintext-26251122"
NAMES_JSON = HERE.parent / "refs" / "entity-locid-names.json"
ALIAS_JSON = HERE.parent / "refs" / "pod-rack-aliases.json"
RACK_TID = 0xA98BB156
OFF_SPAWN = 556          # spawn_payload_size：前 N 个槽生成
OFF_RANDOM = 552         # random_payload_size：≠0 时随机抽
OFF_SIDE = 52            # RackAttach +0x34 = RackSide（0 = 未 authore）


# ------------------------------------------------------------------ 容器
def entity_blocks(buf: bytes) -> dict[int, dict]:
    """实体库块序列：u32 type | 'LDLD' | ver | type | payload | u8 wide | 7 rsv"""
    out, pos = {}, 0
    while True:
        j = buf.find(b"LDLD", pos)
        if j < 0:
            break
        head = j - 4
        if head < 0:
            pos = j + 4
            continue
        tid = struct.unpack_from("<I", buf, head)[0]
        ver, inner, payload = struct.unpack_from("<III", buf, j + 4)
        if ver != 1 or inner != tid or head + 28 + payload > len(buf):
            pos = j + 4
            continue
        out.setdefault(tid, {"head": head, "tid": tid, "payload": payload, "body": head + 28})
        pos = head + 28 + payload
    return out


# ------------------------------------------------------------------ 载荷名
def load_entity_names() -> dict[int, dict]:
    if not NAMES_JSON.exists():
        return {}
    data = json.loads(NAMES_JSON.read_text(encoding="utf-8"))
    return {int(e["key"], 16): e for e in data["entity_index"]}


def item_label(names: dict[int, dict], key: int) -> str:
    if not key:
        return "—"
    e = names.get(key)
    if not e:
        return f"0x{key:016X}"
    nm = e.get("name") or "?"
    kind = e.get("kind") or "?"
    return f"{nm} [{kind}]"


# ------------------------------------------------------------------ rack 解析
class Racks:
    def __init__(self, plain_dir: pathlib.Path, names: dict[int, dict]):
        self.dir = plain_dir
        self.names = names
        self.lib = TypeLib((plain_dir / "dl_library.dl_typelib").read_bytes())
        self.ent = (plain_dir / "generated_entities.dl_bin").read_bytes()
        blk = entity_blocks(self.ent).get(RACK_TID)
        if not blk:
            raise SystemExit(f"✗ {plain_dir} 里没有 HellpodRackComponentData 块")
        self.body = blk["body"]
        ms = self.lib.members(RACK_TID)
        self.slot_bytes = ms[0]["size64"]
        row_tid = ms[1]["type_id"]
        self.stride = self.lib.desc(row_tid)[3]
        self.row_count = ms[1]["size64"] // self.stride
        rms = self.lib.members(row_tid)
        self.slot_off = rms[0]["offset64"]
        self.slot_stride = self.lib.desc(rms[0]["type_id"])[3]
        self.n_slots = rms[0]["size64"] // self.slot_stride
        self.row_base = self.body + self.slot_bytes
        self.keys = {}
        for i in range(self.slot_bytes // 16):
            k, v = struct.unpack_from("<QI", self.ent, self.body + 16 * i)
            if k:
                self.keys[k] = v

    def row(self, row: int) -> dict:
        o = self.row_base + row * self.stride
        items, sides = [], []
        for i in range(self.n_slots):
            p = o + self.slot_off + i * self.slot_stride
            items.append(struct.unpack_from("<Q", self.ent, p)[0])
            sides.append(struct.unpack_from("<I", self.ent, p + OFF_SIDE)[0])
        return {
            "row": row,
            "key": next((k for k, v in self.keys.items() if v == row), 0),
            "spawn": struct.unpack_from("<I", self.ent, o + OFF_SPAWN)[0],
            "random": struct.unpack_from("<I", self.ent, o + OFF_RANDOM)[0],
            "items": items,
            "sides": sides,
            "authored": sum(1 for x in items if x),
        }

    def all_rows(self) -> list[dict]:
        return [self.row(r) for r in range(self.row_count)]


# ------------------------------------------------------------------ 战备名（可选）
def strat_names(plain_dir: pathlib.Path) -> dict[int, dict]:
    """rack 首槽物品 → 战备行（`+0xF8` LOE id 唯一命中 / `+0xA8` 包唯一命中）。

    纯只读尽力而为：命中不唯一就留空，宁缺勿错。
    """
    try:
        sys.path.insert(0, str(HERE))
        from pod_loadout import Data                                # noqa: PLC0415
        from strat_slot_census import strat_rows, internal_names    # noqa: PLC0415
    except Exception:                                              # noqa: BLE001
        return {}
    d = Data()
    _m, _stride, rack_rows, _base = d.hashmap(RACK_TID)
    rws = strat_rows(d)
    internals, _keys = internal_names(d, rws)
    rows_meta = []
    for idx, (base, _body) in enumerate(rws):
        rows_meta.append({
            "idx": idx,
            "id": struct.unpack_from("<I", d.strat, base)[0],
            "a8": struct.unpack_from("<Q", d.strat, base + 0xA8)[0],
            "f8": struct.unpack_from("<I", d.strat, base + 0xF8)[0],
            "name": internals[idx],
        })
    out = {}
    for row in range(rack_rows):
        r = d.rack(row)
        first = next((x for x in r["items"] if x), 0)
        if not first:
            continue
        loe, pkg = d.item_loadout_id(first), d.item_package(first)
        hit_f8 = [m for m in rows_meta if loe and m["f8"] == loe]
        hit_a8 = [m for m in rows_meta if pkg and m["a8"] == pkg]
        hit = hit_f8 if len(hit_f8) == 1 else (hit_a8 if len(hit_a8) == 1 else [])
        if hit:
            out[row] = hit[0]
    return out


# ------------------------------------------------------------------ 分类
def capacity_class(r: dict) -> str:
    if r["random"]:
        return "随机"
    if r["spawn"] >= 4:
        return "多件"
    if r["spawn"] == 2:
        return "成对"
    return "单件"


def describe(racks: Racks, strat: dict[int, dict], sdk: dict | None,
             alias: dict | None = None) -> list[dict]:
    alias = alias or {}
    out = []
    for r in racks.all_rows():
        payloads = [(i, item_label(racks.names, it), r["sides"][i])
                    for i, it in enumerate(r["items"]) if it]
        st = strat.get(r["row"])
        al = alias.get(r["row"]) or alias.get(str(r["row"])) or {}
        # 实际吐出件数：spawn 数的是「前 N 个非空槽」（引擎跳过空槽，把后面的 authored 槽顶上来），
        # 所以 spawn > authored 的舱实际只会掉 authored 件。
        effective = min(r["spawn"], r["authored"])
        out.append({
            **r,
            "capacity": capacity_class(r),
            "effective": effective,
            "payloads": payloads,
            "strat": st["name"] if st else "",
            "strat_id": st["id"] if st else None,
            "alias": al.get("name", ""),
            "alias_status": al.get("status", ""),
            "alias_note": al.get("note", ""),
        })
    if sdk:
        for e in out:
            e["sdk"] = match_sdk(e, sdk)
    return out


def match_sdk(entry: dict, sdk: dict) -> str:
    """用 (spawn, random, authored 数, 槽 payload 名后缀) 在 SDK 56 条里找唯一同构。

    宁可留空也不猜：命中 >1 条就放弃（例：rack 47 的 "Machine Gun" 同时被 MG-43 / MG-206 命中，
    靠人工 alias 才定得下来）。
    """
    if not entry["authored"]:
        return ""
    mine = [n.split(" [")[0].lower() for _i, n, _s in entry["payloads"]]
    cands = []
    for r in sdk["racks"]:
        if r["spawnCount"]["value"] != entry["spawn"] or r["randomPayloadSize"] != entry["random"]:
            continue
        theirs = [(s["current"] or {}).get("name") or "" for s in r["slots"]]
        theirs = [t.lower() for t in theirs if t]
        if len(theirs) != len(mine):
            continue
        if all(a in b or b in a for a, b in zip(mine, theirs)):
            cands.append(r["name"])
    return cands[0] if len(cands) == 1 else ""


# ------------------------------------------------------------------ 输出
def fmt_payloads(entry: dict, limit: int = 0) -> str:
    parts = []
    for i, label, side in entry["payloads"]:
        short = label.split(" [")[0]
        kind = label.split("[")[-1].rstrip("]") if "[" in label else "?"
        parts.append(f"{i}:{short}({kind},side{side})")
    if limit and len(parts) > limit:
        return " · ".join(parts[:limit]) + f" …(+{len(parts) - limit})"
    return " · ".join(parts) if parts else "（空）"


def _short(label: str) -> str:
    return label.split(" [")[0]


def _unnamed(label: str) -> bool:
    return _short(label) in ("", "?", "未知") or _short(label).startswith("0x")


def pod_label(e: dict) -> str:
    if e.get("alias"):
        return e["alias"]
    if e.get("sdk"):
        return e["sdk"]
    if e["strat"]:
        return e["strat"].strip()
    if not e["payloads"]:
        return "（空 rack）"
    if all(_unnamed(lab) for _i, lab, _s in e["payloads"]):
        return f"未命名载荷 ×{len(e['payloads'])} 舱"
    first = _short(e["payloads"][0][1])
    return f"{first} 舱" if len(e["payloads"]) == 1 else f"{first} 等 {len(e['payloads'])} 件 舱"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plain", default=DEFAULT_PLAIN)
    ap.add_argument("--rack", type=int)
    ap.add_argument("--table", action="store_true", help="输出 markdown 全表")
    ap.add_argument("--json", help="把全量普查写成 json")
    ap.add_argument("--out", help="把 markdown 表写成文件")
    ap.add_argument("--sdk", help="PodPayloadCapabilities.json（可选，用来补舱名）")
    ap.add_argument("--alias", help=f"人工舱名表（默认 {ALIAS_JSON}）")
    ap.add_argument("--compare", help="另一份明文目录，比 spawn/载荷 是否漂移")
    ap.add_argument("--no-strat", action="store_true", help="跳过战备名反查（更快）")
    a = ap.parse_args()

    plain = pathlib.Path(a.plain)
    names = load_entity_names()
    racks = Racks(plain, names)
    alias_path = pathlib.Path(a.alias) if a.alias else (ALIAS_JSON if ALIAS_JSON.exists() else None)
    alias = {}
    if alias_path and alias_path.exists():
        alias = json.loads(alias_path.read_text(encoding="utf-8")).get("aliases", {})
    strat = {}
    if not a.no_strat:
        if pathlib.Path(DEFAULT_PLAIN).resolve() == plain.resolve():
            strat = strat_names(plain)
        else:
            print("⚠ 战备名反查只支持默认明文目录（pod_loadout 里是写死的），已跳过", file=sys.stderr)
    sdk = json.loads(pathlib.Path(a.sdk).read_text(encoding="utf-8")) if a.sdk else None
    entries = describe(racks, strat, sdk, alias)

    if a.rack is not None:
        e = entries[a.rack]
        print(f"rack {e['row']}  key={e['key']:#018x}  spawn={e['spawn']}  random={e['random']}  "
              f"authored={e['authored']}/{racks.n_slots}")
        print(f"  舱：{pod_label(e)}" + (f"（战备行 #{e['strat_id']}）" if e["strat_id"] else ""))
        for i, label, side in e["payloads"]:
            print(f"    槽{i}  side={side}  {label}  {e['items'][i]:#018x}")
        return 0

    if a.compare:
        other = Racks(pathlib.Path(a.compare), names)
        other_rows = {r["row"]: r for r in other.all_rows()}
        print(f"跨 build 对比：{a.compare} → {a.plain}")
        drift = 0
        for e in entries:
            o = other_rows.get(e["row"])
            if not o:
                print(f"  rack {e['row']:2d}  另一 build 无此行")
                continue
            if o["spawn"] != e["spawn"] or o["random"] != e["random"] or o["items"] != e["items"]:
                drift += 1
                print(f"  rack {e['row']:2d}  spawn {o['spawn']}→{e['spawn']}  "
                      f"rnd {o['random']}→{e['random']}  items {'变' if o['items'] != e['items'] else '同'}")
        print(f"  ⇒ {len(entries)} 行里 {drift} 行有差异")
        return 0

    # 分布
    dist = {}
    for e in entries:
        dist[e["spawn"]] = dist.get(e["spawn"], 0) + 1
    rnd = [e["row"] for e in entries if e["random"]]
    print(f"{plain}\\generated_entities.dl_bin：{racks.row_count} 条 rack，"
          f"每行 {racks.n_slots} 槽 × {racks.slot_stride} B，行 {racks.stride} B")
    print("spawn_payload_size 分布：" + "  ".join(f"{k} 槽×{v} 条" for k, v in sorted(dist.items())))
    print(f"random_payload_size≠0：rack {rnd or '无'}")
    print("高容量舱（spawn ≥ 2）：")
    for e in entries:
        if e["spawn"] >= 2:
            print(f"  rack {e['row']:2d}  spawn={e['spawn']} rnd={e['random']}  "
                  f"{pod_label(e)}  ←  {fmt_payloads(e)}")

    if a.table or a.out:
        lines = [
            "| rack | 舱 / 消费战备 | spawn | random | authored | 实吐 | 槽（side:载荷） |",
            "|---:|---|---:|---:|---:|---:|---|",
        ]
        for e in entries:
            lines.append(f"| {e['row']} | {pod_label(e)} | {e['spawn']} | {e['random']} | "
                         f"{e['authored']} | {e['effective']} | {fmt_payloads(e)} |")
        table = "\n".join(lines)
        if a.out:
            pathlib.Path(a.out).write_text(table + "\n", encoding="utf-8")
            print(f"→ {a.out}")
        else:
            print(table)

    if a.json:
        serial = []
        for e in entries:
            serial.append({
                "row": e["row"], "key": f"0x{e['key']:016X}", "spawn": e["spawn"],
                "random": e["random"], "authored": e["authored"], "effective": e["effective"],
                "capacity": e["capacity"],
                "pod": pod_label(e), "stratagem": e["strat"], "stratagem_id": e["strat_id"],
                "sdk": e.get("sdk", ""),
                "slots": [{"slot": i, "item": f"0x{e['items'][i]:016X}", "label": label, "side": side}
                          for i, label, side in e["payloads"]],
            })
        pathlib.Path(a.json).write_text(json.dumps({
            "build": plain.name, "table": "HellpodRackComponentData", "type": f"0x{RACK_TID:08X}",
            "rows": racks.row_count, "slots_per_row": racks.n_slots,
            "spawn_distribution": {str(k): v for k, v in sorted(dist.items())},
            "racks": serial}, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"→ {a.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
