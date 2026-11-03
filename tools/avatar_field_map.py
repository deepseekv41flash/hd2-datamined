#!/usr/bin/env python3
"""avatar_field_map.py -- name every field of the Helldiver `AvatarComponent` record, offline.

Where the names come from
    - `refs/web/filediver_datalibrary_avatar_component.go` (vendored from xypwn/filediver, MIT-ish
      reverse-engineering Go sources) declares the same structs in Go field order.
    - Go layout (sequential, natural alignment) is simulated here, then **validated against our
      typelib**: every typelib member offset/size of `AvatarComponentData` must equal a simulated
      struct boundary, and the total size must equal the block row stride (852 B in build 26251122).
    - Current build 26251122 **has no `MovementHaptics` member** (filediver's snapshot does, 40 B):
      pass --drop-haptics (default on) so offsets line up.

Usage
    python tools/avatar_field_map.py                 # print the full map with current vanilla values
    python tools/avatar_field_map.py --plain X.dl_bin --compare M.dl_bin   # show §diff vs another table
    python tools/avatar_field_map.py --json out.json
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import struct
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from pod_rack_swap import parse_blocks  # noqa: E402
from typelib import TypeLib              # noqa: E402

GO_SRC = pathlib.Path(r"D:\mod\refs\web\filediver_datalibrary_avatar_component.go")
PLAIN = r"D:\mod\refs\dlbin\plaintext-26251122\generated_entities.dl_bin"
TYPELIB = r"D:\mod\refs\dlbin\plaintext-26251122\dl_library.dl_typelib"
BLOCK_TID = 0x40EF204C          # AvatarComponentData
ROW_TID = 0xB501F712            # AvatarComponent
HELLDIVER_KEY = 0x4D1C334D294DFA97

SIZES = {
    "float32": 4, "uint32": 4, "int32": 4, "uint16": 2, "int16": 2, "uint8": 1, "int8": 1,
    "uint64": 8, "int64": 8,
    "stingray.ThinHash": 4, "stingray.Hash": 8,
    "mgl32.Vec2": 8, "mgl32.Vec3": 12,
}


def parse_go_structs(path: pathlib.Path):
    text = path.read_text(encoding="utf-8")
    out = {}
    for m in re.finditer(r"^type (\w+) struct \{\n(.*?)^\}", text, re.M | re.S):
        name, body = m.group(1), m.group(2)
        fields = []
        for line in body.splitlines():
            line = line.strip()
            if not line or line.startswith("//"):
                continue
            mm = re.match(r"^([A-Za-z_]\w*)\s+([\[\]\w\.]+)", line)
            if not mm:
                continue
            fields.append((mm.group(1), mm.group(2)))
        out[name] = fields
    return out


def type_size(t: str, structs: dict) -> int:
    if t in SIZES:
        return SIZES[t]
    if t.startswith("enum."):
        return 4
    if t.startswith("[") and "]" in t:
        n, rest = t[1:].split("]")
        return int(n) * type_size(rest, structs)
    if t in structs:
        return layout(t, structs)[1]
    raise KeyError(t)


def type_align(t: str, structs: dict) -> int:
    """Go natural alignment: scalars 4 (f32/u32/enum/ThinHash), 8 for u64/Hash; Vec2/Vec3 align 4
    (they are [N]float32); arrays take the element alignment; structs the max member alignment."""
    if t in ("uint64", "int64", "stingray.Hash"):
        return 8
    if t in ("mgl32.Vec2", "mgl32.Vec3", "float32", "uint32", "int32"):
        return 4
    if t.startswith("enum.") or t in SIZES:
        return 4
    if t.startswith("[") and "]" in t:
        return type_align(t[1:].split("]")[1], structs)
    if t in structs:
        return max([type_align(ft, structs) for _n, ft in structs[t]] or [1])
    raise KeyError(t)


def layout(name: str, structs: dict):
    """Return ([(offset, field, type, size)], total_size) for a Go struct (natural alignment)."""
    fields = structs[name]
    off, out = 0, []
    for fname, ftype in fields:
        sz = type_size(ftype, structs)
        align = type_align(ftype, structs)
        if off % align:
            off += align - off % align
        out.append((off, fname, ftype, sz))
        off += sz
    return out, off


def find_row(data: bytes, lib: TypeLib, key: int):
    blocks = parse_blocks(data)
    b = [x for x in blocks if x["type_id"] == BLOCK_TID]
    if len(b) != 1:
        raise SystemExit("✗ 找不到唯一的 AvatarComponentData 块")
    b = b[0]
    slots = lib.members(BLOCK_TID)[0]["size64"]
    stride = lib.desc(lib.members(BLOCK_TID)[1]["type_id"])[3]
    body = b["head"] + 28
    for i in range(slots // 16):
        k, v = struct.unpack_from("<QI", data, body + 16 * i)
        if k == key:
            return body + slots + v * stride, stride, lib.members(BLOCK_TID)
    raise SystemExit("✗ 键不在哈希图里")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plain", default=PLAIN)
    ap.add_argument("--key", default=hex(HELLDIVER_KEY))
    ap.add_argument("--drop-haptics", dest="drop_haptics", action="store_true", default=True)
    ap.add_argument("--keep-haptics", dest="drop_haptics", action="store_false")
    ap.add_argument("--json", default=None)
    a = ap.parse_args()

    structs = parse_go_structs(GO_SRC)
    fields_full, total_full = layout("AvatarComponent", structs)
    print("filediver AvatarComponent: %d members, %d B (with MovementHaptics)" % (
        len(fields_full), total_full))
    # current build: drop MovementHaptics (10 ThinHash = 40 B), then shift later members
    fields, total = [], 0
    for off, fname, ftype, sz in fields_full:
        if a.drop_haptics and fname == "MovementHaptics":
            continue
        fields.append((total, fname, ftype, sz))
        total += sz
    print("current-build layout: %d members, %d B (haptics dropped: %s)" % (
        len(fields), total, a.drop_haptics))

    data = pathlib.Path(a.plain).read_bytes()
    lib = TypeLib(open(TYPELIB, "rb").read())
    row, stride, block_members = find_row(data, lib, int(a.key, 0))
    print("row @0x%X stride %d  typelib members %s" % (
        row, stride, [(m["offset64"], m["size64"]) for m in block_members]))
    assert total == stride, "layout total %d != row stride %d" % (total, stride)
    # cross-check: every typelib member offset of the row struct must exist in the simulated layout
    row_members = lib.members(ROW_TID)
    sim_offsets = {off for off, _n, _t, _s in fields}
    tl_offsets = {m["offset64"] for m in row_members}
    missing = sorted(tl_offsets - sim_offsets)
    print("typelib-vs-simulated member offsets: %s" % (
        "PASS (all %d typelib offsets found)" % len(tl_offsets) if not missing
        else "FAIL missing %s" % [hex(x) for x in missing]))
    assert not missing, "typelib offsets not covered by simulated layout"

    # flatten recursively, print values
    table = []

    def walk(prefix, ftype, base_off):
        if ftype.startswith("["):
            n, rest = ftype[1:].split("]")
            sz = type_size(rest, structs)
            for i in range(int(n)):
                walk("%s[%d]" % (prefix, i), rest, base_off + i * sz)
        elif ftype in structs:
            for off, fname, ft, _sz in layout(ftype, structs)[0]:
                walk(prefix + "." + fname, ft, base_off + off)
        else:
            sz = type_size(ftype, structs)
            raw = data[row + base_off:row + base_off + sz]
            if sz == 4:
                u = struct.unpack("<I", raw)[0]
                f = struct.unpack("<f", raw)[0]
                table.append((base_off, prefix, ftype, sz, "f32=%g u32=%d 0x%08X" % (f, u, u)))
            elif sz == 8:
                v2 = struct.unpack("<2f", raw)
                u = struct.unpack("<Q", raw)[0]
                table.append((base_off, prefix, ftype, sz, "vec2=(%g, %g) u64=0x%X" % (v2[0], v2[1], u)))
            elif sz == 12:
                v3 = struct.unpack("<3f", raw)
                table.append((base_off, prefix, ftype, sz, "vec3=(%g, %g, %g)" % v3))
            else:
                table.append((base_off, prefix, ftype, sz, raw.hex()))

    for off, fname, ftype, sz in fields:
        walk(fname, ftype, off)
    print("\n%-7s %-62s %-16s %s" % ("offset", "field", "type", "value"))
    for off, name, ftype, sz, val in table:
        print("+0x%03X  %-62s %-16s %s" % (off, name, ftype, val))
    if a.json:
        pathlib.Path(a.json).write_text(json.dumps(
            [{"offset": o, "field": n, "type": t, "size": s, "value": v}
             for o, n, t, s, v in table], indent=1, ensure_ascii=False), encoding="utf-8")
        print("\nwrote", a.json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
