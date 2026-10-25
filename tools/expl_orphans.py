"""爆炸表孤儿行分析（26088801 离线版，重跑 memmod 时代 build_row_catalogue.py 的方法）。

memmod 时代（build 25988413）结论：爆炸行 422 条中 **263 条无主**，其中 94 条
「伤害行独占」，且最干净的全空行是 17 / 28 / 38 / 3 / 12。
本脚本用离线明文重算同一套判据，供跨 build 复核（游标常量必须重取）。

判据（与老脚本一致）：
  爆炸行无主 = 没有任何射弹行的 +0x90（命中爆炸）或 +0x9C（失效爆炸）指向它

用法：
  python expl_orphans.py                 # 摘要 + 全空候选
  python expl_orphans.py --list          # 全部孤儿行
  python expl_orphans.py --type 17 275   # 查指定爆炸行
  python expl_orphans.py --json out.json
"""
from __future__ import annotations

import argparse
import json
import os
import struct
import sys

sys.stdout.reconfigure(encoding="utf-8")

ROOT = r"D:\mod\refs\dlbin\plaintext-26088801"
EXPL = os.path.join(ROOT, "generated_explosion_settings.dl_bin")
PROJ = os.path.join(ROOT, "generated_projectile_settings.dl_bin")
DMG = os.path.join(ROOT, "generated_damage_settings.dl_bin")

EXPL_STRIDE, EXPL_BASE = 152, 44
PROJ_STRIDE, PROJ_BASE = 272, 44
DMG_STRIDE, DMG_BASE = 76, 44

P_EXPL_IN = 0x090     # 射弹 +144 命中爆炸
P_EXPL_OUT = 0x09C    # 射弹 +156 失效爆炸
P_DMG = 0x03C
P_TYPE = 0x000

E_TYPE = 0x000
E_DMG = 0x004
E_R_IN = 0x010
E_R_MID = 0x014
E_R_OUT = 0x018
E_R4 = 0x01C
E_SHRAP_N = 0x050
E_SHRAP_PROJ = 0x054


def groups(path: str):
    """通用 dl_bin 组遍历：u32 组数 + 每组 LDLD 头(24) + payload。"""
    data = open(path, "rb").read()
    n = struct.unpack_from("<I", data, 0)[0]
    off, out = 4, []
    for _ in range(n):
        if data[off:off + 4] != b"LDLD":
            raise SystemExit(f"✗ {path} 组头 magic 不对 @{off:#x}")
        _ver, gid, size, typ, _unk = struct.unpack_from("<IIIII", data, off + 4)
        payload = data[off + 24:off + 24 + size]
        out.append({"gid": gid, "type": typ, "payload": payload, "off": off})
        off += 24 + size
    if off != len(data):
        raise SystemExit(f"✗ {path} 组遍历未走到底：{off:#x} vs {len(data):#x}")
    return out


def rows(path: str, stride: int):
    """返回 {type: (行号, 行字节)}；只处理 payload 以 u64 0x10 + u64 count 开头的数组组。"""
    out = {}
    for g in groups(path):
        p = g["payload"]
        if len(p) < 16 or struct.unpack_from("<Q", p, 0)[0] != 0x10:
            continue
        n = struct.unpack_from("<Q", p, 8)[0]
        if 16 + n * stride > len(p):
            continue
        for i in range(n):
            r = 16 + i * stride
            t = struct.unpack_from("<I", p, r)[0]
            out[t] = (i, p[r:r + stride])
    return out


def u32(row: bytes, off: int) -> int:
    return struct.unpack_from("<I", row, off)[0]


def f32(row: bytes, off: int) -> float:
    return struct.unpack_from("<f", row, off)[0]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true", help="列出全部孤儿爆炸行")
    ap.add_argument("--type", type=int, nargs="*", default=[], help="查指定爆炸 type")
    ap.add_argument("--json", help="机器可读输出")
    args = ap.parse_args()

    expl = rows(EXPL, EXPL_STRIDE)
    proj = rows(PROJ, PROJ_STRIDE)
    dmg = rows(DMG, DMG_STRIDE)

    inbound: dict[int, list[int]] = {}
    for pt, (_i, row) in proj.items():
        for off, tag in ((P_EXPL_IN, "impact"), (P_EXPL_OUT, "expire")):
            inbound.setdefault(u32(row, off), []).append(pt)

    expl_types = set(expl)
    referenced = {t for t in inbound if t in expl_types}
    orphans = sorted(expl_types - referenced)

    # 伤害行引用计数（全表，含孤儿与有主）
    dmg_ref: dict[int, list[int]] = {}
    for et, (_i, row) in expl.items():
        d = u32(row, E_DMG)
        dmg_ref.setdefault(d, []).append(et)

    def info(t: int) -> dict:
        i, row = expl[t]
        d = u32(row, E_DMG)
        return {
            "type": t,
            "row_index": i,
            "dmg": d,
            "dmg_in_dmgtable": d in dmg,
            "dmg_users": dmg_ref.get(d, []),
            "r_in": f32(row, E_R_IN),
            "r_mid": f32(row, E_R_MID),
            "r_out": f32(row, E_R_OUT),
            "r4": f32(row, E_R4),
            "shrap_n": u32(row, E_SHRAP_N),
            "shrap_proj": u32(row, E_SHRAP_PROJ),
            "zero_radii": all(abs(f32(row, o)) < 1e-9 for o in (E_R_IN, E_R_MID, E_R_OUT, E_R4)),
        }

    print(f"爆炸行 {len(expl)} · 射弹行 {len(proj)} · 伤害行 {len(dmg)}")
    print(f"被射弹引用 {len(referenced)} · **无主 {len(orphans)}**")
    orphan_info = [info(t) for t in orphans]
    exclusive = [o for o in orphan_info if o["dmg_users"] == [o["type"]]]
    print(f"其中「伤害行独占」{len(exclusive)} · 「伤害行在伤害表里存在」{sum(1 for o in orphan_info if o['dmg_in_dmgtable'])}")

    blanks = [o for o in orphan_info
              if o["dmg"] == 0 and o["zero_radii"] and o["shrap_n"] == 0 and o["shrap_proj"] == 0]
    print(f"\n★ 完全空白孤儿行（dmg=0 · 半径全 0 · 无破片）：{len(blanks)}")
    for o in blanks:
        print(f"   爆炸 {o['type']:>3}  row#{o['row_index']}")

    near = [o for o in orphan_info
            if o["type"] not in {b["type"] for b in blanks}
            and o["zero_radii"] and o["shrap_n"] == 0 and o["dmg_users"] == [o["type"]]]
    print(f"\n近空白孤儿（半径全 0 · 无破片 · 伤害行独占）：{len(near)}")
    for o in near[:40]:
        print(f"   爆炸 {o['type']:>3}  row#{o['row_index']:>3}  dmg={o['dmg']}")

    if args.list:
        print("\n=== 全部孤儿爆炸行 ===")
        for o in sorted(orphan_info, key=lambda x: -x["dmg_users"].__len__()):
            print(f"  {o['type']:>3} row#{o['row_index']:>3} dmg={o['dmg']:>4} "
                  f"r=({o['r_in']:.2f},{o['r_mid']:.2f},{o['r_out']:.2f},{o['r4']:.2f}) "
                  f"shrap={o['shrap_n']}x{o['shrap_proj']} users={len(o['dmg_users'])}")

    for t in args.type:
        if t not in expl:
            print(f"\n爆炸 {t}: 不存在")
            continue
        i, row = expl[t]
        o = info(t)
        print(f"\n爆炸 {t} row#{i}  无主={t in orphans}")
        print(f"  +0x004 dmg={o['dmg']} (伤害表内={o['dmg_in_dmgtable']}, 引用方={o['dmg_users']})")
        print(f"  半径 in/mid/out/r4 = {o['r_in']:.3f} / {o['r_mid']:.3f} / {o['r_out']:.3f} / {o['r4']:.3f}")
        print(f"  破片 {o['shrap_n']} × 弹 {o['shrap_proj']}")
        nz = [(off, u32(row, off)) for off in range(0, EXPL_STRIDE, 4) if u32(row, off)]
        print("  非零 u32: " + ", ".join(f"+{off:#04x}={v}" for off, v in nz))

    if args.json:
        json.dump({"expl_rows": len(expl), "proj_rows": len(proj),
                   "referenced": sorted(referenced), "orphans": orphan_info},
                  open(args.json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"\n✓ {args.json}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
