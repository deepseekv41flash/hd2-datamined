#!/usr/bin/env python3
"""Compare guidance-related data rows across guided weapons (build 26251122).

Read-only. Prints: component inventory, WeaponData/ProjectileWeapon/GuidanceTarget
field values, and the spawned missile entity's component inventory + key rows.
"""
from __future__ import annotations
import struct, pathlib, sys

sys.path.insert(0, r"D:\mod\work\repo-datamined\tools")
sys.path.insert(0, r"D:\mod\c12-recon")
from typelib import TypeLib                       # noqa: E402
from pod_rack_swap import parse_blocks            # noqa: E402

PLAIN = r"D:\mod\refs\dlbin\plaintext-26251122\generated_entities.dl_bin"
TYPELIB = r"D:\mod\refs\dlbin\plaintext-26251122\dl_library.dl_typelib"
NAMES = r"D:\mod\filediver-dl-type-names.txt"

WEAPONS = {
    "Spear":            0x25AA2FD4643CF4EE,
    "P-92 Warrant":     0xCF8934FF6567A42D,
    "P-33 MissilePistol": 0x14D5D4506056C7A4,
    "Commando":         0x5990123D142B16CB,
    "WASP":             0xCC786F6491FE7E65,
}

WD, PW, GT = 0x88E4DBB1, 0x45171B68, 0x84957034
SEEK, EYE = 0xBF3A6789, 0x14729B6A


def load_names():
    v = {}
    for line in pathlib.Path(NAMES).read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("//"):
            continue
        h = 5381
        for b in line.encode("utf-8"):
            h = (h * 33 + b) & 0xFFFFFFFF
        v[(h - 5381) & 0xFFFFFFFF] = line
    return v


def main():
    data = pathlib.Path(PLAIN).read_bytes()
    lib = TypeLib(open(TYPELIB, "rb").read())
    names = load_names()
    blocks = parse_blocks(data)
    info = []
    for b in blocks:
        try:
            ms = lib.members(b["type_id"])
        except Exception:
            continue
        if len(ms) < 2:
            continue
        info.append({
            "tid": b["type_id"], "head": b["head"], "payload": b["payload"],
            "slots": ms[0]["size64"], "row_type": ms[1]["type_id"],
            "stride": lib.desc(ms[1]["type_id"])[3],
        })

    def find(block_tid, key):
        for b in info:
            if b["tid"] != block_tid:
                continue
            body = b["head"] + 28
            slots, stride = b["slots"], b["stride"]
            for i in range(slots // 16):
                k, v = struct.unpack_from("<QI", data, body + 16 * i)
                if k == key:
                    rows = (b["payload"] - slots) // stride
                    if v >= rows:
                        return None
                    return body + slots + v * stride, stride, v, rows
            return None
        return None

    def inventory(key):
        out = []
        for b in info:
            got = find(b["tid"], key)
            if got:
                row, stride, r, n = got
                out.append((b["tid"], r, stride, n))
        return out

    def u32(row, off):
        return struct.unpack_from("<I", data, row + off)[0]

    def f32(row, off):
        return struct.unpack_from("<f", data, row + off)[0]

    for wname, key in WEAPONS.items():
        print("=" * 100)
        print(f"### {wname}  entity 0x{key:016X}")
        inv = inventory(key)
        print("  components:", ", ".join(f"{names.get(t,'0x%08X'%t)}({t:#010x}) row{r} stride{s}"
                                         for t, r, s, n in inv if names.get(t)))
        others = [t for t, r, s, n in inv if not names.get(t)]
        if others:
            print("  unnamed blocks:", [f"0x{t:08X}" for t in others])

        g = find(WD, key)
        if g:
            row, stride, r, n = g
            print(f"\n  -- WeaponData (row {r}/{n})")
            print(f"     +0x080={u32(row,0x80)} +0x084={u32(row,0x84)} +0x088={u32(row,0x88)} +0x08C={u32(row,0x8C)}")
            print(f"     fireModes +0x90..9C = {[u32(row,0x90+i*4) for i in range(4)]}")
            print(f"     functionInfo +0xB8 = L{u32(row,0xB8)} R{u32(row,0xBC)}   +0xC0(u64)={u32(row,0xC0)}:{u32(row,0xC4)}")
            print(f"     +0x12C={u32(row,0x12C)} +0x130={u32(row,0x130)}  +0x160={u32(row,0x160)} +0x164={f32(row,0x164):.3f} "
                  f"+0x168={f32(row,0x168):.3f} +0x16C={u32(row,0x16C)}")
            print(f"     +0x170={f32(row,0x170):.3f}/{f32(row,0x174):.3f}  +0x178={f32(row,0x178):.4f}/{f32(row,0x17C):.4f}")
            print(f"     +0x180-183={[u32(row,0x180+i) for i in range(4)]} +0x184={u32(row,0x184)} +0x188={u32(row,0x188)} +0x18C={u32(row,0x18C)}")
            print(f"     +0x190={u32(row,0x190)} crosshair(+0x194)={u32(row,0x194)}")
            nodes = [tuple(u32(row, 0x198 + i*12 + j*4) for j in range(3)) for i in range(4)]
            print(f"     sightNodes = {nodes}")
            print(f"     +0x3A0={u32(row,0x3A0):#010x}  +0x3B4/8/C={u32(row,0x3B4):#010x}/{u32(row,0x3B8):#010x}/{u32(row,0x3BC):#010x}")

        g = find(PW, key)
        if g:
            row, stride, r, n = g
            print(f"\n  -- ProjectileWeapon (row {r}/{n})")
            print(f"     +0x000 primaryType={u32(row,0)}  +0x008={f32(row,8):.3f}  +0x010={f32(row,0x10):.3f} +0x014={f32(row,0x14):.3f} "
                  f"+0x018={f32(row,0x18):.3f} +0x01C={f32(row,0x1C):.3f}  +0x024(u8)={u32(row,0x24)}")
            print(f"     +0x028 spawnedEntity=0x{u32(row,0x2C):08X}{u32(row,0x28):08X}   +0x030={u32(row,0x30)}")
            print(f"     +0x078={u32(row,0x78):#010x} +0x090={u32(row,0x90)} +0x0E8={u32(row,0xE8):#010x}")
            print(f"     +0x230={u32(row,0x230)} +0x23C={f32(row,0x23C):.3f}  altType(+0x240)={u32(row,0x240)} "
                  f"altSpawn=0x{u32(row,0x24C):08X}{u32(row,0x248):08X}")
            spawn = (u32(row, 0x28) | (u32(row, 0x2C) << 32))
            spawn_alt = (u32(row, 0x248) | (u32(row, 0x24C) << 32))

        g = find(GT, key)
        if g:
            row, stride, r, n = g
            print(f"\n  -- GuidanceTarget (row {r}/{n})")
            print(f"     +0x00..: {[u32(row,i*4) for i in range(16)]}")
            print(f"     +0x10 lockTime={f32(row,0x10):.3f} +0x14={f32(row,0x14):.3f} +0x18={f32(row,0x18):.3f} "
                  f"+0x1C(requiresLock,u8)={data[row+0x1C]} +0x20 dot={f32(row,0x20):.3f} +0x24 scale={f32(row,0x24):.3f} +0x28={u32(row,0x28)}")
            print(f"     +0x2C..0x3B atoms = {[f'{u32(row,0x2C+i*4):#010x}' for i in range(4)]}")
            print(f"     +0x3C elem0 = {[data[row+0x3C+i] for i in range(12)]}")
            print(f"     +0x48 binding={u32(row,0x48)}")
            for e in range(4):
                base = 0x4C + e * 12
                print(f"     +0x{base:02X} elem{e} = {[data[row+base+i] for i in range(12)]}")

        for label, ent in (("primary spawned", spawn), ("alt spawned", spawn_alt)):
            if not ent:
                continue
            print(f"\n  -- missile entity ({label}) 0x{ent:016X}")
            inv2 = inventory(ent)
            print("     components:", ", ".join(f"{names.get(t,'0x%08X'%t)}({t:#010x}) row{r} stride{s}"
                                               for t, r, s, n in inv2 if names.get(t)))
            others = [t for t, r, s, n in inv2 if not names.get(t)]
            if others:
                print("     unnamed blocks:", [f"0x{t:08X}" for t in others])
            for comp, tag in ((SEEK, "SeekingMissile"), (EYE, "SensorEye"), (GT, "GuidanceTarget")):
                g2 = find(comp, ent)
                if not g2:
                    continue
                row, stride, r, n = g2
                print(f"     {tag} (row {r}/{n}, stride {stride}):")
                for off in range(0, stride, 16):
                    chunk = [u32(row, off + i * 4) for i in range(4)]
                    print(f"       +0x{off:03X} {['%#010x' % x for x in chunk]}")


if __name__ == "__main__":
    main()
