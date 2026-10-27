"""Join variant_catalog.json (the third-party proxy mod's catalogue) with the local presence table.

Read-only.  Output: out/planet/presence-variants.json + a console table.
"""
import json
import re
import struct
from pathlib import Path

CAT = Path(r"D:/Downloads/variant_mod/variant_catalog.json")
P = Path(r"D:/mod/refs/dlbin/plaintext-26088801/generated_galactic_presence_settings.dl_bin")
OUT = Path(r"D:/mod/work/repo-datamined/out/planet/presence-variants.json")

d = P.read_bytes()
pos, rows = 4, []
while pos + 24 <= len(d) and d[pos:pos + 4] == b"LDLD":
    ver, tid, size, wide, flags = struct.unpack_from("<IIIII", d, pos + 4)
    payload = d[pos + 24: pos + 24 + size]
    strs = [m.group().decode("latin1") for m in re.finditer(rb"[ -~]{3,}", payload[1000:])]
    name = next((x for x in strs if x != "None" and not x.startswith("content/")), "(unnamed)")
    ap = next((x for x in strs if x.startswith("content/")), "")
    b = payload[:1000]
    rows.append({
        "index": len(rows),
        "name": name,
        "addpath": ap,
        "race": struct.unpack_from("<I", b, 0x1C)[0],
        "kind": struct.unpack_from("<I", b, 0x14)[0],
        "parent_ref": struct.unpack_from("<Q", b, 0x08)[0],
        "key_lo": struct.unpack_from("<I", b, 0x20)[0],
        "key_hi": struct.unpack_from("<I", b, 0x24)[0],
        "category": struct.unpack_from("<Q", b, 0x28)[0],
    })
    pos += 24 + size

by_name = {r["name"]: r for r in rows}
cat = json.loads(CAT.read_text(encoding="utf-8"))

RACE = {0: "none", 1: "superearth/seaf", 2: "terminid", 3: "automaton", 4: "illuminate"}
out = []
print(f"{'变种':22s} {'effect ids':16s} {'presence 行':26s} race  parent  catalog-help")
for variant, meta in cat["meta"].items():
    pname = meta.get("presence", "")
    ids = cat["variants"].get(variant, [])
    row = by_name.get(pname)
    rec = {
        "variant": variant,
        "effect_ids": ids,
        "tag": meta.get("tag"),
        "mechanic": meta.get("mechanic"),
        "presence": pname,
        "presence_row": row["index"] if row else None,
        "race": row["race"] if row else None,
        "race_name": RACE.get(row["race"]) if row else None,
        "parent_ref": row["parent_ref"] if row else None,
        "key": (f"0x{row['key_hi']:08X}{row['key_lo']:08X}") if row else None,
        "category": (f"0x{row['category']:016X}") if row else None,
        "catalog_faction": meta.get("faction"),
        "help": meta.get("help"),
        "found": bool(row),
    }
    out.append(rec)
    print(f"{variant:22s} {str(ids):16s} {pname:26s} "
          f"{str(row['race']) if row else '-':4s}  {str(row['parent_ref']) if row else '-':6s}  {meta.get('help', '')[:34]}")

missing = [r for r in out if not r["found"]]
print(f"\njoined {len(out) - len(missing)}/{len(out)} variants; missing presence rows: {[r['presence'] for r in missing]}")

# which presence rows look enemy-related but are not in the catalogue
cat_pres = {r["presence"] for r in out}
others = [r for r in rows if r["name"] not in cat_pres and re.search(r"bugs_|bots_|bot_|illuminate_|elite_|seaf", r["name"])]
print(f"\nenemy-looking presence rows NOT in the catalogue ({len(others)}):")
for r in others:
    print(f"  {r['index']:3d} {r['name']:34s} race={r['race']} kind={r['kind']} key=0x{r['key_hi']:08X}{r['key_lo']:08X}")

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({"variants": out, "presence_rows": rows}, indent=1), encoding="utf-8")
print(f"\nwrote {OUT}")
