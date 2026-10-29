#!/usr/bin/env python3
"""planet_tables.py -- read-only survey/dump of the planet-side `.dl_bin` tables.

WHY
    The planet area is a family of ~12 tables (planet_data, zone_data, planet_region_settings,
    galactic_presence_settings, ...) and every question about them starts the same way: how many
    rows, how wide, what does a row point at, and what are the strings behind those pointers.
    Doing that by hand per table is hours of struct-unpacking; this tool answers it in one command.

MODEL (verified on this build's plaintext cache)
    file   = u32 group_count, then group_count * group
    group  = 'LDLD' u32 version, u32 type_id, u32 payload_size, u32 wide, u32 flags   (24 B)
             payload[payload_size]
    payload= rows (stride from the typelib type) followed by a per-group string/data tail
    A row's string members are *offsets relative to the payload start* (same convention as
    filediver's `base`), so a member that holds a small positive number is a candidate pointer.

WHAT IT DOES NOT DO
    It never writes, never launches the game, never touches process memory.  Input is the
    already-decrypted plaintext cache; the tool refuses a sealed file (no LTLD/LDLD magic).

USAGE
    python tools/planet_tables.py survey                     # every planet-side table at a glance
    python tools/planet_tables.py names planet_data          # per-row tail strings (planet names)
    python tools/planet_tables.py dump galactic_presence_settings --limit 12
    python tools/planet_tables.py dump planet_data --json out/planet/planet_data.json
    python tools/planet_tables.py fields planet_data         # typelib member map for the row type
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import struct
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import typelib  # noqa: E402

PLAIN = pathlib.Path(r"D:/mod/refs/dlbin/plaintext-26251122")
NAMES_TXT = pathlib.Path(__file__).resolve().parent.parent / "refs" / "dl-type-names.txt"

PLANET_TABLES = [
    "galactic_presence_settings", "planet_data", "planet_override_settings",
    "planet_region_settings", "planet_types_settings", "planet_color_set_settings",
    "planet_territory_graphs", "zone_data", "region_settings", "scenario_settings",
    "solar_system_settings", "distant_war_effect_settings", "environment_settings",
    "weather_settings", "sky_settings", "route_settings", "location_groups",
    "satellite_groups", "resource_swap", "modifier_settings", "generation_settings",
]


# ----------------------------------------------------------------------------- type names
def type_name_index() -> dict[int, str]:
    """djb2(name) -> name, same variant the engine uses for type ids."""
    idx: dict[int, str] = {}
    if not NAMES_TXT.exists():
        return idx
    for line in NAMES_TXT.read_text(encoding="utf-8", errors="replace").splitlines():
        s = line.strip()
        if not s or s.startswith("//") or s.startswith("====="):
            continue
        idx.setdefault(typelib.type_hash(s), s)
    return idx


# ----------------------------------------------------------------------------- container
class Group:
    __slots__ = ("index", "offset", "version", "type_id", "size", "wide", "flags", "payload")

    def __init__(self, i, off, ver, tid, size, wide, flags, payload):
        self.index, self.offset = i, off
        self.version, self.type_id, self.size = ver, tid, size
        self.wide, self.flags, self.payload = wide, flags, payload


def parse_groups(data: bytes) -> list[Group]:
    """Every LDLD group in the file, in file order, across *all* containers.

    A table can hold more than one container: `region_settings` is 74 `GenerationRegionSettings`
    groups followed by `u32 13` + 13 `GenerationRegionGroup` groups.  Walking only the first run of
    groups silently turns the second container into "leftover bytes" (a real misdiagnosis was made
    that way: "the region definitions cannot be joined anywhere").
    """
    if data[:4] == b"LTLD" or b"LDLD" not in data[:64]:
        raise SystemExit("not a plaintext .dl_bin (no LDLD group header near the start)")
    groups: list[Group] = []
    pos = 0
    while True:
        at = data.find(b"LDLD", pos)
        if at < 0 or at + 24 > len(data):
            break
        ver, tid, size, wide, flags = struct.unpack_from("<IIIII", data, at + 4)
        if ver not in (1, 2) or size == 0 or at + 24 + size > len(data):
            pos = at + 4
            continue
        groups.append(Group(len(groups), at, ver, tid, size, wide, flags, data[at + 24: at + 24 + size]))
        pos = at + 24 + size
    if not groups:
        raise SystemExit("no LDLD group with a plausible header")
    leftovers = len(data) - (groups[-1].offset + 24 + groups[-1].size)
    if leftovers:
        print(f"  ! {leftovers} B after the last group", file=sys.stderr)
    return groups


def by_type(groups: list[Group]) -> dict[int, list[Group]]:
    """Group list split by container type, most-populated first."""
    out: dict[int, list[Group]] = {}
    for g in groups:
        out.setdefault(g.type_id, []).append(g)
    return dict(sorted(out.items(), key=lambda kv: -len(kv[1])))


def strings_in(blob: bytes, minlen: int = 3) -> list[tuple[int, str]]:
    return [(m.start(), m.group().decode("latin1"))
            for m in re.finditer(rb"[ -~]{%d,}" % minlen, blob)]


def cstr_at(blob: bytes, off: int) -> str | None:
    if off <= 0 or off >= len(blob):
        return None
    end = blob.find(b"\x00", off)
    if end < 0 or end - off < 2:
        return None
    raw = blob[off:end]
    if any(c < 0x20 or c > 0x7E for c in raw):
        return None
    return raw.decode("latin1")


# ----------------------------------------------------------------------------- row decode
def row_type(lib: typelib.TypeLib, groups: list[Group]) -> tuple[int, int, list]:
    tid = groups[0].type_id
    desc = lib.desc(tid)
    members = lib.members(tid)
    size = desc[3]          # size64
    return tid, size, members


GEOMETRY = pathlib.Path(__file__).resolve().parent.parent / "refs" / "table-geometry.json"


def geometry_for(table: str) -> dict:
    """`refs/table-geometry.json` records the *element* type for container-shaped tables."""
    if not GEOMETRY.exists():
        return {}
    doc = json.loads(GEOMETRY.read_text(encoding="utf-8"))
    for t in doc.get("tables", []):
        if t.get("table") == f"generated_{table}.dl_bin":
            types = t.get("types") or []
            return types[0] if types else {}
    return {}


def row_layout(table: str, lib: typelib.TypeLib, groups: list[Group]) -> tuple[int, int, int | None]:
    """(row_type_id, stride, container_offset).

    Two shapes: the group type *is* the row type, or the group type is a one-member container whose
    single 16-byte member is `(offset, count)` pointing at an array of the element type.
    """
    tid = groups[0].type_id
    members = lib.members(tid)
    desc = lib.desc(tid)
    geo = geometry_for(table)
    elem_tid = geo.get("element_type_id")
    if len(members) == 1 and members[0]["size64"] == 16 and elem_tid and elem_tid in lib._index:
        return elem_tid, lib.desc(elem_tid)[3], members[0]["offset64"]
    return tid, desc[3], None


def decode_row(blob: bytes, members: list, stride: int, base: int = 0) -> dict:
    """Top-level members of one row; anything that looks like a pointer or an array is resolved.

    `base` is the row's offset inside the group payload; pointer members are resolved against the
    payload start (`blob`), scalars are read at `base + member offset`.
    """
    out: dict = {"_pointers": {}, "_arrays": {}, "_scalars": {}}
    for m in members:
        off, msize, mtype = m["offset64"], m["size64"], m["type_id"]
        if off + msize > stride:
            continue
        at = base + off
        if msize == 8 and mtype == 0:
            val = struct.unpack_from("<Q", blob, at)[0]
            text = cstr_at(blob, val)
            if text:
                out["_pointers"][f"+0x{off:X}"] = text
                continue
            out["_scalars"][f"+0x{off:X}"] = val
        elif msize == 16 and mtype != 0:
            a_off, a_cnt = struct.unpack_from("<QQ", blob, at)
            if 0 < a_off < len(blob) and 0 < a_cnt < 4096 and a_off % 4 == 0:
                span = len(blob) - a_off
                out["_arrays"][f"+0x{off:X}"] = {
                    "offset": a_off, "count": a_cnt,
                    "elem_size_upper": round(span / a_cnt, 2) if a_cnt else None,
                    "raw": blob[a_off:a_off + min(span, 64)].hex(),
                }
                continue
            out["_scalars"][f"+0x{off:X}"] = f"{a_off}:{a_cnt}"
        elif msize == 1:
            out["_scalars"][f"+0x{off:X}"] = blob[at]
        elif msize == 4:
            as_u32 = struct.unpack_from("<I", blob, at)[0]
            as_f32 = struct.unpack_from("<f", blob, at)[0]
            out["_scalars"][f"+0x{off:X}"] = (f"{as_u32}" if not (-1e9 < as_f32 < 1e9 and as_f32 not in (0.0,) and abs(as_f32) > 1e-6) else f"{as_f32:.6g}")
        elif msize == 8:
            out["_scalars"][f"+0x{off:X}"] = struct.unpack_from("<Q", blob, at)[0]
        else:
            out["_scalars"][f"+0x{off:X}"] = blob[at:at + msize].hex()
    return out


def iter_rows(groups: list[Group], stride: int, container: int | None = None):
    """Yield (group, row_index, payload, row_offset). Strings/pointers resolve against payload[0]."""
    for g in groups:
        if container is None:
            n = max(1, g.size // stride) if stride else 1
            for i in range(n):
                base = i * stride
                if base + stride > len(g.payload):
                    break
                yield g, i, g.payload, base
        else:
            a_off, a_cnt = struct.unpack_from("<QQ", g.payload, container)
            for i in range(min(a_cnt, 4096)):
                base = a_off + i * stride
                if base + stride > len(g.payload):
                    break
                yield g, i, g.payload, base


# ----------------------------------------------------------------------------- commands
def cmd_survey(a) -> int:
    names = type_name_index()
    lib = typelib.TypeLib((PLAIN / "dl_library.dl_typelib").read_bytes())
    print(f"{'table/container':46s} {'plain':>9s} {'grp':>4s} {'stride':>6s} {'rows_est':>8s} {'shape':>12s} type")
    for t in PLANET_TABLES:
        p = PLAIN / f"generated_{t}.dl_bin"
        if not p.exists():
            print(f"{t:46s} {'-':>9s} (missing)")
            continue
        data = p.read_bytes()
        try:
            groups = parse_groups(data)
        except SystemExit as e:
            print(f"{t:46s} {len(data):9d} {str(e)}")
            continue
        containers = by_type(groups)
        for ci, (tid, gs) in enumerate(containers.items()):
            try:
                ltid, stride, container = row_layout(t, lib, gs)
            except KeyError:
                label = t if ci == 0 else f"{t}[{ci}]"
                print(f"{label:46s} {len(data):9d} {len(gs):4d} {'?':>6s} {'?':>6s} 0x{tid:08X} not in typelib")
                continue
            rows, tail, ragged = 0, 0, 0
            for g in gs:
                if container is None:
                    n = max(1, g.size // stride)
                    rows += n
                    tail += g.size - n * stride
                    ragged += 1 if g.size % stride else 0
                else:
                    a_off, a_cnt = struct.unpack_from("<QQ", g.payload, container)
                    rows += a_cnt
                    tail += g.size - (a_off + a_cnt * stride)
            label = t if ci == 0 else f"{t}[{ci}]"
            tname = names.get(ltid, f"0x{ltid:08X}")
            # rows_est is Σ size//stride: correct for batched tables, OVER-counts tables that hold
            # exactly one record per group plus an in-group tail (zone_data reads 517 that way, truth
            # is 88 = one per ZoneId).  So print the shape and never trust rows_est for "1/grp+tail".
            shape = "1/grp+tail" if (container is None and len(gs) > 1 and ragged * 4 >= len(gs) * 3) else "N/grp"
            print(f"{label:46s} {len(data):9d} {len(gs):4d} {stride:6d} {rows:8d} {shape:>12s} {tname}")
    return 0


def pick_container(groups: list[Group], want: str) -> tuple[int, list[Group]]:
    """(type_id, groups) for the requested container: index, hex type id, or the primary one."""
    containers = by_type(groups)
    if not want:
        return next(iter(containers.items()))
    for tid, gs in containers.items():
        if want == f"0x{tid:08X}" or want == f"0x{tid:x}" or want == str(tid):
            return tid, gs
    idx = int(want)
    return list(containers.items())[idx]


def cmd_fields(a) -> int:
    lib = typelib.TypeLib((PLAIN / "dl_library.dl_typelib").read_bytes())
    groups = parse_groups((PLAIN / f"generated_{a.table}.dl_bin").read_bytes())
    _tid, groups = pick_container(groups, a.type)
    tid, stride, container = row_layout(a.table, lib, groups)
    members = lib.members(tid)
    names = type_name_index()
    print(f"table {a.table}  row type 0x{tid:08X} ({names.get(tid, '?')})  stride {stride}"
          f"  members {len(members)}  container={container}")
    for m in members:
        off, msize = m["offset64"], m["size64"]
        mtype = m["type_id"]
        print(f"  +0x{off:<4X} size={msize:<3d} type=0x{mtype:08X} {names.get(mtype, '')}")
    return 0


def cmd_names(a) -> int:
    groups = parse_groups((PLAIN / f"generated_{a.table}.dl_bin").read_bytes())
    for g in groups[: a.limit or None]:
        ss = [s for _, s in strings_in(g.payload)]
        print(f"{g.index:4d} size={g.size:5d} {ss}")
    return 0


def cmd_dump(a) -> int:
    lib = typelib.TypeLib((PLAIN / "dl_library.dl_typelib").read_bytes())
    groups = parse_groups((PLAIN / f"generated_{a.table}.dl_bin").read_bytes())
    _tid, groups = pick_container(groups, a.type)
    tid, stride, container = row_layout(a.table, lib, groups)
    print(f"container 0x{_tid:08X} groups={len(groups)} row_type=0x{tid:08X} stride={stride}", file=sys.stderr)
    members = lib.members(tid)
    out = []
    for g, i, payload, base in iter_rows(groups, stride, container):
        if a.limit and len(out) >= a.limit:
            break
        rows_end = base + stride
        rec = {"group": g.index, "row": i, "payload_size": g.size, "row_offset": base,
               "tail_strings": [s for _, s in strings_in(payload[rows_end:])]}
        rec.update(decode_row(payload, members, stride, base))
        out.append(rec)
    if a.json:
        p = pathlib.Path(a.json)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(out, indent=1), encoding="utf-8")
        print(f"wrote {p} ({len(out)} rows)")
    else:
        for rec in out:
            print(f"\n=== group {rec['group']} row {rec['row']}  payload={rec['payload_size']} base={rec['row_offset']}")
            if rec["tail_strings"]:
                print("  strings:", rec["tail_strings"])
            if rec["_pointers"]:
                print("  ptr    :", rec["_pointers"])
            if rec["_arrays"]:
                print("  arrays :", {k: (v["offset"], v["count"], v["elem_size_upper"])
                                    for k, v in rec["_arrays"].items()})
            print("  scalars:", rec["_scalars"])
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("survey", help="one line per planet-side table")
    s.set_defaults(func=cmd_survey)

    s = sub.add_parser("fields", help="typelib member map for a table's row type")
    s.add_argument("table")
    s.add_argument("--type", default="", help="container index / 0xTYPE (default: primary)")
    s.set_defaults(func=cmd_fields)

    s = sub.add_parser("names", help="per-group tail strings")
    s.add_argument("table")
    s.add_argument("--limit", type=int, default=0)
    s.set_defaults(func=cmd_names)

    s = sub.add_parser("dump", help="decode rows (pointers/arrays/scalars)")
    s.add_argument("table")
    s.add_argument("--type", default="", help="container index / 0xTYPE (default: primary)")
    s.add_argument("--limit", type=int, default=0)
    s.add_argument("--json", default="")
    s.set_defaults(func=cmd_dump)

    a = ap.parse_args()
    return a.func(a)


if __name__ == "__main__":
    sys.exit(main())
