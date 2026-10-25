"""Give entity component rows a field map: typelib offsets + filediver field names.

The entity component blocks in ``generated_entities.dl_bin`` store their rows in
an inline array whose layout lives in ``dl_library.dl_typelib``::

    component block payload = [0] hashmap (16 B header + slots)
                              [1] inline array of rows  <- the field map below

The typelib has no strings, so member names are missing.  ``xypwn/filediver``
declares the same structs in Go field order, so pairing the Go field list with
the typelib member list (by simulated Go layout offsets) recovers the names.

usage:
  python tools/entity_fields.py --component WeaponDataComponentData
  python tools/entity_fields.py --component WeaponDataComponentData --json out.json

⚠ 本示例写于 build 25988413；当前 build 用 tools/entity_field_set.py（同样的读法 + 门禁），
完整案例见 docs/cases/。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(r"D:\mod\tools")))

import typelib as T                                  # noqa: E402  (D:\mod\tools\typelib.py)

TYPELIB = Path(r"D:\mod\refs\dlbin\plaintext-all\dl_library.dl_typelib")
#: filediver Go sources already downloaded next to this project
GO_SOURCES = {
    "WeaponDataComponentData": Path(r"D:\mod\refs\web\datalibrary_weapon_data_component.go"),
    "ProjectileWeaponComponentData": Path(r"D:\mod\refs\web\datalibrary_projectile_weapon_component.go"),
}

#: primitive sizes used to simulate the Go layout (Go == on-disk layout here)
PRIMITIVE = {
    "float32": 4, "uint32": 4, "int32": 4, "uint16": 2, "uint8": 1, "int8": 1,
    "uint64": 8, "int64": 8,
}
VECTOR = {"mgl32.Vec2": 8, "mgl32.Vec3": 12, "mgl32.Vec4": 16}
POINTERISH = {"stingray.Hash": 8, "stingray.ThinHash": 4}


def djb2(text: str) -> int:
    value = 5381
    for byte in text.encode():
        value = (value * 33 + byte) & 0xFFFFFFFF
    return (value - 5381) & 0xFFFFFFFF


def go_fields(path: Path, struct: str) -> list[dict]:
    """Fields of a Go struct in declaration order, with a simulated offset."""
    text = path.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"type " + struct + r" struct \{(.*?)\n\}", text, re.S)
    if not match:
        raise SystemExit(f"{path}: struct {struct} not found")
    fields = []
    for line in match.group(1).splitlines():
        line = line.split("//", 1)[0].strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        name, type_text = parts[0], parts[1]
        fields.append({"name": name, "type": type_text})
    return fields


def parse_type(text: str) -> tuple[int, int]:
    """(size, alignment) of a Go field type; unknown types fall back to (0, 1)."""
    if text in PRIMITIVE:
        size = PRIMITIVE[text]
        return size, min(size, 8)
    if text in VECTOR:
        size = VECTOR[text]
        return size, 4
    if text in POINTERISH:
        size = POINTERISH[text]
        return size, min(size, 8)
    array = re.fullmatch(r"\[(\d+)\](.+)", text)
    if array:
        count = int(array.group(1))
        inner_size, inner_align = parse_type(array.group(2))
        return count * inner_size, inner_align or 1
    if text.startswith("enum."):
        return 4, 4
    return 0, 1        # nested struct: size comes from the typelib member at that position


def align_go_fields(fields: list[dict]) -> list[dict]:
    """Simulate Go struct layout; nested structs get their size filled later."""
    offset = 0
    out = []
    for field in fields:
        size, align = parse_type(field["type"])
        if size:
            offset = (offset + align - 1) // align * align
        out.append({**field, "offset": offset, "size": size})
        offset += size
    return out


def build_map(lib, component: dict) -> list[dict]:
    """Pair the Go field list with the members of the *row* struct."""
    tid = component["row_type"]
    members = lib.members(tid)
    fields = align_go_fields(go_fields(component["path"], component["struct"]))
    rows = []
    index = 0
    for field in fields:
        if field["name"] == "_":
            # Go padding does not exist in the typelib (members are real fields)
            continue
        if index >= len(members):
            rows.append({**field, "member": None, "note": "typelib exhausted"})
            continue
        member = members[index]
        # a nested struct has size 0 in the Go parser: take the typelib size
        if field["size"] == 0:
            field["size"] = member["size64"]
        rows.append({
            "name": field["name"],
            "go_type": field["type"],
            "offset": member["offset64"],
            "size": member["size64"],
            "type_id": f"0x{member['type_id']:08X}",
        })
        index += 1
    rows.append({"name": "<typelib tail>", "remaining_members": len(members) - index})
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--component", required=True)
    ap.add_argument("--json", type=Path)
    ap.add_argument("--limit", type=int, default=200)
    args = ap.parse_args()

    lib = T.TypeLib(TYPELIB.read_bytes())
    type_id = djb2(args.component)
    if type_id not in lib._index:
        print(f"error: {args.component} (0x{type_id:08X}) is not in the typelib", file=sys.stderr)
        return 2
    desc = lib.desc(type_id)
    slots = lib.members(type_id)
    if len(slots) < 2:
        print(f"error: {args.component} typelib layout has {len(slots)} member(s), expected 2 "
              f"(hashmap + row array)", file=sys.stderr)
        return 2
    row_type = slots[1]["type_id"]
    row_desc = lib.desc(row_type)
    row_size = row_desc[3]
    count = slots[1]["size64"] // row_size if row_size else 0
    print(f"{args.component} type=0x{type_id:08X}: hashmap {slots[0]['size64']:,} B + "
          f"row array {slots[1]['size64']:,} B")
    print(f"  row struct 0x{row_type:08X}: {row_size:,} B x {count} row(s), "
          f"{row_desc[6]} members")
    go = GO_SOURCES.get(args.component)
    if go is None or not go.exists():
        print("  (no filediver source for this component; printing offsets only)")
        for index, member in enumerate(lib.members(row_type)[:args.limit]):
            print(f"  [{index:2d}] off {member['offset64']:>6} size {member['size64']:>5} "
                  f"type 0x{member['type_id']:08X}")
        return 0

    rows = build_map(lib, {"row_type": row_type, "path": go,
                           "struct": "WeaponDataComponent" if "weapon_data" in go.name
                           else "ProjectileWeaponComponent"})
    print(f"{'field':40s} {'go type':22s} {'offset':>7} {'size':>5} {'type id':>12}")
    for row in rows:
        if "member" in row and row.get("member") is None and row.get("note"):
            print(f"{row['name']:40s} {'-':22s} {'-':>7} {'-':>5}   {row['note']}")
            continue
        if "remaining_members" in row:
            print(f"  typelib members not consumed: {row['remaining_members']}")
            continue
        print(f"{row['name']:40s} {row['go_type']:22s} {row['offset']:>7} "
              f"{row['size']:>5}   {row['type_id']}")
    if args.json:
        args.json.write_text(json.dumps(rows, indent=1), encoding="utf-8")
        print(f"wrote {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
