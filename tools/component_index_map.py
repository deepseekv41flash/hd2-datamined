#!/usr/bin/env python3
"""Derive the entity component-index space offline (for one generated_entities.dl_bin).

Block 0 (EntitySettingsHashmap, 0x80C1CA70) stores, per entity key, a **byte offset + u16 count**
into a packed u16 list = the entity's component-type indices.  Every other block's hashmap tells
which entities own a row of that component.  Matching the two views solves
    component block <-> component type index
without any runtime pointers (runtime-free replacement for the old dump-window method).

usage:
  python tools/component_index_map.py [--plain <generated_entities.dl_bin>] [--json out.json]
"""
from __future__ import annotations

import argparse
import json
import pathlib
import struct
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from pod_rack_swap import parse_blocks  # noqa: E402
from typelib import TypeLib              # noqa: E402

PLAIN = r"D:\mod\refs\dlbin\plaintext-26251122\generated_entities.dl_bin"
TYPELIB = r"D:\mod\refs\dlbin\plaintext-26251122\dl_library.dl_typelib"
B0_TID = 0x80C1CA70
NAMES_MANIFEST = r"C:\Users\Admin\HD2SDK-CommunityEdition\.tmp-c9data\shal_files.txt"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plain", default=PLAIN)
    ap.add_argument("--typelib", default=TYPELIB)
    ap.add_argument("--json", default=None)
    a = ap.parse_args()
    data = pathlib.Path(a.plain).read_bytes()
    lib = TypeLib(open(a.typelib, "rb").read())
    blocks = parse_blocks(data)
    b0 = [b for b in blocks if b["type_id"] == B0_TID][0]
    body = b0["head"] + 28
    payload_end = body + b0["payload"]

    entity_list = {}
    for i in range((payload_end - body) // 32 if False else 4096):
        rec = struct.unpack_from("<QIIIIII", data, body + 32 * i)
        key, list_off, _z1, count, _z2, _h, _z3 = rec
        if key:
            entity_list[key] = (list_off, count)
    print("block0: payload %d B, entities %d" % (b0["payload"], len(entity_list)))

    idx_entities = {}
    for key, (off, count) in entity_list.items():
        vals = struct.unpack_from("<%dH" % count, data, body + off)
        for v in vals:
            idx_entities.setdefault(v, set()).add(key)

    results, unresolved = {}, []
    for b in blocks:
        tid = b["type_id"]
        if tid == B0_TID:
            continue
        try:
            hmap_bytes = lib.members(tid)[0]["size64"]
        except KeyError:
            unresolved.append((tid, b["head"], "no typelib"))
            continue
        body_b = b["head"] + 28
        keys = set()
        for i in range(hmap_bytes // 16):
            k, _v = struct.unpack_from("<QI", data, body_b + 16 * i)
            if k:
                keys.add(k)
        cand = [v for v, ents in idx_entities.items() if ents == keys]
        if len(cand) == 1:
            results[tid] = {"index": cand[0], "head": b["head"],
                            "payload": b["payload"], "entities": len(keys)}
        else:
            unresolved.append((tid, b["head"], "cands=%s" % cand[:8]))
    # second pass: blocks are stored in the same order as their component indices (verified:
    # every resolved pair is monotonic), so a run of unresolved blocks between two anchors must take
    # the remaining unused indices of that gap, in order.
    order = [(rank, b) for rank, b in enumerate(blocks) if b["type_id"] != B0_TID]
    rank_of = {b["head"]: rank for rank, b in enumerate(blocks)}
    used = {info["index"] for info in results.values()}
    anchors = sorted(((rank_of[b["head"]], results[b["type_id"]]["index"])
                      for b in blocks if b["type_id"] in results))
    inferred = 0
    for (r0, i0), (r1, i1) in zip(anchors, anchors[1:]):
        run = [b for rank, b in order if r0 < rank < r1 and b["type_id"] not in results]
        free = [v for v in range(i0 + 1, i1) if v not in used]
        if len(run) == len(free) and run:
            for b, v in zip(run, free):
                results[b["type_id"]] = {"index": v, "head": b["head"], "payload": b["payload"],
                                         "entities": -1, "inferred": True}
                used.add(v)
                inferred += 1
    print("resolved %d/%d blocks (%d inferred from index order)" % (
        len(results), len(blocks) - 1, inferred))
    for tid, head, why in unresolved[:12]:
        print("  UNRESOLVED tid 0x%08X head 0x%X %s" % (tid, head, why))

    names = {}
    try:
        sys.path.insert(0, r"C:\Users\Admin\HD2SDK-CommunityEdition")
        from srkit.util.hashing import djb2_type_id
        manifest = pathlib.Path(NAMES_MANIFEST)
        if manifest.is_file():
            for line in manifest.read_text(encoding="utf-8", errors="replace").splitlines():
                line = line.strip()
                if line.startswith("data/components/") and line.endswith(".json"):
                    nm = line[len("data/components/"):-5]
                    names[djb2_type_id(nm)] = nm
    except Exception as exc:                                    # noqa: BLE001
        print("  (component names unavailable: %s)" % exc)
    seen = {}
    for tid, info in sorted(results.items(), key=lambda kv: kv[1]["index"]):
        nm = names.get(tid, "?")
        print("  idx %3d  tid 0x%08X  %-34s payload %-7d entities %d"
              % (info["index"], tid, nm, info["payload"], info["entities"]))
        seen.setdefault(info["index"], []).append(nm)
    dup = {k: v for k, v in seen.items() if len(v) > 1}
    if dup:
        print("  DUPLICATE indices:", dup)
    if a.json:
        pathlib.Path(a.json).write_text(json.dumps(
            {"index_of": {("0x%08X" % t): v["index"] for t, v in results.items()},
             "unresolved": [[("0x%08X" % t), h, w] for t, h, w in unresolved]}, indent=1),
            encoding="utf-8")
        print("wrote", a.json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
