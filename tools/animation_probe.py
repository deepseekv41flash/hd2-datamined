#!/usr/bin/env python3
"""animation_probe.py -- 读 Stingray `animation`（动画 clip）：长度 + **它到底动了哪些骨骼**。

为什么需要它
    哨戒/炮塔这类"落地后要伸出来"的壳，姿态是**状态机 layer0 的 clip** 决定的；
    如果某个状态绑的 clip **没有**给升降骨骼（`elevator_01/02`、`base_elevation_arm`…）打关键帧，
    那么进入这个状态时那些骨骼就停在 bind ⇒ 模型整体偏低（缩在车体里）。
    `srkit` 对 `animation` 只有 raw fallback，没有解码器 ⇒ 本工具补这一格。

格式来源
    xypwn/filediver `stingray/animation`（BSD-3）。头：
    `unk00 u32 | boneCount u32 | length f32 | size u32 | hashesCount u32 | beatCount u32
     | hashes[hashesCount] u64 | beats[beatCount]{f32 time, u32 name} | unk02 u16
     | 压缩位图 ceil(boneCount*3/8) 字节（补偶数） | 每骨骼初始变换 | hashFloats[hashesCount] f32`
    之后是条目流，直到 `kind=0x0003`（Terminator）：
    `kind u16`；`type=(kind&0xC000)>>14`：0=Extended 1=Scale 2=Position 3=Rotation
      · 非 Extended：`bone=(kind&0x3FF0)>>4`，再跟 `u16` 时间戳，数据 6/6/4 B（pos/scl/rot）
      · Extended：subtype=kind；除 0x0003 外先读 `bone u32 + time f32`，数据 12/16/12/0 B
    最后 4 B 是 size。

用法
    python tools/animation_probe.py clip.bin
    python tools/animation_probe.py clip.bin --bones bones_xxx.json      # 反查骨骼名
    python tools/animation_probe.py <dir> --bones bones.json             # 批量

判读
    `bones=` 列出**有键的骨骼索引**（映射到名字）。若升降骨骼不在列表里 ⇒ 这个 clip 管不到升降。
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import struct
import sys

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:                                            # noqa: BLE001
        pass

TYPE_NAMES = {0: "Extended", 1: "Scale", 2: "Position", 3: "Rotation"}
DATA_LEN = {2: 6, 3: 4, 1: 6}          # 非 Extended：pos / rot / scl
EXT_DATA_LEN = {0x0002: 0, 0x0004: 12, 0x0005: 16, 0x0006: 12}


def parse_header(b: bytes) -> tuple[dict, int]:
    unk00, bone_count, length, size, hashes_count, beat_count = struct.unpack_from("<IIfIII", b, 0)
    off = 24
    hashes = [struct.unpack_from("<Q", b, off + i * 8)[0] for i in range(hashes_count)]
    off += 8 * hashes_count
    beats = [struct.unpack_from("<fI", b, off + i * 8) for i in range(beat_count)]
    off += 8 * beat_count
    unk02 = struct.unpack_from("<H", b, off)[0]
    off += 2
    bits = (bone_count * 3 + 7) // 8
    if bits % 2:
        bits += 1
    comp_bytes = b[off:off + bits]
    off += bits
    comps = []
    for bone in range(bone_count):
        bit = bone * 3
        get = lambda k: (comp_bytes[(bit + k) // 8] >> ((bit + k) % 8)) & 1   # noqa: E731
        comps.append((get(0), get(1), get(2)))       # pos, rot, scl 是否压缩
    for bone in range(bone_count):
        p, r, s = comps[bone]
        off += 6 if p else 12
        off += 4 if r else 16
        off += 6 if s else 12
    off += 4 * hashes_count                      # hashFloats
    return dict(unk00=unk00, bone_count=bone_count, length=length, size=size,
                hashes=hashes, beat_count=beat_count, beats=beats,
                compression=comps, header_end=off), off


def parse_entries(b: bytes, off: int) -> list[dict]:
    out = []
    n = len(b)
    while off + 2 <= n:
        kind = struct.unpack_from("<H", b, off)[0]
        off += 2
        typ = (kind & 0xC000) >> 14
        if typ == 0:
            sub = kind
            if sub == 0x0003:
                out.append(dict(terminator=True))
                break
            if off + 8 > n:
                break
            bone, ts = struct.unpack_from("<If", b, off)
            off += 8
            off += EXT_DATA_LEN.get(sub, 0)
            out.append(dict(type="Extended", sub=hex(sub), bone=bone, time=ts))
        else:
            if off + 2 > n:
                break
            tsu = struct.unpack_from("<H", b, off)[0]
            off += 2
            bone = (kind & 0x3FF0) >> 4
            off += DATA_LEN[typ]
            t = (((kind & 0x000F) << 16) | tsu) / 1000.0
            out.append(dict(type=TYPE_NAMES[typ], bone=bone, time=t))
    return out


def load_bone_names(path: str | None) -> list[str]:
    if not path:
        return []
    j = json.load(open(path, encoding="utf-8"))
    bones = sorted(j.get("bones", []), key=lambda x: x.get("index", 0))
    return [b.get("name") or b.get("hash_hex") for b in bones]


def probe(path: str, names: list[str]) -> dict:
    b = open(path, "rb").read()
    h, off = parse_header(b)
    entries = parse_entries(b, off)
    tracks = {}
    for e in entries:
        if e.get("terminator"):
            continue
        tracks.setdefault(e["bone"], []).append(e)
    return dict(path=path, size=len(b), header=h, entries=entries, tracks=tracks)


def fmt_bone(i: int, names: list[str]) -> str:
    if 0 <= i < len(names):
        return f"{i}:{names[i]}"
    return f"{i}"


def main() -> int:
    ap = argparse.ArgumentParser(description="读 animation clip：长度与有键的骨骼")
    ap.add_argument("path", help="clip toc.bin 或包含 toc.bin 的目录")
    ap.add_argument("--bones", default=None, help="bones_<id>.json（srkit extract --decoded 产出）")
    ap.add_argument("--keyed", action="store_true", help="只列出有键的骨骼名（一行）")
    ap.add_argument("--matrix", action="store_true",
                    help="目录模式：一张表（clip × 骨骼有无键）")
    a = ap.parse_args()
    names = load_bone_names(a.bones)

    if os.path.isdir(a.path):
        files = sorted(glob.glob(os.path.join(a.path, "**", "toc.bin"), recursive=True)) or \
                sorted(glob.glob(os.path.join(a.path, "*.bin")))
        rows = [probe(f, names) for f in files]
        if a.matrix:
            allb = sorted({i for r in rows for i in r["tracks"]})
            head = "clip".ljust(40) + "len(s)  " + "  ".join(f"{fmt_bone(i, names):>22}" for i in allb)
            print(head)
            for r in rows:
                cells = []
                for i in allb:
                    n = len(r["tracks"].get(i, []))
                    cells.append(f"{('x%d' % n) if n else '-':>22}")
                print(os.path.basename(os.path.dirname(r["path"])).ljust(40) +
                      f"{r['header']['length']:6.2f}  " + "  ".join(cells))
            return 0
        for r in rows:
            show(r, names)
        return 0

    r = probe(a.path, names)
    if a.keyed:
        print(", ".join(fmt_bone(i, names) for i in sorted(r["tracks"])))
        return 0
    show(r, names)
    return 0


def show(r: dict, names: list[str]) -> None:
    h = r["header"]
    keyed = sorted(r["tracks"])
    print(f"{os.path.basename(os.path.dirname(r['path'])) or r['path']}  {r['size']:,} B")
    print(f"  boneCount={h['bone_count']}  length={h['length']:.3f}s  "
          f"hashes={len(h['hashes'])}  beats={h['beat_count']}  entries={len(r['entries'])}")
    print(f"  有键骨骼 {len(keyed)}/{h['bone_count']}: " +
          ", ".join(f"{fmt_bone(i, names)}×{len(r['tracks'][i])}" for i in keyed))


if __name__ == "__main__":
    raise SystemExit(main())
