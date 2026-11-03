#!/usr/bin/env python3
"""avatar_deltas.py -- which entity deltas patch AvatarComponentData (comp 235), and which avatar fields
they overwrite. This is the data-level bridge between customizations (armor/boosters/loadout) and the
Helldiver AvatarComponent record.

Background
    `generated_entity_deltas.dl_bin` (ComponentEntityDeltaStorage) holds, per customization resource hash,
    a list of {component index, member offset, bytes}.  A patch whose component == 235 overwrites a field of
    the avatar's AvatarComponentData — the game turns that into a per-spawn private copy of the record
    (hd2runtime: "The game makes a private copy only at spawn, from an entity delta").
    Current build has exactly 3 such deltas:

      0x73012E9238B6E3B9  walk 1.5 / jog 4.08          (the ship avatar's private copy)
      0x7CBC47149F781994  sprint stamina decay 4 s, recover stand/crouch/prone 18/16/14 s
      0x42654E8989043F96  long-throw power multiplier 1.85

usage
    python tools/avatar_deltas.py                  # current build, comp 235, named fields
    python tools/avatar_deltas.py --component 239  # any other component (name unknown unless in map)
    python tools/avatar_deltas.py --json out.json
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import struct
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from ref_scan import load_delta_store, delta_patches  # noqa: E402

PLAIN = r"D:\mod\refs\dlbin\plaintext-26251122"
FIELDS = pathlib.Path(r"D:\mod\work\repo-datamined\refs\avatar-component-fields-26251122.json")
AVATAR_COMPONENT = 235


def main() -> int:
    ap = argparse.ArgumentParser(description="列出写 AvatarComponentData 的 entity delta")
    ap.add_argument("--plaintext", default=PLAIN)
    ap.add_argument("--component", type=int, default=AVATAR_COMPONENT)
    ap.add_argument("--fields", default=str(FIELDS))
    ap.add_argument("--json", default=None)
    ap.add_argument("--all-patches", action="store_true", help="也打印其它组件的命中（默认只打目标组件）")
    a = ap.parse_args()

    store = load_delta_store(pathlib.Path(a.plaintext) / "generated_entity_deltas.dl_bin")
    if store is None:
        print("✗ 没找到 ComponentEntityDeltaStorage 块")
        return 2
    field_of = {}
    try:
        for f in json.loads(pathlib.Path(a.fields).read_text(encoding="utf-8")):
            if f["size"] == 4:
                field_of[f["offset"]] = f["field"]
    except FileNotFoundError:
        print("⚠ 没有字段图 JSON，只打印偏移")

    print("delta store: %d keys, %s B; 目标组件索引 %d" % (
        len(store["hashmap"]), f"{store['size']:,}", a.component))
    hist = collections.Counter()
    touching = {}
    for key in store["hashmap"]:
        pats = delta_patches(store, key)
        for p in pats:
            hist[p["component"]] += 1
        hit = [p for p in pats if p["component"] == a.component]
        if hit:
            touching[key] = hit
    print("组件补丁直方图 top10:", hist.most_common(10))
    print("写目标组件的 delta: %d 个" % len(touching))

    out = {}
    for key, pats in sorted(touching.items(), key=lambda kv: -len(kv[1])):
        print("\nkey 0x%016X  (%d patches)" % (key, len(pats)))
        rows = []
        for p in pats:
            name = field_of.get(p["member"], "?")
            if p["size"] == 4:
                u = struct.unpack("<I", p["bytes"])[0]
                f = struct.unpack("<f", p["bytes"])[0]
                print("   +0x%03X %-52s f32=%-10g u32=%d" % (p["member"], name, f, u))
                rows.append({"member": p["member"], "field": name, "size": 4,
                             "f32": f, "u32": u})
            else:
                print("   +0x%03X %-52s size %d hex %s" % (
                    p["member"], name, p["size"], p["bytes"].hex()))
                rows.append({"member": p["member"], "field": name, "size": p["size"],
                             "hex": p["bytes"].hex()})
        out["%016X" % key] = rows
    freq = collections.Counter()
    for rows in out.values():
        for r in rows:
            freq[(r["member"], r["field"])] += 1
    print("\n被 patch 的字段:")
    for (off, name), n in freq.most_common():
        print("  +0x%03X %-52s x%d" % (off, name, n))
    if a.json:
        pathlib.Path(a.json).write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
        print("\nwrote", a.json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
